#!/usr/bin/env python3
"""
Analyze TPS during a specific test window with synchronized terminals
"""
import sys
from datetime import datetime, timedelta
from web3 import Web3

def main():
    # Connect to L2
    rpc_url = "http://46.165.235.105:8545"
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print(f"❌ Failed to connect to {rpc_url}")
        sys.exit(1)
    
    print("=" * 90)
    print("📊 TPS Analysis - Test Window Mode")
    print("=" * 90)
    
    # Get current block info
    latest_block_num = w3.eth.block_number
    latest_block = w3.eth.get_block(latest_block_num)
    latest_timestamp = latest_block.timestamp
    latest_time = datetime.fromtimestamp(latest_timestamp)
    
    print(f"Latest block: {latest_block_num}")
    print(f"Latest time:  {latest_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Ask user for time window
    print("Enter test window duration in minutes (or press Enter for last 5 minutes):")
    duration_input = input("> ").strip()
    duration_minutes = int(duration_input) if duration_input else 5
    
    print(f"\n🔍 Analyzing last {duration_minutes} minutes...")
    
    # Calculate time range
    start_time = latest_time - timedelta(minutes=duration_minutes)
    start_timestamp = int(start_time.timestamp())
    
    # Find blocks in range
    print("Scanning blocks...")
    blocks_in_range = []
    
    # Binary search for start block (approximate)
    low, high = max(0, latest_block_num - 1000), latest_block_num
    while low < high:
        mid = (low + high) // 2
        try:
            block = w3.eth.get_block(mid)
            if block.timestamp < start_timestamp:
                low = mid + 1
            else:
                high = mid
        except:
            low = mid + 1
    
    start_block_num = low
    
    # Collect all blocks in time range
    for block_num in range(start_block_num, latest_block_num + 1):
        try:
            block = w3.eth.get_block(block_num, full_transactions=False)
            if block.timestamp >= start_timestamp:
                blocks_in_range.append({
                    'number': block.number,
                    'timestamp': block.timestamp,
                    'tx_count': len(block.transactions),
                    'time': datetime.fromtimestamp(block.timestamp)
                })
        except Exception as e:
            print(f"Error fetching block {block_num}: {e}")
    
    if not blocks_in_range:
        print("❌ No blocks found in time range")
        return
    
    # Calculate statistics
    first_block = blocks_in_range[0]
    last_block = blocks_in_range[-1]
    time_span = last_block['timestamp'] - first_block['timestamp']
    total_txs = sum(b['tx_count'] for b in blocks_in_range)
    tx_counts = [b['tx_count'] for b in blocks_in_range]
    
    print("\n" + "=" * 90)
    print(f"📈 TPS Results for {duration_minutes}-minute window")
    print("=" * 90)
    print(f"Time Range:       {first_block['time'].strftime('%H:%M:%S')} - {last_block['time'].strftime('%H:%M:%S')}")
    print(f"Block Range:      {first_block['number']} - {last_block['number']}")
    print(f"Total Blocks:     {len(blocks_in_range)}")
    print(f"Time Span:        {time_span} seconds ({time_span/60:.2f} minutes)")
    print(f"Block Time:       {time_span / len(blocks_in_range):.2f} seconds avg")
    print()
    print(f"Total Txs:        {total_txs}")
    print(f"Average TPS:      {total_txs / time_span if time_span > 0 else 0:.2f}")
    print(f"Peak Block Txs:   {max(tx_counts)}")
    print(f"Min Block Txs:    {min(tx_counts)}")
    print(f"Avg Txs/Block:    {sum(tx_counts) / len(tx_counts):.2f}")
    print(f"Empty Blocks:     {sum(1 for c in tx_counts if c == 0)}")
    
    # Find peak TPS window (consecutive 5 blocks)
    if len(blocks_in_range) >= 5:
        best_tps = 0
        best_window_start = 0
        for i in range(len(blocks_in_range) - 4):
            window = blocks_in_range[i:i+5]
            window_txs = sum(b['tx_count'] for b in window)
            window_time = window[-1]['timestamp'] - window[0]['timestamp']
            window_tps = window_txs / window_time if window_time > 0 else 0
            if window_tps > best_tps:
                best_tps = window_tps
                best_window_start = i
        
        peak_window = blocks_in_range[best_window_start:best_window_start+5]
        print(f"\n🔥 Peak 5-Block Window:")
        print(f"   Blocks: {peak_window[0]['number']} - {peak_window[-1]['number']}")
        print(f"   TPS: {best_tps:.2f}")
        print(f"   Transactions: {sum(b['tx_count'] for b in peak_window)}")
    
    # Show top 10 busiest blocks
    print(f"\n🚀 Top 10 Busiest Blocks:")
    sorted_blocks = sorted(blocks_in_range, key=lambda x: x['tx_count'], reverse=True)[:10]
    for block in sorted_blocks:
        print(f"   Block {block['number']} ({block['time'].strftime('%H:%M:%S')}): {block['tx_count']} txs")
    
    # Show timeline visualization
    print(f"\n📊 Transaction Timeline (last {min(50, len(blocks_in_range))} blocks):")
    print(f"{'Block':<10} {'Time':<10} {'Txs':<6} {'Graph'}")
    print("-" * 90)
    
    recent_blocks = blocks_in_range[-min(50, len(blocks_in_range)):]
    max_txs = max(b['tx_count'] for b in recent_blocks) if recent_blocks else 1
    for block in recent_blocks:
        bar_width = int((block['tx_count'] / max_txs) * 50) if max_txs > 0 else 0
        bar = '█' * bar_width
        print(f"{block['number']:<10} {block['time'].strftime('%H:%M:%S'):<10} {block['tx_count']:<6} {bar}")
    
    print("\n" + "=" * 90)
    print("✅ Analysis complete!")
    print("=" * 90)
    
    # Calculate blocks per minute
    blocks_per_min = len(blocks_in_range) / (time_span / 60) if time_span > 0 else 0
    print(f"\nℹ️  Block production rate: {blocks_per_min:.2f} blocks/minute ({60/blocks_per_min:.2f}s per block)")

if __name__ == "__main__":
    main()
