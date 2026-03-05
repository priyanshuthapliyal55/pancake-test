#!/usr/bin/env python3
"""Check if WETH has required functions"""

import json
from web3 import Web3

# Load configuration
with open('deployed_addresses.json') as f:
    config = json.load(f)

L2_RPC_URL = config['rpc_url']
weth_address = config['addresses']['WETH']

w3 = Web3(Web3.HTTPProvider(L2_RPC_URL))

print("Checking WETH contract")
print("=" * 70)
print(f"WETH Address: {weth_address}\n")

# Load WETH artifact to check ABI
try:
    with open('../build/WBNB.sol') as f:
        print("Found WBNB.sol source file")
except:
    print("WBNB.sol source not found")

# Try to call deposit
WETH_ABI = [
    {"constant": False, "inputs": [], "name": "deposit", "outputs": [], "payable": True, "type": "function"},
    {"constant": False, "inputs": [{"name": "wad", "type": "uint"}], "name": "withdraw", "outputs": [], "type": "function"},
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
]

weth = w3.eth.contract(address=weth_address, abi=WETH_ABI)

print("Testing WETH functions:\n")

# Test name/symbol
try:
    name = weth.functions.name().call()
    print(f"✅ name(): {name}")
except Exception as e:
    print(f"❌ name() failed: {e}")

try:
    symbol = weth.functions.symbol().call()
    print(f"✅ symbol(): {symbol}")
except Exception as e:
    print(f"❌ symbol() failed: {e}")

# Test deposit (just estimate gas, don't actually call)
try:
    from eth_account import Account
    with open('mnemonic.txt') as f:
        mnemonic = f.read().strip()
    Account.enable_unaudited_hdwallet_features()
    deployer = Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")
    deployer_address = deployer.address
    
    gas = weth.functions.deposit().estimate_gas({
        'from': deployer_address,
        'value': w3.to_wei(0.01, 'ether')
    })
    print(f"✅ deposit() exists and can be called (gas estimate: {gas})")
except Exception as e:
    print(f"❌ deposit() failed: {str(e)[:200]}")
    print("\n⚠️  WETH doesn't have deposit() function!")
    print("This is required for Router.addLiquidityETH to work")
    print("\nThe Router expects WETH9 standard with:")
    print("  - deposit() payable")
    print("  - withdraw(uint)")

print("\n" + "=" * 70)
print("Checking bytecode of deployed WETH...")

code = w3.eth.get_code(weth_address).hex()
print(f"Bytecode length: {len(code)} bytes")

# Check if deposit() selector (0xd0e30db0) is in bytecode
deposit_selector = "d0e30db0"
if deposit_selector in code:
    print(f"✅ deposit() selector found in bytecode")
else:
    print(f"❌ deposit() selector NOT found in bytecode")
    print("   This WETH contract is missing the deposit function!")

# Check if withdraw() selector (0x2e1a7d4d) is in bytecode
withdraw_selector = "2e1a7d4d"
if withdraw_selector in code:
    print(f"✅ withdraw() selector found in bytecode")
else:
    print(f"❌ withdraw() selector NOT found in bytecode")

print("\n" + "=" * 70)
print("Solution:")
print("=" * 70)
print("If deposit() is missing, you need to redeploy WETH using WETH9.sol")
print("The current WETH might be WBNB which has different interface.")
print("\nRun: python3 redeploy_weth.py")
