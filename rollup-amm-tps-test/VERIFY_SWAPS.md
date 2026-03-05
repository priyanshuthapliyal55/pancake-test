# Quick Reference: Verify Swap Transactions

## Method 1: Using check_swaps.py (Recommended)

```bash
cd rollup-amm-tps-test

# Update addresses in check_swaps.py first
# ROUTER_ADDRESS, WETH_ADDRESS, CAKE_ADDRESS, FACTORY_ADDRESS

python3 check_swaps.py
```

Then select:
- **Option 1**: Check if pair has liquidity
- **Option 3**: Simulate a swap (no transaction)
- **Option 5**: Execute a test swap (0.00001 WETH)
- **Option 6**: Check recent swap events in last 100 blocks

---

## Method 2: Quick Python Commands

### Check Pair Exists and Has Liquidity

```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('http://your-rpc:8545'))

FACTORY_ABI = [{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"pair","type":"address"}],"stateMutability":"view","type":"function"}]

PAIR_ABI = [{"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"stateMutability":"view","type":"function"}]

factory = w3.eth.contract(address='YOUR_FACTORY_ADDRESS', abi=FACTORY_ABI)
pair_addr = factory.functions.getPair('WETH_ADDRESS', 'CAKE_ADDRESS').call()

if pair_addr == '0x0000000000000000000000000000000000000000':
    print("❌ Pair doesn't exist!")
else:
    print(f"✅ Pair: {pair_addr}")
    pair = w3.eth.contract(address=pair_addr, abi=PAIR_ABI)
    reserves = pair.functions.getReserves().call()
    print(f"Reserve0: {w3.from_wei(reserves[0], 'ether')}")
    print(f"Reserve1: {w3.from_wei(reserves[1], 'ether')}")
```

### Check Token Balance

```python
ERC20_ABI = [{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]

weth = w3.eth.contract(address='WETH_ADDRESS', abi=ERC20_ABI)
balance = weth.functions.balanceOf('YOUR_ACCOUNT').call()
print(f"WETH Balance: {w3.from_wei(balance, 'ether')}")
```

### Check Transaction Status

```python
# By transaction hash
tx_hash = '0xYourTransactionHash...'
receipt = w3.eth.get_transaction_receipt(tx_hash)

if receipt['status'] == 1:
    print(f"✅ Transaction successful!")
    print(f"Block: {receipt['blockNumber']}")
    print(f"Gas used: {receipt['gasUsed']}")
else:
    print(f"❌ Transaction failed!")
```

### Check for Swap Events

```python
PAIR_ABI_WITH_EVENTS = [
    {"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"stateMutability":"view","type":"function"},
    {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"sender","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount0In","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"amount1In","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"amount0Out","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"amount1Out","type":"uint256"},{"indexed":True,"internalType":"address","name":"to","type":"address"}],"name":"Swap","type":"event"}
]

pair = w3.eth.contract(address='PAIR_ADDRESS', abi=PAIR_ABI_WITH_EVENTS)

# Check last 100 blocks
current_block = w3.eth.block_number
swap_filter = pair.events.Swap.create_filter(
    fromBlock=current_block - 100,
    toBlock=current_block
)

events = swap_filter.get_all_entries()
print(f"Found {len(events)} swaps in last 100 blocks")

for event in events[-5:]:  # Show last 5
    print(f"\nBlock {event['blockNumber']}:")
    print(f"  Tx: {event['transactionHash'].hex()}")
    print(f"  Amount0In: {w3.from_wei(event['args']['amount0In'], 'ether')}")
    print(f"  Amount1Out: {w3.from_wei(event['args']['amount1Out'], 'ether')}")
```

---

## Method 3: Using Web3 CLI (cast from Foundry)

If you have Foundry installed:

```bash
# Check pair reserves
cast call PAIR_ADDRESS "getReserves()" --rpc-url http://your-rpc:8545

# Check WETH balance
cast call WETH_ADDRESS "balanceOf(address)" YOUR_ADDRESS --rpc-url http://your-rpc:8545

# Check transaction status
cast receipt TX_HASH --rpc-url http://your-rpc:8545

# Get recent block logs for Swap events
cast logs --from-block -100 --address PAIR_ADDRESS "Swap(address indexed,uint256,uint256,uint256,uint256,address indexed)" --rpc-url http://your-rpc:8545
```

