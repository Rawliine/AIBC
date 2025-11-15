# Project Documentation

## `dpodl_core/trainer.py`
*   **Description:** This file orchestrates the distributed D-PoDL (Decentralized Proof of Deep Learning) training using Ray Train. It handles Ray initialization, dataset loading and partitioning, worker configuration (including D-PoDL parameters), and the execution of the training process. It also processes results from workers, including block candidates and Model Transactions (MTXs), and interacts with the blockchain to fetch pending MTXs and update the reference model.
*   **Functions:**
    *   `run_training(cli_num_workers: int = None)`:
        *   **Description:** The main function that sets up and runs the D-PoDL training. It loads configurations, initializes Ray, prepares data partitions, determines the reference model CIDs (from config override or blockchain), sets up worker configurations, initializes and runs the Ray `TorchTrainer`. After training, it processes results from worker reports (metrics dataframe) to identify block candidates and new MTX candidates. It then fetches pending MTXs from the blockchain, evaluates them, selects the best MTX, updates its status on the blockchain, and finally calls the `ModelRegistry` smart contract to update the global reference model.
        *   **Variables:**
            *   `app_config`: Loaded application configuration.
            *   `num_workers`: Number of Ray workers.
            *   `train_partitions`, `val_partition`: Data partitions for training and validation.
            *   `current_ref_model_state_cid_for_run`, `current_ref_dpodl_checkpoint_cid_for_run`: CIDs for the reference model state and D-PoDL checkpoint.
            *   `train_loop_config`: Configuration dictionary passed to each worker.
            *   `scaling_config`, `run_config`: Ray AIR scaling and run configurations.
            *   `trainer`: Ray `TorchTrainer` instance.
            *   `result`: Result object from `trainer.fit()`.
            *   `block_candidates`, `new_mtx_candidates`: Lists to store candidate submissions from workers.
            *   `pending_mtxs_from_chain`: List of MTXs fetched from the `MTXMempool` contract.
            *   `evaluated_mtxs`: List of MTXs after fetching their details from IPFS.
            *   `best_mtx_candidate`: The selected MTX to update the reference model.
            *   `dpodl_checkpoint_cid_to_submit`, `mtx_id_to_submit`, `model_state_cid_to_submit`: Details of the best MTX for blockchain submission.
            *   `signer_private_key`: Private key for the registry operator.
            *   `status_update_receipt`, `update_receipt`: Transaction receipts from blockchain interactions.
*   **Interactions:**
    *   Uses `ray` for distributed training.
    *   `dpodl_core.data_loader.load_dataset_and_partition` for data loading.
    *   `dpodl_core.worker.worker_train_loop` as the training function for each Ray worker.
    *   `dpodl_core.utils.logger` for logging.
    *   `dpodl_core.blockchain_interface` for all smart contract interactions (getting reference CIDs, fetching MTXs, updating MTX status, updating model registry).
    *   `dpodl_core.config_utils.get_config` for application configuration.
    *   `dpodl_core.ipfs_utils.load_pickled_dict_from_ipfs` to load D-PoDL state from MTX CIDs.

## `dpodl_core/utils.py`
*   **Description:** This file provides utility functions used across the `dpodl_core` package, including memory logging, checkpoint saving/loading, model weight transfer, and data collation.
*   **Functions:**
    *   `log_memory_usage_gpu(msg="")`: Logs GPU memory usage if CUDA is available.
    *   `log_memory_usage_cpu(msg="")`: Logs CPU memory (RSS) usage.
    *   `save_checkpoint(epoch: int, model: torch.nn.Module, optimizer: torch.optim.Optimizer, loss: float, checkpoint_path: str, dpodl_state: dict = None, upload_to_ipfs_flag: bool = True)`: Saves a training checkpoint (model state, optimizer state, epoch, loss, D-PoDL state) locally and optionally uploads it to IPFS.
        *   **Variables:** `state`, `checkpoint_dir`, `ipfs_cid`.
        *   **Returns:** IPFS CID if uploaded successfully, otherwise the local `checkpoint_path` or `None` on error.
    *   `load_checkpoint(checkpoint_path: str, model: torch.nn.Module, optimizer: torch.optim.Optimizer)`: Loads a training checkpoint from a local file, restoring model, optimizer, epoch, and D-PoDL state.
        *   **Variables:** `start_epoch`, `loss`, `dpodl_state`, `checkpoint`.
        *   **Returns:** Tuple `(start_epoch, loss, dpodl_state)`.
    *   `transfer_weights(source_state_dict: OrderedDict, target_model: torch.nn.Module)`: Transfers weights from a source `state_dict` to a target model, matching layers by name and shape.
        *   **Variables:** `target_state_dict`, `transferred_count`, `skipped_count`, `new_state_dict`.
    *   `collate_batch(batch_data, seq_len=32)`: Collates a batch of data from Hugging Face dataset format to PyTorch tensors, handling padding and truncation.
        *   **Variables:** `texts`, `labels`, `padding_token_id`, `texts_t`, `labels_t`.
        *   **Returns:** Tuple `(texts_t, labels_t)` as PyTorch tensors.
*   **Interactions:**
    *   Uses `torch` for model and tensor operations.
    *   `psutil` for CPU memory monitoring.
    *   `ipfshttpclient` for IPFS interactions.
    *   `logging` for logging.

