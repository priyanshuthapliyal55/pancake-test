#!/bin/bash

# Deployment script for Sepolia testnet
# This deploys PancakeSwap contracts and prepares for TPS testing

echo "=== PancakeSwap Sepolia Deployment ==="
echo ""

# Check mnemonic
if [ ! -f "mnemonic.txt" ] || grep -q "<enter mnemonic here>" mnemonic.txt; then
    echo "ERROR: Please add your mnemonic to mnemonic.txt"
    exit 1
fi

echo "Step 1: Deploy Core Contracts (Factory)"
cd ../pancake-swap-core
echo "Installing dependencies..."
npm install

echo "Deploying to Sepolia..."
npx truffle migrate --network sepolia

echo ""
echo "Step 2: Copy Factory address from output above"
read -p "Enter Factory address: " FACTORY_ADDRESS

echo ""
echo "Step 3: Deploy Router"
cd ../pancake-swap-periphery
npm install

echo "Deploying Router with Factory: $FACTORY_ADDRESS"
FACTORY_ADDRESS=$FACTORY_ADDRESS npx truffle migrate --network sepolia

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. Deploy a test token (CAKE) or use existing token"
echo "2. Create pair using Factory.createPair(WETH, CAKE)"
echo "3. Add liquidity to the pair"
echo "4. Update addresses in rollup-amm-tps-test/blockchain.py"
echo "5. Run: python prepare.py to fund test accounts"
echo "6. Run: python tps_test.py -n 0 to execute TPS test"
