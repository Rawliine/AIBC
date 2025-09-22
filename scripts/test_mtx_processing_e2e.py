#!/usr/bin/env python

import os
import time
import logging
import sys
from web3 import Web3 # Added for direct Web3 usage if any

# Adjust path to import from dpodl_core
# This might need adjustment based on how you run the script (e.g., from root or from scripts/ folder)
sys.path.append(os.path.join(os.path.dirname(__file__), '..')) # Restoring this line

from dpodl_core.blockchain_interface import (
    initialize_blockchain_connection,
    get_current_reference_model_state_cid,
    get_current_reference_dpodl_checkpoint_cid,
    submit_mtx,
    get_mtx_details, # To verify status later
    get_token, # To check balances, and now to get the contract instance
    get_w3, # Changed from get_web3_instance
    update_mtx_status,
    update_reference_model_from_mtx,
    get_model_registry_mempool_address,
    fetch_pending_mtxs, # Changed from get_all_pending_mtxs to actual function name
)
from dpodl_core.ipfs_utils import (
    get_ipfs_client, # Added this import
    save_model_state_to_ipfs, 
    save_checkpoint_data_to_ipfs, # Changed from save_pickled_dict_to_ipfs
    load_pickled_dict_from_ipfs, load_model_state_from_ipfs
)
from dpodl_core.config_utils import get_config # Keep get_config
from dpodl_core.trainer import run_training # We will call the trainer's main orchestration function
from dpodl_core.utils import get_logger, setup_main_file_logging, restore_original_streams # Removed load_config
from dpodl_core.blockchain_config import PinataConfig, get_contract_info # Import get_contract_info

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_mtx_e2e")

# --- Configuration ---
# Ensure these environment variables are set before running the test
# TEST_WORKER_PRIVATE_KEY: Private key of an account to act as MTX submitter
# REGISTRY_OPERATOR_PRIVATE_KEY: Private key of the ModelRegistry owner/operator
# These should be pre-funded with gas on your local Hardhat node.

# Configure basic logging for the script itself
# This logger will write to the console as usual, unless setup_main_file_logging is called
script_logger = get_logger(__name__) # Module-specific logger

# --- Configuration & Setup ---
CONFIG = get_config() # Use get_config from config_utils

# Fetch contract addresses using get_contract_info
mempool_address, _ = get_contract_info("MTXMempool")
registry_address, _ = get_contract_info("ModelRegistry")
token_address, _ = get_contract_info("DPoDLToken")

if not mempool_address or not registry_address or not token_address:
    script_logger.error("Failed to retrieve one or more contract addresses. Exiting.")
    # Consider exiting more gracefully or raising an exception
    sys.exit(1) # Exit if critical configuration is missing

MTX_MEMPOOL_CONTRACT_ADDRESS = mempool_address
MODEL_REGISTRY_CONTRACT_ADDRESS = registry_address
DPODL_TOKEN_CONTRACT_ADDRESS = token_address

REGISTRY_OPERATOR_PRIVATE_KEY = os.getenv("REGISTRY_OPERATOR_PRIVATE_KEY")
if not REGISTRY_OPERATOR_PRIVATE_KEY:
    script_logger.warning("REGISTRY_OPERATOR_PRIVATE_KEY is not set in .env. Registry updates will fail.")

# Account that will submit the MTX (e.g., a worker)
# Use one of the worker keys for testing submission
SUBMITTER_PRIVATE_KEY = os.getenv("WORKER_PRIVATE_KEY_0", "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80") 
SUBMITTER_ADDRESS = Web3().eth.account.from_key(SUBMITTER_PRIVATE_KEY).address

# Account that will be rewarded (can be same as submitter or different)
REWARD_ADDRESS = SUBMITTER_ADDRESS 

