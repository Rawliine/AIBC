# System Architecture: AI & Blockchain Integration (D-PoDL)

## 1. Overview

This project implements a **Decentralized Proof of Deep Learning (D-PoDL)** system, integrating advanced Artificial Intelligence (AI) model training with blockchain technology. The core objective is to create a transparent, verifiable, and incentivized ecosystem for distributed AI model development.

The system leverages a Ray cluster for distributed AI training, Python-based workers that execute the D-PoDL protocol, smart contracts deployed on an Ethereum-compatible blockchain for governance and state management, and IPFS for decentralized storage of model artifacts and proofs.

## 2. Main Components

The system comprises several key components:

*   **AI/ML Compute Layer (Ray Cluster):**
    *   **Ray:** A distributed computing framework used to manage and scale AI training tasks across multiple workers and potentially multiple machines.
    *   **Python Workers (`dpodl_core/worker.py`):** These are Ray actors or tasks that execute the core D-PoDL training and proof-generation logic. Each worker is responsible for a segment of the D-PoDL lifecycle.
    *   **PyTorch & Transformers:** Used for defining and training the neural network models (e.g., `DeeperTransformer` for text classification).

*   **Blockchain Layer (Ethereum-based):**
    *   **Smart Contracts (`blockchain/contracts/`):**
        *   `DPoDLToken.sol`: An ERC20 token used for incentivizing participation (e.g., rewarding workers/miners).
        *   `ModelRegistry.sol`: The primary contract for recording the canonical chain of validated D-PoDL model "blocks." It enforces consensus rules (T1 hash, T_acc accuracy) and manages D-PoDL parameters.
        *   `MTXMempool.sol`: A mempool for "Model Transactions" (MTX) – proposed models that may not meet full block criteria but can serve as starting points or be recorded for their contributions.
    *   **Hardhat:** Development environment for compiling, deploying, and testing smart contracts.
    *   **Web3.py Interface (`dpodl_core/blockchain_interface.py`):** Enables Python components (workers, trainer) to interact with the deployed smart contracts (read state, submit transactions).

*   **Decentralized Storage Layer:**
    *   **IPFS (InterPlanetary File System):** Used for storing large files such as model checkpoints, training traces, and associated metadata. Content is addressed by its hash (CID), ensuring immutability and verifiability.

*   **Orchestration & Configuration:**
    *   **Trainer Script (`dpodl_core/trainer.py`):** Manages the overall D-PoDL training runs, initializes Ray, configures workers, and collects results.
    *   **Configuration Files (`.env`, `blockchain_config.py`):** Manage sensitive data (private keys, API keys) and blockchain connection details.

## 3. D-PoDL Lifecycle & Interaction Flow

The D-PoDL process involves a cyclical interaction between the AI compute layer and the blockchain.

### 3.1. Task Initiation & Reference Model Selection

1.  **Training Orchestration:** A training run is typically initiated via the `dpodl_core.trainer.py` script.
2.  **Reference Model Fetch:**
    *   The trainer (or each worker, depending on the exact flow division) queries the `ModelRegistry` smart contract (via `blockchain_interface.get_current_reference_cid()`) to fetch the IPFS CID of the latest validated model block. This CID serves as the `reference_model_id` for the new training cycle.
    *   If the registry is empty (genesis state), training may start from a predefined initial state or randomly.

### 3.2. Pre-Hash & Hash-to-Architecture (HtoA)

This phase occurs within each D-PoDL worker (`worker.py`):

1.  **Pre-Hash Calculation:**
    *   The worker takes the `prev_block_hash` (hash of the last block in `ModelRegistry` or a genesis hash) and the `reference_model_id`.
    *   It searches for a `nonce` such that `SHA3-256(prev_block_hash + reference_model_id + nonce)` results in a hash value (`pre_hash_value`) that is less than or equal to the current `t1Threshold` (difficulty target stored in `ModelRegistry`). This is a Proof-of-Work like step.
2.  **Seed Extraction:** A deterministic `random_seed` (for data shuffling, RNGs) and a `seed_for_weights` (for model weight initialization if not transferring) are extracted from the successful `pre_hash_value`.
3.  **Hash-to-Architecture (HtoA):**
    *   The `pre_hash_value` is used to deterministically derive the neural network's hyperparameters (e.g., `embed_dim`, `num_layers`, `num_heads`) from a predefined parameter space (`crypto.hash_to_architecture()`).
    *   A new model instance (e.g., `DeeperTransformer`) is created with this derived architecture.

### 3.3. Model Initialization & Distributed Training

1.  **Reference Model Weight Transfer (Optional):**
    *   If a `reference_model_id` was fetched, the worker attempts to download the corresponding model state dictionary from IPFS (using `ipfs_utils.load_model_state_from_ipfs()`).
    *   If successful, compatible weights are transferred from the reference model to the newly HtoA-generated model structure (`utils.transfer_weights()`).
    *   If no reference model or transfer fails, the new model's weights are initialized using the `seed_for_weights` extracted from the Pre-Hash.
2.  **Data Loading & Preparation:**
    *   The `data_loader.py` script loads a dataset (e.g., AG News), tokenizes it, and partitions it for the Ray workers. Each worker receives its data shard.
