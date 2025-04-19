# dpodl_core/verification.py

import logging
from collections import OrderedDict

from .crypto import (
    build_merkle_tree,
    get_merkle_proof,
    verify_merkle_proof,
    bytes_to_hex,
    hash_bytes, # Potentially needed for leaf hash if not passed directly
    verify_pre_hash_threshold,
    verify_post_hash_threshold,
    extract_seed_from_hash,
    hash_to_architecture,
    calculate_post_hash
)

logger = logging.getLogger(__name__)

def generate_merkle_proof_for_step(step_number: int, checkpoint_hashes_hex: OrderedDict[str, str]) -> list[tuple[bytes, bool]] | None:
    """
    Generates a Merkle proof for a specific training step using the stored checkpoint hashes.

    Args:
        step_number: The training step number for which to generate the proof.
        checkpoint_hashes_hex: An OrderedDict mapping step number (str) to checkpoint hash (hex str),
                               as stored in the D-PoDL state.

    Returns:
        The Merkle proof (list of tuples(sibling_hash_bytes, is_right_sibling)),
        or None if the step is not found or an error occurs.
    """
    logger.info(f"Attempting to generate Merkle proof for step {step_number}.")

    if not checkpoint_hashes_hex:
        logger.warning("Checkpoint hashes dictionary is empty.")
        return None

    # Ensure keys are integers for sorting and lookup, and convert hex values to bytes
    try:
        checkpoint_hashes_bytes = OrderedDict(
            (int(k), bytes.fromhex(v)) for k, v in checkpoint_hashes_hex.items()
        )
    except ValueError as e:
        logger.error(f"Error converting checkpoint hashes: {e}")
        return None

    # Sort steps to determine the leaf index
    sorted_steps = sorted(checkpoint_hashes_bytes.keys())

    try:
        leaf_index = sorted_steps.index(step_number)
    except ValueError:
        logger.warning(f"Step {step_number} not found in the provided checkpoint hashes {sorted_steps}.")
        return None

    leaf_hashes = list(checkpoint_hashes_bytes.values())

    if not leaf_hashes:
        logger.warning("No leaf hashes found after processing.")
        return None

    # Rebuild the Merkle tree to get all levels
    try:
        _merkle_root, tree_levels = build_merkle_tree(leaf_hashes) # We only need tree_levels here
    except Exception as e:
        logger.error(f"Error building Merkle tree for proof generation: {e}", exc_info=True)
        return None

    # Generate the proof
    try:
        proof = get_merkle_proof(leaf_index, tree_levels)
        logger.info(f"Successfully generated Merkle proof for step {step_number} at index {leaf_index}.")
        return proof
    except Exception as e:
        logger.error(f"Error generating Merkle proof: {e}", exc_info=True)
        return None

def verify_checkpoint_merkle_proof(
    step_number: int,
    checkpoint_hash_hex: str,
    proof: list[tuple[bytes, bool]],
    expected_merkle_root_hex: str,
    all_checkpoint_hashes_hex: OrderedDict[str, str]
) -> bool:
    """
    Verifies a Merkle proof for a specific checkpoint against an expected root.

    Args:
        step_number: The step number of the checkpoint being verified.
        checkpoint_hash_hex: The hash (hex string) of the specific checkpoint (the leaf).
        proof: The Merkle proof path obtained externally (e.g., via generate_merkle_proof_for_step).
        expected_merkle_root_hex: The expected Merkle root hash (hex string).
        all_checkpoint_hashes_hex: The full OrderedDict of step->hash (hex) used to build the original tree.
                                    Needed to determine the leaf index correctly.

    Returns:
        True if the proof is valid, False otherwise.
    """
    logger.info(f"Verifying Merkle proof for step {step_number} against root {expected_merkle_root_hex[:10]}...")

    if not all_checkpoint_hashes_hex:
        logger.warning("Full checkpoint hashes dictionary is empty for index determination.")
        return False

    # Determine leaf index from the full set
    try:
        # Convert keys to int for sorting
        sorted_steps = sorted([int(k) for k in all_checkpoint_hashes_hex.keys()])
        leaf_index = sorted_steps.index(step_number)
    except ValueError:
        logger.warning(f"Step {step_number} not found in the full checkpoint hashes; cannot determine leaf index.")
        return False
    except Exception as e:
        logger.error(f"Error determining leaf index: {e}")
        return False

    # Convert necessary hex strings to bytes
    try:
        leaf_hash_bytes = bytes.fromhex(checkpoint_hash_hex)
        root_hash_bytes = bytes.fromhex(expected_merkle_root_hex)
    except ValueError as e:
        logger.error(f"Error converting hex strings (leaf/root) to bytes: {e}")
        return False

    # Perform the verification
    try:
        is_valid = verify_merkle_proof(leaf_hash_bytes, leaf_index, proof, root_hash_bytes)
        logger.info(f"Merkle proof verification result for step {step_number}: {is_valid}")
        return is_valid
    except Exception as e:
        logger.error(f"Error during Merkle proof verification: {e}", exc_info=True)
        return False

