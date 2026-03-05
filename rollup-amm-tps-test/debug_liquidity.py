#!/usr/bin/env python3
"""Debug script to check why addLiquidityETH is failing"""

import json
from web3 import Web3
from eth_account import Account
from pathlib import Path

# Load configuration
L2_RPC_URL = "http://localhost:8545"
L2_CHAIN_ID =  

w3 = Web3(Web3.HTTPProvider(L2_RPC_URL))

# Load deployer account
with open('mnemonic.txt') as f:
    mnemonic = f.read().strip()
Account.enable_unaudited_hdwallet_features()
deployer = Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")
deployer_address = deployer.address

print(f"Checking deployment for: {deployer_address}")
print(f"Balance: {w3.from_wei(w3.eth.get_balance(deployer_address), 'ether')} ETH\n")

# Load deployed addresses
with open('deployed_addresses.json') as f:
    config = json.load(f)

addresses = config.get('addresses', {})
cake_address = config.get('CAKE', addresses.get('CAKE'))
weth_address = addresses.get('WETH')
router_address = addresses.get('Router')
factory_address = addresses.get('Factory')

print(f"WETH: {weth_address}")
print(f"Factory: {factory_address}")
print(f"Router: {router_address}")
print(f"CAKE: {cake_address}\n")

# Simple ABI for checking
SIMPLE_ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "", "type": "address"}, {"name": "", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
]

# Check CAKE balance and allowance
cake_contract = w3.eth.contract(address=cake_address, abi=SIMPLE_ERC20_ABI)
cake_balance = cake_contract.functions.balanceOf(deployer_address).call()
cake_allowance = cake_contract.functions.allowance(deployer_address, router_address).call()

print(f"CAKE Balance: {w3.from_wei(cake_balance, 'ether')} CAKE")
print(f"CAKE Allowance to Router: {w3.from_wei(cake_allowance, 'ether')} CAKE\n")

# Check Router's WETH address
router_abi = [
    {"constant": True, "inputs": [], "name": "WETH", "outputs": [{"name": "", "type": "address"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "factory", "outputs": [{"name": "", "type": "address"}], "type": "function"},
]

router_contract = w3.eth.contract(address=router_address, abi=router_abi)
router_weth = router_contract.functions.WETH().call()
router_factory = router_contract.functions.factory().call()

print(f"Router's WETH address: {router_weth}")
print(f"Router's Factory address: {router_factory}\n")

if router_weth.lower() != weth_address.lower():
    print("❌ ERROR: Router's WETH address doesn't match deployed WETH!")
    print(f"   Expected: {weth_address}")
    print(f"   Got:      {router_weth}")

if router_factory.lower() != factory_address.lower():
    print("❌ ERROR: Router's Factory address doesn't match deployed Factory!")
    print(f"   Expected: {factory_address}")
    print(f"   Got:      {router_factory}")

# Check if pair exists
factory_abi = [
    {"constant": True, "inputs": [{"name": "", "type": "address"}, {"name": "", "type": "address"}], "name": "getPair", "outputs": [{"name": "", "type": "address"}], "type": "function"},
]

factory_contract = w3.eth.contract(address=factory_address, abi=factory_abi)
pair_address = factory_contract.functions.getPair(weth_address, cake_address).call()

print(f"\nWETH/CAKE Pair: {pair_address}")
if pair_address == "0x0000000000000000000000000000000000000000":
    print("❌ ERROR: Pair doesn't exist! Need to create it first.")
else:
    print("✅ Pair exists")

print("\n" + "="*70)
print("Suggested fix:")
print("="*70)
if router_weth.lower() != weth_address.lower():
    print("1. Redeploy Router with correct WETH address")
elif pair_address == "0x0000000000000000000000000000000000000000":
    print("1. Create the pair first with factory.createPair()")
elif cake_allowance == 0:
    print("1. Approve Router to spend CAKE tokens")
elif cake_balance < w3.to_wei(1000, 'ether'):
    print("1. Deploy CAKE token or get more CAKE balance")
else:
    print("1. Check Router contract code for bugs")
    print("2. Try with smaller amounts (0.1 ETH + 100 CAKE)")
