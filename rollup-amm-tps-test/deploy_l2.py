#!/usr/bin/env python3
"""
Complete Deployment Script for L2 TPS Testing
Deploys: WETH, Factory, Router, CAKE Token, and sets up liquidity pool
"""

import json
import time
from web3 import Web3
from eth_account import Account
from pathlib import Path


# =============================================================================
# CONFIGURATION - UPDATE THESE FOR YOUR L2
# =============================================================================

# Your L2 Configuration
L2_RPC_URL = "http://localhost:8545"  # Change this
L2_CHAIN_ID = 1376  # Change this to your L2 chain ID
L2_NAME = "MY_L2"  # Change this to your L2 name

# Gas settings (adjust for your L2)
GAS_PRICE_GWEI = 0.001  # Adjust based on your L2
MAX_GAS = 8000000

# Liquidity amounts (adjust as needed)
INITIAL_ETH_LIQUIDITY = 0.1  # ETH to add to pool
INITIAL_CAKE_LIQUIDITY = 100  # CAKE tokens to add to pool

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

# Get deployer account
Account.enable_unaudited_hdwallet_features()
deployer = Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")
deployer_address = deployer.address

print("=" * 70)
print("🚀 L2 DEX Deployment Script")
print("=" * 70)
print(f"Network: {L2_NAME}")
print(f"Chain ID: {L2_CHAIN_ID}")
print(f"RPC: {L2_RPC_URL}")
print(f"Deployer: {deployer_address}")

# Check balance
balance = w3.eth.get_balance(deployer_address)
balance_eth = w3.from_wei(balance, 'ether')
print(f"Balance: {balance_eth} ETH")
print("=" * 70)

if balance_eth < 0.1:
    print("\n⚠️  WARNING: You need at least 0.1 ETH for deployment")
    print("   Get testnet/L2 tokens first!")
    exit(1)

input("\n✅ Press Enter to start deployment...")


# =============================================================================
# CONTRACT ABIS AND BYTECODE
# =============================================================================

# Load compiled WETH contract
with open('out/WETH.sol/WETH.json', 'r') as f:
    weth_json = json.load(f)
    WETH9_BYTECODE = weth_json['bytecode']['object'] if isinstance(weth_json['bytecode'], dict) else weth_json['bytecode']
    WETH9_ABI = weth_json['abi']

# Fallback WETH9 ABI if needed
WETH9_ABI_FALLBACK = [
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": False, "inputs": [], "name": "deposit", "outputs": [], "payable": True, "type": "function"},
    {"constant": False, "inputs": [{"name": "wad", "type": "uint256"}], "name": "withdraw", "outputs": [], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "dst", "type": "address"}, {"name": "wad", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "guy", "type": "address"}, {"name": "wad", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"inputs": [], "payable": False, "stateMutability": "nonpayable", "type": "constructor"},
    {"payable": True, "stateMutability": "payable", "type": "fallback"}
]

