from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from eth_account import Account
from web3 import Web3

import argparse
import asyncio
import json
import logging
import random
import signal
import sys
import threading
import time
import websockets

from blockchain import BlockchainData, ChainId, Contract, Token

logging.basicConfig(format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


EXECUTION_STARTED = False
TERMINATION_REQUESTED = False
def signal_handler(_sig, _frame):
    logger.info('===== Termination requested =====')
    if not EXECUTION_STARTED:
        sys.exit(0)
    global TERMINATION_REQUESTED
    TERMINATION_REQUESTED = True


def generate_ethereum_accounts(mnemonic, count):
    Account.enable_unaudited_hdwallet_features()
    accounts = []
    for i in range(count):
        account = Account.from_mnemonic(mnemonic, account_path=f"m/44'/60'/0'/0/{i}")
        accounts.append(account)
    return accounts


def request_to_json(method, params, request_id=None):
    if request_id is None:
        request_id = random.randint(0, int(1e9))
    return {
        'jsonrpc': '2.0',
        'id': request_id,
        'method': method,
        'params': params,
    }


def retriable(method):
    def wrapper(self, *args, **kwargs):
        retry_secs = 0.1
        max_retries = 8
        retry_count = 0
        while not TERMINATION_REQUESTED:
            try:
                return method(self, *args, **kwargs)
            except Exception as e:
                retry_count += 1
                if retry_count > max_retries:
                    return False
                logger.info(f"[{self.account.address}] Failed to execute {method.__name__}: {e}. Retry #{retry_count}")
                time.sleep(retry_secs)
                retry_secs *= 2
        return False
    return wrapper


class Trader:
    def __init__(self, chain_id: ChainId, account: Account, transfer_txs_count=None, token_address=None, recipient_address=None, transfer_amount=None):
        self.account = account
        self.transfer_txs_count = transfer_txs_count
        # Initialize web3:
        self.blockchain = BlockchainData(chain_id)
        # Use HTTP provider for initial setup (getting nonce)
        self.w3 = Web3(Web3.HTTPProvider(self.blockchain.http_rpc_url()))
        # Get nonce including pending transactions to avoid nonce conflicts
        self.nonce = self.w3.eth.get_transaction_count(account.address, 'pending')
        self.chain_id = chain_id.value
        
        # Token configuration - use provided token or default to CAKE
        if token_address:
            self.token_address = token_address
        else:
            self.token_address = self.blockchain.get_address(Token.CAKE)
        
        # Recipient configuration - if not provided, send to self
        if recipient_address:
            self.recipient_address = recipient_address
        else:
            self.recipient_address = account.address
            
        # Transfer amount - default to 1000 wei (1e-15 tokens for 18 decimal tokens)
        if transfer_amount:
            self.transfer_amount = transfer_amount
        else:
            self.transfer_amount = 1000  # 1000 wei = 0.000000000000001 tokens
        
        # Initialize gas price:
        self.gas_price = 2 * self.w3.eth.gas_price
        # Initialize variables:
        self.request_id = 1
        self.signed_txs_by_nonce = {}
        self.nonce_by_request_id = {}
        # Track send timestamps for latency analysis:
        self.tx_send_timestamps = {}
        # Prefill signed txs:
        self.prefill_signed_txs()

    def transfer_prefill(self):
        """
        Create a token transfer transaction.
        ERC20 transfer function signature: transfer(address to, uint256 amount)
        Function selector: 0xa9059cbb
        """
        # Encode the transfer calldata:
        # Function selector (4 bytes) + recipient address (32 bytes, left-padded) + amount (32 bytes)
        recipient_padded = self.recipient_address.lower()[2:].zfill(64)  # Remove 0x and pad to 32 bytes
        amount_hex = hex(self.transfer_amount)[2:].zfill(64)  # Convert to hex and pad to 32 bytes
        calldata = f"0xa9059cbb{recipient_padded}{amount_hex}"
        
        tx = {
            'value': 0,
            'chainId': self.chain_id,
            'from': self.account.address,
            'gas': 100000,  # Token transfers typically need ~65k gas, using 100k for safety
            'gasPrice': self.gas_price,
            'nonce': self.nonce,
            'to': self.token_address,
            'data': calldata,
        }
        signed_tx = Account.sign_transaction(tx, self.account.key)
        self.signed_txs_by_nonce[self.nonce] = signed_tx
        self.nonce += 1
        return True

    def prefill_signed_txs(self):
        for _ in range(self.transfer_txs_count):
            self.transfer_prefill()

    def start(self):
        logger.info(f'[{self.account.address}] Starting...')
        sending_thread = threading.Thread(target=self._sending_thread)
        sending_thread.start()
        sending_thread.join()

    @retriable
    def _sending_thread(self):
        asyncio.run(self._sending_thread_async())

    async def _sending_thread_async(self):
        ws_url = self.blockchain.ws_rpc_url()
        retry_delay = 0.5
        max_retries = 5
        
        for retry in range(max_retries):
            try:
                async with websockets.connect(ws_url) as ws:
                    # Re-sync nonce before sending
                    current_nonce = self.w3.eth.get_transaction_count(self.account.address, 'pending')
                    if current_nonce > min(self.signed_txs_by_nonce.keys(), default=0):
                        logger.info(f"[{self.account.address}] Nonce re-sync: chain={current_nonce}, local={min(self.signed_txs_by_nonce.keys())}")
                        # Remove stale transactions
                        stale_nonces = [n for n in self.signed_txs_by_nonce.keys() if n < current_nonce]
                        for stale_nonce in stale_nonces:
                            del self.signed_txs_by_nonce[stale_nonce]
                            logger.info(f"[{self.account.address}] Removed stale tx with nonce={stale_nonce}")
                    
                    # 1. Send all transactions:
                    for (nonce, signed_tx) in list(self.signed_txs_by_nonce.items()):
                        await self._send_transaction(ws, signed_tx, nonce)
                        # Small delay to avoid overwhelming the sequencer
                        await asyncio.sleep(0.001)
                    
                    # 2. Wait for RPC acknowledgements and resend if necessary:
                    while not TERMINATION_REQUESTED and len(self.signed_txs_by_nonce) > 0:
                        message = await ws.recv()
                        json_response = json.loads(message)
                        request_id = json_response["id"]
                        nonce = self.nonce_by_request_id[request_id]
                        error_message = (json_response["error"].get("message") if "error" in json_response else None) or ""
                        
                        if "result" in json_response or error_message.startswith('known transaction'):
                            if nonce in self.signed_txs_by_nonce:
                                tx_hash = self.signed_txs_by_nonce[nonce].hash.hex()
                                del self.signed_txs_by_nonce[nonce]
                                logger.info(f"[{self.account.address}] Tx request accepted (transfer): {tx_hash} | nonce={nonce} | id={request_id}")
                        else:
                            # Error: RPC didn't accept transaction
                            logger.info(f"[{self.account.address}] Recv: {message}")
                            
                            # Handle nonce too low - remove stale transactions
                            if "nonce too low" in error_message:
                                logger.info(f"[{self.account.address}] Nonce too low detected, removing stale tx with nonce={nonce}")
                                if nonce in self.signed_txs_by_nonce:
                                    del self.signed_txs_by_nonce[nonce]
                                continue
                            
                            if nonce not in self.signed_txs_by_nonce:
                                continue
                                
                            signed_tx = self.signed_txs_by_nonce[nonce]
                            if "insufficient funds" in error_message or "transaction underpriced" in error_message:
                                # No need to resend, tx will fail:
                                logger.info(f"[{self.account.address}] Aborting tx: {signed_tx.hash.hex()} | nonce={nonce}")
                                del self.signed_txs_by_nonce[nonce]
                                continue
                            
                            # Connection error - will reconnect on outer retry
                            if "dial tcp" in error_message or "connect:" in error_message:
                                logger.info(f"[{self.account.address}] Connection error, will retry connection")
                                break
                            
                            # Resend for other errors
                            await asyncio.sleep(0.1)
                            await self._send_transaction(ws, signed_tx, nonce)
                    
                    # Successfully completed
                    return
                    
            except (websockets.exceptions.WebSocketException, ConnectionError, OSError) as e:
                logger.info(f"[{self.account.address}] Connection failed (attempt {retry+1}/{max_retries}): {e}")
                if retry < max_retries - 1 and not TERMINATION_REQUESTED:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise

    async def _send_transaction(self, ws, signed_tx, nonce):
        json_request = request_to_json("eth_sendRawTransaction", ["0x" + signed_tx.rawTransaction.hex()], request_id=self.request_id)
        send_time = time.time()
        await ws.send(json.dumps(json_request))
        tx_hash = signed_tx.hash.hex()
        # Record send timestamp for latency tracking
        self.tx_send_timestamps[tx_hash] = send_time
        logger.info(f"[{self.account.address}] Tx request sent (transfer): {tx_hash} | nonce={nonce} | id={self.request_id}")
        self.nonce_by_request_id[self.request_id] = nonce
        self.request_id += 1


def run_in_parallel(objects):
    def start_and_wait(obj):
        obj.start()
    global EXECUTION_STARTED
    EXECUTION_STARTED = True
    start_time = time.time()
    logger.info(f"Start time: {start_time}")
    if len(objects) > 1:
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(start_and_wait, obj) for obj in objects]
        for future in as_completed(futures):
            future.result()
    elif len(objects) == 1:
        start_and_wait(objects[0])
    end_time = time.time()
    logger.info(f"End time: {end_time}")
    
    # Save all transaction send timestamps for latency analysis
    all_timestamps = {}
    for obj in objects:
        all_timestamps.update(obj.tx_send_timestamps)
    
    if all_timestamps:
        timestamps_file = f"tx_timestamps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(timestamps_file, 'w') as f:
            json.dump(all_timestamps, f, indent=2)
        logger.info(f"Saved {len(all_timestamps)} tx timestamps to {timestamps_file}")


