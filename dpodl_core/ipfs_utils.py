import logging
import ipfshttpclient
import torch
import io
import os
import tempfile
import json
import requests # For Pinata API
import asyncio # Add asyncio import
from dpodl_core.blockchain_config import PinataConfig
import safetensors.torch
from typing import Dict, Any, Tuple, Optional
from .crypto import (
    sha256_hash_hex, 
    create_manifest_message, 
    sign_manifest_eip712, 
    verify_manifest_signature,
    recover_manifest_signer
)

from .blockchain_config import IPFS_HOST
# Use a more specific logger if available, otherwise a default one
logger = logging.getLogger(__name__) # Or use your project's custom logger if it exists

# Global IPFS client instance
_ipfs_client = None

def _prepare_dict_for_pickle(data_dict):
    """Recursively prepares a dictionary for pickling by moving tensors to CPU."""
    if not isinstance(data_dict, dict):
        return data_dict # Only process dicts

    prepared_dict = {}
    for key, value in data_dict.items():
        if isinstance(value, torch.Tensor):
            prepared_dict[key] = value.cpu()
        elif isinstance(value, dict):
            prepared_dict[key] = _prepare_dict_for_pickle(value) # Recurse for nested dicts
        elif isinstance(value, list):
            # Process lists: create a new list with processed items
            prepared_list = []
            for item in value:
                if isinstance(item, torch.Tensor):
                    prepared_list.append(item.cpu())
                elif isinstance(item, dict):
                    prepared_list.append(_prepare_dict_for_pickle(item))
                else:
                    prepared_list.append(item)
            prepared_dict[key] = prepared_list
        else:
            prepared_dict[key] = value
    return prepared_dict

def get_ipfs_client():
    global _ipfs_client
    if _ipfs_client is None:
        try:
            _ipfs_client = ipfshttpclient.connect(IPFS_HOST, timeout=10)
            logger.info(f"Successfully connected to IPFS daemon at {IPFS_HOST}")
        except Exception as e:
            logger.error(f"Failed to connect to IPFS daemon at {IPFS_HOST}. Is it running? Error: {e}")
            # Optionally, raise the exception or handle it to prevent app from starting if IPFS is critical
            # raise e 
    return _ipfs_client

def add_data_to_ipfs(data: bytes) -> str | None:
    """Adds raw bytes to IPFS and returns the CID."""
    client = get_ipfs_client()
    if not client:
        return None
    try:
        res = client.add_bytes(data)
        logger.info(f"Data added to IPFS with CID: {res}")
        return res
    except ipfshttpclient.exceptions.CommunicationError as e:
        logger.error(f"IPFS daemon not running or not accessible at {IPFS_HOST}. Error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error adding data to IPFS: {e}")
        return None

def load_data_from_ipfs(cid: str) -> bytes | None:
    """Loads raw data from IPFS given a CID."""
    client = get_ipfs_client()
    if not client:
        return None
    try:
        data = client.cat(cid)
        logger.info(f"Data loaded from IPFS for CID: {cid}")
        return data
    except ipfshttpclient.exceptions.CommunicationError as e:
        logger.error(f"IPFS daemon not running or not accessible at {IPFS_HOST}. Error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading data from IPFS (CID: {cid}): {e}")
        return None


