import pytest
import torch
from collections import OrderedDict
import hashlib
import struct

# Import functions from the module to be tested
from dpodl_core.crypto import (
    hash_bytes,
    bytes_to_hex,
    hash_model_state,
    build_merkle_tree,
    get_merkle_proof,
    verify_merkle_proof,
    calculate_pre_hash,
    verify_pre_hash_threshold,
    extract_seed_from_hash,
    hash_to_architecture,
    PARAM_SPACE, # Import the definition for validation
    calculate_post_hash,
    verify_post_hash_threshold,
    deterministic_json_dumps
)

# --- Fixtures ---

@pytest.fixture
def sample_state_dict():
    """Provides a simple, deterministic OrderedDict for model state."""
    state = OrderedDict()
    state['layer1.weight'] = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    state['layer1.bias'] = torch.tensor([0.1, 0.2])
    state['layer2.weight'] = torch.tensor([[5.0, 6.0, 7.0]])
    return state

@pytest.fixture
def sample_leaf_hashes():
    """Provides a list of sample leaf hashes (bytes)."""
    return [
        hash_bytes(b'leaf1'),
        hash_bytes(b'leaf2'),
        hash_bytes(b'leaf3'),
        hash_bytes(b'leaf4'),
        hash_bytes(b'leaf5') # Non-power of 2
    ]

# --- Test Hashing Utilities ---

def test_hash_bytes():
    data = b'test data'
    expected_hash_bytes = hashlib.sha3_256(data).digest()
    assert hash_bytes(data) == expected_hash_bytes

def test_bytes_to_hex():
    data = b'\xde\xad\xbe\xef'
    expected_hex = 'deadbeef'
    assert bytes_to_hex(data) == expected_hex

def test_hash_model_state_deterministic(sample_state_dict):
    hash1 = hash_model_state(sample_state_dict)
    # Create another identical state dict to ensure order doesn't matter if keys are same
    state_dict2 = OrderedDict()
    state_dict2['layer1.weight'] = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    state_dict2['layer1.bias'] = torch.tensor([0.1, 0.2])
    state_dict2['layer2.weight'] = torch.tensor([[5.0, 6.0, 7.0]])
    hash2 = hash_model_state(state_dict2)
    assert hash1 == hash2
    assert isinstance(hash1, bytes)

def test_hash_model_state_changes(sample_state_dict):
    hash1 = hash_model_state(sample_state_dict)
    # Modify a tensor slightly
    sample_state_dict['layer1.bias'] = torch.tensor([0.1, 0.21]) # Changed bias
    hash2 = hash_model_state(sample_state_dict)
    assert hash1 != hash2

def test_deterministic_json_dumps():
    data1 = {"b": 2, "a": 1, "c": {"z": 10, "x": 5}}
    data2 = {"a": 1, "c": {"x": 5, "z": 10}, "b": 2} # Different order
    dump1 = deterministic_json_dumps(data1)
    dump2 = deterministic_json_dumps(data2)
    assert dump1 == dump2
    expected_dump = '{"a": 1, "b": 2, "c": {"x": 5, "z": 10}}'
    assert dump1 == expected_dump


# --- Test Merkle Tree Implementation ---

def test_build_merkle_tree_empty():
    root, levels = build_merkle_tree([])
    assert root == hash_bytes(b"")
    assert levels == [[]]

def test_build_merkle_tree_single():
    leaf = hash_bytes(b'leaf1')
    root, levels = build_merkle_tree([leaf])
    assert root == leaf
    assert levels == [[leaf]]

def test_build_merkle_tree_power_of_two():
    leaves = [hash_bytes(f'leaf{i}'.encode()) for i in range(4)]
    root, levels = build_merkle_tree(leaves)
    assert len(levels) == 3 # Leaves, level 1, root
    assert len(levels[0]) == 4
    assert len(levels[1]) == 2
    assert len(levels[2]) == 1
    assert root == levels[2][0]

def test_build_merkle_tree_padding(sample_leaf_hashes):
    # 5 leaves, padded to 8
    root, levels = build_merkle_tree(sample_leaf_hashes[:]) # Pass a copy
    assert len(levels) == 4 # Leaves, level 1, level 2, root
    assert len(levels[0]) == 8 # Padded leaves
    assert len(levels[1]) == 4
    assert len(levels[2]) == 2
    assert len(levels[3]) == 1
    assert levels[0][4] == levels[0][5] == levels[0][6] == levels[0][7] # Duplicated last leaf

