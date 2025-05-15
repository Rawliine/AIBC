import os
import time
import ray
import torch
import logging
import argparse
import traceback

# Ray AIR / train
from ray.train.torch import TorchTrainer
from ray.air.config import ScalingConfig, RunConfig
from ray.train import Checkpoint, FailureConfig

# Import components from within the package
from .data_loader import load_dataset_and_partition
from .worker import worker_train_loop  # Import the worker loop
from .utils import logger # Import logger if configured globally
# Import the blockchain interface functions
from . import blockchain_interface
from .blockchain_interface import (
    get_current_reference_model_state_cid, 
    get_current_reference_dpodl_checkpoint_cid,
    fetch_pending_mtxs,
    update_reference_model_from_mtx, # Added for MTX processing
    # Add the new debug function import here if it makes sense, or call it directly
    # For now, assume it will be added to blockchain_interface and called
)
from .config_utils import get_config # Import the new config utility
from .ipfs_utils import load_pickled_dict_from_ipfs # Added for MTX processing

# Configure logging if not already done globally
# logging.basicConfig(level=logging.INFO) 
# logger = logging.getLogger("dpodl_trainer")

# --- Simulated Mempool for Model Transactions (MTX) ---
# global mtx_mempool # This was a placeholder, actual MTXs are on-chain
# mtx_mempool = [] 

# def select_best_mtx(mempool):
# """Selects the 'best' mtx from the mempool (e.g., highest accuracy)."""
# if not mempool:
# return None
# # Simple selection: highest accuracy. Could be more complex (steps, lineage, etc.)
# best_mtx = max(mempool, key=lambda x: x.get('accuracy', 0.0))
# logger.info(f"Selected best mtx from mempool: CID {best_mtx.get('ipfs_cid')}, Acc {best_mtx.get('accuracy'):.4f}")
# return best_mtx
# ------------------------------------------------------

