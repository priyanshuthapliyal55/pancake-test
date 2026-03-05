# Deployment Guide for Sepolia TPS Test

## Prerequisites

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get Sepolia ETH**
   - Use faucet: https://sepoliafaucet.com/
   - You'll need ~0.5 ETH for deployment + testing

3. **Set Up Mnemonic**
   - Create a new wallet mnemonic or use existing one
   - Add it to `mnemonic.txt`
   - Account 0 will be the deployer/funder

## Step 1: Deploy DEX Contracts

Navigate to the pancake-swap-core directory and deploy:

```bash
cd ../pancake-swap-core
npm install
npm run compile
```

Deploy PancakeFactory and PancakeRouter:
- PancakeFactory
- WETH9 (or use existing Sepolia WETH: 0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9)
- Create token pairs (WETH/TestToken)
- PancakeRouter02

**Known Sepolia Addresses:**
- WETH9: `0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9`

## Step 2: Deploy Test Token (CAKE equivalent)

Deploy an ERC20 token or use existing testnet tokens:
- Deploy from: `pancake-swap-testnet/build/tokens/CAKEToken.sol`
- Mint sufficient supply for testing

## Step 3: Create Liquidity Pool

1. Add liquidity to WETH/CAKE pair
2. Need enough depth for 2000+ swaps of 1 Gwei each
3. Recommended: Add at least 1 WETH + equivalent CAKE

## Step 4: Update blockchain.py

After deployment, update addresses in `blockchain.py`:

```python
ChainId.SEPOLIA_TESTNET: NetworkData(
    addresses={
        Contract.PANCAKE_SMART_ROUTER: '0xYourRouter02Address',
        Token.CAKE: '0xYourCakeTokenAddress',
        Token.WETH: '0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9',
    },
)
```

## Step 5: Prepare Accounts

```bash
# Fund 100 test accounts
python prepare.py
```

This will:
- Transfer 0.002 ETH to each of 100 accounts
- Wrap ETH to WETH
- Approve router to spend WETH

## Step 6: Run TPS Test

For small test (single machine):
```bash
python tps_test.py -n 0 2>&1 | tee logs/tps00.log
```

For full test (10 machines/IPs):
```bash
# On each machine/IP, run different index:
python tps_test.py -n 0 2>&1 | tee logs/tps00.log  # Machine 1
python tps_test.py -n 1 2>&1 | tee logs/tps01.log  # Machine 2
# ... etc
```

## Step 7: Analyze Results

```bash
# Combine logs
cat logs/tps0*.log > logs/tps.log

# Parse and calculate TPS
python logs_parser.py
```

## Quick Deployment Script

You can also use Hardhat/Foundry for deployment. Example with Foundry:

```bash
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Deploy Factory
forge create --rpc-url https://rpc.sepolia.org \
  --private-key YOUR_PRIVATE_KEY \
  pancake-swap-core/contracts/PancakeFactory.sol:PancakeFactory \
  --constructor-args YOUR_ADDRESS

# Deploy Router
forge create --rpc-url https://rpc.sepolia.org \
  --private-key YOUR_PRIVATE_KEY \
  pancake-swap-periphery/contracts/PancakeRouter.sol:PancakeRouter \
  --constructor-args FACTORY_ADDRESS WETH_ADDRESS
```

## Troubleshooting

- **Insufficient liquidity**: Add more to the pool
- **RPC rate limits**: Use Infura/Alchemy with API key
- **Gas too high**: Sepolia has lower gas than mainnet, but adjust if needed
- **Nonce errors**: Clear pending transactions or wait

## Expected TPS on Sepolia

Sepolia has similar block time/gas limits to Ethereum mainnet:
- Block time: ~12 seconds
- Gas limit: 30M per block
- Expected TPS: ~20-40 tx/s (depends on network congestion)
