import os
import logging
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Default (Dev) Configuration
DEFAULT_CONFIG = {
    "dataset_name": "ag_news",
    "dataset_path": None, # Or specify a default path if you have one
    "num_train_samples": None, # Full dataset
    "num_val_samples": None, # Full dataset
    "epochs": 5,
    "batch_size": 128,
    "seq_len": 128,
    "lr": 0.001,
    "embed_dim": 256, # Default, HtoA might override
    "num_heads": 8,   # Default, HtoA might override
    "num_layers": 6,  # Default, HtoA might override
    "t1_threshold": 1809251394333065553493296640760748560207343510400633813116524750123642650624, # from logs
    "t2_threshold": 115792089237316195423570985008687907853269984665640564039457584007913129639936, # from logs
    "t_acc_threshold": 0.97, # from logs
    "prev_block_hash": "0x1111", # Default from logs, can be overridden
    "reference_model_id": None,
    "checkpoint_path": "checkpoint_dpodl.pt",
    "ipfs_enabled": True,
    "model_override_params": None # To specify fixed small model for testing
}

# Test-Specific Overrides
TEST_CONFIG_OVERRIDES = {
    "dataset_name": "ag_news_tiny", # Placeholder, actual tiny dataset path will be needed
    "dataset_path": "./data/ag_news_tiny", # Example path
    "num_train_samples": 200,
    "num_val_samples": 50,
    "epochs": 2,
    "batch_size": 32, # Smaller batch size for tiny dataset
    # "lr": 0.01, # Potentially adjust LR for tiny dataset/epochs
    "ipfs_enabled": True, # <--- Changed to True as per user request
    "model_override_params": { # Simplified model for testing
        "embed_dim": 64,
        "num_heads": 2,
        "num_layers": 1,
    }
    # t1_threshold remains the same as per user request
    # t2_threshold and t_acc_threshold could also be made easier for tests if desired,
    # but not explicitly requested for modification yet.
}

def get_config():
    env = os.getenv("DPODL_ENV", "dev").lower()
    config = DEFAULT_CONFIG.copy()

    if env == "test":
        logger.info(f"Loading TEST configuration overrides (DPODL_ENV={env})")
        config.update(TEST_CONFIG_OVERRIDES)
        # Special handling for model_override_params which is a dict
        if TEST_CONFIG_OVERRIDES.get("model_override_params"):
            if config.get("model_override_params") is None:
                config["model_override_params"] = {}
            config["model_override_params"].update(TEST_CONFIG_OVERRIDES["model_override_params"])
    else:
        logger.info(f"Loading DEV configuration (DPODL_ENV={env})")

    return config

def get_worker_security_config(worker_id=0):
    """
    Gets worker security configuration from environment variables.
    
    Args:
        worker_id: The worker ID (0, 1, etc.) to get specific keys
        
    Returns:
        dict: Security configuration for the worker
    """
    # Get worker-specific private key
    worker_private_key = None
    worker_address = None
    
    # Try worker-specific key first
    env_key = f"WORKER_PRIVATE_KEY_{worker_id}"
    if env_key in os.environ:
        worker_private_key = os.environ[env_key]
    # Fallback to generic test key
    elif "TEST_WORKER_PRIVATE_KEY" in os.environ:
        worker_private_key = os.environ["TEST_WORKER_PRIVATE_KEY"]
        logger.info(f"Using TEST_WORKER_PRIVATE_KEY for worker {worker_id}")
    
    # Generate address from private key if we have one
    if worker_private_key:
        try:
            from eth_account import Account
            # Ensure proper format
            if not worker_private_key.startswith('0x'):
                worker_private_key = '0x' + worker_private_key
            account = Account.from_key(worker_private_key)
            worker_address = account.address
            logger.info(f"Worker {worker_id} address: {worker_address}")
        except Exception as e:
            logger.error(f"Failed to derive address from private key for worker {worker_id}: {e}")
            worker_private_key = None
    
    # Create a simple dataset hash (you can make this more sophisticated)
    dataset_hash = os.environ.get("DATASET_HASH")
    if not dataset_hash:
        # Generate a default hash based on dataset name and environment
        env = os.getenv("DPODL_ENV", "dev").lower()
        dataset_name = "ag_news"  # Default, could be enhanced
        hash_input = f"{dataset_name}_{env}_v1".encode('utf-8')
        dataset_hash = hashlib.sha256(hash_input).hexdigest()
        logger.info(f"Generated default dataset hash: {dataset_hash[:16]}...")
    
    return {
        "worker_private_key": worker_private_key,
        "worker_address": worker_address,
        "dataset_hash": dataset_hash,
        "secure_loading_enabled": worker_private_key is not None
    }

def enhance_config_with_security(base_config, worker_id=0):
    """
    Enhances the base config with worker security settings.
    
    Args:
        base_config: The base configuration dict
        worker_id: The worker ID for this specific worker
        
    Returns:
        dict: Enhanced configuration with security settings
    """
    security_config = get_worker_security_config(worker_id)
    enhanced_config = base_config.copy()
    enhanced_config.update(security_config)
    
    if security_config["secure_loading_enabled"]:
        logger.info(f"✓ Secure loading enabled for worker {worker_id}")
    else:
        logger.warning(f"⚠ Secure loading not available for worker {worker_id} - missing private key")
    
    return enhanced_config

if __name__ == '__main__':
    # Test the config loader
    print("--- Default (Dev) Config ---\n")
    os.environ["DPODL_ENV"] = "dev"
    dev_config = get_config()
    for key, value in dev_config.items():
        print(f"{key}: {value}")

    print("\n--- Test Config ---\n")
    os.environ["DPODL_ENV"] = "test"
    test_config = get_config()
    for key, value in test_config.items():
        print(f"{key}: {value}")

    # Example of accessing a nested dict
    print("\nTest model override:", test_config.get("model_override_params"))
    # Cleanup env var for other potential script runs
    del os.environ["DPODL_ENV"] 