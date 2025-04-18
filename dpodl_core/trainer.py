import os
import time
import ray
import torch
import logging

# Ray AIR / train
from ray.train.torch import TorchTrainer
from ray.air.config import ScalingConfig, RunConfig
from ray.train import Checkpoint

# Import components from within the package
from .data_loader import load_dataset_and_partition
from .worker import worker_train_loop  # Import the worker loop
from .utils import logger # Import logger if configured globally

# Configure logging if not already done globally
# logging.basicConfig(level=logging.INFO) 
# logger = logging.getLogger("dpodl_trainer")

def run_training(
    num_workers: int = 1,
    epochs: int = 5,
    batch_size: int = 256,
    seq_len: int = 128,
    embed_dim: int = 256,
    num_heads: int = 8,
    num_layers: int = 6,
    checkpoint_path: str = "checkpoint_deeper.pt",
    # Add D-PoDL parameters with defaults
    prev_block_hash: str = "0x0000000000000000", # Placeholder
    t1_threshold: int = 2**240, # Placeholder High Threshold (easy)
    t2_threshold: int = 2**256, # Placeholder Max Threshold (easy)
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
        "reference_model_id": reference_model_id,
    }
    logger.info(f"Worker config prepared: {train_loop_config}")

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
            # Add failure config later if needed
            # failure_config=ray.train.FailureConfig(max_failures=1)
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
    logger.info("Starting trainer.fit()...")
    result = trainer.fit()
    logger.info(f"Training finished. Ray result: {result}")

if __name__ == "__main__":
    logger.info("Running trainer script directly.")
    # Example local run with placeholder D-PoDL values
    run_training(
        num_workers=2,
        epochs=5,
        batch_size=256,
        seq_len=128,
        embed_dim=256,
        num_heads=8,
        num_layers=6,
        checkpoint_path="checkpoint_dpodl.pt",
        # Pass placeholder D-PoDL params for testing
        prev_block_hash="0x1111",
        t1_threshold=2**250 # Make it very easy for testing
    )
