#!/usr/bin/env python3
"""
Get detailed revert reason for failed transaction
"""

from web3 import Web3
from eth_account import Account
from blockchain import BlockchainData, ChainId

# =============================================================================
# CONFIGURATION
# =============================================================================

TX_HASH = "0x15ae81bb9a62594ba27676de6583a368203b8fb25ec060e66fd6f632b7389e4c"
CHAIN_ID = ChainId.MY_CUSTOM_L2

# =============================================================================
# SETUP
# =============================================================================

blockchain = BlockchainData(CHAIN_ID)
w3 = Web3(Web3.HTTPProvider(blockchain.http_rpc_url()))

print("=" * 70)
print("🔍 Transaction Failure Analysis")
print("=" * 70)
print(f"TX Hash: {TX_HASH}")
print("=" * 70)

# Get transaction and receipt
try:
    tx = w3.eth.get_transaction(TX_HASH)
    receipt = w3.eth.get_transaction_receipt(TX_HASH)
except Exception as e:
    print(f"❌ Error getting transaction: {e}")
    exit(1)

print(f"\n📋 Transaction Details:")
print(f"From:       {tx['from']}")
print(f"To:         {tx['to']}")
print(f"Value:      {w3.from_wei(tx['value'], 'ether')} ETH")
print(f"Gas Limit:  {tx['gas']}")
print(f"Gas Price:  {w3.from_wei(tx['gasPrice'], 'gwei')} Gwei")
print(f"Nonce:      {tx['nonce']}")
print(f"Block:      {receipt['blockNumber']}")
print(f"Gas Used:   {receipt['gasUsed']}")
print(f"Status:     {'✅ Success' if receipt['status'] == 1 else '❌ Failed'}")

# =============================================================================
# Method 1: Try to replay transaction to get revert reason
# =============================================================================

print("\n" + "=" * 70)
print("METHOD 1: Replay Transaction to Get Revert Reason")
print("=" * 70)

try:
    # Try to call the transaction at the block it was mined
    w3.eth.call(
        {
            'from': tx['from'],
            'to': tx['to'],
            'data': tx['input'],
            'value': tx['value'],
            'gas': tx['gas'],
            'gasPrice': tx['gasPrice'],
        },
        block_identifier=receipt['blockNumber'] - 1  # Block before it was mined
    )
    print("✅ Transaction would succeed in replay (odd...)")
except Exception as e:
    error_msg = str(e)
    print(f"❌ Transaction reverted with error:")
    print(f"   {error_msg}")
    
    # Try to parse common revert reasons
    if "execution reverted" in error_msg.lower():
        print("\n🔍 Common Revert Reasons:")
        
        if "insufficient" in error_msg.lower():
            print("   → Insufficient balance or allowance")
            print("   → Check WETH balance and router approval")
        
        if "expired" in error_msg.lower() or "deadline" in error_msg.lower():
            print("   → Transaction deadline expired")
            print("   → Increase deadline in swap call")
        
        if "slippage" in error_msg.lower() or "k" in error_msg.lower():
            print("   → Insufficient output amount (slippage too high)")
            print("   → Reduce amountOutMin or add more liquidity")
        
        if "liquidity" in error_msg.lower():
            print("   → Insufficient liquidity in pair")
            print("   → Add more liquidity to the pool")

# =============================================================================
# Method 2: Decode Input Data
# =============================================================================

print("\n" + "=" * 70)
print("METHOD 2: Decode Transaction Input")
print("=" * 70)

input_data = tx['input']
print(f"Input data: {input_data[:66]}... ({len(input_data)} chars)")

# Check function selector
selector = input_data[:10]
print(f"\nFunction selector: {selector}")

known_selectors = {
    '0x472b43f3': 'swapExactTokensForTokens(uint256,uint256,address[],address)',
    '0x38ed1739': 'swapExactTokensForTokens(uint256,uint256,address[],address,uint256)',
    '0x18cbafe5': 'swapExactTokensForETH(uint256,uint256,address[],address,uint256)',
    '0x7ff36ab5': 'swapExactETHForTokens(uint256,address[],address,uint256)',
}

if selector in known_selectors:
    print(f"Function: {known_selectors[selector]}")
else:
    print(f"Unknown function (custom or different router version)")

