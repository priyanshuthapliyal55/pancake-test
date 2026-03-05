# Complete Step-by-Step Guide: Deploy and Test on Your L2

This guide walks you through deploying a DEX and running TPS tests **from scratch** on your own L2 blockchain.

---

## Prerequisites

### What You Need:
1. **Your L2 blockchain running** (OP Stack, Arbitrum Orbit, etc.)
2. **Native tokens** (at least 1 ETH/equivalent for deployment + testing)
3. **RPC URLs**:
   - HTTP RPC endpoint: `https://your-l2-rpc-url`
   - WebSocket RPC endpoint: `wss://your-l2-ws-url`
4. **Chain ID** of your L2
5. **Python 3.8+** and **Node.js 14+** installed

### Get Your Wallet Ready:
- Have a mnemonic/seed phrase (or generate a new one)
- Account 0 from this mnemonic will be the deployer
- Fund account 0 with native tokens on your L2

---

## Part 1: Initial Setup

### Step 1: Install Dependencies

```bash
cd /home/priyanshu/op-stack/pancake-swap-testnet/rollup-amm-tps-test

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import web3; print('✅ Web3 installed')"
```

### Step 2: Configure Your Mnemonic

```bash
# Edit mnemonic.txt with your seed phrase
nano mnemonic.txt
```

Add your 12 or 24 word mnemonic:
```
your twelve word seed phrase goes here like this example text
```

⚠️ **Security**: This mnemonic generates 100 test accounts. Keep it safe but separate from your main funds.

### Step 3: Verify Your L2 Connection

Test your RPC connection:

```bash
# Test with Python
python3 << 'EOF'
from web3 import Web3

# Replace with your L2 RPC URL
rpc_url = "https://your-l2-rpc-url"
w3 = Web3(Web3.HTTPProvider(rpc_url))

if w3.is_connected():
    print(f"✅ Connected to L2")
    print(f"   Chain ID: {w3.eth.chain_id}")
    print(f"   Latest block: {w3.eth.block_number}")
else:
    print("❌ Connection failed")
EOF
```

---

## Part 2: Compile Contracts

### Step 4: Compile DEX Contracts

```bash
# Make the compile script executable
chmod +x compile_contracts.sh

# Compile all contracts (Factory, Router, Pair)
./compile_contracts.sh
```

This compiles:
- `PancakeFactory` (creates trading pairs)
- `PancakePair` (liquidity pool implementation)
- `PancakeRouter` (handles swaps and liquidity)

**Expected output:**
```
✅ Core contracts compiled
✅ Periphery contracts compiled
```

**Troubleshooting:**
- If you see `npm: command not found`: Install Node.js
- If you see `truffle: command not found`: Install globally with `npm install -g truffle`
- If compilation fails: Check that you're using Node.js v14-v16 (not v18+)

---

## Part 3: Deploy Contracts to Your L2

### Step 5: Configure Deployment Script

Edit [deploy_l2.py](deploy_l2.py) and update the configuration at the top:

```python
# Your L2 Configuration
L2_RPC_URL = "https://your-l2-rpc-url"  # ← Change this
L2_CHAIN_ID = 12345  # ← Change this to your L2 chain ID
L2_NAME = "MY_L2"  # ← Change this to your L2 name

# Gas settings (adjust for your L2)
GAS_PRICE_GWEI = 0.001  # ← Adjust based on your L2
```

### Step 6: Run Deployment Script

```bash
python deploy_l2.py
```

**What happens:**
1. ✅ Deploys WETH9 (wrapped native token)
2. ✅ Deploys PancakeFactory
3. ✅ Deploys PancakeRouter
4. ⚠️  Prompts for CAKE token address (see next step)
5. ✅ Creates WETH/CAKE pair
6. ✅ Adds initial liquidity
7. ✅ Saves addresses to `deployed_addresses.json`

### Step 7: Deploy CAKE Token

The deployment script will pause and ask for CAKE token address.

**Option A: Deploy via Remix (Easiest)**