async def create_dummy_dpodl_checkpoint_and_upload(steps_completed=100, accuracy_val=0.75):
    """Creates a dummy D-PoDL checkpoint dict and uploads its components to IPFS."""
    script_logger.info("Creating and uploading dummy D-PoDL checkpoint to IPFS...")
    
    # 1. Dummy Model State (e.g., a simple dictionary)
    dummy_model_state = {"layer1.weights": [0.1, 0.2], "epoch": 1, "architecture": "dummy_transformer_small"}
    # save_model_state_to_ipfs is also async, so it needs to be awaited
    model_state_cid = await save_model_state_to_ipfs(dummy_model_state, model_name="dummy_model_state_for_mtx")
    if not model_state_cid:
        script_logger.error("Failed to upload dummy model state to IPFS.")
        return None, None
    script_logger.info(f"Dummy model state uploaded to IPFS. CID: {model_state_cid}")

    # 2. Dummy D-PoDL State (dictionary with proofs, hashes, etc.)
    dummy_dpodl_state = {
        "prev_block_hash": "0x" + "a"*64,
        "nonce": 12345,
        "pre_hash_value": "0x" + "b"*64,
        "reference_model_id": "QmReferenceModelStateCIDPreviouslyUsedByWorker", # Could be None if from genesis
        "random_seed": 78910,
        "seed_for_weights": 78910, # Often same as random_seed or derived
        "t1_threshold": CONFIG["t1_threshold"], 
        "t2_threshold": CONFIG["t2_threshold"],
        "accuracy": accuracy_val, # This is the crucial field for selection!
        "t_acc_threshold": CONFIG["t_acc_threshold"],
        "final_model_state_hash": "0x" + "c"*64, # Hash of the model state
        "final_model_state_cid": model_state_cid, # CID of the actual model state (weights, etc.) <--- IMPORTANT FOR REGISTRY
        "post_hash_value": "0x" + "d"*64,
        "steps_at_checkpoint": steps_completed,
        "merkle_root": "0x" + "e"*64,
        "checkpoint_hashes": ["0x"+"f"*10 for _ in range(5)], # List of intermediate hashes
        "trace_hash": "0x" + "g"*64,
        "trace_file_path": "/tmp/dummy_trace.jsonl" # Path on worker, not directly used by blockchain
    }
    # Use the correct function name and await it
    dpodl_checkpoint_cid = await save_checkpoint_data_to_ipfs(dummy_dpodl_state, name="dummy_dpodl_chkpt_for_mtx")
    if not dpodl_checkpoint_cid:
        script_logger.error("Failed to upload dummy D-PoDL checkpoint state to IPFS.")
        return None, None # Or handle error appropriately
    script_logger.info(f"Dummy D-PoDL checkpoint state uploaded to IPFS. CID: {dpodl_checkpoint_cid}")

    return model_state_cid, dpodl_checkpoint_cid

