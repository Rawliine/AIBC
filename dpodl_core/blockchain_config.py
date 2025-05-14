# dpodl_core/blockchain_config.py
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file at the project root
# Assumes .env file is in the parent directory of dpodl_core
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

# --- Network Configuration ---
# Default to local Hardhat node if not specified in .env
NETWORK_URL = os.getenv('BLOCKCHAIN_NETWORK_URL', 'http://127.0.0.1:8545')
CHAIN_ID = int(os.getenv('BLOCKCHAIN_CHAIN_ID', 31337))
NETWORK_NAME = os.getenv('BLOCKCHAIN_NETWORK_NAME', 'localhost') # Or 'hardhat', 'sepolia', etc.

# --- Contract Deployment Information ---
# Path to the hardhat-deploy deployments directory (relative to this file)
DEPLOYMENTS_PATH = Path(__file__).parent.parent / 'blockchain' / 'deployments'

# Function to load contract ABI and address
def get_contract_info(contract_name: str, network_name: str = NETWORK_NAME) -> tuple[str, dict] | tuple[None, None]:
    """Loads the address and ABI for a given contract and network.

    Args:
        contract_name: The name of the contract (e.g., "DPoDLToken").
        network_name: The name of the network (e.g., "localhost", "sepolia").

    Returns:
        A tuple containing (contract_address, contract_abi) or (None, None) if not found.
    """
    deployment_file = DEPLOYMENTS_PATH / network_name / f"{contract_name}.json"
    if not deployment_file.exists():
        print(f"Error: Deployment file not found for {contract_name} on network {network_name} at {deployment_file}")
        return None, None

    try:
        with open(deployment_file, 'r') as f:
            deployment_data = json.load(f)
        contract_address = deployment_data.get('address')
        contract_abi = deployment_data.get('abi')

        if not contract_address or not contract_abi:
            print(f"Error: Address or ABI not found in {deployment_file}")
            return None, None

        return contract_address, contract_abi
    except Exception as e:
        print(f"Error loading contract info from {deployment_file}: {e}")
        return None, None

# Example usage (typically you would not call these directly here)
if __name__ == "__main__":
    print("Testing blockchain_config.py...")
    # Test existing network
    # print("DPoDLToken on localhost:", get_contract_info("DPoDLToken", "localhost"))
    # Test non-existent contract
    # get_contract_info("NonExistent")
    # Test non-existent network
    # get_contract_info("DPoDLToken", "nonexistent_network")

# Worker Funding
FUND_WORKERS_ON_START = os.getenv("FUND_WORKERS_ON_START", "True").lower() == "true"
MIN_WORKER_BALANCE_ETH = float(os.getenv("MIN_WORKER_BALANCE_ETH", 0.01))
FUND_AMOUNT_ETH = float(os.getenv("FUND_AMOUNT_ETH", 0.05))

# IPFS Configuration
IPFS_HOST = os.getenv("IPFS_HOST", "/ip4/127.0.0.1/tcp/5001/http")

# Pinata Configuration (Moved into a class)
class PinataConfig:
    PINATA_API_KEY = os.getenv("PINATA_API_KEY", "YOUR_PINATA_API_KEY")
    PINATA_SECRET_API_KEY = os.getenv("PINATA_SECRET_API_KEY", "YOUR_PINATA_SECRET_API_KEY")
    PINATA_JWT = os.getenv("PINATA_JWT", "YOUR_PINATA_JWT")
    PINATA_API_URL = os.getenv("PINATA_API_URL", "https://api.pinata.cloud/pinning/pinByHash")
    ENABLE_PINNING = os.getenv("ENABLE_PINATA_PINNING", "false").lower() == "true"

# D-PoDL specific parameters (defaults, can be fetched from ModelRegistry)
DEFAULT_T1_THRESHOLD = "0x0000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
DEFAULT_ACCURACY_THRESHOLD_BPS = 8500 # 85.00%
DEFAULT_BLOCK_REWARD_AMOUNT = 10 * (10**18) # 10 DPDL tokens (assuming 18 decimals)
DEFAULT_MIN_TRAINING_STEPS = 100
DEFAULT_MAX_TRAINING_STEPS = 10000
DEFAULT_MIN_ACCURACY_IMPROVEMENT_BPS = 100 # 1%
DEFAULT_MIN_STEP_IMPROVEMENT = 50
DEFAULT_REFERENCE_REWARD_SHARE_BPS = 2000 # 20% 