#!/usr/bin/env python3
"""
Check if accounts have been wrapped and prepared
"""

import json
from web3 import Web3
from eth_account import Account
from blockchain import BlockchainData, ChainId, Token

# Setup
blockchain = BlockchainData(ChainId.MY_CUSTOM_L2)
w3 = Web3(Web3.HTTPProvider(blockchain.http_rpc_url()))

# Load accounts
mnemonic = open("mnemonic.txt", "r").read().strip()
Account.enable_unaudited_hdwallet_features()

# Load WETH
weth_address = blockchain.get_address(Token.WETH)
ERC20_ABI = [
    {"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
]
weth = w3.eth.contract(address=weth_address, abi=ERC20_ABI)

print("=" * 70)
print("Checking Account Preparation Status")
print("=" * 70)

# Check first 10 accounts
accounts_to_check = 10

ready_count = 0
not_ready_count = 0

for i in range(accounts_to_check):
    account = Account.from_mnemonic(mnemonic, account_path=f"m/44'/60'/0'/0/{i}")
    
    eth_balance = w3.eth.get_balance(account.address)
    weth_balance = weth.functions.balanceOf(account.address).call()
    
    status = "✅" if weth_balance > 0 else "❌"
    
    if weth_balance > 0:
        ready_count += 1
    else:
        not_ready_count += 1
    
    print(f"{status} Account {i}: {account.address}")
    print(f"   ETH:  {w3.from_wei(eth_balance, 'ether'):.6f}")
    print(f"   WETH: {w3.from_wei(weth_balance, 'ether'):.9f}")

print("\n" + "=" * 70)
print(f"Summary: {ready_count} ready, {not_ready_count} not ready (out of {accounts_to_check} checked)")
print("=" * 70)

if not_ready_count > 0:
    print("\n❌ Accounts are NOT properly prepared!")
    print("\nPossible reasons:")
    print("1. prepare.py didn't complete successfully")
    print("2. prepare.py was interrupted")
    print("3. WETH contract address is wrong in blockchain.py")
    print("4. Wrapping transactions failed")
    print("\nTo fix:")
    print("  python3 prepare.py")
else:
    print("\n✅ All checked accounts are ready for TPS test!")
