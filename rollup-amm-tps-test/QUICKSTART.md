# Quick Start Guide - TPS Test on Your Blockchain

## Setup (5 minutes)

### 1. Install Dependencies
```bash
cd rollup-amm-tps-test
pip install -r requirements.txt
```

### 2. Add Your Mnemonic
Edit `mnemonic.txt` and replace the placeholder with your seed phrase:
```
your twelve word seed phrase goes here like this example text
```

⚠️ **Account 0 needs testnet ETH** - Get from https://sepoliafaucet.com/

### 3. Deploy Contracts (Sepolia)

**Option A: Automated (Recommended)**
```bash
./deploy.sh
```

**Option B: Manual**
```bash
# Deploy Factory
cd ../pancake-swap-core
npm install
npx truffle migrate --network sepolia

# Deploy Router (replace FACTORY_ADDRESS)
cd ../pancake-swap-periphery
npm install
FACTORY_ADDRESS=0xYourFactoryAddress npx truffle migrate --network sepolia
```

### 4. Deploy Test Token & Create Pair

Use Remix to deploy a simple ERC20 token or use the one in `/build/tokens/CAKEToken.sol`

Then create a pair and add liquidity:
```javascript
// Using web3 or ethers
factory.createPair(WETH_ADDRESS, CAKE_ADDRESS)
// Then add liquidity via Router
router.addLiquidity(...)
```

### 5. Update Configuration

Edit `blockchain.py` and replace the addresses:
```python
ChainId.SEPOLIA_TESTNET: NetworkData(
    addresses={
        Contract.PANCAKE_SMART_ROUTER: '0xYourRouterAddress',
        Token.CAKE: '0xYourTokenAddress',
        Token.WETH: '0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9',
    },
)
```

## Running the Test

### Prepare Accounts (one time)
```bash
python prepare.py
```
This funds 100 accounts with 0.002 ETH each and wraps/approves for trading.

### Run TPS Test

**Quick test (10 accounts):**
```bash
python tps_test.py -n 0 2>&1 | tee logs/tps00.log
```

**Full test (100 accounts from 10 IPs):**
```bash
# On 10 different machines or IPs, run:
python tps_test.py -n 0 2>&1 | tee logs/tps00.log  # accounts 0-9
python tps_test.py -n 1 2>&1 | tee logs/tps01.log  # accounts 10-19
# ... through n=9
```

### Analyze Results
```bash
cat logs/tps0*.log > logs/tps.log
python logs_parser.py tps.log SEPOLIA_TESTNET
```

## For Your Custom OP Stack Chain

If you have your own OP Stack rollup instead of Sepolia:

1. Update `blockchain.py` with your chain info:
```python
ChainId.MY_CHAIN = 12345  # your chain ID

MY_CHAIN: NetworkData(
    chain_id=12345,
    http_rpc_url='https://your-rpc-url.com',
    ws_rpc_url='wss://your-ws-rpc.com',
    addresses={...}
)
```

2. Update `tps_test.py` line 210:
```python
objects = [Trader(ChainId.MY_CHAIN, account, swap_txs_count=20) for account in accounts]
```

3. Deploy contracts to your chain using same process

## Troubleshooting

**"Insufficient funds" error:**
- Ensure account 0 has enough ETH
- Each of 100 accounts needs 0.002 ETH

**"Insufficient liquidity" in swaps:**
- Add more liquidity to the WETH/CAKE pair
- Need at least 1 WETH worth of depth

**RPC connection errors:**
- Check RPC URLs in blockchain.py
- Ensure WebSocket endpoint is accessible
- Some providers need API keys

**"Transaction underpriced":**
- Increase gas price in tps_test.py (line 84): `self.gas_price = 3 * self.w3.eth.gas_price`

## Expected Results

Sepolia (Ethereum testnet):
- Block time: ~12 seconds
- Expected TPS: 20-40 tx/s

Your OP Stack chain:
- Depends on block gas limit and block time
- OP Mainnet achieves ~140 tx/s
- Calculate: `max_tps = block_gas_limit / avg_swap_gas / block_time`
- Typical swap uses ~105k gas
