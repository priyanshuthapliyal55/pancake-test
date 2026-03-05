#!/usr/bin/env python3
"""
Simplified Deployment Script using Foundry compiled artifacts
"""

import json
import time
from web3 import Web3
from eth_account import Account
from pathlib import Path


# =============================================================================
# CONFIGURATION
# =============================================================================

L2_RPC_URL = "http://46.165.235.105:8545"
L2_CHAIN_ID = 11155111
L2_NAME = "MY_L2"
GAS_PRICE_GWEI = 0.001
MAX_GAS = 8000000

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
    print(f"   RPC: {L2_RPC_URL}")
    print("   Make sure your L2 is running and accessible")
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
    exit(1)

input("\n✅ Press Enter to start deployment...")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_contract_artifact(path):
    """Load compiled contract from Foundry build output"""
    with open(path) as f:
        artifact = json.load(f)
    
    # Foundry stores ABI and bytecode differently than Truffle
    if 'abi' in artifact:
        abi = artifact['abi']
    else:
        # Might be in different format
        abi = artifact.get('metadata', {}).get('output', {}).get('abi', [])
    
    bytecode = artifact.get('bytecode', {}).get('object', '')
    if not bytecode or bytecode == '0x':
        bytecode = artifact.get('evm', {}).get('bytecode', {}).get('object', '')
    
    return abi, bytecode


def deploy_contract(name, abi, bytecode, constructor_args=None, value=0):
    """Deploy a contract"""
    print(f"\n📦 Deploying {name}...")
    
    # Ensure bytecode has 0x prefix
    if not bytecode.startswith('0x'):
        bytecode = '0x' + bytecode
    
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Build constructor transaction
    if constructor_args:
        construct_txn = contract.constructor(*constructor_args)
    else:
        construct_txn = contract.constructor()
    
    # Build transaction
    try:
        gas_estimate = construct_txn.estimate_gas({
            'from': deployer_address,
            'value': value
        })
        gas_limit = int(gas_estimate * 1.3)
    except Exception as e:
        print(f"   ⚠️  Gas estimation failed: {e}")
        gas_limit = MAX_GAS
    
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
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
    print(f"   TX: {tx_hash.hex()}")
    print(f"   ⏳ Waiting for confirmation...")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    
    if receipt['status'] == 1:
        print(f"   ✅ {name} deployed at: {receipt['contractAddress']}")
        return receipt['contractAddress']
    else:
        print(f"   ❌ Deployment failed!")
        exit(1)


# =============================================================================
# DEPLOYMENT
# =============================================================================

deployed_addresses = {}

# Step 1: Find and load compiled contracts
print("\n" + "=" * 70)
print("Loading compiled contracts...")
print("=" * 70)

core_build = Path("../pancake-swap-core/build")
periphery_build = Path("../pancake-swap-periphery/build")

# Load WETH from our compiled version
weth_path = Path("out/WETH.sol/WETH.json")
if weth_path.exists():
    weth_abi, weth_bytecode = load_contract_artifact(weth_path)
    print(f"✅ Loaded WETH from compiled artifact")
else:
    print("❌ WETH.sol not compiled. Run: forge build WETH.sol --use 0.5.16")
    exit(1)

# Load Factory
factory_path = list(core_build.glob("**/PancakeFactory.json"))[0]
factory_abi, factory_bytecode = load_contract_artifact(factory_path)
print(f"✅ Loaded PancakeFactory")

# Load Router
router_path = list(periphery_build.glob("**/PancakeRouter.json"))[0]
router_abi, router_bytecode = load_contract_artifact(router_path)
print(f"✅ Loaded PancakeRouter")

# Deploy WETH
print("\n" + "=" * 70)
print("STEP 1: Deploy WETH")
print("=" * 70)
weth_address = deploy_contract("WETH", weth_abi, weth_bytecode)
deployed_addresses['WETH'] = weth_address
time.sleep(2)

# Deploy Factory
print("\n" + "=" * 70)
print("STEP 2: Deploy PancakeFactory")
print("=" * 70)
factory_address = deploy_contract(
    "PancakeFactory",
    factory_abi,
    factory_bytecode,
    constructor_args=[deployer_address]
)
deployed_addresses['Factory'] = factory_address
time.sleep(2)

# Deploy Router
print("\n" + "=" * 70)
print("STEP 3: Deploy PancakeRouter")
print("=" * 70)
router_address = deploy_contract(
    "PancakeRouter",
    router_abi,
    router_bytecode,
    constructor_args=[factory_address, weth_address]
)
deployed_addresses['Router'] = router_address
time.sleep(2)

# Save results
print("\n" + "=" * 70)
print("🎉 DEPLOYMENT COMPLETE!")
print("=" * 70)

for name, address in deployed_addresses.items():
    print(f"{name:20} : {address}")

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

print("\n" + "=" * 70)
print("UPDATE blockchain.py:")
print("=" * 70)
print(f"""
ChainId.{L2_NAME} = {L2_CHAIN_ID}

# Add to BlockchainData.NETWORKS:
ChainId.{L2_NAME}: NetworkData(
    chain_id={L2_CHAIN_ID},
    http_rpc_url='{L2_RPC_URL}',
    ws_rpc_url='wss://your-l2-ws-url',
    addresses={{
        Contract.PANCAKE_SMART_ROUTER: '{deployed_addresses.get("Router", "0x...")}',
        Token.CAKE: '0xYourCakeTokenAddress',  # Deploy separately
        Token.WETH: '{deployed_addresses.get("WETH", "0x...")}',
    }},
),
""")

print("\n" + "=" * 70)
print("NEXT STEPS:")
print("=" * 70)
print("1. Deploy CAKE token (use Remix or separate script)")
print("2. Create WETH/CAKE pair using Factory.createPair()")
print("3. Add liquidity via Router.addLiquidityETH()")
print("4. Update blockchain.py with all addresses")
print("5. Run: python3 prepare.py")
print("6. Run: python3 tps_test.py -n 0")
print("=" * 70)
