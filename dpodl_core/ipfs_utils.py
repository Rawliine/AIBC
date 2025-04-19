import logging
import ipfshttpclient
import torch
import io

logger = logging.getLogger(__name__)

# TODO: Make IPFS address configurable
IPFS_API_ADDR = '/ip4/127.0.0.1/tcp/5001'

def get_ipfs_client():
    """Connects to the local IPFS daemon."""
    try:
        client = ipfshttpclient.connect(IPFS_API_ADDR, timeout=60)
        # Quick check if daemon is alive
        client.version() 
        logger.info(f"Connected to IPFS daemon at {IPFS_API_ADDR}")
        return client
    except Exception as e:
        logger.warning(f"Could not connect to IPFS daemon at {IPFS_API_ADDR}: {e}. IPFS operations will fail.")
        return None

def add_file_to_ipfs(file_path: str, client=None) -> str or None:
    """Adds a local file to IPFS and returns the CID."""
    if client is None:
        client = get_ipfs_client()
    
    if not client:
        return None
        
    try:
        res = client.add(file_path)
        cid = res['Hash']
        logger.info(f"Added {file_path} to IPFS. CID: {cid}")
        return cid
    except Exception as e:
        logger.error(f"Failed to add {file_path} to IPFS: {e}")
        return None

def load_model_state_from_ipfs(cid: str, client=None) -> dict or None:
    """
    Loads a PyTorch state_dict from an IPFS CID.
    Assumes the CID points to a file created by torch.save(state_dict, ...).
    
    Returns:
        The loaded state_dict or None if loading fails.
    """
    if client is None:
        client = get_ipfs_client()
        
    if not client:
        logger.warning(f"IPFS client not available. Cannot load model state for CID: {cid}")
        return None
        
    logger.info(f"Attempting to load model state from IPFS CID: {cid}")
    try:
        # Get file content from IPFS
        file_content = client.cat(cid)
        
        # Load state_dict using torch.load from bytes
        buffer = io.BytesIO(file_content)
        state_dict = torch.load(buffer, map_location='cpu') # Load to CPU initially
        logger.info(f"Successfully loaded state_dict from CID: {cid}")
        return state_dict
    except ipfshttpclient.exceptions.ErrorResponse as e:
        logger.error(f"IPFS error response while fetching CID {cid}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to load state_dict from IPFS CID {cid}: {e}", exc_info=True)
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
