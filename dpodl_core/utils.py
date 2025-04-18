# dpodl_core/utils.py
import os
import psutil
import torch
import logging
import subprocess
import json
import ipfshttpclient
from collections import OrderedDict # Import OrderedDict

# Use basicConfig only if no handlers are configured by caller (e.g., Ray)
if not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Use the root logger or a specific logger for this module
logger = logging.getLogger("dpodl_core.utils") 

# --- Memory Logging --- #

def log_memory_usage_gpu(msg=""):
    """
    Log GPU memory usage.
    """
    if torch.cuda.is_available():
        alloc = torch.cuda.memory_allocated() / (1024 ** 2)
        max_alloc = torch.cuda.max_memory_allocated() / (1024 ** 2)
        reserved = torch.cuda.memory_reserved() / (1024**2)
        max_reserved = torch.cuda.max_memory_reserved() / (1024**2)
        logger.info(f"[GPU Memory] {msg} Current alloc: {alloc:.2f} MB, Max alloc: {max_alloc:.2f} MB, Reserved: {reserved:.2f} MB, Max Reserved: {max_reserved:.2f} MB")
    else:
        logger.debug("[GPU Memory] CUDA not available.")

def log_memory_usage_cpu(msg=""):
    """
    Log CPU memory (RSS) usage.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info().rss / (1024 ** 2)
    logger.info(f"[CPU Memory] {msg} RSS: {mem_info:.2f} MB")

# --- Checkpointing --- #

def save_checkpoint(
    epoch: int,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    loss: float,
    checkpoint_path: str,
    # D-PoDL specific state to save
    dpodl_state: dict = None 
):
    """
    Saves a training checkpoint locally.
    Includes model state, optimizer state, epoch, loss, and D-PoDL state.
    NOTE: IPFS saving logic is here but will fail if daemon isn't running.
    
    Args:
        epoch: Current epoch number (to be saved).
        model: The model instance.
        optimizer: The optimizer instance.
        loss: The loss value for this epoch/checkpoint.
        checkpoint_path: Local path to save the checkpoint file.
        dpodl_state: Dictionary containing D-PoDL context 
                     (e.g., {'nonce', 'pre_hash_value', 'reference_model_id',
                      'random_seed', 'seed_for_weights', 't1_threshold', 't2_threshold'}).
                      
    Returns:
        IPFS CID if upload is successful, otherwise None.
    """
    state = {
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "loss": loss,
        "dpodl_state": dpodl_state if dpodl_state is not None else {} # Store D-PoDL state
    }
    try:
        # Ensure directory exists only if the path includes one
        checkpoint_dir = os.path.dirname(checkpoint_path)
        if checkpoint_dir: # Only call makedirs if dirname is not empty
            os.makedirs(checkpoint_dir, exist_ok=True)
        torch.save(state, checkpoint_path)
        logger.info(f"Checkpoint saved locally at {checkpoint_path}")
        if dpodl_state:
            logger.info(f"Saved D-PoDL state: {list(dpodl_state.keys())}")
    except Exception as e:
        logger.error(f"Failed to save checkpoint locally to {checkpoint_path}: {e}", exc_info=True)
        return None # Indicate failure

    # --- IPFS Upload (Optional) ---
    ipfs_cid = None
    try:
        # Attempt connection within the function - less efficient but self-contained
        client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001', timeout=5) # Add timeout
        # Quick check
        client.version() 
        
        # Add the file to IPFS
        res = client.add(checkpoint_path)
        ipfs_cid = res['Hash']
        logger.info(f"Checkpoint uploaded to IPFS. CID: {ipfs_cid}")
        
        # Optional: Record CID locally
        # Consider a more robust tracking mechanism than a simple text file
        try:
            with open('checkpoint_cids.txt', 'a') as f:
                f.write(f"{epoch},{ipfs_cid},{checkpoint_path}\n")
        except Exception as f_err:
            logger.warning(f"Failed to write CID to checkpoint_cids.txt: {f_err}")
            
    except ipfshttpclient.exceptions.ConnectionError:
        logger.warning(f"IPFS connection failed (daemon not running?). Checkpoint CID not generated for {checkpoint_path}.")
    except Exception as e:
        logger.error(f"An error occurred during IPFS upload for {checkpoint_path}: {e}")
        
    # Return CID if successful, otherwise None
    return ipfs_cid 

def load_checkpoint(checkpoint_path: str, model: torch.nn.Module, optimizer: torch.optim.Optimizer):
    """
    Loads a training checkpoint from a local file.
    Restores model state, optimizer state, epoch, and D-PoDL state.
    
    Args:
        checkpoint_path: Path to the checkpoint file.
        model: The model instance to load state into.
        optimizer: The optimizer instance to load state into.
        
    Returns:
        Tuple: (start_epoch, loss, dpodl_state)
         - start_epoch (int): Epoch number to resume from.
         - loss (float): Loss value from the checkpoint.
         - dpodl_state (dict): Loaded D-PoDL state dictionary, or empty dict if none found.
    """
    start_epoch = 0
    loss = float("inf")
    dpodl_state = {}
    
    if os.path.isfile(checkpoint_path):
        try:
            logger.info(f"Loading checkpoint from {checkpoint_path}...")
            checkpoint = torch.load(checkpoint_path, map_location="cpu") 
            
            model.load_state_dict(checkpoint["model_state_dict"])
            if optimizer and 'optimizer_state_dict' in checkpoint:
                 optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            else:
                 logger.warning("Optimizer state not loaded (not found in checkpoint or optimizer not provided).")
            
            start_epoch = checkpoint.get("epoch", 0)
            loss = checkpoint.get("loss", float("inf"))
            dpodl_state = checkpoint.get("dpodl_state", {}) # Load D-PoDL state
            
            logger.info(f"Loaded checkpoint from {checkpoint_path} (epoch={start_epoch}, loss={loss:.4f})")
            if dpodl_state:
                logger.info(f"Loaded D-PoDL state keys: {list(dpodl_state.keys())}")
            else:
                logger.warning("No D-PoDL state found in checkpoint.")
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint from {checkpoint_path}: {e}. Starting fresh.", exc_info=True)
            start_epoch = 0
            loss = float("inf")
            dpodl_state = {} # Reset state on error
    else:
        logger.warning(f"No checkpoint file found at {checkpoint_path}. Starting fresh.")
        
    return start_epoch, loss, dpodl_state

# --- Model Weight Transfer --- #

def transfer_weights(source_state_dict: OrderedDict, target_model: torch.nn.Module):
    """
    Transfers weights from a source state_dict to a target model.
    Only copies weights for layers with matching names and shapes.
    Useful for initializing a model from a reference model (transfer learning).

    Args:
        source_state_dict: The state_dict loaded from the reference model.
        target_model: The newly initialized model instance to transfer weights into.
    """
    target_state_dict = target_model.state_dict()
    transferred_count = 0
    skipped_count = 0
    
    logger.info(f"Attempting to transfer weights. Target layers: {len(target_state_dict)}, Source layers: {len(source_state_dict)}")
    
    # Create a new state dict for loading into the target model
    new_state_dict = target_state_dict.copy()
    
    for name, target_param in target_state_dict.items():
        if name in source_state_dict:
            source_param = source_state_dict[name]
            if source_param.shape == target_param.shape:
                # Copy the weights from source to the new state dict
                new_state_dict[name] = source_param
                transferred_count += 1
                logger.debug(f"Transferred weights for layer: {name} | Shape: {target_param.shape}")
            else:
                # Shape mismatch, keep target's initial weights
                logger.warning(f"Skipping layer {name}: Shape mismatch. Target: {target_param.shape}, Source: {source_param.shape}")
                skipped_count += 1
        else:
            # Layer not found in source, keep target's initial weights
            logger.warning(f"Skipping layer {name}: Not found in source state_dict.")
            skipped_count += 1
            
    # Load the modified state dict into the target model
    target_model.load_state_dict(new_state_dict)
    logger.info(f"Weight transfer complete. Transferred: {transferred_count}, Skipped: {skipped_count}")

# --- Data Handling --- #

def collate_batch(batch_data, seq_len=32):
    """
    Collates a batch of data from Hugging Face dataset format to PyTorch tensors.
    Handles padding and truncation.
    """
    texts = []
    labels = []

    if not isinstance(batch_data, list):
        batch_data = list(batch_data)

    for example in batch_data:
        # Adapt based on actual dataset keys
        label = example.get("label", example.get("labels")) 
        input_ids = example.get("input_ids")
        
        if label is None or input_ids is None:
             logger.warning(f"Skipping example due to missing keys: {example.keys()}")
             continue

        # Truncate or pad input_ids
        if len(input_ids) > seq_len:
            input_ids = input_ids[:seq_len]
        else:
            # Use a padding token ID (e.g., 0 for BERT-like models) if available
            # padding_token_id = tokenizer.pad_token_id if hasattr(tokenizer, 'pad_token_id') else 0
            padding_token_id = 0 # Assuming 0 is padding
            input_ids += [padding_token_id] * (seq_len - len(input_ids))

        labels.append(label)
        texts.append(input_ids)
        
    if not texts or not labels:
        # Return empty tensors if batch is empty after filtering
        return torch.tensor([], dtype=torch.long), torch.tensor([], dtype=torch.long)

    try:
        texts_t = torch.tensor(texts, dtype=torch.long)
        labels_t = torch.tensor(labels, dtype=torch.long)
    except Exception as e:
        logger.error(f"Error converting batch to tensor: {e}. Batch size: {len(batch_data)}")
        # Return empty tensors on error
        return torch.tensor([], dtype=torch.long), torch.tensor([], dtype=torch.long)
        
    return texts_t, labels_t
