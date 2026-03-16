#!/usr/bin/env python3
"""
Deploy full JPMD-like upgradeable token (with proxy) to L2
This mimics the exact architecture of JPMD on Base
"""
import json
import sys
from pathlib import Path
from web3 import Web3
from eth_account import Account

def load_foundry_artifact(contract_name):
    """Load contract ABI and bytecode from Foundry output"""
    artifact_path = Path(__file__).parent / f"out/{contract_name}.sol/{contract_name}.json"
    
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    
    with open(artifact_path, 'r') as f:
        artifact = json.load(f)
    
    abi = artifact['abi']
    bytecode = artifact['bytecode']['object']
    
    if not bytecode.startswith('0x'):
        bytecode = '0x' + bytecode
    
    return abi, bytecode

def main():
    # Load mnemonic
    mnemonic_file = Path(__file__).parent / "mnemonic.txt"
    if not mnemonic_file.exists():
        print("❌ mnemonic.txt not found")
        sys.exit(1)
    
    mnemonic = mnemonic_file.read_text().strip()
    Account.enable_unaudited_hdwallet_features()
    deployer = Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")
    
    # Connect to L2
    rpc_url = "https://eth-sepolia.rpcmanager.zeeve.net/75z9g86fuof7mm2p690g/rpc"  # Change to your L2 RPC URL
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print(f"❌ Failed to connect to {rpc_url}")
        print("   Update rpc_url in this script")
        sys.exit(1)
    
    print("=" * 80)
    print("🪙 Deploying Upgradeable JPMD Token (Full Version)")
    print("=" * 80)
    print(f"✅ Connected to L2")
    print(f"   Deployer: {deployer.address}")
    balance = w3.eth.get_balance(deployer.address)
    print(f"   Balance: {w3.from_wei(balance, 'ether')} ETH\n")
    
    if balance == 0:
        print("❌ Deployer has no ETH balance!")
        sys.exit(1)
    
    # Check if compiled
    if not (Path(__file__).parent / "out/Token.sol/Token.json").exists():
        print("❌ Contracts not compiled!")
        print("\nRun these commands first:")
        print("  npm install")
        print("  forge build")
        sys.exit(1)
    
    try:
        # Load artifacts
        print("📦 Loading contract artifacts...")
        token_abi, token_bytecode = load_foundry_artifact("Token")
        proxy_abi, proxy_bytecode = load_foundry_artifact("TokenProxy")
        print("   ✅ Loaded Token and TokenProxy\n")
        
        # Configuration
        token_name = "JPMD"
        token_symbol = "JPMD"
        initial_supply = 100_100_000  # 1,001,000 JPMD (with 2 decimals)
        admin = deployer.address
        
        # Step 1: Deploy implementation
        print("🚀 Step 1/3: Deploying Token implementation...")
        TokenImpl = w3.eth.contract(abi=token_abi, bytecode=token_bytecode)
        
        # Estimate gas or use high limit
        try:
            estimated_gas = TokenImpl.constructor().estimate_gas({'from': deployer.address})
            gas_limit = int(estimated_gas * 1.5)  # Add 50% buffer
            print(f"   Estimated gas: {estimated_gas:,} (using {gas_limit:,} with buffer)")
        except Exception as e:
            gas_limit = 10000000  # 10M gas fallback
            print(f"   Could not estimate gas, using {gas_limit:,}")
        
        tx1 = TokenImpl.constructor().build_transaction({
            'from': deployer.address,
            'nonce': w3.eth.get_transaction_count(deployer.address),
            'gas': gas_limit,
            'gasPrice': w3.eth.gas_price
        })
        
        signed_tx1 = deployer.sign_transaction(tx1)
        tx1_hash = w3.eth.send_raw_transaction(signed_tx1.rawTransaction)
        print(f"   TX: {tx1_hash.hex()}")
        print(f"   ⏳ Waiting for confirmation...")
        
        receipt1 = w3.eth.wait_for_transaction_receipt(tx1_hash, timeout=300)
        if receipt1.status == 0:
            print("❌ Implementation deployment failed!")
            sys.exit(1)
        
        impl_address = receipt1.contractAddress
        print(f"   ✅ Implementation deployed: {impl_address}\n")
        
        # Step 2: Prepare initialization data
        print("🔧 Step 2/3: Preparing initialization data...")
        token = w3.eth.contract(address=impl_address, abi=token_abi)
        init_data = token.encodeABI(
            fn_name='initialize',
            args=[token_name, token_symbol, initial_supply, admin]
        )
        print(f"   ✅ Init data prepared ({len(init_data)} bytes)\n")
        
        # Step 3: Deploy proxy
        print("🚀 Step 3/3: Deploying TokenProxy...")
        TokenProxyContract = w3.eth.contract(abi=proxy_abi, bytecode=proxy_bytecode)
        
        tx2 = TokenProxyContract.constructor(impl_address, init_data).build_transaction({
            'from': deployer.address,
            'nonce': w3.eth.get_transaction_count(deployer.address),
            'gas': 2000000,
            'gasPrice': w3.eth.gas_price
        })
        
        signed_tx2 = deployer.sign_transaction(tx2)
        tx2_hash = w3.eth.send_raw_transaction(signed_tx2.rawTransaction)
        print(f"   TX: {tx2_hash.hex()}")
        print(f"   ⏳ Waiting for confirmation...")
        
        receipt2 = w3.eth.wait_for_transaction_receipt(tx2_hash, timeout=300)
        if receipt2.status == 0:
            print("❌ Proxy deployment failed!")
            sys.exit(1)
        
        proxy_address = receipt2.contractAddress
        print(f"   ✅ Proxy deployed: {proxy_address}\n")
        
        # Verify deployment by reading through proxy
        print("🔍 Verifying deployment...")
        token_proxy = w3.eth.contract(address=proxy_address, abi=token_abi)
        
        name = token_proxy.functions.name().call()
        symbol = token_proxy.functions.symbol().call()
        decimals = token_proxy.functions.decimals().call()
        total_supply = token_proxy.functions.totalSupply().call()
        admin_balance = token_proxy.functions.balanceOf(admin).call()
        
        print("=" * 80)
        print("✅ Deployment Successful!")
        print("=" * 80)
        print(f"Proxy Address        : {proxy_address}")
        print(f"Implementation       : {impl_address}")
        print(f"Name                 : {name}")
        print(f"Symbol               : {symbol}")
        print(f"Decimals             : {decimals}")
        print(f"Total Supply         : {total_supply:,} base units ({total_supply / (10 ** decimals):,.0f} {symbol})")
        print(f"Admin Balance        : {admin_balance:,} base units ({admin_balance / (10 ** decimals):,.0f} {symbol})")
        print(f"Admin (has all roles): {admin}")
        print("=" * 80)
        print()
        print("📝 Important:")
        print(f"   Use the PROXY address for all interactions: {proxy_address}")
        print(f"   The proxy is upgradeable via UPGRADER_ROLE")
        print("=" * 80)
        print()
        print("🎯 Next Steps:")
        print("=" * 80)
        print("1. Export the proxy address:")
        print(f"   export JPMD_ADDRESS={proxy_address}")
        print()
        print("2. Distribute tokens to test accounts:")
        print(f"   python distribute_jpmd.py {proxy_address} 10000")
        print()
        print("3. Run transfer TPS test:")
        print(f"   python tps_test_transfers.py -n 0 --token {proxy_address} --amount 100")
        print("=" * 80)
        
        # Save to deployed_addresses.json
        deployed_file = Path(__file__).parent / "deployed_addresses.json"
        if deployed_file.exists():
            with open(deployed_file, 'r') as f:
                deployed = json.load(f)
        else:
            deployed = {}
        
        deployed['JPMD_PROXY'] = proxy_address
        deployed['JPMD_IMPLEMENTATION'] = impl_address
        
        with open(deployed_file, 'w') as f:
            json.dump(deployed, f, indent=2)
        
        print(f"\n💾 Saved addresses to {deployed_file}")
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
