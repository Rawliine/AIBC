# Deployment Guide: D-PoDL System

This guide outlines the steps and considerations for deploying the Decentralized Proof of Deep Learning (D-PoDL) system. It covers the blockchain components, the AI/ML training infrastructure, and essential supporting services.

## Prerequisites

Before starting the deployment, ensure you have the following:

*   Access to machines that can run Ethereum nodes (or a compatible testnet/mainnet).
*   Access to machines for setting up a Ray cluster (head and worker nodes).
*   An IPFS node or access to a public/private IPFS gateway.
*   Node.js and npm/yarn for Hardhat deployment.
*   Python environment with dependencies from `requirements.txt` installed.
*   Docker (optional, but recommended for consistency).

## 1. Blockchain Component Deployment

The blockchain components are managed using Hardhat.

### 1.1. Network Configuration

*   Update `blockchain/hardhat.config.js` with the desired network details (e.g., RPC URL, private keys for deployment accounts, chain ID).
    *   For local development, the default `hardhat` network can be used.
    *   For testnets (e.g., Sepolia) or mainnet, ensure you have funded accounts and correct RPC endpoints.
*   Update `blockchain/helper-hardhat-config.js` if deploying to a new network not listed, specifying `blockConfirmations` and any network-specific parameters.

### 1.2. Contract Deployment

1.  Navigate to the `blockchain/` directory:
    ```bash
    cd blockchain
    ```
2.  Install dependencies:
    ```bash
    npm install
    # or
    yarn install
    ```
3.  Deploy the contracts to the configured network:
    ```bash
    npx hardhat deploy --network <your_network_name>
    ```
    (e.g., `npx hardhat deploy --network sepolia`)

    This will execute the scripts in the `deploy/` folder in order:
    *   `001_deploy_token.js`: Deploys `DPoDLToken.sol`.
    *   `002_deploy_registry.js`: Deploys `ModelRegistry.sol`.
    *   `003_deploy_mempool.js`: Deploys `MTXMempool.sol`.
    *   `004_configure_roles.js`: Configures the `MINTER_ROLE` for `ModelRegistry` on `DPoDLToken`.

4.  **Important:** After deployment, Hardhat typically saves deployment artifacts (contract addresses, ABIs) in `blockchain/deployments/<your_network_name>/`. These are crucial for the Python backend to interact with the contracts. Ensure `dpodl_core/blockchain_config.py` is updated or correctly configured to load these artifacts for the chosen network.

## 2. AI/ML Infrastructure (Ray Cluster)

The AI model training is performed on a Ray cluster.

### 2.1. Ray Head Node Setup

1.  Choose a machine for the Ray head node.
2.  Install Ray: `pip install ray[default]` (or as per project `requirements.txt`).
3.  Start the Ray head node:
    ```bash
    ray start --head --port=6379 --dashboard-host 0.0.0.0
    ```
    *   Note the Ray head node address (e.g., `ray://<head_node_ip>:10001` or the IP displayed by `ray start`). This will be needed for workers and the `trainer.py` script.
    *   Access the Ray Dashboard at `http://<head_node_ip>:8265`.

### 2.2. Ray Worker Node(s) Setup

1.  On each machine designated as a Ray worker:
2.  Install Ray (same version as the head node).
3.  Start the Ray worker, connecting to the head node:
    ```bash
    ray start --address='<head_node_ip>:6379'
    ```
    Replace `<head_node_ip>:6379` with the actual address of your Ray head node's Redis port.

### 2.3. Code and Dependencies

*   Ensure the `dpodl_core/` codebase and all Python dependencies (`requirements.txt`) are available and installed on all Ray nodes (head and workers) in the same environment. This is critical for `worker.py` and other distributed functions to execute correctly.
*   Consider using a shared file system (e.g., NFS) or containerization (Docker) to ensure consistent environments across the cluster.

## 3. IPFS Setup

IPFS is used for storing model data and proofs.

### 3.1. Install and Initialize IPFS

1.  Follow the official IPFS installation guide for your operating system ([https://docs.ipfs.tech/install/](https://docs.ipfs.tech/install/)).
2.  Initialize an IPFS node:
    ```bash
    ipfs init
    ```
3.  Start the IPFS daemon:
    ```bash
    ipfs daemon
    ```
    By default, the API server runs on `localhost:5001` and the gateway on `localhost:8080`.

### 3.2. Configuration for `dpodl_core`

*   The `dpodl_core/ipfs_utils.py` script connects to an IPFS daemon. By default, it might assume `localhost:5001`.
*   If your IPFS daemon is running on a different host or port, or if you're using a remote IPFS pinning service, you'll need to configure `ipfshttpclient.connect()` accordingly. This might involve:
    *   Setting environment variables.
    *   Modifying `ipfs_utils.py` to accept configuration parameters (e.g., from a config file or environment variables).
    *   Ensuring network accessibility between the machines running `dpodl_core` scripts and the IPFS daemon.

## 4. `dpodl_core` Python Backend Configuration

The Python scripts in `dpodl_core/` need to be configured to connect to the deployed blockchain and Ray cluster.

### 4.1. Blockchain Connection

*   `dpodl_core/blockchain_config.py`: This file is central to connecting to the deployed smart contracts.
    *   Ensure it correctly loads the contract addresses and ABIs from the Hardhat deployment artifacts for the target network.
    *   The `WEB3_PROVIDER_URI` needs to be set to the RPC endpoint of your chosen Ethereum network.
    *   Private keys for accounts that will interact with the contracts (e.g., submitting MTXs, claiming rewards) must be securely managed and accessible. Environment variables are a common way to handle this.

### 4.2. Ray Connection

*   `dpodl_core/trainer.py`: This script initializes the Ray connection using `ray.init(address='auto')` or a specific address.
    *   If running `trainer.py` on the Ray head node, `'auto'` might work.
    *   If running from a separate machine, you'll need to provide the Ray head node address (e.g., `ray.init(address='ray://<head_node_ip>:10001')`).

### 4.3. Other Configurations

*   Review all scripts in `dpodl_core/` for hardcoded values, paths, or settings that might need adjustment for your deployment environment.
*   **Logging:** Configure logging levels and outputs as needed for monitoring and debugging.
*   **Data Paths:** Ensure paths for datasets (e.g., in `data_loader.py`) are correct for the deployment environment.

## 5. Running the System

Once all components are deployed and configured:

1.  **Start IPFS Daemon:** Ensure it's running and accessible.
2.  **Start Ray Cluster:** Head node and worker nodes.
3.  **Run `trainer.py`:**
    ```bash
    # Navigate to the project root or ensure dpodl_core is in PYTHONPATH
    python dpodl_core/trainer.py --ray-address <ray_head_address_if_not_auto> --num-workers <N> ... (other arguments)
    ```
    This will initiate the training process, which involves `worker.py` instances running on the Ray cluster, interacting with IPFS and the blockchain.

## 6. Monitoring and Maintenance

*   **Ray Dashboard:** `http://<ray_head_ip>:8265` for monitoring Ray cluster status, logs, and job progress.
*   **Blockchain Explorer:** Use a block explorer (e.g., Etherscan for mainnet/testnets, or a local explorer) to monitor contract interactions.
*   **IPFS:** Monitor IPFS node status and data pinning.
*   **Logging:** Regularly check logs from `trainer.py`, `worker.py`, and other components for errors or important information.
*   **Updates & Upgrades:** Plan for updating smart contracts (if upgradeable patterns are used), Ray versions, IPFS versions, and Python dependencies.

This guide provides a high-level overview. Specific deployment details may vary based on your exact infrastructure and security requirements. 