#!/usr/bin/env python3
"""
Fund test accounts with ETH for gas fees
"""

from eth_account import Account
from web3 import Web3
import json
import time

# Load configuration
with open('deployed_addresses.json', 'r') as f:
    config = json.load(f)
    rpc_url = config['rpc_url']

# Initialize web3
w3 = Web3(Web3.HTTPProvider(rpc_url))

# Check connection
if not w3.is_connected():
    print(f"❌ Failed to connect to {rpc_url}")
    exit(1)

print(f"✅ Connected to {rpc_url}")
print(f"   Chain ID: {w3.eth.chain_id}")

# Load deployer account (account 0)
mnemonic = open("mnemonic.txt", "r").read().strip()
Account.enable_unaudited_hdwallet_features()
deployer = Account.from_mnemonic(mnemonic, account_path=f"m/44'/60'/0'/0/0")

print(f"\n👤 Deployer: {deployer.address}")
deployer_balance = w3.eth.get_balance(deployer.address)
print(f"   Balance: {w3.from_wei(deployer_balance, 'ether')} ETH")

if deployer_balance == 0:
    print("\n❌ Deployer has no ETH! Fund the deployer account first:")
    print(f"   {deployer.address}")
    exit(1)

# Generate test accounts (indices 1-100)
print("\n📋 Generating 100 test accounts...")
test_accounts = []
for i in range(1, 101):
    account = Account.from_mnemonic(mnemonic, account_path=f"m/44'/60'/0'/0/{i}")
    test_accounts.append(account)

# Amount to send per account (0.01 ETH = enough for ~50 token transfers)
eth_per_account = w3.to_wei('0.01', 'ether')
total_needed = eth_per_account * len(test_accounts)

print(f"\n💰 Funding Details:")
print(f"   Accounts to fund: {len(test_accounts)}")
print(f"   ETH per account: {w3.from_wei(eth_per_account, 'ether')} ETH")
print(f"   Total needed: {w3.from_wei(total_needed, 'ether')} ETH (+ gas)")

if deployer_balance < total_needed:
    print(f"\n⚠️  Warning: Deployer balance ({w3.from_wei(deployer_balance, 'ether')} ETH) may be insufficient")
    print(f"   Consider reducing the amount or funding more accounts later")

print("\n🚀 Starting distribution...")

# Get initial nonce
nonce = w3.eth.get_transaction_count(deployer.address, 'pending')
gas_price = w3.eth.gas_price

successful = 0
failed = 0

for i, account in enumerate(test_accounts):
    try:
        # Check if account already has sufficient balance
        current_balance = w3.eth.get_balance(account.address)
        if current_balance >= eth_per_account:
            print(f"   [{i+1}/100] {account.address} - Already funded (has {w3.from_wei(current_balance, 'ether')} ETH), skipping")
            successful += 1
            continue
        
        # Build transaction
        tx = {
            'from': deployer.address,
            'to': account.address,
            'value': eth_per_account,
            'gas': 21000,  # Standard ETH transfer
            'gasPrice': gas_price,
            'nonce': nonce,
            'chainId': w3.eth.chain_id,
        }
        
        # Sign and send
        signed_tx = deployer.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"   [{i+1}/100] {account.address} - Sent {w3.from_wei(eth_per_account, 'ether')} ETH")
        print(f"             TX: {tx_hash.hex()}")
        
        nonce += 1
        successful += 1
        
        # Small delay to avoid overwhelming the node
        time.sleep(0.1)
        
    except Exception as e:
        print(f"   [{i+1}/100] {account.address} - ❌ Failed: {e}")
        failed += 1
        # Continue with next account

print(f"\n✅ Distribution complete!")
print(f"   Successful: {successful}/100")
print(f"   Failed: {failed}/100")

if successful > 0:
    print(f"\n⏳ Waiting a few seconds for transactions to be processed...")
    time.sleep(5)
    
    # Verify some accounts
    print(f"\n🔍 Verifying first 5 accounts:")
    for i in range(min(5, len(test_accounts))):
        account = test_accounts[i]
        balance = w3.eth.get_balance(account.address)
        print(f"   {account.address}: {w3.from_wei(balance, 'ether')} ETH")

print("\n🎉 Done! Accounts are ready for TPS testing.")
print("\nNext steps:")
print("1. If you need tokens, run: python3 distribute_tokens.py")
print("2. Run TPS test: python3 tps_test_transfers.py -n 0 --token <TOKEN_ADDRESS> --txs 200")
