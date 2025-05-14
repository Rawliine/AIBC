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

This section details the components that need to be running. For a concise typical workflow, see Section 7.

### Step 1: Start IPFS Daemon

Initialize and start the IPFS daemon (if not already initialized):
```bash
ipfs init
ipfs daemon
```

### Step 2: Deploy Blockchain Contracts (if needed)

For local development, you'll start a local Hardhat node and deploy your contracts to it.

**1. Start Hardhat Node (in a separate terminal):**
Navigate to the `blockchain/` directory and run:
```bash
cd blockchain
npx hardhat node
```
**Important:** Keep this terminal window open.

**2. Compile and Deploy Contracts (in another terminal):**
Navigate to the `blockchain/` directory (if not already there) and run:
```bash
cd blockchain
npx hardhat compile
npx hardhat deploy --network hardhat
cd .. 
```
This deploys to the `hardhat` network which the `npx hardhat node` command just started.
The `cd ..` returns you to the project root.

## 4. Running the D-PoDL System

Run the Python trainer module from the project root. This will automatically start Ray:
```bash
python -m dpodl_core.trainer
```

**Note on Environment Profiles:**
The system supports different environment profiles using the `DPODL_ENV` environment variable:
*   **`dev` (default if `DPODL_ENV` is not set or set to `dev`):** Uses the standard, full configurations for dataset size, model complexity, etc.
*   **`test`:** Uses a "tiny" dataset and simplified model parameters for significantly faster execution, ideal for local development, quick tests, and debugging.

To run with the **test environment**:
1.  Ensure you have created the tiny dataset (see Section 4.1).
2.  Set the environment variable in your terminal:
    ```bash
    export DPODL_ENV=test
    ```
3.  Then run the trainer:
    ```bash
    python -m dpodl_core.trainer
    ```

### 4.1. Creating the Tiny Dataset (for Test Environment)

The `test` environment relies on a small version of the AG News dataset. To generate this:
1.  Navigate to the project root directory.
2.  Run the script:
    ```bash
    python scripts/create_tiny_dataset.py
    ```
    This will create the necessary data files in `./data/ag_news_tiny/`. This step only needs to be done once.

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

These are the essential steps to run the D-PoDL system for typical local development after initial setup:

1.  **Start IPFS Daemon (if not already running):**
    Open a terminal and run:
    ```bash
    ipfs daemon
    ```

2.  **Start Local Blockchain Node & Deploy Contracts:**
    *   **Terminal 1 (Blockchain Node):**
        ```bash
        cd blockchain
        npx hardhat node
        ```
        (Keep this running)
    *   **Terminal 2 (Deploy Contracts):**
        ```bash
        cd blockchain
        npx hardhat compile && npx hardhat deploy --network hardhat
        cd ..
        ```

3.  **Run the D-PoDL Trainer (from project root):**
    Open another terminal (or use one where you ran contract deployment) and ensure you are in the project root directory:
    ```bash
    python -m dpodl_core.trainer
    ```

This order ensures all dependencies are available.

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
    *   `config_utils.py`: Manages loading of environment-specific configurations.
*   `docs/`: Project documentation.
*   `tests/`: Python unit and integration tests.
*   `scripts/`: Helper scripts (e.g., for dataset creation).
*   `requirements.txt`: Python dependencies.