---

## Method 4: Check During TPS Test

### Monitor in Real-Time

```bash
# Run TPS test with logging
python3 tps_test.py -n 0 2>&1 | tee logs/tps00.log

# In another terminal, check blocks
watch -n 1 'cast blockNumber --rpc-url http://your-rpc:8545'

# Check pair reserves changing
watch -n 2 'python3 -c "from web3 import Web3; w3=Web3(Web3.HTTPProvider(\"http://your-rpc:8545\")); pair=w3.eth.contract(address=\"PAIR_ADDR\", abi=[{\"inputs\":[],\"name\":\"getReserves\",\"outputs\":[{\"internalType\":\"uint112\",\"name\":\"_reserve0\",\"type\":\"uint112\"},{\"internalType\":\"uint112\",\"name\":\"_reserve1\",\"type\":\"uint112\"},{\"internalType\":\"uint32\",\"name\":\"_blockTimestampLast\",\"type\":\"uint32\"}],\"stateMutability\":\"view\",\"type\":\"function\"}]); r=pair.functions.getReserves().call(); print(f\"R0: {w3.from_wei(r[0], \'ether\')} R1: {w3.from_wei(r[1], \'ether\')}\")"'
```

### Check Test Results

After running the test:

```bash
# Count successful transactions in logs
grep "✅" logs/tps00.log | wc -l

# Check for errors
grep "❌\|Error\|Failed" logs/tps00.log

# Parse transaction hashes
grep "TX:" logs/tps00.log | head -5

# Verify specific transaction
python3 -c "
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('http://your-rpc:8545'))
receipt = w3.eth.get_transaction_receipt('0xTxHash...')
print(f'Status: {\"Success\" if receipt[\"status\"] == 1 else \"Failed\"}')
print(f'Block: {receipt[\"blockNumber\"]}')
"
```

---

## Method 5: Block Explorer (if available)

### If your blockchain has an explorer (like Etherscan):

1. **Go to Router contract page:**
   - Navigate to: `https://your-explorer/address/ROUTER_ADDRESS`
   - Click "Events" or "Logs" tab
   - Look for swap-related events

2. **Check specific transaction:**
   - Search for transaction hash
   - Verify "Status: Success"
   - Check "Event Logs" for Swap events

3. **View token transfers:**
   - Go to WETH token contract
   - Check recent transfers to/from Pair address

---

## Method 6: Direct RPC Calls

### Using curl:

```bash
# Get latest block
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  http://your-rpc:8545

# Get transaction receipt
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getTransactionReceipt","params":["0xTxHash..."],"id":1}' \
  http://your-rpc:8545

# Call pair.getReserves()
# (Need to encode function selector and call contract)
```

---

## Troubleshooting Checklist

If swaps aren't working:

- [ ] **Pair exists:** Run Method 1 to check pair address isn't 0x0...
- [ ] **Liquidity exists:** Pair reserves should be > 0
- [ ] **Balance sufficient:** Account has WETH to swap
- [ ] **Approval granted:** Router is approved to spend WETH
- [ ] **Gas price set:** Transaction gas price is sufficient
- [ ] **Deadline valid:** Swap deadline hasn't expired
- [ ] **Slippage OK:** amountOutMin isn't too high
- [ ] **Router address correct:** Using correct Router contract
- [ ] **Path correct:** [WETH, CAKE] in right order

---

## Quick Diagnostic Commands

```bash
# All-in-one check
python3 check_swaps.py
# Select option 8 (Run all checks)

# Or run individual checks
python3 -c "from check_swaps import *; check_pair_reserves()"
python3 -c "from check_swaps import *; check_balances()"
python3 -c "from check_swaps import *; simulate_swap(w3.to_wei(0.001, 'ether'))"
```

---

## Expected Output for Working Swaps

### Successful Swap Example:

```
📦 Deploying transaction...
   TX: 0x1234...abcd
   ⏳ Waiting for confirmation...
   ✅ Swap successful!

💰 CAKE received: 9.95423 CAKE
📊 Gas used: 125847
🔗 Block: 123456
```

### Pair with Liquidity:

```
✅ Pair exists at: 0x5678...efgh

Reserve0: 1.0 tokens
Reserve1: 10000.0 tokens

✅ Liquidity exists - swaps should work!
```
