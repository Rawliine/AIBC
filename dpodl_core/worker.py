import os
import time
import ray
import torch
import logging
import torch.distributed as dist
import json # Added for saving trace
import tempfile # Added for saving trace
from ray.train import get_context, report # Import report
from torch.utils.data import DataLoader
from collections import OrderedDict # Added for checkpoint hashes

# Import necessary components from the package
from .models import DeeperTransformer
from .utils import (
    logger as global_logger, # Rename to avoid conflict with worker_logger
    log_memory_usage_cpu,
    log_memory_usage_gpu,
    save_checkpoint,
    load_checkpoint,
    collate_batch,
    transfer_weights
)
# Import IPFS functions separately
from .ipfs_utils import (
    load_model_state_from_ipfs, # Import from correct module
    add_file_to_ipfs # We might need this later for traces?
)
# Import crypto functions
from .crypto import (
    calculate_pre_hash,
    verify_pre_hash_threshold,
    extract_seed_from_hash,
    hash_to_architecture, # Using placeholder
    calculate_post_hash,
    verify_post_hash_threshold,
    hash_model_state, # Import for checkpoint hashing
    hash_bytes, # Import for trace hashing
    build_merkle_tree, # Import for Merkleization
    bytes_to_hex # Import for logging root hash
)
# Import blockchain interface functions
from .blockchain_interface import submit_block, submit_mtx
# crypto and ipfs_utils might be needed later
# from .crypto import ... 
# from .ipfs_utils import ...

# Define a maximum number of nonce attempts to prevent infinite loops
MAX_NONCE_ATTEMPTS = 1_000_000 # Example limit
CHECKPOINT_INTERVAL_STEPS = 100 # Create a model hash every 100 steps
# TRACE_RECORDING_ENABLED = True # Control flag if needed

# --- Helper Function --- #

def evaluate_accuracy(model, val_dataset, batch_size, device, seq_len, collate_fn):
    """
    Evaluates the model's accuracy on the validation dataset.
    """
    model.eval() # Set model to evaluation mode
    # Let DataLoader handle batching, use our collate_fn for tensor conversion
    val_loader = DataLoader(
        val_dataset, 
        batch_size=batch_size, 
        collate_fn=lambda batch: collate_fn(batch, seq_len=seq_len)
    )
    correct = 0
    total = 0
    
    with torch.no_grad(): # Disable gradient calculations
        for batch_tensors in val_loader: # DataLoader now yields tensors directly
            texts_t, labels_t = batch_tensors
            
            if texts_t.numel() == 0: # Skip empty batches potentially yielded by collate_fn
                continue
                
            texts_t = texts_t.to(device)
            labels_t = labels_t.to(device)
            
            outputs = model(texts_t)
            _, predicted = torch.max(outputs.data, 1)
            total += labels_t.size(0)
            correct += (predicted == labels_t).sum().item()
            
    accuracy = correct / total if total > 0 else 0.0
    model.train() # Set model back to training mode
    return accuracy

# --- Main Worker Loop --- #

