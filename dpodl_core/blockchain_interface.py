import os
import time
import logging
from web3 import Web3
# from web3.middleware import geth_poa_middleware # Old import
# Try importing directly from the specific module
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from web3.exceptions import TransactionNotFound

# Import config and contract info loader
from .blockchain_config import NETWORK_URL, CHAIN_ID, get_contract_info

logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- Global Web3 Connection and Contracts --- #
# Initialize connection and contracts once when the module is loaded.
# This assumes the interface is used within a single process context.
# For multi-process (like Ray workers potentially), consider passing
# connection/contract instances or re-initializing per process.

w3 = None
registry_contract = None
mempool_contract = None
token_contract = None

def initialize_blockchain_connection():
    global w3, registry_contract, mempool_contract, token_contract
    if w3:
        logger.debug("Blockchain connection already initialized.")
        return # Already initialized

    logger.info(f"Initializing blockchain connection to {NETWORK_URL} (Chain ID: {CHAIN_ID})")
    try:
        w3 = Web3(Web3.HTTPProvider(NETWORK_URL))
        # Inject PoA middleware if necessary
        logger.debug("Injecting PoA middleware...")
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0) # Use the correct imported name

        if not w3.is_connected():
            raise ConnectionError(f"Failed to connect to Web3 provider at {NETWORK_URL}")

        logger.info(f"Connected to blockchain. Chain ID: {w3.eth.chain_id}")
        if w3.eth.chain_id != CHAIN_ID:
            logger.warning(f"Connected Chain ID ({w3.eth.chain_id}) does not match expected Chain ID ({CHAIN_ID}) from config!")

        # --- Load Contracts ---
        logger.info("Loading contract addresses and ABIs...")

        registry_address, registry_abi = get_contract_info("ModelRegistry")
        if registry_address and registry_abi:
            registry_contract = w3.eth.contract(address=registry_address, abi=registry_abi)
            logger.info(f"ModelRegistry contract loaded at {registry_address}")
        else:
            logger.error("Failed to load ModelRegistry info. Interface may be unusable.")

        mempool_address, mempool_abi = get_contract_info("MTXMempool")
        if mempool_address and mempool_abi:
            mempool_contract = w3.eth.contract(address=mempool_address, abi=mempool_abi)
            logger.info(f"MTXMempool contract loaded at {mempool_address}")
        else:
            logger.error("Failed to load MTXMempool info.")

        token_address, token_abi = get_contract_info("DPoDLToken")
        if token_address and token_abi:
            token_contract = w3.eth.contract(address=token_address, abi=token_abi)
            logger.info(f"DPoDLToken contract loaded at {token_address}")
        else:
            logger.error("Failed to load DPoDLToken info.")

    except Exception as e:
        logger.error(f"Failed to initialize blockchain connection or load contracts: {e}", exc_info=True)
        # Reset globals on failure
        w3 = None
        registry_contract = None
        mempool_contract = None
        token_contract = None

# Call initialization when the module is first imported
initialize_blockchain_connection()

# --- Helper Functions to Access Globals (optional) ---
def get_w3():
    if not w3:
        logger.warning("Web3 connection not initialized. Call initialize_blockchain_connection() or check for errors.")
    return w3

def get_registry():
    if not registry_contract:
        logger.warning("ModelRegistry contract not loaded.")
    return registry_contract

def get_mempool():
    if not mempool_contract:
        logger.warning("MTXMempool contract not loaded.")
    return mempool_contract

def get_token():
    if not token_contract:
        logger.warning("DPoDLToken contract not loaded.")
    return token_contract

# --- Contract Read Functions --- #

def get_current_reference_cid() -> str | None:
    """Gets the current reference model CID from the ModelRegistry."""
    registry = get_registry()
    if not registry:
        return None
    try:
        logger.debug("Calling ModelRegistry.getCurrentReferenceModel()...")
        cid = registry.functions.getCurrentReferenceModel().call()
        logger.info(f"Current reference model CID from registry: {cid}")
        return cid
    except Exception as e:
        logger.error(f"Error calling getCurrentReferenceModel: {e}", exc_info=True)
        return None

# Add other read functions as needed (e.g., get_t1_threshold, get_mtx_details)

# --- Contract Write Functions (Require Signing) --- #

