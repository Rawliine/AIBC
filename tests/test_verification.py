# tests/test_verification.py

import pytest
from collections import OrderedDict

# Assuming your main code is structured correctly for relative imports
from dpodl_core.crypto import hash_bytes, build_merkle_tree, bytes_to_hex, calculate_pre_hash, extract_seed_from_hash, hash_to_architecture, calculate_post_hash, hash_model_state
from dpodl_core.verification import (
    generate_merkle_proof_for_step,
    verify_checkpoint_merkle_proof,
    verify_proof_of_training_consistency
)

# --- Fixtures ---

@pytest.fixture
def sample_checkpoint_hashes() -> OrderedDict[int, bytes]:
    """Generates sample checkpoint hashes (bytes) keyed by step number (int)."""
    hashes = OrderedDict()
    hashes[0] = hash_bytes(b'initial_state') # Step 0 for initial
    hashes[100] = hash_bytes(b'checkpoint_100')
    hashes[200] = hash_bytes(b'checkpoint_200')
    hashes[300] = hash_bytes(b'checkpoint_300')
    hashes[350] = hash_bytes(b'checkpoint_350') # Non-regular interval
    return hashes

@pytest.fixture
def sample_checkpoint_hashes_hex(sample_checkpoint_hashes) -> OrderedDict[str, str]:
    """Converts sample hashes to hex strings keyed by string step numbers."""
    return OrderedDict((str(k), bytes_to_hex(v)) for k, v in sample_checkpoint_hashes.items())

@pytest.fixture
def sample_merkle_root_hex(sample_checkpoint_hashes) -> str:
    """Calculates the Merkle root for the sample hashes."""
    leaf_hashes = list(sample_checkpoint_hashes.values())
    root, _ = build_merkle_tree(leaf_hashes)
    return bytes_to_hex(root)

@pytest.fixture
def valid_dpodl_state() -> dict:
    """Creates a sample valid D-PoDL state dictionary for testing,
       ensuring generated hashes meet non-maximal thresholds."""
    # Re-import necessary functions locally within the fixture scope just in case
    from dpodl_core.crypto import (
        calculate_pre_hash, verify_pre_hash_threshold, extract_seed_from_hash,
        hash_to_architecture, calculate_post_hash, verify_post_hash_threshold,
        hash_bytes, bytes_to_hex, build_merkle_tree
    )

    # Consistent values
    prev_block = "0x" + "a"*64
    ref_id = None
    # Set reasonably difficult, non-maximal thresholds
    t1 = 2**248 # Easier threshold, likely to find nonce quickly
    t2 = 2**250 # Easier threshold, likely for post-hash adjustment to succeed
    initial_accuracy = 0.925
    initial_steps = 350 # Start near the last step in sample_checkpoint_hashes

    # 1. Find a nonce that satisfies T1 (Mimic Pre-Hash mining)
    nonce = 0
    pre_hash = None
    max_nonce_attempts = 10000 # Limit search
    found_pre_hash = False
    for i in range(max_nonce_attempts):
        nonce = i
        calculated_hash = calculate_pre_hash(prev_block, ref_id, nonce)
        if verify_pre_hash_threshold(calculated_hash, t1):
            pre_hash = calculated_hash
            found_pre_hash = True
            break
    if not found_pre_hash:
        pytest.fail(f"Could not find nonce satisfying T1={t1} within {max_nonce_attempts} attempts")

    # 2. Derive seeds from the valid pre_hash
    random_seed = extract_seed_from_hash(pre_hash)
    htoA_result = hash_to_architecture(pre_hash)
    weight_seed = htoA_result['seed_for_weights']

    # 3. Calculate Post-Hash based on initial parameters
    # Use a dummy model hash for consistency check
    final_model_hash_bytes = hash_bytes(b"final_model_state_dummy")
    final_model_hash_hex = bytes_to_hex(final_model_hash_bytes)

    accuracy = initial_accuracy
    steps = initial_steps # Use the initial steps
    post_hash = calculate_post_hash(final_model_hash_hex, accuracy, steps)

    # 4. Set T2 threshold to ensure the calculated post_hash passes
    #    (Add a small buffer just in case, though direct equality is fine)
    t2 = int(post_hash, 16) + 1000

    # Merkle root and trace hash are not checked by this specific function,
    # but included for completeness of a typical state object.
    # Using sample_checkpoint_hashes fixture logic here
    _hashes = OrderedDict()
    _hashes[0] = hash_bytes(b'initial_state')
    _hashes[100] = hash_bytes(b'checkpoint_100')
    _hashes[200] = hash_bytes(b'checkpoint_200')
    _hashes[300] = hash_bytes(b'checkpoint_300')
    _hashes[350] = hash_bytes(b'checkpoint_350')
    _root, _ = build_merkle_tree(list(_hashes.values()))
    merkle_root_hex = bytes_to_hex(_root)
    checkpoint_hashes_hex = OrderedDict((str(k), bytes_to_hex(v)) for k, v in _hashes.items())
    trace_hash_hex = bytes_to_hex(hash_bytes(b'dummy_trace_content'))

    state = {
        'pre_hash_value': pre_hash,
        'nonce': nonce,
        'reference_model_id': ref_id,
        't1_threshold': t1,
        'random_seed': random_seed,
        'seed_for_weights': weight_seed,
        'final_model_state_hash': final_model_hash_hex,
        'accuracy': accuracy,
        'steps_at_checkpoint': steps,
        'post_hash_value': post_hash,
        't2_threshold': t2,
        'merkle_root': merkle_root_hex,
        'checkpoint_hashes': checkpoint_hashes_hex,
        'trace_hash': trace_hash_hex,
    }
    return state

