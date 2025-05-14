# dpodl_core/verification.py
import logging
from collections import OrderedDict
from .crypto import (
    build_merkle_tree,
    get_merkle_proof,
    verify_merkle_proof,
    bytes_to_hex,
    calculate_pre_hash,
    verify_pre_hash_threshold, # Added for consistency check
    extract_seed_from_hash,   # Added for consistency check
    calculate_post_hash,
    verify_post_hash_threshold, # Added for consistency check
    hash_bytes # Added for empty tree check
)
# Import load_checkpoint at top level for consistency
from .utils import load_checkpoint

logger = logging.getLogger(__name__)
# Basic config if run standalone or not configured globally
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- Merkle Proof Generation ---

def generate_merkle_proof_for_step(
    target_step: int,
    checkpoint_hashes: OrderedDict[int, bytes]
) -> list[tuple[bytes, bool]] | None:
    """
    Generates a Merkle proof for a specific checkpoint step hash.

    Args:
        target_step: The step number whose hash we need the proof for.
        checkpoint_hashes: An OrderedDict mapping step numbers (int) to their
                           model state hashes (bytes). The order must be the
                           order used to originally build the tree.

    Returns:
        A Merkle proof list [(sibling_hash_bytes, is_right_sibling), ...],
        or None if the step is not found or tree generation fails.
    """
    if not isinstance(checkpoint_hashes, OrderedDict):
        logger.error("checkpoint_hashes must be an OrderedDict.")
        return None
    if not checkpoint_hashes:
        logger.warning("Cannot generate proof for empty checkpoint_hashes.")
        return None

    leaf_hashes = list(checkpoint_hashes.values())
    leaf_keys = list(checkpoint_hashes.keys())

    if target_step not in leaf_keys:
        logger.error(f"Target step {target_step} not found in checkpoint hash keys: {leaf_keys}")
        return None

    try:
        leaf_index = leaf_keys.index(target_step)
    except ValueError:
         # Should not happen due to the check above, but as safety
         logger.error(f"Internal error: Failed to find index for target step {target_step} despite key check.")
         return None

    # Rebuild the tree to get levels.
    # Optimization: If tree levels were stored alongside the root,
    # this rebuild could be avoided. For now, we rebuild.
    merkle_root_bytes, tree_levels = build_merkle_tree(leaf_hashes)

    if not tree_levels or merkle_root_bytes is None:
        logger.error("Failed to build Merkle tree for proof generation.")
        return None

    proof = get_merkle_proof(leaf_index, tree_levels)
    logger.info(f"Generated Merkle proof for step {target_step} (leaf index {leaf_index}) with {len(proof)} elements.")
    return proof

# --- Merkle Proof Verification ---

def verify_checkpoint_merkle_proof(
    target_step: int,
    target_hash_hex: str,
    proof_hex: list[tuple[str, bool]], # Proof with hex hashes
    expected_root_hex: str,
    all_checkpoint_keys: list[int] # All step keys in original order
) -> bool:
    """
    Verifies a Merkle proof for a specific checkpoint hash against a known root hash.

    Args:
        target_step: The step number being verified.
        target_hash_hex: The claimed hash (hex) of the model state at target_step.
        proof_hex: The Merkle proof path, with sibling hashes as hex strings.
        expected_root_hex: The expected Merkle root hash (hex) stored previously.
        all_checkpoint_keys: List of all step keys (int) in the exact order
                             they appeared when the original tree was built.
                             Needed to determine the correct leaf_index.

    Returns:
        True if the proof is valid and reconstructs the expected root, False otherwise.
    """
    if not all_checkpoint_keys:
         logger.error("Cannot verify proof: all_checkpoint_keys list is empty.")
         return False

    try:
        target_hash_bytes = bytes.fromhex(target_hash_hex)
        expected_root_bytes = bytes.fromhex(expected_root_hex)
        proof_bytes = [(bytes.fromhex(h_hex), is_right) for h_hex, is_right in proof_hex]
    except ValueError as e:
        logger.error(f"Invalid hex string provided during conversion for verification: {e}")
        return False
    except TypeError as e:
        logger.error(f"Invalid proof format provided: {e}")
        return False

    try:
        # We need the original index to verify correctly, especially with padding.
        leaf_index = all_checkpoint_keys.index(target_step)
    except ValueError:
        logger.error(f"Target step {target_step} not found in the provided list of all checkpoint keys.")
        return False

    # Perform the cryptographic verification
    is_valid = verify_merkle_proof(target_hash_bytes, leaf_index, proof_bytes, expected_root_bytes)

    logger.info(f"Merkle proof verification result for step {target_step}: {'VALID' if is_valid else 'INVALID'}")
    return is_valid

# --- D-PoDL State Consistency Verification ---

