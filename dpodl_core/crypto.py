import hashlib
import logging
import struct
import json
from collections import OrderedDict
import math # Added for Merkle tree padding
from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3
import time

# Configure logging for this module
logger = logging.getLogger(__name__)
# Basic config if run standalone or not configured globally
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)

# --- Hashing Utilities --- #

def hash_bytes(data_bytes: bytes) -> bytes:
    """Calculates SHA3-256 hash of bytes and returns bytes."""
    return hashlib.sha3_256(data_bytes).digest()

def hash_hex(hex_string: str) -> bytes:
    """Calculates SHA3-256 hash of a hex string's UTF-8 bytes."""
    return hash_bytes(hex_string.encode('utf-8'))
    
def bytes_to_hex(data_bytes: bytes) -> str:
    """Converts bytes to a hex string."""
    return data_bytes.hex()

def hash_pair(left: bytes, right: bytes) -> bytes:
    """Hashes the concatenation of two byte strings (hashes)."""
    return hash_bytes(left + right)

def hash_model_state(state_dict: OrderedDict) -> bytes:
    """
    Calculates a deterministic SHA3-256 hash (bytes) of a PyTorch model's state_dict.
    """
    hasher = hashlib.sha3_256()
    for key in sorted(state_dict.keys()):
        param = state_dict[key]
        param_bytes = param.cpu().numpy().tobytes()
        hasher.update(key.encode('utf-8'))
        hasher.update(param_bytes)
    return hasher.digest()

# --- Merkle Tree Implementation --- #

def build_merkle_tree(leaf_hashes: list[bytes]) -> tuple[bytes, list[list[bytes]]]:
    """
    Builds a Merkle tree from a list of leaf hashes (bytes).
    Handles padding for non-power-of-2 leaves by duplicating the last hash.

    Args:
        leaf_hashes: A list of byte strings, each representing a leaf hash.

    Returns:
        A tuple containing:
          - merkle_root (bytes): The root hash of the tree.
          - tree_levels (list[list[bytes]]): All levels of the tree, including leaves.
                                            tree_levels[0] is the leaf level.
    """
    if not leaf_hashes:
        return hash_bytes(b""), [[]] # Empty tree

    num_leaves = len(leaf_hashes)
    # Pad to the nearest power of 2 by duplicating the last element
    target_size = 1 << (num_leaves - 1).bit_length() if num_leaves > 0 else 0
    if num_leaves < target_size:
         leaf_hashes.extend([leaf_hashes[-1]] * (target_size - num_leaves))
    
    tree_levels = [leaf_hashes]
    current_level = leaf_hashes

    while len(current_level) > 1:
        next_level = []
        # Process pairs of hashes
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i+1] if (i+1) < len(current_level) else left # Handle last odd element
            parent_hash = hash_pair(left, right)
            next_level.append(parent_hash)
        tree_levels.append(next_level)
        current_level = next_level
        
    merkle_root = current_level[0] if current_level else hash_bytes(b"")
    logger.info(f"Built Merkle tree with {num_leaves} leaves (padded to {target_size}). Root: {bytes_to_hex(merkle_root)[:10]}...")
    return merkle_root, tree_levels