def _send_signed_transaction(w3_instance, chain_id, transaction, private_key):
    """Helper to sign and send a transaction using EIP-1559."""
    try:
        account = w3_instance.eth.account.from_key(private_key)
        address = account.address
        logger.info(f"Signing transaction using address: {address}")

        # Remove legacy gasPrice if it exists (shouldn't, but defensively)
        transaction.pop('gasPrice', None)

        # Estimate gas limit
        try:
            gas_estimate = w3_instance.eth.estimate_gas(transaction)
            transaction['gas'] = int(gas_estimate * 1.2) # Add a buffer
            logger.info(f"Estimated gas: {gas_estimate}, using gas limit: {transaction['gas']}")
        except Exception as estimate_e:
            logger.warning(f"Gas estimation failed: {estimate_e}. Using fixed gas limit.")
            transaction['gas'] = 2_000_000 # Fallback fixed gas limit

        # Set EIP-1559 fees
        # For localhost/hardhat, priority fee can often be low
        # For testnets/mainnet, use w3.eth.max_priority_fee or oracle
        max_priority_fee_per_gas = w3_instance.to_wei('1', 'gwei') # Example: 1 Gwei priority fee
        latest_block = w3_instance.eth.get_block('latest')
        base_fee = latest_block.baseFeePerGas
        # Calculate maxFeePerGas = (2 * baseFee) + maxPriorityFee (recommended practice)
        max_fee_per_gas = (2 * base_fee) + max_priority_fee_per_gas
        
        transaction['maxPriorityFeePerGas'] = max_priority_fee_per_gas
        transaction['maxFeePerGas'] = max_fee_per_gas
        logger.info(f"Using EIP-1559 fees: maxFee={w3_instance.from_wei(max_fee_per_gas, 'gwei')} Gwei, maxPriorityFee={w3_instance.from_wei(max_priority_fee_per_gas, 'gwei')} Gwei")

        # Get nonce
        nonce = w3_instance.eth.get_transaction_count(address)
        transaction['nonce'] = nonce
        transaction['chainId'] = chain_id

        # Sign transaction
        logger.debug(f"Transaction dict FINAL before signing: {transaction}")
        
        signed_tx = w3_instance.eth.account.sign_transaction(transaction, private_key)

        # --- Advanced Inspection of SignedTransaction object ---
        logger.info("--- Advanced SignedTransaction Object Inspection ---")
        logger.info(f"Type of signed_tx: {type(signed_tx)}")
        logger.info(f"Attributes of signed_tx (dir()): {dir(signed_tx)}")
        logger.info(f"signed_tx object (repr()): {repr(signed_tx)}")

        raw_tx_bytes_for_sending = None
        found_attribute_name = None
        potential_raw_tx_attributes = [
            'rawTransaction', 'raw_transaction', 'rlp', 'rlp_encoded', 
            'serialized', 'signed_transaction_bytes'
        ]

        for attr_name in potential_raw_tx_attributes:
            try:
                value = getattr(signed_tx, attr_name, None)
                if value is not None and isinstance(value, bytes):
                    raw_tx_bytes_for_sending = value
                    found_attribute_name = attr_name
                    logger.info(f"SUCCESS: Found raw transaction bytes in attribute '{found_attribute_name}'. Type: {type(raw_tx_bytes_for_sending)}, Value (hex): {raw_tx_bytes_for_sending.hex()}")
                    break # Found it, no need to check others
                elif value is not None:
                    logger.info(f"Found attribute '{attr_name}' but it's not bytes. Type: {type(value)}, Value: {value}")
            except AttributeError:
                logger.debug(f"Attribute '{attr_name}' not found on signed_tx.")
            except Exception as e_getattr:
                logger.warning(f"Error accessing attribute '{attr_name}': {e_getattr}")

        if raw_tx_bytes_for_sending is None:
            logger.error("CRITICAL: Could not find suitable raw transaction bytes attribute after checking common names.")
            # Consider raising the original AttributeError if it was for 'rawTransaction', or a more general one.
            raise AttributeError(f"Could not find raw transaction bytes in SignedTransaction object. Inspected attributes: {potential_raw_tx_attributes}. Object representation: {repr(signed_tx)}")
        
        logger.info(f"Using attribute '{found_attribute_name}' for raw transaction bytes.")
        # --- End of Advanced Inspection ---

        # Send transaction
        logger.info(f"Sending transaction from {address} (Nonce: {nonce})...")
        tx_hash = w3_instance.eth.send_raw_transaction(raw_tx_bytes_for_sending)
        logger.info(f"Transaction sent. Hash: {tx_hash.hex()}")

        # Wait for receipt (consider timeout)
        logger.info("Waiting for transaction receipt...")
        # Set a reasonable timeout, e.g., 120 seconds
        receipt = w3_instance.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        logger.info(f"Transaction confirmed. Block: {receipt.blockNumber}, Gas used: {receipt.gasUsed}")
        
        if receipt.status == 0:
             logger.error(f"Transaction FAILED! Receipt: {receipt}")
             # Consider raising an exception here
             return None
             
        return receipt

    except TransactionNotFound:
        logger.error(f"Transaction {tx_hash.hex()} not found after timeout.")
        return None
    except Exception as e:
        logger.error(f"Error sending transaction: {e}", exc_info=True)
        return None