# --- Proof of Training Verification --- #

def verify_proof_of_training_consistency(dpodl_state: dict) -> bool:
    """
    Performs internal consistency checks on a loaded D-PoDL state dictionary.
    This verifies relationships between hashes, seeds, thresholds, and other metadata
    based on the D-PoDL rules.

    Note: This does NOT verify the Merkle root against external checkpoints or
          the trace hash against an external trace file. Those are separate steps.

    Args:
        dpodl_state: The dictionary loaded from a checkpoint's 'dpodl_state'.

    Returns:
        True if all internal consistency checks pass, False otherwise.
    """
    logger.info("Performing internal consistency checks on D-PoDL state...")
    checks_passed = True

    required_keys = [
        'pre_hash_value', 't1_threshold', 'post_hash_value', 't2_threshold',
        'random_seed', 'seed_for_weights', 'final_model_state_hash',
        'accuracy', 'steps_at_checkpoint'
    ]
    for key in required_keys:
        if key not in dpodl_state or dpodl_state[key] is None:
            logger.error(f"Missing or None value for required key '{key}' in dpodl_state.")
            return False # Cannot perform checks without essential keys

    # Extract values for clarity
    pre_hash = dpodl_state['pre_hash_value']
    t1 = dpodl_state['t1_threshold']
    post_hash = dpodl_state['post_hash_value']
    t2 = dpodl_state['t2_threshold']
    stored_random_seed = dpodl_state['random_seed']
    stored_weight_seed = dpodl_state['seed_for_weights']
    final_model_hash = dpodl_state['final_model_state_hash']
    accuracy = dpodl_state['accuracy']
    steps = dpodl_state['steps_at_checkpoint']

    # 1. Check Pre-Hash against T1
    if not verify_pre_hash_threshold(pre_hash, t1):
        logger.warning(f"Check Failed: Pre-Hash {pre_hash[:10]}... does not meet threshold T1 ({t1}).")
        checks_passed = False
    else:
        logger.info("Check Passed: Pre-Hash meets T1.")

    # 2. Check Post-Hash against T2
    if not verify_post_hash_threshold(post_hash, t2):
        logger.warning(f"Check Failed: Post-Hash {post_hash[:10]}... does not meet threshold T2 ({t2}).")
        checks_passed = False
    else:
        logger.info("Check Passed: Post-Hash meets T2.")

    # 3. Verify random_seed derived from pre_hash
    try:
        derived_random_seed = extract_seed_from_hash(pre_hash)
        if derived_random_seed != stored_random_seed:
            logger.warning(f"Check Failed: Stored random_seed ({stored_random_seed}) does not match seed derived from pre_hash ({derived_random_seed}).")
            checks_passed = False
        else:
            logger.info("Check Passed: Stored random_seed matches derived seed.")
    except Exception as e:
        logger.error(f"Error deriving random_seed from pre_hash: {e}")
        checks_passed = False

    # 4. Verify seed_for_weights derived from pre_hash (via HtoA)
    try:
        derived_htoA = hash_to_architecture(pre_hash)
        derived_weight_seed = derived_htoA['seed_for_weights']
        if derived_weight_seed != stored_weight_seed:
            logger.warning(f"Check Failed: Stored seed_for_weights ({stored_weight_seed}) does not match seed derived from HtoA ({derived_weight_seed}).")
            checks_passed = False
        else:
            logger.info("Check Passed: Stored seed_for_weights matches HtoA derived seed.")
    except ValueError as e:
        logger.error(f"Error deriving HtoA (invalid pre_hash length?): {e}")
        checks_passed = False
    except Exception as e:
        logger.error(f"Error deriving HtoA from pre_hash: {e}")
        checks_passed = False

    # 5. Verify post_hash derived from components
    try:
        derived_post_hash = calculate_post_hash(final_model_hash, accuracy, steps)
        if derived_post_hash != post_hash:
            logger.warning(f"Check Failed: Stored post_hash ({post_hash[:10]}...) does not match hash derived from components ({derived_post_hash[:10]}...).")
            checks_passed = False
        else:
            logger.info("Check Passed: Stored post_hash matches derived post_hash.")
    except Exception as e:
        logger.error(f"Error deriving post_hash from components: {e}")
        checks_passed = False

    logger.info(f"D-PoDL state internal consistency check result: {checks_passed}")
    return checks_passed 