def get_merkle_proof(leaf_index: int, tree_levels: list[list[bytes]]) -> list[tuple[bytes, bool]]:
    """
    Generates a Merkle proof (path) for a specific leaf.

    Args:
        leaf_index: The index of the leaf for which to generate the proof.
        tree_levels: All levels of the Merkle tree (output from build_merkle_tree).

    Returns:
        A list of tuples (hash_bytes, is_right_sibling). 
        Each tuple represents a sibling hash needed to reconstruct the root.
        is_right_sibling is True if the sibling hash is on the right.
    """
    if not tree_levels or not tree_levels[0] or leaf_index >= len(tree_levels[0]):
        return [] # Invalid input

    proof = []
    current_index = leaf_index

    # Iterate through levels from bottom up (excluding root level)
    for i in range(len(tree_levels) - 1):
        current_level = tree_levels[i]
        is_right_node = current_index % 2 != 0
        sibling_index = current_index - 1 if is_right_node else current_index + 1

        if sibling_index < len(current_level):
            sibling_hash = current_level[sibling_index]
            proof.append((sibling_hash, not is_right_node)) # Sibling is right if current node is left
        else:
            # This might happen with padding, the sibling is the node itself
            # In a perfectly balanced tree, this case might not be strictly needed,
            # but adding for robustness with padding.
            sibling_hash = current_level[current_index] 
            proof.append((sibling_hash, not is_right_node)) 
            
        # Move to the parent index in the next level up
        current_index //= 2
        
    return proof

def verify_merkle_proof(leaf_hash: bytes, leaf_index: int, proof: list[tuple[bytes, bool]], root_hash: bytes) -> bool:
    """
    Verifies a Merkle proof.

    Args:
        leaf_hash: The hash of the leaf being verified.
        leaf_index: The original index of the leaf in the leaf list.
        proof: The Merkle proof path obtained from get_merkle_proof.
        root_hash: The expected root hash of the tree.

    Returns:
        True if the proof is valid and reconstructs the root_hash, False otherwise.
    """
    current_hash = leaf_hash
    current_index = leaf_index # Keep track of index to handle padding logic if needed

    for sibling_hash, is_right_sibling in proof:
        if is_right_sibling: # Sibling is on the right
            current_hash = hash_pair(current_hash, sibling_hash)
        else: # Sibling is on the left
            current_hash = hash_pair(sibling_hash, current_hash)
        # current_index //= 2 # Not strictly needed for verification if proof is correct
        
    is_valid = current_hash == root_hash
    logger.debug(f"Merkle verification result: {is_valid}. Calculated root: {bytes_to_hex(current_hash)[:10]}..., Expected root: {bytes_to_hex(root_hash)[:10]}...")
    return is_valid


# --- Pre-Hash Components --- 

def calculate_pre_hash(prev_block_hash: str, reference_model_id: str or None, nonce: int) -> str:
    """
    Calculates the Pre-Hash value using SHA3-256.
    Input order matters for reproducibility.
    
    Args:
        prev_block_hash: Hash of the previous block (hex string).
        reference_model_id: ID/Hash of the model being referenced (hex string), or None.
        nonce: Integer nonce found by the miner.
        
    Returns:
        SHA3-256 hash as a hex string.
    """
    hasher = hashlib.sha3_256() # Use SHA3-256
    hasher.update(prev_block_hash.encode('utf-8'))
    if reference_model_id:
        hasher.update(reference_model_id.encode('utf-8'))
    else:
        # Use a standard placeholder if no reference model
        hasher.update(b"NO_REFERENCE") 
    hasher.update(str(nonce).encode('utf-8'))
    
    hex_hash = hasher.hexdigest()
    # logger.debug(f"Calculated pre_hash: {hex_hash} for nonce {nonce}")
    return hex_hash

def verify_pre_hash_threshold(pre_hash_hex: str, t1_threshold: int) -> bool:
    """
    Verifies if the pre-hash value (as hex string) meets the T1 difficulty threshold.
    
    Args:
        pre_hash_hex: The calculated pre-hash (hex string).
        t1_threshold: The target difficulty threshold (integer).
        
    Returns:
        True if hash <= threshold, False otherwise.
    """
    try:
        # Compare integers directly for robust threshold check
        hash_int = int(pre_hash_hex, 16)
        is_valid = hash_int <= t1_threshold
        # logger.debug(f"Verifying pre_hash {pre_hash_hex} ({hash_int}) <= {t1_threshold}: {is_valid}")
        return is_valid
    except ValueError:
        logger.error(f"Invalid hex string provided for pre_hash: {pre_hash_hex}")
        return False

