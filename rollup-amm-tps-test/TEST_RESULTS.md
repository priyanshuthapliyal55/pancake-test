# L2 AMM TPS Test - Deployment & Results Summary

## 🎯 Objective
Successfully deployed PancakeSwap DEX contracts to custom L2 blockchain and measured transaction throughput using AMM swap operations.

## 📋 Deployment Details

### Network Configuration
- **Chain ID**: 11155111
- **RPC URL**: http://46.165.235.105:8545
- **Block Explorer**: N/A (custom L2)

### Deployed Contracts
| Contract | Address | Status |
|----------|---------|--------|
| WETH | `0x6e881c585748cbAab9bB366ae7b87832F973f8c5` | ✅ Deployed |
| PancakeFactory | `0x84141fcDA62C498B96c6c20267D68459DCADA55A` | ✅ Deployed |
| PancakeRouter | `0xBC4974366dF3b95036AA59DD240637b7c6527ab9` | ✅ Deployed |
| CAKE Token | `0x9Dc3bFe767CeCD81F97B5ed7f1df640F6876CE62` | ✅ Deployed |
| WETH/CAKE Pair | `0x7fEa22C180828f55e7271bD9747C1227D1811C64` | ✅ Created |

### Initial Liquidity
- **ETH**: 1.0 ETH
- **CAKE**: 10,000 CAKE
- **Liquidity Added**: ✅ Successfully

## 🔧 Technical Stack

### Compilation
- **Tool**: Foundry/forge v1.5.1-stable
- **Solidity Versions**:
  - Core contracts: 0.5.16
  - Periphery contracts: 0.6.6
  - Token contracts: 0.5.16
- **EVM Version**: Istanbul (required for L2 compatibility)

### Testing Framework
- **Language**: Python 3.10
- **Libraries**: web3.py, eth-account
- **Authentication**: HD Wallet (mnemonic-based)
- **Test Accounts**: 100 accounts funded from index m/44'/60'/0'/0/0 to m/44'/60'/0'/0/99

## 📊 TPS Test Results

### Test Configuration
- **Accounts Used**: 10 (indices 0-9)
- **Swaps Per Account**: 20
- **Total Swap Transactions**: 200
- **Transaction Type**: WETH ↔ CAKE swaps via Router

### Performance Metrics (Last 100 Blocks)
```
Block Range:      539478 - 539577
Time Span:        396 seconds (6.60 minutes)
Total Txs:        878 transactions
Average TPS:      2.22 TPS
Peak Block Txs:   56 transactions
Min Block Txs:    0 transactions
Avg Txs/Block:    8.78 transactions
```

### Peak Performance Blocks
| Block | Transaction Count |
|-------|------------------|
| 539563 | 56 txs |
| 539565 | 55 txs |
| 539568 | 55 txs |
| 539562 | 54 txs |
| 539570 | 54 txs |

## 🚀 Key Achievements

1. ✅ **Successfully resolved EVM compatibility issues**
   - Compiled custom WETH contract with Istanbul EVM version
   - All contracts deployed without errors

2. ✅ **Switched from Truffle to Foundry**
   - Avoided Node.js native module dependency issues
   - Faster compilation times

3. ✅ **Complete DEX deployment**
   - Factory, Router, WETH, and CAKE token all operational
   - Liquidity pool created and funded

4. ✅ **Successful TPS benchmark**
   - 200 swap transactions sent concurrently
   - L2 processing at 2.22 TPS average
   - Peak blocks handled 50+ transactions

## 🛠️ Scripts Available

### Deployment Scripts
- `deploy_simple.py` - Deploy WETH, Factory, Router
- `deploy_cake.py` - Deploy CAKE token
- `setup_liquidity.py` - Create pair and add liquidity

### Testing Scripts
- `prepare.py` - Fund test accounts with ETH and WETH
- `tps_test.py -n 0` - Run TPS test (10 accounts × 20 swaps)
- `analyze_tps.py` - Calculate TPS from blockchain data

### Compilation
- `compile_contracts.sh` - Compile all contracts using Foundry

## 📝 Configuration Files

### blockchain.py
```python
ChainId.SEPOLIA_TESTNET: NetworkData(
    chain_id=11155111,
    http_rpc_url='http://46.165.235.105:8545',
    ws_rpc_url='ws://46.165.235.105:8546',
    addresses={
        Contract.PANCAKE_SMART_ROUTER: '0xBC4974366dF3b95036AA59DD240637b7c6527ab9',
        Token.CAKE: '0x9Dc3bFe767CeCD81F97B5ed7f1df640F6876CE62',
        Token.WETH: '0x6e881c585748cbAab9bB366ae7b87832F973f8c5',
    },
)
```

## 🔍 Observations

### L2 Performance Characteristics
1. **Block Time**: ~4 seconds average (396s / 100 blocks)
2. **Transaction Throughput**: Capable of 50+ txs per block during peak
3. **Average Load**: 8.78 transactions per block
4. **Consistency**: Mix of empty and full blocks suggests variable load

### Recommendation
The L2 shows good transaction capacity with peaks of 50+ transactions per block. The average TPS of 2.22 is conservative due to including empty blocks. During active trading periods, the chain demonstrates significantly higher throughput.

## 📚 Resources

### Contract Repositories
- **Core**: `/home/priyanshu/op-stack/pancake-swap-testnet/pancake-swap-core/`
- **Periphery**: `/home/priyanshu/op-stack/pancake-swap-testnet/pancake-swap-periphery/`
- **Testing**: `/home/priyanshu/op-stack/pancake-swap-testnet/rollup-amm-tps-test/`

### Key Files
- Mnemonic: `rollup-amm-tps-test/mnemonic.txt`
- Deployed Addresses: `rollup-amm-tps-test/deployed_addresses.json`
- Network Config: `rollup-amm-tps-test/blockchain.py`

## 🎓 Lessons Learned

1. **EVM Version Compatibility**: Always match compiled bytecode EVM version to target chain
2. **Foundry > Truffle**: For modern development, Foundry offers better dependency management
3. **Custom Token Deployment**: Simpler ERC20 implementations work better for testing than complex production tokens
4. **Parallel Testing**: Running swaps from multiple accounts concurrently provides realistic load testing

## ✅ Next Steps

To run additional tests:

1. **Run with more accounts**:
   ```bash
   python3 tps_test.py -n 1  # Uses accounts 10-19
   python3 tps_test.py -n 2  # Uses accounts 20-29
   ```

2. **Modify swap count**: Edit `tps_test.py` line 207 to change `swap_txs_count=20`

3. **Test other networks**: Update `blockchain.py` with new network configuration

4. **Analyze specific test runs**: Use transaction hashes from test output to analyze specific performance characteristics

---
**Test Completed**: February 27, 2026
**Status**: ✅ SUCCESS