# --- Test Merkle Proof Generation ---

def test_generate_merkle_proof_valid(sample_checkpoint_hashes_hex, sample_merkle_root_hex):
    """Tests generating a proof for a valid, existing step."""
    step_to_prove = 200
    proof = generate_merkle_proof_for_step(step_to_prove, sample_checkpoint_hashes_hex)

    assert proof is not None
    assert isinstance(proof, list)
    # Verify the generated proof using the verification function
    checkpoint_hash_hex = sample_checkpoint_hashes_hex[str(step_to_prove)]
    assert verify_checkpoint_merkle_proof(
        step_to_prove,
        checkpoint_hash_hex,
        proof,
        sample_merkle_root_hex,
        sample_checkpoint_hashes_hex
    )

def test_generate_merkle_proof_step_zero(sample_checkpoint_hashes_hex, sample_merkle_root_hex):
    """Tests generating a proof for step 0."""
    step_to_prove = 0
    proof = generate_merkle_proof_for_step(step_to_prove, sample_checkpoint_hashes_hex)
    assert proof is not None
    checkpoint_hash_hex = sample_checkpoint_hashes_hex[str(step_to_prove)]
    assert verify_checkpoint_merkle_proof(
        step_to_prove, checkpoint_hash_hex, proof, sample_merkle_root_hex, sample_checkpoint_hashes_hex
    )

def test_generate_merkle_proof_last_step(sample_checkpoint_hashes_hex, sample_merkle_root_hex):
    """Tests generating a proof for the last step."""
    step_to_prove = 350
    proof = generate_merkle_proof_for_step(step_to_prove, sample_checkpoint_hashes_hex)
    assert proof is not None
    checkpoint_hash_hex = sample_checkpoint_hashes_hex[str(step_to_prove)]
    assert verify_checkpoint_merkle_proof(
        step_to_prove, checkpoint_hash_hex, proof, sample_merkle_root_hex, sample_checkpoint_hashes_hex
    )

def test_generate_merkle_proof_step_not_found(sample_checkpoint_hashes_hex):
    """Tests generating proof for a step not present in the hashes."""
    step_to_prove = 150
    proof = generate_merkle_proof_for_step(step_to_prove, sample_checkpoint_hashes_hex)
    assert proof is None

def test_generate_merkle_proof_empty_hashes():
    """Tests generating proof with an empty hash dictionary."""
    proof = generate_merkle_proof_for_step(100, OrderedDict())
    assert proof is None

def test_generate_merkle_proof_invalid_hex(sample_checkpoint_hashes_hex):
    """Tests generating proof when dict contains invalid hex."""
    invalid_hashes = sample_checkpoint_hashes_hex.copy()
    invalid_hashes['100'] = "invalid-hex-string"
    proof = generate_merkle_proof_for_step(100, invalid_hashes)
    assert proof is None

# --- Test Merkle Proof Verification ---

def test_verify_merkle_proof_valid(sample_checkpoint_hashes_hex, sample_merkle_root_hex):
    """Tests verification with a valid proof (generated internally)."""
    step_to_verify = 100
    checkpoint_hash_hex = sample_checkpoint_hashes_hex[str(step_to_verify)]
    # Generate the proof first
    proof = generate_merkle_proof_for_step(step_to_verify, sample_checkpoint_hashes_hex)
    assert proof is not None

    is_valid = verify_checkpoint_merkle_proof(
        step_to_verify,
        checkpoint_hash_hex,
        proof,
        sample_merkle_root_hex,
        sample_checkpoint_hashes_hex
    )
    assert is_valid

def test_verify_merkle_proof_invalid_root(sample_checkpoint_hashes_hex):
    """Tests verification fails with an incorrect Merkle root."""
    step_to_verify = 200
    checkpoint_hash_hex = sample_checkpoint_hashes_hex[str(step_to_verify)]
    proof = generate_merkle_proof_for_step(step_to_verify, sample_checkpoint_hashes_hex)
    assert proof is not None
    invalid_root_hex = bytes_to_hex(hash_bytes(b'invalid root'))

    is_valid = verify_checkpoint_merkle_proof(
        step_to_verify,
        checkpoint_hash_hex,
        proof,
        invalid_root_hex,
        sample_checkpoint_hashes_hex
    )
    assert not is_valid

