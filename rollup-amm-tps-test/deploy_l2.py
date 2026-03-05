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
L2_RPC_URL = "http://46.165.235.105:8545"  # Change this
L2_CHAIN_ID = 11155111  # Change this to your L2 chain ID
L2_NAME = "MY_L2"  # Change this to your L2 name

# Gas settings (adjust for your L2)
GAS_PRICE_GWEI = 0.001  # Adjust based on your L2
MAX_GAS = 8000000

# Liquidity amounts (adjust as needed)
INITIAL_ETH_LIQUIDITY = 0.5  # ETH to add to pool
INITIAL_CAKE_LIQUIDITY = 1000  # CAKE tokens to add to pool

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

# Simplified WETH9 ABI and Bytecode
WETH9_ABI = [
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

WETH9_BYTECODE = "0x60806040526040518060400160405280600b81526020017f5772617070656420424e420000000000000000000000000000000000000000008152506000908051906020019061004f929190610062565b5060006001555034801561006257600080fd5b50610107565b828054600181600116156101000203166002900490600052602060002090601f016020900481019282601f106100a357805160ff19168380011785556100d1565b828001600101855582156100d1579182015b828111156100d05782518255916020019190600101906100b5565b5b5090506100de91906100e2565b5090565b61010491905b808211156101005760008160009055506001016100e8565b5090565b90565b6107e6806101166000396000f3fe6080604052600436106100555760003560e01c8063095ea7b31461005a57806318160ddd146100c757806323b872dd146100f25780632e1a7d4d14610185578063313ce567146101c057806370a08231146101ee57806395d89b4114610253578063a9059cbb146102e3578063d0e30db014610356578063dd62ed3e14610360575b600080fd5b34801561006657600080fd5b506100ad6004803603604081101561007d57600080fd5b81019080803573ffffffffffffffffffffffffffffffffffffffff169060200190929190803590602001909291905050506103e5565b604051808215151515815260200191505060405180910390f35b3480156100d357600080fd5b506100dc6104d7565b6040518082815260200191505060405180910390f35b3480156100fe57600080fd5b5061016b6004803603606081101561011557600080fd5b81019080803573ffffffffffffffffffffffffffffffffffffffff169060200190929190803573ffffffffffffffffffffffffffffffffffffffff169060200190929190803590602001909291905050506104dd565b604051808215151515815260200191505060405180910390f35b34801561019157600080fd5b506101be600480360360208110156101a857600080fd5b8101908080359060200190929190505050610748565b005b3480156101cc57600080fd5b506101d5610850565b604051808260ff1660ff16815260200191505060405180910390f35b3480156101fa57600080fd5b5061023d6004803603602081101561021157600080fd5b81019080803573ffffffffffffffffffffffffffffffffffffffff169060200190929190505050610855565b6040518082815260200191505060405180910390f35b34801561025f57600080fd5b5061026861086d565b6040518080602001828103825283818151815260200191508051906020019080838360005b838110156102a857808201518184015260208101905061028d565b50505050905090810190601f1680156102d55780820380516001836020036101000a031916815260200191505b509250505060405180910390f35b3480156102ef57600080fd5b5061033c6004803603604081101561030657600080fd5b81019080803573ffffffffffffffffffffffffffffffffffffffff1690602001909291908035906020019092919050505061090b565b604051808215151515815260200191505060405180910390f35b61035e61091f565b005b34801561036c57600080fd5b506103cf6004803603604081101561038357600080fd5b81019080803573ffffffffffffffffffffffffffffffffffffffff169060200190929190803573ffffffffffffffffffffffffffffffffffffffff16906020019092919050505061098e565b6040518082815260200191505060405180910390f35b600081600360003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002060008573ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020819055508273ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff167f8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925846040518082815260200191505060405180910390a36001905092915050565b60015490565b60008060003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002054821115151561052c57600080fd5b600360008573ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002060003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000205482111515156105b757600080fd5b816000808673ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020600082825401925050819055506106588260008086815260200190815260200160002060003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020546109b390919063ffffffff16565b60008085815260200190815260200160002060003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020819055508273ffffffffffffffffffffffffffffffffffffffff168473ffffffffffffffffffffffffffffffffffffffff167fddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef846040518082815260200191505060405180910390a3600190509392505050565b806000803373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002054101515156107b5576040517f08c379a000000000000000000000000000000000000000000000000000000000815260040180806020018281038252602b8152602001807f5772617070656420424e423a20696e73756666696369656e742062616c616e6381526020017f6520666f72207769746864726177616c00000000000000000000000000000000815250604001915050600a09150fd5b806000803373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020600082825403925050819055503373ffffffffffffffffffffffffffffffffffffffff166108fc829081150290604051600060405180830381858888f1935050505015801561084d573d6000803e3d6000fd5b50565b601290565b60026020528060005260406000206000915090505481565b60008054600181600116156101000203166002900480601f0160208091040260200160405190810160405280929190818152602001828054600181600116156101000203166002900480156109035780601f106108d857610100808354040283529160200191610903565b820191906000526020600020905b8154815290600101906020018083116108e657829003601f168201915b505050505081565b60006109183384846104dd565b9050929150505056fea265627a7a723158202d9f5f61f6f0e5d7cf6c3e6e9e5e9c5e8e6e0f5e5e9e7e7e7e7e7e7e7e7e7e7e64736f6c634300050c0032"

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
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
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
    txn = func(*args).build_transaction({
        'from': deployer_address,
        'nonce': w3.eth.get_transaction_count(deployer_address),
        'gas': MAX_GAS,
        'gasPrice': w3.to_wei(GAS_PRICE_GWEI, 'gwei'),
        'chainId': L2_CHAIN_ID,
        'value': value
    })
    
    signed_txn = w3.eth.account.sign_transaction(txn, deployer.key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    
    if receipt['status'] == 1:
        print(f"   ✅ Success! TX: {tx_hash.hex()}")
        return receipt
    else:
        print(f"   ❌ Transaction failed!")
        exit(1)


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

# Load factory bytecode from compiled contracts
factory_path = Path("../pancake-swap-core/build/contracts/PancakeFactory.json")
if not factory_path.exists():
    print("❌ PancakeFactory.json not found!")
    print("   Run: cd ../pancake-swap-core && npm install && npx truffle compile")
    exit(1)

with open(factory_path) as f:
    factory_artifact = json.load(f)

factory_address = deploy_contract(
    "PancakeFactory",
    factory_artifact['abi'],
    factory_artifact['bytecode'],
    constructor_args=[deployer_address]
)
deployed_addresses['Factory'] = factory_address
time.sleep(2)


# Step 3: Deploy Router
print("\n" + "=" * 70)
print("STEP 3: Deploy PancakeRouter")
print("=" * 70)

router_path = Path("../pancake-swap-periphery/build/contracts/PancakeRouter.json")
if not router_path.exists():
    print("❌ PancakeRouter.json not found!")
    print("   Run: cd ../pancake-swap-periphery && npm install && npx truffle compile")
    exit(1)

with open(router_path) as f:
    router_artifact = json.load(f)

router_address = deploy_contract(
    "PancakeRouter",
    router_artifact['abi'],
    router_artifact['bytecode'],
    constructor_args=[factory_address, weth_address]
)
deployed_addresses['Router'] = router_address
time.sleep(2)


# Step 4: Deploy CAKE Token
print("\n" + "=" * 70)
print("STEP 4: Deploy CAKE Test Token")
print("=" * 70)

# For simplicity, using a basic ERC20. In production, compile CAKEToken.sol
# Here's a minimal ERC20 bytecode - you can replace with compiled CAKEToken
print("   Note: Using simplified ERC20 token")
print("   For production, compile and use CAKEToken.sol")

cake_path = Path("../build/tokens/CAKEToken.sol")
# We'll need to compile this properly
print(f"   ⚠️  To deploy proper CAKE token, compile {cake_path}")
print(f"   For now, please deploy CAKE token manually or compile CAKEToken.sol")
print(f"   ")
print(f"   Quick option: Use Remix IDE to deploy CAKEToken.sol")

# Placeholder - user needs to provide this
cake_address = input("\n   Enter deployed CAKE token address (or press Enter to skip): ").strip()
if cake_address and cake_address.startswith('0x'):
    deployed_addresses['CAKE'] = cake_address
else:
    print("   ⚠️  Skipping CAKE deployment - you'll need to deploy it separately")
    deployed_addresses['CAKE'] = "0x0000000000000000000000000000000000000000"


# Step 5: Create Pair and Add Liquidity (if CAKE is deployed)
if deployed_addresses['CAKE'] != "0x0000000000000000000000000000000000000000":
    print("\n" + "=" * 70)
    print("STEP 5: Create Pair and Add Liquidity")
    print("=" * 70)
    
    factory_contract = w3.eth.contract(address=factory_address, abi=factory_artifact['abi'])
    router_contract = w3.eth.contract(address=router_address, abi=router_artifact['abi'])
    cake_contract = w3.eth.contract(address=deployed_addresses['CAKE'], abi=SIMPLE_ERC20_ABI)
    
    # Create pair
    print("\n   Creating WETH/CAKE pair...")
    send_transaction(factory_contract, 'createPair', weth_address, deployed_addresses['CAKE'])
    
    # Get pair address
    pair_address = factory_contract.functions.getPair(weth_address, deployed_addresses['CAKE']).call()
    print(f"   ✅ Pair created at: {pair_address}")
    deployed_addresses['WETH_CAKE_PAIR'] = pair_address
    
    # Approve router to spend CAKE
    cake_amount = w3.to_wei(INITIAL_CAKE_LIQUIDITY, 'ether')
    print(f"\n   Approving router to spend {INITIAL_CAKE_LIQUIDITY} CAKE...")
    send_transaction(cake_contract, 'approve', router_address, cake_amount)
    
    # Add liquidity
    eth_amount = w3.to_wei(INITIAL_ETH_LIQUIDITY, 'ether')
    deadline = int(time.time()) + 3600  # 1 hour from now
    
    print(f"\n   Adding liquidity: {INITIAL_ETH_LIQUIDITY} ETH + {INITIAL_CAKE_LIQUIDITY} CAKE...")
    send_transaction(
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
    
    print("   ✅ Liquidity added successfully!")


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
