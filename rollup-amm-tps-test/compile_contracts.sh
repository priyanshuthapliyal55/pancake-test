#!/bin/bash
# Compile all necessary contracts for deployment using Foundry

set -e

echo "========================================="
echo "  Compiling Pancake Swap Contracts"
echo "  Using Foundry/forge (fast & simple)"
echo "========================================="

# Make sure forge is in PATH
export PATH="$HOME/.foundry/bin:$PATH"

# Compile pancake-swap-core (Factory, Pair)
echo ""
echo "📦 Compiling pancake-swap-core..."
cd ../pancake-swap-core
forge build
echo "✅ Core contracts compiled"

# Compile pancake-swap-periphery (Router)
echo ""
echo "📦 Compiling pancake-swap-periphery..."
cd ../pancake-swap-periphery
forge build --skip test --skip "*Example*" --skip "*Migrator*" --skip "* Oracle*"
echo "✅ Periphery contracts compiled"

echo ""
echo "========================================="
echo "  ✅ All contracts compiled successfully!"
echo "========================================="
echo ""
echo "Compiled contracts are in:"
echo "  - pancake-swap-core/build/"
echo "  - pancake-swap-periphery/build/"
echo ""
echo "Next step: python deploy_l2.py"

echo ""
echo "========================================="
echo "  ✅ All contracts compiled successfully!"
echo "========================================="
echo ""
echo "Next step: Run python deploy_l2.py"
