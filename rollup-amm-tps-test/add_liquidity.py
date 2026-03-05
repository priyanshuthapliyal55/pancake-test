#!/usr/bin/env python3
"""
Manually add liquidity to WETH/CAKE pair
Use this if automatic deployment didn't add liquidity or you need more
"""

import json
import time
from web3 import Web3
from eth_account import Account
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

# Load deployment addresses
try:
    with open('deployed_addresses.json', 'r') as f:
        config = json.load(f)
    
    L2_RPC_URL = config['rpc_url']
    L2_CHAIN_ID = config['chain_id']
    ROUTER_ADDRESS = config['addresses']['Router']
    WETH_ADDRESS = config['addresses']['WETH']
    CAKE_ADDRESS = config['addresses']['CAKE']
    
    print("✅ Loaded configuration from deployed_addresses.json")
except FileNotFoundError:
    print("❌ deployed_addresses.json not found!")
    print("   Run deploy_l2.py first")
    exit(1)

# Liquidity amounts
ETH_AMOUNT = float(input("Enter ETH amount to add (e.g., 0.5): "))
CAKE_AMOUNT = float(input("Enter CAKE amount to add (e.g., 1000): "))

# =============================================================================
# SETUP
# =============================================================================

# Read mnemonic
with open('mnemonic.txt', 'r') as f:
    mnemonic = f.read().strip()

# Setup Web3
w3 = Web3(Web3.HTTPProvider(L2_RPC_URL))
if not w3.is_connected():
    print("❌ Failed to connect to RPC")
    exit(1)

# Get account
Account.enable_unaudited_hdwallet_features()
account = Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")

print(f"\n{'=' * 70}")
print(f"Adding Liquidity to WETH/CAKE Pair")
print(f"{'=' * 70}")
print(f"Account: {account.address}")
print(f"ETH: {ETH_AMOUNT}")
print(f"CAKE: {CAKE_AMOUNT}")
print(f"{'=' * 70}\n")

# Load ABIs
router_abi = json.load(open('../pancake-swap-periphery/build/contracts/PancakeRouter.json'))['abi']
erc20_abi = [
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], 
     "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "account", "type": "address"}], 
     "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
]

router = w3.eth.contract(address=ROUTER_ADDRESS, abi=router_abi)
cake = w3.eth.contract(address=CAKE_ADDRESS, abi=erc20_abi)

# =============================================================================
# ADD LIQUIDITY
# =============================================================================

def send_tx(tx_func, *args, value=0):
    """Helper to send transaction"""
    tx = tx_func(*args).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 3000000,
        'gasPrice': w3.to_wei(0.001, 'gwei'),
        'chainId': L2_CHAIN_ID,
        'value': value
    })
    
    signed = w3.eth.account.sign_transaction(tx, account.key)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    
    print(f"   TX: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    
    if receipt['status'] == 1:
        print(f"   ✅ Success!")
        return receipt
    else:
        print(f"   ❌ Failed!")
        exit(1)

# Check CAKE balance
cake_balance = cake.functions.balanceOf(account.address).call()
cake_balance_human = w3.from_wei(cake_balance, 'ether')
print(f"Your CAKE balance: {cake_balance_human}")

if cake_balance_human < CAKE_AMOUNT:
    print(f"❌ Insufficient CAKE! You have {cake_balance_human}, need {CAKE_AMOUNT}")
    exit(1)

# Check ETH balance
eth_balance = w3.eth.get_balance(account.address)
eth_balance_human = w3.from_wei(eth_balance, 'ether')
print(f"Your ETH balance: {eth_balance_human}")

if eth_balance_human < ETH_AMOUNT + 0.01:  # +0.01 for gas
    print(f"❌ Insufficient ETH! You have {eth_balance_human}, need {ETH_AMOUNT + 0.01}")
    exit(1)

# Step 1: Approve CAKE
print("\n1️⃣  Approving CAKE...")
cake_wei = w3.to_wei(CAKE_AMOUNT, 'ether')
send_tx(cake.functions.approve, ROUTER_ADDRESS, cake_wei)

# Step 2: Add Liquidity
print("\n2️⃣  Adding liquidity...")
eth_wei = w3.to_wei(ETH_AMOUNT, 'ether')
deadline = int(time.time()) + 3600  # 1 hour

send_tx(
    router.functions.addLiquidityETH,
    CAKE_ADDRESS,  # token
    cake_wei,  # amountTokenDesired
    0,  # amountTokenMin (set to 0 for testing, use proper slippage in production)
    0,  # amountETHMin
    account.address,  # to
    deadline,  # deadline
    value=eth_wei
)

print(f"\n{'=' * 70}")
print(f"✅ Liquidity added successfully!")
print(f"{'=' * 70}")
print(f"\nYou can now run TPS tests:")
print(f"  python prepare.py")
print(f"  python tps_test.py -n 0")
