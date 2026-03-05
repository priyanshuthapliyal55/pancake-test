# Step-by-Step Contract Deployment Guide

This guide walks you through deploying PancakeSwap contracts (Factory, Router, and test tokens) on your blockchain network.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Step 1: Environment Setup](#step-1-environment-setup)
- [Step 2: Compile Contracts](#step-2-compile-contracts)
- [Step 3: Deploy Core Contracts](#step-3-deploy-core-contracts)
- [Step 4: Deploy Test Token (CAKE)](#step-4-deploy-test-token-cake)
- [Step 5: Create Trading Pair](#step-5-create-trading-pair)
- [Step 6: Add Liquidity](#step-6-add-liquidity)
- [Step 7: Update Configuration](#step-7-update-configuration)
- [Step 8: Prepare Test Accounts](#step-8-prepare-test-accounts)
- [Step 9: Run TPS Test](#step-9-run-tps-test)
- [Step 10: Analyze Results](#step-10-analyze-results)

---

## Prerequisites

### 1. Install Dependencies

```bash
# Python dependencies for test scripts
cd rollup-amm-tps-test
pip install -r requirements.txt
```

### 2. Install Node.js Dependencies

```bash
# For pancake-swap-core
cd pancake-swap-core
npm install

# For pancake-swap-periphery
cd ../pancake-swap-periphery
npm install
```

### 3. Get Test ETH

- **For Sepolia Testnet**: Use faucet at https://sepoliafaucet.com/
- **For your custom L2**: Use your L2's faucet or admin account
- **Required amount**: ~0.5 ETH for deployment + testing

### 4. Set Up Wallet

Edit `rollup-amm-tps-test/mnemonic.txt` and add your wallet seed phrase:
```
your twelve word seed phrase goes here like this example text
```

⚠️ **IMPORTANT**: 
- Account 0 (first account from mnemonic) will be the deployer
- Make sure this account has sufficient ETH before proceeding

---

## Step 1: Environment Setup

### Configure Your Network

Update `rollup-amm-tps-test/deploy_simple.py` with your network details:

```python
L2_RPC_URL = "http://your-rpc-url:8545"  # Your blockchain RPC URL
L2_CHAIN_ID = 11155111                    # Your chain ID
L2_NAME = "MY_L2"                         # Network name
GAS_PRICE_GWEI = 0.001                    # Gas price (adjust as needed)
MAX_GAS = 8000000                         # Max gas limit
```

### Verify Connection

```bash
cd rollup-amm-tps-test
python3 -c "from web3 import Web3; w3 = Web3(Web3.HTTPProvider('http://your-rpc-url:8545')); print('Connected!' if w3.is_connected() else 'Failed!')"
```

---

## Step 2: Compile Contracts

### Option A: Using Foundry (Recommended)

```bash
cd rollup-amm-tps-test

# Compile WETH
forge build WETH.sol --use 0.5.16

# Compile PancakeFactory
cd ../pancake-swap-core
npm run compile
# or
npx truffle compile

# Compile PancakeRouter
cd ../pancake-swap-periphery
npm run compile
```

### Option B: Using Hardhat

```bash
cd pancake-swap-core
npx hardhat compile

cd ../pancake-swap-periphery
npx hardhat compile
```

### Verify Compilation

Check that build artifacts exist:
```bash
ls -la pancake-swap-core/build/contracts/PancakeFactory.json
ls -la pancake-swap-periphery/build/contracts/PancakeRouter.json
ls -la rollup-amm-tps-test/out/WETH.sol/WETH.json
```

---

## Step 3: Deploy Core Contracts

### Method 1: Automated Deployment (Easiest)

```bash
cd rollup-amm-tps-test
python3 deploy_simple.py
```

This script will:
1. Deploy WETH contract
2. Deploy PancakeFactory contract
3. Deploy PancakeRouter contract
4. Save addresses to `deployed_addresses.json`

### Method 2: Manual Deployment

**Deploy WETH:**
```bash
cd rollup-amm-tps-test
python3
```
```python
from web3 import Web3
from eth_account import Account
import json

# Setup
w3 = Web3(Web3.HTTPProvider('http://your-rpc-url:8545'))
Account.enable_unaudited_hdwallet_features()
with open('mnemonic.txt') as f:
    mnemonic = f.read().strip()
deployer = Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")

# Load WETH
with open('out/WETH.sol/WETH.json') as f:
    weth_artifact = json.load(f)
    weth_abi = weth_artifact['abi']
    weth_bytecode = weth_artifact['bytecode']['object']

# Deploy WETH
WETH = w3.eth.contract(abi=weth_abi, bytecode=weth_bytecode)
tx = WETH.constructor().build_transaction({
    'from': deployer.address,
    'nonce': w3.eth.get_transaction_count(deployer.address),
    'gas': 2000000,
    'gasPrice': w3.to_wei(0.001, 'gwei'),
})
signed = w3.eth.account.sign_transaction(tx, deployer.key)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
weth_address = receipt['contractAddress']
print(f"WETH deployed at: {weth_address}")
```

**Deploy Factory and Router:**

Follow similar process for Factory (with deployer address as constructor arg) and Router (with factory and WETH addresses as constructor args).

### Save Deployment Addresses

After deployment, you should have these addresses:
- **WETH**: 0x...
- **Factory**: 0x...
- **Router**: 0x...

---

## Step 4: Deploy Test Token (CAKE)

### Option A: Using Remix (Easiest)

1. Go to https://remix.ethereum.org
2. Upload `build/tokens/CAKEToken.sol`
3. Compile with Solidity 0.6.12
4. Deploy to your network using Metamask/Injected Provider
5. Copy the deployed contract address

### Option B: Using Python Script

Create `rollup-amm-tps-test/deploy_cake.py`:

```python
from web3 import Web3
from eth_account import Account
import json

w3 = Web3(Web3.HTTPProvider('http://your-rpc-url:8545'))

# Load deployer
Account.enable_unaudited_hdwallet_features()
with open('mnemonic.txt') as f:
    mnemonic = f.read().strip()
deployer = Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")

# Simple ERC20 bytecode and ABI (or load from CAKEToken.sol)
# Deploy and save address
```

Run:
```bash
python3 deploy_cake.py
```

### Verify Token

After deployment, verify you can interact with the token:
```bash
python3
```
```python
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('http://your-rpc-url:8545'))

# Standard ERC20 ABI
token = w3.eth.contract(address='YOUR_CAKE_ADDRESS', abi=ERC20_ABI)
print(f"Token name: {token.functions.name().call()}")
print(f"Token symbol: {token.functions.symbol().call()}")
print(f"Total supply: {token.functions.totalSupply().call()}")
```

---

## Step 5: Create Trading Pair

Create a WETH/CAKE trading pair using the Factory contract:

```python
from web3 import Web3
from eth_account import Account
import json

w3 = Web3(Web3.HTTPProvider('http://your-rpc-url:8545'))

# Load deployer
Account.enable_unaudited_hdwallet_features()
with open('mnemonic.txt') as f:
    mnemonic = f.read().strip()
deployer = Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")

# Factory ABI (load from build artifacts)
with open('../pancake-swap-core/build/contracts/PancakeFactory.json') as f:
    factory_abi = json.load(f)['abi']

factory = w3.eth.contract(
    address='YOUR_FACTORY_ADDRESS',
    abi=factory_abi
)

# Create pair
tx = factory.functions.createPair(
    'YOUR_WETH_ADDRESS',
    'YOUR_CAKE_ADDRESS'
).build_transaction({
    'from': deployer.address,
    'nonce': w3.eth.get_transaction_count(deployer.address),
    'gas': 5000000,
    'gasPrice': w3.to_wei(0.001, 'gwei'),
})

signed = w3.eth.account.sign_transaction(tx, deployer.key)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

# Get pair address
pair_address = factory.functions.getPair(
    'YOUR_WETH_ADDRESS',
    'YOUR_CAKE_ADDRESS'
).call()

print(f"Pair created at: {pair_address}")
```

---

## Step 6: Add Liquidity

Add initial liquidity to enable trading:

```python
from web3 import Web3
from eth_account import Account
import json
from datetime import datetime, timedelta

w3 = Web3(Web3.HTTPProvider('http://your-rpc-url:8545'))

# Load deployer
Account.enable_unaudited_hdwallet_features()
with open('mnemonic.txt') as f:
    mnemonic = f.read().strip()
deployer = Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")

# Load Router ABI
with open('../pancake-swap-periphery/build/contracts/PancakeRouter.json') as f:
    router_abi = json.load(f)['abi']

router = w3.eth.contract(address='YOUR_ROUTER_ADDRESS', abi=router_abi)

# Load CAKE token
with open('path/to/ERC20_ABI.json') as f:
    erc20_abi = json.load(f)

cake = w3.eth.contract(address='YOUR_CAKE_ADDRESS', abi=erc20_abi)

# Approve CAKE for Router
approve_amount = w3.to_wei(1000000, 'ether')  # 1M CAKE
tx = cake.functions.approve(
    'YOUR_ROUTER_ADDRESS',
    approve_amount
).build_transaction({
    'from': deployer.address,
    'nonce': w3.eth.get_transaction_count(deployer.address),
    'gas': 100000,
    'gasPrice': w3.to_wei(0.001, 'gwei'),
})
signed = w3.eth.account.sign_transaction(tx, deployer.key)
w3.eth.send_raw_transaction(signed.rawTransaction)
w3.eth.wait_for_transaction_receipt(signed.rawTransaction.hex())

# Add liquidity
# Adding 1 ETH + 100 CAKE
deadline = int((datetime.now() + timedelta(minutes=20)).timestamp())

tx = router.functions.addLiquidityETH(
    'YOUR_CAKE_ADDRESS',           # token
    w3.to_wei(100, 'ether'),        # amountTokenDesired (100 CAKE)
    w3.to_wei(99, 'ether'),         # amountTokenMin (99 CAKE minimum)
    w3.to_wei(0.99, 'ether'),       # amountETHMin (0.99 ETH minimum)
    deployer.address,               # to
    deadline                        # deadline
).build_transaction({
    'from': deployer.address,
    'value': w3.to_wei(1, 'ether'), # 1 ETH
    'nonce': w3.eth.get_transaction_count(deployer.address),
    'gas': 500000,
    'gasPrice': w3.to_wei(0.001, 'gwei'),
})

signed = w3.eth.account.sign_transaction(tx, deployer.key)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print(f"Liquidity added! TX: {tx_hash.hex()}")
```

**Recommended Liquidity Amounts:**
- For TPS test (2000+ swaps): Add at least **1 ETH + equivalent CAKE**
- Each swap uses minimal amounts (~0.00000005 WETH)
- Ensure sufficient depth to avoid slippage issues

---

## Step 7: Update Configuration

Edit `rollup-amm-tps-test/blockchain.py` to add your network configuration:

```python
# Add new ChainId
class ChainId(enum.Enum):
    # ... existing chains ...
    MY_CUSTOM_L2 = 1376  # Your actual chain ID

# Add to NETWORKS dictionary
class BlockchainData:
    NETWORKS = {
        # ... existing networks ...
        ChainId.MY_CUSTOM_L2: NetworkData(
            chain_id=1376,  # Your chain ID
            http_rpc_url='http://your-rpc-url:8545',
            ws_rpc_url='ws://your-ws-url:8546',
            addresses={
                Contract.PANCAKE_SMART_ROUTER: '0xYourRouterAddress',
                Token.CAKE: '0xYourCakeAddress',
                Token.WETH: '0xYourWETHAddress',
            },
        ),
    }
```

---

## Step 8: Prepare Test Accounts

This step funds 100 test accounts with ETH, wraps it to WETH, and approves the router:

```bash
cd rollup-amm-tps-test

# Update prepare.py to use your chain
# Edit the script and change: chain_id = ChainId.MY_CUSTOM_L2

# Run preparation
python3 prepare.py
```

**What prepare.py does:**
1. Derives 100 accounts from your mnemonic (indices 0-99)
2. Sends 0.002 ETH to each account from account 0
3. Wraps 0.00000005 ETH to WETH for each account
4. Approves Router to spend WETH for each account

**Time required**: ~5-10 minutes depending on network speed

---

## Step 8.5: Verify Swaps Are Working (Optional but Recommended)

Before running the full TPS test, verify that swaps work correctly:

### Using the Verification Script

```bash
cd rollup-amm-tps-test

# Update check_swaps.py with your contract addresses
# Then run it:
python3 check_swaps.py
```

**Available verification methods:**
1. **Check pair reserves** - Verify liquidity exists
2. **Check token balances** - View WETH/CAKE balances
3. **Simulate swap** - Calculate expected output (no transaction)
4. **Check allowances** - Verify router approval
5. **Execute test swap** - Run a real 0.00001 WETH swap
6. **Check recent swap events** - View swap history
7. **Check specific transaction** - Inspect a transaction hash
8. **Run all checks** - Complete verification

### Quick Manual Verification

**Check reserves:**
```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('http://your-rpc:8545'))

# Get pair address
factory = w3.eth.contract(address='FACTORY_ADDRESS', abi=FACTORY_ABI)
pair = factory.functions.getPair('WETH_ADDRESS', 'CAKE_ADDRESS').call()

# Check reserves
pair_contract = w3.eth.contract(address=pair, abi=PAIR_ABI)
reserves = pair_contract.functions.getReserves().call()
print(f"Reserve0: {w3.from_wei(reserves[0], 'ether')}")
print(f"Reserve1: {w3.from_wei(reserves[1], 'ether')}")
```

**Check if swap transaction succeeded:**
```python
# Get transaction receipt
receipt = w3.eth.get_transaction_receipt('0xYourTxHash...')
print(f"Status: {receipt['status']}")  # 1 = success, 0 = failed
print(f"Gas used: {receipt['gasUsed']}")

# Check for Swap events in logs
for log in receipt['logs']:
    if log['address'].lower() == pair.lower():
        print("✅ Swap event found!")
```

**Using Block Explorer (if available):**
1. Go to your blockchain explorer
2. Search for the Router contract address
3. View recent transactions
4. Check for `swapExactTokensForTokens` calls
5. Verify transaction status is "Success"

---

## Step 9: Run TPS Test

### Quick Test (10 accounts)

Perfect for testing if everything works:

```bash
cd rollup-amm-tps-test
python3 tps_test.py -n 0 2>&1 | tee logs/tps00.log
```

This sends 20 swaps from accounts 0-9.

### Full TPS Test (100 accounts)

For accurate TPS measurement, run from **10 different machines/IPs** to avoid RPC rate limits:

**Machine 1:**
```bash
python3 tps_test.py -n 0 2>&1 | tee logs/tps00.log  # accounts 0-9
```

**Machine 2:**
```bash
python3 tps_test.py -n 1 2>&1 | tee logs/tps01.log  # accounts 10-19
```

**Continue for n=2 through n=9...**

Each instance sends 200 transactions (20 swaps × 10 accounts).

**Single Machine Alternative** (if RPC has high limits):
```bash
for i in {0..9}; do
    python3 tps_test.py -n $i 2>&1 | tee logs/tps0${i}.log &
done
wait
```

⚠️ **Note**: Running from single IP may trigger rate limits

---

## Step 10: Analyze Results

### Combine Logs

```bash
cd rollup-amm-tps-test
cat logs/tps0*.log > logs/tps.log
```

### Parse and Calculate TPS

```bash
python3 logs_parser.py logs/tps.log MY_CUSTOM_L2
```

### Generate Visualization

If you have matplotlib installed:

```bash
python3 analyze_tps.py
```

This creates plots showing:
- Transaction distribution over time
- Blocks containing test transactions
- Calculated TPS

### Understanding Results

The TPS calculation:
```
TPS = Total Transactions / (Last Block Timestamp - First Block Timestamp)
```

**Example output:**
```
Total transactions: 2000
First block: 1234567 (timestamp: 1630000000)
Last block: 1234578 (timestamp: 1630000011)
Duration: 11 seconds
TPS: 181.8 tx/s
```

---

## Troubleshooting

### AttributeError: 'SignedTransaction' object has no attribute 'rawTransaction'

**Problem**: Error when running `deploy_simple.py`:
```
AttributeError: 'SignedTransaction' object has no attribute 'rawTransaction'
```

**Cause**: Web3.py version incompatibility. Newer versions (v6+) use `raw_transaction` (snake_case) instead of `rawTransaction` (camelCase).

**Solution**:
```bash
# Fix applied! The deploy_simple.py has been updated.
# If you still see this error in other scripts, change:
signed_txn.rawTransaction  # OLD
# to:
signed_txn.raw_transaction  # NEW
```

**Alternative**: Downgrade web3.py (not recommended)
```bash
pip install web3==5.31.4
```

### Contract Deployment Fails

**Problem**: Gas estimation fails or deployment reverts

**Solutions**:
- Increase `MAX_GAS` in deploy_simple.py
- Check deployer has sufficient ETH
- Verify RPC is responding correctly
- Try manual deployment with higher gas limit

### Pair Creation Fails

**Problem**: `createPair` reverts with "Pair already exists"

**Solution**:
```python
# Check if pair already exists
pair = factory.functions.getPair(WETH_ADDRESS, CAKE_ADDRESS).call()
if pair != '0x0000000000000000000000000000000000000000':
    print(f"Pair already exists at {pair}")
```

### Liquidity Addition Fails

**Problem**: Router transaction reverts

**Common causes**:
1. Token not approved for Router
2. Insufficient token balance
3. Deadline expired
4. Minimum amounts too high (slippage)

**Debug**:
```python
# Check approval
allowance = cake.functions.allowance(deployer.address, router_address).call()
print(f"Allowance: {allowance}")

# Check balance
balance = cake.functions.balanceOf(deployer.address).call()
print(f"Balance: {balance}")
```

### TPS Test Connection Issues

**Problem**: WebSocket connection fails

**Solution**:
1. Verify WS endpoint in `blockchain.py`
2. Check firewall allows WebSocket connections
3. Try HTTP endpoint as fallback (slower)

### Rate Limiting

**Problem**: "Too many requests" errors

**Solutions**:
- Reduce concurrent requests
- Use multiple IPs (10 recommended for full test)
- Increase delays between transactions
- Use dedicated RPC node

---

## Quick Reference Commands

```bash
# Full deployment from scratch
cd rollup-amm-tps-test
python3 deploy_simple.py              # Deploy contracts
# ... deploy CAKE token manually ...
# ... create pair and add liquidity ...
# Update blockchain.py with addresses
python3 prepare.py                     # Prepare accounts
python3 tps_test.py -n 0               # Run test
python3 logs_parser.py logs/tps00.log  # Analyze

# Cleanup and redeploy
rm deployed_addresses.json
rm -rf ../pancake-swap-core/build
rm -rf ../pancake-swap-periphery/build
# Start over from Step 2
```

---

## Additional Resources

- **PancakeSwap Documentation**: https://docs.pancakeswap.finance/
- **Uniswap V2 Documentation**: https://docs.uniswap.org/contracts/v2/overview
- **Web3.py Documentation**: https://web3py.readthedocs.io/
- **Foundry Book**: https://book.getfoundry.sh/

---

## Summary Checklist

- [ ] Install dependencies (Python, Node.js)
- [ ] Get test ETH for deployer account
- [ ] Configure mnemonic.txt
- [ ] Update deploy_simple.py with network details
- [ ] Compile contracts (WETH, Factory, Router)
- [ ] Deploy core contracts (automated or manual)
- [ ] Deploy CAKE token
- [ ] Create WETH/CAKE pair
- [ ] Add liquidity (minimum 1 ETH + equivalent CAKE)
- [ ] Update blockchain.py with all addresses
- [ ] Run prepare.py to fund test accounts
- [ ] Run TPS test (quick test first)
- [ ] Analyze results with logs_parser.py
- [ ] Document your TPS results!

---

**Need help?** Check the existing guides:
- `DEPLOYMENT_GUIDE.md` - Detailed deployment steps
- `QUICKSTART.md` - Quick start for common networks
- `COMPLETE_SETUP_GUIDE.md` - Complete setup instructions
- `README.md` - Project overview and test results
