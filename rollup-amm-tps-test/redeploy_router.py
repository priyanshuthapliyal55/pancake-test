#!/usr/bin/env python3
"""
Redeploy only the Router with updated init code hash
Keeps existing WETH, Factory, CAKE, and Pair
"""

import json
import time
from web3 import Web3
from eth_account import Account
from pathlib import Path

# Load existing configuration
with open('deployed_addresses.json') as f:
    config = json.load(f)

L2_RPC_URL = config['rpc_url']
L2_CHAIN_ID = config['chain_id']
L2_NAME = config['network']

w3 = Web3(Web3.HTTPProvider(L2_RPC_URL))

if not w3.is_connected():
    print("❌ Failed to connect to RPC")
    exit(1)

# Load deployer account
with open('mnemonic.txt') as f:
    mnemonic = f.read().strip()

Account.enable_unaudited_hdwallet_features()
deployer = Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")
deployer_address = deployer.address

print("=" * 70)
print("🔄 Redeploy PancakeRouter")
print("=" * 70)
print(f"Network: {L2_NAME}")
print(f"Chain ID: {L2_CHAIN_ID}")
print(f"Deployer: {deployer_address}")
print(f"Balance: {w3.from_wei(w3.eth.get_balance(deployer_address), 'ether')} ETH")
print("=" * 70)

# Get existing addresses
weth_address = config['addresses']['WETH']
factory_address = config['addresses']['Factory']

print(f"\nUsing existing contracts:")
print(f"  WETH:    {weth_address}")
print(f"  Factory: {factory_address}")

# Load Router artifact
router_path = Path("../pancake-swap-periphery/build/PancakeRouter.sol/PancakeRouter.json")
if not router_path.exists():
    print("\n❌ PancakeRouter.json not found!")
    print("   Run: cd ../pancake-swap-periphery && forge build --force")
    exit(1)

with open(router_path) as f:
    router_artifact = json.load(f)

# Extract bytecode
router_bytecode = router_artifact['bytecode']
if isinstance(router_bytecode, dict):
    router_bytecode = router_bytecode['object']

if not router_bytecode.startswith('0x'):
    router_bytecode = '0x' + router_bytecode

print(f"\nRouter bytecode length: {len(router_bytecode)} bytes")
print(f"\n✅ Press Enter to deploy Router...")
input()

# Deploy Router
print("\n📦 Deploying PancakeRouter...")

contract = w3.eth.contract(abi=router_artifact['abi'], bytecode=router_bytecode)
construct_txn = contract.constructor(factory_address, weth_address)

# Estimate gas
try:
    gas_estimate = construct_txn.estimate_gas({'from': deployer_address})
    gas_limit = int(gas_estimate * 1.2)
    print(f"   Gas estimate: {gas_estimate}")
except Exception as e:
    print(f"   ⚠️  Gas estimation failed: {e}")
    gas_limit = 8000000

# Build transaction
txn = construct_txn.build_transaction({
    'from': deployer_address,
    'nonce': w3.eth.get_transaction_count(deployer_address),
    'gas': gas_limit,
    'gasPrice': w3.to_wei(0.001, 'gwei'),
    'chainId': L2_CHAIN_ID,
})

# Sign and send
signed_txn = w3.eth.account.sign_transaction(txn, deployer.key)
tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

print(f"   TX: {tx_hash.hex()}")
print(f"   ⏳ Waiting for confirmation...")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

if receipt['status'] == 1:
    router_address = receipt['contractAddress']
    print(f"   ✅ Router deployed at: {router_address}")
else:
    print(f"   ❌ Deployment failed!")
    exit(1)

# Update configuration
config['addresses']['Router'] = router_address

# Save updated configuration
with open('deployed_addresses.json', 'w') as f:
    json.dump(config, f, indent=2)

print("\n" + "=" * 70)
print("✅ Router redeployed successfully!")
print("=" * 70)
print(f"New Router address: {router_address}")
print("\n✅ deployed_addresses.json updated")

print("\n" + "=" * 70)
print("Next Steps:")
print("=" * 70)
print("1. Test liquidity addition:")
print("   python3 test_router_stepbystep.py")
print("\n2. If successful, update blockchain.py with new Router address")
print("\n3. Run TPS test:")
print("   ./run_synchronized_test.sh")
