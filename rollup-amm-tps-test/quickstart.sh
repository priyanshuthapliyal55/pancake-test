#!/bin/bash
# Quick Start Script - Run everything in one go

set -e  # Exit on error

echo "========================================="
echo "  🚀 L2 TPS Test - Quick Start"
echo "========================================="
echo ""

# Check if mnemonic exists
if [ ! -f "mnemonic.txt" ]; then
    echo "❌ mnemonic.txt not found!"
    echo "   Create it first with your seed phrase"
    exit 1
fi

echo "Step 1: Installing Python dependencies..."
pip install -q -r requirements.txt
echo "✅ Python dependencies installed"
echo ""

echo "Step 2: Compiling contracts..."
./compile_contracts.sh
echo ""

echo "Step 3: Ready to deploy!"
echo ""
echo "⚠️  Before continuing:"
echo "   1. Edit deploy_l2.py with your L2 configuration:"
echo "      - L2_RPC_URL"
echo "      - L2_CHAIN_ID"
echo "      - L2_NAME"
echo "   2. Make sure account 0 has native tokens on your L2"
echo ""
read -p "Press Enter when ready to deploy contracts..."
echo ""

echo "Step 4: Deploying contracts to your L2..."
python deploy_l2.py
echo ""

echo "Step 5: Update blockchain.py..."
echo "   Check deploy_l2.py output for the exact code to add"
echo "   Add your L2 configuration to blockchain.py"
echo ""
read -p "Press Enter after updating blockchain.py..."
echo ""

echo "Step 6: Preparing test accounts..."
python prepare.py
echo ""

echo "Step 7: Running quick TPS test (10 accounts)..."
mkdir -p logs
python tps_test.py -n 0 2>&1 | tee logs/tps00.log
echo ""

echo "Step 8: Analyzing results..."
python logs_parser.py
echo ""

echo "========================================="
echo "  🎉 Quick start complete!"
echo "========================================="
echo ""
echo "For full test (100 accounts):"
echo "  Run from 10 different IPs:"
echo "  python tps_test.py -n 0  # accounts 0-9"
echo "  python tps_test.py -n 1  # accounts 10-19"
echo "  ..."
echo "  python tps_test.py -n 9  # accounts 90-99"
echo ""
echo "Then combine and analyze:"
echo "  cat logs/tps0*.log > logs/tps.log"
echo "  python logs_parser.py"
echo ""
echo "See COMPLETE_SETUP_GUIDE.md for details"