def extract_seed_from_hash(pre_hash_hex: str) -> int:
    """
    Deterministically extracts a 32-bit integer seed from the pre-hash.
    Uses the last 8 hex characters (4 bytes).
    """
    if len(pre_hash_hex) < 8:
        logger.warning(f"Pre-hash {pre_hash_hex} too short, using fallback seed.")
        return 0 # Fallback seed
        
    seed_hex = pre_hash_hex[-8:]
    seed_int = int(seed_hex, 16)
    # logger.debug(f"Extracted seed {seed_int} from pre_hash {pre_hash_hex}")
    return seed_int

# --- Robust Architecture Mapping --- 

# Define parameter spaces (adjust ranges as needed)
PARAM_SPACE = {
    'embed_dim': [128, 256, 384, 512],      # Embedding dimensions
    'num_heads': [4, 8, 12, 16],            # Attention heads (divisible by embed_dim)
    'num_layers': list(range(4, 13)),       # Number of transformer blocks (4-12)
    'activation': ['relu', 'gelu'],         # Activation function in FF layers
    'dropout_rate': [0.0, 0.1, 0.2]         # Dropout rate
}

def _map_hash_segment_to_param(segment_hex: str, param_options: list):
    """Helper to map a hash segment to an option in a list."""
    segment_int = int(segment_hex, 16)
    index = segment_int % len(param_options)
    return param_options[index]

def hash_to_architecture(pre_hash_hex: str) -> dict:
    """
    Deterministically maps a pre-hash (SHA3-256 hex string) to model architecture parameters.
    Uses hash segmentation to select parameters from predefined spaces.
    Ensures constraints like num_heads divisibility.
    
    Args:
        pre_hash_hex: The validated pre-hash (64 hex chars).
        
    Returns:
        A dictionary containing architecture parameters.
    """
    if len(pre_hash_hex) != 64: # SHA3-256 produces 64 hex characters
        raise ValueError("Invalid pre_hash length for SHA3-256.")

    logger.info(f"Mapping hash {pre_hash_hex[:10]}... to architecture.")
    
    # Divide hash into 8-char (4-byte) segments
    segments = [pre_hash_hex[i:i+8] for i in range(0, 64, 8)]
    if len(segments) != 8:
        raise ValueError("Hash segmentation failed.") # Should not happen

    # Map segments to parameters
    arch_params = {}
    arch_params['num_layers'] = _map_hash_segment_to_param(segments[0], PARAM_SPACE['num_layers'])
    arch_params['activation'] = _map_hash_segment_to_param(segments[1], PARAM_SPACE['activation'])
    arch_params['dropout_rate'] = _map_hash_segment_to_param(segments[2], PARAM_SPACE['dropout_rate'])
    
    # Select embed_dim first
    arch_params['embed_dim'] = _map_hash_segment_to_param(segments[3], PARAM_SPACE['embed_dim'])
    
    # Select num_heads ensuring it divides embed_dim
    valid_heads = [h for h in PARAM_SPACE['num_heads'] if arch_params['embed_dim'] % h == 0]
    if not valid_heads:
        # Fallback if no valid heads found for the selected embed_dim (shouldn't happen with good ranges)
        logger.warning(f"No valid heads for embed_dim {arch_params['embed_dim']}, falling back to 4.")
        valid_heads = [4]
    arch_params['num_heads'] = _map_hash_segment_to_param(segments[4], valid_heads)

    # Extract seed using a dedicated segment (different from the one used for params)
    # Using segment 7 to avoid overlap with parameter selection
    seed_for_weights = int(segments[7], 16)

    logger.info(f"Derived architecture: {arch_params}")
    
    # Return parameters and the seed specifically for weight initialization
    return {
        "architecture": arch_params,
        "seed_for_weights": seed_for_weights
    }

# --- Post-Hash Components (using SHA3-256) --- 

