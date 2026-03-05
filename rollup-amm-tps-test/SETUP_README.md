# 🚀 Complete L2 Deployment & TPS Testing Suite

I've created a complete automated deployment and testing solution for running AMM TPS tests on your L2 from scratch (no contracts deployed yet).

## 📁 What's Been Created

### Core Scripts:

1. **[deploy_l2.py](deploy_l2.py)** ⭐
   - Complete automated deployment script
   - Deploys: WETH, Factory, Router
   - Creates pair and adds liquidity
   - Saves all addresses to `deployed_addresses.json`
   - Just configure RPC URL and chain ID at the top!

2. **[compile_contracts.sh](compile_contracts.sh)**
   - Compiles all Pancake Swap contracts
   - Runs npm install automatically
   - One command to prepare everything

3. **[add_liquidity.py](add_liquidity.py)**
   - Manually add more liquidity if needed
   - Reads config from `deployed_addresses.json`
   - Interactive prompts for amounts

4. **[quickstart.sh](quickstart.sh)**
   - Run the entire flow in one command
   - Automated setup from start to finish
   - Good for testing the process

### Documentation:

5. **[COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)** 📚
   - Comprehensive 14-step guide
   - Covers everything from prerequisites to results
   - Troubleshooting section
   - Manual deployment fallback instructions

### Updated Files:

6. **[blockchain.py](blockchain.py)**
   - Added template for custom L2 configuration
   - Clear comments showing where to add your chain
   - Example configuration included

## 🎯 Quick Start (3 Steps)

### 1. Configure Your L2

Edit `deploy_l2.py` (top of file):
```python
L2_RPC_URL = "https://your-l2-rpc-url"
L2_CHAIN_ID = 12345  # Your chain ID
L2_NAME = "MY_L2"
```

### 2. Add Your Mnemonic

Edit `mnemonic.txt`:
```
your twelve word seed phrase goes here
```

Make sure account 0 has ~1 ETH on your L2.

### 3. Run Deployment

```bash
# Compile contracts
./compile_contracts.sh

# Deploy everything
python deploy_l2.py

# Update blockchain.py with printed addresses

# Prepare accounts
python prepare.py

# Run test
python tps_test.py -n 0
```

## 📊 What Gets Deployed

```
Your L2
├── WETH Contract (wrapped native token)
├── PancakeFactory (creates pairs)
├── PancakeRouter (handles swaps/liquidity)
├── CAKE Token (test token - you deploy via Remix)
├── WETH/CAKE Pair (liquidity pool)
└── 100 Test Accounts (funded & ready)
```

## 🔄 Full Workflow

```bash
# 1. One-time setup
cd rollup-amm-tps-test
pip install -r requirements.txt

# 2. Configure (edit these files)
nano deploy_l2.py      # Set RPC URL, chain ID
nano mnemonic.txt      # Add seed phrase

# 3. Compile & Deploy
./compile_contracts.sh
python deploy_l2.py

# 4. Deploy CAKE token (via Remix)
# Copy/paste build/tokens/CAKEToken.sol to Remix
# Deploy to your L2
# Enter address when deploy_l2.py prompts

# 5. Update config
nano blockchain.py     # Add your L2 (script prints exact code)

# 6. Prepare & Test
python prepare.py                           # Fund 100 accounts
python tps_test.py -n 0 2>&1 | tee logs/tps00.log  # Run test
python logs_parser.py                       # Analyze results
```

## 📖 Detailed Guide

See **[COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)** for:
- Detailed explanations of each step
- Troubleshooting common issues
- Manual deployment instructions
- Advanced configuration options
- Multi-machine test setup

## 🛠️ Script Details

### deploy_l2.py

**Features:**
- ✅ Connects to your L2 via RPC
- ✅ Deploys WETH9, Factory, Router
- ✅ Creates WETH/CAKE pair
- ✅ Adds initial liquidity
- ✅ Saves all addresses to JSON
- ✅ Prints exact code for blockchain.py
- ✅ Configurable gas prices
- ✅ Automatic gas estimation
- ✅ Transaction confirmation waiting

