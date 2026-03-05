#!/usr/bin/env python3
"""
Test addLiquidityETH with very small amounts to debug the issue
"""

import json
import time
from web3 import Web3
from eth_account import Account

# Load configuration
try:
    with open('deployed_addresses.json') as f:
        config = json.load(f)
except FileNotFoundError:
    print("❌ deployed_addresses.json not found. Run deploy_l2.py first.")
    exit(1)

L2_RPC_URL = config['rpc_url']
L2_CHAIN_ID = config['chain_id']
addresses = config['addresses']

w3 = Web3(Web3.HTTPProvider(L2_RPC_URL))

# Load deployer account
with open('mnemonic.txt') as f:
    mnemonic = f.read().strip()

Account.enable_unaudited_hdwallet_features()
deployer = Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")
deployer_address = deployer.address

print("Testing addLiquidityETH with minimal amounts")
print("=" * 70)
print(f"Chain ID: {L2_CHAIN_ID}")
print(f"Deployer: {deployer_address}")
print(f"Balance: {w3.from_wei(w3.eth.get_balance(deployer_address), 'ether')} ETH\n")

# Get addresses
weth_address = addresses['WETH']
router_address = addresses['Router']
factory_address = addresses['Factory']
cake_address = config.get('CAKE', addresses.get('CAKE'))

print(f"WETH: {weth_address}")
print(f"Factory: {factory_address}")
print(f"Router: {router_address}")
print(f"CAKE: {cake_address}\n")

# Load Router ABI
with open('../pancake-swap-periphery/build/PancakeRouter.sol/PancakeRouter.json') as f:
    router_artifact = json.load(f)

router = w3.eth.contract(address=router_address, abi=router_artifact['abi'])

# Load Factory ABI for checking pair
with open('../pancake-swap-core/build/PancakeFactory.sol/PancakeFactory.json') as f:
    factory_artifact = json.load(f)

factory = w3.eth.contract(address=factory_address, abi=factory_artifact['abi'])

# Check pair
pair_address = factory.functions.getPair(weth_address, cake_address).call()
print(f"Pair address: {pair_address}")

if pair_address == "0x0000000000000000000000000000000000000000":
    print("❌ Pair doesn't exist! Creating it first...")
    
    create_tx = factory.functions.createPair(weth_address, cake_address).build_transaction({
        'from': deployer_address,
        'nonce': w3.eth.get_transaction_count(deployer_address),
        'gas': 3000000,
        'gasPrice': w3.to_wei(0.001, 'gwei'),
        'chainId': L2_CHAIN_ID,
    })
    
    signed = w3.eth.account.sign_transaction(create_tx, deployer.key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"Creating pair TX: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt['status'] != 1:
        print("❌ Failed to create pair")
        exit(1)
    
    pair_address = factory.functions.getPair(weth_address, cake_address).call()
    print(f"✅ Pair created: {pair_address}\n")
else:
    print(f"✅ Pair exists\n")

# Load Pair ABI to check reserves
PAIR_ABI = [
    {"constant": True, "inputs": [], "name": "getReserves", "outputs": [{"name": "reserve0", "type": "uint112"}, {"name": "reserve1", "type": "uint112"}, {"name": "blockTimestampLast", "type": "uint32"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "type": "function"},
]

pair = w3.eth.contract(address=pair_address, abi=PAIR_ABI)
reserves = pair.functions.getReserves().call()
token0 = pair.functions.token0().call()
token1 = pair.functions.token1().call()

print(f"Token0: {token0}")
print(f"Token1: {token1}")
print(f"Reserve0: {reserves[0]}")
print(f"Reserve1: {reserves[1]}\n")

if reserves[0] > 0 or reserves[1] > 0:
    print("⚠️  Pair already has liquidity!")
    print("This is not a fresh pair. Continuing anyway...\n")

# Approve CAKE
ERC20_ABI = [
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "", "type": "address"}, {"name": "", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
]

cake = w3.eth.contract(address=cake_address, abi=ERC20_ABI)

# Test with 3 different amounts
test_amounts = [
    (0.01, 10),    # Very small
    (0.05, 50),    # Small
    (0.1, 100),    # Medium
]

for eth_amt, cake_amt in test_amounts:
    print(f"\n{'='*70}")
    print(f"Testing: {eth_amt} ETH + {cake_amt} CAKE")
    print('='*70)
    
    eth_wei = w3.to_wei(eth_amt, 'ether')
    cake_wei = w3.to_wei(cake_amt, 'ether')
    
    # Check balance
    cake_balance = cake.functions.balanceOf(deployer_address).call()
    if cake_balance < cake_wei:
        print(f"❌ Insufficient CAKE. Have: {w3.from_wei(cake_balance, 'ether')}, Need: {cake_amt}")
        continue
    
    # Approve
    print("Approving CAKE...")
    allowance = cake.functions.allowance(deployer_address, router_address).call()
    if allowance < cake_wei:
        approve_tx = cake.functions.approve(router_address, cake_wei * 10).build_transaction({
            'from': deployer_address,
            'nonce': w3.eth.get_transaction_count(deployer_address),
            'gas': 100000,
            'gasPrice': w3.to_wei(0.001, 'gwei'),
            'chainId': L2_CHAIN_ID,
        })
        
        signed = w3.eth.account.sign_transaction(approve_tx, deployer.key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        
        if receipt['status'] != 1:
            print("❌ Approval failed")
            continue
        print("✅ Approved")
    else:
        print("✅ Already approved")
    
    # Try addLiquidityETH
    deadline = int(time.time()) + 3600
    
    print(f"Calling addLiquidityETH...")
    try:
        gas_estimate = router.functions.addLiquidityETH(
            cake_address,
            cake_wei,
            cake_wei // 2,  # amountTokenMin (50% slippage)
            eth_wei // 2,   # amountETHMin (50% slippage)
            deployer_address,
            deadline
        ).estimate_gas({
            'from': deployer_address,
            'value': eth_wei
        })
        
        print(f"✅ Gas estimate: {gas_estimate}")
        print(f"   This amount should work! Adding liquidity...")
        
        liquidity_tx = router.functions.addLiquidityETH(
            cake_address,
            cake_wei,
            0,  # amountTokenMin
            0,  # amountETHMin
            deployer_address,
            deadline
        ).build_transaction({
            'from': deployer_address,
            'nonce': w3.eth.get_transaction_count(deployer_address),
            'gas': int(gas_estimate * 1.5),
            'gasPrice': w3.to_wei(0.001, 'gwei'),
            'chainId': L2_CHAIN_ID,
            'value': eth_wei
        })
        
        signed = w3.eth.account.sign_transaction(liquidity_tx, deployer.key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"TX: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        
        if receipt['status'] == 1:
            print(f"✅ SUCCESS! Liquidity added with {eth_amt} ETH + {cake_amt} CAKE")
            print(f"   Gas used: {receipt['gasUsed']}")
            
            # Check new reserves
            reserves = pair.functions.getReserves().call()
            print(f"   New reserves: {reserves[0]}, {reserves[1]}")
            break
        else:
            print(f"❌ Transaction reverted")
            print(f"   Gas used: {receipt['gasUsed']}")
            
    except Exception as e:
        print(f"❌ Gas estimation failed: {str(e)[:200]}")
        print(f"   This amount will likely revert")

print("\n" + "="*70)
print("Test complete")
