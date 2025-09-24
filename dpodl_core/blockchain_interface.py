import os
import time
import logging
import json
from web3 import Web3
# from web3.middleware import geth_poa_middleware # Old import
# Try importing directly from the specific module
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from web3.exceptions import TransactionNotFound, ContractLogicError
from web3.logs import EventLogErrorFlags # Import EventLogErrorFlags
from eth_account import Account
from eth_account.datastructures import SignedTransaction
from dotenv import load_dotenv

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

TX_TIMEOUT = int(os.getenv("TX_TIMEOUT", "300"))

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
    logger.warning("DEPRECATED: get_current_reference_cid() is deprecated. Use get_current_reference_model_state_cid() or get_current_reference_dpodl_checkpoint_cid().")
    # For backward compatibility during transition, it can call the new model_state_cid function
    return get_current_reference_model_state_cid()

def get_current_reference_model_state_cid() -> str | None:
    """Gets the current reference model's STATE CID from the ModelRegistry."""
    registry = get_registry()
    if not registry:
        return None
    try:
        logger.debug("Calling ModelRegistry.getCurrentReferenceModelStateCID()...")
        cid = registry.functions.getCurrentReferenceModelStateCID().call()
        logger.info(f"Current reference model state CID from registry: {cid}")
        return cid
    except Exception as e:
        logger.error(f"Error calling getCurrentReferenceModelStateCID: {e}", exc_info=True)
        return None

def get_current_reference_dpodl_checkpoint_cid() -> str | None:
    """Gets the current reference model's DPoDL CHECKPOINT CID from the ModelRegistry."""
    registry = get_registry()
    if not registry:
        return None
    try:
        logger.debug("Calling ModelRegistry.getCurrentReferenceDpodlCheckpointCID()...")
        cid = registry.functions.getCurrentReferenceDpodlCheckpointCID().call()
        logger.info(f"Current reference DPoDL checkpoint CID from registry: {cid}")
        return cid
    except Exception as e:
        logger.error(f"Error calling getCurrentReferenceDpodlCheckpointCID: {e}", exc_info=True)
        return None

# --- MTXMempool Read Functions ---
MTX_STATUS_MAP = {
    0: "Pending",
    1: "SelectedForProcessing",
    2: "Processed",
    3: "Rejected"
}

def get_mtx_mempool_count() -> int | None:
    """Gets the current total number of MTXs submitted to MTXMempool."""
    mempool = get_mempool()
    if not mempool:
        return None
    try:
        logger.debug("Calling MTXMempool.getMtxCount()...")
        count = mempool.functions.getMtxCount().call()
        logger.info(f"MTXMempool count: {count}")
        return count
    except Exception as e:
        logger.error(f"Error calling MTXMempool.getMtxCount: {e}", exc_info=True)
        return None

def get_mtx_details(mtx_id: int) -> dict | None:
    """Gets the details of a specific MTX by its ID from MTXMempool."""
    mempool = get_mempool()
    if not mempool:
        return None
    try:
        logger.debug(f"Calling MTXMempool.getMtxDetails({mtx_id})...")
        # The order of fields in the returned tuple matches the struct definition in Solidity
        # struct ModelTransaction {
        #     uint256 mtxId;
        #     string ipfsCID;
        #     uint256 accuracyBPS;
        #     uint256 steps;
        #     string referenceModelCID;
        #     address submitter;
        #     uint256 timestamp;
        #     Status status; // enum will be an int (0-3)
        #     bool isValid;
        # }
        details_tuple = mempool.functions.getMtxDetails(mtx_id).call()
        
        if not details_tuple[8]: # Check isValid flag
            logger.warning(f"MTX ID {mtx_id} is not valid or has been marked invalid.")
            return None

        details_dict = {
            "mtxId": details_tuple[0],
            "ipfsCID": details_tuple[1],
            "accuracyBPS": details_tuple[2],
            "steps": details_tuple[3],
            "referenceModelCID": details_tuple[4],
            "submitter": details_tuple[5],
            "timestamp": details_tuple[6],
            "status_raw": details_tuple[7],
            "status_str": MTX_STATUS_MAP.get(details_tuple[7], "UnknownStatus"),
            "isValid": details_tuple[8]
        }
        logger.info(f"MTX {mtx_id} details: {details_dict}")
        return details_dict
    except Exception as e:
        # Check if it's due to our custom InvalidMtxId error (if web3.py surfaces it clearly)
        # For now, general catch
        logger.error(f"Error calling MTXMempool.getMtxDetails({mtx_id}): {e}", exc_info=True)
        return None