def wait_until_target_time():
    now = datetime.now()
    logger.info(f"Time now: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    target = now.replace(minute=now.minute - (now.minute % 5), second=0, microsecond=0) + timedelta(minutes=5)
    wait_secs = (target - datetime.now()).total_seconds()
    if wait_secs < 60:
        logger.info("Launch is too soon. Aborting...")
        sys.exit(0)
    logger.info(f"Scheduled at: {target.strftime('%Y-%m-%d %H:%M:%S')}")
    time.sleep(wait_secs)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    # Parse arguments:
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', type=int, required=True, help='index of trader')
    parser.add_argument('--token', type=str, help='Token contract address (default: CAKE from deployed_addresses.json)')
    parser.add_argument('--recipient', type=str, help='Recipient address (default: send to self)')
    parser.add_argument('--amount', type=int, help='Transfer amount in wei (default: 1000)')
    parser.add_argument('--txs', type=int, default=200, help='Number of transactions per account (default: 200)')
    args = parser.parse_args()
    
    trader_index = args.n
    
    # Initialize accounts:
    mnemonic = open("mnemonic.txt", "r").read().strip()
    start_index = 10 * trader_index
    accounts = generate_ethereum_accounts(mnemonic, count=100)[start_index:start_index+10]
    
    # Change ChainId here to test different networks
    objects = [
        Trader(
            ChainId.MY_CUSTOM_L2, 
            account, 
            transfer_txs_count=args.txs,
            token_address=args.token,
            recipient_address=args.recipient,
            transfer_amount=args.amount
        ) 
        for account in accounts
    ]
    
    # Execute in parallel:
    wait_until_target_time()  # All terminals sync to next 5-min mark
    run_in_parallel(objects)