def run_training(
    # num_workers: int = 1, # Now fetched from config
    # epochs: int = 5, # Now fetched from config
    # batch_size: int = 128, # Now fetched from config
    # seq_len: int = 128, # Now fetched from config
    # embed_dim: int = 256, # Now fetched from config
    # num_heads: int = 8, # Now fetched from config
    # num_layers: int = 6, # Now fetched from config
    # checkpoint_path: str = "checkpoint_deeper.pt", # Now fetched from config
    # # Add D-PoDL parameters with defaults
    # prev_block_hash: str = "0x0000000000000000", # Placeholder # Now fetched from config
    # t1_threshold: int = 2**240, # Placeholder High Threshold (easy) # Now fetched from config
    # t2_threshold: int = 2**256, # Placeholder Max Threshold (easy) # Now fetched from config
    # t_acc_threshold: float = 0.95, # Add Target Accuracy Threshold # Now fetched from config
    # reference_model_id: str = None # Placeholder # Now fetched from config
    cli_num_workers: int = None # Allow CLI override for num_workers
):
    """
    Orchestrates the distributed D-PoDL training using Ray Train.
    - Initializes Ray.
    - Loads and partitions dataset.
    - Sets up configuration for workers, including D-PoDL params.
    - Creates and runs the Ray TorchTrainer.
    """
    logger.info("Starting D-PoDL training orchestration...")
    
    # --- Load Configuration ---
    app_config = get_config()
    num_workers = cli_num_workers if cli_num_workers is not None else app_config.get("num_workers", 2) # Default to 2 if not in config
    # --- Ray Initialization --- 
    if not ray.is_initialized():
        logger.info("Initializing Ray...")
        ray.init(address="auto" if os.environ.get("RAY_ADDRESS") else None, 
                 ignore_reinit_error=True, 
                 include_dashboard=True,
                 logging_level=logging.INFO, # Set Ray logging level
                 _metrics_export_port=8081 
                )
        logger.info("Ray initialized.")
    else:
        logger.info("Ray already initialized.")

    # --- Data Loading --- 
    logger.info("Loading and partitioning dataset...")
    # Load both train and validation partitions
    data_loaded = load_dataset_and_partition(
        dataset_name=app_config["dataset_name"],
        num_workers=num_workers, 
        batch_size=app_config["batch_size"],
        dataset_path_override=app_config.get("dataset_path"),
        num_train_samples=app_config.get("num_train_samples"),
        num_val_samples=app_config.get("num_val_samples")
    ) 
    train_partitions = data_loaded["train_partitions"]
    val_partition = data_loaded["val_dataset"] # Assuming val_dataset is suitable for all workers
    logger.info(f"Dataset loaded. Train partitions: {len(train_partitions)}, Val dataset: {val_partition}")

    # --- Determine Reference Model CIDs for this run --- 
    # These are the CIDs that workers will base their training on.
    
    # Try to get reference model state CID override from config first (for testing)
    current_ref_model_state_cid_for_run = app_config.get("reference_model_id_override") # Assuming this key means model_state_cid override
    current_ref_dpodl_checkpoint_cid_for_run = app_config.get("reference_dpodl_checkpoint_cid_override") # New override for DPoDL checkpoint

    if current_ref_model_state_cid_for_run is not None:
        logger.info(f"Using overridden reference_model_state_cid from config: {current_ref_model_state_cid_for_run}")
        if current_ref_dpodl_checkpoint_cid_for_run is None:
            logger.warning("reference_model_id_override is set, but reference_dpodl_checkpoint_cid_override is not. DPoDL checkpoint CID will be None.")
    else:
        logger.info("No reference_model_id_override in config. Querying blockchain registry...")
        current_ref_model_state_cid_for_run = get_current_reference_model_state_cid()
        current_ref_dpodl_checkpoint_cid_for_run = get_current_reference_dpodl_checkpoint_cid()

        if not current_ref_model_state_cid_for_run:
            logger.warning("Failed to get reference model state CID from registry or registry is at genesis (empty state CID). Starting fresh or from absolute genesis.")
            # current_ref_model_state_cid_for_run will be None or empty string from contract
        else:
            logger.info(f"Using current reference model state CID from registry: {current_ref_model_state_cid_for_run}")
        
        if not current_ref_dpodl_checkpoint_cid_for_run:
            logger.info("Current reference DPoDL checkpoint CID from registry is None/empty.")
        else:
            logger.info(f"Using current reference DPoDL checkpoint CID from registry: {current_ref_dpodl_checkpoint_cid_for_run}")
    
    # Ensure workers get None if CIDs are empty strings from contract for clarity
    if isinstance(current_ref_model_state_cid_for_run, str) and not current_ref_model_state_cid_for_run:
        current_ref_model_state_cid_for_run = None
    if isinstance(current_ref_dpodl_checkpoint_cid_for_run, str) and not current_ref_dpodl_checkpoint_cid_for_run:
        current_ref_dpodl_checkpoint_cid_for_run = None

    # --- Worker Configuration --- 
    train_loop_config = {
        # Data/Model params
        "train_partitions": train_partitions, 
        "val_partition": val_partition,     
        "seq_len": app_config["seq_len"],
        "batch_size": app_config["batch_size"],
        "epochs": app_config["epochs"],
        "lr": app_config["lr"],
        # Model architecture params - will be used if HtoA is not active or as fallback
        "embed_dim": app_config["embed_dim"], 
        "num_heads": app_config["num_heads"], 
        "num_layers": app_config["num_layers"], 
        "checkpoint_path": app_config["checkpoint_path"],
        # D-PoDL params
        "prev_block_hash": app_config["prev_block_hash"],
        "t1_threshold": app_config["t1_threshold"],
        "t2_threshold": app_config["t2_threshold"],
        "t_acc_threshold": app_config["t_acc_threshold"],
        "reference_model_state_cid": current_ref_model_state_cid_for_run, # NEW KEY for model weights
        "reference_dpodl_checkpoint_cid": current_ref_dpodl_checkpoint_cid_for_run, # NEW KEY for DPoDL proofs of reference
        "ipfs_enabled": app_config["ipfs_enabled"], # Pass IPFS enabled flag
        "model_override_params": app_config.get("model_override_params") # Pass model override
    }
    # logger.info(f"Worker config prepared: {train_loop_config}") # Logged later if needed

    # --- Ray Trainer Setup --- 
    scaling_config = ScalingConfig(
            num_workers=num_workers,
            use_gpu=torch.cuda.is_available(),
            resources_per_worker={"CPU": 0.25, "GPU": 0.25},
            # backend="gloo" # Consider Gloo for CPU or heterogeneous clusters
        )
    logger.info(f"Using ScalingConfig: {scaling_config}")

    run_config = RunConfig(
            name="DPoDL_Training_Run",
            storage_path=f"file://{os.path.abspath('ray_results')}",
            failure_config=FailureConfig(max_failures=2) # Allow up to 2 worker failures
        )
    logger.info(f"Using RunConfig: {run_config}")

    trainer = TorchTrainer(
        train_loop_per_worker=worker_train_loop, # Use the imported function
        train_loop_config=train_loop_config,
        scaling_config=scaling_config,
        run_config=run_config,
    )
    logger.info("TorchTrainer initialized.")

    # --- Execute Training --- 
    logger.info(f"Starting trainer.fit() with config: {train_loop_config}")
    result = trainer.fit()
    logger.info(f"Training finished.") # Basic log, details below

    # --- Process Results --- 
    logger.info("Processing results from workers...")
    block_candidates = []
    new_mtx_candidates = []

    # --- Process Metrics Dataframe for General Progress AND Submissions ---
    if result.metrics_dataframe is not None and not result.metrics_dataframe.empty:
        logger.info("Processing results from metrics_dataframe...")
        for index, report_data in result.metrics_dataframe.iterrows():
            worker_id_df = report_data.get("pid", report_data.get("hostname", f"worker_{report_data.get('trial_id', 'unknown')}"))

            # Check if this is a submission report
            if report_data.get("is_submission_report") == True:
                submission = {
                    "epoch": report_data.get("submission_epoch"),
                    "action_taken": report_data.get("submission_action"),
                    "model_cid": report_data.get("submission_model_cid"),
                    "tx_hash": report_data.get("submission_tx_hash"),
                    "accuracy": report_data.get("submission_accuracy"),
                    "total_steps_overall": report_data.get("submission_total_steps"),
                    "worker_rank": report_data.get("submission_worker_rank") # Changed from rank to worker_rank for consistency
                }
                logger.info(f"  Extracted SUBMISSION from metrics_dataframe (Worker {submission['worker_rank']}): {submission}")
                if submission["action_taken"] == "SAVE_BLOCK_CHECKPOINT":
                    block_candidates.append(submission)
                elif submission["action_taken"] == "SAVE_MTX_CHECKPOINT":
                    new_mtx_candidates.append(submission)
            else:
                # This is a regular end-of-epoch report, log general progress
                epoch_num_df = report_data.get("epoch")
                loss_df = report_data.get("loss")
                acc_df = report_data.get("accuracy")
                action_df = report_data.get("action_taken") # This is the general action from end of epoch
                
                # Format loss and accuracy strings safely
                loss_str = f"{loss_df:.4f}" if loss_df is not None else "N/A"
                acc_str = f"{acc_df:.4f}" if acc_df is not None else "N/A"
                action_str = action_df if action_df is not None else "N/A"

                if epoch_num_df is not None: # Ensure it's a valid epoch report
                    logger.info(f"  Metrics DF (End of Epoch) - Worker [{worker_id_df}] Epoch [{epoch_num_df}]: Loss={loss_str}, Acc={acc_str}, Action={action_str}")
    else:
        logger.warning("No metrics dataframe found or it is empty.")

    # Log findings from actual submissions (now populated from metrics_dataframe)
    if block_candidates:
        logger.info(f"Found {len(block_candidates)} actual block candidates from worker reports:")
        for bc in block_candidates:
            logger.info(f"  - ModelCID: {bc['model_cid']}, TxHash: {bc['tx_hash']}, Accuracy: {bc['accuracy']:.4f}, Steps: {bc['total_steps_overall']}, Worker: {bc['worker_rank']}")
            # TODO: Add logic to select best block candidate and submit to blockchain
    else:
        logger.info("No actual block candidates reported by workers.")

    if new_mtx_candidates:
        logger.info(f"Found {len(new_mtx_candidates)} actual new MTX candidates from worker reports:")
        for mtx in new_mtx_candidates:
            logger.info(f"  - ModelCID: {mtx['model_cid']}, TxHash: {mtx['tx_hash']}, Accuracy: {mtx['accuracy']:.4f}, Steps: {mtx['total_steps_overall']}, Worker: {mtx['worker_rank']}")
            # Add to our simulated mempool (replace with actual mempool logic)
            # mtx_mempool.append(mtx) # Consider if mempool needs different structure
    else:
        logger.info("No actual new MTX candidates reported by workers.")
        
    # logger.info(f"Current MTX Mempool size: {len(mtx_mempool)}") # If using mtx_mempool
    # --- End Processing Results --- 

    # --- Process Pending MTXs from Blockchain Mempool (Phase 1, Step 2 & 3) ---
    logger.info("--- Starting MTX Mempool Processing (Off-Chain Selection & Update) ---")
    pending_mtxs_from_chain = fetch_pending_mtxs()
    
    evaluated_mtxs = []
    if not pending_mtxs_from_chain:
        logger.info("No pending MTXs found in the MTXMempool contract.")
    else:
        logger.info(f"Found {len(pending_mtxs_from_chain)} pending MTXs in contract. Evaluating...")
        for mtx_data in pending_mtxs_from_chain:
            logger.info(f"Processing MTX ID: {mtx_data['mtxId']}, Submitter: {mtx_data['submitter']}, Checkpoint CID: {mtx_data['ipfsCID']}")
            dpodl_state_checkpoint = load_pickled_dict_from_ipfs(mtx_data['ipfsCID'], name=f"MTX_{mtx_data['mtxId']}_DPoDL_State")
            if dpodl_state_checkpoint:
                accuracy = dpodl_state_checkpoint.get("accuracy") # This is the float accuracy 0.0 to 1.0
                if accuracy is not None:
                    evaluated_mtxs.append({
                        "mtxId": mtx_data['mtxId'],
                        "ipfsCID": mtx_data['ipfsCID'],
                        "submitter": mtx_data['submitter'],
                        "accuracy": accuracy, # Storing the float accuracy
                        "accuracyBPS_reported": mtx_data['accuracyBPS'], # Keep the originally reported one for comparison if needed
                        "steps": mtx_data['steps'],
                        "referenceModelCID": mtx_data['referenceModelCID']
                    })
                    logger.info(f"  Successfully evaluated MTX ID {mtx_data['mtxId']}. Fetched Accuracy: {accuracy:.4f}")
                else:
                    logger.warning(f"  Could not find 'accuracy' in DPoDL state for MTX ID {mtx_data['mtxId']}. Skipping.")
            else:
                logger.warning(f"  Failed to load DPoDL state from IPFS for MTX ID {mtx_data['mtxId']} (CID: {mtx_data['ipfsCID']}). Skipping.")

    if evaluated_mtxs:
        # Select best MTX (highest accuracy, then lowest mtxId for tie-breaking)
        evaluated_mtxs.sort(key=lambda x: (-x['accuracy'], x['mtxId'])) # Sort by accuracy DESC, then mtxId ASC
        best_mtx_candidate = evaluated_mtxs[0]
        logger.info(f"Selected BEST MTX candidate from mempool: ID {best_mtx_candidate['mtxId']}, Submitter: {best_mtx_candidate['submitter']}, DPoDL Checkpoint CID: {best_mtx_candidate['ipfsCID']}, True Accuracy: {best_mtx_candidate['accuracy']:.4f}")
        
        # Phase 1, Step 3: Call ModelRegistry.sol to update the reference model
        dpodl_checkpoint_cid_to_submit = best_mtx_candidate['ipfsCID']
        mtx_id_to_submit = best_mtx_candidate['mtxId']

        # Load the DPoDL state to get the actual model_state_cid submitted by the worker
        dpodl_state_data = load_pickled_dict_from_ipfs(dpodl_checkpoint_cid_to_submit, name=f"MTX_{mtx_id_to_submit}_DPoDL_State_for_submission")
        
        model_state_cid_to_submit = None
        if dpodl_state_data:
            # The key for model_state_cid depends on what worker.py saves it as.
            # Common keys might be: 'final_model_state_cid', 'model_state_cid', 'model_weights_cid'.
            # Let's assume 'final_model_state_cid' based on prior discussions on worker outputs.
            model_state_cid_to_submit = dpodl_state_data.get("final_model_state_cid") 
            if not model_state_cid_to_submit:
                # Fallback to other potential keys if the primary one is not found
                model_state_cid_to_submit = dpodl_state_data.get("model_state_cid")
            if not model_state_cid_to_submit:
                 model_state_cid_to_submit = dpodl_state_data.get("model_checkpoint_cid") # If worker used this generic key for model state
            
            if model_state_cid_to_submit:
                logger.info(f"Extracted Model State CID for submission: {model_state_cid_to_submit} from DPoDL Checkpoint {dpodl_checkpoint_cid_to_submit}")
                
                # --- DEBUGGING: Check mtxMempoolContract address in ModelRegistry ---
                # from . import blockchain_interface # Ensure module is loaded for direct call
                # try:
                #     logger.info("DEBUG: Querying ModelRegistry for its mtxMempoolContract address...")
                #     mempool_addr_in_registry = blockchain_interface.get_model_registry_mempool_address()
                #     logger.info(f"DEBUG: MTXMempool address set in ModelRegistry: {mempool_addr_in_registry}")
                # except Exception as e_debug_addr:
                #     logger.error(f"DEBUG: Error querying mtxMempoolContract address from ModelRegistry: {e_debug_addr}")
                # --- END DEBUGGING ---

                signer_private_key = os.getenv("REGISTRY_OPERATOR_PRIVATE_KEY")
                if not signer_private_key:
                    logger.error("REGISTRY_OPERATOR_PRIVATE_KEY not found in environment. Cannot submit MTX update to ModelRegistry.")
                else:
                    # --->>> NEW: Update MTX status to SelectedForProcessing <<<---
                    logger.info(f"Attempting to update status of MTX ID {mtx_id_to_submit} to 'SelectedForProcessing' (1) in MTXMempool...")
                    status_update_receipt = blockchain_interface.update_mtx_status(
                        mtx_id=mtx_id_to_submit,
                        status_code=1,  # 1 for MTXMempool.Status.SelectedForProcessing
                        signer_private_key=signer_private_key
                    )

                    if status_update_receipt and status_update_receipt.get("status") == 1:
                        logger.info(f"Successfully updated status for MTX ID {mtx_id_to_submit} to SelectedForProcessing. Tx: {status_update_receipt.get('tx_hash')}")
                        
                        # Now proceed to call ModelRegistry
                        logger.info(f"Calling ModelRegistry to update with MTX ID {mtx_id_to_submit}, Model State CID {model_state_cid_to_submit}, DPoDL Checkpoint CID {dpodl_checkpoint_cid_to_submit}")
                        update_receipt = update_reference_model_from_mtx(
                            model_state_cid=model_state_cid_to_submit,
                            dpodl_checkpoint_cid=dpodl_checkpoint_cid_to_submit,
                            mtx_id=mtx_id_to_submit,
                            signer_private_key=signer_private_key
                        )

                        if update_receipt and update_receipt.get("status") == 1:
                            tx_hash = update_receipt.get("tx_hash")
                            logger.info(f"Successfully updated ModelRegistry with MTX ID {mtx_id_to_submit}. TxHash: {tx_hash}")
                            # Optionally, re-fetch and log the new global CIDs to confirm
                            new_global_model_state = get_current_reference_model_state_cid()
                            new_global_dpodl_checkpoint = get_current_reference_dpodl_checkpoint_cid()
                            logger.info(f"New global reference model state CID: {new_global_model_state}, DPoDL checkpoint CID: {new_global_dpodl_checkpoint}")
                        else:
                            logger.error(f"Failed to update ModelRegistry with MTX ID {mtx_id_to_submit}. Receipt: {update_receipt}")
                            # Consider if we need to revert the status of MTX ID {mtx_id_to_submit} back to Pending or mark as Rejected
                            # For now, it will remain SelectedForProcessing but not processed by ModelRegistry.
                    else:
                        logger.error(f"FAILED to update status for MTX ID {mtx_id_to_submit} to SelectedForProcessing. Receipt: {status_update_receipt}. ModelRegistry update will not be attempted.")
            else:
                logger.error(f"Could not find 'final_model_state_cid' (or similar) in DPoDL state for MTX ID {mtx_id_to_submit} (DPoDL CID: {dpodl_checkpoint_cid_to_submit}). Cannot update ModelRegistry.")
        else:
            logger.error(f"Failed to load DPoDL state from IPFS for MTX ID {mtx_id_to_submit} (DPoDL CID: {dpodl_checkpoint_cid_to_submit}). Cannot determine model_state_cid for submission.")

    elif pending_mtxs_from_chain: # Some were pending but none could be evaluated
        logger.info("No MTXs could be successfully evaluated from the pending list.")
    else: # No pending and none evaluated (already covered by initial check)
        pass 

    logger.info("--- Finished MTX Mempool Processing ---")

    # In a real system, run_training would be called again, potentially
    # looping or triggered by new tasks/blocks. The select_best_mtx 
    # logic would run at the start of that next call.

if __name__ == "__main__":
    logger.info("Running trainer script directly.")
    # Example local run with placeholder D-PoDL values
    # Parameters formerly passed here will now be fetched by get_config()
    
    # Allow overriding num_workers from CLI for convenience during testing
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-workers", type=int, help="Number of Ray workers")
    args = parser.parse_args()

    run_training(cli_num_workers=args.num_workers)
