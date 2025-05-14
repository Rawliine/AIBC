import os
import time
import ray
import torch
import logging
import argparse

# Ray AIR / train
from ray.train.torch import TorchTrainer
from ray.air.config import ScalingConfig, RunConfig
from ray.train import Checkpoint, FailureConfig

# Import components from within the package
from .data_loader import load_dataset_and_partition
from .worker import worker_train_loop  # Import the worker loop
from .utils import logger # Import logger if configured globally
# Import the blockchain interface function
from .blockchain_interface import get_current_reference_cid
from .config_utils import get_config # Import the new config utility

# Configure logging if not already done globally
# logging.basicConfig(level=logging.INFO) 
# logger = logging.getLogger("dpodl_trainer")

# --- Simulated Mempool for Model Transactions (MTX) ---
global mtx_mempool
mtx_mempool = [] # Global or passed around in a real system

def select_best_mtx(mempool):
    """Selects the 'best' mtx from the mempool (e.g., highest accuracy)."""
    if not mempool:
        return None
    # Simple selection: highest accuracy. Could be more complex (steps, lineage, etc.)
    best_mtx = max(mempool, key=lambda x: x.get('accuracy', 0.0))
    logger.info(f"Selected best mtx from mempool: CID {best_mtx.get('ipfs_cid')}, Acc {best_mtx.get('accuracy'):.4f}")
    return best_mtx
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

    # --- Determine Reference Model ID for this run --- 
    # Use the one passed in, otherwise get from the blockchain registry
    # current_reference_model_id = app_config["reference_model_id"] # Use config value
    # Simplification: Always try to fetch from blockchain unless explicitly set in config for testing
    
    if app_config.get("reference_model_id_override") is not None: # Allow test override
        current_reference_model_id = app_config["reference_model_id_override"]
        logger.info(f"Using overridden reference_model_id from config: {current_reference_model_id}")
    elif app_config["reference_model_id"]:
        current_reference_model_id = app_config["reference_model_id"]
        logger.info(f"Using provided reference_model_id from config: {current_reference_model_id}")
    else:
        logger.info("No reference_model_id in config. Querying blockchain registry...")
        current_reference_model_id = get_current_reference_cid()
        if not current_reference_model_id:
            # Handle case where blockchain call fails or returns empty (genesis)
            logger.warning("Failed to get reference CID from registry or registry is at genesis. Starting fresh.")
            current_reference_model_id = None # Ensure it's None if empty or error
        else:
            logger.info(f"Using current reference model from registry: {current_reference_model_id}")
    # ----------------------------------------------------

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
        "reference_model_id": current_reference_model_id,
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
