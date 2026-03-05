#!/usr/bin/env python3
"""
Manual script to add liquidity if deploy_l2.py fails at that step
"""

import json
import time
from web3 import Web3
from eth_account import Account

# Load configuration
with open('deployed_addresses.json') as f:
    config = json.load(f)

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

print("Manual Liquidity Addition")
print("=" * 70)
print(f"Deployer: {deployer_address}")
print(f"Balance: {w3.from_wei(w3.eth.get_balance(deployer_address), 'ether')} ETH")
print()

# Load Router ABI
with open('../pancake-swap-periphery/build/PancakeRouter.sol/PancakeRouter.json') as f:
    router_artifact = json.load(f)

router_address = addresses['Router']
cake_address = config.get('CAKE', addresses.get('CAKE'))
weth_address = addresses['WETH']

router = w3.eth.contract(address=router_address, abi=router_artifact['abi'])

# Simple ERC20 ABI
ERC20_ABI = [
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
]

cake = w3.eth.contract(address=cake_address, abi=ERC20_ABI)

# Parameters
ETH_AMOUNT = input("Enter ETH amount (default 0.5): ").strip() or "0.5"
CAKE_AMOUNT = input("Enter CAKE amount (default 1000): ").strip() or "1000"

eth_wei = w3.to_wei(float(ETH_AMOUNT), 'ether')
cake_wei = w3.to_wei(float(CAKE_AMOUNT), 'ether')

print(f"\nAdding Liquidity:")
print(f"  {ETH_AMOUNT} ETH")
print(f"  {CAKE_AMOUNT} CAKE")
print()

# Check CAKE balance
balance = cake.functions.balanceOf(deployer_address).call()
print(f"CAKE Balance: {w3.from_wei(balance, 'ether')} CAKE")

if balance < cake_wei:
    print("❌ Insufficient CAKE balance!")
    exit(1)

# Step 1: Approve CAKE
print("\nStep 1: Approving CAKE...")
approve_tx = cake.functions.approve(router_address, cake_wei).build_transaction({
    'from': deployer_address,
    'nonce': w3.eth.get_transaction_count(deployer_address),
    'gas': 100000,
    'gasPrice': w3.to_wei(0.001, 'gwei'),
    'chainId': L2_CHAIN_ID,
})

signed = w3.eth.account.sign_transaction(approve_tx, deployer.key)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print(f"TX: {tx_hash.hex()}")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

if receipt['status'] == 1:
    print("✅ Approved")
else:
    print("❌ Approval failed")
    exit(1)

# Step 2: Add Liquidity
print("\nStep 2: Adding liquidity...")
deadline = int(time.time()) + 3600

try:
    # First try to estimate gas
    gas_estimate = router.functions.addLiquidityETH(
        cake_address,
        cake_wei,
        0,  # amountTokenMin
        0,  # amountETHMin
        deployer_address,
        deadline
    ).estimate_gas({
        'from': deployer_address,
        'value': eth_wei
    })
    print(f"Gas estimate: {gas_estimate}")
    gas_limit = int(gas_estimate * 1.5)
except Exception as e:
    print(f"⚠️  Gas estimation failed: {e}")
    print("This usually means the transaction will revert")
    print("\nPossible reasons:")
    print("1. Pair doesn't exist - create it first with Factory.createPair()")
    print("2. Router's WETH address doesn't match deployed WETH")
    print("3. Amounts are invalid")
    exit(1)

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
    'gas': gas_limit,
    'gasPrice': w3.to_wei(0.001, 'gwei'),
    'chainId': L2_CHAIN_ID,
    'value': eth_wei
})

signed = w3.eth.account.sign_transaction(liquidity_tx, deployer.key)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print(f"TX: {tx_hash.hex()}")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

if receipt['status'] == 1:
    print("✅ Liquidity added successfully!")
else:
    print("❌ Transaction failed")
    print(f"Gas used: {receipt['gasUsed']} / {gas_limit}")