def verify_proof_of_training_consistency(dpodl_state: dict) -> bool:
    """
    Performs comprehensive internal consistency checks on a loaded D-PoDL state
    dictionary, typically loaded from a checkpoint.

    Checks include:
    - Presence of essential keys.
    - Consistency of Pre-Hash, Post-Hash, Seeds, Merkle Root.
    - Validity against T1 and T2 thresholds.

    Args:
        dpodl_state: The dictionary loaded from a checkpoint's 'dpodl_state'.

    Returns:
        True if all consistency checks pass, False otherwise.
    """
    if not isinstance(dpodl_state, dict) or not dpodl_state:
        logger.error("Cannot verify consistency: Invalid or empty dpodl_state provided.")
        return False

    logger.info("Starting D-PoDL state consistency verification...")
    checks_passed = True
    missing_keys = []

    # --- Check 1: Presence of essential keys ---
    # These keys are crucial for the other checks.
    required_keys = [
        'prev_block_hash', 'nonce', 'reference_model_id', # For Pre-Hash
        'pre_hash_value', 't1_threshold', 'random_seed',  # Pre-Hash results & params
        'accuracy', 'steps_at_checkpoint', 'final_model_state_hash', # For Post-Hash
        'post_hash_value', 't2_threshold', # Post-Hash results & params
        'checkpoint_hashes', 'merkle_root' # Merkleization results
        # 'seed_for_weights' might also be essential depending on usage
        # 'trace_hash', 'trace_file_path' are optional but useful if present
    ]
    for key in required_keys:
        if key not in dpodl_state:
            missing_keys.append(key)

    if missing_keys:
        logger.error(f"Consistency check FAILED: D-PoDL state missing required keys: {missing_keys}")
        # Cannot proceed reliably without these keys.
        return False
    logger.debug("Check 1 Passed: All essential keys present.")

    # --- Check 2: Pre-Hash recalculation and T1 Verification ---
    try:
        prev_bk = dpodl_state['prev_block_hash']
        ref_id = dpodl_state['reference_model_id'] # Can be None
        nonce = dpodl_state['nonce']
        pre_hash_stored = dpodl_state['pre_hash_value']
        t1 = dpodl_state['t1_threshold']

        # Recalculate
        pre_hash_calculated = calculate_pre_hash(prev_bk, ref_id, nonce)

        if pre_hash_calculated != pre_hash_stored:
            logger.error(f"Consistency check FAILED: Pre-Hash mismatch! "
                         f"Stored: {pre_hash_stored}, Recalculated: {pre_hash_calculated} "
                         f"(Inputs: prevBK='{prev_bk}', refM='{ref_id}', nonce={nonce})")
            checks_passed = False
        else:
            logger.debug("Check 2a Passed: Pre-Hash recalculation consistent.")

            # Verify against T1 only if recalculation passed
            if not verify_pre_hash_threshold(pre_hash_calculated, t1):
                 logger.error(f"Consistency check FAILED: Stored Pre-Hash {pre_hash_calculated} does not meet T1 threshold {t1}.")
                 checks_passed = False
            else:
                 logger.debug("Check 2b Passed: Pre-Hash meets T1 threshold.")

    except Exception as e:
        logger.error(f"Consistency check FAILED: Error during Pre-Hash/T1 check: {e}", exc_info=True)
        checks_passed = False

    # --- Check 3: Seed recalculation ---
    # This checks if the random_seed matches the one derived from the pre_hash
    try:
        seed_stored = dpodl_state['random_seed']
        pre_hash_stored = dpodl_state['pre_hash_value'] # Use the stored one

        # Recalculate
        seed_calculated = extract_seed_from_hash(pre_hash_stored)

        if seed_calculated != seed_stored:
            logger.error(f"Consistency check FAILED: Random Seed mismatch! "
                         f"Stored: {seed_stored}, Recalculated: {seed_calculated} "
                         f"(From Pre-Hash: {pre_hash_stored})")
            checks_passed = False
        else:
            logger.debug("Check 3 Passed: Random seed consistent with Pre-Hash.")
    except Exception as e:
        logger.error(f"Consistency check FAILED: Error during Seed check: {e}", exc_info=True)
        checks_passed = False

    # --- Check 4: Post-Hash recalculation and T2 Verification ---
    try:
        final_hash = dpodl_state['final_model_state_hash']
        accuracy = dpodl_state['accuracy']
        steps = dpodl_state['steps_at_checkpoint']
        post_hash_stored = dpodl_state['post_hash_value']
        t2 = dpodl_state['t2_threshold']

        # Recalculate
        post_hash_calculated = calculate_post_hash(final_hash, accuracy, steps)

        if post_hash_calculated != post_hash_stored:
            logger.error(f"Consistency check FAILED: Post-Hash mismatch! "
                         f"Stored: {post_hash_stored}, Recalculated: {post_hash_calculated} "
                         f"(Inputs: final_hash='{final_hash[:10]}...', acc={accuracy}, steps={steps})")
            checks_passed = False
        else:
             logger.debug("Check 4a Passed: Post-Hash recalculation consistent.")

             # Verify against T2 only if recalculation passed
             if not verify_post_hash_threshold(post_hash_calculated, t2):
                  logger.error(f"Consistency check FAILED: Stored Post-Hash {post_hash_calculated} does not meet T2 threshold {t2}.")
                  checks_passed = False
             else:
                  logger.debug("Check 4b Passed: Post-Hash meets T2 threshold.")

    except KeyError as e:
        logger.error(f"Consistency check FAILED: Missing key required for Post-Hash/T2 check: {e}")
        checks_passed = False
    except Exception as e:
        logger.error(f"Consistency check FAILED: Error during Post-Hash/T2 check: {e}", exc_info=True)
        checks_passed = False

    # --- Check 5: Merkle Root recalculation ---
    try:
        stored_hashes_map = dpodl_state.get('checkpoint_hashes', {})
        stored_merkle_root = dpodl_state['merkle_root']
        expected_empty_root_hex = bytes_to_hex(hash_bytes(b'')) # Precompute for clarity

        if not isinstance(stored_hashes_map, (dict, OrderedDict)):
             logger.error(f"Consistency check FAILED: checkpoint_hashes is not a dictionary/OrderedDict.")
             checks_passed = False
        elif not stored_hashes_map:
             logger.warning("Checkpoint hashes dictionary is empty.")
             if stored_merkle_root != expected_empty_root_hex:
                 logger.error(f"Consistency check FAILED: Merkle root ({stored_merkle_root}) is non-empty but checkpoint hashes are empty (expected empty root: {expected_empty_root_hex}).")
                 checks_passed = False
             else:
                  logger.debug("Check 5 Passed: Merkle Root consistent (empty tree).")
        else:
            # Convert keys to int, sort, then get corresponding hex values and convert to bytes
            leaf_hashes_bytes = []
            conversion_error = False
            try:
                # Sort keys numerically to ensure deterministic order
                sorted_step_keys = sorted([int(k) for k in stored_hashes_map.keys()])
                for step_key in sorted_step_keys:
                    step_str = str(step_key) # Get original string key
                    hash_hex = stored_hashes_map[step_str]
                    leaf_hashes_bytes.append(bytes.fromhex(hash_hex))
            except (ValueError, TypeError, KeyError) as conv_err:
                 logger.error(f"Consistency check FAILED: Invalid format in checkpoint_hashes state: {conv_err}")
                 checks_passed = False
                 conversion_error = True

            if not conversion_error:
                # Rebuild the tree only if conversion succeeded
                recalculated_root_bytes, _ = build_merkle_tree(leaf_hashes_bytes)
                recalculated_root_hex = bytes_to_hex(recalculated_root_bytes)

                if recalculated_root_hex != stored_merkle_root:
                    logger.error(f"Consistency check FAILED: Merkle Root mismatch! "
                                 f"Stored: {stored_merkle_root}, Recalculated: {recalculated_root_hex}")
                    checks_passed = False
                else:
                     logger.debug("Check 5 Passed: Merkle Root recalculation consistent.")

    except Exception as e:
        logger.error(f"Consistency check FAILED: Error during Merkle Root check: {e}", exc_info=True)
        checks_passed = False

    # --- Check 6: Trace Hash Verification (Placeholder) ---
    # if 'trace_hash' in dpodl_state and dpodl_state['trace_hash'] is not None:
    #     logger.debug("Trace hash found in state.")
    #     # To verify this fully, we'd need:
    #     # 1. The trace file itself (e.g., retrieve via CID stored in dpodl_state['trace_file_path'] if it's an IPFS CID)
    #     # 2. Read the file content.
    #     # 3. Hash the content using hash_bytes().
    #     # 4. Compare bytes_to_hex(calculated_trace_hash) with dpodl_state['trace_hash'].
    #     # This requires I/O and potentially network access (IPFS), which is
    #     # beyond the scope of this internal consistency check function.
    #     # This verification should happen at a higher level that can handle retrieval.
    #     logger.warning("Trace hash verification requires external trace file retrieval - Skipping in this function.")


    # --- Final Result ---
    logger.info(f"D-PoDL State Consistency Verification Result: {'PASSED' if checks_passed else 'FAILED'}")
    return checks_passed