def calculate_post_hash(final_model_state_hash: str, accuracy: float, steps: int) -> str:
    """
    Calculates the Post-Hash using SHA3-256 based on the final model state hash,
    accuracy, and number of training steps.
    
    Args:
        final_model_state_hash: Hex string hash of the final model's state_dict.
        accuracy: Final accuracy achieved (float).
        steps: Total number of training steps performed.
        
    Returns:
        SHA3-256 hash as a hex string.
    """
    hasher = hashlib.sha3_256()
    hasher.update(final_model_state_hash.encode('utf-8'))
    # Use a stable representation for float (big-endian double)
    hasher.update(struct.pack(">d", accuracy))
    hasher.update(str(steps).encode('utf-8'))
    hex_hash = hasher.hexdigest()
    logger.debug(f"Calculated post_hash: {hex_hash} for acc={accuracy}, steps={steps}")
    return hex_hash

def verify_post_hash_threshold(post_hash_hex: str, t2_threshold: int) -> bool:
    """
    Verifies the Post-Hash against T2.
    """
    try:
        hash_int = int(post_hash_hex, 16)
        is_valid = hash_int <= t2_threshold
        logger.debug(f"Verifying post_hash {post_hash_hex} ({hash_int}) <= {t2_threshold}: {is_valid}")
        return is_valid
    except ValueError:
        logger.error(f"Invalid hex string provided for post_hash: {post_hash_hex}")
        return False

# --- Utility for Deterministic Hashing --- #

def deterministic_json_dumps(data):
    """Serializes data to JSON string deterministically (sorted keys)."""
    return json.dumps(data, sort_keys=True)

# --- SHA-256 File Hashing (for manifest validation) --- #

def sha256_hash_bytes(data: bytes) -> bytes:
    """Calculates SHA-256 hash of bytes and returns bytes (for file integrity checks)."""
    return hashlib.sha256(data).digest()

def sha256_hash_hex(data: bytes) -> str:
    """Calculates SHA-256 hash of bytes and returns hex string."""
    return hashlib.sha256(data).hexdigest()

# --- EIP-712 Signature System --- #

# EIP-712 Domain and Types for DPoDL Model Manifests
DPODL_DOMAIN_NAME = "DPoDLManifest"
DPODL_DOMAIN_VERSION = "1"

def get_eip712_domain(chain_id: int, verifying_contract: str) -> dict:
    """Constructs the EIP-712 domain separator for DPoDL manifests."""
    return {
        "name": DPODL_DOMAIN_NAME,
        "version": DPODL_DOMAIN_VERSION,
        "chainId": chain_id,
        "verifyingContract": verifying_contract
    }

def get_eip712_manifest_types() -> dict:
    """Defines the EIP-712 types for DPoDL model manifest signing."""
    return {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"}
        ],
        "Manifest": [
            {"name": "modelCid", "type": "string"},
            {"name": "checkpointCid", "type": "string"},
            {"name": "manifestCid", "type": "string"},
            {"name": "modelSha256", "type": "string"},
            {"name": "checkpointSha256", "type": "string"},
            {"name": "modelSize", "type": "uint256"},
            {"name": "checkpointSize", "type": "uint256"},
            {"name": "datasetHash", "type": "string"},
            {"name": "steps", "type": "uint256"},
            {"name": "accuracyBPS", "type": "uint256"},
            {"name": "referenceDpodlCid", "type": "string"},
            {"name": "submitter", "type": "address"},
            {"name": "timestamp", "type": "uint256"},
            {"name": "artifactVersion", "type": "string"}
        ]
    }

