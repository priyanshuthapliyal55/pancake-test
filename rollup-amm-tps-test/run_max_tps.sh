#!/bin/bash
# Run Maximum TPS Test - All 10 Traders in Parallel from One Terminal

TOKEN="${1:-0x29fB7b60A3375D5f1b4de0969381a2EF31830B5d}"
TXS="${2:-10000}"

echo "=========================================="
echo "🚀 MAXIMUM TPS TEST"
echo "=========================================="
echo "Token:           $TOKEN"
echo "Txs/Account:     $TXS"
echo "Total Accounts:  100 (10 traders × 10 accounts)"
echo "Total Txs:       $((TXS * 100))"
echo "=========================================="
echo ""

# Create logs directory
mkdir -p logs

# Kill any existing test processes
pkill -f "tps_test_transfers.py" 2>/dev/null || true
sleep 1

echo "Starting all 10 traders in parallel..."

# Launch all 10 traders as background processes
for i in {0..9}; do
    echo "  Launching trader $i..."
    python3 tps_test_transfers.py -n $i --token "$TOKEN" --txs $TXS > logs/trader_$i.log 2>&1 &
    PIDS[$i]=$!
    sleep 0.5  # Small delay to avoid overwhelming the startup
done

echo ""
echo "✅ All 10 traders launched!"
echo ""
echo "📊 Monitor progress:"
echo "   tail -f logs/trader_0.log"
echo "   tail -f logs/trader_*.log  # Watch all"
echo ""
echo "⏹️  Stop all traders:"
echo "   pkill -f tps_test_transfers.py"
echo ""
echo "⏳ Waiting for all traders to complete..."
echo ""

# Wait for all background processes
for pid in "${PIDS[@]}"; do
    wait $pid 2>/dev/null || echo "  Trader with PID $pid completed"
done

echo ""
echo "=========================================="
echo "✅ ALL TRADERS COMPLETED!"
echo "=========================================="
echo ""
echo "📈 Analyze results:"
echo "   python3 analyze_detailed.py"
echo ""