def test_verify_merkle_proof_invalid_leaf(sample_checkpoint_hashes_hex, sample_merkle_root_hex):
    """Tests verification fails with an incorrect leaf hash."""
    step_to_verify = 300
    invalid_checkpoint_hash_hex = bytes_to_hex(hash_bytes(b'wrong checkpoint'))
    proof = generate_merkle_proof_for_step(step_to_verify, sample_checkpoint_hashes_hex)
    assert proof is not None

    is_valid = verify_checkpoint_merkle_proof(
        step_to_verify,
        invalid_checkpoint_hash_hex,
        proof,
        sample_merkle_root_hex,
        sample_checkpoint_hashes_hex
    )
    assert not is_valid

def test_verify_merkle_proof_tampered_proof(sample_checkpoint_hashes_hex, sample_merkle_root_hex):
    """Tests verification fails with a tampered proof."""
    step_to_verify = 0
    checkpoint_hash_hex = sample_checkpoint_hashes_hex[str(step_to_verify)]
    proof = generate_merkle_proof_for_step(step_to_verify, sample_checkpoint_hashes_hex)
    assert proof is not None

    if not proof: # Skip if proof is empty (e.g., single leaf tree)
        pytest.skip("Proof is empty, cannot tamper")

    # Tamper: change one hash in the proof
    tampered_proof = proof[:-1] + [(hash_bytes(b'tampered'), proof[-1][1])]

    is_valid = verify_checkpoint_merkle_proof(
        step_to_verify,
        checkpoint_hash_hex,
        tampered_proof,
        sample_merkle_root_hex,
        sample_checkpoint_hashes_hex
    )
    assert not is_valid

def test_verify_merkle_proof_step_not_in_all_hashes(sample_checkpoint_hashes_hex, sample_merkle_root_hex):
    """Tests verification fails if step number isn't in the provided full hash list (for index calc)."""
    step_to_verify = 100 # This step *is* in the hash list
    checkpoint_hash_hex = sample_checkpoint_hashes_hex[str(step_to_verify)]
    proof = generate_merkle_proof_for_step(step_to_verify, sample_checkpoint_hashes_hex)
    assert proof is not None

    # Create a partial hash list that's missing the step we need for index calc
    partial_hashes = sample_checkpoint_hashes_hex.copy()
    del partial_hashes[str(step_to_verify)]

    is_valid = verify_checkpoint_merkle_proof(
        step_to_verify,
        checkpoint_hash_hex,
        proof,
        sample_merkle_root_hex,
        partial_hashes # Pass the incomplete list
    )
    assert not is_valid 

# --- Test Proof of Training Consistency ---

def test_pot_consistency_valid(valid_dpodl_state):
    """Tests consistency check with a fully valid state."""
    assert verify_proof_of_training_consistency(valid_dpodl_state)

def test_pot_consistency_invalid_t1(valid_dpodl_state):
    """Tests failure when pre_hash doesn't meet T1."""
    invalid_state = valid_dpodl_state.copy()
    invalid_state['t1_threshold'] = 0 # Set T1 impossibly low
    assert not verify_proof_of_training_consistency(invalid_state)

def test_pot_consistency_invalid_t2(valid_dpodl_state):
    """Tests failure when post_hash doesn't meet T2."""
    invalid_state = valid_dpodl_state.copy()
    invalid_state['t2_threshold'] = 0 # Set T2 impossibly low
    assert not verify_proof_of_training_consistency(invalid_state)

def test_pot_consistency_wrong_random_seed(valid_dpodl_state):
    """Tests failure when stored random_seed is incorrect."""
    invalid_state = valid_dpodl_state.copy()
    invalid_state['random_seed'] += 1 # Tamper with seed
    assert not verify_proof_of_training_consistency(invalid_state)

def test_pot_consistency_wrong_weight_seed(valid_dpodl_state):
    """Tests failure when stored seed_for_weights is incorrect."""
    invalid_state = valid_dpodl_state.copy()
    invalid_state['seed_for_weights'] += 1 # Tamper with seed
    assert not verify_proof_of_training_consistency(invalid_state)

def test_pot_consistency_wrong_post_hash_calc(valid_dpodl_state):
    """Tests failure when post_hash cannot be reproduced from components."""
    invalid_state = valid_dpodl_state.copy()
    # Tamper with one of the inputs to the post_hash calculation
    invalid_state['accuracy'] = 0.5
    # The stored post_hash will no longer match the calculation
    assert not verify_proof_of_training_consistency(invalid_state)

def test_pot_consistency_missing_key(valid_dpodl_state):
    """Tests failure when a required key is missing."""
    invalid_state = valid_dpodl_state.copy()
    del invalid_state['accuracy'] # Remove a required key
    assert not verify_proof_of_training_consistency(invalid_state)

def test_pot_consistency_none_value(valid_dpodl_state):
    """Tests failure when a required key has a None value."""
    invalid_state = valid_dpodl_state.copy()
    invalid_state['t1_threshold'] = None # Set a required key to None
    assert not verify_proof_of_training_consistency(invalid_state) 