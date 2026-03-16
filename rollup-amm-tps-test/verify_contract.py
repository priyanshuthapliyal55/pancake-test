#!/usr/bin/env python3
"""
Quick verification script to compare deployed contracts
"""
from web3 import Web3

# Your deployment
your_rpc = "http://46.165.235.105:8545"
your_proxy = "0x84141fcDA62C498B96c6c20267D68459DCADA55A"
your_impl = "0x6e881c585748cbAab9bB366ae7b87832F973f8c5"

# Base deployment (for comparison)
base_rpc = "https://mainnet.base.org"
base_proxy = "0x7e0aedc93d9f898be835a44bfca3842e52416b82"
base_impl = "0x620244706ba6c771ec417662a0bfb6fe6d1c5ae2"

w3_your = Web3(Web3.HTTPProvider(your_rpc))
w3_base = Web3(Web3.HTTPProvider(base_rpc))

print("=" * 70)
print("Contract Verification")
print("=" * 70)

# Check proxy bytecode
your_proxy_code = w3_your.eth.get_code(your_proxy).hex()
base_proxy_code = w3_base.eth.get_code(base_proxy).hex()

print(f"\n📋 PROXY BYTECODE:")
print(f"Your proxy length : {len(your_proxy_code)} bytes")
print(f"Base proxy length : {len(base_proxy_code)} bytes")
print(f"Exact match       : {'✅ YES' if your_proxy_code == base_proxy_code else '❌ NO'}")

# Check implementation bytecode
your_impl_code = w3_your.eth.get_code(your_impl).hex()
base_impl_code = w3_base.eth.get_code(base_impl).hex()

print(f"\n📋 IMPLEMENTATION BYTECODE:")
print(f"Your impl length  : {len(your_impl_code)} bytes")
print(f"Base impl length  : {len(base_impl_code)} bytes")
print(f"Exact match       : {'✅ YES' if your_impl_code == base_impl_code else '❌ NO'}")

# Check similarity
if your_impl_code != base_impl_code:
    similarity = sum(a == b for a, b in zip(your_impl_code, base_impl_code)) / max(len(your_impl_code), len(base_impl_code)) * 100
    print(f"Similarity        : {similarity:.2f}%")

print("\n" + "=" * 70)

# Check if contracts are functional
print("\n🔍 FUNCTIONAL TEST:")
try:
    # Simple ERC20 ABI for testing
    abi = [{"inputs":[],"name":"decimals","outputs":[{"type":"uint8"}],"stateMutability":"view","type":"function"}]
    
    your_token = w3_your.eth.contract(address=your_proxy, abi=abi)
    decimals = your_token.functions.decimals().call()
    print(f"Your token decimals: {decimals}")
    print(f"Expected (JPMD)    : 2")
    print(f"Match              : {'✅ YES' if decimals == 2 else '❌ NO'}")
except Exception as e:
    print(f"❌ Error reading contract: {e}")

print("=" * 70)