def test_merkle_proof_generation_verification(sample_leaf_hashes):
    leaves = sample_leaf_hashes[:] # Use a copy
    num_leaves = len(leaves)
    root, levels = build_merkle_tree(leaves) # Builds padded tree

    # Verify proof for each original leaf
    for i in range(num_leaves):
        leaf_hash = sample_leaf_hashes[i] # The original hash
        proof = get_merkle_proof(i, levels)
        assert verify_merkle_proof(leaf_hash, i, proof, root)

def test_merkle_proof_invalid_leaf(sample_leaf_hashes):
    leaves = sample_leaf_hashes[:]
    root, levels = build_merkle_tree(leaves)
    proof = get_merkle_proof(0, levels) # Proof for leaf 0
    wrong_leaf = hash_bytes(b'wrong_leaf')
    assert not verify_merkle_proof(wrong_leaf, 0, proof, root)

def test_merkle_proof_invalid_proof(sample_leaf_hashes):
     leaves = sample_leaf_hashes[:]
     root, levels = build_merkle_tree(leaves)
     proof = get_merkle_proof(1, levels) # Proof for leaf 1
     # Tamper with the proof
     if proof:
         tampered_proof = proof[:-1] + [(hash_bytes(b'tampered'), proof[-1][1])]
         assert not verify_merkle_proof(leaves[1], 1, tampered_proof, root)
     else:
         pytest.skip("Proof is empty, cannot tamper")


# --- Test Pre-Hash Components ---

PREV_HASH = "0x" + "a" * 64
REF_ID = "0x" + "b" * 64
NONCE = 12345
T1_THRESHOLD_HIGH = 2**256 - 1 # Always pass
T1_THRESHOLD_LOW = 0 # Always fail (unless hash is zero)

def test_calculate_pre_hash():
    h1 = calculate_pre_hash(PREV_HASH, REF_ID, NONCE)
    h2 = calculate_pre_hash(PREV_HASH, REF_ID, NONCE)
    h3 = calculate_pre_hash(PREV_HASH, REF_ID, NONCE + 1)
    h4 = calculate_pre_hash(PREV_HASH, None, NONCE) # Test without ref id
    assert isinstance(h1, str)
    assert len(h1) == 64 # SHA3-256 hex length
    assert h1 == h2 # Deterministic
    assert h1 != h3 # Changes with nonce
    assert h1 != h4 # Changes with ref_id presence

    # Check expected concatenation order (internal detail, but useful)
    hasher = hashlib.sha3_256()
    hasher.update(PREV_HASH.encode('utf-8'))
    hasher.update(REF_ID.encode('utf-8'))
    hasher.update(str(NONCE).encode('utf-8'))
    expected_h1 = hasher.hexdigest()
    assert h1 == expected_h1

    hasher_no_ref = hashlib.sha3_256()
    hasher_no_ref.update(PREV_HASH.encode('utf-8'))
    hasher_no_ref.update(b"NO_REFERENCE")
    hasher_no_ref.update(str(NONCE).encode('utf-8'))
    expected_h4 = hasher_no_ref.hexdigest()
    assert h4 == expected_h4


def test_verify_pre_hash_threshold():
    # Generate a real hash to test against
    test_hash = calculate_pre_hash(PREV_HASH, REF_ID, 5)
    test_hash_int = int(test_hash, 16)

    assert verify_pre_hash_threshold(test_hash, T1_THRESHOLD_HIGH)
    assert verify_pre_hash_threshold(test_hash, test_hash_int) # Equal should pass
    assert verify_pre_hash_threshold(test_hash, test_hash_int + 1) # Higher threshold passes
    assert not verify_pre_hash_threshold(test_hash, test_hash_int - 1) # Lower threshold fails
    assert not verify_pre_hash_threshold(test_hash, T1_THRESHOLD_LOW)
    assert not verify_pre_hash_threshold("invalid-hex", T1_THRESHOLD_HIGH)

def test_extract_seed_from_hash():
    test_hash = calculate_pre_hash(PREV_HASH, REF_ID, NONCE)
    seed = extract_seed_from_hash(test_hash)
    assert isinstance(seed, int)

    # Check determinism
    seed2 = extract_seed_from_hash(test_hash)
    assert seed == seed2

    # Check extraction logic (last 8 hex chars)
    expected_seed_hex = test_hash[-8:]
    expected_seed_int = int(expected_seed_hex, 16)
    assert seed == expected_seed_int

    # Test short hash
    short_hash = "1234567"
    assert extract_seed_from_hash(short_hash) == 0 # Fallback seed


