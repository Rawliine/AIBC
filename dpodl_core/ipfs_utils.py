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

from .blockchain_config import IPFS_HOST
# Use a more specific logger if available, otherwise a default one
logger = logging.getLogger(__name__) # Or use your project's custom logger if it exists

# Global IPFS client instance
_ipfs_client = None

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
    """Loads a model's state_dict from IPFS given a CID."""
    try:
        model_bytes = load_data_from_ipfs(cid)
        if model_bytes:
            buffer = io.BytesIO(model_bytes)
            model_state = torch.load(buffer)
            logger.info(f"Model '{model_name}' state_dict loaded from IPFS (CID: {cid})")
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

        # Convert checkpoint data (dict) to bytes (e.g., using JSON)
        buffer = io.BytesIO()
        # Use pickle or json to serialize the dictionary
        import pickle
        pickle.dump(checkpoint_data, buffer)
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