def submit_block(
    ipfs_cid: str,
    accuracy_bps: int,
    steps: int,
    post_hash: int, # Assuming post_hash is uint256 in contract
    reference_cid: str,
    signer_private_key: str
) -> dict | None:
    """Submits a block to the ModelRegistry contract."""
    w3_conn = get_w3()
    registry = get_registry()
    if not w3_conn or not registry:
        logger.error("Cannot submit block: Interface not initialized.")
        return None
    if not signer_private_key:
         logger.error("Cannot submit block: Signer private key required.")
         return None

    try:
        logger.info(f"Building submitBlock transaction for CID: {ipfs_cid}")
        # Ensure accuracy_bps and steps are ints if needed by web3.py (should handle python ints/bigints)
        # Convert post_hash hex string to integer if necessary (assuming int input here)
        # Ensure reference_cid is string

        transaction = registry.functions.submitBlock(
            ipfs_cid,
            accuracy_bps,
            steps,
            post_hash, # Pass as int/bigint
            reference_cid
        ).build_transaction({
            # 'from': account.address, # Let helper handle this
            # 'nonce': w3.eth.get_transaction_count(account.address),
            # Gas/GasPrice/ChainID handled by helper
        })
        
        receipt = _send_signed_transaction(w3_conn, CHAIN_ID, transaction, signer_private_key)
        return receipt # Return receipt (or None on failure)

    except Exception as e:
        logger.error(f"Error building or sending submitBlock transaction: {e}", exc_info=True)
        return None

def submit_mtx(
    ipfs_cid: str,
    accuracy_bps: int,
    steps: int,
    reference_cid: str,
    signer_private_key: str
) -> dict | None:
    """Submits a model transaction (MTX) to the MTXMempool contract."""
    w3_conn = get_w3()
    mempool = get_mempool()
    if not w3_conn or not mempool:
        logger.error("Cannot submit MTX: Interface not initialized.")
        return None
    if not signer_private_key:
         logger.error("Cannot submit MTX: Signer private key required.")
         return None

    try:
        logger.info(f"Building submitMtx transaction for CID: {ipfs_cid}")
        transaction = mempool.functions.submitMtx(
            ipfs_cid,
            accuracy_bps,
            steps,
            reference_cid
        ).build_transaction({
            # Params handled by helper
        })

        receipt = _send_signed_transaction(w3_conn, CHAIN_ID, transaction, signer_private_key)
        return receipt

    except Exception as e:
        logger.error(f"Error building or sending submitMtx transaction: {e}", exc_info=True)
        return None

# Example usage (if run directly)
if __name__ == '__main__':
    print("\n--- Blockchain Interface Module --- ")
    if not w3:
        print("Blockchain connection failed during import.")
    else:
        print("Blockchain connection successful.")
        print(f"Network URL: {NETWORK_URL}")
        print(f"Chain ID: {CHAIN_ID}")
        # Test reading current reference
        current_ref = get_current_reference_cid()
        print(f"Current Reference CID: {current_ref}")

        # Example Transaction (requires a PRIVATE_KEY in .env for local node testing)
        test_private_key = os.getenv('TEST_WORKER_PRIVATE_KEY') # Add this to .env for testing
        if test_private_key and registry_contract:
             print("\n--- Testing Transaction Submission (Requires TEST_WORKER_PRIVATE_KEY in .env) ---")
             # Note: Use dummy values that meet contract requirements for local testing
             # These values likely won't pass real thresholds but test transaction flow
             dummy_cid = f"QmTestTxCID_{int(time.time())}"
             dummy_acc = 8600 # 86%
             dummy_steps = 100
             dummy_post_hash = 12345 # Small int, should pass threshold
             dummy_ref = get_current_reference_cid() or "" # Use current or genesis
             
             print(f"Submitting dummy block: CID={dummy_cid}, Acc={dummy_acc}, Steps={dummy_steps}, PostHash={dummy_post_hash}, Ref={dummy_ref}")
             block_receipt = submit_block(
                 dummy_cid, 
                 dummy_acc, 
                 dummy_steps, 
                 dummy_post_hash, 
                 dummy_ref, 
                 test_private_key
             )
             if block_receipt:
                  print(f"  Block submission SUCCESS! Tx Hash: {block_receipt.transactionHash.hex()}")
                  # Update reference for potential MTX test
                  dummy_ref = dummy_cid 
             else:
                  print("  Block submission FAILED.")
             
             # Test MTX submission
             dummy_mtx_cid = f"QmTestMtxCID_{int(time.time())}"
             dummy_mtx_acc = 7000 # Below block threshold
             dummy_mtx_steps = 50
             
             print(f"Submitting dummy MTX: CID={dummy_mtx_cid}, Acc={dummy_mtx_acc}, Steps={dummy_mtx_steps}, Ref={dummy_ref}")
             mtx_receipt = submit_mtx(
                 dummy_mtx_cid,
                 dummy_mtx_acc,
                 dummy_mtx_steps,
                 dummy_ref, # Reference the block we just submitted (or tried to)
                 test_private_key
             )
             if mtx_receipt:
                 print(f"  MTX submission SUCCESS! Tx Hash: {mtx_receipt.transactionHash.hex()}")
             else:
                  print("  MTX submission FAILED.")
                 
        elif not test_private_key:
            print("\nSkipping transaction tests: TEST_WORKER_PRIVATE_KEY not found in .env") 