def worker_train_loop(config):
    """
    Function executed on each Ray worker for D-PoDL training.
    Includes Pre-Hash, Training, and Post-Hash stages (partially implemented).
    - Performs Pre-Hash check (finding nonce, verifying T1).
    - Extracts random seed for deterministic training.
    - Initializes model (potentially from reference).
    - Runs training epochs.
    - Saves checkpoints locally and potentially to IPFS.
    """
    # ===>>> Worker Logging Setup <<<===
    rank = get_context().get_world_rank()
    worker_logger = logging.getLogger(f"Worker_{rank}")
    if not worker_logger.hasHandlers():
         handler = logging.StreamHandler()
         formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
         handler.setFormatter(formatter)
         worker_logger.addHandler(handler)
         worker_logger.setLevel(logging.INFO)
    worker_logger.info("--- worker_train_loop started! ---")

    # ===>>> Configuration Extraction <<<===
    world_size = get_context().get_world_size()
    worker_logger.info(f"Worker rank: {rank}, World size: {world_size}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    worker_logger.info(f"Using device: {device}")

    # Training params
    train_partition = config["train_partitions"][rank]
    val_partition = config["val_partition"]
    seq_len = config["seq_len"]
    batch_size = config["batch_size"]
    epochs = config["epochs"]
    lr = config["lr"]
    # D-PoDL specific config
    prev_block_hash = config.get("prev_block_hash", "0x0000")
    reference_model_id = config.get("reference_model_id", None)
    t1_threshold = config.get("t1_threshold", 2**256-1) # Default to max value (no threshold)
    t2_threshold = config.get("t2_threshold", 2**256-1) # Default to max value
    checkpoint_path = config["checkpoint_path"]
    t_acc_threshold = config.get("t_acc_threshold", 0.9999) # Extract Tacc, default high

    # ===>>> Pre-Hash Stage (Finding Nonce) <<<===
    worker_logger.info(f"Starting Pre-Hash stage... Target T1: {t1_threshold}")
    start_nonce_time = time.time()
    nonce = 0
    pre_hash_value = None
    found_nonce = False
    
    # Simple nonce search loop
    for attempt in range(MAX_NONCE_ATTEMPTS):
        nonce = attempt # Start nonce search from 0 for this example
        calculated_hash = calculate_pre_hash(prev_block_hash, reference_model_id, nonce)
        
        if verify_pre_hash_threshold(calculated_hash, t1_threshold):
            pre_hash_value = calculated_hash
            found_nonce = True
            worker_logger.info(f"Found valid nonce {nonce} after {attempt+1} attempts. Pre-Hash: {pre_hash_value}")
            break # Exit loop once valid nonce is found
        
        # Optional: Log progress periodically
        # if attempt % 10000 == 0:
        #    worker_logger.debug(f"Pre-Hash attempt {attempt}, hash: {calculated_hash[:10]}...")
            
    if not found_nonce:
        worker_logger.error(f"Failed to find a valid nonce after {MAX_NONCE_ATTEMPTS} attempts. Aborting worker.")
        # Report failure back to Ray Train if possible, or just raise an error
        raise RuntimeError(f"Worker {rank} failed Pre-Hash stage.")
        
    nonce_time = time.time() - start_nonce_time
    worker_logger.info(f"Pre-Hash stage completed in {nonce_time:.2f}s.")

    # Extract seed for deterministic training
    random_seed = extract_seed_from_hash(pre_hash_value)
    worker_logger.info(f"Extracted random seed: {random_seed}")

    # ===>>> Model Initialization using HtoA <<<===
    worker_logger.info("Initializing model based on Pre-Hash...")
    derived_config = hash_to_architecture(pre_hash_value)
    architecture_params = derived_config["architecture"]
    seed_for_weights = derived_config["seed_for_weights"]
    worker_logger.info(f"Derived architecture: {architecture_params}")
    worker_logger.info(f"Seed for weight initialization: {seed_for_weights}")

    # Instantiate the target model structure based on derived parameters
    vocab_size = 30522 
    num_classes = 4
    model = DeeperTransformer(
        vocab_size=vocab_size,
        embed_dim=architecture_params["embed_dim"],
        seq_len=seq_len, 
        num_heads=architecture_params["num_heads"],
        num_layers=architecture_params["num_layers"],
        num_classes=num_classes
    ).to(device)
    worker_logger.info(f"Target model structure instantiated on device {device}.")

    # ===>>> Load Private Key for Signing <<<===
    # Get the worker's rank to load a rank-specific private key
    # rank = get_context().get_world_rank() # Already obtained earlier
    
    worker_specific_env_var = f"WORKER_PRIVATE_KEY_{rank}"
    worker_private_key = os.getenv(worker_specific_env_var)

    if not worker_private_key:
        error_msg = f"{worker_specific_env_var} environment variable not set for worker {rank}. Each worker requires a unique private key."
        worker_logger.error(error_msg)
        raise ValueError(error_msg)
    else:
        try:
            from web3 import Web3 # Local import for quick check
            signer_address = Web3().eth.account.from_key(worker_private_key).address
            worker_logger.info(f"Worker {rank} will sign transactions with address: {signer_address} (from {worker_specific_env_var})")
        except Exception as key_err:
            error_msg = f"Provided {worker_specific_env_var} for worker {rank} is invalid: {key_err}"
            worker_logger.error(error_msg)
            raise ValueError(error_msg)

    # --- Attempt Reference Model Loading & Weight Transfer ---
    reference_loaded_successfully = False
    if reference_model_id:
        worker_logger.info(f"Attempting to load reference model: {reference_model_id}")
        source_state_dict = load_model_state_from_ipfs(reference_model_id)
        
        if source_state_dict:
            worker_logger.info("Reference model state loaded. Attempting weight transfer...")
            try:
                transfer_weights(source_state_dict, model) # Use the utility function
                reference_loaded_successfully = True
                worker_logger.info("Successfully transferred weights from reference model.")
            except Exception as transfer_e:
                worker_logger.error(f"Failed to transfer weights from reference model {reference_model_id}: {transfer_e}", exc_info=True)
        else:
            worker_logger.warning(f"Could not load state dict for reference model {reference_model_id}. Proceeding with fresh initialization.")
    else:
        worker_logger.info("No reference model ID provided.")

    # --- Deterministic Weight Initialization (if reference loading failed or wasn't used) ---
    if not reference_loaded_successfully:
        worker_logger.info(f"Applying seed {seed_for_weights} for fresh weight initialization.")
        torch.manual_seed(seed_for_weights)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed_for_weights)
        # Re-initialize weights using standard methods but with the specific seed set.
        # The model was already instantiated, triggering default init. 
        # If a different init strategy is needed, apply it here:
        # model.apply(weights_init_function) 
        # For default init, the seeding above is sufficient before instantiation.
        # Since instantiation happened before potential transfer, we might need
        # to re-apply default init if transfer fails.
        # Let's assume default init during DeeperTransformer() was sufficient for now.
        worker_logger.info("Model initialized with seeded fresh weights.")
    
    # Model is now ready, either with transferred weights or freshly initialized ones.
    
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    # Get dataset partitions
    my_data_list = list(train_partition)
    worker_logger.info(f"Received train partition ({len(my_data_list)} samples) and val partition ({len(val_partition)} samples).")

    # Load D-PoDL state from checkpoint if it exists
    start_epoch, prev_loss, loaded_dpodl_state = load_checkpoint(checkpoint_path, model, optimizer)
    worker_logger.info(f"Loaded checkpoint: start_epoch={start_epoch}, prev_loss={prev_loss}")
    
    # Use loaded D-PoDL state if available, otherwise use config/derived values
    # Important for resuming correctly after a crash
    if loaded_dpodl_state:
        worker_logger.info("Using D-PoDL state loaded from checkpoint.")
        nonce = loaded_dpodl_state.get('nonce', nonce) # Keep initial nonce if not found
        pre_hash_value = loaded_dpodl_state.get('pre_hash_value', pre_hash_value)
        reference_model_id = loaded_dpodl_state.get('reference_model_id', reference_model_id)
        random_seed = loaded_dpodl_state.get('random_seed', random_seed)
        seed_for_weights = loaded_dpodl_state.get('seed_for_weights', seed_for_weights)
        t1_threshold = loaded_dpodl_state.get('t1_threshold', t1_threshold)
        t2_threshold = loaded_dpodl_state.get('t2_threshold', t2_threshold)
        # We might need to re-seed RNGs here based on loaded state
        worker_logger.info(f"Resuming with loaded state: nonce={nonce}, seed={random_seed}, weight_seed={seed_for_weights}")
        torch.manual_seed(random_seed) # Re-seed main RNG
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(random_seed)
        rng = torch.Generator().manual_seed(random_seed) # Re-seed data shuffling RNG
    else:
        worker_logger.info("No D-PoDL state loaded from checkpoint, using derived/config values.")

    # ===>>> Deterministic Training Setup <<<===
    worker_logger.info(f"Setting up RNG with seed: {random_seed}")
    rng = torch.Generator().manual_seed(random_seed)
    # Setup other deterministic aspects if necessary
    torch.manual_seed(random_seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(random_seed)
    # Consider deterministic algorithms if full reproducibility is critical
    # torch.backends.cudnn.deterministic = True
    # torch.backends.cudnn.benchmark = False

    # Placeholder for validation logic
    validation_batches = []

    # ===>>> Training Loop <<<===
    worker_logger.info(f"Starting training loop from epoch {start_epoch} to {epochs}.")
    total_steps_so_far = loaded_dpodl_state.get('steps_at_checkpoint', 0) # Get steps from loaded state
    steps_this_run = 0
    checkpoint_hashes = OrderedDict() # Store {step: hash_bytes} for Merkle tree
    training_trace = [] # List to store trace records for this run

    # Load previous checkpoint hashes if resuming
    if loaded_dpodl_state.get('checkpoint_hashes'):
        try:
            # Convert hex strings back to bytes
            saved_hashes = loaded_dpodl_state['checkpoint_hashes']
            checkpoint_hashes = OrderedDict((int(k), bytes.fromhex(v)) for k, v in saved_hashes.items())
            worker_logger.info(f"Loaded {len(checkpoint_hashes)} checkpoint hashes from previous run.")
        except Exception as load_hash_e:
            worker_logger.warning(f"Could not load checkpoint hashes from state: {load_hash_e}. Starting fresh hash list.")
            checkpoint_hashes = OrderedDict()
            
    # Add hash of initial state (before training starts/resumes)
    if total_steps_so_far == 0 and 0 not in checkpoint_hashes:
         initial_state_hash = hash_model_state(model.state_dict())
         checkpoint_hashes[0] = initial_state_hash
         worker_logger.info(f"Added initial model state hash at step 0: {bytes_to_hex(initial_state_hash)[:10]}...")

    try:
        for epoch in range(start_epoch, epochs):
            t0 = time.time()
            model.train()

            # Shuffle with deterministic RNG
            indices = torch.randperm(len(my_data_list), generator=rng).tolist()
            my_data_list_shuffled = [my_data_list[i] for i in indices]

            epoch_loss = 0.0
            step_count = 0 # Steps within this epoch
            
            # ===>>> Batch Loop <<<===
            for start_idx in range(0, len(my_data_list_shuffled), batch_size):
                current_total_step = total_steps_so_far + steps_this_run + step_count + 1
                step_start_time = time.time() # Define step_start_time HERE
                
                # --- Training Step --- 
                batch_slice = my_data_list_shuffled[start_idx : start_idx + batch_size]
                texts_t, labels_t = collate_batch(batch_slice, seq_len=seq_len)
                if texts_t.numel() == 0: continue # Skip empty batches
                texts_t = texts_t.to(device)
                labels_t = labels_t.to(device)
                
                optimizer.zero_grad()
                logits = model(texts_t)
                loss = torch.nn.functional.cross_entropy(logits, labels_t)
                loss.backward()
                optimizer.step()
                step_end_time = time.time()
                # --- End Training Step --- 

                # --- Trace Recording --- 
                trace_record = {
                    "step": current_total_step,
                    "epoch": epoch,
                    "timestamp": step_end_time,
                    "step_duration_ms": int((step_end_time - step_start_time) * 1000),
                    "loss": loss.item(),
                    # "grad_norm": grad_norm, # Uncomment if calculated
                    # TODO: Add parameter norm? (Expensive)
                    # TODO: Add memory/GPU stats? (Can be noisy)
                }
                training_trace.append(trace_record)
                # --- End Trace Recording --- 

                epoch_loss += loss.item()
                step_count += 1

                # --- Merkle Checkpoint Hashing --- 
                if current_total_step % CHECKPOINT_INTERVAL_STEPS == 0:
                    chkpt_hash = hash_model_state(model.state_dict())
                    checkpoint_hashes[current_total_step] = chkpt_hash
                    worker_logger.debug(f"Stored checkpoint hash at step {current_total_step}: {bytes_to_hex(chkpt_hash)[:10]}...")

                # --- Logging --- 
                if step_count % 100 == 0: # Log every 100 steps within epoch
                     worker_logger.info(f"Epoch {epoch} Step {step_count} (Total: {current_total_step}) - loss={loss.item():.4f}")
                     log_memory_usage_cpu(f"Worker {rank}")
                     log_memory_usage_gpu(f"Worker {rank}")

            # --- End of Epoch --- 
            epoch_loss /= max(step_count, 1)
            dt = time.time() - t0
            worker_logger.info(f"Finished epoch {epoch} with loss={epoch_loss:.4f} in {dt:.1f}s")

            # Update total steps processed in this run
            steps_this_epoch = step_count
            steps_this_run += steps_this_epoch
            current_total_steps = total_steps_so_far + steps_this_run

            # ===>>> Post-Epoch Evaluation and Post-Hash <<<===
            worker_logger.info(f"Epoch {epoch} finished. Evaluating accuracy...")
            accuracy = evaluate_accuracy(model, val_partition, batch_size, device, seq_len, collate_batch)
            worker_logger.info(f"Epoch {epoch} accuracy: {accuracy:.4f}")

            worker_logger.info("Calculating final model state hash...")
            final_model_state_hash_bytes = hash_model_state(model.state_dict()) # Get bytes
            final_model_state_hash_hex = bytes_to_hex(final_model_state_hash_bytes)
            worker_logger.info(f"Final model state hash: {final_model_state_hash_hex[:10]}...")

            worker_logger.info("Calculating Post-Hash...")
            post_hash_value = calculate_post_hash(final_model_state_hash_hex, accuracy, current_total_steps)
            worker_logger.info(f"Calculated Post-Hash: {post_hash_value}")

            worker_logger.info(f"Verifying Post-Hash against T2 threshold: {t2_threshold}")
            is_post_hash_valid = verify_post_hash_threshold(post_hash_value, t2_threshold)

            # --- Decide Action based on Post-Hash and Accuracy --- 
            action = "DISCARD"
            if is_post_hash_valid:
                if accuracy >= t_acc_threshold:
                    action = "SAVE_BLOCK_CHECKPOINT"
                else:
                    action = "SAVE_MTX_CHECKPOINT"
            else:
                action = "DISCARD"

            worker_logger.info(f"Post-Epoch Action Decision: {action} (PostHash Valid: {is_post_hash_valid}, Accuracy: {accuracy:.4f} >= Tacc: {t_acc_threshold:.4f})")
                
            if action in ["SAVE_BLOCK_CHECKPOINT", "SAVE_MTX_CHECKPOINT"]:
                # Build Merkle Tree for this epoch's state (or potentially full history)
                # For simplicity, build based on all hashes collected so far
                leaf_hashes = list(checkpoint_hashes.values())
                merkle_root, _ = build_merkle_tree(leaf_hashes)
                merkle_root_hex = bytes_to_hex(merkle_root)
                worker_logger.info(f"Merkle root for steps up to {current_total_steps}: {merkle_root_hex[:10]}...")

                # --- Save Training Trace & Calculate Hash --- 
                trace_file_path = None
                trace_hash_hex = None
                try:
                    # Use tempfile for trace to handle potential cleanup
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".jsonl", prefix=f"trace_rank{rank}_epoch{epoch}_") as tmp_trace_file:
                        trace_file_path = tmp_trace_file.name
                        # Write trace records as JSON lines
                        for record in training_trace:
                             tmp_trace_file.write(json.dumps(record) + '\n')
                        worker_logger.info(f"Training trace saved locally to {trace_file_path}")
                    
                    # Hash the content of the saved trace file
                    with open(trace_file_path, 'rb') as f_read:
                         trace_bytes = f_read.read()
                         trace_hash_bytes = hash_bytes(trace_bytes)
                         trace_hash_hex = bytes_to_hex(trace_hash_bytes)
                         worker_logger.info(f"Calculated trace hash: {trace_hash_hex[:10]}...")
                except Exception as trace_e:
                    worker_logger.error(f"Failed to save or hash training trace: {trace_e}", exc_info=True)
                    # Decide how to handle: proceed without trace hash or fail?
                    # For now, we proceed without it.
                # --- End Trace Saving/Hashing --- 

                # Collect D-PoDL state for checkpointing (add accuracy explicitly)
                current_dpodl_state = {
                    'prev_block_hash': prev_block_hash, # Explicitly add prev_block_hash
                    'nonce': nonce,
                    'pre_hash_value': pre_hash_value,
                    'reference_model_id': reference_model_id,
                    'random_seed': random_seed,
                    'seed_for_weights': seed_for_weights,
                    't1_threshold': t1_threshold,
                    't2_threshold': t2_threshold,
                    'accuracy': accuracy, # Ensure accuracy is saved
                    't_acc_threshold': t_acc_threshold, # Save threshold used for decision
                    'final_model_state_hash': final_model_state_hash_hex, # Save hex
                    'post_hash_value': post_hash_value,
                    'steps_at_checkpoint': current_total_steps,
                    'merkle_root': merkle_root_hex, # Save hex representation
                    # Save checkpoint hashes (convert bytes back to hex for JSON serialization)
                    'checkpoint_hashes': OrderedDict((str(k), bytes_to_hex(v)) for k, v in checkpoint_hashes.items()),
                    'trace_hash': trace_hash_hex, # Add trace hash
                    'trace_file_path': trace_file_path # Optional: path if needed later (might be temp)
                }
                
                checkpoint_type = "block_candidate" if action == "SAVE_BLOCK_CHECKPOINT" else "model_transaction"
                worker_logger.info(f"Saving checkpoint for {checkpoint_type}...")

                # --- Save Checkpoint (potentially getting IPFS CID) ---
                ipfs_cid = save_checkpoint(
                    epoch + 1, model, optimizer, epoch_loss, 
                    checkpoint_path, 
                    dpodl_state=current_dpodl_state
                )
                worker_logger.info(f"Checkpoint saved. Type: {checkpoint_type}. IPFS CID (if IPFS running): {ipfs_cid}")
                
                # ===>>> Submit Result to Blockchain <<<===
                submission_receipt = None
                if ipfs_cid: # Only submit if we have an IPFS CID for the checkpoint
                    if action == "SAVE_BLOCK_CHECKPOINT":
                        worker_logger.info("Submitting block candidate to ModelRegistry...")
                        # Ensure post_hash_value is int (it's calculated as hex, needs conversion)
                        try:
                            post_hash_int = int(post_hash_value, 16) 
                        except ValueError:
                             worker_logger.error(f"Invalid post_hash_value hex string: {post_hash_value}. Cannot submit.")
                             post_hash_int = None # Indicate error
                             
                        if post_hash_int is not None:
                            submission_receipt = submit_block(
                                ipfs_cid=ipfs_cid,
                                accuracy_bps=int(accuracy * 10000), # Convert accuracy to BPS
                                steps=current_total_steps,
                                post_hash=post_hash_int, # Pass integer post-hash
                                reference_cid=reference_model_id or "", # Use empty string for genesis
                                signer_private_key=worker_private_key
                            )
                    elif action == "SAVE_MTX_CHECKPOINT":
                        worker_logger.info("Submitting model transaction to MTXMempool...")
                        submission_receipt = submit_mtx(
                            ipfs_cid=ipfs_cid,
                            accuracy_bps=int(accuracy * 10000),
                            steps=current_total_steps,
                            reference_cid=reference_model_id or "",
                            signer_private_key=worker_private_key
                        )
                    
                    # Log submission result
                    if submission_receipt:
                        worker_logger.info(f"Blockchain submission SUCCESSFUL for {action}. Tx: {submission_receipt.transactionHash.hex()}")
                    else:
                        worker_logger.error(f"Blockchain submission FAILED for {action} (CID: {ipfs_cid}). Check logs.")
                        # How should failure be handled? Continue? Stop worker?
                        # For now, just log the error.

                else:
                    worker_logger.warning(f"Skipping blockchain submission for {action} because IPFS CID is missing.")
                # ===>>> End Blockchain Submission <<<===
                
                # Clean up trace file if it was temporary and hashing was successful
                if trace_file_path and trace_hash_hex and "tmp" in trace_file_path:
                    try:
                        os.remove(trace_file_path)
                        worker_logger.info(f"Removed temporary trace file: {trace_file_path}")
                    except OSError as rm_e:
                         worker_logger.warning(f"Could not remove temporary trace file {trace_file_path}: {rm_e}")
                         
                # Clear trace for the next epoch/run segment
                # If resuming, trace should ideally be loaded, but this simple version resets.
                training_trace = [] 

            else: # action == "DISCARD"
                worker_logger.warning(f"Post-Hash INVALID for epoch {epoch}. Checkpoint not saved. Continuing training...")

                # Decide if trace should be cleared even if checkpoint not saved
                training_trace = [] 

            # Update total steps for next epoch calculation (only if checkpoint wasn't saved? No, update regardless)
            total_steps_so_far = current_total_steps 
                
    except Exception as e:
        worker_logger.error(f"Worker crashed during training loop: {e}", exc_info=True)
        # Attempt to save trace before potentially saving emergency checkpoint
        emergency_trace_hash_hex = None # Initialize HERE
        emergency_trace_file_path = None # Also initialize path
        try:
             with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".jsonl", prefix=f"emergency_trace_rank{rank}_") as tmp_trace_file:
                 emergency_trace_file_path = tmp_trace_file.name # Assign path
                 for record in training_trace:
                      tmp_trace_file.write(json.dumps(record) + '\n')
                 # trace_file_path = tmp_trace_file.name # Redundant assignment
             with open(emergency_trace_file_path, 'rb') as f_read:
                  trace_hash_bytes = hash_bytes(f_read.read())
                  emergency_trace_hash_hex = bytes_to_hex(trace_hash_bytes)
             worker_logger.info(f"Saved emergency trace to {emergency_trace_file_path}, hash: {emergency_trace_hash_hex[:10]}...")
        except Exception as trace_e:
             worker_logger.error(f"Failed to save or hash emergency trace: {trace_e}")

        # --- Save Emergency Checkpoint --- 
        try:
            current_epoch = epoch if 'epoch' in locals() else start_epoch
            # Build Merkle Tree from current hashes
            leaf_hashes = list(checkpoint_hashes.values())
            merkle_root, _ = build_merkle_tree(leaf_hashes)
            merkle_root_hex = bytes_to_hex(merkle_root)

            emergency_dpodl_state = {
                'prev_block_hash': prev_block_hash, # Explicitly add prev_block_hash
                'nonce': nonce,
                'pre_hash_value': pre_hash_value,
                'reference_model_id': reference_model_id,
                'random_seed': random_seed,
                'seed_for_weights': seed_for_weights,
                't1_threshold': t1_threshold,
                't2_threshold': t2_threshold,
                'steps_at_checkpoint': total_steps_so_far + steps_this_run, # Best estimate
                'merkle_root': merkle_root_hex,
                'checkpoint_hashes': OrderedDict((str(k), bytes_to_hex(v)) for k, v in checkpoint_hashes.items()),
                'trace_hash': emergency_trace_hash_hex, # Add trace hash if available
                'trace_file_path': emergency_trace_file_path # Add trace path if available
            }
            emergency_cid = save_checkpoint(current_epoch, model, optimizer, epoch_loss,
                                          f"emergency_{checkpoint_path}", dpodl_state=emergency_dpodl_state)
            worker_logger.info(f"Emergency checkpoint saved. IPFS CID (if IPFS running): {emergency_cid}")
            # Clean up emergency trace file only if checkpoint saving succeeded
            if emergency_trace_file_path and os.path.exists(emergency_trace_file_path):
                 try:
                     os.remove(emergency_trace_file_path)
                     worker_logger.info(f"Removed emergency trace file: {emergency_trace_file_path}")
                 except OSError as rm_e:
                      worker_logger.warning(f"Could not remove emergency trace file {emergency_trace_file_path}: {rm_e}")
        except Exception as save_e:
             worker_logger.error(f"Failed to save emergency checkpoint: {save_e}")
        raise # Re-raise the original exception that caused the crash

    worker_logger.info(f"Training complete.")
