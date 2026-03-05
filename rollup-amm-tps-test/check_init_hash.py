#!/usr/bin/env python3
"""
Get the INIT_CODE_HASH from the deployed Factory
This must match the hardcoded value in PancakeLibrary
"""

import json
from web3 import Web3

# Load configuration
with open('deployed_addresses.json') as f:
    config = json.load(f)

L2_RPC_URL = config['rpc_url']
factory_address = config['addresses']['Factory']

w3 = Web3(Web3.HTTPProvider(L2_RPC_URL))

print("Checking Factory INIT_CODE_HASH")
print("=" * 70)
print(f"Factory: {factory_address}\n")

# Load Factory ABI
with open('../pancake-swap-core/build/PancakeFactory.sol/PancakeFactory.json') as f:
    factory_artifact = json.load(f)

factory = w3.eth.contract(address=factory_address, abi=factory_artifact['abi'])

# Get INIT_CODE_PAIR_HASH
try:
    init_hash = factory.functions.INIT_CODE_PAIR_HASH().call()
    print(f"✅ Factory's INIT_CODE_PAIR_HASH:")
    print(f"   {init_hash.hex()}\n")
except Exception as e:
    print(f"❌ Could not read INIT_CODE_PAIR_HASH: {e}")
    print("\nThe Factory might not have this getter function.")
    print("Let me calculate it from PancakePair bytecode...\n")
    
    # Calculate from PancakePair bytecode
    with open('../pancake-swap-core/build/PancakePair.sol/PancakePair.json') as f:
        pair_artifact = json.load(f)
    
    bytecode = pair_artifact['bytecode']
    if isinstance(bytecode, dict):
        bytecode = bytecode['object']
    
    if not bytecode.startswith('0x'):
        bytecode = '0x' + bytecode
    
    # Calculate keccak256 hash
    init_hash = Web3.keccak(hexstr=bytecode)
    print(f"✅ Calculated INIT_CODE_HASH from PancakePair bytecode:")
    print(f"   {init_hash.hex()}\n")

# Check what's in PancakeLibrary
print("Checking PancakeLibrary.sol...")
print("-" * 70)

with open('../pancake-swap-periphery/contracts/libraries/PancakeLibrary.sol') as f:
    content = f.read()
    
    # Find the hex line
    for i, line in enumerate(content.split('\n'), 1):
        if 'hex' in line and len(line) > 50:
            print(f"Line {i}: {line.strip()}")

print("\n" + "=" * 70)
print("ISSUE FOUND:")
print("=" * 70)
print(f"The hardcoded hash in PancakeLibrary is:")
print(f"  0xd0d4c4cd0848c93cb4fd1f498d7013ee6bfb25783ea21593d5834f5d250ece66")
print(f"\nYour Factory's actual hash is:")
print(f"  {init_hash.hex()}")

if init_hash.hex() != '0xd0d4c4cd0848c93cb4fd1f498d7013ee6bfb25783ea21593d5834f5d250ece66':
    print(f"\n❌ MISMATCH! This is why addLiquidity() fails.")
    print(f"\nThe Router calculates the pair address using the wrong hash,")
    print(f"so it tries to interact with the wrong contract address.")
    print(f"\n{'='*70}")
    print("FIX:")
    print('='*70)
    print(f"\nUpdate PancakeLibrary.sol line 24:")
    print(f"  hex'{init_hash.hex()[2:]}' // init code hash")
    print(f"\nThen recompile and redeploy the Router:")
    print(f"  cd ../pancake-swap-periphery")
    print(f"  forge build --force")
    print(f"  # Update deploy_l2.py with new Router address")
else:
    print(f"\n✅ Hash matches! The issue is elsewhere.")
