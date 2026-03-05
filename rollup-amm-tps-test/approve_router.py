#!/usr/bin/env python3
"""
Approve router to spend WETH for all accounts
"""

from web3 import Web3
from eth_account import Account
import json
from blockchain import BlockchainData, ChainId, Token, Contract
import concurrent.futures
import time

# Setup
blockchain = BlockchainData(ChainId.MY_CUSTOM_L2)
w3 = Web3(Web3.HTTPProvider(blockchain.http_rpc_url()))

weth_address = blockchain.get_address(Token.WETH)
router_address = blockchain.get_address(Contract.PANCAKE_SMART_ROUTER)

print(f"WETH: {weth_address}")
print(f"Router: {router_address}")

# Load ABIs
WETH_ABI = json.loads(open('abis/WETH9.abi', 'r').read())
weth = w3.eth.contract(address=weth_address, abi=WETH_ABI)

# Load mnemonic
mnemonic = open("mnemonic.txt", "r").read().strip()
Account.enable_unaudited_hdwallet_features()

# Max allowance
MAX_UINT256 = 2**256 - 1

def check_and_approve(account_index):
    """Check allowance and approve if needed"""
    try:
        account = Account.from_mnemonic(mnemonic, account_path=f"m/44'/60'/0'/0/{account_index}")
        
        # Check current allowance
        allowance = weth.functions.allowance(account.address, router_address).call()
        
        if allowance > 0:
            print(f"✅ Account {account_index}: Already approved (allowance: {w3.from_wei(allowance, 'ether')} WETH)")
            return True
        
        # Need to approve
        print(f"🔨 Account {account_index}: Approving router...")
        
        nonce = w3.eth.get_transaction_count(account.address)
        
        tx = weth.functions.approve(router_address, MAX_UINT256).build_transaction({
            'from': account.address,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
        })
        
        signed = w3.eth.account.sign_transaction(tx, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        
        if receipt['status'] == 1:
            print(f"✅ Account {account_index}: Approved! TX: {tx_hash.hex()}")
            return True
        else:
            print(f"❌ Account {account_index}: Approval failed!")
            return False
            
    except Exception as e:
        print(f"❌ Account {account_index}: Error - {e}")
        return False

print("\n" + "=" * 70)
print("Approving Router for All Accounts")
print("=" * 70)

# Process in parallel (10 at a time)
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(check_and_approve, i) for i in range(100)]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]

successful = sum(results)
print("\n" + "=" * 70)
print(f"✅ Approved: {successful}/100 accounts")
print("=" * 70)
