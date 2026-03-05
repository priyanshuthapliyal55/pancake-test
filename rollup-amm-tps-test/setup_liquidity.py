#!/usr/bin/env python3
"""
Create WETH/CAKE pair and add liquidity
"""
import json
import sys
from pathlib import Path
from web3 import Web3
from eth_account import Account

def load_contract_artifact(artifact_path):
    """Load contract ABI and bytecode from Foundry output"""
    with open(artifact_path, 'r') as f:
        artifact = json.load(f)
    return artifact['abi']

def main():
    # Load mnemonic
    mnemonic_file = Path(__file__).parent / "mnemonic.txt"
    mnemonic = mnemonic_file.read_text().strip()
    Account.enable_unaudited_hdwallet_features()
    account = Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")
    
    # Connect to L2
    rpc_url = "http://46.165.235.105:8545"
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print(f"❌ Failed to connect to {rpc_url}")
        sys.exit(1)
    
    # Load deployed addresses
    addresses_file = Path(__file__).parent / "deployed_addresses.json"
    with open(addresses_file, 'r') as f:
        data = json.load(f)
    
    weth_addr = data['addresses']['WETH']
    factory_addr = data['addresses']['Factory']
    router_addr = data['addresses']['Router']
    cake_addr = data['CAKE']
    
    print("=" * 70)
    print("💧 Setting up WETH/CAKE Liquidity Pool")
    print("=" * 70)
    print(f"Deployer: {account.address}")
    print(f"Balance: {w3.from_wei(w3.eth.get_balance(account.address), 'ether')} ETH")
    print(f"\nWETH    : {weth_addr}")
    print(f"Factory : {factory_addr}")
    print(f"Router  : {router_addr}")
    print(f"CAKE    : {cake_addr}")
    print("=" * 70)
    
    # Load contract ABIs
    weth_abi = load_contract_artifact(Path(__file__).parent / "out/WETH.sol/WETH.json")
    factory_abi = load_contract_artifact(Path(__file__).parent.parent / "pancake-swap-core/build/PancakeFactory.sol/PancakeFactory.json")
    router_abi = load_contract_artifact(Path(__file__).parent.parent / "pancake-swap-periphery/build/PancakeRouter.sol/PancakeRouter.json")
    cake_abi = load_contract_artifact(Path(__file__).parent / "out/CAKEToken.sol/CAKEToken.json")
    
    weth = w3.eth.contract(address=weth_addr, abi=weth_abi)
    factory = w3.eth.contract(address=factory_addr, abi=factory_abi)
    router = w3.eth.contract(address=router_addr, abi=router_abi)
    cake = w3.eth.contract(address=cake_addr, abi=cake_abi)
    
    # Step 1: Create pair
    print("\n🔗 Step 1: Create WETH/CAKE pair...")
    try:
        pair_addr = factory.functions.getPair(weth_addr, cake_addr).call()
        if pair_addr != '0x0000000000000000000000000000000000000000':
            print(f"   ✅ Pair already exists at: {pair_addr}")
        else:
            raise Exception("Pair doesn't exist")
    except:
        tx = factory.functions.createPair(weth_addr, cake_addr).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 5000000,
            'gasPrice': w3.to_wei('0.001', 'gwei')
        })
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"   TX: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        pair_addr = factory.functions.getPair(weth_addr, cake_addr).call()
        print(f"   ✅ Pair created at: {pair_addr}")
    
    # Save pair address
    data['Pair_WETH_CAKE'] = pair_addr
    with open(addresses_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Step 2: Approve CAKE spending
    print("\n💰 Step 2: Approve Router to spend CAKE...")
    cake_amount = w3.to_wei(10000, 'ether')  # 10,000 CAKE
    
    allowance = cake.functions.allowance(account.address, router_addr).call()
    if allowance >= cake_amount:
        print(f"   ✅ Already approved: {w3.from_wei(allowance, 'ether')} CAKE")
    else:
        tx = cake.functions.approve(router_addr, cake_amount).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 100000,
            'gasPrice': w3.to_wei('0.001', 'gwei')
        })
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"   TX: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"   ✅ Approved {w3.from_wei(cake_amount, 'ether')} CAKE")
    
    # Step 3: Add liquidity
    print("\n🌊 Step 3: Add liquidity (1 ETH + 10,000 CAKE)...")
    eth_amount = w3.to_wei(1, 'ether')
    deadline = w3.eth.get_block('latest').timestamp + 300  # 5 minutes
    
    tx = router.functions.addLiquidityETH(
        cake_addr,                    # token
        cake_amount,                  # amountTokenDesired
        0,                            # amountTokenMin
        0,                            # amountETHMin
        account.address,              # to
        deadline                      # deadline
    ).build_transaction({
        'from': account.address,
        'value': eth_amount,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 5000000,
        'gasPrice': w3.to_wei('0.001', 'gwei')
    })
    
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"   TX: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"   ✅ Liquidity added successfully!")
    
    # Verify liquidity
    pair_abi = [
        {"constant": True, "inputs": [], "name": "getReserves", "outputs": [{"name": "reserve0", "type": "uint112"}, {"name": "reserve1", "type": "uint112"}, {"name": "blockTimestampLast", "type": "uint32"}], "type": "function"},
        {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "type": "function"},
        {"constant": True, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "type": "function"}
    ]
    pair = w3.eth.contract(address=pair_addr, abi=pair_abi)
    
    token0 = pair.functions.token0().call()
    token1 = pair.functions.token1().call()
    reserves = pair.functions.getReserves().call()
    
    print("\n" + "=" * 70)
    print("✅ Liquidity Pool Status:")
    print("=" * 70)
    print(f"Pair Address: {pair_addr}")
    print(f"Token0: {token0} (Reserve: {w3.from_wei(reserves[0], 'ether')})")
    print(f"Token1: {token1} (Reserve: {w3.from_wei(reserves[1], 'ether')})")
    print("=" * 70)
    print("\n✅ Setup complete! Ready for TPS testing.")
    print("\nNext steps:")
    print("1. Update blockchain.py with deployed addresses")
    print("2. Run: python3 prepare.py")
    print("3. Run: python3 tps_test.py -n 0")

if __name__ == "__main__":
    main()
