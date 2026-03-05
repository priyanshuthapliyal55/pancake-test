"""
Quick deployment script for Sepolia testnet
Deploys PancakeFactory, Router, and test tokens
"""
from eth_account import Account
from web3 import Web3
import json
import sys

# Configuration
SEPOLIA_RPC = "https://rpc.sepolia.org"
SEPOLIA_CHAIN_ID = 11155111

# Known addresses
WETH_SEPOLIA = "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9"

def deploy_contract(w3, account, bytecode, abi, constructor_args=[]):
    """Deploy a contract and return its address"""
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Build deployment transaction
    deploy_tx = contract.constructor(*constructor_args).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 5000000,
        'gasPrice': w3.eth.gas_price,
        'chainId': SEPOLIA_CHAIN_ID
    })
    
    # Sign and send
    signed = account.sign_transaction(deploy_tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(f"Deployment tx: {tx_hash.hex()}")
    
    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Contract deployed at: {receipt.contractAddress}")
    return receipt.contractAddress

def main():
    # Load mnemonic
    try:
        mnemonic = open("mnemonic.txt", "r").read().strip()
        if "<enter mnemonic here>" in mnemonic or not mnemonic:
            print("ERROR: Please add your mnemonic to mnemonic.txt")
            sys.exit(1)
    except FileNotFoundError:
        print("ERROR: mnemonic.txt not found")
        sys.exit(1)
    
    # Get deployer account
    Account.enable_unaudited_hdwallet_features()
    deployer = Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")
    
    # Connect to Sepolia
    w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC))
    if not w3.is_connected():
        print("ERROR: Cannot connect to Sepolia RPC")
        sys.exit(1)
    
    balance = w3.eth.get_balance(deployer.address)
    print(f"\nDeployer: {deployer.address}")
    print(f"Balance: {w3.from_wei(balance, 'ether')} ETH")
    
    if balance < w3.to_wei(0.1, 'ether'):
        print("\nWARNING: Low balance. Get Sepolia ETH from: https://sepoliafaucet.com/")
        sys.exit(1)
    
    print("\n=== Deployment Plan ===")
    print("1. Load compiled contracts from ../pancake-swap-core/build/")
    print("2. Deploy PancakeFactory")
    print("3. Deploy test CAKE token")
    print("4. Deploy PancakeRouter (using existing WETH)")
    print("5. Create WETH/CAKE pair")
    print("6. Add initial liquidity")
    print("\nPress Enter to continue or Ctrl+C to abort...")
    input()
    
    # TODO: Load ABIs and bytecode from build directory
    print("\nNOTE: This script requires compiled contracts.")
    print("Run these commands first:")
    print("  cd ../pancake-swap-core")
    print("  npm install")
    print("  npm run compile")
    print("\nThen manually deploy using Remix, Hardhat, or Foundry.")
    print("\nAfter deployment, update addresses in blockchain.py")
    

if __name__ == "__main__":
    main()
