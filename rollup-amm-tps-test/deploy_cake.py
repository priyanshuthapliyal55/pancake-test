#!/usr/bin/env python3
"""
Simple script to deploy CAKE token to L2
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
    account = Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")
    
    # Connect to L2
    rpc_url = "http://46.165.235.105:8545"
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print(f"❌ Failed to connect to {rpc_url}")
        sys.exit(1)
    
    print("=" * 70)
    print("🪙 Deploying CAKE Token to L2")
    print("=" * 70)
    print(f"✅ Connected to L2")
    print(f"   Deployer: {account.address}")
    print(f"   Balance: {w3.from_wei(w3.eth.get_balance(account.address), 'ether')} ETH\n")
    
    # Load compiled CAKE token
    cake_path = Path(__file__).parent / "out/CAKEToken.sol/CAKEToken.json"
    if not cake_path.exists():
        print("❌ CAKEToken not compiled. Run: forge build CAKEToken.sol --use 0.5.16")
        sys.exit(1)
    
    print("📦 Loading CAKE token artifact...")
    cake_abi, cake_bytecode = load_contract_artifact(cake_path)
    print(f"   ✅ Loaded {len(cake_abi)} functions\n")
    
    # Deploy CAKE
    print("🚀 Deploying CAKE token...")
    CAKEToken = w3.eth.contract(abi=cake_abi, bytecode=cake_bytecode)
    
    # Build transaction
    tx = CAKEToken.constructor().build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 2000000,
        'gasPrice': w3.to_wei('0.001', 'gwei')
    })
    
    # Sign and send
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"   TX: {tx_hash.hex()}")
    print(f"   ⏳ Waiting for confirmation...")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    cake_address = receipt.contractAddress
    
    print(f"   ✅ CAKE deployed at: {cake_address}\n")
    
    # Verify deployment
    cake = w3.eth.contract(address=cake_address, abi=cake_abi)
    name = cake.functions.name().call()
    symbol = cake.functions.symbol().call()
    total_supply = cake.functions.totalSupply().call()
    decimals = cake.functions.decimals().call()
    deployer_balance = cake.functions.balanceOf(account.address).call()
    
    print("=" * 70)
    print("✅ CAKE Token Details:")
    print("=" * 70)
    print(f"Address      : {cake_address}")
    print(f"Name         : {name}")
    print(f"Symbol       : {symbol}")
    print(f"Decimals     : {decimals}")
    print(f"Total Supply : {w3.from_wei(total_supply, 'ether'):,.0f} {symbol}")
    print(f"Your Balance : {w3.from_wei(deployer_balance, 'ether'):,.0f} {symbol}")
    print("=" * 70)
    
    # Save address
    addresses_file = Path(__file__).parent / "deployed_addresses.json"
    if addresses_file.exists():
        with open(addresses_file, 'r') as f:
            addresses = json.load(f)
    else:
        addresses = {}
    
    addresses['CAKE'] = cake_address
    
    with open(addresses_file, 'w') as f:
        json.dump(addresses, f, indent=2)
    
    print(f"\n✅ Address saved to deployed_addresses.json")

if __name__ == "__main__":
    main()