def fetch_pending_mtxs() -> list:
    """Fetches all MTXs from MTXMempool that are in 'Pending' status."""
    pending_mtxs = []
    total_mtx_count = get_mtx_mempool_count()

    if total_mtx_count is None:
        logger.error("Could not fetch total MTX count. Cannot fetch pending MTXs.")
        return pending_mtxs # Return empty list
    
    if total_mtx_count == 0:
        logger.info("No MTXs in the mempool.")
        return pending_mtxs

    logger.info(f"Total MTXs to check: {total_mtx_count}")
    for i in range(1, total_mtx_count + 1): # MTX IDs start from 1
        details = get_mtx_details(i)
        if details and details["status_raw"] == 0: # 0 is Status.Pending
            pending_mtxs.append(details)
            logger.debug(f"Added pending MTX ID {i} to the list.")
        elif not details:
            logger.warning(f"Could not retrieve details for MTX ID {i}, skipping.")
            # This could happen if an ID was skipped or if there's an issue with an MTX
    
    logger.info(f"Found {len(pending_mtxs)} MTXs in Pending status.")
    return pending_mtxs

# --- New function to get MTXMempool address from ModelRegistry --- #
def get_model_registry_mempool_address() -> str | None:
    """Reads the mtxMempoolContract address set in the ModelRegistry contract."""
    registry = get_registry()
    if not registry:
        logger.error("ModelRegistry contract not loaded, cannot get its MTXMempool address.")
        return None
    try:
        logger.debug("Calling ModelRegistry.mtxMempoolContract()...")
        address = registry.functions.mtxMempoolContract().call()
        logger.info(f"MTXMempool address configured in ModelRegistry: {address}")
        return address
    except Exception as e:
        logger.error(f"Error calling ModelRegistry.mtxMempoolContract(): {e}", exc_info=True)
        return None

# Add other read functions as needed (e.g., get_t1_threshold, get_mtx_details)

# --- Contract Write Functions (Require Signing) --- #

