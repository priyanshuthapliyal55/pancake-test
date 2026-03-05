#!/usr/bin/env python3
"""
Manual Swap Verification Script
Check if swaps are working on your deployed DEX
"""

import json
from web3 import Web3
from eth_account import Account
from datetime import datetime

# =============================================================================
# CONFIGURATION - Update these with your values
# =============================================================================

RPC_URL = "http://46.165.235.105:8545"
CHAIN_ID = 11155111

# Load from deployed_addresses.json or set manually
ROUTER_ADDRESS = "0xYourRouterAddress"
WETH_ADDRESS = "0xYourWETHAddress"
CAKE_ADDRESS = "0xYourCakeAddress"
FACTORY_ADDRESS = "0xYourFactoryAddress"

# =============================================================================
# SETUP
# =============================================================================

w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    print("❌ Failed to connect to RPC")
    exit(1)

# Load mnemonic
with open('mnemonic.txt', 'r') as f:
    mnemonic = f.read().strip()

Account.enable_unaudited_hdwallet_features()
account = Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")

print("=" * 70)
print("🔍 DEX Swap Verification Tool")
print("=" * 70)
print(f"Connected to: {RPC_URL}")
print(f"Chain ID: {CHAIN_ID}")
print(f"Account: {account.address}")
print("=" * 70)

# =============================================================================
# ABIs
# =============================================================================

ROUTER_ABI = [
    {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},
]

FACTORY_ABI = [
    {"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"pair","type":"address"}],"stateMutability":"view","type":"function"},
]

PAIR_ABI = [
    {"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"sender","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount0In","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"amount1In","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"amount0Out","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"amount1Out","type":"uint256"},{"indexed":True,"internalType":"address","name":"to","type":"address"}],"name":"Swap","type":"event"},
]

