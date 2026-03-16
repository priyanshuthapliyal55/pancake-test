#!/usr/bin/env python3
"""
Distribute JPMD tokens to test accounts for transfer testing
"""
import json
import sys
from pathlib import Path
from web3 import Web3
from eth_account import Account

# Simple ERC20 ABI for transfers
ERC20_ABI = [
    {"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}
]

def generate_accounts(mnemonic, count):
    Account.enable_unaudited_hdwallet_features()
    return [Account.from_mnemonic(mnemonic, account_path=f"m/44'/60'/0'/0/{i}") for i in range(count)]

def main():
    # Load deployed addresses
    deployed_file = Path(__file__).parent / "deployed_addresses.json"
    if not deployed_file.exists():
        print("❌ deployed_addresses.json not found")
        sys.exit(1)
    
    with open(deployed_file, 'r') as f:
        deployed = json.load(f)
    
    jpmd_address = deployed.get('JPMD_PROXY')
    if not jpmd_address:
        print("❌ JPMD_PROXY not found in deployed_addresses.json")
        sys.exit(1)
    
    rpc_url = deployed.get('rpc_url', 'https://eth-sepolia.rpcmanager.zeeve.net/75z9g86fuof7mm2p690g/rpc')
    
    # Load mnemonic
    mnemonic_file = Path(__file__).parent / "mnemonic.txt"
    if not mnemonic_file.exists():
        print("❌ mnemonic.txt not found")
        sys.exit(1)
    
    mnemonic = mnemonic_file.read_text().strip()
    
    # Account 0 is distributor, accounts 1-100 are test accounts
    all_accounts = generate_accounts(mnemonic, 101)
    distributor = all_accounts[0]
    test_accounts = all_accounts[1:101]  # 100 test accounts
    
    # Connect to chain
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(f"❌ Failed to connect to {rpc_url}")
        sys.exit(1)
    
    print("=" * 70)
    print("💸 Distributing JPMD Tokens")
    print("=" * 70)
    print(f"Chain        : {rpc_url}")
    print(f"Token        : {jpmd_address}")
    print(f"Distributor  : {distributor.address}")
    
    # Load token
    jpmd = w3.eth.contract(address=Web3.to_checksum_address(jpmd_address), abi=ERC20_ABI)
    
    try:
        symbol = jpmd.functions.symbol().call()
        decimals = jpmd.functions.decimals().call()
        balance = jpmd.functions.balanceOf(distributor.address).call()
    except Exception as e:
        print(f"❌ Failed to read token: {e}")
        sys.exit(1)
    
    # Amount per account: 10,000 base units = 100 JPMD (with 2 decimals)
    amount_per_account = 10000
    total_needed = amount_per_account * len(test_accounts)
    
    print(f"Symbol       : {symbol}")
    print(f"Decimals     : {decimals}")
    print(f"Your Balance : {balance:,} ({balance / (10 ** decimals):,.2f} {symbol})")
    print(f"Amount/Acct  : {amount_per_account:,} ({amount_per_account / (10 ** decimals):,.2f} {symbol})")
    print(f"Total Needed : {total_needed:,} ({total_needed / (10 ** decimals):,.2f} {symbol})")
    print(f"Recipients   : {len(test_accounts)} accounts")
    print("=" * 70)
    
    if balance < total_needed:
        print(f"❌ Insufficient balance! Need {total_needed:,} but have {balance:,}")
        sys.exit(1)
    
    print()
    print("🚀 Distributing tokens...")
    successful = 0
    failed = 0
    
    for i, account in enumerate(test_accounts):
        try:
            tx = jpmd.functions.transfer(account.address, amount_per_account).build_transaction({
                'from': distributor.address,
                'nonce': w3.eth.get_transaction_count(distributor.address),
                'gas': 100000,
                'gasPrice': w3.eth.gas_price
            })
            
            signed_tx = distributor.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
            
            if receipt.status == 1:
                successful += 1
                if (i + 1) % 10 == 0:
                    print(f"   ✅ {successful}/{len(test_accounts)} accounts funded")
            else:
                failed += 1
                
        except Exception as e:
            failed += 1
            if failed < 5:  # Only show first few errors
                print(f"   ❌ Failed account {i}: {e}")
    
    print()
    print("=" * 70)
    print("✅ Distribution Complete")
    print("=" * 70)
    print(f"Successful : {successful}/{len(test_accounts)}")
    print(f"Failed     : {failed}/{len(test_accounts)}")
    print("=" * 70)
    
    if successful > 0:
        print()
        print("🎯 Ready to run transfer test:")
        print(f"   python tps_test_transfers.py -n 0 --token {jpmd_address}")

if __name__ == "__main__":
    main()
