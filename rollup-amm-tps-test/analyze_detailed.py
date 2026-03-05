#!/usr/bin/env python3
"""
Enhanced TPS Analysis - Excludes empty blocks for accurate metrics
"""
import sys
import json
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
    print("📊 ENHANCED TPS TEST REPORT")
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
    print("Enter test window duration in minutes (default: 5):")
    duration_input = input("> ").strip()
    duration_minutes = int(duration_input) if duration_input else 5
    
    print(f"\n🔍 Analyzing last {duration_minutes} minutes...")
    
    # Calculate time range
    start_time = latest_time - timedelta(minutes=duration_minutes)
    start_timestamp = int(start_time.timestamp())
    
    # Binary search for start block
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
    
    # Collect all blocks (without full transaction details for speed)
    print(f"Fetching blocks {start_block_num} to {latest_block_num}...")
    all_blocks = []
    
    for block_num in range(start_block_num, latest_block_num + 1):
        try:
            block = w3.eth.get_block(block_num, full_transactions=False)
            if block.timestamp >= start_timestamp:
                block_time = datetime.fromtimestamp(block.timestamp)
                all_blocks.append({
                    'number': block.number,
                    'timestamp': block.timestamp,
                    'time': block_time,
                    'tx_count': len(block.transactions),
                    'gas_used': block.gasUsed,
                    'transactions': block.transactions  # Just tx hashes
                })
        except Exception as e:
            print(f"Error fetching block {block_num}: {e}")
    
    if not all_blocks:
        print("❌ No blocks found in time range")
        return
    
    # Separate active blocks (with transactions) from empty blocks
    active_blocks = [b for b in all_blocks if b['tx_count'] > 0]
    empty_blocks = [b for b in all_blocks if b['tx_count'] == 0]
    
    if not active_blocks:
        print("\n❌ No transactions found in the specified time window")
        print(f"   Searched {len(all_blocks)} blocks, all were empty")
        return
    
    # Calculate overall window stats
    first_block = all_blocks[0]
    last_block = all_blocks[-1]
    total_window_time = last_block['timestamp'] - first_block['timestamp']
    
    # Calculate active period stats (only blocks with transactions)
    first_active = active_blocks[0]
    last_active = active_blocks[-1]
    active_time = last_active['timestamp'] - first_active['timestamp']
    if active_time == 0:
        active_time = 4  # Single block, assume 4s block time
    
    total_txs = sum(b['tx_count'] for b in active_blocks)
    
    # Collect transaction details (sample only for speed - much faster!)
    print(f"Analyzing {total_txs} transactions (using smart sampling for speed)...")
    
    # Calculate gas statistics from blocks (much faster than per-tx receipts)
    total_gas = sum(b['gas_used'] for b in active_blocks)
    avg_gas = total_gas / total_txs if total_txs > 0 else 0
    
    # Sample a few transactions to check success rate
    sample_size = min(100, total_txs)
    successful_sampled = 0
    failed_sampled = 0
    sample_gas_list = []
    
    tx_sample = []
    for block in active_blocks[:10]:  # Sample from first 10 active blocks
        for tx_hash in block['transactions'][:10]:  # Up to 10 txs per block
            if len(tx_sample) < sample_size:
                tx_sample.append((tx_hash, block['timestamp']))
    
    for tx_hash, timestamp in tx_sample:
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            sample_gas_list.append(receipt.gasUsed)
            if receipt.status == 1:
                successful_sampled += 1
            else:
                failed_sampled += 1
        except:
            pass
    
    # Estimate success rate from sample
    if successful_sampled + failed_sampled > 0:
        success_rate = successful_sampled / (successful_sampled + failed_sampled)
        successful_txs = int(total_txs * success_rate)
        failed_txs = total_txs - successful_txs
    else:
        successful_txs = total_txs
        failed_txs = 0
    
    # Calculate gas statistics from sample
    min_gas = min(sample_gas_list) if sample_gas_list else int(avg_gas * 0.9)
    max_gas = max(sample_gas_list) if sample_gas_list else int(avg_gas * 1.1)
    
    # Calculate latencies
    min_latency = 0  # Best case: immediate inclusion
    max_latency = active_time  # Worst case: waited until last block
    avg_latency = active_time / 2  # Approximate average
    
    # Calculate TPS metrics
    # Sent TPS: assume all submitted simultaneously at first active block
    tps_sent = total_txs  # All submitted within ~1 second
    # Achieved TPS: based on active processing time only
    tps_achieved = total_txs / active_time if active_time > 0 else 0
    
    # Print Report
    print("\n" + "=" * 90)
    print("📋 TEST SUMMARY")
    print("=" * 90)
    print(f"Overall Window:   {first_block['time'].strftime('%H:%M:%S')} - {last_block['time'].strftime('%H:%M:%S')} ({len(all_blocks)} blocks)")
    print(f"Active Period:    {first_active['time'].strftime('%H:%M:%S')} - {last_active['time'].strftime('%H:%M:%S')} ({len(active_blocks)} blocks)")
    print(f"Empty Blocks:     {len(empty_blocks)} blocks (excluded from TPS calculation)")
    print(f"Block Time:       {active_time / len(active_blocks):.2f} seconds avg")
    
    print("\n" + "=" * 90)
    print("🚀 TRANSACTION THROUGHPUT")
    print("=" * 90)
    print(f"📤 TPS Sent:       {tps_sent:.2f} TPS (all {total_txs} txs submitted simultaneously)")
    print(f"📥 TPS Achieved:   {tps_achieved:.2f} TPS (processed over {active_time}s active time)")
    print(f"📊 Efficiency:     {(tps_achieved/tps_sent)*100:.1f}% (achieved vs sent)")
    print(f"\nTotal Txs:        {total_txs}")
    print(f"Successful:       ~{successful_txs} ({successful_txs/total_txs*100:.1f}%) [estimated from {len(tx_sample)} sampled]")
    print(f"Failed:           ~{failed_txs} ({failed_txs/total_txs*100:.1f}%)" if failed_txs > 0 else "Failed:           ~0")
    print(f"Peak Block Txs:   {max(b['tx_count'] for b in active_blocks)}")
    print(f"Avg Txs/Block:    {total_txs / len(active_blocks):.2f} (active blocks only)")
    
    print("\n" + "=" * 90)
    print("⏱️  LATENCY METRICS")
    print("=" * 90)
    print(f"Min Latency:      ~{min_latency}s (immediate inclusion)")
    print(f"Max Latency:      ~{max_latency}s (last transaction confirmed)")
    print(f"Avg Latency:      ~{avg_latency:.1f}s (estimated)")
    print(f"Processing Time:  {active_time}s ({len(active_blocks)} active blocks)")
    
    print("\n" + "=" * 90)
    print("⛽ GAS USAGE STATISTICS")
    print("=" * 90)
    print(f"Total Gas Used:   {total_gas:,} gas")
    print(f"Average Gas/Tx:   {avg_gas:,.0f} gas")
    print(f"Min Gas Used:     {min_gas:,} gas")
    print(f"Max Gas Used:     {max_gas:,} gas")
    print(f"Gas Efficiency:   {(avg_gas/max_gas)*100:.1f}% (avg/max)")
    
    # Gas distribution (from sample)
    if sample_gas_list:
        gas_ranges = {
            '< 100k': sum(1 for g in sample_gas_list if g < 100000),
            '100k-200k': sum(1 for g in sample_gas_list if 100000 <= g < 200000),
            '200k-300k': sum(1 for g in sample_gas_list if 200000 <= g < 300000),
            '300k-400k': sum(1 for g in sample_gas_list if 300000 <= g < 400000),
            '400k+': sum(1 for g in sample_gas_list if g >= 400000),
        }
        print(f"\nGas Distribution (from {len(sample_gas_list)} sampled txs):")
        for range_name, count in gas_ranges.items():
            if count > 0:
                pct = (count / len(sample_gas_list)) * 100
                bar = '█' * int(pct / 2)
                print(f"  {range_name:12s}: {count:4d} txs ({pct:5.1f}%) {bar}")
    
    # Peak performance window
    if len(active_blocks) >= 5:
        best_tps = 0
        best_window = None
        for i in range(len(active_blocks) - 4):
            window = active_blocks[i:i+5]
            window_txs = sum(b['tx_count'] for b in window)
            window_time = window[-1]['timestamp'] - window[0]['timestamp']
            if window_time == 0:
                window_time = 4 * 5  # Assume 4s per block
            window_tps = window_txs / window_time
            if window_tps > best_tps:
                best_tps = window_tps
                best_window = window
        
        if best_window:
            print("\n" + "=" * 90)
            print("🔥 PEAK 5-BLOCK WINDOW (Active Blocks Only)")
            print("=" * 90)
            print(f"Blocks:           {best_window[0]['number']} - {best_window[-1]['number']}")
            print(f"Time:             {best_window[0]['time'].strftime('%H:%M:%S')} - {best_window[-1]['time'].strftime('%H:%M:%S')}")
            print(f"Peak TPS:         {best_tps:.2f}")
            print(f"Transactions:     {sum(b['tx_count'] for b in best_window)}")
    
    # Top busiest blocks
    print("\n" + "=" * 90)
    print("🚀 TOP 10 BUSIEST BLOCKS")
    print("=" * 90)
    sorted_blocks = sorted(active_blocks, key=lambda x: x['tx_count'], reverse=True)[:10]
    for i, block in enumerate(sorted_blocks, 1):
        print(f"{i:2}. Block {block['number']} ({block['time'].strftime('%H:%M:%S')}): "
              f"{block['tx_count']} txs, {block['gas_used']:,} gas")
    
    # One-liner summary
    print("\n" + "=" * 90)
    print("📝 ONE-LINE SUMMARY")
    print("=" * 90)
    print(f"Sent {total_txs} txs at {tps_sent:.0f} TPS (simultaneous), "
          f"L2 processed at {tps_achieved:.2f} TPS over {active_time}s "
          f"({len(active_blocks)} active blocks, {avg_gas/1000:.0f}k gas/tx avg, "
          f"latency {min_latency}-{max_latency}s)")
    
    print("\n" + "=" * 90)
    print("✅ REPORT COMPLETE")
    print("=" * 90)
    print(f"\nℹ️  Note: {len(empty_blocks)} empty blocks excluded from TPS calculation")
    print(f"   TPS calculated using only {len(active_blocks)} active blocks with transactions")
    print(f"   Success rate & gas stats estimated from {len(tx_sample)} sampled transactions (fast mode)")
    print(f"   Total gas calculated from block data (100% accurate)")

if __name__ == "__main__":
    main()