ERC20_ABI = [
    {"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
]

# =============================================================================
# METHOD 1: Check Pair Reserves
# =============================================================================

def check_pair_reserves():
    """Check if liquidity exists in the pair"""
    print("\n" + "=" * 70)
    print("METHOD 1: Check Pair Reserves")
    print("=" * 70)
    
    try:
        factory = w3.eth.contract(address=FACTORY_ADDRESS, abi=FACTORY_ABI)
        pair_address = factory.functions.getPair(WETH_ADDRESS, CAKE_ADDRESS).call()
        
        if pair_address == '0x0000000000000000000000000000000000000000':
            print("❌ Pair doesn't exist! Create pair first.")
            return False
        
        print(f"✅ Pair exists at: {pair_address}")
        
        pair = w3.eth.contract(address=pair_address, abi=PAIR_ABI)
        reserves = pair.functions.getReserves().call()
        token0 = pair.functions.token0().call()
        token1 = pair.functions.token1().call()
        
        print(f"\nToken0: {token0}")
        print(f"Token1: {token1}")
        print(f"\nReserve0: {w3.from_wei(reserves[0], 'ether')} tokens")
        print(f"Reserve1: {w3.from_wei(reserves[1], 'ether')} tokens")
        print(f"Last Update: {datetime.fromtimestamp(reserves[2])}")
        
        if reserves[0] == 0 or reserves[1] == 0:
            print("\n❌ No liquidity in pair! Add liquidity first.")
            return False
        
        print("\n✅ Liquidity exists - swaps should work!")
        return True
        
    except Exception as e:
        print(f"❌ Error checking pair: {e}")
        return False

# =============================================================================
# METHOD 2: Check Token Balances
# =============================================================================

def check_balances(address=None):
    """Check WETH and CAKE balances"""
    if address is None:
        address = account.address
    
    print("\n" + "=" * 70)
    print(f"METHOD 2: Check Balances for {address}")
    print("=" * 70)
    
    try:
        weth = w3.eth.contract(address=WETH_ADDRESS, abi=ERC20_ABI)
        cake = w3.eth.contract(address=CAKE_ADDRESS, abi=ERC20_ABI)
        
        weth_balance = weth.functions.balanceOf(address).call()
        cake_balance = cake.functions.balanceOf(address).call()
        eth_balance = w3.eth.get_balance(address)
        
        print(f"ETH Balance:  {w3.from_wei(eth_balance, 'ether')} ETH")
        print(f"WETH Balance: {w3.from_wei(weth_balance, 'ether')} WETH")
        print(f"CAKE Balance: {w3.from_wei(cake_balance, 'ether')} CAKE")
        
        return weth_balance, cake_balance
        
    except Exception as e:
        print(f"❌ Error checking balances: {e}")
        return 0, 0

# =============================================================================
# METHOD 3: Simulate Swap (Read-Only)
# =============================================================================

def simulate_swap(amount_in_wei):
    """Simulate a swap to see expected output"""
    print("\n" + "=" * 70)
    print("METHOD 3: Simulate Swap (Read-Only)")
    print("=" * 70)
    
    try:
        router = w3.eth.contract(address=ROUTER_ADDRESS, abi=ROUTER_ABI)
        path = [WETH_ADDRESS, CAKE_ADDRESS]
        
        amounts_out = router.functions.getAmountsOut(amount_in_wei, path).call()
        
        print(f"Input:  {w3.from_wei(amount_in_wei, 'ether')} WETH")
        print(f"Output: {w3.from_wei(amounts_out[1], 'ether')} CAKE")
        print(f"Rate:   1 WETH = {w3.from_wei(amounts_out[1], 'ether') / w3.from_wei(amount_in_wei, 'ether'):.6f} CAKE")
        
        return amounts_out[1]
        
    except Exception as e:
        print(f"❌ Error simulating swap: {e}")
        return 0

# =============================================================================
# METHOD 4: Check Allowances
# =============================================================================

def check_allowances():
    """Check if router is approved to spend tokens"""
    print("\n" + "=" * 70)
    print("METHOD 4: Check Allowances")
    print("=" * 70)
    
    try:
        weth = w3.eth.contract(address=WETH_ADDRESS, abi=ERC20_ABI)
        
        allowance = weth.functions.allowance(account.address, ROUTER_ADDRESS).call()
        
        print(f"WETH Allowance for Router: {w3.from_wei(allowance, 'ether')} WETH")
        
        if allowance == 0:
            print("❌ No allowance! Approve router first.")
            return False
        else:
            print("✅ Router is approved to spend WETH")
            return True
            
    except Exception as e:
        print(f"❌ Error checking allowance: {e}")
        return False

# =============================================================================
# METHOD 5: Execute Test Swap
# =============================================================================

def execute_test_swap():
    """Execute a real test swap"""
    print("\n" + "=" * 70)
    print("METHOD 5: Execute Test Swap")
    print("=" * 70)
    
    # Check prerequisites
    weth_balance, cake_balance = check_balances()
    
    if weth_balance == 0:
        print("❌ No WETH balance! Wrap some ETH first.")
        return False
    
    # Small test amount (0.00001 WETH)
    swap_amount = w3.to_wei(0.00001, 'ether')
    
    if weth_balance < swap_amount:
        print(f"❌ Insufficient WETH. Have: {w3.from_wei(weth_balance, 'ether')}, Need: {w3.from_wei(swap_amount, 'ether')}")
        return False
    
    try:
        router = w3.eth.contract(address=ROUTER_ADDRESS, abi=ROUTER_ABI)
        path = [WETH_ADDRESS, CAKE_ADDRESS]
        
        # Simulate first
        amounts_out = router.functions.getAmountsOut(swap_amount, path).call()
        expected_cake = amounts_out[1]
        min_cake = int(expected_cake * 0.95)  # 5% slippage
        
        print(f"\nSwapping {w3.from_wei(swap_amount, 'ether')} WETH")
        print(f"Expected output: {w3.from_wei(expected_cake, 'ether')} CAKE")
        print(f"Minimum output: {w3.from_wei(min_cake, 'ether')} CAKE (5% slippage)")
        
        # Get balances before
        cake_before = w3.eth.contract(address=CAKE_ADDRESS, abi=ERC20_ABI).functions.balanceOf(account.address).call()
        
        # Build transaction
        deadline = w3.eth.get_block('latest')['timestamp'] + 300  # 5 minutes
        
        tx = router.functions.swapExactTokensForTokens(
            swap_amount,
            min_cake,
            path,
            account.address,
            deadline
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'chainId': CHAIN_ID,
        })
        
        # Sign and send
        signed = w3.eth.account.sign_transaction(tx, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        
        print(f"\n📤 Transaction sent: {tx_hash.hex()}")
        print("⏳ Waiting for confirmation...")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            print("✅ Swap successful!")
            
            # Check balance after
            cake_after = w3.eth.contract(address=CAKE_ADDRESS, abi=ERC20_ABI).functions.balanceOf(account.address).call()
            cake_received = cake_after - cake_before
            
            print(f"\n💰 CAKE received: {w3.from_wei(cake_received, 'ether')} CAKE")
            print(f"📊 Gas used: {receipt['gasUsed']}")
            print(f"🔗 Block: {receipt['blockNumber']}")
            
            return True
        else:
            print("❌ Swap failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error executing swap: {e}")
        return False

# =============================================================================
# METHOD 6: Check Recent Swap Events
# =============================================================================

def check_swap_events(from_block='latest', to_block='latest'):
    """Check for Swap events in the pair contract"""
    print("\n" + "=" * 70)
    print("METHOD 6: Check Recent Swap Events")
    print("=" * 70)
    
    try:
        factory = w3.eth.contract(address=FACTORY_ADDRESS, abi=FACTORY_ABI)
        pair_address = factory.functions.getPair(WETH_ADDRESS, CAKE_ADDRESS).call()
        
        if pair_address == '0x0000000000000000000000000000000000000000':
            print("❌ Pair doesn't exist!")
            return
        
        pair = w3.eth.contract(address=pair_address, abi=PAIR_ABI)
        
        # Get latest blocks
        if from_block == 'latest':
            current_block = w3.eth.block_number
            from_block = max(0, current_block - 100)  # Last 100 blocks
            to_block = current_block
        
        print(f"Searching blocks {from_block} to {to_block}...")
        
        # Get Swap events
        swap_filter = pair.events.Swap.create_filter(
            fromBlock=from_block,
            toBlock=to_block
        )
        
        events = swap_filter.get_all_entries()
        
        if len(events) == 0:
            print("❌ No swap events found in recent blocks")
            print("   Try executing a swap first!")
        else:
            print(f"✅ Found {len(events)} swap event(s):")
            for i, event in enumerate(events[-10:], 1):  # Show last 10
                print(f"\n  Swap #{i}:")
                print(f"    Block: {event['blockNumber']}")
                print(f"    Tx: {event['transactionHash'].hex()}")
                print(f"    Sender: {event['args']['sender']}")
                print(f"    To: {event['args']['to']}")
                if event['args']['amount0In'] > 0:
                    print(f"    Amount In: {w3.from_wei(event['args']['amount0In'], 'ether')} token0")
                if event['args']['amount1In'] > 0:
                    print(f"    Amount In: {w3.from_wei(event['args']['amount1In'], 'ether')} token1")
                if event['args']['amount0Out'] > 0:
                    print(f"    Amount Out: {w3.from_wei(event['args']['amount0Out'], 'ether')} token0")
                if event['args']['amount1Out'] > 0:
                    print(f"    Amount Out: {w3.from_wei(event['args']['amount1Out'], 'ether')} token1")
        
    except Exception as e:
        print(f"❌ Error checking events: {e}")

# =============================================================================
# METHOD 7: Check Specific Transaction
# =============================================================================

def check_transaction(tx_hash):
    """Check if a specific transaction was a successful swap"""
    print("\n" + "=" * 70)
    print("METHOD 7: Check Specific Transaction")
    print("=" * 70)
    
    try:
        tx = w3.eth.get_transaction(tx_hash)
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        
        print(f"Transaction: {tx_hash}")
        print(f"From: {tx['from']}")
        print(f"To: {tx['to']}")
        print(f"Block: {receipt['blockNumber']}")
        print(f"Status: {'✅ Success' if receipt['status'] == 1 else '❌ Failed'}")
        print(f"Gas Used: {receipt['gasUsed']}")
        
        # Check if it's a swap transaction
        if tx['to'].lower() == ROUTER_ADDRESS.lower():
            print("\n✅ This is a Router transaction")
            
            # Decode logs to find Swap events
            factory = w3.eth.contract(address=FACTORY_ADDRESS, abi=FACTORY_ABI)
            pair_address = factory.functions.getPair(WETH_ADDRESS, CAKE_ADDRESS).call()
            pair = w3.eth.contract(address=pair_address, abi=PAIR_ABI)
            
            swap_events = pair.events.Swap().process_receipt(receipt)
            
            if swap_events:
                print(f"✅ Found {len(swap_events)} Swap event(s)")
                for event in swap_events:
                    print(f"\n  Swap Details:")
                    print(f"    Amount0In: {w3.from_wei(event['args']['amount0In'], 'ether')}")
                    print(f"    Amount1In: {w3.from_wei(event['args']['amount1In'], 'ether')}")
                    print(f"    Amount0Out: {w3.from_wei(event['args']['amount0Out'], 'ether')}")
                    print(f"    Amount1Out: {w3.from_wei(event['args']['amount1Out'], 'ether')}")
            else:
                print("❌ No Swap events found in transaction")
        
    except Exception as e:
        print(f"❌ Error checking transaction: {e}")

# =============================================================================
# MAIN MENU
# =============================================================================

def main():
    print("\n" + "=" * 70)
    print("Select verification method:")
    print("=" * 70)
    print("1. Check pair reserves (verify liquidity exists)")
    print("2. Check token balances")
    print("3. Simulate swap (read-only)")
    print("4. Check allowances")
    print("5. Execute test swap (REAL transaction)")
    print("6. Check recent swap events")
    print("7. Check specific transaction")
    print("8. Run all checks")
    print("0. Exit")
    print("=" * 70)
    
    choice = input("\nEnter choice (0-8): ").strip()
    
    if choice == '1':
        check_pair_reserves()
    elif choice == '2':
        check_balances()
    elif choice == '3':
        amount = float(input("Amount of WETH to swap (e.g., 0.001): "))
        simulate_swap(w3.to_wei(amount, 'ether'))
    elif choice == '4':
        check_allowances()
    elif choice == '5':
        confirm = input("⚠️  This will execute a REAL swap. Continue? (yes/no): ")
        if confirm.lower() == 'yes':
            execute_test_swap()
    elif choice == '6':
        check_swap_events()
    elif choice == '7':
        tx_hash = input("Enter transaction hash (0x...): ").strip()
        check_transaction(tx_hash)
    elif choice == '8':
        check_pair_reserves()
        check_balances()
        check_allowances()
        simulate_swap(w3.to_wei(0.00001, 'ether'))
        check_swap_events()
    elif choice == '0':
        print("Goodbye!")
        return
    else:
        print("Invalid choice")

if __name__ == "__main__":
    # Try to load addresses from deployed_addresses.json
    try:
        with open('deployed_addresses.json', 'r') as f:
            deployed = json.load(f)
            if 'addresses' in deployed:
                ROUTER_ADDRESS = deployed['addresses'].get('Router', ROUTER_ADDRESS)
                WETH_ADDRESS = deployed['addresses'].get('WETH', WETH_ADDRESS)
                FACTORY_ADDRESS = deployed['addresses'].get('Factory', FACTORY_ADDRESS)
                print(f"✅ Loaded addresses from deployed_addresses.json")
    except:
        print("⚠️  Could not load deployed_addresses.json - using configured values")
    
    main()
