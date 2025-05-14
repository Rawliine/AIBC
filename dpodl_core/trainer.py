import os
import time
import ray
import torch
import logging

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
    num_workers: int = 1,
    epochs: int = 5,
    batch_size: int = 128,
    seq_len: int = 128,
    embed_dim: int = 256,
    num_heads: int = 8,
    num_layers: int = 6,
    checkpoint_path: str = "checkpoint_deeper.pt",
    # Add D-PoDL parameters with defaults
    prev_block_hash: str = "0x0000000000000000", # Placeholder
    t1_threshold: int = 2**240, # Placeholder High Threshold (easy)
    t2_threshold: int = 2**256, # Placeholder Max Threshold (easy)
    t_acc_threshold: float = 0.95, # Add Target Accuracy Threshold
    reference_model_id: str = None # Placeholder
):
    """
    Orchestrates the distributed D-PoDL training using Ray Train.
    - Initializes Ray.
    - Loads and partitions dataset.
    - Sets up configuration for workers, including D-PoDL params.
    - Creates and runs the Ray TorchTrainer.
    """
    logger.info("Starting D-PoDL training orchestration...")
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
    data_loaded = load_dataset_and_partition(num_workers, batch_size) 
    train_partitions = data_loaded["train_partitions"]
    val_partition = data_loaded["val_dataset"] # Assuming val_dataset is suitable for all workers
    logger.info(f"Dataset loaded. Train partitions: {len(train_partitions)}, Val dataset: {val_partition}")

    # --- Determine Reference Model ID for this run --- 
    # Use the one passed in, otherwise get from the blockchain registry
    if reference_model_id:
        current_reference_model_id = reference_model_id
        logger.info(f"Using provided reference_model_id: {current_reference_model_id}")
    else:
        logger.info("No reference_model_id provided. Querying blockchain registry...")
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
        "train_partitions": train_partitions, # Renamed for clarity
        "val_partition": val_partition,     # Pass validation data
        "seq_len": seq_len,
        "batch_size": batch_size,
        "epochs": epochs,
        "lr": 1e-3,
        "embed_dim": embed_dim, # Note: This might be overridden by HtoA
        "num_heads": num_heads, # Note: This might be overridden by HtoA
        "num_layers": num_layers, # Note: This might be overridden by HtoA
        "checkpoint_path": checkpoint_path,
        # D-PoDL params
        "prev_block_hash": prev_block_hash,
        "t1_threshold": t1_threshold,
        "t2_threshold": t2_threshold,
        "t_acc_threshold": t_acc_threshold, # Pass Tacc to worker
        # Use the determined reference model ID for this run
        "reference_model_id": current_reference_model_id, 
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

    if result.metrics_dataframe is not None:
        # Ray Train reports metrics per-epoch/per-step usually.
        # We need to filter for our specific reported status dicts.
        # Let's look for the last report per worker if multiple reports exist.
        # Group by worker index and get the last entry (assuming step increases)
        # Note: Accessing custom reported dicts might need specific Ray versions/APIs.
        # This approach assumes the dict is flattened or accessible.
        # A simpler approach might be to look at result.checkpoint
        
        # Alternative: iterate through checkpoints if results are tied to them
        # checkpoints = result.best_checkpoints # or result.checkpoints

        # Let's assume reported metrics are directly accessible (may need adjustment)
        try:
            # Example: Accessing metrics reported via `report()`
            # The exact structure depends on Ray version and how reports are aggregated.
            # We might need to access raw logs or a specific results attribute.
            # Let's try iterating through the history which often contains reported dicts.
            if result.metrics_dataframe is not None and not result.metrics_dataframe.empty:
                 # Find rows containing our custom status report
                 report_df = result.metrics_dataframe[result.metrics_dataframe['status'].notna()].copy()
                 # Get the last report for each worker
                 last_reports = report_df.loc[report_df.groupby('training_iteration')['steps'].idxmax()]
                 
                 for index, report_data in last_reports.iterrows():
                    status = report_data.get("status")
                    cid = report_data.get("ipfs_cid")
                    acc = report_data.get("accuracy")
                    steps = report_data.get("steps")
                    # Potentially retrieve summary from flattened columns if needed
                    # summary = report_data.get("dpodl_state_summary") 

                    logger.info(f"  Worker reported: Status={status}, CID={cid}, Acc={acc:.4f}, Steps={steps}")
                    
                    if status == "SAVE_BLOCK_CHECKPOINT":
                        block_candidates.append({"ipfs_cid": cid, "accuracy": acc, "steps": steps})
                    elif status == "SAVE_MTX_CHECKPOINT":
                        # Add to a temporary list first
                        new_mtx_candidates.append({"ipfs_cid": cid, "accuracy": acc, "steps": steps})
            else:
                 logger.warning("No metrics dataframe found or it is empty.")

        except Exception as e:
            logger.error(f"Error processing Ray Train results: {e}. Check result structure.", exc_info=True)

    # Log findings
    if block_candidates:
        logger.info(f"Found {len(block_candidates)} block candidates:")
        for bc in block_candidates:
            logger.info(f"  - CID: {bc['ipfs_cid']}, Accuracy: {bc['accuracy']:.4f}, Steps: {bc['steps']}")
            # TODO: Add logic to select best block candidate and submit to blockchain
    else:
        logger.info("No block candidates reported by workers.")

    # Remove old simulated mempool addition
    # if new_mtx_candidates:
    #     logger.info(f"Found {len(new_mtx_candidates)} new mtx candidates to add to mempool:")
    #     for mtx in new_mtx_candidates:
    #         logger.info(f"  - CID: {mtx['ipfs_cid']}, Accuracy: {mtx['accuracy']:.4f}, Steps: {mtx['steps']}")
    #         # Add to our simulated mempool (replace with actual mempool logic)
    #         mtx_mempool.append(mtx) 
    # else:
    #     logger.info("No new mtx candidates reported by workers.")
        
    # logger.info(f"Current MTX Mempool size: {len(mtx_mempool)}")
    # --- End Processing Results --- 

    # In a real system, run_training would be called again, potentially
    # looping or triggered by new tasks/blocks. The select_best_mtx 
    # logic would run at the start of that next call.


if __name__ == "__main__":
    logger.info("Running trainer script directly.")
    # Example local run with placeholder D-PoDL values
    run_training(
        num_workers=2,
        epochs=5,
        batch_size=128,
        seq_len=128,
        embed_dim=256,
        num_heads=8,
        num_layers=6,
        checkpoint_path="checkpoint_dpodl.pt",
        # Pass placeholder D-PoDL params for testing
        prev_block_hash="0x1111",
        t1_threshold=2**250, # Make it very easy for testing
        t_acc_threshold=0.97 # Example Tacc for testing
    )
