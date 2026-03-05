#!/usr/bin/env python3
"""
Calculate TPS from test results by examining transaction receipts
"""
import json
import sys
from pathlib import Path
from web3 import Web3
from collections import defaultdict

def main():
    # Connect to L2
    rpc_url = "http://46.165.235.105:8545"
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print(f"❌ Failed to connect to {rpc_url}")
        sys.exit(1)
    
    print("=" * 70)
    print("📊 TPS Analysis for Swap Transactions")
    print("=" * 70)
    
    # Read the test output file - you'll need to provide the path
    # For now, let's query recent blocks
    
    latest_block_num = w3.eth.block_number
    print(f"Latest block: {latest_block_num}\n")
   
    # Analyze last 100 blocks
    print("Analyzing recent blocks...")
    blocks_info = []
    tx_counts = []
    
    for block_num in range(latest_block_num - 99, latest_block_num + 1):
        try:
            block = w3.eth.get_block(block_num, full_transactions=False)
            blocks_info.append({
                'number': block.number,
                'timestamp': block.timestamp,
                'tx_count': len(block.transactions)
            })
            tx_counts.append(len(block.transactions))
        except Exception as e:
            print(f"Error fetching block {block_num}: {e}")
    
    if not blocks_info:
        print("No blocks retrieved")
        return
    
    # Calculate TPS
    first_block = blocks_info[0]
    last_block = blocks_info[-1]
    time_span = last_block['timestamp'] - first_block['timestamp']
    total_txs = sum(tx_counts)
    
    print(f"\n📈 Results for last 100 blocks:")
    print(f"   Block range: {first_block['number']} - {last_block['number']}")
    print(f"   Time span: {time_span} seconds ({time_span/60:.2f} minutes)")
    print(f"   Total transactions: {total_txs}")
    print(f"   Average TPS: {total_txs / time_span if time_span > 0 else 0:.2f}")
    print(f"   Peak block tx count: {max(tx_counts)}")
    print(f"   Min block tx count: {min(tx_counts)}")
    print(f"   Avg txs per block: {sum(tx_counts) / len(tx_counts):.2f}")
    
    # Find blocks with highest transaction counts
    print(f"\n🔥 Top 10 busiest blocks:")
    sorted_blocks = sorted(blocks_info, key=lambda x: x['tx_count'], reverse=True)[:10]
    for block in sorted_blocks:
        print(f"   Block {block['number']}: {block['tx_count']} transactions")
    
    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
