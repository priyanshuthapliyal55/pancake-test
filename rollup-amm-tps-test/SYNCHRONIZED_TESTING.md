# 🚀 Synchronized TPS Testing Guide

## Why Synchronized Testing?

For accurate TPS measurements, all transactions should hit the network **at the same time** from multiple terminals. This creates real network stress and shows true throughput capacity.

## How It Works

1. **Open multiple terminals** (recommended: 5-10)
2. **Start the test in each terminal** - they will wait
3. **All terminals synchronize** to the next 5-minute mark (e.g., 14:50:00, 14:55:00)
4. **Bang!** All terminals fire transactions simultaneously
5. **Analyze the test window** to measure peak TPS

---

## 🎯 Quick Start

### Method 1: Interactive Script (Easiest)

Open **5 terminals** and run in each:
```bash
./run_synchronized_test.sh
```

Follow the prompts:
- Terminal 1: Select terminal 1/5
- Terminal 2: Select terminal 2/5
- ... and so on

All terminals will wait and start together at the next 5-minute mark.

---

### Method 2: Manual Command

If you prefer direct control:

**Terminal 1:**
```bash
python3 tps_test.py -n 0  # Accounts 0-9
```

**Terminal 2:**
```bash
python3 tps_test.py -n 1  # Accounts 10-19
```

**Terminal 3:**
```bash
python3 tps_test.py -n 2  # Accounts 20-29
```

**Terminal 4:**
```bash
python3 tps_test.py -n 3  # Accounts 30-39
```

**Terminal 5:**
```bash
python3 tps_test.py -n 4  # Accounts 40-49
```

Each shows:
```
[2026-02-27 14:47:23] Time now: 2026-02-27 14:47:23
[2026-02-27 14:47:23] Scheduled at: 2026-02-27 14:50:00
```

All wait until 14:50:00, then **BOOM** - simultaneous execution!

---

## 📊 Analyze Results

After all terminals complete:

```bash
python3 analyze_test_window.py
```

Enter test duration (e.g., `5` for 5 minutes) to see:
- **Peak TPS** during the test window
- **Top 10 busiest blocks**
- **Transaction timeline** visualization
- **5-block peak window** TPS

---

## 📈 What Each Configuration Tests

| Terminals | Accounts | Total Swaps | Network Load |
|-----------|----------|-------------|--------------|
| 1 | 10 | 200 | Light |
| 2 | 20 | 400 | Moderate |
| 5 | 50 | 1,000 | Heavy |
| 10 | 100 | 2,000 | Maximum |

**Each account sends 20 swaps** (alternating WETH↔CAKE), so:
- 5 terminals = 1,000 swaps hitting simultaneously
- 10 terminals = 2,000 swaps hitting simultaneously

---

## ⏰ Timing Details

### Synchronization Points
Tests sync to **every 5 minutes**: 
- 14:50:00
- 14:55:00
- 15:00:00
- etc.

### Minimum Wait
Script requires **60+ seconds** before sync point. If you start at 14:49:30, it will sync to 14:55:00 (not 14:50:00).

---

## 🔍 What to Look For

### Good TPS Performance:
✅ Peak 5-block window shows high TPS (10+ TPS)  
✅ Busy blocks have 50+ transactions  
✅ Few empty blocks during test window  
✅ Consistent block times

### Signs of Congestion:
⚠️ Transactions taking multiple blocks to confirm  
⚠️ Many empty blocks mixed with full ones  
⚠️ Increasing block times  

---

## 💡 Pro Tips

1. **Wait between tests**: Let the chain settle for 5 minutes between test runs

2. **Check account balances**: If tests fail, accounts may need refunding:
   ```bash
   python3 prepare.py
   ```

3. **Monitor live**: In another terminal, watch blocks in real-time:
   ```bash
   watch -n 2 'python3 -c "from web3 import Web3; w3=Web3(Web3.HTTPProvider(\"http://46.165.235.105:8545\")); b=w3.eth.get_block(\"latest\"); print(f\"Block: {b.number}, Txs: {len(b.transactions)}, Time: {b.timestamp}\")"'
   ```

4. **Test progression**:
   - Start with 2 terminals
   - Then 5 terminals
   - Finally 10 terminals for maximum stress

---

## 📝 Example Test Session

```bash
# Terminal 1
./run_synchronized_test.sh
> How many terminals? 5
> Which terminal? 1
# Waits until next 5-min mark...
# Executes 200 swaps
# Done!

# Terminal 2
./run_synchronized_test.sh
> How many terminals? 5
> Which terminal? 2
# Waits until same 5-min mark...
# Executes 200 swaps
# Done!

# ... repeat for terminals 3, 4, 5 ...

# After all complete:
python3 analyze_test_window.py
> Enter test window: 5

# Results show:
#   Average TPS: 15.23
#   Peak 5-Block Window TPS: 28.5
#   Peak Block: 182 transactions
```

---

## 🎓 Understanding the Results

**Average TPS** = Total transactions / Total time  
- Includes empty blocks between bursts
- Good for overall throughput

**Peak Window TPS** = Best 5 consecutive blocks  
- Shows maximum sustained throughput
- Best measure of true capacity

**Peak Block Txs** = Most transactions in one block  
- Shows block capacity limit
- L2 consensus/gas limits

---

## 🆘 Troubleshooting

### "Launch is too soon"
Started too close to 5-minute mark. Wait and try again at next mark.

### "Insufficient funds" errors
Accounts need more ETH/WETH:
```bash
python3 prepare.py
```

### Test completes instantly
Check that `wait_until_target_time()` is uncommented in tps_test.py line 209.

### Different terminals start at different times
Make sure all terminals are started **before** the 5-minute mark hits.

---

## 🎯 Recommended Test Sequence

1. **Warmup**: 1 terminal (200 swaps)
2. **Light load**: 2 terminals (400 swaps)
3. **Moderate load**: 5 terminals (1,000 swaps)
4. **Heavy load**: 10 terminals (2,000 swaps)

Run analyze_test_window.py after each to track TPS scaling!
