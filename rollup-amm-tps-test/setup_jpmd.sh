#!/bin/bash
# Setup and deploy full JPMD token (upgradeable with proxy)

set -e

echo "=================================================="
echo "🔧 JPMD Token Deployment Setup"
echo "=================================================="
echo ""

# Check if foundry is installed
if ! command -v forge &> /dev/null; then
    echo "❌ Foundry not found!"
    echo ""
    echo "Install Foundry first:"
    echo "  curl -L https://foundry.paradigm.xyz | bash"
    echo "  foundryup"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found!"
    echo ""
    echo "Install Node.js and npm first:"
    echo "  Ubuntu: sudo apt install nodejs npm"
    echo "  macOS:  brew install node"
    exit 1
fi

echo "✅ Prerequisites installed"
echo ""

# Install dependencies
echo "📦 Installing OpenZeppelin contracts..."
npm install --save @openzeppelin/contracts@^5.0.2 @openzeppelin/contracts-upgradeable@^5.0.2
echo ""

# Install and compile with Solc 0.8.20
echo "📥 Installing Solc 0.8.20..."
svm install 0.8.20 || true
echo ""

# Compile contracts
echo "🔨 Compiling contracts with Solc 0.8.20..."
forge build --use 0.8.20
echo ""

if [ ! -f "out/Token.sol/Token.json" ]; then
    echo "❌ Compilation failed!"
    exit 1
fi

echo "✅ Contracts compiled successfully"
echo ""

# Make deploy script executable
chmod +x deploy_jpmd_full.py

echo "=================================================="
echo "✅ Setup Complete!"
echo "=================================================="
echo ""
echo "🚀 Deploy JPMD token:"
echo "   python deploy_jpmd_full.py"
echo ""
echo "⚙️  Don't forget to update the RPC URL in deploy_jpmd_full.py"
echo "    (currently set to http://localhost:8545)"
echo "=================================================="