3.  **Distributed Training via Ray:**
    *   The `trainer.py` configures and launches the Ray `TorchTrainer`, which distributes the `worker_train_loop` to multiple Ray workers.
    *   Each worker trains its version of the model on its data partition for a set number of epochs/steps.
    *   **Training Integrity:**
        *   **Merkle Tree of States:** During training, workers periodically hash their model's state (`crypto.hash_model_state()`) and store these hashes. These are later used to construct a Merkle root, providing a compact proof of the training trajectory.
        *   **Training Trace:** Detailed logs of training steps (loss, duration, etc.) are collected. This trace is saved and its hash is also recorded.

### 3.4. Post-Epoch Validation & Proof Generation

After each training epoch (or a defined period) within the worker:

1.  **Evaluation:** The model's `accuracy` is evaluated on a validation dataset.
2.  **Final Model State Hash:** The state dictionary of the trained model is hashed (`crypto.hash_model_state()`) to get `final_model_state_hash`.
3.  **Post-Hash Calculation:**
    *   A `post_hash_value` is calculated using `SHA3-256(final_model_state_hash + accuracy + total_steps)` (`crypto.calculate_post_hash()`).
4.  **Post-Hash Verification:** The `post_hash_value` is checked against the `t2Threshold` (a secondary difficulty/validation target from `ModelRegistry`).

### 3.5. Checkpoint, IPFS Upload & Blockchain Submission

Based on the Post-Hash validity and accuracy:

1.  **Decision:**
    *   **Valid Block:** If `post_hash_value <= t2Threshold` AND `accuracy >= tAccuracyThresholdBPS` (from `ModelRegistry`), the result is a candidate for a new block in the `ModelRegistry`.
    *   **Model Transaction (MTX):** If `post_hash_value <= t2Threshold` BUT `accuracy < tAccuracyThresholdBPS`, the result may be submitted to the `MTXMempool`.
    *   **Discard:** If `post_hash_value > t2Threshold`, the result is typically discarded.
2.  **Checkpointing & IPFS:**
    *   If not discarded, the worker creates a comprehensive checkpoint (`utils.save_checkpoint()`) containing:
        *   Model state dictionary.
        *   Optimizer state.
        *   Epoch, loss, accuracy.
        *   All D-PoDL metadata: `pre_hash_value`, `nonce`, `reference_model_id`, seeds, thresholds used, `final_model_state_hash`, `post_hash_value`, Merkle root of intermediate states, hash of the training trace.
    *   This checkpoint file is **uploaded to IPFS**, yielding an `ipfs_cid`.
3.  **Blockchain Transaction:**
    *   The worker uses its private key (`WORKER_PRIVATE_KEY`) to sign and send a transaction (via `blockchain_interface.py`):
        *   **To `ModelRegistry.submitBlock()`:** If it's a valid block candidate. Parameters include `ipfs_cid`, `accuracy_bps`, `steps`, `post_hash` (integer), and `reference_cid`.
        *   **To `MTXMempool.submitMtx()`:** If it's an MTX candidate. Parameters include `ipfs_cid`, `accuracy_bps`, `steps`, and `reference_cid`.
    *   The smart contract validates the submission against its current state and rules. For `ModelRegistry`, this includes checking the `reference_cid`, `accuracy_bps` against `tAccuracyThresholdBPS`, and `post_hash` against `t1Threshold` (note: the worker's `pre_hash_value` met `t1Threshold`, while the `post_hash_value` from the worker is submitted to the contract and also checked against a threshold, which appears to be `t1Threshold` again in `ModelRegistry.sol:submitBlock`, which might need clarification if T1 and T2 are distinct or if T1 applies to both pre and post hashes in the registry context).
        *Self-correction during thought process: `ModelRegistry.submitBlock` validates `_postHash < t1Threshold`. The `worker.py` calculates `pre_hash` against `t1_threshold` and `post_hash` against `t2_threshold`. If `t1Threshold` and `t2Threshold` can be different, the worker decides based on `t2_threshold` but the contract `ModelRegistry` might re-validate the submitted `_postHash` against its own `t1Threshold`. This detail needs careful alignment between worker logic and contract logic for final block acceptance.*

### 3.6. Rewards & Cycle Repetition

1.  **Rewards:**
    *   If a block is successfully accepted by `ModelRegistry`, the contract mints `DPoDLToken`s (via its `MINTER_ROLE` on the token contract) and sends them to the `proposer` (the worker's address).
2.  **New Cycle:** The newly accepted block's IPFS CID becomes the `reference_model_id` for the next cycle of the D-PoDL process. The system is designed for continuous improvement and contribution.

## 4. Data and Control Flow Summary

*   **Control:** Initiated by `trainer.py`, distributed by Ray. Workers drive the D-PoDL cycle, interacting with IPFS and Blockchain. Smart contracts govern state transitions and rewards.
*   **Data:**
    *   **Dataset:** Sourced (e.g., AG News), tokenized, partitioned by `data_loader.py`.
    *   **Models:** Architecture derived via HtoA. State dictionaries stored as checkpoints.
    *   **Proofs & Metadata:** Pre-Hash, Post-Hash, Merkle roots, trace hashes, D-PoDL parameters are generated and stored within checkpoints.
    *   **Storage:** Checkpoints (containing models and all proofs/metadata) are stored on IPFS. Blockchain stores CIDs and core consensus parameters.

This architecture aims to establish a verifiable, decentralized, and progressively self-improving AI model development ecosystem.