def _send_signed_transaction(w3_instance, chain_id, transaction, private_key):
    """Helper to sign and send a transaction using EIP-1559."""
    try:
        account = w3_instance.eth.account.from_key(private_key)
        address = account.address
        logger.info(f"Signing transaction using address: {address}")

        # Ensure 'from' field is set for eth_call and estimate_gas
        if 'from' not in transaction:
            transaction['from'] = address
        elif transaction['from'] != address:
            logger.warning(f"Transaction 'from' field {transaction['from']} differs from signer {address}. Overwriting.")
            transaction['from'] = address

        # Remove legacy gasPrice if it exists (shouldn't, but defensively)
        transaction.pop('gasPrice', None)

        # Attempt eth_call to get potential revert reason before estimating gas
        try:
            logger.debug(f"Attempting eth_call for transaction: {transaction}")
            # For eth_call, we don't need nonce, gas, maxFeePerGas, maxPriorityFeePerGas yet.
            # A copy of the transaction without these might be safer for eth_call.
            minimal_call_tx = transaction.copy()
            minimal_call_tx.pop('nonce', None)
            minimal_call_tx.pop('gas', None)
            minimal_call_tx.pop('maxFeePerGas', None)
            minimal_call_tx.pop('maxPriorityFeePerGas', None)
            # Ensure 'from' is present for eth_call
            if 'from' not in minimal_call_tx:
                 minimal_call_tx['from'] = address

            if 'value' in transaction: # Include value if it's a payable function
                minimal_call_tx['value'] = transaction.get('value')

            # Add a high gas limit for the eth_call simulation
            minimal_call_tx['gas'] = 5_000_000 # A large gas limit for simulation

            # --- DETAILED LOGGING FOR PRE-FLIGHT ETH_CALL (using minimal_call_tx) ---
            logger.info(f"PRE-FLIGHT ETH_CALL (minimal_call_tx) DETAILS:")
            logger.info(f"  To: {minimal_call_tx.get('to')}")
            logger.info(f"  From: {minimal_call_tx.get('from')}")
            logger.info(f"  Data: {minimal_call_tx.get('data')}")
            logger.info(f"  Gas: {minimal_call_tx.get('gas')}")
            logger.info(f"  Value: {minimal_call_tx.get('value', 'Not Present')}")
            # --- END DETAILED LOGGING ---

            call_result = w3_instance.eth.call(minimal_call_tx, 'latest')
            logger.debug(f"eth_call successful. Result: {call_result.hex() if isinstance(call_result, bytes) else call_result}")
        except Exception as call_e: # Catching a broad exception to see any error from eth_call
            logger.error(f"eth_call FAILED before gas estimation. Error: {call_e}", exc_info=True)
            # If it's a ContractLogicError, it might contain the revert reason we need.
            # We can choose to re-raise or just log and let estimate_gas try.
            # For now, just log and proceed to estimate_gas, as estimate_gas itself might also fail with a reason.

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

        # Extract raw transaction bytes for sending
        raw_tx_bytes_for_sending = None
        potential_raw_tx_attributes = [
            'rawTransaction', 'raw_transaction', 'rlp', 'rlp_encoded', 
            'serialized', 'signed_transaction_bytes'
        ]

        for attr_name in potential_raw_tx_attributes:
            try:
                value = getattr(signed_tx, attr_name, None)
                if value is not None and isinstance(value, bytes):
                    raw_tx_bytes_for_sending = value
                    logger.debug(f"Found raw transaction bytes in attribute '{attr_name}'")
                    break # Found it, no need to check others
            except AttributeError:
                logger.debug(f"Attribute '{attr_name}' not found on signed_tx.")
            except Exception as e_getattr:
                logger.warning(f"Error accessing attribute '{attr_name}': {e_getattr}")

        if raw_tx_bytes_for_sending is None:
            logger.error("CRITICAL: Could not find suitable raw transaction bytes attribute after checking common names.")
            # Consider raising the original AttributeError if it was for 'rawTransaction', or a more general one.
            raise AttributeError(f"Could not find raw transaction bytes in SignedTransaction object. Inspected attributes: {potential_raw_tx_attributes}. Object representation: {repr(signed_tx)}")
        
        # Transaction ready for sending

        # Send transaction
        logger.info(f"Sending transaction from {address} (Nonce: {nonce})...")
        tx_hash = w3_instance.eth.send_raw_transaction(raw_tx_bytes_for_sending)
        logger.info(f"Transaction sent. Hash: {tx_hash.hex()}")

        # Wait for receipt (consider timeout)
        logger.info("Waiting for transaction receipt...")
        try:
            receipt = w3_instance.eth.wait_for_transaction_receipt(tx_hash, timeout=TX_TIMEOUT)
            # Log more details from the receipt, ensuring it's not excessively verbose unless debugging
            log_receipt_details(receipt) 
        
            if receipt.status == 0:
                    logger.error(f"Transaction failed (receipt.status == 0).")
                    # Attempt to get revert reason by replaying the transaction using eth_call at the block before it was mined
                    try:
                        tx_details = w3_instance.eth.get_transaction(tx_hash)
                        if tx_details and tx_details.get('blockNumber') is not None:
                            call_params = {
                                'to': tx_details.get('to'),
                                'from': tx_details.get('from'), # Original EOA sender
                                'value': tx_details.get('value'),
                                'data': tx_details.get('input'), # 'input' is the data field for historical transactions
                                # Add gas and gasPrice if they were part of the original tx, or allow eth_call to use defaults
                                'gas': tx_details.get('gas'),
                                'gasPrice': tx_details.get('gasPrice')
                            }
                            # Remove None values to avoid issues with eth_call
                            call_params = {k: v for k, v in call_params.items() if v is not None}
                            
                            logger.info(f"Attempting to get revert reason by re-calling failed tx (hash: {tx_hash.hex()}) at block {tx_details.blockNumber - 1}")
                            revert_call_result = w3_instance.eth.call(call_params, tx_details.blockNumber - 1)
                            logger.error(f"  eth_call result for failed tx: {revert_call_result.hex() if isinstance(revert_call_result, bytes) else revert_call_result}")
                            # Basic attempt to decode common string revert: Error(string)
                            if isinstance(revert_call_result, bytes) and revert_call_result.startswith(bytes.fromhex('08c379a0')):
                                reason = w3_instance.codec.decode(['string'], revert_call_result[4:])[0]
                                logger.error(f"  Decoded revert reason: {reason}")
                            else:
                                logger.error(f"  Could not decode standard string revert reason from result.")
                        else:
                            logger.error("Could not get transaction details or blockNumber to attempt fetching revert reason.")
                    except ContractLogicError as cle:
                         logger.error(f"  Re-call for revert reason failed with ContractLogicError. Message: '{cle.message}'. Data: {cle.data if hasattr(cle, 'data') else 'N/A'}")
                    except Exception as e_call_revert:
                        logger.error(f"  Could not fetch revert reason via eth_call: {e_call_revert}", exc_info=True)
                    return {"tx_hash": tx_hash.hex(), "receipt": receipt, "error": "Transaction reverted with status 0", "status": 0}

            logger.info(f"Transaction confirmed. Block: {receipt.blockNumber}, Gas used: {receipt.gasUsed}")
            return {"tx_hash": tx_hash.hex(), "receipt": receipt, "status": 1}
        except w3_instance.exceptions.TimeExhausted:
            logger.error(f"Timeout waiting for transaction receipt for tx {tx_hash.hex()}", exc_info=True)
            return {"tx_hash": tx_hash.hex(), "receipt": None, "error": "Timeout waiting for receipt", "status": -2} # Custom status for timeout
    except TransactionNotFound:
        logger.error(f"Transaction {tx_hash.hex()} not found after timeout.")
        return None
    except Exception as e:
        logger.error(f"Error sending transaction: {e}", exc_info=True)
        return None