**Configuration (top of file):**
```python
L2_RPC_URL = "https://..."
L2_CHAIN_ID = 12345
L2_NAME = "MY_L2"
GAS_PRICE_GWEI = 0.001
INITIAL_ETH_LIQUIDITY = 0.5
INITIAL_CAKE_LIQUIDITY = 1000
```

### add_liquidity.py

Use this to:
- Add more liquidity after deployment
- Top up if pool gets depleted during testing
- Adjust liquidity amounts

Automatically reads from `deployed_addresses.json`.

### compile_contracts.sh

Compiles:
1. pancake-swap-core (Factory, Pair)
2. pancake-swap-periphery (Router)

Creates `build/` folders with compiled artifacts.

## 📋 Requirements

**System:**
- Python 3.8+
- Node.js 14-16 (v18+ has issues with Truffle)
- npm
- Git

**L2 Requirements:**
- EVM-compatible L2 blockchain
- HTTP RPC endpoint
- WebSocket RPC endpoint
- Native tokens for gas (~1 ETH for full deployment + test)

**Python Packages (in requirements.txt):**
- web3 >= 6.0.0
- eth-account >= 0.8.0
- websockets >= 10.0

## 🎓 Understanding the Test

**What it measures:**
- Transactions per second (TPS) during high load
- Uses Uniswap V2-style swaps as benchmark
- Industry standard AMM test

**Test setup:**
- 100 accounts each do 20 swaps = 2000 total transactions
- All sent in parallel to stress test your L2
- Measures time from first tx included to last tx included

**Results comparison:**
- zkSync Era: ~180 TPS
- OP Mainnet: ~140 TPS
- Polygon zkEVM: ~5 TPS
- **Your L2: ? TPS** 🚀

## 🔧 Troubleshooting

### "Connection refused"
- Check RPC URL in deploy_l2.py
- Make sure your L2 is running
- Test with: `curl https://your-rpc-url`

### "Insufficient funds"
- Fund account 0 from mnemonic with native tokens
- Need ~1 ETH for deployment + testing

### "Contract deployment failed"
- Check gas prices for your L2
- Increase MAX_GAS if needed
- Verify EVM compatibility

### "Compilation failed"
- Downgrade to Node.js v14-v16
- Run `npm install` in core and periphery folders
- Install truffle globally: `npm install -g truffle`

See [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md#troubleshooting) for more.

## 📞 Next Steps

1. ✅ Review [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)
2. ✅ Configure your L2 in deploy_l2.py
3. ✅ Run ./compile_contracts.sh
4. ✅ Run python deploy_l2.py
5. ✅ Update blockchain.py
6. ✅ Run python prepare.py
7. ✅ Run python tps_test.py -n 0
8. ✅ Analyze results!

## 📝 Files Overview

```
rollup-amm-tps-test/
├── 🆕 deploy_l2.py              # Automated deployment
├── 🆕 add_liquidity.py          # Add more liquidity
├── 🆕 compile_contracts.sh      # Compile all contracts
├── 🆕 quickstart.sh             # Run everything at once
├── 🆕 COMPLETE_SETUP_GUIDE.md   # Detailed guide
├── ✏️ blockchain.py              # Updated with L2 template
├── prepare.py                   # Fund test accounts (existing)
├── tps_test.py                  # Run TPS test (existing)
├── logs_parser.py               # Analyze results (existing)
├── mnemonic.txt                 # Your seed phrase (edit this)
└── requirements.txt             # Python deps (existing)

Generated during deployment:
├── deployed_addresses.json      # All contract addresses
└── logs/
    ├── tps00.log ... tps09.log # Test logs
    ├── tps.log                  # Combined log
    ├── swaps.log                # Sorted transactions
    └── tps-results.log          # Final TPS calculation
```

---

**Ready to test your L2? Start with [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)! 🚀**
