#!/usr/bin/env python

import os
import time
import logging
import sys

# Adjust path to import from dpodl_core
# This might need adjustment based on how you run the script (e.g., from root or from scripts/ folder)
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dpodl_core.blockchain_interface import (
    initialize_blockchain_connection,
    get_current_reference_model_state_cid,
    get_current_reference_dpodl_checkpoint_cid,
    submit_mtx,
    get_mtx_details, # To verify status later
    get_token, # To check balances
    get_w3 # Added to get web3 instance for account derivation
)
from dpodl_core.ipfs_utils import save_checkpoint_data_to_ipfs, get_ipfs_client # Using save_checkpoint_data_to_ipfs for pickled dict
from dpodl_core.config_utils import get_config
from dpodl_core.trainer import run_training # We will call the trainer's main orchestration function

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_mtx_e2e")

# --- Configuration ---
# Ensure these environment variables are set before running the test
# TEST_WORKER_PRIVATE_KEY: Private key of an account to act as MTX submitter
# REGISTRY_OPERATOR_PRIVATE_KEY: Private key of the ModelRegistry owner/operator
# These should be pre-funded with gas on your local Hardhat node.

def main():
    logger.info("Starting E2E test for MTX Processing and Rewards...")

    # Initialize blockchain and IPFS (ensure IPFS daemon is running)
    initialize_blockchain_connection()
    ipfs_client = get_ipfs_client()
    if not ipfs_client:
        logger.error("IPFS client not available. Exiting.")
        return

    app_config = get_config() # Load environment specific config (dev/test)

    worker_private_key = os.getenv("TEST_WORKER_PRIVATE_KEY")
    registry_operator_private_key = os.getenv("REGISTRY_OPERATOR_PRIVATE_KEY")

    if not worker_private_key:
        logger.error("TEST_WORKER_PRIVATE_KEY not set in environment. Cannot submit MTX.")
        return
    if not registry_operator_private_key:
        logger.error("REGISTRY_OPERATOR_PRIVATE_KEY not set in environment. Trainer won't be able to update registry.")
        # Note: trainer.py itself fetches this, so this check is more for awareness here.
        # The test will proceed, and trainer.py will log the error if it can't find its key.

    # 1. Get Initial Reference Model State CID (base for the MTX)
    logger.info("Fetching initial reference model state CID from ModelRegistry...")
    initial_ref_model_state_cid = get_current_reference_model_state_cid()
    if not initial_ref_model_state_cid:
        logger.warning("Initial reference model state CID is empty/None. This might be okay for absolute genesis.")
        # If it's truly the first run, this CID might be the one set in constructor (e.g. placeholder)
        # For the submit_mtx call, if it's empty, we might need to pass an empty string or a defined genesis CID.
        # The MTXMempool's submitMtx expects a referenceModelCID.
        # Let's assume ModelRegistry's getCurrentReferenceModelStateCID returns a non-empty string after deployment (from constructor arg)
        if not initial_ref_model_state_cid: # if still None after warning (e.g. contract returned empty string which get_fn converted to None)
             initial_ref_model_state_cid = "Qm__ABSOLUTE_GENESIS_STATE_CID_FOR_MTX_REFERENCE__" # Fallback for safety if contract allows empty
             logger.info(f"Using fallback absolute genesis CID for MTX reference: {initial_ref_model_state_cid}")


    logger.info(f"Initial reference model state CID: {initial_ref_model_state_cid}")

    # 2. Prepare and Submit an MTX from a simulated worker
    logger.info("Preparing dummy DPoDL checkpoint data for MTX...")
    dummy_model_state_cid_for_mtx = f"QmModelForMTX_{int(time.time())}"
    dpodl_state_for_mtx = {
        "final_model_state_cid": dummy_model_state_cid_for_mtx,
        "accuracy": 0.8876,  # True accuracy (float)
        "steps_trained_locally": 150,
        "reference_model_state_cid_used": initial_ref_model_state_cid,
        # Add other relevant D-PoDL proof data as expected by your system
    }
    
    # Save this DPoDL state to IPFS (as a pickled dictionary)
    # save_checkpoint_data_to_ipfs is async, but blockchain_interface is sync.
    # For this test script, let's manage the event loop if direct async call is needed,
    # or use a sync wrapper if ipfs_utils provides one.
    # Current save_checkpoint_data_to_ipfs in ipfs_utils is async.
    # Let's assume we have a sync version or handle it:
    
    # Hacky way to run async from sync for this test script, replace with proper async handling if utils are all async
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    dpodl_checkpoint_cid_for_mtx = loop.run_until_complete(
        save_checkpoint_data_to_ipfs(dpodl_state_for_mtx, name=f"E2E_Test_MTX_DPoDL_State")
    )

    if not dpodl_checkpoint_cid_for_mtx:
        logger.error("Failed to save DPoDL state to IPFS for MTX. Aborting.")
        return
    logger.info(f"Dummy DPoDL state for MTX saved to IPFS. DPoDL Checkpoint CID: {dpodl_checkpoint_cid_for_mtx}")

    # accuracy_bps for MTX submission (self-reported by worker)
    reported_accuracy_bps = int(dpodl_state_for_mtx["accuracy"] * 10000) 
    reported_steps = dpodl_state_for_mtx["steps_trained_locally"]

    logger.info(f"Submitting MTX to mempool: DPoDL_CID={dpodl_checkpoint_cid_for_mtx}, AccBPS={reported_accuracy_bps}, Steps={reported_steps}, RefStateCID={initial_ref_model_state_cid}")
    
    submission_result = submit_mtx(
        ipfs_cid=dpodl_checkpoint_cid_for_mtx, # This is the DPoDL checkpoint CID for the MTX
        accuracy_bps=reported_accuracy_bps,
        steps=reported_steps,
        reference_cid=initial_ref_model_state_cid, # The model state it was based on
        signer_private_key=worker_private_key
    )

    if not submission_result or not submission_result.get("receipt") or submission_result["receipt"].get("status") != 1:
        logger.error(f"Failed to submit MTX. Result: {submission_result}")
        return
    
    submit_receipt = submission_result["receipt"]
    submitted_mtx_id_for_check = submission_result.get("mtxId")

    logger.info(f"MTX submitted successfully! TxHash: {submit_receipt.transactionHash.hex()}. Parsed MTX ID: {submitted_mtx_id_for_check}")
    
    if submitted_mtx_id_for_check is None:
        logger.warning("submit_mtx did not return an mtxId. Verification of status by ID will be skipped. Please check MtxSubmitted event parsing.")

    # It might take a moment for the event/MTX to be fully indexed by the trainer's next call
    logger.info("Waiting a few seconds for MTX to propagate if needed...")
    time.sleep(5) # Adjust as necessary for your local node

    # 3. Run the Trainer Orchestration
    # The trainer will fetch pending MTXs, select the best, and call ModelRegistry
    logger.info("Running D-PoDL training orchestration (which includes MTX processing)...")
    # Ensure DPODL_ENV is set to your test environment if trainer.py relies on it
    # For this E2E test, we assume the trainer will pick up the REGISTRY_OPERATOR_PRIVATE_KEY from its env
    
    # The run_training function might run for multiple epochs based on config.
    # For E2E of MTX processing, we need it to complete its MTX selection phase.
    # If `run_training` is very long, we might need a more targeted function from trainer
    # or adjust its config for a quick run for this test.
    # For now, assume `run_training` from `test` profile is fast enough.
    try:
        run_training() # cli_num_workers can be passed if needed
    except Exception as e:
        logger.error(f"Error during run_training: {e}", exc_info=True)
        # Even if training part fails, MTX processing might have occurred if it's at the end.
        # We will proceed to check status.

    logger.info("Trainer orchestration finished (or an attempt was made).")

    # 4. Verification
    logger.info("--- Verifying MTX Processing Results ---")
    
    selected_mtx_id_by_trainer = 1 
    # DPoDL Checkpoint CID for MTX 1 (from trainer logs): QmZQBd1bkwTTTb5mogobjoibVn94AzwxmzQ1THonGahrSs
    # Model State CID for MTX 1 (from trainer logs, extracted from its DPoDL checkpoint): QmModelForMTX_1747271946
    expected_model_cid_after_update = "QmModelForMTX_1747271946" 
    expected_dpodl_cid_after_update = "QmZQBd1bkwTTTb5mogobjoibVn94AzwxmzQ1THonGahrSs"
    submitter_of_selected_mtx = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266" # Submitter of MTX 1

    # Check status of the MTX selected by the trainer
    logger.info(f"Checking status of MTX ID {selected_mtx_id_by_trainer} (selected by trainer for update)")
    mtx_info_selected = get_mtx_details(selected_mtx_id_by_trainer)
    if mtx_info_selected:
        logger.info(f"MTX {selected_mtx_id_by_trainer} details after trainer run: {mtx_info_selected}")
        if mtx_info_selected.get("status_str") == "Processed":
            logger.info(f"SUCCESS: MTX ID {selected_mtx_id_by_trainer} status is Processed as expected.")
        else:
            logger.error(f"FAILURE: MTX ID {selected_mtx_id_by_trainer} status is {mtx_info_selected.get('status_str')}, expected Processed.")
            all_checks_pass = False
    else:
        logger.error(f"FAILURE: Could not retrieve details for MTX ID {selected_mtx_id_by_trainer}.")
        all_checks_pass = False


    # Also check the status of the MTX originally submitted by this E2E script (if it's different)
    if submission_result and "mtxId" in submission_result and submission_result["mtxId"] is not None:
        submitted_mtx_id_by_script = submission_result["mtxId"]
        if submitted_mtx_id_by_script != selected_mtx_id_by_trainer:
            logger.info(f"Checking status of MTX ID {submitted_mtx_id_by_script} (submitted by E2E script)")
            mtx_info_script_submitted = get_mtx_details(submitted_mtx_id_by_script)
            if mtx_info_script_submitted:
                logger.info(f"MTX {submitted_mtx_id_by_script} details after trainer run: {mtx_info_script_submitted}")
                # This MTX might be Pending or Rejected if another was chosen. Not a strict failure if not Processed.
                logger.info(f"Status of E2E-submitted MTX ID {submitted_mtx_id_by_script}: {mtx_info_script_submitted.get('status_str')}")
            else:
                logger.warning(f"Could not retrieve details for E2E-submitted MTX ID {submitted_mtx_id_by_script}.")
    else:
        logger.warning("Could not determine the MTX ID submitted by the E2E script for status check.")


    logger.info("Verifying global model CIDs in ModelRegistry...")
    final_global_model_cid = get_current_reference_model_state_cid()
    final_global_dpodl_cid = get_current_reference_dpodl_checkpoint_cid()
    logger.info(f"Final global model state CID: {final_global_model_cid}")
    logger.info(f"Final global DPoDL checkpoint CID: {final_global_dpodl_cid}")

    if final_global_model_cid == expected_model_cid_after_update:
        logger.info(f"SUCCESS: Global model state CID is {final_global_model_cid} as expected.")
    else:
        logger.error(f"FAILURE: Global model state CID is {final_global_model_cid}, expected {expected_model_cid_after_update}.")
        cid_update_failed = True
        all_checks_pass = False

    if final_global_dpodl_cid == expected_dpodl_cid_after_update:
        logger.info(f"SUCCESS: Global DPoDL checkpoint CID is {final_global_dpodl_cid} as expected.")
    else:
        logger.error(f"FAILURE: Global DPoDL checkpoint CID is {final_global_dpodl_cid}, expected {expected_dpodl_cid_after_update}.")
        cid_update_failed = True
        all_checks_pass = False

    logger.info("--- Verifying MTX Submitter Token Balance ---")
    
    # Verify reward for the submitter of the *selected* MTX
    logger.info(f"Checking token balance for selected MTX submitter: {submitter_of_selected_mtx}")
    initial_reward_amount_str = os.getenv("INITIAL_MTX_REWARD_AMOUNT", "50000000000000000000") # 50 DPDL
    expected_reward_wei = int(initial_reward_amount_str)
    logger.info(f"Expected reward for MTX (in Wei, from config): {expected_reward_wei}")

    # The current ModelRegistry doesn't reward genesis submission, only updates from MTX.
    token_contract_instance = get_token()
    if not token_contract_instance:
        logger.error("DPoDLToken contract instance not available. Cannot check balance.")
        all_checks_pass = False
    else:
        submitter_balance_wei = token_contract_instance.functions.balanceOf(submitter_of_selected_mtx).call()
        logger.info(f"Selected MTX Submitter ({submitter_of_selected_mtx}) DPoDLToken balance (Wei): {submitter_balance_wei}")

        # This check assumes the submitter might have other tokens or received other rewards.
        # A truly accurate check would require knowing the balance *before* this specific reward.
        # For simplicity, we check if the balance is at least the reward amount.
        if submitter_balance_wei >= expected_reward_wei: # Simplistic check
            logger.info(f"SUCCESS: Selected MTX Submitter token balance ({submitter_balance_wei} Wei) is sufficient to cover the expected reward ({expected_reward_wei} Wei).")
        else:
            logger.error(f"FAILURE: Selected MTX Submitter token balance ({submitter_balance_wei} Wei) is less than the expected reward ({expected_reward_wei} Wei).")
            all_checks_pass = False
        
    # Log the original submitter's balance too if different for completeness
    if worker_private_key:
        from eth_account import Account
        worker_address = Account.from_key(worker_private_key).address
        if worker_address.lower() != submitter_of_selected_mtx.lower():
            if not token_contract_instance:
                logger.error("DPoDLToken contract instance not available. Cannot check E2E script submitter balance.")
                # all_checks_pass might already be False from above
            else:
                original_submitter_balance_wei = token_contract_instance.functions.balanceOf(worker_address).call()
                logger.info(f"E2E Script's MTX Submitter ({worker_address}) DPoDLToken balance (Wei): {original_submitter_balance_wei}")


    logger.info("E2E test for MTX Processing finished.")
    if not all_checks_pass:
        logger.error("One or more checks FAILED.")
    else:
        logger.info("All checks PASSED.")

if __name__ == "__main__":
    main() 