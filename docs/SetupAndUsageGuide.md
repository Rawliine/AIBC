# Project Setup and Usage Guide: D-PoDL

This guide provides instructions for setting up and running the D-PoDL project for local development, testing, and basic usage. It reflects the actual workflow used in practice, based on terminal history.

## 1. Prerequisites

*   **Git:** For cloning the repository.
*   **Python:** Version 3.8+ (check `runtime.txt` or project specifics).
*   **Pip:** For Python package management.
*   **Node.js:** Version 16+ (for Hardhat).
*   **npm or yarn:** For Node.js package management.
*   **Docker & Docker Compose:** Optional, for running local dependencies like Ganache and IPFS.
*   **Conda:** For managing Python environments (optional but recommended).

## 2. Initial Project Setup

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd <project_directory_name>
    ```

2.  **Python Environment Setup:**
    ```bash
    conda create -n AIBC python=3.10 -y
    conda activate AIBC
    pip install -r requirements.txt
    ```

3.  **Blockchain Environment Setup (Hardhat):**
    ```bash
    cd blockchain
    npm install  # or yarn install
    cd ..
    ```

## 3. Running Local Dependencies (Order Matters!)

### Step 1: Start IPFS Daemon

Initialize and start the IPFS daemon (if not already initialized):
```bash
ipfs init
ipfs daemon
```

### Step 2: Deploy Blockchain Contracts (if needed)

Compile and deploy contracts to the local Hardhat network:
```bash
cd blockchain
npx hardhat node
npx hardhat compile
npx hardhat deploy --network hardhat
cd ..
```

## 4. Running the D-PoDL System

Run the Python trainer module from the project root. This will automatically start Ray:
```bash
python -m dpodl_core.trainer
```

## 5. Monitoring and Troubleshooting

*   **Ray Dashboard:** Accessible at `http://<your_ip>:8265` for monitoring cluster status and jobs.
*   **Logs:** Check `/tmp/ray/session_latest/logs/` for Ray logs if issues arise.
*   **Network/Firewall:** Ensure ports 6379, 8076, 8077, and 8265 are open and accessible. Use `sudo iptables -A INPUT -p tcp --dport <port> -j ACCEPT` as needed.
*   **IPFS:** If you see connection errors, ensure the daemon is running and accessible on port 5001.

## 6. Testing

Run Python tests:
```bash
pytest tests/
```

Run Solidity tests:
```bash
cd blockchain
npx hardhat test
cd ..
```

## 7. Typical Workflow Summary

1. **Start IPFS daemon:**
   ```bash
   ipfs daemon
   ```
2. **Deploy contracts :**
   ```bash
   cd blockchain && npx hardhat node
   cd blockchain && npx hardhat compile && npx hardhat deploy --network hardhat && cd ..
   ```
3. **Run the trainer:**
   ```bash
   python -m dpodl_core.trainer
   ```

This order ensures all dependencies are available and avoids connection errors. Adjust IP addresses and ports as needed for your environment.

## 8. Project Structure Overview

(Refer to `docs/architecture.md` for a detailed architecture breakdown.)

*   `blockchain/`: Smart contracts, deployment scripts, Hardhat configuration.
    *   `contracts/`: Solidity source files.
    *   `deploy/`: Hardhat deployment scripts.
    *   `test/`: Hardhat JavaScript/TypeScript tests.
*   `dpodl_core/`: Python backend for AI training, Ray orchestration, IPFS, and blockchain interaction.
    *   `trainer.py`: Main script to start the distributed training.
    *   `worker.py`: Logic executed by each Ray worker.
    *   `blockchain_interface.py`: Handles contract interactions.
    *   `ipfs_utils.py`: IPFS helper functions.
    *   `crypto.py`: D-PoDL cryptographic logic.
    *   `models.py`: PyTorch model definition.
    *   `data_loader.py`: Data loading and preprocessing.
*   `docs/`: Project documentation.
*   `tests/`: Python unit and integration tests.
*   `requirements.txt`: Python dependencies.
*   `package.json`: Node.js dependencies (for `blockchain/` primarily).
*   `.gitignore`: Files and directories to ignore in Git.
*   `README.md`: Main project overview.

## 9. Common Issues & Troubleshooting

*   **Python Dependencies:** Ensure `pip install -r requirements.txt` completes successfully in your virtual environment.
*   **Node.js Dependencies:** Ensure `npm install` in `blockchain/` completes.
*   **Docker Services:** Check `docker ps` to ensure Ganache and IPFS containers are running. View logs with `docker-compose logs <service_name>`.
*   **Hardhat Deployment:** Verify network names in `hardhat.config.js` and the `--network` flag match. Check Ganache logs for deployment transactions.
*   **Ray Connection:** Ensure `ray start --head` is running. The trainer script needs the correct Ray head address.
*   **IPFS Daemon:** Make sure the IPFS daemon is running and accessible on the configured API port (usually 5001).
*   **Private Keys/RPC URLs:** Double-check that private keys (for contract deployment and interaction) and RPC URLs are correct and have funds if needed.

## 10. Environment Configuration

Ensure your `.env` file in the project root is correctly configured. Each Ray worker requires its own unique private key for signing blockchain transactions. If you are running `N` workers, you need to define `WORKER_PRIVATE_KEY_0` through `WORKER_PRIVATE_KEY_N-1`.

**Example for 2 workers:**
```
BLOCKCHAIN_NETWORK_URL="http://127.0.0.1:8545"
BLOCKCHAIN_CHAIN_ID="31337"
BLOCKCHAIN_NETWORK_NAME="localhost"

# Private key for Worker 0 (e.g., Hardhat Account #1)
WORKER_PRIVATE_KEY_0="0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"

# Private key for Worker 1 (e.g., Hardhat Account #2)
WORKER_PRIVATE_KEY_1="0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"

# Fallback/Test key for direct script runs (if any still use it, like blockchain_interface.py direct test)
TEST_WORKER_PRIVATE_KEY="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" # Example: Hardhat Account #0
```

*   **`WORKER_PRIVATE_KEY_X`**: The private key for worker with rank `X`. These should be distinct for each worker to avoid nonce conflicts.
*   **`TEST_WORKER_PRIVATE_KEY`**: This might be used by standalone test scripts or direct runs of `blockchain_interface.py`. Ensure it's different from worker keys if used concurrently.

This guide should help you get the D-PoDL project up and running locally. For more detailed information on specific components, refer to their respective documentation or the `docs/architecture.md` file. 