async def pin_to_pinata(cid: str, name: str = None) -> bool:
    """
    Pins a CID to Pinata for persistence.

    Args:
        cid (str): The IPFS CID to pin.
        name (str, optional): A name for the pin on Pinata. Defaults to None.

    Returns:
        bool: True if pinning was successful or already pinned, False otherwise.
    """
    if not PinataConfig.ENABLE_PINNING:
        logger.info(f"Pinata pinning is disabled via ENABLE_PINATA_PINNING. Skipping pin for CID {cid}.")
        return True # Indicate successful handling of the pinning step (by skipping)

    use_jwt = False
    if PinataConfig.PINATA_JWT and PinataConfig.PINATA_JWT != "YOUR_PINATA_JWT":
        use_jwt = True
    elif not PinataConfig.PINATA_API_KEY or PinataConfig.PINATA_API_KEY == "YOUR_PINATA_API_KEY" or \
         not PinataConfig.PINATA_SECRET_API_KEY or PinataConfig.PINATA_SECRET_API_KEY == "YOUR_PINATA_SECRET_API_KEY":
        logger.warning("Pinata API Key/Secret or JWT not configured sufficiently. Skipping pinning.")
        return False

    headers = {}
    if use_jwt:
        headers["Authorization"] = f"Bearer {PinataConfig.PINATA_JWT}"
    else:
        headers["pinata_api_key"] = PinataConfig.PINATA_API_KEY
        headers["pinata_secret_api_key"] = PinataConfig.PINATA_SECRET_API_KEY

    body = {
        "hashToPin": cid,
    }
    if name:
        body["pinataMetadata"] = {"name": name}

    try:
        # Using a synchronous requests call here as the parent functions are not async
        # If worker.py becomes async, this can be awaited.
        response = requests.post(PinataConfig.PINATA_API_URL, json=body, headers=headers, timeout=30)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        
        result = response.json()
        logger.info(f"Pinata pinning status for CID {cid} ({name or 'N/A'}): {result.get('status', 'Unknown')}. Timestamp: {result.get('timestamp')}")
        return True
    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            # Capture full details first
            error_status = e.response.status_code
            error_headers = e.response.headers
            error_body_text = e.response.text
            full_error_details = f"Status: {error_status}, Headers: {error_headers}, Body: {error_body_text}"

            if error_status == 400:
                try:
                    error_data_json = e.response.json()
                    if "DUPLICATE_PIN" in str(error_data_json).upper() or \
                       (isinstance(error_data_json, dict) and "already pinned" in error_data_json.get("error", {}).get("reason", "").lower()):
                        logger.info(f"CID {cid} ({name or 'N/A'}) is already pinned on Pinata.")
                        return True
                    logger.error(f"Pinata API HTTP Error (400) for CID {cid} ({name or 'N/A'}): {e} - Response JSON: {error_data_json}")
                except json.JSONDecodeError:
                    logger.error(f"Pinata API HTTP Error (400) for CID {cid} ({name or 'N/A'}) with non-JSON response: {e} - Full Raw Response: {full_error_details}")
            else: # Handles 403 and other non-400 HTTP errors
                logger.error(f"Pinata API HTTP Error (Status: {error_status}) for CID {cid} ({name or 'N/A'}): {e} - Full Raw Response: {full_error_details}")
        else: # e.response is None, which is unexpected for HTTPError but good to cover
            logger.error(f"Pinata API HTTP Error for CID {cid} ({name or 'N/A'}): {e} - No response object available in exception.")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Pinata API Request Error for CID {cid} ({name or 'N/A'}): {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during Pinata pinning for CID {cid} ({name or 'N/A'}): {e}")
        return False


async def save_model_state_to_ipfs(model_state: dict, model_name: str) -> str | None:
    """Saves a model's state_dict to a temporary file, then to IPFS, and returns the CID."""
    try:
        client = get_ipfs_client()
        if not client:
            return None

        # Convert model state dict to bytes
        buffer = io.BytesIO()
        torch.save(model_state, buffer)
        buffer.seek(0)
        model_bytes = buffer.read()

        # Add to IPFS
        res = client.add_bytes(model_bytes)
        logger.info(f"Model '{model_name}' state_dict saved to IPFS with CID: {res}")

        # Pin to Pinata (await the async call)
        await pin_to_pinata(res, name=f"{model_name}_checkpoint")

        return res
    except Exception as e:
        logger.error(f"Error saving model state '{model_name}' to IPFS: {e}")
        return None

def load_model_state_from_ipfs(cid: str, model_name: str) -> dict | None:
    """
    DEPRECATED: Legacy unsafe model loading. Use load_secure_model_artifacts instead.
    Loads a model's state_dict from IPFS given a CID with weights_only=True for safety.
    """
    logger.warning(f"Using deprecated unsafe model loading for {model_name}. Consider upgrading to secure format.")
    try:
        model_bytes = load_data_from_ipfs(cid)
        if model_bytes:
            buffer = io.BytesIO(model_bytes)
            # Use weights_only=True to prevent arbitrary code execution
            model_state = torch.load(buffer, weights_only=True)
            logger.info(f"Model '{model_name}' state_dict loaded from IPFS (CID: {cid}) with weights_only=True")
            return model_state
        return None
    except Exception as e:
        logger.error(f"Error loading model state '{model_name}' from IPFS (CID: {cid}): {e}")
        return None

# Example for checkpoint data (JSON)
async def save_checkpoint_data_to_ipfs(checkpoint_data: dict, name: str = "dpodl_checkpoint_data") -> str | None:
    """Saves checkpoint data (as JSON) to IPFS and returns the CID."""
    try:
        client = get_ipfs_client()
        if not client:
            return None

        # Prepare the dictionary for pickling (move tensors to CPU)
        prepared_checkpoint_data = _prepare_dict_for_pickle(checkpoint_data)

        # Convert checkpoint data (dict) to bytes (e.g., using JSON)
        buffer = io.BytesIO()
        # Use pickle or json to serialize the dictionary
        torch.save(prepared_checkpoint_data, buffer)
        buffer.seek(0)
        data_bytes = buffer.read()

        # Add to IPFS
        res = client.add_bytes(data_bytes)
        logger.info(f"Checkpoint data '{name}' saved to IPFS with CID: {res}")

        # Pin to Pinata (await the async call)
        await pin_to_pinata(res, name=f"{name}_checkpoint_data")

        return res
    except Exception as e:
        logger.error(f"Error saving checkpoint data '{name}' to IPFS: {e}")
        return None

def load_checkpoint_data_from_ipfs(cid: str, name: str) -> dict | None:
    """Loads checkpoint data (JSON) from IPFS given a CID."""
    try:
        json_bytes = load_data_from_ipfs(cid)
        if json_bytes:
            checkpoint_data = json.loads(json_bytes.decode('utf-8'))
            logger.info(f"Checkpoint data '{name}' loaded from IPFS (CID: {cid})")
            return checkpoint_data
        return None
    except Exception as e:
        logger.error(f"Error loading checkpoint data '{name}' from IPFS (CID: {cid}): {e}")
        return None

def load_pickled_dict_from_ipfs(cid: str, name: str = "dpodl_checkpoint_pickle") -> dict | None:
    """
    DEPRECATED: Legacy unsafe pickle loading. Use load_secure_model_artifacts instead.
    Loads a pickled dictionary (like D-PoDL checkpoint state) from IPFS given a CID.
    """
    logger.warning(f"Using deprecated unsafe pickle loading for {name}. Consider upgrading to secure format.")
    try:
        pickled_bytes = load_data_from_ipfs(cid)
        if pickled_bytes:
            # import pickle # No longer using pickle directly for loading here
            import io      # For BytesIO
            import torch   # For torch.load
            buffer = io.BytesIO(pickled_bytes)
            # Use torch.load with weights_only=True for safety (may fail with complex objects)
            # map_location can be useful if loading CUDA tensors on CPU.
            try:
                data_dict = torch.load(buffer, map_location=torch.device('cpu'), weights_only=True)
                logger.info(f"Data '{name}' loaded safely with weights_only=True from IPFS (CID: {cid})")
                return data_dict
            except Exception as weights_only_err:
                logger.warning(f"weights_only=True failed for {name}, falling back to unsafe mode: {weights_only_err}")
                buffer.seek(0)  # Reset buffer position
                data_dict = torch.load(buffer, map_location=torch.device('cpu'))
                logger.warning(f"Data '{name}' loaded using UNSAFE torch.load from IPFS (CID: {cid})")
                return data_dict
        return None
    # torch.load can raise various errors, including pickle.UnpicklingError or RuntimeError
    except Exception as e: 
        logger.error(f"Error loading/unpickling data for '{name}' from IPFS using torch.load (CID: {cid}): {e}", exc_info=True)
        return None

def merge_model_states(state_dicts: list[dict]) -> dict:
    if not state_dicts: return {}
    # Use first state_dict as base
    merged_state = state_dicts[0].copy()
    num_models = len(state_dicts)
    logger.info(f"Attempting to merge {num_models} state dicts...")
    
    for name, base_param in state_dicts[0].items():
        params_to_avg = [base_param]
        for i in range(1, num_models):
            if name in state_dicts[i] and state_dicts[i][name].shape == base_param.shape:
                params_to_avg.append(state_dicts[i][name])
            else:
                logger.warning(f"Layer {name} mismatch or missing in model {i+1}. Excluding from average.")
        
        if len(params_to_avg) > 1: # Only average if multiple valid params found
             # Ensure all tensors are float for averaging
            float_params = [p.float().cpu() for p in params_to_avg]
            avg_param = torch.stack(float_params, dim=0).mean(dim=0)
            merged_state[name] = avg_param.to(base_param.dtype) # Cast back to original dtype
            logger.debug(f"Averaged layer {name} from {len(params_to_avg)} models.")
        else:
             # Keep the base param if no others matched
             merged_state[name] = base_param

    logger.info("Merging complete.")
    return merged_state

# --- Security Configuration --- #

# File size limits (configurable)
DEFAULT_MAX_MODEL_SIZE = 200 * 1024 * 1024  # 200MB default
DEFAULT_MAX_CHECKPOINT_SIZE = 50 * 1024 * 1024  # 50MB default

# Allowed tensor dtypes for security
ALLOWED_DTYPES = {
    torch.float32,
    torch.bfloat16,
    torch.float16,
    torch.int32,
    torch.int64,
    torch.int8,
    torch.uint8,
    torch.bool
}

# JSON schema for checkpoint metadata
CHECKPOINT_SCHEMA_REQUIRED_FIELDS = {
    "steps", "accuracy_bps", "dataset_hash", "reference_dpodl_cid", 
    "model_hash", "merkle_root", "seed", "artifact_version"
}

# --- Secure Save Functions --- #

async def save_secure_model_artifacts(
    model_state_dict: Dict[str, torch.Tensor],
    checkpoint_metadata: Dict[str, Any],
    private_key: str,
    submitter_address: str,
    chain_id: int,
    verifying_contract: str,
    dataset_hash: str,
    reference_dpodl_cid: str = "",
    pin_to_pinata_flag: bool = True
) -> Optional[Tuple[str, str, str]]:
    """
    Securely saves model artifacts as safetensors + signed manifest.
    
    Args:
        model_state_dict: The model's state dictionary
        checkpoint_metadata: Training metadata (steps, accuracy, etc.)
        private_key: Private key for EIP-712 signing
        submitter_address: The submitter's Ethereum address
        chain_id: Blockchain chain ID
        verifying_contract: Contract address for EIP-712 domain
        dataset_hash: Hash of the dataset used for training
        reference_dpodl_cid: Reference model's DPoDL checkpoint CID
        pin_to_pinata_flag: Whether to pin to Pinata
        
    Returns:
        tuple: (model_cid, checkpoint_cid, manifest_cid) or None if failed
    """
    try:
        client = get_ipfs_client()
        if not client:
            logger.error("IPFS client not available for secure save")
            return None

        # Validate inputs
        if not _validate_model_state_dict(model_state_dict):
            logger.error("Model state dict validation failed")
            return None
            
        if not _validate_checkpoint_metadata(checkpoint_metadata):
            logger.error("Checkpoint metadata validation failed")
            return None

        # 1. Save model weights as safetensors
        model_bytes = _serialize_safetensors(model_state_dict)
        if len(model_bytes) > DEFAULT_MAX_MODEL_SIZE:
            logger.error(f"Model size {len(model_bytes)} exceeds limit {DEFAULT_MAX_MODEL_SIZE}")
            return None
            
        model_cid = client.add_bytes(model_bytes)
        model_sha256 = sha256_hash_hex(model_bytes)
        logger.info(f"Model safetensors saved to IPFS: {model_cid}")

        # 2. Save checkpoint metadata as JSON
        checkpoint_bytes = json.dumps(checkpoint_metadata, sort_keys=True).encode('utf-8')
        if len(checkpoint_bytes) > DEFAULT_MAX_CHECKPOINT_SIZE:
            logger.error(f"Checkpoint size {len(checkpoint_bytes)} exceeds limit {DEFAULT_MAX_CHECKPOINT_SIZE}")
            return None
            
        checkpoint_cid = client.add_bytes(checkpoint_bytes)
        checkpoint_sha256 = sha256_hash_hex(checkpoint_bytes)
        logger.info(f"Checkpoint metadata saved to IPFS: {checkpoint_cid}")

        # 3. Create and sign manifest
        manifest_data = create_manifest_message(
            model_cid=model_cid,
            checkpoint_cid=checkpoint_cid,
            manifest_cid="",  # Will be filled after we get the CID
            model_sha256=model_sha256,
            checkpoint_sha256=checkpoint_sha256,
            model_size=len(model_bytes),
            checkpoint_size=len(checkpoint_bytes),
            dataset_hash=dataset_hash,
            steps=checkpoint_metadata["steps"],
            accuracy_bps=checkpoint_metadata["accuracy_bps"],
            reference_dpodl_cid=reference_dpodl_cid,
            submitter_address=submitter_address,
            artifact_version=checkpoint_metadata.get("artifact_version", "1.0")
        )

        # First, save manifest without signature to get CID
        temp_manifest = {
            "format_version": "1.0",
            "files": {
                "model.safetensors": {
                    "cid": model_cid,
                    "sha256": model_sha256,
                    "size": len(model_bytes)
                },
                "checkpoint.json": {
                    "cid": checkpoint_cid,
                    "sha256": checkpoint_sha256,
                    "size": len(checkpoint_bytes)
                }
            },
            "metadata": manifest_data,
            "signature": None,  # Will be filled
            "structured_data": None  # Will be filled
        }

        # Create temporary manifest to get its CID
        temp_manifest_bytes = json.dumps(temp_manifest, sort_keys=True).encode('utf-8')
        temp_manifest_cid = client.add_bytes(temp_manifest_bytes)
        
        # Update manifest data with actual CID
        manifest_data["manifestCid"] = temp_manifest_cid

        # Sign the complete manifest
        signature_hex, structured_data = sign_manifest_eip712(
            manifest_data, chain_id, verifying_contract, private_key
        )

        # Create final manifest with signature
        final_manifest = {
            "format_version": "1.0",
            "files": {
                "model.safetensors": {
                    "cid": model_cid,
                    "sha256": model_sha256,
                    "size": len(model_bytes)
                },
                "checkpoint.json": {
                    "cid": checkpoint_cid,
                    "sha256": checkpoint_sha256,
                    "size": len(checkpoint_bytes)
                }
            },
            "metadata": manifest_data,
            "signature": signature_hex,
            "structured_data": structured_data
        }

        # Save final signed manifest
        final_manifest_bytes = json.dumps(final_manifest, sort_keys=True).encode('utf-8')
        manifest_cid = client.add_bytes(final_manifest_bytes)
        logger.info(f"Signed manifest saved to IPFS: {manifest_cid}")

        # Pin to Pinata if requested
        if pin_to_pinata_flag:
            await pin_to_pinata(model_cid, f"model_{model_cid[:12]}")
            await pin_to_pinata(checkpoint_cid, f"checkpoint_{checkpoint_cid[:12]}")
            await pin_to_pinata(manifest_cid, f"manifest_{manifest_cid[:12]}")

        return model_cid, checkpoint_cid, manifest_cid

    except Exception as e:
        logger.error(f"Error in secure model save: {e}", exc_info=True)
        return None

# --- Secure Load Functions --- #

def load_secure_model_artifacts(
    manifest_cid: str,
    expected_submitter: str = None,
    load_weights: bool = True,
    max_model_size: int = DEFAULT_MAX_MODEL_SIZE,
    max_checkpoint_size: int = DEFAULT_MAX_CHECKPOINT_SIZE
) -> Optional[Dict[str, Any]]:
    """
    Securely loads and validates model artifacts.
    
    Args:
        manifest_cid: The manifest CID to load
        expected_submitter: Expected submitter address (None to skip check)
        load_weights: Whether to load the actual model weights
        max_model_size: Maximum allowed model size
        max_checkpoint_size: Maximum allowed checkpoint size
        
    Returns:
        dict: {
            'model_state_dict': torch.state_dict (if load_weights=True),
            'checkpoint_metadata': dict,
            'manifest': dict,
            'is_valid': bool,
            'validation_errors': list
        }
    """
    validation_errors = []
    result = {
        'model_state_dict': None,
        'checkpoint_metadata': None,
        'manifest': None,
        'is_valid': False,
        'validation_errors': validation_errors
    }

    try:
        client = get_ipfs_client()
        if not client:
            validation_errors.append("IPFS client not available")
            return result

        # 1. Load and parse manifest
        manifest_bytes = load_data_from_ipfs(manifest_cid)
        if not manifest_bytes:
            validation_errors.append("Failed to load manifest from IPFS")
            return result

        try:
            manifest = json.loads(manifest_bytes.decode('utf-8'))
        except json.JSONDecodeError as e:
            validation_errors.append(f"Invalid manifest JSON: {e}")
            return result

        result['manifest'] = manifest

        # 2. Validate manifest structure
        if not _validate_manifest_structure(manifest):
            validation_errors.append("Invalid manifest structure")
            return result

        # 3. Verify EIP-712 signature if expected_submitter provided
        if expected_submitter:
            signature = manifest.get('signature')
            structured_data = manifest.get('structured_data')
            
            if not signature or not structured_data:
                validation_errors.append("Missing signature or structured data")
                return result

            if not verify_manifest_signature(signature, structured_data, expected_submitter):
                # Also try recovering to see who actually signed
                actual_signer = recover_manifest_signer(signature, structured_data)
                validation_errors.append(f"Signature verification failed. Expected: {expected_submitter}, Actual: {actual_signer}")
                return result

        # 4. Load and validate checkpoint metadata
        checkpoint_cid = manifest['files']['checkpoint.json']['cid']
        checkpoint_bytes = load_data_from_ipfs(checkpoint_cid)
        if not checkpoint_bytes:
            validation_errors.append("Failed to load checkpoint from IPFS")
            return result

        # Validate checkpoint size
        if len(checkpoint_bytes) > max_checkpoint_size:
            validation_errors.append(f"Checkpoint size {len(checkpoint_bytes)} exceeds limit {max_checkpoint_size}")
            return result

        # Validate checkpoint hash
        expected_checkpoint_hash = manifest['files']['checkpoint.json']['sha256']
        actual_checkpoint_hash = sha256_hash_hex(checkpoint_bytes)
        if actual_checkpoint_hash != expected_checkpoint_hash:
            validation_errors.append("Checkpoint hash mismatch")
            return result

        try:
            checkpoint_metadata = json.loads(checkpoint_bytes.decode('utf-8'))
        except json.JSONDecodeError as e:
            validation_errors.append(f"Invalid checkpoint JSON: {e}")
            return result

        if not _validate_checkpoint_metadata(checkpoint_metadata):
            validation_errors.append("Invalid checkpoint metadata")
            return result

        result['checkpoint_metadata'] = checkpoint_metadata

        # 5. Load and validate model weights (if requested)
        if load_weights:
            model_cid = manifest['files']['model.safetensors']['cid']
            model_bytes = load_data_from_ipfs(model_cid)
            if not model_bytes:
                validation_errors.append("Failed to load model from IPFS")
                return result

            # Validate model size
            if len(model_bytes) > max_model_size:
                validation_errors.append(f"Model size {len(model_bytes)} exceeds limit {max_model_size}")
                return result

            # Validate model hash
            expected_model_hash = manifest['files']['model.safetensors']['sha256']
            actual_model_hash = sha256_hash_hex(model_bytes)
            if actual_model_hash != expected_model_hash:
                validation_errors.append("Model hash mismatch")
                return result

            # Load safetensors
            try:
                from safetensors.torch import load
                model_state_dict = load(model_bytes)
            except Exception as e:
                validation_errors.append(f"Failed to load safetensors: {e}")
                return result

            # Validate tensor dtypes
            if not _validate_model_state_dict(model_state_dict):
                validation_errors.append("Model state dict validation failed")
                return result

            result['model_state_dict'] = model_state_dict

        # If we get here, everything is valid
        result['is_valid'] = True
        logger.info(f"Successfully loaded and validated secure model artifacts from {manifest_cid}")

    except Exception as e:
        validation_errors.append(f"Unexpected error: {e}")
        logger.error(f"Error in secure model load: {e}", exc_info=True)

    return result

# --- Helper Functions --- #

def _serialize_safetensors(state_dict: Dict[str, torch.Tensor]) -> bytes:
    """Serialize a state dict to safetensors format."""
    # Use safetensors.torch.save_file with a BytesIO buffer
    from safetensors.torch import save
    buffer = io.BytesIO()
    # safetensors expects the buffer to be passed directly, not as a file-like object
    tensor_bytes = save(state_dict)
    return tensor_bytes

def _validate_model_state_dict(state_dict: Dict[str, torch.Tensor]) -> bool:
    """Validate that a model state dict contains only allowed tensor types."""
    try:
        for key, tensor in state_dict.items():
            if not isinstance(tensor, torch.Tensor):
                logger.error(f"Non-tensor value found in state dict: {key}")
                return False
            
            if tensor.dtype not in ALLOWED_DTYPES:
                logger.error(f"Disallowed dtype {tensor.dtype} for tensor {key}")
                return False
                
            # Additional size checks
            if tensor.numel() > 1e9:  # > 1B parameters per tensor
                logger.error(f"Tensor {key} too large: {tensor.numel()} elements")
                return False
                
        return True
    except Exception as e:
        logger.error(f"Error validating state dict: {e}")
        return False

def _validate_checkpoint_metadata(metadata: Dict[str, Any]) -> bool:
    """Validate checkpoint metadata has required fields."""
    try:
        missing_fields = CHECKPOINT_SCHEMA_REQUIRED_FIELDS - set(metadata.keys())
        if missing_fields:
            logger.error(f"Missing required fields in checkpoint: {missing_fields}")
            return False
            
        # Type checks
        if not isinstance(metadata.get("steps"), int) or metadata["steps"] < 0:
            logger.error("Invalid steps value")
            return False
            
        if not isinstance(metadata.get("accuracy_bps"), int) or not (0 <= metadata["accuracy_bps"] <= 10000):
            logger.error("Invalid accuracy_bps value")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error validating checkpoint metadata: {e}")
        return False

def _validate_manifest_structure(manifest: Dict[str, Any]) -> bool:
    """Validate that manifest has the expected structure."""
    try:
        required_keys = {'format_version', 'files', 'metadata'}
        if not all(key in manifest for key in required_keys):
            logger.error("Missing required keys in manifest")
            return False
            
        files = manifest.get('files', {})
        required_files = {'model.safetensors', 'checkpoint.json'}
        if not all(file in files for file in required_files):
            logger.error("Missing required files in manifest")
            return False
            
        # Check each file has required fields
        for filename, file_info in files.items():
            required_file_keys = {'cid', 'sha256', 'size'}
            if not all(key in file_info for key in required_file_keys):
                logger.error(f"Missing required fields for file {filename}")
                return False
                
        return True
    except Exception as e:
        logger.error(f"Error validating manifest structure: {e}")
        return False