# Simple ERC20 Token (for CAKE) - Simplified version
SIMPLE_ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "recipient", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"inputs": [{"name": "name_", "type": "string"}, {"name": "symbol_", "type": "string"}, {"name": "initialSupply", "type": "uint256"}], "type": "constructor"}
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def deploy_contract(contract_name, abi, bytecode, constructor_args=None, value=0):
    """Deploy a contract and wait for confirmation"""
    print(f"\n📦 Deploying {contract_name}...")
    
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Build constructor transaction
    if constructor_args:
        construct_txn = contract.constructor(*constructor_args)
    else:
        construct_txn = contract.constructor()
    
    # Estimate gas
    try:
        gas_estimate = construct_txn.estimate_gas({
            'from': deployer_address,
            'value': value
        })
        gas_limit = int(gas_estimate * 1.2)  # 20% buffer
    except Exception as e:
        print(f"   ⚠️  Gas estimation failed: {e}")
        gas_limit = MAX_GAS
    
    # Build transaction
    txn = construct_txn.build_transaction({
        'from': deployer_address,
        'nonce': w3.eth.get_transaction_count(deployer_address),
        'gas': gas_limit,
        'gasPrice': w3.to_wei(GAS_PRICE_GWEI, 'gwei'),
        'chainId': L2_CHAIN_ID,
        'value': value
    })
    
    # Sign and send
    signed_txn = w3.eth.account.sign_transaction(txn, deployer.key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    
    print(f"   TX: {tx_hash.hex()}")
    print(f"   ⏳ Waiting for confirmation...")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    
    if receipt['status'] == 1:
        print(f"   ✅ {contract_name} deployed at: {receipt['contractAddress']}")
        return receipt['contractAddress']
    else:
        print(f"   ❌ Deployment failed!")
        exit(1)


def send_transaction(contract, function_name, *args, value=0):
    """Send a transaction to a contract"""
    print(f"   📤 Calling {function_name}...")
    
    func = getattr(contract.functions, function_name)
    
    # Try to estimate gas first to catch reverts early
    try:
        gas_estimate = func(*args).estimate_gas({
            'from': deployer_address,
            'value': value
        })
        gas_limit = min(int(gas_estimate * 1.5), MAX_GAS)
        print(f"   ⛽ Estimated gas: {gas_estimate}")
    except Exception as e:
        print(f"   ⚠️  Gas estimation failed: {str(e)[:200]}")
        print(f"   This usually means the transaction will revert.")
        print(f"   Attempting anyway with max gas...")
        gas_limit = MAX_GAS
    
    txn = func(*args).build_transaction({
        'from': deployer_address,
        'nonce': w3.eth.get_transaction_count(deployer_address),
        'gas': gas_limit,
        'gasPrice': w3.to_wei(GAS_PRICE_GWEI, 'gwei'),
        'chainId': L2_CHAIN_ID,
        'value': value
    })
    
    signed_txn = w3.eth.account.sign_transaction(txn, deployer.key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    
    if receipt['status'] == 1:
        print(f"   ✅ Success! TX: {tx_hash.hex()}")
        return receipt
    else:
        print(f"   ❌ Transaction failed!")
        print(f"   Gas used: {receipt['gasUsed']} / {gas_limit}")
        return None


# =============================================================================
# DEPLOYMENT STEPS
# =============================================================================

deployed_addresses = {}

# Step 1: Deploy WETH
print("\n" + "=" * 70)
print("STEP 1: Deploy WETH Contract")
print("=" * 70)

weth_address = deploy_contract("WETH9", WETH9_ABI, WETH9_BYTECODE)
deployed_addresses['WETH'] = weth_address
time.sleep(2)


# Step 2: Load and deploy Factory
print("\n" + "=" * 70)
print("STEP 2: Deploy PancakeFactory")
print("=" * 70)

# Load factory bytecode from compiled contracts (Foundry output)
factory_path = Path("../pancake-swap-core/build/PancakeFactory.sol/PancakeFactory.json")
if not factory_path.exists():
    print("❌ PancakeFactory.json not found!")
    print("   Run: cd ../pancake-swap-core && forge build --force")
    exit(1)

with open(factory_path) as f:
    factory_artifact = json.load(f)

# Extract bytecode properly from Foundry format
factory_bytecode = factory_artifact['bytecode']
if isinstance(factory_bytecode, dict):
    factory_bytecode = factory_bytecode['object']

factory_address = deploy_contract(
    "PancakeFactory",
    factory_artifact['abi'],
    factory_bytecode,
    constructor_args=[deployer_address]
)
deployed_addresses['Factory'] = factory_address
time.sleep(2)


# Step 3: Deploy Router
print("\n" + "=" * 70)
print("STEP 3: Deploy PancakeRouter")
print("=" * 70)

router_path = Path("../pancake-swap-periphery/build/PancakeRouter.sol/PancakeRouter.json")
if router_path.exists():
    print("   Loading compiled PancakeRouter...")
    with open(router_path) as f:
        router_artifact = json.load(f)

    # Extract bytecode properly from Foundry format
    router_bytecode = router_artifact['bytecode']
    if isinstance(router_bytecode, dict):
        router_bytecode = router_bytecode['object']

    router_address = deploy_contract(
        "PancakeRouter",
        router_artifact['abi'],
        router_bytecode,
        constructor_args=[factory_address, weth_address]
    )
    deployed_addresses['Router'] = router_address
else:
    print("   ⚠️  PancakeRouter.json not found!")
    print("   The periphery contracts have compilation issues with imports.")
    print("   ")
    print("   Option 1: Deploy Router manually using Remix IDE")
    print("   Option 2: Use existing Router if re-deploying")
    print("   ")
    router_address = input("   Enter PancakeRouter address (or press Enter to skip): ").strip()
    if router_address and router_address.startswith('0x'):
        deployed_addresses['Router'] = router_address
        print(f"   ✅ Using Router at: {router_address}")
    else:
        print("   ⚠️  Skipping Router deployment - you'll need to deploy it separately")
        print("   ❌ Cannot continue without Router. Exiting...")
        exit(1)

time.sleep(2)


# Step 4: Deploy CAKE Token
print("\n" + "=" * 70)
print("STEP 4: Deploy CAKE Test Token")
print("=" * 70)

# Load compiled CAKE token
cake_path = Path("out/CAKEToken.sol/CAKEToken.json")
if cake_path.exists():
    print("   Loading compiled CAKE token...")
    with open(cake_path) as f:
        cake_artifact = json.load(f)
    
    cake_address = deploy_contract(
        "CAKEToken",
        cake_artifact['abi'],
        cake_artifact['bytecode']['object'],
        constructor_args=[]
    )
    deployed_addresses['CAKE'] = cake_address
    print(f"   ✅ CAKE Token deployed successfully!")
else:
    print("   ⚠️  CAKEToken.json not found in out/ directory")
    print("   Compile it with: forge build CAKEToken.sol --use 0.5.16 --evm-version istanbul")
    cake_address = input("\n   Enter deployed CAKE token address (or press Enter to skip): ").strip()
    if cake_address and cake_address.startswith('0x'):
        deployed_addresses['CAKE'] = cake_address
    else:
        print("   ⚠️  Skipping CAKE deployment - you'll need to deploy it separately")
        deployed_addresses['CAKE'] = "0x0000000000000000000000000000000000000000"

time.sleep(2)


# Step 5: Create Pair and Add Liquidity (if CAKE is deployed)
if deployed_addresses['CAKE'] != "0x0000000000000000000000000000000000000000":
    print("\n" + "=" * 70)
    print("STEP 5: Create Pair and Add Liquidity")
    print("=" * 70)
    
    try:
        factory_contract = w3.eth.contract(address=factory_address, abi=factory_artifact['abi'])
        router_contract = w3.eth.contract(address=router_address, abi=router_artifact['abi'])
        cake_contract = w3.eth.contract(address=deployed_addresses['CAKE'], abi=SIMPLE_ERC20_ABI)
        
        # Create pair
        print("\n   Creating WETH/CAKE pair...")
        result = send_transaction(factory_contract, 'createPair', weth_address, deployed_addresses['CAKE'])
        
        if result is None:
            print("   ⚠️  Failed to create pair - it may already exist")
        
        # Get pair address
        pair_address = factory_contract.functions.getPair(weth_address, deployed_addresses['CAKE']).call()
        print(f"   ✅ Pair exists at: {pair_address}")
        deployed_addresses['WETH_CAKE_PAIR'] = pair_address
        
        # Approve router to spend CAKE
        cake_amount = w3.to_wei(INITIAL_CAKE_LIQUIDITY, 'ether')
        print(f"\n   Approving router to spend {INITIAL_CAKE_LIQUIDITY} CAKE...")
        result = send_transaction(cake_contract, 'approve', router_address, cake_amount)
        
        if result is None:
            raise Exception("Failed to approve CAKE")
        
        # Add liquidity
        eth_amount = w3.to_wei(INITIAL_ETH_LIQUIDITY, 'ether')
        deadline = int(time.time()) + 3600  # 1 hour from now
        
        print(f"\n   Adding liquidity: {INITIAL_ETH_LIQUIDITY} ETH + {INITIAL_CAKE_LIQUIDITY} CAKE...")
        result = send_transaction(
            router_contract,
            'addLiquidityETH',
            deployed_addresses['CAKE'],  # token
            cake_amount,  # amountTokenDesired
            0,  # amountTokenMin
            0,  # amountETHMin
            deployer_address,  # to
            deadline,  # deadline
            value=eth_amount
        )
        
        if result:
            print("   ✅ Liquidity added successfully!")
        else:
            print("   ⚠️  Liquidity addition failed")
            print("   You can add it manually later using the Router contract")
            
    except Exception as e:
        print(f"\n   ⚠️  Liquidity setup encountered an error: {e}")
        print("   Continuing with deployment - you can add liquidity manually later")



# =============================================================================
# SAVE RESULTS
# =============================================================================

print("\n" + "=" * 70)
print("🎉 DEPLOYMENT COMPLETE!")
print("=" * 70)

for name, address in deployed_addresses.items():
    print(f"{name:20} : {address}")

# Save to file
config = {
    'network': L2_NAME,
    'chain_id': L2_CHAIN_ID,
    'rpc_url': L2_RPC_URL,
    'addresses': deployed_addresses,
    'deployer': deployer_address
}

with open('deployed_addresses.json', 'w') as f:
    json.dump(config, f, indent=2)

print("\n✅ Addresses saved to deployed_addresses.json")

# Print blockchain.py update
print("\n" + "=" * 70)
print("UPDATE blockchain.py with:")
print("=" * 70)

print(f"""
class ChainId(enum.Enum):
    # ... existing chains ...
    {L2_NAME} = {L2_CHAIN_ID}

# Add to BlockchainData.NETWORKS:
ChainId.{L2_NAME}: NetworkData(
    chain_id={L2_CHAIN_ID},
    http_rpc_url='{L2_RPC_URL}',
    ws_rpc_url='wss://your-l2-ws-url',  # Update with WS URL
    addresses={{
        Contract.PANCAKE_SMART_ROUTER: '{deployed_addresses.get("Router", "0x...")}',
        Token.CAKE: '{deployed_addresses.get("CAKE", "0x...")}',
        Token.WETH: '{deployed_addresses.get("WETH", "0x...")}',
    }},
),
""")

print("\n" + "=" * 70)
print("NEXT STEPS:")
print("=" * 70)
print("1. Update blockchain.py with the addresses above")
print("2. Run: python prepare.py (to fund test accounts)")
print("3. Run: python tps_test.py -n 0 (to test)")
print("=" * 70)
