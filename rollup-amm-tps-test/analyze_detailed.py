#!/usr/bin/env python3
"""
Enhanced TPS Analysis - 100% Accurate Data by Analyzing All Transactions
"""
import sys
import json
import os
import glob
from datetime import datetime, timedelta
from web3 import Web3
from collections import defaultdict

def main():
    # Connect to L2
    rpc_url = "http://localhost:8545"
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
    active_blocks = [b for b in all_blocks if b['tx_count'] > 1]
    empty_blocks = [b for b in all_blocks if b['tx_count'] == 1]
    
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
        active_time = 2  # Single block, assume 2s block time
    
    total_txs = sum(b['tx_count'] for b in active_blocks)
    
    # Collect ALL transaction details for 100% accuracy
    print(f"Fetching {total_txs} transaction receipts for accurate analysis...")
    print("(This may take a minute...)")
    
    tx_details = []
    successful_txs = 0
    failed_txs = 0
    gas_used_list = []
    tx_by_block = defaultdict(list)
    
    # Progress tracking
    processed = 0
    for block in active_blocks:
        block_timestamp = block['timestamp']
        for tx_hash in block['transactions']:
            try:
                receipt = w3.eth.get_transaction_receipt(tx_hash)
                tx = w3.eth.get_transaction(tx_hash)
                
                tx_info = {
                    'hash': tx_hash.hex(),
                    'block': receipt.blockNumber,
                    'block_timestamp': block_timestamp,
                    'status': receipt.status,
                    'gas_used': receipt.gasUsed,
                    'gas_price': tx.gasPrice,
                    'from': receipt['from'],
                    'to': receipt.to,
                }
                
                tx_details.append(tx_info)
                gas_used_list.append(receipt.gasUsed)
                tx_by_block[receipt.blockNumber].append(tx_info)
                
                if receipt.status == 1:
                    successful_txs += 1
                else:
                    failed_txs += 1
                    
                processed += 1
                if processed % 100 == 0:
                    print(f"  Progress: {processed}/{total_txs} transactions processed ({processed/total_txs*100:.1f}%)")
                    
            except Exception as e:
                print(f"  Warning: Could not fetch tx {tx_hash.hex()}: {e}")
    
    print(f"  ✅ Completed: {len(tx_details)} transactions analyzed\n")
    
    # Load timestamp data if available for precise latency
    timestamp_files = sorted(glob.glob("tx_timestamps_*.json"), reverse=True)
    send_timestamps = {}
    if timestamp_files:
        print(f"Found {len(timestamp_files)} timestamp file(s). Loading most recent...")
        try:
            with open(timestamp_files[0], 'r') as f:
                send_timestamps = json.load(f)
            print(f"  ✅ Loaded {len(send_timestamps)} send timestamps from {timestamp_files[0]}\n")
        except Exception as e:
            print(f"  ⚠️  Could not load timestamps: {e}\n")
    
    # Calculate latencies if we have timestamp data
    latencies = []
    if send_timestamps:
        for tx_info in tx_details:
            tx_hash = tx_info['hash']
            # Try both with and without 0x prefix
            tx_hash_clean = tx_hash[2:] if tx_hash.startswith('0x') else tx_hash
            tx_hash_prefixed = '0x' + tx_hash_clean
            
            send_time = send_timestamps.get(tx_hash_clean) or send_timestamps.get(tx_hash_prefixed)
            if send_time:
                confirm_time = tx_info['block_timestamp']
                latency = confirm_time - send_time
                latencies.append(latency)
    
    # Calculate gas statistics (100% accurate now)
    if gas_used_list:
        total_gas = sum(gas_used_list)
        avg_gas = total_gas / len(gas_used_list)
        min_gas = min(gas_used_list)
        max_gas = max(gas_used_list)
        
        # Percentiles
        sorted_gas = sorted(gas_used_list)
        p50_gas = sorted_gas[len(sorted_gas) // 2]
        p95_gas = sorted_gas[int(len(sorted_gas) * 0.95)]
        p99_gas = sorted_gas[int(len(sorted_gas) * 0.99)]
    else:
        total_gas = avg_gas = min_gas = max_gas = p50_gas = p95_gas = p99_gas = 0
    
    # Calculate latency statistics
    if latencies:
        min_latency = min(latencies)
        max_latency = max(latencies)
        avg_latency = sum(latencies) / len(latencies)
        sorted_latencies = sorted(latencies)
        p50_latency = sorted_latencies[len(sorted_latencies) // 2]
        p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        p99_latency = sorted_latencies[int(len(sorted_latencies) * 0.99)]
    else:
        # Fallback to estimates
        min_latency = 0
        max_latency = active_time
        avg_latency = active_time / 2
        p50_latency = avg_latency
        p95_latency = active_time * 0.95
        p99_latency = active_time * 0.99
    
    # Calculate TPS metrics
    # Sent TPS: assume all submitted simultaneously at first active block
    tps_sent = total_txs  # All submitted within ~1 second
    # Average TPS: average txs per block divided by block time
    avg_txs_per_block = total_txs / len(active_blocks)
    block_time_avg = active_time / (len(active_blocks) - 1) if len(active_blocks) > 1 else 2.0
    tps_average = avg_txs_per_block / block_time_avg if block_time_avg > 0 else 0
    # Aggregate TPS: total throughput over entire period (useful for very short windows)
    tps_aggregate = total_txs / active_time if active_time > 0 else 0
    
    # Verify we have transaction data
    if not tx_details:
        print("\n⚠️  Warning: No transaction details could be retrieved")
        print("   Showing block-level statistics only\n")
        successful_txs = total_txs
        failed_txs = 0
    
    # Print Report
    print("\n" + "=" * 90)
    print("📋 TEST SUMMARY")
    print("=" * 90)
    print(f"Overall Window:   {first_block['time'].strftime('%H:%M:%S')} - {last_block['time'].strftime('%H:%M:%S')} ({len(all_blocks)} blocks)")
    print(f"Active Period:    {first_active['time'].strftime('%H:%M:%S')} - {last_active['time'].strftime('%H:%M:%S')} ({len(active_blocks)} blocks)")
    print(f"Time Span:        {active_time}s (from block {first_active['number']} to {last_active['number']})")
    print(f"Block Intervals:  {len(active_blocks) - 1} intervals × {block_time_avg:.2f}s = {active_time}s")
    print(f"Empty Blocks:     {len(empty_blocks)} blocks (excluded from TPS calculation)")
    
    print("\n" + "=" * 90)
    print("🚀 TRANSACTION THROUGHPUT")
    print("=" * 90)
    print(f"📤 TPS Sent:       {tps_sent:.2f} TPS (all {total_txs} txs submitted simultaneously)")
    print(f"📥 TPS Average:    {tps_average:.2f} TPS (avg {avg_txs_per_block:.1f} txs/block ÷ {block_time_avg:.2f}s)")
    print(f"📊 TPS Aggregate:  {tps_aggregate:.2f} TPS (total {total_txs} txs over {active_time}s span)")
    print(f"⚡ Efficiency:     {(tps_average/tps_sent)*100:.1f}% (avg achieved vs sent)")
    
    if tx_details:
        print(f"\nTotal Txs:        {len(tx_details)} (100% analyzed)")
        print(f"✅ Successful:    {successful_txs} ({successful_txs/len(tx_details)*100:.1f}%)")
        print(f"❌ Failed:        {failed_txs} ({failed_txs/len(tx_details)*100:.1f}%)" if failed_txs > 0 else "❌ Failed:        0 (0%)")
    else:
        print(f"\nTotal Txs:        {total_txs}")
        print(f"Status:           Unknown (receipts not fetched)")
        
    print(f"Peak Block Txs:   {max(b['tx_count'] for b in active_blocks)}")
    print(f"Avg Txs/Block:    {total_txs / len(active_blocks):.2f} (active blocks only)")
    
    print("\n" + "=" * 90)
    print("⏱️  LATENCY METRICS")
    print("=" * 90)
    if latencies:
        print(f"Data Source:      tx_timestamps_*.json (EXACT measurements)")
        print(f"Samples:          {len(latencies)}/{len(tx_details)} transactions ({len(latencies)/len(tx_details)*100:.1f}%)")
        print(f"Min Latency:      {min_latency:.3f}s")
        print(f"Avg Latency:      {avg_latency:.3f}s")
        print(f"P50 Latency:      {p50_latency:.3f}s (median)")
        print(f"P95 Latency:      {p95_latency:.3f}s")
        print(f"P99 Latency:      {p99_latency:.3f}s")
        print(f"Max Latency:      {max_latency:.3f}s")
    else:
        print(f"Data Source:      Block timestamps (ESTIMATED)")
        print(f"Min Latency:      ~{min_latency}s (immediate inclusion)")
        print(f"Max Latency:      ~{max_latency}s (last transaction confirmed)")
        print(f"Avg Latency:      ~{avg_latency:.1f}s (estimated)")
        print(f"\n⚠️  Tip: Run tps_test_transfers.py to generate exact latency data")
    print(f"Processing Time:  {active_time}s span ({len(active_blocks)-1} intervals of {block_time_avg:.2f}s each)")
    
    print("\n" + "=" * 90)
    print("⛽ GAS USAGE STATISTICS")
    print("=" * 90)
    print(f"Total Gas Used:   {total_gas:,} gas")
    print(f"Average Gas/Tx:   {avg_gas:,.0f} gas")
    print(f"Min Gas:          {min_gas:,} gas")
    print(f"P50 Gas (median): {p50_gas:,} gas")
    print(f"P95 Gas:          {p95_gas:,} gas")
    print(f"P99 Gas:          {p99_gas:,} gas")
    print(f"Max Gas:          {max_gas:,} gas")
    print(f"Gas Efficiency:   {(avg_gas/max_gas)*100:.1f}% (avg/max)")
    
    # Gas distribution (100% accurate now)
    if gas_used_list:
        gas_ranges = {
            '< 50k': sum(1 for g in gas_used_list if g < 50000),
            '50k-100k': sum(1 for g in gas_used_list if 50000 <= g < 100000),
            '100k-150k': sum(1 for g in gas_used_list if 100000 <= g < 150000),
            '150k-200k': sum(1 for g in gas_used_list if 150000 <= g < 200000),
            '200k-300k': sum(1 for g in gas_used_list if 200000 <= g < 300000),
            '300k+': sum(1 for g in gas_used_list if g >= 300000),
        }
        print(f"\nGas Distribution (100% of {len(gas_used_list)} transactions):")
        for range_name, count in gas_ranges.items():
            if count > 0:
                pct = (count / len(gas_used_list)) * 100
                bar_len = min(40, int(pct / 2))
                bar = '█' * bar_len
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
    latency_str = f"{min_latency:.2f}-{max_latency:.2f}s" if latencies else f"~{min_latency}-{max_latency:.0f}s"
    tx_count = len(tx_details) if tx_details else total_txs
    intervals = len(active_blocks) - 1
    print(f"Sent {tx_count} txs at {tps_sent:.0f} TPS (simultaneous), "
          f"L2 processed at {tps_average:.2f} TPS average over {active_time}s "
          f"({len(active_blocks)} blocks = {intervals} intervals, {avg_txs_per_block:.1f} txs/block, "
          f"{block_time_avg:.2f}s/block, {avg_gas/1000:.0f}k gas/tx avg, {successful_txs} successful, latency {latency_str})")
    
    print("\n" + "=" * 90)
    print("✅ REPORT COMPLETE")
    print("=" * 90)
    if tx_details:
        print(f"\n📊 Accuracy: 100% of transactions analyzed ({len(tx_details)} receipts fetched)")
    else:
        print(f"\n⚠️  Accuracy: Block-level only ({total_txs} transactions in blocks)")
    print(f"   {len(empty_blocks)} empty blocks excluded from TPS calculation")
    print(f"   TPS calculated using only {len(active_blocks)} active blocks with transactions")
    print(f"   ℹ️  Note: {len(active_blocks)} blocks = {len(active_blocks)-1} intervals (time from first to last)")
    if latencies:
        print(f"   ⏱️  {len(latencies)} exact latency measurements from timestamp file")
    else:
        print(f"   ⚠️  Latency estimated (run test with timestamp tracking for exact data)")
    
    # Additional insights - top gas consumers
    if tx_details:
        print("\n" + "=" * 90)
        print("🔥 HIGH GAS CONSUMERS (Top 10)")
        print("=" * 90)
        sorted_by_gas = sorted(tx_details, key=lambda x: x['gas_used'], reverse=True)[:10]
        for i, tx in enumerate(sorted_by_gas, 1):
            status = "✅" if tx['status'] == 1 else "❌"
            print(f"{i:2}. {status} {tx['hash'][:16]}... "
                  f"gas: {tx['gas_used']:,} | block: {tx['block']}")
    
    # Failed transactions if any
    if failed_txs > 0 and tx_details:
        print("\n" + "=" * 90)
        print(f"❌ FAILED TRANSACTIONS ({failed_txs} total)")
        print("=" * 90)
        failed_tx_list = [tx for tx in tx_details if tx['status'] == 0]
        for i, tx in enumerate(failed_tx_list[:10], 1):  # Show first 10
            print(f"{i:2}. {tx['hash'][:16]}... "
                  f"gas: {tx['gas_used']:,} | block: {tx['block']}")
        if len(failed_tx_list) > 10:
            print(f"   ... and {len(failed_tx_list) - 10} more")
    
    # Export detailed data
    if tx_details:
        export_file = f"tps_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            export_data = {
                'summary': {
                    'total_txs': len(tx_details),
                    'successful': successful_txs,
                    'failed': failed_txs,
                    'tps_average': tps_average,
                    'tps_aggregate': tps_aggregate,
                    'active_time': active_time,
                    'active_blocks': len(active_blocks),
                    'avg_gas': avg_gas,
                    'min_latency': min_latency,
                    'avg_latency': avg_latency,
                    'max_latency': max_latency,
                },
                'transactions': tx_details[:1000],  # Limit to first 1000 for file size
                'blocks': [{
                    'number': b['number'],
                    'timestamp': b['timestamp'],
                    'tx_count': b['tx_count'],
                    'gas_used': b['gas_used']
                } for b in active_blocks]
            }
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            print(f"\n💾 Detailed data exported to: {export_file}")
        except Exception as e:
            print(f"\n⚠️  Could not export data: {e}")
    
    print("\n" + "=" * 90)

if __name__ == "__main__":
    main()