## `dpodl_core/worker.py`
*   **Description:** This file contains the main training loop executed by each Ray worker. It implements the D-PoDL protocol, including Pre-Hash (nonce mining, T1 verification), deterministic model initialization (Hash-to-Architecture or HtoA), training epochs, Post-Hash (T2 verification), checkpointing (local and IPFS), Merkle tree construction for state verification, and submission of results (block or MTX candidates) to the blockchain and Ray Train.
*   **Functions:**
    *   `evaluate_accuracy(model, val_dataset, batch_size, device, seq_len, collate_fn)`: Evaluates the model's accuracy on the validation dataset.
        *   **Variables:** `val_loader`, `correct`, `total`, `accuracy`.
        *   **Returns:** Accuracy (float).
    *   `worker_train_loop(config)`: The main function executed by each Ray worker.
        *   **Description:**
            1.  **Setup:** Initializes logging, fetches configuration, sets device.
            2.  **Pre-Hash:** Finds a valid `nonce` that satisfies the `t1_threshold` by hashing `prev_block_hash`, `reference_model_id`, and `nonce`. Extracts a `random_seed` from the valid `pre_hash_value`.
            3.  **Model Initialization:** Derives model architecture parameters (`final_architecture_params`) and a `seed_for_weights` using HtoA from `pre_hash_value`, or uses `model_override_params` from config. Instantiates the `DeeperTransformer` model. Loads worker-specific private key. Optionally loads a `reference_model_state` from IPFS and transfers weights if `transfer_reference_weights` is enabled. If no reference model, initializes weights deterministically using `seed_for_weights`.
            4.  **Training Setup:** Initializes optimizer, loads data partition. Loads checkpoint if available, restoring epoch, loss, and `loaded_dpodl_state` (including D-PoDL parameters, hashes, and steps). Sets up deterministic RNGs using `random_seed`.
            5.  **Training Loop (Epochs & Batches):**
                *   Iterates through epochs and batches.
                *   Performs training steps (forward pass, loss calculation, backward pass, optimizer step).
                *   Records training trace (`training_trace`) with step details (loss, duration).
                *   Periodically hashes the model state (`hash_model_state`) and stores it in `checkpoint_hashes` for Merkle tree construction.
            6.  **Post-Epoch:**
                *   Evaluates model `accuracy`.
                *   Calculates `final_model_state_hash_hex` and `post_hash_value` (from final model hash, accuracy, steps).
                *   Verifies `post_hash_value` against `t2_threshold`.
                *   Builds a Merkle tree from `checkpoint_hashes` to get `merkle_root_hex`.
                *   Performs D-PoDL state consistency verification (`verify_proof_of_training_consistency`).
                *   Decides `action` ("SAVE_BLOCK_CHECKPOINT", "SAVE_MTX_CHECKPOINT", or "DISCARD") based on Post-Hash validity, accuracy vs `t_acc_threshold`, and state consistency.
            7.  **Checkpointing & Submission:**
                *   If action is SAVE_BLOCK/MTX_CHECKPOINT:
                    *   Saves training trace to a temporary file and calculates `trace_hash_hex`.
                    *   Collects `current_dpodl_state` (all D-PoDL parameters, hashes, CIDs, accuracy, steps, Merkle root, trace hash).
                    *   Saves this D-PoDL state and model to a local checkpoint file (`save_checkpoint`), optionally uploading to IPFS.
                    *   If IPFS is enabled:
                        *   Saves the final model state (`model.state_dict()`) to IPFS, getting `final_model_cid_for_tx`.
                        *   Saves `current_dpodl_state` (which now includes `model_weights_ipfs_cid` if it's an MTX) to IPFS, getting `checkpoint_data_cid_for_tx`.
                        *   Submits to blockchain:
                            *   `submit_block` (with `final_model_cid_for_tx`, `checkpoint_data_cid_for_tx`, etc.) if action is SAVE_BLOCK_CHECKPOINT.
                            *   `submit_mtx` (with `checkpoint_data_cid_for_tx` as the main IPFS CID, accuracy, steps, etc., signed by `worker_private_key`) if action is SAVE_MTX_CHECKPOINT.
                    *   Reports submission details (action, CIDs, tx_hash, accuracy, steps, rank) to Ray Train using `ray.train.report`.
            8.  **Reporting & Cleanup:** Reports epoch metrics (loss, accuracy, steps, action) to Ray Train. Clears `training_trace`.
            9.  **Error Handling:** Includes a `try-except` block for the main training loop. If an error occurs, it attempts to save an emergency trace and an emergency checkpoint with the current D-PoDL state before re-raising the exception.
        *   **Variables:**
            *   `rank`, `world_size`: Ray worker context.
            *   `device`: "cuda" or "cpu".
            *   `train_partition`, `val_partition`, `seq_len`, `batch_size`, `epochs`, `lr`: Training parameters from config.
            *   `prev_block_hash`, `reference_model_id`, `t1_threshold`, `t2_threshold`, `checkpoint_path`, `t_acc_threshold`, `ipfs_enabled`, `model_override_params`: D-PoDL and operational parameters from config.
            *   `nonce`, `pre_hash_value`, `found_nonce`: Pre-Hash stage variables.
            *   `random_seed`: Seed extracted from `pre_hash_value`.
            *   `derived_config_htoa`, `architecture_params_htoa`, `seed_for_weights`, `final_architecture_params`: HtoA variables.
            *   `model`: `DeeperTransformer` instance.
            *   `worker_private_key`, `signer_address`: Worker's blockchain signing key and address.
            *   `reference_model_state`: State dict of the reference model loaded from IPFS.
            *   `optimizer`: `torch.optim.Adam` instance.
            *   `start_epoch`, `prev_loss`, `loaded_dpodl_state`: Loaded from checkpoint.
            *   `rng`: PyTorch random number generator.
            *   `total_steps_so_far`, `steps_this_run`, `checkpoint_hashes`, `training_trace`: Training progress and Merkle tree data.
            *   `epoch_loss`, `step_count`, `current_total_step`: Loop variables.
            *   `texts_t`, `labels_t`, `logits`, `loss`: Batch training variables.
            *   `accuracy`: Validation accuracy.
            *   `final_model_state_hash_bytes`, `final_model_state_hash_hex`, `post_hash_value`, `is_post_hash_valid`: Post-Hash stage variables.
            *   `merkle_root`, `merkle_root_hex`: Merkle tree root.
            *   `current_dpodl_state_for_verification`, `is_state_consistent`: D-PoDL state for verification.
            *   `action`: Worker's decision ("SAVE_BLOCK_CHECKPOINT", "SAVE_MTX_CHECKPOINT", "DISCARD").
            *   `submitted_model_cid_for_record`, `tx_hash_for_record`: For reporting to Ray Train.
            *   `trace_file_path`, `trace_hash_hex`: Training trace details.
            *   `current_dpodl_state`: D-PoDL state saved to checkpoint.
            *   `ipfs_cid_from_save`: CID of the saved checkpoint from `save_checkpoint`.
            *   `final_model_cid_for_tx`, `checkpoint_data_cid_for_tx`: CIDs for blockchain submission.
            *   `submission_receipt`: Receipt from blockchain transaction.
            *   `submission_details_for_report`, `metrics_to_report`: Dictionaries reported to Ray Train.
            *   `emergency_trace_hash_hex`, `emergency_trace_file_path`, `emergency_dpodl_state`, `emergency_cid`: For error handling.
*   **Interactions:**
    *   `ray.train.get_context`, `ray.train.report` for Ray Train integration.
    *   `torch` for model, optimizer, data loading, and tensor operations.
    *   `dpodl_core.models.DeeperTransformer` for the model architecture.
    *   `dpodl_core.utils` for logging, checkpointing (`save_checkpoint`, `load_checkpoint`), data collation (`collate_batch`), and weight transfer (`transfer_weights`).
    *   `dpodl_core.ipfs_utils` for loading reference model (`load_model_state_from_ipfs`), saving final model state (`save_model_state_to_ipfs`), saving D-PoDL state (`save_checkpoint_data_to_ipfs`).
    *   `dpodl_core.crypto` for all cryptographic operations (hashing, Merkle tree, Pre-Hash, Post-Hash, HtoA).
    *   `dpodl_core.blockchain_interface` for submitting blocks (`submit_block`) and MTXs (`submit_mtx`).
    *   `dpodl_core.verification` for D-PoDL state consistency checks (`verify_proof_of_training_consistency`).

## `dpodl_core/blockchain_interface.py`
*   **Description:** This file handles all interactions with the Ethereum blockchain via Web3.py. It initializes the Web3 connection, loads smart contract ABIs and addresses, and provides functions to read from and write to the `ModelRegistry`, `MTXMempool`, and `DPoDLToken` contracts.
*   **Global Variables:**
    *   `w3`: Web3 instance.
    *   `registry_contract`, `mempool_contract`, `token_contract`: Web3 contract objects.
    *   `TX_TIMEOUT`: Timeout for waiting for transaction receipts.
    *   `MTX_STATUS_MAP`: Mapping of MTX status codes to human-readable strings.
*   **Functions:**
    *   `initialize_blockchain_connection()`: Initializes the global `w3` instance and contract objects using `NETWORK_URL`, `CHAIN_ID`, and contract details from `blockchain_config.get_contract_info()`. Injects PoA middleware if needed.
    *   `get_w3()`, `get_registry()`, `get_mempool()`, `get_token()`: Helper functions to access the global Web3 and contract instances.
    *   `get_current_reference_model_state_cid() -> str | None`: Reads `currentModelStateCID` from `ModelRegistry`.
    *   `get_current_reference_dpodl_checkpoint_cid() -> str | None`: Reads `currentDpodlCheckpointCID` from `ModelRegistry`.
    *   `get_mtx_mempool_count() -> int | None`: Reads MTX count from `MTXMempool.getMtxCount()`.
    *   `get_mtx_details(mtx_id: int) -> dict | None`: Fetches details of a specific MTX from `MTXMempool.getMtxDetails()`.
    *   `fetch_pending_mtxs() -> list`: Fetches all MTXs with "Pending" status from `MTXMempool` by iterating through `getMtxDetails()`.
    *   `get_model_registry_mempool_address() -> str | None`: Reads the configured `mtxMempoolContract` address from `ModelRegistry`.
    *   `_send_signed_transaction(w3_instance, chain_id, transaction, private_key)`: A private helper function to sign and send a transaction. It handles gas estimation (with fallback), EIP-1559 fee calculation, nonce retrieval, signing, sending the raw transaction, and waiting for the receipt. It includes detailed logging and error handling, including attempting to get revert reasons for failed transactions.
        *   **Variables:** `account`, `address`, `minimal_call_tx`, `call_result`, `gas_estimate`, `max_priority_fee_per_gas`, `base_fee`, `max_fee_per_gas`, `nonce`, `signed_tx`, `raw_tx_bytes_for_sending`, `tx_hash`, `receipt`, `tx_details`, `call_params`, `revert_call_result`, `reason`.
        *   **Returns:** A dictionary with `tx_hash`, `receipt`, `status`, and optionally `error` or `mtxId`.
    *   `submit_block(...) -> dict | None`: Builds and sends a transaction to `ModelRegistry.submitBlock()`.
        *   **Parameters:** `new_model_state_cid`, `new_dpodl_checkpoint_cid`, `accuracy_bps`, `steps`, `post_hash`, `reference_dpodl_checkpoint_cid`, `signer_private_key`.
    *   `submit_mtx(ipfs_cid: str, accuracy_bps: int, steps: int, reference_cid: str, signer_private_key: str) -> dict | None`: Builds and sends a transaction to `MTXMempool.submitMtx()`. Parses the `MtxSubmitted` event to extract `mtxId`.
        *   **Variables:** `transaction`, `send_result`, `actual_receipt`, `tx_hash_hex`, `events`, `parsed_mtx_id`.
    *   `update_reference_model_from_mtx(model_state_cid: str, dpodl_checkpoint_cid: str, mtx_id: int, signer_private_key: str) -> dict | None`: Builds and sends a transaction to `ModelRegistry.updateReferenceModelFromMtx()`. Includes detailed error logging for `ContractLogicError`.
    *   `update_mtx_status(mtx_id: int, status_code: int, signer_private_key: str) -> dict | None`: Builds and sends a transaction to `MTXMempool.updateMtxStatus()`. Parses the `MtxStatusUpdated` event.
    *   `log_receipt_details(receipt)`: Logs details of a transaction receipt.
*   **Interactions:**
    *   `web3.Web3` for Ethereum blockchain interaction.
    *   `eth_account` for transaction signing.
    *   `dotenv` for loading environment variables.
    *   `dpodl_core.blockchain_config` for network URL, chain ID, and contract information (`get_contract_info`).
    *   Uses ABIs of `ModelRegistry`, `MTXMempool`, and `DPoDLToken` (loaded via `get_contract_info`).

## `dpodl_core/ipfs_utils.py`
*   **Description:** This file provides utilities for interacting with IPFS, including adding and loading raw data, model states, and checkpoint data. It also includes functionality for pinning data to Pinata for persistence.
*   **Global Variables:**
    *   `_ipfs_client`: Global `ipfshttpclient.Client` instance.
*   **Functions:**
    *   `_prepare_dict_for_pickle(data_dict)`: Recursively prepares a dictionary for pickling by moving PyTorch tensors to CPU. Handles nested dictionaries and lists of tensors.
    *   `get_ipfs_client()`: Returns a memoized `ipfshttpclient` connected to `IPFS_HOST`.
    *   `add_data_to_ipfs(data: bytes) -> str | None`: Adds raw bytes to IPFS.
    *   `load_data_from_ipfs(cid: str) -> bytes | None`: Loads raw bytes from IPFS given a CID.
    *   `pin_to_pinata(cid: str, name: str = None) -> bool` (async): Pins a CID to Pinata using API key/secret or JWT from `PinataConfig`. Handles duplicate pins.
        *   **Variables:** `use_jwt`, `headers`, `body`, `response`, `result`, `error_status`, `error_data_json`.
    *   `save_model_state_to_ipfs(model_state: dict, model_name: str) -> str | None` (async): Saves a model's `state_dict` to IPFS (after serializing with `torch.save`) and pins it to Pinata.
        *   **Variables:** `buffer`, `model_bytes`, `res`.
    *   `load_model_state_from_ipfs(cid: str, model_name: str) -> dict | None`: Loads a model's `state_dict` (serialized with `torch.save`) from IPFS.
        *   **Variables:** `model_bytes`, `buffer`, `model_state`.
    *   `save_checkpoint_data_to_ipfs(checkpoint_data: dict, name: str = "dpodl_checkpoint_data") -> str | None` (async): Saves checkpoint data (a dictionary, prepared with `_prepare_dict_for_pickle` and serialized with `torch.save`) to IPFS and pins it.
        *   **Variables:** `prepared_checkpoint_data`, `buffer`, `data_bytes`, `res`.
    *   `load_checkpoint_data_from_ipfs(cid: str, name: str) -> dict | None`: Loads JSON checkpoint data from IPFS. **Note:** The implementation uses `json.loads`, but `save_checkpoint_data_to_ipfs` uses `torch.save`. This is inconsistent. It should likely use `load_pickled_dict_from_ipfs` or `save_checkpoint_data_to_ipfs` should save as JSON if this function is intended to load JSON.
        *   **Variables:** `json_bytes`, `checkpoint_data`.
    *   `load_pickled_dict_from_ipfs(cid: str, name: str = "dpodl_checkpoint_pickle") -> dict | None`: Loads a pickled dictionary (e.g., D-PoDL state saved with `torch.save`) from IPFS using `torch.load`.
        *   **Variables:** `pickled_bytes`, `buffer`, `data_dict`.
    *   `merge_model_states(state_dicts: list[dict]) -> dict`: Averages the parameters of multiple model `state_dict`s.
        *   **Variables:** `merged_state`, `num_models`, `params_to_avg`, `float_params`, `avg_param`.
*   **Interactions:**
    *   `ipfshttpclient` for local IPFS daemon communication.
    *   `torch` for saving/loading model states and preparing dictionaries.
    *   `requests` for Pinata API interaction.
    *   `asyncio` for managing async Pinata calls within sync contexts (though `save_model_state_to_ipfs` and `save_checkpoint_data_to_ipfs` are themselves async).
    *   `dpodl_core.blockchain_config.IPFS_HOST`, `dpodl_core.blockchain_config.PinataConfig`.

## `dpodl_core/config_utils.py`
*   **Description:** This file manages application configurations. It defines a default (development) configuration and allows overriding parameters for a test environment based on the `DPODL_ENV` environment variable.
*   **Global Variables:**
    *   `DEFAULT_CONFIG`: Dictionary holding default configuration values (dataset, model, D-PoDL parameters, IPFS settings).
    *   `TEST_CONFIG_OVERRIDES`: Dictionary holding overrides for the "test" environment (e.g., smaller dataset, fewer epochs, simplified model).
*   **Functions:**
    *   `get_config()`: Returns the active configuration dictionary based on `DPODL_ENV`. If "test", it merges `TEST_CONFIG_OVERRIDES` into `DEFAULT_CONFIG`.
        *   **Variables:** `env`, `config`.
*   **Interactions:**
    *   Uses `os.getenv` to read `DPODL_ENV`.
    *   `logging` for information messages.

## `dpodl_core/data_loader.py`
*   **Description:** This file is responsible for loading, tokenizing, and partitioning datasets for distributed training with Ray. It supports loading datasets from Hugging Face Hub or a local path, sub-sampling, and creating data partitions for each Ray worker.
*   **Functions:**
    *   `load_partition(dataset, indices: List[int])` (`@ray.remote`): A Ray remote function that loads a specific partition of a Hugging Face dataset using a list of indices.
        *   **Variables:** `subset`.
        *   **Returns:** A Hugging Face `Dataset` subset.
    *   `load_dataset_and_partition(...) -> Dict[str, Any]`:
        *   **Description:** Loads a dataset (from Hugging Face or local path), optionally sub-samples it for training and validation, tokenizes the text data using a "bert-base-uncased" tokenizer, and partitions the training set indices for distribution to Ray workers. The actual data loading for partitions is then done via the remote `load_partition` function.
        *   **Parameters:** `dataset_name`, `num_workers`, `batch_size`, `split_ratio`, `dataset_path_override`, `num_train_samples`, `num_val_samples`.
        *   **Variables:**
            *   `full_train_dataset`, `full_val_dataset`: Loaded (and potentially sub-sampled) Hugging Face datasets.
            *   `dataset`, `dataset_hf`, `dataset_dict_temp`, `dataset_dict_hf`: Intermediate dataset objects.
            *   `tokenizer`: `AutoTokenizer` instance.
            *   `tokenized_train_dataset`, `tokenized_val_dataset`: Datasets after tokenization.
            *   `vocab`: Vocabulary mapping from tokenizer.
            *   `train_size`, `train_indices`, `chunk_size`, `splitted_indices`: Variables for partitioning logic.
            *   `futures`, `train_partitions`: For Ray remote task execution and results.
        *   **Returns:** A dictionary containing `vocab`, `tokenizer`, `train_partitions` (list of Hugging Face `Dataset` objects, one per worker), and `val_dataset` (tokenized Hugging Face `Dataset`).
*   **Interactions:**
    *   `ray` for remote data partitioning (`@ray.remote`, `ray.get`).
    *   `datasets` (Hugging Face library) for `load_dataset`, `DatasetDict`, `Dataset`.
    *   `transformers` (Hugging Face library) for `AutoTokenizer`.
    *   `torch` (implicitly, as Hugging Face datasets can be converted to Torch tensors).
    *   `logging` for messages.

## `dpodl_core/blockchain_config.py`
*   **Description:** This file centralizes blockchain-related configurations, such as network URLs, chain IDs, paths to contract deployment artifacts, and IPFS/Pinata settings. It loads sensitive information from a `.env` file.
*   **Global Variables:**
    *   `NETWORK_URL`, `CHAIN_ID`, `NETWORK_NAME`: Blockchain network parameters.
    *   `DEPLOYMENTS_PATH`: Path to Hardhat deployment artifacts.
    *   `FUND_WORKERS_ON_START`, `MIN_WORKER_BALANCE_ETH`, `FUND_AMOUNT_ETH`: Parameters for worker funding (not directly used by other read files but present).
    *   `IPFS_HOST`: IPFS daemon connection string.
    *   `PinataConfig` (class): Contains `PINATA_API_KEY`, `PINATA_SECRET_API_KEY`, `PINATA_JWT`, `PINATA_API_URL`, `ENABLE_PINNING`.
    *   `DEFAULT_T1_THRESHOLD`, `DEFAULT_ACCURACY_THRESHOLD_BPS`, etc.: Default D-PoDL parameters (likely fallbacks or for reference, as contracts might hold the canonical values).
*   **Functions:**
    *   `get_contract_info(contract_name: str, network_name: str = NETWORK_NAME) -> tuple[str, dict] | tuple[None, None]`: Loads the contract address and ABI from the JSON deployment file found in `DEPLOYMENTS_PATH` for the specified contract and network.
        *   **Variables:** `deployment_file`, `deployment_data`, `contract_address`, `contract_abi`.
*   **Interactions:**
    *   `os.getenv` and `dotenv.load_dotenv` for reading environment variables from `.env`.
    *   `pathlib.Path` for path manipulation.
    *   `json` for loading contract artifact files.

## `dpodl_core/verification.py`
*   **Description:** This file provides functions for cryptographic verification related to the D-PoDL protocol. This includes generating and verifying Merkle proofs for checkpointed model states and performing comprehensive consistency checks on the D-PoDL state dictionary.
*   **Functions:**
    *   `generate_merkle_proof_for_step(target_step: int, checkpoint_hashes: OrderedDict[int, bytes]) -> list[tuple[bytes, bool]] | None`: Generates a Merkle proof for a specific checkpoint step hash given an ordered dictionary of all checkpoint hashes.
        *   **Variables:** `leaf_hashes`, `leaf_keys`, `leaf_index`, `merkle_root_bytes`, `tree_levels`, `proof`.
    *   `verify_checkpoint_merkle_proof(target_step: int, target_hash_hex: str, proof_hex: list[tuple[str, bool]], expected_root_hex: str, all_checkpoint_keys: list[int]) -> bool`: Verifies a Merkle proof for a given target hash (hex) against an expected root hash (hex), using the proof path (hex) and the list of all original step keys to determine the correct leaf index.
        *   **Variables:** `target_hash_bytes`, `expected_root_bytes`, `proof_bytes`, `leaf_index`, `is_valid`.
    *   `verify_proof_of_training_consistency(dpodl_state: dict) -> bool`: Performs comprehensive internal consistency checks on a D-PoDL state dictionary.
        *   **Description:** Checks for the presence of essential keys. Recalculates and verifies:
            1.  Pre-Hash against stored `pre_hash_value` and `t1_threshold`.
            2.  `random_seed` derived from `pre_hash_value`.
            3.  Post-Hash against stored `post_hash_value` and `t2_threshold`.
            4.  Merkle Root by rebuilding the tree from `checkpoint_hashes`.
        *   **Variables:** `checks_passed`, `missing_keys`, `required_keys`, `prev_bk`, `ref_id`, `nonce`, `pre_hash_stored`, `t1`, `pre_hash_calculated`, `seed_stored`, `seed_calculated`, `final_hash`, `accuracy`, `steps`, `post_hash_stored`, `t2`, `post_hash_calculated`, `stored_hashes_map`, `stored_merkle_root`, `expected_empty_root_hex`, `leaf_hashes_bytes`, `sorted_step_keys`, `recalculated_root_bytes`, `recalculated_root_hex`.
    *   `load_and_verify_checkpoint_state(checkpoint_path: str) -> bool`: A helper function that loads a checkpoint using `utils.load_checkpoint` and then runs `verify_proof_of_training_consistency` on its D-PoDL state.
        *   **Variables:** `dpodl_state`, `start_epoch`, `loss`.
*   **Interactions:**
    *   `dpodl_core.crypto` for Merkle tree operations (`build_merkle_tree`, `get_merkle_proof`, `verify_merkle_proof`), hashing (`calculate_pre_hash`, `calculate_post_hash`, `bytes_to_hex`, `hash_bytes`), and threshold verification (`verify_pre_hash_threshold`, `verify_post_hash_threshold`), seed extraction (`extract_seed_from_hash`).
    *   `dpodl_core.utils.load_checkpoint` to load checkpoint data for verification.
    *   `logging` for messages.
    *   `collections.OrderedDict`.

## `dpodl_core/crypto.py`
*   **Description:** This file implements various cryptographic primitives and utilities required for the D-PoDL protocol. This includes hashing functions, Merkle tree construction and proof generation/verification, Pre-Hash and Post-Hash calculations, seed extraction, and a deterministic Hash-to-Architecture (HtoA) mapping.
*   **Global Variables:**
    *   `PARAM_SPACE`: A dictionary defining the possible values for model architecture parameters used in HtoA (e.g., `embed_dim`, `num_heads`, `num_layers`).
*   **Functions:**
    *   `hash_bytes(data_bytes: bytes) -> bytes`: Calculates SHA3-256 of bytes.
    *   `hash_hex(hex_string: str) -> bytes`: Calculates SHA3-256 of a hex string's UTF-8 bytes.
    *   `bytes_to_hex(data_bytes: bytes) -> str`: Converts bytes to a hex string.
    *   `hash_pair(left: bytes, right: bytes) -> bytes`: Hashes the concatenation of two byte strings.
    *   `hash_model_state(state_dict: OrderedDict) -> bytes`: Calculates a deterministic SHA3-256 hash of a PyTorch model's `state_dict`. Iterates sorted keys and hashes key names and tensor bytes.
    *   `build_merkle_tree(leaf_hashes: list[bytes]) -> tuple[bytes, list[list[bytes]]]`: Builds a Merkle tree from a list of leaf hashes (bytes). Handles padding for non-power-of-2 leaves by duplicating the last hash. Returns the Merkle root (bytes) and all tree levels.
        *   **Variables:** `num_leaves`, `target_size`, `tree_levels`, `current_level`, `next_level`, `parent_hash`, `merkle_root`.
    *   `get_merkle_proof(leaf_index: int, tree_levels: list[list[bytes]]) -> list[tuple[bytes, bool]]`: Generates a Merkle proof (path) for a specific leaf index given the tree levels.
        *   **Variables:** `proof`, `current_index`, `current_level`, `is_right_node`, `sibling_index`, `sibling_hash`.
    *   `verify_merkle_proof(leaf_hash: bytes, leaf_index: int, proof: list[tuple[bytes, bool]], root_hash: bytes) -> bool`: Verifies a Merkle proof.
        *   **Variables:** `current_hash`, `is_valid`.
    *   `calculate_pre_hash(prev_block_hash: str, reference_model_id: str or None, nonce: int) -> str`: Calculates the Pre-Hash (SHA3-256 hex string) from `prev_block_hash`, `reference_model_id` (or "NO_REFERENCE"), and `nonce`.
    *   `verify_pre_hash_threshold(pre_hash_hex: str, t1_threshold: int) -> bool`: Verifies if `pre_hash_hex` (converted to int) is less than or equal to `t1_threshold`.
    *   `extract_seed_from_hash(pre_hash_hex: str) -> int`: Extracts a 32-bit integer seed from the last 8 hex characters of `pre_hash_hex`.
    *   `_map_hash_segment_to_param(segment_hex: str, param_options: list)`: Helper for HtoA to map a hash segment (hex) to an option in a list by modulo arithmetic.
    *   `hash_to_architecture(pre_hash_hex: str) -> dict`: Deterministically maps a `pre_hash_hex` (SHA3-256) to model architecture parameters and a `seed_for_weights`. It segments the hash and uses `_map_hash_segment_to_param` with `PARAM_SPACE` to select parameters, ensuring constraints (e.g., `embed_dim` divisible by `num_heads`).
        *   **Variables:** `segments`, `arch_params`, `valid_heads`, `seed_for_weights`.
        *   **Returns:** A dictionary `{"architecture": arch_params, "seed_for_weights": seed_for_weights}`.
    *   `calculate_post_hash(final_model_state_hash: str, accuracy: float, steps: int) -> str`: Calculates the Post-Hash (SHA3-256 hex string) from `final_model_state_hash`, `accuracy` (packed as double), and `steps`.
    *   `verify_post_hash_threshold(post_hash_hex: str, t2_threshold: int) -> bool`: Verifies if `post_hash_hex` (converted to int) is less than or equal to `t2_threshold`.
    *   `deterministic_json_dumps(data)`: Serializes data to a JSON string with sorted keys for deterministic output.
*   **Interactions:**
    *   Uses `hashlib` for SHA3-256.
    *   `struct` for packing float `accuracy` deterministically.
    *   `json` for deterministic dumps.
    *   `collections.OrderedDict` (for `hash_model_state`).
    *   `math` (for `bit_length` in Merkle tree padding).
    *   `logging` for messages.

## `dpodl_core/__init__.py`
*   **Description:** This file is currently empty. It marks the `dpodl_core` directory as a Python package.
*   **Functions:** None.
*   **Variables:** None.
*   **Interactions:** None.

## `dpodl_core/models.py`
*   **Description:** This file defines the PyTorch neural network models used in the D-PoDL system, specifically a Transformer-based architecture.
*   **Classes:**
    *   `TransformerBlock(nn.Module)`: A simplified Transformer block consisting of multi-head self-attention followed by a skip connection, and a feed-forward linear layer also followed by a skip connection.
        *   **`__init__(self, embed_dim, num_heads)`**: Initializes `nn.MultiheadAttention` and `nn.Linear`.
        *   **`forward(self, x)`**: Defines the forward pass.
        *   **Variables:** `attn`, `linear_ff`, `attn_out`, `ff_out`.
    *   `DeeperTransformer(nn.Module)`: A deeper Transformer model for classification, composed of an embedding layer, a stack of `TransformerBlock` modules, and a final linear output head.
        *   **`__init__(self, vocab_size=30522, embed_dim=256, seq_len=128, num_heads=8, num_layers=6, num_classes=4)`**: Initializes `nn.Embedding`, a `nn.ModuleList` of `TransformerBlock`s, and an `nn.Linear` output head.
            *   **Instance Variables:** `seq_len`, `embed_dim`, `num_layers`, `embedding`, `blocks`, `output_head`.
        *   **`forward(self, x)`**: Defines the forward pass: embedding -> Transformer blocks -> average pooling -> output head.
            *   **Variables:** `embedded`, `block`, `pooled`, `logits`.
*   **Interactions:**
    *   Uses `torch` and `torch.nn`, `torch.nn.functional`.

## `scripts/test_mtx_processing_e2e.py`
*   **Description:** This script provides an end-to-end test for the Model Transaction (MTX) processing workflow. It simulates an MTX submission by a worker, then runs the main trainer orchestration (which includes MTX selection and processing by the "registry operator"), and finally verifies that the MTX was processed correctly, the global model CIDs in the `ModelRegistry` were updated, and the MTX submitter received a token reward.
*   **Functions:**
    *   `main()`:
        *   **Description:**
            1.  Initializes blockchain connection and IPFS client. Loads configuration.
            2.  Retrieves `TEST_WORKER_PRIVATE_KEY` and `REGISTRY_OPERATOR_PRIVATE_KEY` from environment variables.
            3.  Fetches the initial global reference model state CID from `ModelRegistry`.
            4.  Prepares a dummy D-PoDL checkpoint dictionary (`dpodl_state_for_mtx`) for a simulated MTX, including a `final_model_state_cid` and accuracy.
            5.  Saves this `dpodl_state_for_mtx` to IPFS using `save_checkpoint_data_to_ipfs`, obtaining `dpodl_checkpoint_cid_for_mtx`.
            6.  Submits this MTX to the `MTXMempool` contract using `submit_mtx`, providing the `dpodl_checkpoint_cid_for_mtx`, reported accuracy/steps, the initial reference model state CID, and signed by `worker_private_key`. Stores the returned `submitted_mtx_id_for_check`.
            7.  Calls `dpodl_core.trainer.run_training()` to trigger the main orchestration logic which should pick up and process the submitted MTX.
            8.  **Verification:**
                *   Checks the status of the MTX ID that the trainer logs indicate was selected (hardcoded `selected_mtx_id_by_trainer = 1` and expected CIDs/submitter for this test). Expects "Processed".
                *   Checks the status of the MTX ID actually submitted by this script (`submitted_mtx_id_by_script`) if different.
                *   Verifies that the global model state CID and D-PoDL checkpoint CID in `ModelRegistry` have been updated to the expected CIDs from the processed MTX.
                *   Checks the DPoDL token balance of the `submitter_of_selected_mtx` to verify they received the `INITIAL_MTX_REWARD_AMOUNT`.
        *   **Variables:**
            *   `ipfs_client`, `app_config`.
            *   `worker_private_key`, `registry_operator_private_key`.
            *   `initial_ref_model_state_cid`.
            *   `dummy_model_state_cid_for_mtx`, `dpodl_state_for_mtx`, `dpodl_checkpoint_cid_for_mtx`.
            *   `reported_accuracy_bps`, `reported_steps`.
            *   `submission_result`, `submit_receipt`, `submitted_mtx_id_for_check`.
            *   `selected_mtx_id_by_trainer`, `expected_model_cid_after_update`, `expected_dpodl_cid_after_update`, `submitter_of_selected_mtx` (hardcoded expected values from a specific test run).
            *   `mtx_info_selected`, `mtx_info_script_submitted`.
            *   `final_global_model_cid`, `final_global_dpodl_cid`.
            *   `initial_reward_amount_str`, `expected_reward_wei`.
            *   `token_contract_instance`, `submitter_balance_wei`.
            *   `all_checks_pass` (boolean flag for overall test result).
*   **Interactions:**
    *   `dpodl_core.blockchain_interface` for all smart contract interactions.
    *   `dpodl_core.ipfs_utils` for saving data to IPFS.
    *   `dpodl_core.config_utils.get_config`.
    *   `dpodl_core.trainer.run_training`.
    *   `asyncio` to run async IPFS calls from the sync script.
    *   `eth_account` to derive worker address from private key for balance check.
    *   `logging` for test output.
    *   Reads environment variables for private keys and reward amounts.

## `scripts/create_tiny_dataset.py`
*   **Description:** This script loads the "ag_news" dataset from Hugging Face, shuffles it, and selects a small subset of training and testing samples. It then saves these tiny datasets as CSV files (`train.csv`, `test.csv`) to a local directory (`./data/ag_news_tiny`). This is used to create a small dataset for faster testing and development.
*   **Functions:**
    *   `create_tiny_dataset()`:
        *   **Variables:** `output_base_dir`, `num_train_samples`, `num_test_samples`, `full_dataset`, `shuffled_dataset`, `tiny_train_dataset`, `tiny_test_dataset`, `train_file_path`, `test_file_path`.
*   **Interactions:**
    *   `datasets.load_dataset` (Hugging Face library).
    *   `os.makedirs`, `os.path.join`, `os.path.abspath`.
    *   `logging`.

## `blockchain/hardhat.config.js`
*   **Description:** This is the Hardhat configuration file for the blockchain part of the project. It defines Solidity compiler settings, network configurations (hardhat, localhost, Sepolia testnet), Etherscan API key for contract verification, and named accounts for deployment scripts (e.g., `deployer`, `registryOwner`).
*   **Key Sections & Variables:**
    *   **Solidity Compiler:** Specifies version "0.8.20", enables optimizer (200 runs), and `viaIR`.
    *   **Networks:**
        *   `hardhat`: `chainId: 31337`.
        *   `localhost`: `chainId: 31337`, `url: "http://127.0.0.1:8545/"`.
        *   `sepolia`: Configured with `SEPOLIA_RPC_URL` (from `.env`), `accounts` (derived from `PRIVATE_KEY` in `.env`), `chainId: 11155111`.
    *   **`etherscan`:** API key `ETHERSCAN_API_KEY` (from `.env`).
    *   **`namedAccounts`:** Defines `deployer`, `registryOwner`, `mempoolOwner` which map to account index 0 by default for different networks.
    *   **Environment Variables Used:** `SEPOLIA_RPC_URL`, `PRIVATE_KEY`, `ETHERSCAN_API_KEY`.
*   **Interactions:**
    *   Requires `@nomicfoundation/hardhat-toolbox`, `hardhat-deploy`, `@nomicfoundation/hardhat-verify`, `dotenv`.

## `blockchain/helper-hardhat-config.js`
*   **Description:** This file provides helper configurations for Hardhat deployment scripts, primarily defining initial parameters for smart contract constructors and identifying development chains.
*   **Key Exports & Variables:**
    *   `developmentChains`: Array `["hardhat", "localhost"]`.
    *   Initial parameters for `ModelRegistry`:
        *   `initialT1Threshold`
        *   `initialAccuracyThresholdBPS` (8500)
        *   `initialBlockRewardAmount` (100 DPDL tokens)
        *   `initialMinTrainingSteps`, `initialMaxTrainingSteps`
        *   `initialMinAccuracyImprovementBPS`, `initialMinStepImprovement`
        *   `initialReferenceRewardShareBPS` (2000, i.e., 20%)
        *   `initialGenesisModelStateCID` (placeholder string)
        *   `initialGenesisDpodlCheckpointCID` (placeholder string, can be empty)
        *   `initialMtxRewardAmount` (50 DPDL tokens)
    *   `parseEther`: A helper function to convert Ether string values to Wei using `ethers.parseEther` (v6) or `ethers.utils.parseEther` (v5).
    *   Network-specific overrides (e.g., for `31337` (Hardhat), `1` (Mainnet)) can be defined but are mostly empty, relying on the common defaults.
*   **Interactions:**
    *   Uses `ethers` (from Hardhat).

## `blockchain/contracts/ModelRegistry.sol`
*   **Description:** This is a Solidity smart contract that manages the canonical chain of D-PoDL model blocks. It enforces consensus rules (T1 hash threshold, accuracy threshold), handles D-PoDL parameters, and rewards proposers. It also interacts with `MTXMempool` to process Model Transactions (MTXs) for updating the global reference model.
*   **Structs:**
    *   `ModelBlock`: Stores details for each validated block (height, model state CID, D-PoDL checkpoint CID, accuracy, steps, post-hash, reference D-PoDL CID, proposer, timestamp).
*   **State Variables (Key Ones):**
    *   D-PoDL parameters: `t1Threshold`, `tAccuracyThresholdBPS`, `blockRewardAmount`, `mtxRewardAmount`, `minTrainingSteps`, etc. (public, settable by owner).
    *   `dpdlToken`: `IERC20` address of the DPoDLToken contract.
    *   `mtxMempoolContract`: `IMTXMempool` interface for the MTXMempool contract.
    *   `modelBlocks`: Mapping `blockHeight => ModelBlock`.
    *   `currentBlockHeight`: Height of the latest block.
    *   `dpodlCheckpointCIDToBlockHeight`: Mapping `dpodlCheckpointCID => blockHeight`.
    *   `currentModelStateCID`, `currentDpodlCheckpointCID`: CIDs for the current global reference model.
    *   `lastGlobalModelUpdateTime`, `lastProcessedMtxId`: Tracking MTX processing.
*   **Events (Key Ones):**
    *   `ModelAccepted`: When a new block is added.
    *   `ParameterUpdated`: When a D-PoDL parameter is changed by the owner.
    *   `GlobalReferenceModelUpdated`: When `currentModelStateCID` or `currentDpodlCheckpointCID` is updated by a new block or an MTX.
    *   `RewardDistributedForMtx`: When an MTX submitter is rewarded.
*   **Constructor:**
    *   Initializes all D-PoDL parameters, token address, initial owner, genesis model CIDs, and MTX reward amount. Sets `currentModelStateCID` and `currentDpodlCheckpointCID` from constructor arguments.
*   **Functions (Key Ones):**
    *   `verifyModelImprovement(...) returns (bool)` (public view): Checks if a submitted model shows sufficient accuracy and step improvement over a reference D-PoDL checkpoint.
    *   `submitBlock(...)` (public):
        *   Allows proposers to submit new model blocks.
        *   **Validations:**
            *   Checks if based on the correct `currentDpodlCheckpointCID`.
            *   Verifies accuracy (`_accuracyBPS`) against `tAccuracyThresholdBPS`.
            *   Verifies `_postHash` against `t1Threshold`.
            *   Checks training `_steps` are within `minTrainingSteps`/`maxTrainingSteps`.
            *   Calls `verifyModelImprovement`.
        *   **State Updates:** Increments `currentBlockHeight`, stores the new `ModelBlock`, updates `dpodlCheckpointCIDToBlockHeight`, and sets `currentModelStateCID` and `currentDpodlCheckpointCID` to the new block's CIDs.
        *   **Rewards:** Mints `blockRewardAmount` to the proposer (msg.sender) and potentially a share (`referenceRewardShareBPS`) to the proposer of the reference block, using `DPoDLToken(address(dpdlToken)).mint()`.
    *   `updateReferenceModelFromMtx(string memory _newModelStateCID, string memory _newDpodlCheckpointCID, uint256 _mtxId)` (external `onlyOwner`):
        *   Updates `currentModelStateCID` and `currentDpodlCheckpointCID` using details from a selected MTX.
        *   Requires the MTX to be in `SelectedForProcessing` status in `mtxMempoolContract`.
        *   Mints `mtxRewardAmount` to the MTX submitter.
        *   Calls `mtxMempoolContract.updateMtxStatus(_mtxId, MTXMempool.Status.Processed)`.
    *   `getCurrentReferenceModelStateCID()`, `getCurrentReferenceDpodlCheckpointCID()` (public view): Getters for the global reference CIDs.
    *   `getBlockDetails(uint256 _blockHeight)`, `getBlockHeightForCID(string memory _dpodlCheckpointCID)` (public view): Getters for block information.
    *   Setter functions for all D-PoDL parameters (e.g., `setT1Threshold`, `setBlockRewardAmount`, `setMtxRewardAmount`), `setDpdlToken`, `setMtxMempoolContract` (all `onlyOwner`).
*   **Interactions:**
    *   `@openzeppelin/contracts/access/Ownable.sol`.
    *   `@openzeppelin/contracts/token/ERC20/IERC20.sol`.
    *   `./DPoDLToken.sol` (casts token address to `DPoDLToken` for minting).
    *   `./MTXMempool.sol` (via `IMTXMempool` interface for getting MTX details and updating status).

## `blockchain/contracts/MTXMempool.sol`
*   **Description:** This Solidity smart contract manages a mempool for Model Transactions (MTXs). MTXs are proposed models that might not meet the full criteria for a new block in `ModelRegistry` but can serve as reference points.
*   **Enums:**
    *   `Status`: Defines MTX lifecycle states (`Pending`, `SelectedForProcessing`, `Processed`, `Rejected`).
*   **Structs:**
    *   `ModelTransaction`: Stores details for each MTX (ID, DPoDL checkpoint IPFS CID, accuracy, steps, reference model CID, submitter, timestamp, status, isValid flag).
*   **State Variables:**
    *   `mtxPool`: Mapping `mtxId => ModelTransaction`.
    *   `nextMtxId`: Counter for unique MTX IDs (starts at 1).
    *   `modelRegistryContract`: Address of the `ModelRegistry` contract (set by owner).
*   **Events:**
    *   `MtxSubmitted`: When a new MTX is added.
    *   `MtxStatusUpdated`: When an MTX's status changes.
*   **Modifiers:**
    *   `onlyModelRegistryOrOwner()`: Restricts access to the `ModelRegistry` contract or the owner.
*   **Constructor:**
    *   Initializes `nextMtxId` to 1 and sets the contract owner.
*   **Functions:**
    *   `setModelRegistryContract(address _registryAddress)` (public `onlyOwner`): Sets the address of the `ModelRegistry`.
    *   `submitMtx(string memory _ipfsCID, uint256 _accuracyBPS, uint256 _steps, string memory _referenceModelCID)` (public):
        *   Allows anyone to submit an MTX.
        *   Creates a new `ModelTransaction` with `Status.Pending` and stores it in `mtxPool`. Increments `nextMtxId`.
    *   `updateMtxStatus(uint256 _mtxId, Status _newStatus)` (public `onlyModelRegistryOrOwner`): Updates the status of an existing MTX. Typically called by `ModelRegistry` or an off-chain operator.
    *   `getMtxDetails(uint256 _mtxId) public view returns (ModelTransaction memory)`: Returns details of a specific MTX.
    *   `getMtxCount() public view returns (uint256)`: Returns the total number of MTXs submitted (`nextMtxId - 1`).
*   **Interactions:**
    *   `@openzeppelin/contracts/access/Ownable.sol`.
    *   Implicitly designed to be called by worker nodes (for `submitMtx`) and the `ModelRegistry` contract (for `updateMtxStatus`).

## `blockchain/contracts/TaskRegistry.sol` (Less central to D-PoDL core logic, brief overview)
*   **Description:** This Solidity contract (seemingly less used by the core D-PoDL files provided) manages the lifecycle of AI training "tasks." Publishers can submit tasks with dataset identifiers, evaluation criteria, target accuracy, reward pools, and duration. The owner can then manage the status of these tasks (Pending, Active, Completed, Cancelled).
*   **Enums:** `TaskStatus`.
*   **Structs:** `Task` (details of a task).
*   **State Variables:** `_taskIds` counter, `tasks` mapping, `tasksByPublisher` mapping.
*   **Functions:** `submitTask`, `startTask` (owner), `completeTask` (owner/publisher), `cancelTask` (owner/publisher), `associateModelToTask` (owner), `getTaskDetails`, `getPublisherTasks`, `getTaskCount`.
*   **Interactions:** `@openzeppelin/contracts/access/Ownable.sol`.

## `blockchain/contracts/DPoDLToken.sol`
*   **Description:** This is a standard ERC20 token contract for the D-PoDL network, named "DPoDL Token" (symbol "DPDL"). It uses OpenZeppelin's `AccessControl` to manage a `MINTER_ROLE`. Only accounts with this role can mint new tokens. The contract deployer receives the admin role and minter role, and the initial supply is minted to the deployer.
*   **State Variables:**
    *   `MINTER_ROLE`: `bytes32` constant for the minter role.
*   **Constructor:**
    *   `constructor(uint256 initialSupply)`: Initializes the token name, symbol. Grants `DEFAULT_ADMIN_ROLE` and `MINTER_ROLE` to `msg.sender`. Mints `initialSupply` (adjusted for decimals) to `msg.sender`.
*   **Functions:**
    *   `mint(address account, uint256 amount)` (public `onlyRole(MINTER_ROLE)`): Mints `amount` new tokens to `account`. This is used by `ModelRegistry` to reward block/MTX proposers.
*   **Interactions:**
    *   `@openzeppelin/contracts/token/ERC20/ERC20.sol`.
    *   `@openzeppelin/contracts/access/AccessControl.sol`.

## Execution Modes

Based on the project structure and scripts, there are two primary ways to run and interact with this D-PoDL system:

### 1. End-to-End MTX Processing Test

*   **Entry Point:** `python scripts/test_mtx_processing_e2e.py`
*   **Purpose:** This script provides a comprehensive end-to-end test for the Model Transaction (MTX) processing workflow. It's designed to validate the entire lifecycle of an MTX, from submission to its effect on the global model registry and reward distribution.
*   **Process:**
    1.  **Initialization:** Connects to the blockchain and IPFS, loads configurations.
    2.  **Simulated MTX Submission:**
        *   A dummy D-PoDL checkpoint (representing a worker's output) is created and saved to IPFS.
        *   This checkpoint CID is then used to submit an MTX to the `MTXMempool` smart contract, simulating a worker's contribution. This is done using a designated "test worker" private key.
    3.  **Trainer Orchestration:** The script then calls `dpodl_core.trainer.run_training()`. In a test context with pre-submitted MTXs, this function will:
        *   Fetch pending MTXs from the `MTXMempool`.
        *   Evaluate them (load their D-PoDL state from IPFS).
        *   Select the "best" MTX based on defined criteria.
        *   Update the status of the selected MTX to `SelectedForProcessing` in the `MTXMempool`.
        *   Call the `ModelRegistry` contract to update the global reference model using the details from the selected MTX. This step also triggers rewarding the MTX submitter and marking the MTX as `Processed`.
    4.  **Verification:** After `run_training()` completes, the script performs several checks:
        *   Verifies that the status of the submitted MTX is now "Processed" in the `MTXMempool`.
        *   Confirms that the global model state CID and D-PoDL checkpoint CID in the `ModelRegistry` have been updated to reflect the CIDs from the processed MTX.
        *   Checks the DPoDL token balance of the MTX submitter to ensure they received the expected reward.
*   **Key Components Used:**
    *   `scripts/test_mtx_processing_e2e.py`
    *   `dpodl_core/trainer.py` (specifically `run_training()`)
    *   `dpodl_core/blockchain_interface.py` (for all smart contract interactions and fetching private keys)
    *   `dpodl_core/ipfs_utils.py` (for saving the dummy MTX checkpoint to IPFS and loading D-PoDL states during trainer evaluation)
    *   `ModelRegistry.sol`, `MTXMempool.sol`, `DPoDLToken.sol` smart contracts.
    *   Environment variables for private keys (`TEST_WORKER_PRIVATE_KEY`, `REGISTRY_OPERATOR_PRIVATE_KEY`) and configuration.

### 2. Distributed D-PoDL Training via Ray

*   **Entry Point:** Primarily through `dpodl_core/trainer.py` (e.g., by running it as a script or calling its `run_training()` function).
*   **Purpose:** To perform the actual distributed training of machine learning models according to the D-PoDL protocol. This mode leverages multiple workers to collaboratively train a model, with blockchain and IPFS used for coordination, verification, and persistence.
*   **Process:**
    1.  **Trainer Initialization (`trainer.py`):**
        *   Loads application configuration (`config_utils.get_config()`).
        *   Initializes a Ray cluster (if not already running).
        *   Loads and partitions the dataset using `data_loader.load_dataset_and_partition()`.
        *   Determines the current global reference model CIDs by querying the `ModelRegistry` contract (via `blockchain_interface.py`).
        *   Constructs a `train_loop_config` dictionary containing all necessary parameters for the workers (dataset partitions, model params, D-PoDL thresholds, IPFS settings, reference CIDs, etc.).
        *   Initializes a Ray `TorchTrainer` with the `worker.worker_train_loop` as the function to execute on each worker and the prepared `train_loop_config`.
        *   Starts the distributed training by calling `trainer.fit()`.
    2.  **Worker Execution (`worker.py` running on Ray workers):**
        *   Each worker receives its rank, world size, and the `train_loop_config`.
        *   **Pre-Hash:** Mines for a valid `nonce` to satisfy the T1 threshold, generating a `pre_hash_value` and a `random_seed`.
        *   **Model Initialization:**
            *   Uses Hash-to-Architecture (HtoA) derived from `pre_hash_value` (via `crypto.hash_to_architecture()`) or uses override parameters from the config to define the model architecture (`models.DeeperTransformer`).
            *   Initializes model weights deterministically using a `seed_for_weights` (also from HtoA) or by transferring weights from a reference model (loaded from IPFS via `ipfs_utils.load_model_state_from_ipfs()` if `reference_model_state_cid` is provided and `transfer_reference_weights` is enabled).
        *   **Training Loop:** Iterates through epochs and batches, performing standard training steps (forward/backward pass, optimizer step).
            *   Records a `training_trace` and periodically hashes the model state for Merkle tree construction.
        *   **Post-Epoch Operations:**
            *   Evaluates model accuracy.
            *   Calculates the `final_model_state_hash` and `post_hash_value` (using `crypto.calculate_post_hash()`).
            *   Verifies the `post_hash_value` against the T2 threshold.
            *   Builds a Merkle tree from `checkpoint_hashes` (`crypto.build_merkle_tree()`).
            *   Performs D-PoDL state consistency verification using `verification.verify_proof_of_training_consistency()`.
            *   Decides an `action` ("SAVE_BLOCK_CHECKPOINT", "SAVE_MTX_CHECKPOINT", or "DISCARD") based on Post-Hash validity, accuracy thresholds, and state consistency.
        *   **Checkpointing & Submission (if not DISCARD):**
            *   Saves the `current_dpodl_state` (containing all relevant D-PoDL parameters, hashes, CIDs, Merkle root, trace hash, etc.) and the model to a local checkpoint (`utils.save_checkpoint()`).
            *   If IPFS is enabled:
                *   Saves the final model state to IPFS (`ipfs_utils.save_model_state_to_ipfs()`), getting `final_model_cid_for_tx`.
                *   Saves the `current_dpodl_state` to IPFS (`ipfs_utils.save_checkpoint_data_to_ipfs()`), getting `checkpoint_data_cid_for_tx`.
            *   Submits the result to the blockchain:
                *   `submit_block()` to `ModelRegistry` if a block candidate.
                *   `submit_mtx()` to `MTXMempool` if an MTX candidate.
                (Both via `blockchain_interface.py`, signed with the worker's private key).
            *   Reports submission details (action, CIDs, tx_hash, accuracy, etc.) to Ray Train using `ray.train.report()`.
        *   Reports epoch metrics (loss, accuracy, action) to Ray Train.
    3.  **Trainer Post-Processing (`trainer.py` after `trainer.fit()`):**
        *   Retrieves results from all workers (e.g., from `result.metrics_dataframe`).
        *   Identifies any block candidates or new MTX candidates reported by workers.
        *   Fetches all currently pending MTXs from the `MTXMempool` contract.
        *   Evaluates these MTXs (loads their D-PoDL state from IPFS to get true model CIDs and accuracy).
        *   Selects the "best" MTX from the evaluated set.
        *   Updates the status of the selected MTX to `SelectedForProcessing` in the `MTXMempool`.
        *   Calls `ModelRegistry.updateReferenceModelFromMtx()` to set the new global reference model based on the selected MTX. This also rewards the submitter and marks the MTX as `Processed`.
*   **Key Components Used:**
    *   `dpodl_core/trainer.py` (main orchestrator)
    *   `dpodl_core/worker.py` (executed by Ray workers)
    *   `dpodl_core/crypto.py` (for all cryptographic operations)
    *   `dpodl_core/verification.py` (for D-PoDL state consistency)
    *   `dpodl_core/models.py` (defines the neural network architecture)
    *   `dpodl_core/ipfs_utils.py` (for all IPFS interactions)
    *   `dpodl_core/blockchain_interface.py` (for all smart contract interactions)
    *   `dpodl_core/data_loader.py` (for dataset loading and partitioning)
    *   `dpodl_core/config_utils.py` and `blockchain_config.py` (for configurations)
    *   `ray` (Tune, Train, AIR) for distributed execution.
    *   Smart contracts: `ModelRegistry.sol`, `MTXMempool.sol`, `DPoDLToken.sol`.

## Flow Summary (Simplified D-PoDL Cycle):

1.  **Trainer (`trainer.py`) starts:**
    *   Gets current global reference CIDs from `ModelRegistry` (via `blockchain_interface`).
    *   Launches Ray workers (`worker.py`) with config including these reference CIDs.
2.  **Worker (`worker.py`) executes:**
    *   Performs Pre-Hash using reference CIDs.
    *   Initializes model (HtoA or from reference loaded from IPFS via `ipfs_utils`).
    *   Trains the model.
    *   Performs Post-Hash and self-verification (`verification.py`).
    *   If criteria met for block: Submits to `ModelRegistry` (via `blockchain_interface`).
    *   If criteria met for MTX: Submits to `MTXMempool` (via `blockchain_interface`).
    *   All submissions involve saving model/D-PoDL state to IPFS (via `ipfs_utils`).
3.  **Trainer (`trainer.py`) post-worker completion:**
    *   Processes worker results.
    *   Fetches pending MTXs from the `MTXMempool` contract.
    *   Evaluates MTXs (loads their D-PoDL state from IPFS to get true model CIDs and accuracy).
    *   Selects the "best" MTX from the evaluated set.
    *   Updates the status of the selected MTX to `SelectedForProcessing` in the `MTXMempool`.
    *   Calls `ModelRegistry.updateReferenceModelFromMtx()` to set the new global reference model based on the selected MTX. This also rewards the submitter and marks the MTX as `Processed`.
4.  Cycle potentially repeats with new global reference CIDs. 