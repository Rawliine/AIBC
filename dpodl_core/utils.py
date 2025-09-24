# dpodl_core/utils.py
import os
import psutil
import torch
import logging
import subprocess
import json
import ipfshttpclient
from collections import OrderedDict # Import OrderedDict
import logging.handlers # Make sure this is imported
import sys # Import sys for stdout/stderr redirection

# Use basicConfig only if no handlers are configured by caller (e.g., Ray)
if not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Use the root logger or a specific logger for this module
logger = logging.getLogger("dpodl_core.utils") 

# Global variable to store the original stdout and stderr
original_stdout = sys.stdout
original_stderr = sys.stderr

class StreamToLogger:
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger_instance, log_level=logging.INFO, original_stream_for_fileno=None):
        self.logger = logger_instance
        self.log_level = log_level
        self.linebuf = ''
        self.original_stream_for_fileno = original_stream_for_fileno
        # Try to get encoding from the original stream, default to utf-8
        if self.original_stream_for_fileno and hasattr(self.original_stream_for_fileno, 'encoding'):
            self.encoding = self.original_stream_for_fileno.encoding
        else:
            self.encoding = "utf-8" # Default encoding

    def write(self, buf):
        for line in buf.rstrip().split('\n'):
            if line.strip():  # Only log non-empty lines
                # Check if line looks like an error message
                if any(error_indicator in line.lower() for error_indicator in ['error', 'exception', 'failed', 'critical', 'fatal']):
                    self.logger.log(logging.ERROR, line.rstrip())
                else:
                    self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass

    def isatty(self):
        if self.original_stream_for_fileno and hasattr(self.original_stream_for_fileno, 'isatty'):
            return self.original_stream_for_fileno.isatty()
        return False

    def fileno(self):
        if self.original_stream_for_fileno and hasattr(self.original_stream_for_fileno, 'fileno'):
            return self.original_stream_for_fileno.fileno()
        # Fallback if no original stream or it has no fileno.
        # This might be problematic if a real fileno is strictly required.
        # For faulthandler, it might need a real one.
        # Raise an error as a non-functional fileno can cause subtle issues.
        raise OSError(f"StreamToLogger (logger: {self.logger.name}, level: {self.log_level}) does not have a valid file descriptor.")


def setup_main_file_logging(log_file_name="main_script.log", logs_dir="logs", max_files=4, max_bytes=10*1024*1024):
    """
    Sets up file logging for a main script, including rotating files and stdout/stderr redirection.
    Args:
        log_file_name (str): The base name for the log file (e.g., 'trainer.log').
        logs_dir (str): The directory to store log files.
        max_files (int): The maximum number of log files to keep.
        max_bytes (int): The maximum size of a log file before rotation.
    """
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    log_file_path = os.path.join(logs_dir, log_file_name)

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO) # Set a base level; can be overridden by specific handlers

    # Remove existing handlers to avoid duplicate logs if this function is called multiple times
    # for handler in root_logger.handlers[:]:
    #     root_logger.removeHandler(handler)

    # Configure RotatingFileHandler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=max_bytes,
        backupCount=max_files -1 if max_files > 0 else 0 # backupCount is N-1 files
    )
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Redirect stdout and stderr to the logger
    # It's important to ensure that the logger used by StreamToLogger is configured
    # to write to the file. Using the root logger here ensures that.
    # Pass the module-level original_stdout/stderr which should be the true console streams.
    sys.stdout = StreamToLogger(root_logger, logging.INFO, original_stream_for_fileno=original_stdout)
    sys.stderr = StreamToLogger(root_logger, logging.ERROR, original_stream_for_fileno=original_stderr)

    root_logger.info(f"Logging initialized. Output is being redirected to {log_file_path}")
    root_logger.info(f"Log rotation configured: max_files={max_files}, max_bytes={max_bytes}")


def restore_original_streams():
    """Restores sys.stdout and sys.stderr to their original values."""
    sys.stdout = original_stdout
    sys.stderr = original_stderr
    logging.getLogger().info("Restored original stdout and stderr streams.")


def get_logger(name, log_file=None, level=logging.INFO, logs_dir="logs", max_files=4, max_bytes=10*1024*1024):
    """
    Returns a logger with the specified name and configuration.
    If log_file is provided, it sets up file logging.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if log_file:
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        log_file_path = os.path.join(logs_dir, log_file)

        # Configure RotatingFileHandler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=max_bytes,
            backupCount=max_files -1 if max_files > 0 else 0 # backupCount is N-1 files
        )
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

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
    dpodl_state: dict = None,
    upload_to_ipfs_flag: bool = True # New flag to control IPFS upload
):
    """
    Saves a training checkpoint locally.
    Includes model state, optimizer state, epoch, loss, and D-PoDL state.
    Optionally uploads to IPFS based on upload_to_ipfs_flag.
    
    Args:
        epoch: Current epoch number (to be saved).
        model: The model instance.
        optimizer: The optimizer instance.
        loss: The loss value for this epoch/checkpoint.
        checkpoint_path: Local path to save the checkpoint file.
        dpodl_state: Dictionary containing D-PoDL context.
        upload_to_ipfs_flag: Boolean indicating whether to upload to IPFS.
                      
    Returns:
        IPFS CID if upload is attempted and successful, otherwise local path or None on error.
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

    # --- IPFS Upload (Conditional) ---
    ipfs_cid = None
    if upload_to_ipfs_flag:
        try:
            client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001', timeout=5)
            client.version() 
            
            res = client.add(checkpoint_path)
            ipfs_cid = res['Hash']
            logger.info(f"Checkpoint uploaded to IPFS. CID: {ipfs_cid}")
            
            try:
                with open('checkpoint_cids.txt', 'a') as f:
                    f.write(f"{epoch},{ipfs_cid},{checkpoint_path}\n")
            except Exception as f_err:
                logger.warning(f"Failed to write CID to checkpoint_cids.txt: {f_err}")
                
        except ipfshttpclient.exceptions.ConnectionError:
            logger.warning(f"IPFS connection failed (daemon not running?). Checkpoint CID not generated for {checkpoint_path}.")
            # Return local path if IPFS fails but local save worked
            return checkpoint_path # Or None, depending on desired behavior on IPFS fail
        except Exception as e:
            logger.error(f"An error occurred during IPFS upload for {checkpoint_path}: {e}")
            # Return local path if IPFS fails
            return checkpoint_path # Or None
    else:
        logger.info(f"IPFS upload skipped for {checkpoint_path} as per configuration.")
        # Return local path when IPFS is skipped but local save was successful
        return checkpoint_path 
        
    return ipfs_cid if ipfs_cid else checkpoint_path # Ensure we return CID if available, else local path

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
            
            # Try weights_only=True first for security, fallback to unsafe if needed
            try:
                checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
                logger.info("Checkpoint loaded with weights_only=True (secure mode)")
            except Exception as weights_only_err:
                logger.warning(f"weights_only=True failed, falling back to unsafe mode: {weights_only_err}")
                checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
                logger.warning("Checkpoint loaded with weights_only=False (unsafe mode)")
            
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