def submit_block(
    new_model_state_cid: str,
    new_dpodl_checkpoint_cid: str,
    accuracy_bps: int,
    steps: int,
    post_hash: int,
    reference_dpodl_checkpoint_cid: str,
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
        logger.info(f"Building submitBlock transaction for Model State CID: {new_model_state_cid}, DPoDL Checkpoint CID: {new_dpodl_checkpoint_cid}")

        transaction = registry.functions.submitBlock(
            new_model_state_cid,
            new_dpodl_checkpoint_cid,
            accuracy_bps,
            steps,
            post_hash,
            reference_dpodl_checkpoint_cid
        ).build_transaction({
            # Params handled by helper
        })
        
        receipt = _send_signed_transaction(w3_conn, CHAIN_ID, transaction, signer_private_key)
        return receipt

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
    """Submits a model transaction (MTX) to the MTXMempool contract.
    Returns a dictionary containing the receipt and the parsed mtxId if successful, else None.
    """
    w3_conn = get_w3()
    mempool_contract_instance = get_mempool() # Renamed for clarity from global 'mempool'
    if not w3_conn or not mempool_contract_instance:
        logger.error("Cannot submit MTX: Interface not initialized.")
        return None
    if not signer_private_key:
         logger.error("Cannot submit MTX: Signer private key required.")
         return None

    try:
        logger.info(f"Building submitMtx transaction for CID: {ipfs_cid}")
        transaction = mempool_contract_instance.functions.submitMtx(
            ipfs_cid,
            accuracy_bps,
            steps,
            reference_cid
        ).build_transaction({
            # Params handled by helper
        })

        # receipt = _send_signed_transaction(w3_conn, CHAIN_ID, transaction, signer_private_key) # Old call
        send_result = _send_signed_transaction(w3_conn, CHAIN_ID, transaction, signer_private_key)
        
        if send_result and send_result.get("status") == 1:
            actual_receipt = send_result.get("receipt") # This is the actual receipt object
            tx_hash_hex = send_result.get("tx_hash")
            logger.info(f"MTX submission transaction successful. TxHash: {tx_hash_hex}. Parsing MtxSubmitted event...")
            try:
                # Correctly use the EventLogErrorFlags enum and the actual receipt object
                events = mempool_contract_instance.events.MtxSubmitted().process_receipt(actual_receipt, errors=EventLogErrorFlags.Warn)
                if events:
                    parsed_mtx_id = events[0]['args']['mtxId']
                    logger.info(f"Successfully parsed MtxSubmitted event. MTX ID: {parsed_mtx_id}")
                    return {"tx_hash": tx_hash_hex, "receipt": actual_receipt, "mtxId": parsed_mtx_id, "status": 1}
                else:
                    logger.warning("MtxSubmitted event not found in transaction receipt logs, though transaction was successful.")
                    return {"tx_hash": tx_hash_hex, "receipt": actual_receipt, "mtxId": None, "status": 1} # Return receipt but indicate mtxId parsing failure
            except Exception as e_event_parsing: 
                logger.error(f"Error parsing MtxSubmitted event: {e_event_parsing}", exc_info=True)
                return {"tx_hash": tx_hash_hex, "receipt": actual_receipt, "mtxId": None, "status": 1} # Return receipt but indicate mtxId parsing failure
        elif send_result: # Transaction failed but we got a result dictionary (e.g. status 0)
            logger.error(f"MTX submission transaction failed. Result: {send_result}")
            return send_result # Forward the error result
        else: # _send_signed_transaction returned None (e.g. timeout before receipt)
            logger.error("MTX submission failed: No result from _send_signed_transaction.")
            return None

    except Exception as e:
        logger.error(f"Error building or sending submitMtx transaction: {e}", exc_info=True)
        return None

def update_reference_model_from_mtx(
    model_state_cid: str,
    dpodl_checkpoint_cid: str,
    mtx_id: int,
    signer_private_key: str
) -> dict | None:
    """Calls updateReferenceModelFromMtx in ModelRegistry.sol."""
    w3_conn = get_w3()
    registry = get_registry()
    if not w3_conn or not registry:
        logger.error("Cannot update reference model from MTX: Interface not initialized.")
        return None
    if not signer_private_key:
         logger.error("Cannot update reference model from MTX: Signer private key required.")
         return None

    try:
        logger.info(f"Building updateReferenceModelFromMtx transaction for MTX ID: {mtx_id}, ModelStateCID: {model_state_cid}, DpodlCheckpointCID: {dpodl_checkpoint_cid}")
        transaction = registry.functions.updateReferenceModelFromMtx(
            model_state_cid,
            dpodl_checkpoint_cid,
            mtx_id
        ).build_transaction({
            # Params handled by helper
        })

        receipt = _send_signed_transaction(w3_conn, CHAIN_ID, transaction, signer_private_key)
        return receipt

    except ContractLogicError as e:
        logger.error(f"ContractLogicError during updateReferenceModelFromMtx (MTX ID: {mtx_id}): {e}")
        # Try to get revert reason if available in data
        if hasattr(e, 'args') and e.args:
            error_details = e.args[0]
            logger.error(f"  Error args: {error_details}")
            if isinstance(error_details, dict):
                message = error_details.get('message', 'No message in dict')
                data = error_details.get('data', 'No data in dict')
                logger.error(f"  ContractLogicError Message: {message}")
                logger.error(f"  ContractLogicError Data: {data}")
                if isinstance(data, str) and data.startswith('0x') and len(data) > 2:
                    try:
                        # Attempt to decode common revert string selector: Error(string)
                        if data.startswith('0x08c379a0'): # selector for Error(string)
                            reason = w3_conn.codec.decode(['string'], bytes.fromhex(data[10:]))[0] # remove selector and offset
                            logger.error(f"  Decoded revert reason: {reason}")
                        else:
                            logger.warning(f"  Data does not match known Error(string) selector. Raw data: {data}")
                    except Exception as decode_err:
                        logger.error(f"  Could not decode revert reason from data '{data}': {decode_err}")
            elif isinstance(error_details, str):
                 logger.error(f"  Raw revert message string: {error_details}")
        return None
    except Exception as e:
        logger.error(f"Generic error building or sending updateReferenceModelFromMtx transaction (MTX ID: {mtx_id}): {e}", exc_info=True)
        return None

def update_mtx_status(
    mtx_id: int,
    status_code: int, # Use integer codes from MTX_STATUS_MAP
    signer_private_key: str
) -> dict | None:
    """Updates the status of an MTX in the MTXMempool."""
    w3_conn = get_w3()
    mempool = get_mempool() # Corrected from mempool_contract_instance to mempool
    if not w3_conn or not mempool:
        logger.error("Cannot update MTX status: Interface not initialized.")
        return None
    if not signer_private_key:
        logger.error("Cannot update MTX status: Signer private key required.")
        return None

    if status_code not in MTX_STATUS_MAP:
        logger.error(f"Invalid status_code {status_code} for update_mtx_status. Valid codes are {list(MTX_STATUS_MAP.keys())}.")
        return None
    
    status_str = MTX_STATUS_MAP[status_code]
    logger.info(f"Building updateMtxStatus transaction for MTX ID: {mtx_id} to status: {status_str} ({status_code})")

    try:
        transaction = mempool.functions.updateMtxStatus(
            mtx_id,
            status_code
        ).build_transaction({
            # Gas/nonce params handled by _send_signed_transaction helper
        })
        
        send_result = _send_signed_transaction(w3_conn, CHAIN_ID, transaction, signer_private_key)
        
        if send_result and send_result.get("status") == 1:
            actual_receipt = send_result.get("receipt")
            tx_hash_hex = send_result.get("tx_hash")
            logger.info(f"MTX status update transaction successful for MTX ID {mtx_id}. TxHash: {tx_hash_hex}. Parsing MtxStatusUpdated event...")
            try:
                events = mempool.events.MtxStatusUpdated().process_receipt(actual_receipt, errors=EventLogErrorFlags.Warn)
                if events:
                    event_args = events[0]['args']
                    parsed_mtx_id = event_args['mtxId']
                    new_status_from_event = event_args['newStatus']
                    logger.info(f"Successfully parsed MtxStatusUpdated event. MTX ID: {parsed_mtx_id}, New Status: {MTX_STATUS_MAP.get(new_status_from_event, 'Unknown')} ({new_status_from_event})")
                    return {"tx_hash": tx_hash_hex, "receipt": actual_receipt, "parsed_mtx_id": parsed_mtx_id, "new_status": new_status_from_event, "status": 1}
                else:
                    logger.warning(f"MtxStatusUpdated event not found in transaction receipt logs for MTX ID {mtx_id}, though transaction was successful.")
                    return {"tx_hash": tx_hash_hex, "receipt": actual_receipt, "parsed_mtx_id": None, "new_status": None, "status": 1}
            except Exception as e_event_parsing:
                logger.error(f"Error parsing MtxStatusUpdated event for MTX ID {mtx_id}: {e_event_parsing}", exc_info=True)
                return {"tx_hash": tx_hash_hex, "receipt": actual_receipt, "parsed_mtx_id": None, "new_status": None, "status": 1}
        elif send_result: # Transaction failed but we got a result dictionary (e.g. status 0)
            logger.error(f"MTX status update transaction failed for MTX ID {mtx_id}. Result: {send_result}")
            return send_result # Forward the error result
        else: # _send_signed_transaction returned None (e.g. timeout before receipt or other critical failure)
            logger.error(f"MTX status update failed for MTX ID {mtx_id}: No result from _send_signed_transaction.")
            return None

    except Exception as e:
        logger.error(f"Error building or sending updateMtxStatus transaction for MTX ID {mtx_id}: {e}", exc_info=True)
        return None

def log_receipt_details(receipt):
    if logger.getEffectiveLevel() <= logging.DEBUG: # Only log full receipt if debug level is set
        logger.debug(f"Full Transaction Receipt: {json.dumps(json.loads(Web3.to_json(receipt)), indent=2)}")
    else:
        logger.info(
            f"Receipt Status: {receipt.status}, Block: {receipt.blockNumber}, " 
            f"GasUsed: {receipt.gasUsed}, TxHash: {receipt.transactionHash.hex()}"
        )

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
        current_model_state_ref = get_current_reference_model_state_cid()
        current_dpodl_checkpoint_ref = get_current_reference_dpodl_checkpoint_cid()
        print(f"Current Reference Model State CID: {current_model_state_ref}")
        print(f"Current Reference DPoDL Checkpoint CID: {current_dpodl_checkpoint_ref}")

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
             # block_receipt = submit_block(
             #     dummy_cid, # This was single ipfsCID, now needs model_state_cid and dpodl_checkpoint_cid
             #     dummy_acc, 
             #     dummy_steps, 
             #     dummy_post_hash, 
             #     dummy_ref, # This was single reference_cid, now needs reference_dpodl_checkpoint_cid
             #     test_private_key
             # )
             # if block_receipt:
             #      print(f"  Block submission SUCCESS! Tx Hash: {block_receipt.transactionHash.hex()}")
             #      # Update reference for potential MTX test
             #      dummy_ref = dummy_cid 
             # else:
             #      print("  Block submission FAILED.")
             
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