1. Open [Remix IDE](https://remix.ethereum.org)
2. Create new file: `CAKEToken.sol`
3. Copy contents from [/home/priyanshu/op-stack/pancake-swap-testnet/build/tokens/CAKEToken.sol](../build/tokens/CAKEToken.sol)
4. Compile with Solidity 0.6.12
5. Connect Remix to your L2:
   - Click "Deploy & Run" tab
   - Environment: "Injected Provider - MetaMask"
   - Switch MetaMask to your L2 network
6. Deploy contract
7. Copy deployed contract address
8. Paste address into the deployment script prompt

**Option B: Deploy via Truffle**

```bash
# TODO: Add truffle deployment for CAKE
```

**Option C: Skip for Now**

Press Enter to skip. You can deploy CAKE later and manually create the pair.

---

## Part 4: Update Configuration

### Step 8: Update blockchain.py

The deployment script will print the exact code to add. Open [blockchain.py](blockchain.py) and add your L2:

```python
class ChainId(enum.Enum):
    # ... existing chains ...
    MY_L2 = 12345  # Your chain ID

# In BlockchainData.NETWORKS, uncomment and update:
ChainId.MY_L2: NetworkData(
    chain_id=12345,
    http_rpc_url='https://your-l2-rpc-url',
    ws_rpc_url='wss://your-l2-ws-url',
    addresses={
        Contract.PANCAKE_SMART_ROUTER: '0xYourRouterAddress',  # From deployed_addresses.json
        Token.CAKE: '0xYourCakeAddress',
        Token.WETH: '0xYourWETHAddress',
    },
),
```

### Step 9: Update Test Scripts

Edit `prepare.py` and `tps_test.py` to use your L2:

```python
# At the top of both files, change:
CHAIN_ID = ChainId.MY_L2  # Instead of ChainId.SEPOLIA_TESTNET
```

---

## Part 5: Prepare Test Accounts

### Step 10: Fund 100 Test Accounts

```bash
python prepare.py
```

**What happens:**
- Generates 100 accounts from your mnemonic
- Sends 0.002 ETH to each account (from account 0)
- Wraps 0.00000005 ETH → WETH for each account
- Approves Router to spend WETH

**Requirements:**
- Account 0 needs ~0.25 ETH total:
  - 0.2 ETH for funding accounts (100 × 0.002)
  - 0.05 ETH buffer for gas fees

**Troubleshooting:**
- "Insufficient funds": Fund account 0 with more tokens
- "RPC error": Check your RPC URL is correct
- Slow execution: Normal on some L2s, be patient

---

## Part 6: Run TPS Test

### Step 11: Quick Test (10 accounts)

Test with just 10 accounts first:

```bash
mkdir -p logs
python tps_test.py -n 0 2>&1 | tee logs/tps00.log
```

**What happens:**
- Accounts 0-9 each execute 20 WETH→CAKE swaps in parallel
- 200 total transactions
- Takes 1-30 seconds depending on your L2
- All transactions are logged

**Check the log:**
```bash
tail -f logs/tps00.log
```

You should see:
```
Sending swaps from accounts 0 to 9...
Account 0: Swap 1/20 sent: 0x1234...
Account 1: Swap 1/20 sent: 0x5678...
...
```

### Step 12: Full Test (100 accounts)

For accurate TPS measurement, run from **10 different IPs** to avoid RPC rate limiting:

**Single Machine Test (for testing):**
```bash
# Run all sequentially (slower, but works)
for i in {0..9}; do
  python tps_test.py -n $i 2>&1 | tee logs/tps0${i}.log
done
```

**Multi-Machine Test (recommended):**

On 10 different servers/IPs, run:
```bash
# Machine 1:
python tps_test.py -n 0 2>&1 | tee logs/tps00.log

# Machine 2:
python tps_test.py -n 1 2>&1 | tee logs/tps01.log

# ... Machine 3-9 ...

# Machine 10:
python tps_test.py -n 9 2>&1 | tee logs/tps09.log
```

**Note:** The script syncs to the next 5-minute mark, so all instances start together.

---

## Part 7: Analyze Results

### Step 13: Combine Logs and Calculate TPS

```bash
# Combine all logs
cat logs/tps0*.log > logs/tps.log

# Parse and calculate TPS
python logs_parser.py
```

**Output:**
- `swaps.log`: All transactions sorted by block and time
- `tps-results.log`: Block analysis and final TPS calculation
- Console: TPS summary and chart

**Understanding Results:**

```
Total transactions: 2000
First tx block: 12345 (timestamp: 1640000000)
Last tx block: 12356 (timestamp: 1640000011)
Duration: 11 seconds
TPS: 181.8 transactions/second
```

**Compare with known L2s:**
- zkSync Era: ~180 TPS
- OP Mainnet: ~140 TPS
- Polygon zkEVM: ~5 TPS
- Your L2: ? TPS 🎉

---

## Part 8: Verify On-Chain

### Step 14: Check Block Explorer

Visit your L2's block explorer and verify:

1. **Router contract**: Should show many `swap` calls
2. **WETH/CAKE pair**: Should show multiple `Swap` events
3. **Test accounts**: Each should have ~20 transactions

Example blocks to check:
- First block of test: Find in `tps-results.log`
- Last block of test: Find in `tps-results.log`
- Your blocks should be mostly your swap transactions

---

## Troubleshooting

### Common Issues:

**1. "Connection refused"**
```
✗ Check RPC URL is correct and accessible
✗ Check firewall/VPN settings
✗ Try with `curl https://your-l2-rpc-url`
```

**2. "Insufficient funds"**
```
✗ Fund the deployer account (account 0 from mnemonic)
✗ Need ~1 ETH for full deployment + testing
```

**3. "Transaction underpriced"**
```
✗ Increase GAS_PRICE_GWEI in deploy_l2.py
✗ Check your L2's minimum gas price
```

**4. "Contract deployment failed"**
```
✗ Check gas limit is sufficient
✗ Some L2s have different EVM opcodes - check compatibility
✗ Try deploying contracts one-by-one manually
```

**5. "RPC rate limited"**
```
✗ Use multiple IP addresses for full test
✗ Run from 10 different machines/VPNs
✗ Contact your L2 provider for higher rate limits
```

**6. "Pair has insufficient liquidity"**
```
✗ Add more liquidity to WETH/CAKE pair
✗ Increase INITIAL_ETH_LIQUIDITY and INITIAL_CAKE_LIQUIDITY
✗ Make sure CAKE has enough supply minted
```

---

## Advanced: Manual Deployment

If the automated script doesn't work, deploy manually:

### Manual Factory Deployment:
```bash
cd ../pancake-swap-core
npm install
npx truffle migrate --network your_network
```

### Manual Router Deployment:
```bash
cd ../pancake-swap-periphery
export FACTORY_ADDRESS=0xYourFactoryAddress
export WETH_ADDRESS=0xYourWETHAddress
npx truffle migrate --network your_network
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed manual steps.

---

## Summary Checklist

- [ ] Python & Node.js installed
- [ ] Dependencies installed (`pip install`, `npm install`)
- [ ] Mnemonic configured in `mnemonic.txt`
- [ ] Account 0 funded with native tokens
- [ ] RPC connection verified
- [ ] Contracts compiled (`./compile_contracts.sh`)
- [ ] L2 configuration updated in `deploy_l2.py`
- [ ] Contracts deployed (`python deploy_l2.py`)
- [ ] CAKE token deployed
- [ ] `blockchain.py` updated with addresses
- [ ] Test scripts updated with chain ID
- [ ] Test accounts prepared (`python prepare.py`)
- [ ] TPS test executed (`python tps_test.py`)
- [ ] Results analyzed (`python logs_parser.py`)
- [ ] Block explorer verified

---

## Next Steps

1. **Optimize for your L2**: Adjust gas prices, batch sizes, account counts
2. **Run multiple tests**: Test at different times of day, different loads
3. **Compare results**: Benchmark against other L2s
4. **Share results**: Publish your findings!

---

## Support

- Check existing issues in the repository
- Review logs for detailed error messages
- Test on Sepolia first before your custom L2
- Make sure your L2 is EVM-compatible

---

**Good luck with your TPS testing! 🚀**