# Try to parse parameters
try:
    # Remove 0x and function selector (first 10 chars)
    params = input_data[10:]
    
    # Parse amountIn (first 32 bytes)
    amount_in = int(params[:64], 16)
    print(f"\nAmount In: {amount_in} wei ({w3.from_wei(amount_in, 'ether')} ETH)")
    
    # Parse amountOutMin (second 32 bytes)
    amount_out_min = int(params[64:128], 16)
    print(f"Amount Out Min: {amount_out_min} wei ({w3.from_wei(amount_out_min, 'ether')} ETH)")
    
    if amount_out_min == 0:
        print("⚠️  Warning: amountOutMin is 0 (no slippage protection)")
    
except Exception as e:
    print(f"Could not parse parameters: {e}")

# =============================================================================
# Method 3: Check Account State at Time of Transaction
# =============================================================================

print("\n" + "=" * 70)
print("METHOD 3: Check Account State")
print("=" * 70)

from_address = tx['from']
router_address = tx['to']

# Load WETH address
from blockchain import Token
weth_address = blockchain.get_address(Token.WETH)

ERC20_ABI = [
    {"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
]

weth = w3.eth.contract(address=weth_address, abi=ERC20_ABI)

# Check at the block before transaction
block_before = receipt['blockNumber'] - 1

try:
    eth_balance = w3.eth.get_balance(from_address, block_identifier=block_before)
    weth_balance = weth.functions.balanceOf(from_address).call(block_identifier=block_before)
    weth_allowance = weth.functions.allowance(from_address, router_address).call(block_identifier=block_before)
    
    print(f"At block {block_before} (before tx):")
    print(f"  ETH Balance:       {w3.from_wei(eth_balance, 'ether')} ETH")
    print(f"  WETH Balance:      {w3.from_wei(weth_balance, 'ether')} WETH")
    print(f"  Router Allowance:  {w3.from_wei(weth_allowance, 'ether')} WETH")
    
    # Try to parse amountIn from transaction
    try:
        params = input_data[10:]
        amount_in = int(params[:64], 16)
        
        print(f"\nRequired for swap: {w3.from_wei(amount_in, 'ether')} WETH")
        
        if weth_balance < amount_in:
            print(f"❌ INSUFFICIENT WETH BALANCE!")
            print(f"   Had: {w3.from_wei(weth_balance, 'ether')} WETH")
            print(f"   Need: {w3.from_wei(amount_in, 'ether')} WETH")
            print(f"   Short by: {w3.from_wei(amount_in - weth_balance, 'ether')} WETH")
        
        if weth_allowance < amount_in:
            print(f"❌ INSUFFICIENT ALLOWANCE!")
            print(f"   Approved: {w3.from_wei(weth_allowance, 'ether')} WETH")
            print(f"   Need: {w3.from_wei(amount_in, 'ether')} WETH")
            print(f"   Short by: {w3.from_wei(amount_in - weth_allowance, 'ether')} WETH")
        
        if weth_balance >= amount_in and weth_allowance >= amount_in:
            print("✅ Balance and allowance were sufficient")
            print("   → Failure likely due to liquidity or other contract issue")
    except:
        pass
        
except Exception as e:
    print(f"❌ Error checking balances: {e}")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 70)
print("🎯 LIKELY CAUSE OF FAILURE")
print("=" * 70)

print("""
Based on gas used (25,350), the transaction failed VERY early.
This usually means:

1. ❌ INSUFFICIENT WETH BALANCE
   → Account didn't have enough WETH to swap
   → Fix: Run python3 prepare.py

2. ❌ NO ROUTER ALLOWANCE
   → Router not approved to spend WETH
   → Fix: Run python3 prepare.py

3. ❌ PAIR DOESN'T EXIST
   → WETH/CAKE pair not created
   → Fix: factory.createPair(WETH, CAKE)

4. ❌ NO LIQUIDITY IN PAIR
   → Pair exists but has 0 reserves
   → Fix: router.addLiquidityETH() or addLiquidity()

5. ❌ WRONG ROUTER ADDRESS
   → Router address in blockchain.py is wrong
   → Fix: Update blockchain.py with correct address

To fix, run:
  python3 diagnose_swap_failure.py   # Check all prerequisites
  python3 prepare.py                 # Prepare accounts
""")
