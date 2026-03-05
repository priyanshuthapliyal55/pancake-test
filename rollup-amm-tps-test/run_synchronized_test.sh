#!/bin/bash
# Synchronized TPS Test Runner
# Run this in multiple terminals for coordinated stress testing

echo "════════════════════════════════════════════════════════════════"
echo "🚀 Synchronized TPS Test"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "How many terminals are you running? (1-10)"
read -p "> " terminal_count

echo ""
echo "Which terminal is this? (1-$terminal_count)"
read -p "> " terminal_num

# Calculate account index
account_index=$((terminal_num - 1))

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Terminal $terminal_num/$terminal_count"
echo "Will test accounts: $(($account_index * 10))-$(($account_index * 10 + 9))"
echo "Transactions: 200 (10 accounts × 20 swaps each)"
echo ""
echo "This terminal will wait and synchronize with others."
echo "All terminals will start at the next 5-minute mark."
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Press Enter to start waiting..."
read

# Run the test
python3 tps_test.py -n $account_index

echo ""
echo "✅ Test completed in Terminal $terminal_num!"
echo ""
echo "After all terminals complete, analyze results with:"
echo "  python3 analyze_test_window.py"