# --- Helper to load state and verify ---
# Example of how verification might be called externally
def load_and_verify_checkpoint_state(checkpoint_path: str) -> bool:
    """
    Loads a checkpoint and runs consistency checks on its D-PoDL state.
    (Assumes load_checkpoint is imported at the top level).

    Args:
        checkpoint_path: Path to the checkpoint file.

    Returns:
        True if loading succeeds and the state is consistent, False otherwise.
    """
    # Import locally to avoid circular dependencies if utils ever imports verification
    # from .utils import load_checkpoint # Moved to top level
    
    dpodl_state = {}
    try:
        # We only need the state, pass None for model/optimizer
        start_epoch, loss, dpodl_state = load_checkpoint(checkpoint_path, model=None, optimizer=None)
        if not dpodl_state:
             logger.warning(f"No D-PoDL state found in checkpoint {checkpoint_path} during verification load.")
             # Consider if this should be a failure or if empty state is verifiable (verify_proof_of_training_consistency handles empty dict)

    except FileNotFoundError:
        logger.error(f"Checkpoint file not found at {checkpoint_path}")
        return False
    except Exception as e:
        logger.error(f"Failed to load checkpoint {checkpoint_path} for verification: {e}", exc_info=True)
        return False

    # Proceed to verify the loaded state (handles empty dict case)
    return verify_proof_of_training_consistency(dpodl_state) 