# --- Test Hash-to-Architecture ---

@pytest.fixture
def sample_pre_hash():
     # Generate a deterministic pre_hash for testing HtoA
     return calculate_pre_hash("0x" + "1" * 64, "0x" + "2" * 64, 99)

def test_hash_to_architecture_output_structure(sample_pre_hash):
    result = hash_to_architecture(sample_pre_hash)
    assert isinstance(result, dict)
    assert "architecture" in result
    assert "seed_for_weights" in result
    assert isinstance(result["architecture"], dict)
    assert isinstance(result["seed_for_weights"], int)

def test_hash_to_architecture_params_in_space(sample_pre_hash):
    result = hash_to_architecture(sample_pre_hash)
    arch = result["architecture"]

    # Check that derived parameters are within the defined PARAM_SPACE
    assert arch['embed_dim'] in PARAM_SPACE['embed_dim']
    assert arch['num_heads'] in PARAM_SPACE['num_heads']
    assert arch['num_layers'] in PARAM_SPACE['num_layers']
    assert arch['activation'] in PARAM_SPACE['activation']
    assert arch['dropout_rate'] in PARAM_SPACE['dropout_rate']

    # Check specific constraints (e.g., embed_dim divisible by num_heads)
    assert arch['embed_dim'] % arch['num_heads'] == 0

def test_hash_to_architecture_deterministic(sample_pre_hash):
    result1 = hash_to_architecture(sample_pre_hash)
    result2 = hash_to_architecture(sample_pre_hash)
    assert result1 == result2 # Entire dict should be identical

def test_hash_to_architecture_changes_with_hash():
    hash1 = calculate_pre_hash("0x" + "1" * 64, None, 1)
    hash2 = calculate_pre_hash("0x" + "1" * 64, None, 2) # Different nonce -> different hash
    result1 = hash_to_architecture(hash1)
    result2 = hash_to_architecture(hash2)
    # It's highly likely they will differ, but not strictly guaranteed
    # if hash segments map to the same indices by chance.
    # A better check might be that *some* parameter differs, or seed differs.
    assert result1 != result2 or result1["seed_for_weights"] != result2["seed_for_weights"]

def test_hash_to_architecture_invalid_length():
    with pytest.raises(ValueError):
        hash_to_architecture("short_hash")
    with pytest.raises(ValueError):
         hash_to_architecture("0x" + "a" * 65) # Too long


# --- Test Post-Hash Components ---

FINAL_STATE_HASH = "0x" + "c" * 64
ACCURACY = 0.95
STEPS = 10000
T2_THRESHOLD_HIGH = 2**256 - 1 # Always pass
T2_THRESHOLD_LOW = 0 # Always fail

def test_calculate_post_hash():
    h1 = calculate_post_hash(FINAL_STATE_HASH, ACCURACY, STEPS)
    h2 = calculate_post_hash(FINAL_STATE_HASH, ACCURACY, STEPS)
    h3 = calculate_post_hash(FINAL_STATE_HASH, ACCURACY + 0.01, STEPS)
    h4 = calculate_post_hash(FINAL_STATE_HASH, ACCURACY, STEPS + 1)
    assert isinstance(h1, str)
    assert len(h1) == 64
    assert h1 == h2 # Deterministic
    assert h1 != h3 # Changes with accuracy
    assert h1 != h4 # Changes with steps

    # Check expected concatenation order
    hasher = hashlib.sha3_256()
    hasher.update(FINAL_STATE_HASH.encode('utf-8'))
    hasher.update(struct.pack(">d", ACCURACY))
    hasher.update(str(STEPS).encode('utf-8'))
    expected_h1_actual = hasher.hexdigest()
    assert h1 == expected_h1_actual


def test_verify_post_hash_threshold():
    test_hash = calculate_post_hash(FINAL_STATE_HASH, ACCURACY, STEPS)
    test_hash_int = int(test_hash, 16)

    assert verify_post_hash_threshold(test_hash, T2_THRESHOLD_HIGH)
    assert verify_post_hash_threshold(test_hash, test_hash_int) # Equal should pass
    assert verify_post_hash_threshold(test_hash, test_hash_int + 1) # Higher threshold passes
    assert not verify_post_hash_threshold(test_hash, test_hash_int - 1) # Lower threshold fails
    assert not verify_post_hash_threshold(test_hash, T2_THRESHOLD_LOW)
    assert not verify_post_hash_threshold("invalid-hex", T2_THRESHOLD_HIGH)


