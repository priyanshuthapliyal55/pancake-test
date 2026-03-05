#!/usr/bin/env python3
"""
Step-by-step debugging of addLiquidityETH
Test each component individually
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

print("Step-by-step Router Testing")
print("=" * 70)

weth_address = addresses['WETH']
router_address = addresses['Router']
factory_address = addresses['Factory']
cake_address = config.get('CAKE', addresses.get('CAKE'))

# ABIs
WETH_ABI = [
    {"constant": False, "inputs": [], "name": "deposit", "outputs": [], "payable": True, "type": "function"},
    {"constant": True, "inputs": [{"name": "", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "guy", "type": "address"}, {"name": "wad", "type": "uint"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "dst", "type": "address"}, {"name": "wad", "type": "uint"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
]

ERC20_ABI = [
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "", "type": "address"}, {"name": "", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
]

PAIR_ABI = [
    {"constant": True, "inputs": [], "name": "getReserves", "outputs": [{"name": "reserve0", "type": "uint112"}, {"name": "reserve1", "type": "uint112"}, {"name": "blockTimestampLast", "type": "uint32"}], "type": "function"},
]

FACTORY_ABI = [
    {"constant": True, "inputs": [{"name": "", "type": "address"}, {"name": "", "type": "address"}], "name": "getPair", "outputs": [{"name": "", "type": "address"}], "type": "function"},
]

weth = w3.eth.contract(address=weth_address, abi=WETH_ABI)
cake = w3.eth.contract(address=cake_address, abi=ERC20_ABI)
factory = w3.eth.contract(address=factory_address, abi=FACTORY_ABI)

# Get pair
pair_address = factory.functions.getPair(weth_address, cake_address).call()
pair = w3.eth.contract(address=pair_address, abi=PAIR_ABI)

print(f"\nTest amounts: 0.01 ETH + 10 CAKE\n")

eth_amount = w3.to_wei(0.01, 'ether')
cake_amount = w3.to_wei(10, 'ether')

# Step 1: Try wrapping ETH manually
print("Step 1: Test WETH.deposit() manually")
print("-" * 70)
try:
    gas = weth.functions.deposit().estimate_gas({
        'from': deployer_address,
        'value': eth_amount
    })
    print(f"✅ WETH.deposit() gas estimate: {gas}")
    
    # Actually deposit
    tx = weth.functions.deposit().build_transaction({
        'from': deployer_address,
        'nonce': w3.eth.get_transaction_count(deployer_address),
        'gas': gas + 10000,
        'gasPrice': w3.to_wei(0.001, 'gwei'),
        'chainId': L2_CHAIN_ID,
        'value': eth_amount
    })
    
    signed = w3.eth.account.sign_transaction(tx, deployer.key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt['status'] == 1:
        weth_balance = weth.functions.balanceOf(deployer_address).call()
        print(f"✅ Successfully deposited! WETH balance: {w3.from_wei(weth_balance, 'ether')} WETH")
    else:
        print(f"❌ Deposit failed")
        exit(1)
        
except Exception as e:
    print(f"❌ WETH deposit failed: {e}")
    exit(1)

# Step 2: Approve WETH to Router
print("\nStep 2: Approve WETH to Router")
print("-" * 70)
try:
    weth_balance = weth.functions.balanceOf(deployer_address).call()
    
    tx = weth.functions.approve(router_address, weth_balance).build_transaction({
        'from': deployer_address,
        'nonce': w3.eth.get_transaction_count(deployer_address),
        'gas': 100000,
        'gasPrice': w3.to_wei(0.001, 'gwei'),
        'chainId': L2_CHAIN_ID,
    })
    
    signed = w3.eth.account.sign_transaction(tx, deployer.key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt['status'] == 1:
        print(f"✅ WETH approved to Router")
    else:
        print(f"❌ Approval failed")
        exit(1)
        
except Exception as e:
    print(f"❌ WETH approval failed: {e}")
    exit(1)

# Step 3: Try addLiquidity (not addLiquidityETH) with WETH
print("\nStep 3: Test Router.addLiquidity() with WETH + CAKE")
print("-" * 70)

# Load Router ABI
with open('../pancake-swap-periphery/build/PancakeRouter.sol/PancakeRouter.json') as f:
    router_artifact = json.load(f)

router = w3.eth.contract(address=router_address, abi=router_artifact['abi'])

# Make sure CAKE is also approved
cake_allowance = cake.functions.allowance(deployer_address, router_address).call()
if cake_allowance < cake_amount:
    print("Approving CAKE first...")
    tx = cake.functions.approve(router_address, cake_amount * 10).build_transaction({
        'from': deployer_address,
        'nonce': w3.eth.get_transaction_count(deployer_address),
        'gas': 100000,
        'gasPrice': w3.to_wei(0.001, 'gwei'),
        'chainId': L2_CHAIN_ID,
    })
    
    signed = w3.eth.account.sign_transaction(tx, deployer.key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("✅ CAKE approved")

deadline = int(time.time()) + 3600

try:
    # Use regular addLiquidity with WETH instead of ETH
    gas = router.functions.addLiquidity(
        weth_address,
        cake_address,
        eth_amount,  # Using the WETH we just wrapped
        cake_amount,
        0,  # amountAMin
        0,  # amountBMin
        deployer_address,
        deadline
    ).estimate_gas({
        'from': deployer_address
    })
    
    print(f"✅ Router.addLiquidity() gas estimate: {gas}")
    print(f"   This means addLiquidity logic is working!")
    
    # Actually add liquidity
    tx = router.functions.addLiquidity(
        weth_address,
        cake_address,
        eth_amount,
        cake_amount,
        0,
        0,
        deployer_address,
        deadline
    ).build_transaction({
        'from': deployer_address,
        'nonce': w3.eth.get_transaction_count(deployer_address),
        'gas': int(gas * 1.5),
        'gasPrice': w3.to_wei(0.001, 'gwei'),
        'chainId': L2_CHAIN_ID,
    })
    
    signed = w3.eth.account.sign_transaction(tx, deployer.key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"TX: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt['status'] == 1:
        print(f"✅ SUCCESS! Liquidity added via addLiquidity()")
        print(f"   Gas used: {receipt['gasUsed']}")
        
        reserves = pair.functions.getReserves().call()
        print(f"   New reserves: {reserves[0]}, {reserves[1]}")
        
        print("\n" + "=" * 70)
        print("CONCLUSION:")
        print("=" * 70)
        print("✅ Router.addLiquidity() works perfectly")
        print("❌ Router.addLiquidityETH() is broken")
        print("\nThis means there's a bug in the addLiquidityETH function")
        print("or the way it wraps ETH to WETH internally.")
        print("\nWorkaround: Use addLiquidity() with pre-wrapped WETH")
    else:
        print(f"❌ addLiquidity failed")
        
except Exception as e:
    print(f"❌ addLiquidity failed: {str(e)[:300]}")
    print("\nIf this also fails, the issue is in the core addLiquidity logic")