async def main(): # Make main async
    # Setup file logging for stdout/stderr at the very beginning
    setup_main_file_logging(log_file_name="test_mtx_processing_e2e.log", logs_dir="logs/e2e_test_runs")
    script_logger.info("======== STARTING E2E MTX PROCESSING TEST ========")
    
    try:
        script_logger.info("Connecting to blockchain and IPFS...")
        # The blockchain_interface module initializes connection on import.
        # We just need to get the w3 instance.
        web3_instance = get_w3() 
        ipfs_client = get_ipfs_client() # Ensure get_ipfs_client is imported
        
        if not web3_instance or not web3_instance.is_connected():
            script_logger.error("Failed to connect to blockchain or get Web3 instance. Exiting test.")
            # Ensure ipfs_client is also checked if it can be None or has a similar check
            if not ipfs_client: # This is fine as a secondary log if web3 fails anyway
                 script_logger.error("IPFS client also appears to be unavailable.")
            return
        
        if not ipfs_client: # Explicitly check if ipfs_client failed to initialize
            script_logger.error("Failed to get IPFS client. Exiting test.")
            return # This return should be INSIDE the if block
            
        script_logger.info("Successfully connected to blockchain and IPFS.")

        # Contracts are loaded by initialize_blockchain_connection() within the blockchain_interface module.
        # So, no explicit load_contracts() call is needed here.
        # load_contracts(web3_instance) # Removed this line

        script_logger.info("Smart contracts should be loaded automatically by blockchain_interface.")
        script_logger.info(f"  MTXMempool Contract Address: {MTX_MEMPOOL_CONTRACT_ADDRESS}")
        script_logger.info(f"  ModelRegistry Contract Address: {MODEL_REGISTRY_CONTRACT_ADDRESS}")
        script_logger.info(f"  DPoDLToken Contract Address: {DPODL_TOKEN_CONTRACT_ADDRESS}")
        script_logger.info(f"  Submitter (Worker) Address: {SUBMITTER_ADDRESS}")
        script_logger.info(f"  Reward Address: {REWARD_ADDRESS}")
        script_logger.info(f"  Pinata Pinning Enabled: {PinataConfig.ENABLE_PINNING}")

        script_logger.info("--- Step 1: Simulating Worker MTX Submission ---")
        # Await the async function call
        _dummy_model_cid_low_acc, dpodl_cid_low_acc = await create_dummy_dpodl_checkpoint_and_upload(steps_completed=100, accuracy_val=0.70)
        _dummy_model_cid_high_acc, dpodl_cid_high_acc = await create_dummy_dpodl_checkpoint_and_upload(steps_completed=120, accuracy_val=0.85)
        
        if not dpodl_cid_low_acc or not dpodl_cid_high_acc:
            script_logger.error("Failed to create and upload one or both dummy D-PoDL checkpoints. Exiting.")
            return

        ref_model_cid_for_mtx = get_current_reference_model_state_cid()
        if not ref_model_cid_for_mtx:
            ref_model_cid_for_mtx = "Qm__GENESIS_OR_SOME_PREVIOUS_MODEL_STATE__"
            script_logger.info(f"ModelRegistry is at genesis or empty. Using placeholder reference model CID for MTX: {ref_model_cid_for_mtx}")
        else:
            script_logger.info(f"Using reference model CID from ModelRegistry for MTX: {ref_model_cid_for_mtx}")

        script_logger.info(f"Submitting MTX with low accuracy (0.70) and DPoDL CID: {dpodl_cid_low_acc}")
        tx_receipt_low = submit_mtx(
            ipfs_cid=dpodl_cid_low_acc,
            accuracy_bps=7000,
            steps=100,
            reference_cid=ref_model_cid_for_mtx,
            signer_private_key=SUBMITTER_PRIVATE_KEY
        )
        if tx_receipt_low and tx_receipt_low.get("status") == 1 and tx_receipt_low.get("mtxId") is not None:
            mtx_id_low = tx_receipt_low["mtxId"]
            script_logger.info(f"Low accuracy MTX submitted successfully! MTX ID: {mtx_id_low}, TxHash: {tx_receipt_low['tx_hash']}")
        else:
            script_logger.error(f"Failed to submit low accuracy MTX or parse ID. Receipt: {tx_receipt_low}")
            return # Exit if the first MTX submission fails
    
        script_logger.info(f"Submitting MTX with high accuracy (0.85) and DPoDL CID: {dpodl_cid_high_acc}")
        tx_receipt_high = submit_mtx(
            ipfs_cid=dpodl_cid_high_acc,
            accuracy_bps=8500,
            steps=120,
            reference_cid=ref_model_cid_for_mtx,
            signer_private_key=SUBMITTER_PRIVATE_KEY
        )
        if tx_receipt_high and tx_receipt_high.get("status") == 1 and tx_receipt_high.get("mtxId") is not None:
            mtx_id_high = tx_receipt_high["mtxId"]
            script_logger.info(f"High accuracy MTX submitted successfully! MTX ID: {mtx_id_high}, TxHash: {tx_receipt_high['tx_hash']}")
        else:
            script_logger.error(f"Failed to submit high accuracy MTX or parse ID. Receipt: {tx_receipt_high}")
            return # Exit if the second MTX submission fails
        
        script_logger.info("Waiting a bit for blockchain state to settle...")
        time.sleep(3)

        # Store details of the MTXs we expect the trainer to process
        expected_high_acc_mtx_id = mtx_id_high
        expected_high_acc_dpodl_cid = dpodl_cid_high_acc
        # This is the CID of the model state *within* the DPoDL checkpoint
        expected_high_acc_model_state_cid_in_dpodl = _dummy_model_cid_high_acc 
        
        script_logger.info(f"--- Expected MTX to be processed by trainer: ID {expected_high_acc_mtx_id}, DPoDL CID {expected_high_acc_dpodl_cid}, Inner Model CID {expected_high_acc_model_state_cid_in_dpodl} ---")

        # --- Step 2: Call Trainer's run_training to orchestrate MTX processing ---
        script_logger.info("Calling dpodl_core.trainer.run_training() to process submitted MTXs...")
        
        # Get token balance BEFORE trainer run (for reward check)
        token_contract_instance = get_token()
        balance_before_trainer_run = 0
        if token_contract_instance:
            try:
                balance_before_trainer_run = token_contract_instance.functions.balanceOf(REWARD_ADDRESS).call()
                script_logger.info(f"DPDL Token balance of reward address ({REWARD_ADDRESS}) BEFORE trainer run: {Web3.from_wei(balance_before_trainer_run, 'ether')} DPDL")
            except Exception as e_balance_before:
                script_logger.error(f"Error fetching token balance before trainer run for {REWARD_ADDRESS}: {e_balance_before}")
                token_contract_instance = None # Invalidate if error occurs

        # Ensure REGISTRY_OPERATOR_PRIVATE_KEY is available for the trainer, as it will need it
        if not REGISTRY_OPERATOR_PRIVATE_KEY:
            script_logger.warning("REGISTRY_OPERATOR_PRIVATE_KEY is not set. The trainer (run_training) might fail to update ModelRegistry or MTX status.")
        
        # The trainer's run_training function will:
        # 1. Fetch pending MTXs (including those we just submitted).
        # 2. Evaluate them (load their DPoDL state from IPFS).
        # 3. Select the best one (should be our high_accuracy_mtx).
        # 4. Update its status to SelectedForProcessing.
        # 5. Update the ModelRegistry with its details, rewarding the submitter.
        try:
            run_training() # No cli_num_workers override, will use config
            script_logger.info("dpodl_core.trainer.run_training() completed.")
        except Exception as e_trainer:
            script_logger.error(f"Error during dpodl_core.trainer.run_training(): {e_trainer}", exc_info=True)
            # We might still want to try and verify some states if the trainer partially ran
            # or just exit if it's a critical failure. For now, we'll proceed to verification.

        script_logger.info("--- Step 3: Verification after Trainer's Orchestration ---")

        # 1. Verify Status of the Expected High Accuracy MTX
        script_logger.info(f"Verifying status of the expected high-accuracy MTX (ID: {expected_high_acc_mtx_id})...")
        mtx_details_after_trainer = get_mtx_details(expected_high_acc_mtx_id)
        if mtx_details_after_trainer:
            script_logger.info(f"  MTX ID {expected_high_acc_mtx_id} details post-trainer: {mtx_details_after_trainer}")
            if mtx_details_after_trainer.get("status_str") == "Processed":
                script_logger.info(f"  SUCCESS: MTX ID {expected_high_acc_mtx_id} status is 'Processed'.")
            else:
                script_logger.error(f"  FAILURE: MTX ID {expected_high_acc_mtx_id} status is '{mtx_details_after_trainer.get('status_str')}', expected 'Processed'.")
        else:
            script_logger.error(f"  FAILURE: Could not fetch details for MTX ID {expected_high_acc_mtx_id} after trainer run.")

        # 2. Verify ModelRegistry CIDs
        script_logger.info("Verifying CIDs in ModelRegistry...")
        final_global_model_cid = get_current_reference_model_state_cid()
        final_global_dpodl_cid = get_current_reference_dpodl_checkpoint_cid()
        script_logger.info(f"  ModelRegistry - Final Model State CID: {final_global_model_cid}")
        script_logger.info(f"  ModelRegistry - Final DPoDL Checkpoint CID: {final_global_dpodl_cid}")

        if final_global_model_cid == expected_high_acc_model_state_cid_in_dpodl:
            script_logger.info(f"  SUCCESS: ModelRegistry Model State CID matches expected: {expected_high_acc_model_state_cid_in_dpodl}.")
        else:
            script_logger.error(f"  FAILURE: ModelRegistry Model State CID is {final_global_model_cid}, expected {expected_high_acc_model_state_cid_in_dpodl}.")
        
        if final_global_dpodl_cid == expected_high_acc_dpodl_cid:
            script_logger.info(f"  SUCCESS: ModelRegistry DPoDL Checkpoint CID matches expected: {expected_high_acc_dpodl_cid}.")
        else:
            script_logger.error(f"  FAILURE: ModelRegistry DPoDL Checkpoint CID is {final_global_dpodl_cid}, expected {expected_high_acc_dpodl_cid}.")

        # 3. Verify Token Reward
        if token_contract_instance: # Only check if instance was valid
            script_logger.info(f"Verifying token reward for submitter ({REWARD_ADDRESS})...")
            balance_after_trainer_run = token_contract_instance.functions.balanceOf(REWARD_ADDRESS).call()
            script_logger.info(f"  DPDL Token balance of reward address ({REWARD_ADDRESS}) AFTER trainer run: {Web3.from_wei(balance_after_trainer_run, 'ether')} DPDL")
            
            # The exact reward amount might come from ModelRegistry's `initialMtxRewardAmount`
            # For now, just check if balance increased.
            if balance_after_trainer_run > balance_before_trainer_run:
                increase_amount = Web3.from_wei(balance_after_trainer_run - balance_before_trainer_run, 'ether')
                script_logger.info(f"  SUCCESS: Reward address received tokens! Balance increased by {increase_amount} DPDL.")
            else:
                script_logger.error(f"  FAILURE: Reward address balance did not increase. Before: {Web3.from_wei(balance_before_trainer_run, 'ether')}, After: {Web3.from_wei(balance_after_trainer_run, 'ether')}.")
        else:
            script_logger.warning("Skipping token reward verification as DPoDLToken contract instance was not available or failed earlier.")

        # Verification for the low-accuracy MTX (optional, should ideally be 'Pending' or 'Rejected' by trainer logic if not selected)
        if 'mtx_id_low' in locals():
            script_logger.info(f"Verifying status of the low-accuracy MTX (ID: {mtx_id_low})...")
            low_mtx_details_after_trainer = get_mtx_details(mtx_id_low)
            if low_mtx_details_after_trainer:
                status_str = low_mtx_details_after_trainer.get('status_str', 'Unknown')
                script_logger.info(f"  Low-accuracy MTX ID {mtx_id_low} status post-trainer: {status_str}")
                # Trainer *might* mark it as Rejected, or leave it Pending if only one MTX is processed per run.
                # This check might need refinement based on trainer's exact logic for non-selected MTXs.
                if status_str == "Pending" or status_str == "Rejected":
                     script_logger.info(f"  INFO: Low-accuracy MTX ID {mtx_id_low} has an expected status ({status_str}).")
                else:
                     script_logger.warning(f"  WARNING: Low-accuracy MTX ID {mtx_id_low} has status '{status_str}'. This might be okay or indicate an issue depending on trainer's non-selection logic.")
            else:
                script_logger.warning(f"  Could not fetch details for low-accuracy MTX ID {mtx_id_low} after trainer run.")

        script_logger.info("======== E2E MTX PROCESSING TEST COMPLETED (Trainer-Driven) ========")

    except Exception as e:
        script_logger.error(f"An uncaught error occurred during the E2E test: {e}", exc_info=True)
    finally:
        # Restore original stdout and stderr before exiting
        restore_original_streams()
        script_logger.info("Restored original stdout/stderr streams. E2E test script finished.")

if __name__ == "__main__":
    import asyncio # Import asyncio here
    asyncio.run(main()) # Run the async main function 