def create_manifest_message(
    model_cid: str,
    checkpoint_cid: str,
    manifest_cid: str,
    model_sha256: str,
    checkpoint_sha256: str,
    model_size: int,
    checkpoint_size: int,
    dataset_hash: str,
    steps: int,
    accuracy_bps: int,
    reference_dpodl_cid: str,
    submitter_address: str,
    timestamp: int = None,
    artifact_version: str = "1.0"
) -> dict:
    """Creates the manifest message data for EIP-712 signing."""
    if timestamp is None:
        timestamp = int(time.time())
    
    return {
        "modelCid": model_cid,
        "checkpointCid": checkpoint_cid,
        "manifestCid": manifest_cid,
        "modelSha256": model_sha256,
        "checkpointSha256": checkpoint_sha256,
        "modelSize": model_size,
        "checkpointSize": checkpoint_size,
        "datasetHash": dataset_hash,
        "steps": steps,
        "accuracyBPS": accuracy_bps,
        "referenceDpodlCid": reference_dpodl_cid,
        "submitter": submitter_address,
        "timestamp": timestamp,
        "artifactVersion": artifact_version
    }

def sign_manifest_eip712(
    manifest_data: dict,
    chain_id: int,
    verifying_contract: str,
    private_key: str
) -> tuple[str, dict]:
    """
    Signs a manifest using EIP-712.
    
    Args:
        manifest_data: The manifest message data
        chain_id: The blockchain chain ID
        verifying_contract: The contract address for domain
        private_key: The signer's private key (hex string with or without 0x)
        
    Returns:
        tuple: (signature_hex, structured_data)
    """
    # Ensure private key has proper format
    if not private_key.startswith('0x'):
        private_key = '0x' + private_key
    
    domain = get_eip712_domain(chain_id, verifying_contract)
    types = get_eip712_manifest_types()
    
    structured_data = {
        "types": types,
        "primaryType": "Manifest", 
        "domain": domain,
        "message": manifest_data
    }
    
    # Encode and sign - pass the full structured data dict
    encoded_data = encode_typed_data(full_message=structured_data)
    signed_message = Account.sign_message(encoded_data, private_key)
    
    signature_hex = signed_message.signature.hex()
    logger.debug(f"Created EIP-712 signature for manifest: {signature_hex[:10]}...")
    
    return signature_hex, structured_data

def verify_manifest_signature(
    signature_hex: str,
    structured_data: dict,
    expected_signer: str
) -> bool:
    """
    Verifies an EIP-712 manifest signature.
    
    Args:
        signature_hex: The signature to verify
        structured_data: The structured data that was signed
        expected_signer: The expected signer address
        
    Returns:
        bool: True if signature is valid and from expected signer
    """
    try:
        # Encode the structured data
        encoded_data = encode_typed_data(full_message=structured_data)
        
        # Recover the signer address
        recovered_address = Account.recover_message(encoded_data, signature=signature_hex)
        
        # Normalize addresses for comparison (checksummed)
        recovered_address = Web3.to_checksum_address(recovered_address)
        expected_signer = Web3.to_checksum_address(expected_signer)
        
        is_valid = recovered_address == expected_signer
        
        if is_valid:
            logger.debug(f"EIP-712 signature verification successful. Signer: {recovered_address}")
        else:
            logger.warning(f"EIP-712 signature verification failed. Expected: {expected_signer}, Recovered: {recovered_address}")
            
        return is_valid
        
    except Exception as e:
        logger.error(f"Error verifying EIP-712 signature: {e}")
        return False

def recover_manifest_signer(signature_hex: str, structured_data: dict) -> str | None:
    """
    Recovers the signer address from an EIP-712 manifest signature.
    
    Args:
        signature_hex: The signature
        structured_data: The structured data that was signed
        
    Returns:
        str: The recovered signer address, or None if recovery fails
    """
    try:
        encoded_data = encode_typed_data(full_message=structured_data)
        recovered_address = Account.recover_message(encoded_data, signature=signature_hex)
        return Web3.to_checksum_address(recovered_address)
    except Exception as e:
        logger.error(f"Error recovering signer from EIP-712 signature: {e}")
        return None
