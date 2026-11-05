# AIBC / D-PoDL codebase review (repository state at last commit fad72ed, 2025-09-28)

Scope: code review of /home/user/AIBC. Sources are repository files, cited as `path:line`. Paper citations: **D-PoDL paper = `Research_papers/579857605/579857605.md`** (Su, Larangeira, Tanaka, "Provably Secure Blockchain Protocols from Distributed Proof-of-Deep-Learning"). **zkDL = `Research_papers/2023-1174/2023-1174.md`** (Sun et al., IACR ePrint 2023/1174). The folder names are correct. The original brief got the ePrint number wrong: it called the D-PoDL paper "2023/1174", which is actually zkDL (`Research_papers/2023-1174/2023-1174.md:1`; `Research_papers/579857605/579857605.md:1`).

What I ran (all in a scratchpad copy, repo unchanged; `git status` shows only `research_notes/` untracked):
- `npm ci` in a copy of `blockchain/` **fails**: "lock file's @openzeppelin/contracts@5.0.2 does not satisfy @openzeppelin/contracts@5.6.1" (package.json asks `^5.3.0`, `blockchain/package.json:21`; lock pins 5.0.2). Running `npm install` instead works (Hardhat 2.24.0, ethers 6.14.0, hardhat-deploy 1.0.2, OZ resolved to 5.6.1), and `npx hardhat test` gives **71 passing**.
- I wrote 5 scratch Hardhat proof-of-concept tests (not in the repo). **All 5 passed**, confirming exploitable contract behaviour (details below).
- Python: CPU venv on Python 3.13 with torch 2.5.1+cpu, pytest 8.3.4, web3 8.0.0, eth-account 0.14.0. Bare `pytest -q` (what Makefile and CI run) **fails at collection** on `scripts/test_mtx_processing_e2e.py` (ImportError without web3; that module also exits or connects to services at import time). `pytest tests old_tests` gives **7 passed**: 6 in `tests/test_utils.py` plus 1 trivial `assert 1+1==2`.
- I wrote a scratch Python PoC against `dpodl_core.crypto` / `dpodl_core.verification`. It confirmed that fabricated proofs pass verification, that post-hash grinding works, and that the manifest signature is not bound to the files it describes (details below).
- I did not install the full `requirements.txt` (tensorflow + deepspeed + ray) and did not run Ray training or IPFS. Statements about runtime Ray behaviour come from reading the code.

---

## Q1. What does each module/contract actually do in practice?

### Takeaway
This is a single-machine Ray + Hardhat + local IPFS prototype. Ray launches N copies of a training loop. Each copy does a trivial nonce search, trains a small text classifier (about 2–30M parameters) on AG News, scores itself, uploads safetensors plus a signed JSON manifest to IPFS, and submits an MTX to a permissionless on-chain list. After training, one privileged operator key reads the self-reported accuracies, picks the highest, and makes it the "reference model" on chain. The block path is effectively dead code. TaskRegistry is not connected to anything.

### Cited Findings
**Orchestration — `dpodl_core/trainer.py`**
- Initializes Ray locally (or `RAY_ADDRESS`), loads and partitions data, builds `train_loop_config`, runs `TorchTrainer(worker_train_loop)` — `dpodl_core/trainer.py:84-92, 99-106, 153-179, 198-208`.
- ScalingConfig requests `resources_per_worker={"CPU": 0.25, "GPU": 0.25}` and sets `use_gpu=torch.cuda.is_available()` — `dpodl_core/trainer.py:183-188`.
- Block candidates reported by workers are only logged. The code still says "TODO: Add logic to select best block candidate and submit to blockchain" — `dpodl_core/trainer.py:256-262`.
- After `fit()`, it fetches all Pending MTXs, loads each manifest from IPFS, and **takes `accuracy_bps` from the submitter's own checkpoint metadata** — `dpodl_core/trainer.py:278-303`. It sorts by that accuracy (`:327`), logs it as "True Accuracy" (`:329`), then uses `REGISTRY_OPERATOR_PRIVATE_KEY` to call `updateMtxStatus(...,1)` and `updateReferenceModelFromMtx` — `dpodl_core/trainer.py:388-411`.
- The second manifest load, the one whose model CID gets submitted, does not pass `expected_submitter`, so the signature is not checked on that load — `dpodl_core/trainer.py:336-339`.

**Worker loop — `dpodl_core/worker.py`**
- Pre-hash: deterministic nonce search starting from 0 — `dpodl_core/worker.py:277-285`. Seed extraction: `:300`. HtoA: `:305-319`. Model build: `:324-331`.
- Per-rank private key from `WORKER_PRIVATE_KEY_{rank}` — `dpodl_core/worker.py:338-353`.
- Each step logs a trace record (loss, timestamps) — `dpodl_core/worker.py:505-515`. Every 100 steps it hashes the model state into `checkpoint_hashes` — `:521-525` (interval `CHECKPOINT_INTERVAL_STEPS = 100`, `:62`).
- End of epoch: evaluate accuracy (`:545`), compute model hash and post-hash (`:549-555`), check T2 (`:558`), build Merkle root (`:561-563`), run a self-consistency check (`:586`). Decision: block if `accuracy >= t_acc`, otherwise MTX (`:592-601`).
- Saves a local torch checkpoint plus legacy IPFS add (`:662-667`). Secure save: safetensors + EIP-712 manifest (`:701-708`, `:778-785`). Then `submit_block(...)` (`:732-740`) or `submit_mtx(...)` (`:847-853`).

**Crypto — `dpodl_core/crypto.py`**
- SHA3-256 helpers — `:20-34`. Model-state hash = SHA3 over sorted keys and raw tensor bytes — `:36-46`.
- Merkle tree with duplicate-last padding — `:50-89`. Proof generation and verification — `:91-156`.
- Pre-hash `SHA3(prevBK ‖ refM or "NO_REFERENCE" ‖ str(nonce))` — `:161-185`.
- HtoA maps hash segments onto a small grid (embed_dim ∈ {128, 256, 384, 512}, heads ∈ {4, 8, 12, 16}, layers 4–12, activation, dropout) — `:225-288`.
- Post-hash `SHA3(model_hash_hex ‖ pack(">d", acc) ‖ str(steps))` — `:292-312`.
- EIP-712 manifest types, signing, and verification — `:345-520`.

**Verification — `dpodl_core/verification.py`**
- `verify_proof_of_training_consistency` recomputes pre-hash, seed, post-hash, and the Merkle root **from values inside the same dict**. It does not check them against a model, data, or the chain — `dpodl_core/verification.py:131-323`.
- The trace-hash check is commented out — `:307-318`.
- `generate_merkle_proof_for_step` / `verify_checkpoint_merkle_proof` (`:26-127`) are **never called** anywhere in the codebase. The only call to the consistency check is the worker checking itself (`dpodl_core/worker.py:586`).
- `load_and_verify_checkpoint_state` passes `model=None` into `load_checkpoint` (`verification.py:344`). That function calls `model.load_state_dict` (`dpodl_core/utils.py:278`), so the helper would always fail and return an empty state. It is also never called.

**Storage — `dpodl_core/ipfs_utils.py`**
- `ipfshttpclient` against local daemon `IPFS_HOST` — `:54-96`; `dpodl_core/blockchain_config.py:67`. Optional Pinata pinning — `ipfs_utils.py:99`.
- Secure save uploads three objects: model.safetensors, checkpoint.json, and a manifest with an EIP-712 signature — `ipfs_utils.py:347-490`.
- Secure load: structure check, optional signature check, SHA-256 checks against hashes **listed in the manifest's own `files` section**, size limits, dtype allow-list — `:498-647`, `:323-343`.
- Legacy `save_checkpoint_data_to_ipfs` writes a torch pickle (`:233`), but `load_checkpoint_data_from_ipfs` reads JSON (`:249-256`). The formats don't match.
- `merge_model_states` (parameter averaging, `:293-319`) is unused.

**Chain I/O — `dpodl_core/blockchain_interface.py`**
- Connects once at import time (`:35-88`) using `ExtraDataToPOAMiddleware` (`:8`), which only exists in web3.py v7+.
- Reads registry CIDs (`:119-145`). Enumerates the mempool one RPC per ID, 1..N (`:214-238`).
- `_send_signed_transaction` handles EIP-1559 fees, does a pre-flight `eth_call`, and waits for the receipt (`:260-429`).
- `submit_block(new_model_state_cid, new_dpodl_checkpoint_cid, accuracy_bps, steps, post_hash, reference_dpodl_checkpoint_cid, signer_private_key)` — `:432-470`. `submit_mtx` — `:472-531`. `update_reference_model_from_mtx` — `:533-588`. `update_mtx_status` — `:590-649`.

**Config — `dpodl_core/config_utils.py`, `dpodl_core/blockchain_config.py`**
- Hard-coded defaults: `t1_threshold = 2^250`, `t2_threshold = 2^256`, `t_acc_threshold = 0.97`, `prev_block_hash = "0x1111"`, `epochs = 5`, `batch_size = 128`, `lr = 1e-3` — `config_utils.py:12-32`. I verified 2^250 and 2^256 numerically.
- The test profile uses a 200/50-sample tiny dataset and a 64-dim, 1-layer, 2-head model override — `config_utils.py:35-52`.
- Contract addresses and ABIs are read from the committed `blockchain/deployments/localhost/*.json` — `blockchain_config.py:18-49`.

**Data — `dpodl_core/data_loader.py`**
- AG News official train (120k) and test (7.6k) splits — `:92-95`. BERT tokenizer, `max_length=128` — `:113-116`.
- Contiguous index sharding per worker — `:126-141`. The test split is returned as `val_dataset` and handed to every worker — `:166-171`; `trainer.py:108, 156`.

**Model — `dpodl_core/models.py`**
- `DeeperTransformer`: token embedding (vocab 30522) → N pre-LN blocks (MultiheadAttention + one `Linear(d, d)` + ReLU) → mean-pool → 4-class head — `:5-72`.
- No positional encoding. The mean-pool includes padding tokens (`:69`).

**Contracts**
- `DPoDLToken.sol`: OZ ERC20 + AccessControl. The deployer gets DEFAULT_ADMIN and MINTER roles and 1M tokens — `blockchain/contracts/DPoDLToken.sol:24-31`. `mint` is gated by MINTER_ROLE — `:41-43`.
- `MTXMempool.sol`: permissionless `submitMtx` stores self-reported `(ipfsCID, accuracyBPS, steps, referenceModelCID)` — `MTXMempool.sol:111-148`. `updateMtxStatus` is callable by owner or registry with no transition rules — `:156-171`.
- `ModelRegistry.sol`: `submitBlock` checks four things — reference == current head, `accuracy >= tAcc`, `postHash < t1Threshold`, steps within [min, max] — plus improvement over the referenced block, then mints the reward — `ModelRegistry.sol:295-443`. `updateReferenceModelFromMtx` is **onlyOwner** and mints `mtxRewardAmount` to the MTX submitter — `:455-500`. Owner setters exist for every parameter and for the token address — `:552-654`.
- `TaskRegistry.sol`: stores task metadata. `rewardPool` is just a number with no escrow — `TaskRegistry.sol:31, 87-125`. `associateModelToTask` has no access control and a `// TODO: Add access control` comment — `:193-201`. No Python module or other contract references TaskRegistry (grep over `dpodl_core/` and `scripts/` finds nothing).

**Deploy — `blockchain/deploy/`**
- 001: token. 002: registry, plus a MINTER grant to the registry. 003: mempool. 004_configure_roles: MINTER grant again. 004_link_contracts: links mempool and registry, plus a third MINTER grant. 005: TaskRegistry — `blockchain/deploy/*.js`.
- Two scripts share the `004_` prefix.
- On-chain parameters: `t1Threshold = 0xFFFF…FF000000` (≈2^256 − 2^24), `tAcc = 8500` bps, block reward 100 DPDL, MTX reward 50 DPDL, steps in [100, 10000], minimum improvement +100 bps and +50 steps, reference share 20%, placeholder genesis CIDs `"Qm__GENESIS_…"` — `blockchain/helper-hardhat-config.js:8-34`.
- `blockchain/scripts/deploy.js` and `interact.js` are 0 bytes.

### Inferences
- In practice the system is "N self-scoring trainers + an off-chain operator that promotes the self-reported best MTX". It is a centralized pipeline with on-chain bookkeeping, not a consensus protocol.
- The useful, reusable parts are the plumbing: the safetensors + content-addressed manifest pattern, the web3 tx helper, the Hardhat project layout, and the role-based mint.

### Gaps
- I did not run `make dev-up` / `make trainer` (needs an IPFS daemon, a Hardhat node, and Ray with the full dependency tree). So I can't confirm the whole loop works today. In particular I did not test whether `resources_per_worker` with `"GPU": 0.25` schedules on a CPU-only host.

---

## Q2. Verification reality: what is verified on-chain vs. trusted from the worker?

### Takeaway
Nothing about training is verified by anyone other than the worker itself. Every value the contracts check (accuracy, steps, post-hash, reference) is a self-reported integer or string. The Merkle root and trace are never sent on-chain, never opened, and never checked by a second party. There is no validator or re-execution path. Miners score themselves on the public AG News test split. That is the opposite of the paper's design, where task publishers hold the test set.

### Cited Findings
- `submitBlock` takes `_postHash` as a caller-supplied `uint256` and only checks `_postHash >= t1Threshold` — `blockchain/contracts/ModelRegistry.sol:300, 327-329`. The contract never computes a hash, never sees a nonce, prevBK, or model hash, and never checks the T1 pre-hash.
- `_accuracyBPS` has a lower bound (`:322-324`) but **no upper bound** (no `<= 10000` check in `submitBlock`; the cap exists only for the threshold setter, `:562`).
- Steps are checked only against [min, max] and a "+minStepImprovement over the reference block" rule — `:332-334, 277-279`.
- **Scratch PoC 1 (Hardhat, passed):** a fresh account called `submitBlock("fake","fakeD",10000,150,0,"QmGD")` and received the 100 DPDL block reward with no training and no IPFS content. The same parameters are in `helper-hardhat-config.js:8-34`.
- **Scratch PoC 2 (passed):** `submitBlock` with `accuracyBPS = 2^256−1` is accepted. The next honest `submitBlock` then reverts, because `referenceBlock.accuracyBPS + minAccuracyImprovementBPS` overflows (`ModelRegistry.sol:272`). One transaction halts the block chain permanently.
- **Scratch PoC 5 (passed):** `MTXMempool.submitMtx("", 999999, 0, "")` from any address is stored as-is (`MTXMempool.sol:111-148`, empty-CID check commented out at `:117`).
- The Merkle root is **never put on-chain**:
  - `submitBlock` has no Merkle parameter (`ModelRegistry.sol:295-302`).
  - `submit_mtx` has no Merkle parameter (`blockchain_interface.py:472-500`).
  - The root lives only inside the worker-written checkpoint JSON (`worker.py:138`, `:649`).
- The worker's `submit_block(...)` call uses keyword names `cid=`, `accuracyBPS=`, `t1_hash=`, `reference_cid=`, `merkle_root=`, `checkpoint_data_cid=` (`worker.py:732-740`). None of these exist in the function signature, and no signer key is passed (`blockchain_interface.py:432-440`). The call therefore raises `TypeError`, which is swallowed by `except Exception` (`worker.py:748-749`). **The worker's block-submission path cannot succeed as written.**
- Self-check only: `verify_proof_of_training_consistency` is called solely by the worker on its own freshly built dict (`worker.py:567-586`). It recomputes hashes from fields in that dict (`verification.py:176-305`). Merkle proof functions are never called (grep: only definitions plus one internal call at `verification.py:73`).
- **Scratch PoC 3 (Python, passed):** I built a dict with no training and random Merkle leaves, used the real nonce search for T1 = 2^250 (found at nonce 140), set `accuracy = 0.99` and `steps = 999999`, and computed post-hash over `"00"*32`. `verify_proof_of_training_consistency(state)` returned **True**.
- Post-hash grinding:
  - The post-hash covers model-hash ‖ accuracy ‖ steps (`crypto.py:292-312`), so any change to a single weight re-randomizes it.
  - **Scratch PoC 4 (passed):** nudging one weight by 1e-7 per attempt satisfied T2 = 2^252 without any training. Expected about 16 attempts; it hit on the first.
  - With the shipped `T2 = 2^256` (`config_utils.py:25`), every model passes anyway. Any 256-bit hash is below 2^256.
- Evaluation set:
  - `val_dataset` is the AG News **test** split (`data_loader.py:94-95`), passed to every worker (`trainer.py:108, 156`; `worker.py:248, 545`).
  - The latest commit message says it is meant to "prevent data leakage" (`git log` fad72ed). That is true only in the train/test sense. Miners still see and self-evaluate on the test data.
  - D-PoDL instead has task publishers split data, publish only training data, and evaluate test accuracy across multiple time slots — `Research_papers/579857605/579857605.md:142, 162`. "miners are given only training datasets" — `:162`.
- MTX "evaluation" by the operator just reads `checkpoint_metadata["accuracy_bps"]`, which the submitter wrote and signed (`trainer.py:296-303`). Nothing re-evaluates the model. The signature proves authorship, not correctness.
- EIP-712 manifest binding gap:
  - `load_secure_model_artifacts` verifies the signature over `manifest['structured_data']` (`ipfs_utils.py:559-571`), then downloads from and hash-checks against `manifest['files'][...]['cid'/'sha256']` (`:574-622`).
  - Nothing checks that `structured_data.message.modelCid/modelSha256` equal `files[...]`.
  - **Scratch PoC 6 (passed):** after swapping `files.model.safetensors.cid` to an attacker CID, `verify_manifest_signature` still returned True.
  - The signed `manifestCid` is the CID of a *temporary* unsigned manifest (`ipfs_utils.py:448-452`), not the final one, so it can't be used for self-binding either.
- When `expected_submitter` is None, signature checking is skipped entirely: `ipfs_utils.py:559`, used at `trainer.py:336-339` and `worker.py:173-189, 366`.
- The validator role doesn't exist anywhere. MTX selection is `onlyOwner` (`ModelRegistry.sol:455-459`), driven by a single env key `REGISTRY_OPERATOR_PRIVATE_KEY` (`trainer.py:388`). In `env.example:19-22` that key is Hardhat account #0, which is also the deployer, token admin, and minter.

### Inferences
- A worker can lie about accuracy, steps, post-hash, and Merkle root with no consequence. On-chain rewards can be minted with zero work (PoC 1). The only friction is the operator's judgment for MTXs, and the operator also relies on self-reports.
- The Merkle "proof of training" is decorative. Even with spot-checks added, the checkpoints are hashes of states that are never published (only the final model is uploaded). A verifier couldn't open a leaf without the intermediate weights, data order, and optimizer state, and bit-exact re-execution on GPU isn't assured (`worker.py:440-442`: deterministic algorithms are commented out).

### Gaps
- No code or docs define a dispute or slashing design. I can't say what the authors intended for a verifier.

---

## Q3. Fidelity to the D-PoDL paper (`Research_papers/579857605/579857605.md`)

### Takeaway
The names map onto the paper (pre-hash/T1, HtoA, post-hash/T2, Tacc, MTX, reference reward, Merkle checkpoints), but the security-relevant semantics are missing or inverted:
- The pre-hash isn't bound to chain state or miner identity.
- HtoA only picks among fixed-depth/width options of one model family, and two of its parameters are ignored.
- The post-hash check is disabled by its threshold and on-chain is just a number the caller supplies.
- Model-referencing isn't wired into the worker.
- The reward split is a fixed one-level 20% rather than step-proportional.
- There is no Verify algorithm, no publisher-held test set, no time slots, and no chain selection rule (Ethereum's own consensus is used and ModelRegistry is a single linear list).

### Cited Findings
| Paper element (579857605.md) | Implementation | Status |
|---|---|---|
| PreHash: `Hash(prevBK, refM, nonce) ≤ T1`, with prevBK the previous block (`:96`) | `calculate_pre_hash(prev_block_hash, reference_model_id, nonce)` (`crypto.py:161-185`). `prev_block_hash` is the static config string `"0x1111"` (`config_utils.py:27`), never read from chain (grep: no chain read in `blockchain_interface.py`/`trainer.py`). The nonce search starts at 0 for everyone (`worker.py:277-279`). | **Deviates.** Not bound to the chain head. Every worker and every run finds the same nonce (PoC: nonce 140), so it provides no pre-computation resilience. On-chain T1 is never checked against a pre-hash at all. |
| HtoA(h1) → (architecture, hyper-params, learnable params lp, seed r) (`:96`) | `hash_to_architecture` picks num_layers / embed_dim / heads / activation / dropout (`crypto.py:225-288`). `DeeperTransformer` ignores activation and dropout (`models.py:5-28, 31-38`). Initial weights come from `torch.manual_seed(seed_for_weights)` **after** the model is already built (`worker.py:324-331` vs `:386-390`), so the seed doesn't affect initial weights in that branch. The test profile overrides HtoA entirely (`config_utils.py:47-51`; `worker.py:311-313`). | **Partial / buggy.** |
| refM: initM ∈ {refM, (A(hpp), lp_ref)} (`:96, :116`) | Trainer passes keys `reference_model_state_cid` / `reference_dpodl_checkpoint_cid` (`trainer.py:171-172`), but the worker reads `config.get("reference_model_id")` (`worker.py:256`). That key isn't in `train_loop_config`, so it's always None. If it were set, `transfer_reference_weights` is undefined (`worker.py:261` commented, used at `:379`) and `transfer_weights` is called with arguments in the wrong order (`worker.py:381` vs `utils.py:306`). | **Not functional.** Workers always train from scratch. Model-referencing never actually happens. |
| Train → (M, acc, S, CPs = {(Mi, acc_i, Si)}) (`:98`) | Uses training accuracy? No — it uses accuracy on the test split (`worker.py:545`). CPs are hashes of states every 100 steps (`worker.py:521-525`). Intermediate models are not saved. | **Deviates.** The paper's block accuracy is *training* accuracy and test accuracy belongs to publishers (`:126, :34`). CPs can't be opened. |
| PostHash: `Hash(M, acc, S) ≤ T2` (`:99`) | `calculate_post_hash` matches the formula (`crypto.py:292-312`). `T2 = 2^256` (`config_utils.py:25`) accepts everything, same as the paper's toy config (`:271`). On-chain, `postHash` is a free parameter compared against `t1Threshold` ≈ 2^256 − 2^24 (`ModelRegistry.sol:327`; `helper-hardhat-config.js:8`). | **Disabled / unverifiable.** The T1/T2 roles are also swapped between Python and chain (acknowledged in `docs/architecture.md:108`). |
| Verify: checks h1, initM derivation, "M is trained correctly from initM … according to (S, CPs)", acc′ = acc, b′ = b (`:101-104`), via Merkle-tree spot-check with polylog verifier cost (`:124`) | Only a self-consistency check (`verification.py:131-323`). No initM derivation check, no CP opening, no accuracy re-measurement. | **Missing.** |
| Tacc relation R and block eligibility (`:174`) | Python Tacc = 0.97 (`config_utils.py:26`) vs on-chain 8500 bps (`helper-hardhat-config.js:9`). Models at 85–97% are classed as MTX by the worker but would be valid blocks on chain. | **Inconsistent.** |
| MTX contains prevBK, refM, nonce, initM, r, D, Tacc, M, acc, S, CPs; miners must reference the latest/highest MTX (anti-DoS) (`:148`) | `ModelTransaction` stores CID, accuracyBPS, steps, referenceModelCID string, submitter, timestamp, status (`MTXMempool.sol:85-95`). No "must reference latest" rule, no fee, no stake. | **Thin; anti-DoS rule missing.** |
| Step restriction across time slots: Σ referenced S + S_bk ≥ Σ main-chain S + Smin (`:164-166`) | Per-block `steps ∈ [min, max]` and `steps ≥ refBlock.steps + 50` (`ModelRegistry.sol:332-334, 277-279`). Because steps must increase monotonically under a fixed `maxTrainingSteps = 10000`, the chain dies after a bounded number of blocks (**scratch PoC 7 passed**: with minStepImprovement 5000, the 3rd block reverts; at defaults the cap is about (10000−100)/50 ≈ 198 blocks). | **Deviates; liveness bug.** |
| Incentives: selected block's miner gets S/(ΣSj+S), each recursively referenced Mj's miner gets Sj/(ΣSj+S) (`:178`) | Fixed `referenceRewardShareBPS = 20%` to the *one* directly referenced *block* proposer (`ModelRegistry.sol:406-421`). A flat `mtxRewardAmount` goes to whichever MTX the owner chooses (`:479-487`). | **Deviates.** Not proportional, not recursive. MTX rewards are discretionary. |
| Task publishers: split data, publish only training set + Tacc, evaluate test accuracy across ℓ time slots (`:142, :162`) | `TaskRegistry` stores free-text dataset and criteria strings and an unescrowed `rewardPool` (`TaskRegistry.sol:25-38`). Not referenced by any Python or contract code. No time-slot concept. | **Missing.** |
| Chain selection: longest-chain or weight-based (`:174-176`) | ModelRegistry is one linear list with "reference must equal current head" (`ModelRegistry.sol:306-319`). No forks, no weights. Ordering is whatever the host EVM chain decides. | **Not applicable / missing.** Effectively replaces the paper's consensus with a smart-contract registry. |
| Ledger security proofs (§5) | None of the assumptions hold: no Verify, no honest-majority verification. | — |
| After MTX promotion, chain continues | After `updateReferenceModelFromMtx`, `currentDpodlCheckpointCID` is set to the MTX CID, which isn't in `dpodlCheckpointCIDToBlockHeight`. So `verifyModelImprovement` reverts "not found in block history" (`ModelRegistry.sol:258-266, 474-475`). **Scratch PoC 8 passed:** after one block plus one MTX promotion, `submitBlock` is permanently bricked. The comment at `:260-264` acknowledges the gap. | **Bug.** The MTX and block paths are mutually exclusive after the first block. |
| "Distributed" meaning | The paper: "we do not require provers to perform a single training course together but let them train atop published pre-trained models" (`:33`). | See Q4. |

- zkDL (`Research_papers/2023-1174/2023-1174.md`) is only mentioned in docs as future work (`docs/StateOfTheArt.md:28, 80-84`; `README.md:311`). No zk code exists.

### Inferences
- The project follows the paper's toy implementation (T1 = 2^240, T2 = 2^256, Tacc 0.97 on MNIST, `579857605.md:271-273`) more closely than its protocol. The thresholds were copied, with T1 at 2^250, while the security-carrying parts (Verify, publisher test sets, referencing rules, step-sum rule) were not built.
- The paper's own Verify relies on "M is trained correctly from initM" checked via Merkle checkpoints (`:101-104, :124`). Any revival needs a concrete verification mechanism: re-execution with dispute, TEE attestation, or zk proofs à la zkDL. The paper treats that as a black box and the code doesn't approximate it.

### Gaps
- The paper doesn't give a concrete HtoA or weight function (`:178` and §5 are abstract), so "correct" HtoA fidelity can't be judged beyond the structure.

---

## Q4. Distributed-training reality

### Takeaway
It is **not** data-parallel training. Ray's TorchTrainer starts N processes and sets up a process group, but the model is never wrapped (`prepare_model`/DDP), so no gradients are ever all-reduced. Each rank independently trains a full copy on a disjoint 1/N shard, from identical initial weights, and submits its own MTX. Communication is local-cluster Ray (plus localhost IPFS and a Hardhat node). Nothing is designed for internet or WAN, heterogeneous, or untrusted participants.

### Cited Findings
- No `prepare_model`, `prepare_data_loader`, `DistributedDataParallel`, or `all_reduce` anywhere in `dpodl_core/` or `scripts/` (grep returns nothing). `torch.distributed` is imported but unused (`worker.py:6`).
- The model is built and stepped locally per rank: `worker.py:324-331, 403, 496-500`. Each rank gets `config["train_partitions"][rank]` (`worker.py:247`), built by contiguous slicing (`data_loader.py:126-141`).
- The same nonce, pre-hash, architecture, and seeds on every rank follow from the deterministic search with identical inputs (`worker.py:277-279`; PoC: nonce 140 → `{num_layers 4, gelu, 0.1, embed 384, heads 4}`).
- Each rank signs and submits its own MTX with its own key (`worker.py:338-353, 847-853`). The trainer then picks one by self-reported accuracy (`trainer.py:327`). Other ranks' work isn't merged; `merge_model_states` exists but is unused (`ipfs_utils.py:293`).
- All ranks share the same relative `checkpoint_path = "checkpoint_dpodl.pt"` for save and resume (`config_utils.py:28`; `worker.py:410, 662-667`), and each writes `worker_{rank}.log` to cwd (`worker.py:224-226`).
- Resume can override pre-hash, nonce, and seeds from whatever local file exists (`worker.py:415-429`). It also cumulatively inflates `steps_at_checkpoint` across runs (`worker.py:449`).
- Ray runs local by default (`trainer.py:86`), with `RunConfig(storage_path=file://…/ray_results)` (`trainer.py:191-195`), so it's a single-node storage assumption. `FailureConfig(max_failures=2)` (`:194`).
- Infrastructure is all localhost: IPFS `127.0.0.1:5001` (`blockchain_config.py:67`; `utils.py:217` hard-codes the address again), Hardhat `127.0.0.1:8545` (`blockchain_config.py:12`), started by `scripts/dev_up.sh:99-153`.
- `old_tests/deepspeed_ray.py` is the only DeepSpeed usage, a toy 10→1 linear model (`old_tests/deepspeed_ray.py:11-47`), yet `deepspeed==0.16.2` is a top-level requirement (`requirements.txt:1`).

### Inferences
- The two concepts conflict. DDP produces one model trained jointly by trusted, tightly synchronized peers. D-PoDL miners are independent, mutually distrustful provers, and "distributed" means sequential referencing (`579857605.md:33`). If DDP were switched on, the N ranks would be one miner (one key, one MTX), and the per-rank keys and MTXs would make no sense. Left off, the N ranks are just N weaker miners on 1/N of the data, all on the same machine. Neither matches a real decentralized-training system.
- A revival should decide whether a "miner" is a cluster (internal DDP/FSDP is fine) or a single participant in a cross-internet protocol. In the second case, low-communication methods such as DiLoCo/streaming DiLoCo-style outer optimizers would be needed instead of Ray all-reduce. That is outside this repo's evidence; another researcher should verify it.

### Gaps
- I can't confirm the Ray working-directory behaviour (shared vs. per-worker cwd) without running Ray 2.40, so whether ranks actually clobber one checkpoint file is unconfirmed.

---

## Q5. Model, dataset, scale; is HtoA meaningful for modern LLM training?

### Takeaway
AG News 4-class classification with a small, non-standard transformer of roughly 2–31M parameters, mostly embedding. HtoA chooses among about 2.6k grid points of one toy family and doesn't carry over to LLM pre-training, where architecture is fixed in advance and the only sensible "hash-derived" inputs are seeds and data order.

### Cited Findings
- Dataset: HF `ag_news`, 120k train / 7.6k test (`data_loader.py:92-95`). Tiny local CSVs exist at `data/ag_news_tiny/` (generated by `scripts/create_tiny_dataset.py`). Tokenizer: `bert-base-uncased`, max length 128 (`data_loader.py:113-116`).
- Model: embedding 30522×d + L × [MHA (4d² + 4d) + Linear d×d + 2 LayerNorm] + head (`models.py:5-58`). HtoA grid: d ∈ {128, 256, 384, 512}, L ∈ 4–12, heads constrained to divide d (`crypto.py:225-231, 271-276`).
- My arithmetic from those definitions:
  - smallest ≈ 3.9M embedding + ~0.33M blocks ≈ **4.2M**
  - largest (d = 512, L = 12) ≈ 15.6M + ~15.7M ≈ **31M**
  - test override (d = 64, L = 1) ≈ **2M** (`config_utils.py:47-51`)
- Architectural weaknesses: no positional encoding, mean-pool over padding (`models.py:62-69`). The feed-forward is a single d→d linear with no expansion (`models.py:13, 25`). The latest commit "Add LayerNorm to TransformerBlock to prevent loss explosion" (4f63c3b) shows training stability was only recently addressed.
- Python Tacc 0.97 (`config_utils.py:26`) mirrors the paper's MNIST toy target (`579857605.md:271`).
- `ALLOWED_DTYPES` / 200 MB model cap (`ipfs_utils.py:324-337`) and `hash_model_state` via `.numpy()` (`crypto.py:43`) would break for bf16 tensors (numpy has no bf16) and for multi-GB checkpoints.

### Inferences
- A 0.97 accuracy target on AG News is probably unreachable for this architecture. My general knowledge, which I couldn't check from repo sources, is that published AG News SOTA is around 95–96% with large pretrained models. So in dev mode every result becomes an MTX and the block path is never exercised.
- For LLM-scale work, HtoA as "random architecture per miner" is counter-productive. Models must be identical to be merged or referenced, and architecture search isn't the useful work. A modern analogue would derive only data-shard selection, seeds, and perhaps an eval-sample subset from a chain beacon.

### Gaps
- No training-run logs or accuracy results are committed (logs are gitignored, `.gitignore:21`), so achieved accuracy is unknown.

---

## Q6. Security and correctness issues

### Takeaway
The contracts are simple and mostly free of reentrancy risk, but trust and economics are broken: unverified self-reported submissions mint tokens, a single transaction can halt the chain, the admin has total control, and the MTX and block paths brick each other. On the Python side, insecure fallbacks are kept and tested, the signature isn't bound to the files it describes, and the IPFS endpoint is trusted.

### Cited Findings
**Contracts**
- Unverified reward minting: `submitBlock` is public and mints `blockRewardAmount` on self-reported data (`ModelRegistry.sol:295-443`). PoC 1 confirms.
- Unbounded `_accuracyBPS` → overflow on the next block → permanent halt (`ModelRegistry.sol:272, 322`). PoC 2 confirms.
- After an MTX promotion, `submitBlock` is bricked (`:258-266, 474-475`). PoC 8 confirms.
- Steps can only increase and are capped at max → finite chain lifetime (`:277-279, 332-334`). PoC 7 confirms.
- Admin powers:
  - Owner can change T1, Tacc, rewards, steps, the token address (`:552-654`), and pick any MTX for reward (`:455`).
  - Token deployer keeps DEFAULT_ADMIN and MINTER, so it can mint without limit (`DPoDLToken.sol:26-28`). It also gets 1M pre-mint (`:30`).
  - `setDpdlToken` can point rewards at any contract (`ModelRegistry.sol:628-632`).
  - Mempool owner can set any MTX to any status, including Pending again (`MTXMempool.sol:214-229`, transition checks commented out).
  - In dev, all roles are account #0 (`hardhat.config.js:50-63`).
- Reward minting failures are silently swallowed with try/catch for blocks (`ModelRegistry.sol:424-441`) but not for MTX rewards (`:482`). That's inconsistent.
- Spam / unbounded storage:
  - `submitMtx` is free and permissionless (`MTXMempool.sol:169-206`). The off-chain reader is O(N) RPCs (`blockchain_interface.py:228-235`).
  - `associateModelToTask` lets anyone push onto an unbounded array that `getTaskDetails` returns in full (`TaskRegistry.sol:193-209`), so a task's view can be gas-griefed.
- String CIDs everywhere (`ModelRegistry.sol:34-39`; `MTXMempool.sol:87-90`) increase gas costs, and no CID format is validated.
- `dpodlCheckpointCIDToBlockHeight[cid]` can be overwritten by resubmitting an existing CID (`ModelRegistry.sol:373`). No uniqueness check.
- Reentrancy: the only external calls are to the trusted token and mempool after state updates (`ModelRegistry.sol:474-489`). I saw no exploitable reentrancy.
- `postHash` is described as "the hash value that met the T1 threshold" (`ModelRegistry.sol:38`), but the Python side sends the post-hash checked against T2 (`worker.py:736`). The semantics differ between the two sides.

**Python**
- Insecure torch.load fallbacks kept:
  - `load_checkpoint` falls back to `weights_only=False` (`utils.py:270-276`).
  - `load_pickled_dict_from_ipfs` falls back to unsafe `torch.load` on IPFS bytes (`ipfs_utils.py:278-285`).
  - The test suite asserts the unsafe fallback happens (`tests/test_utils.py:118-154`).
  - The worker falls back to legacy `load_model_state_from_ipfs` when secure load fails (`worker.py:366-370`). That one uses `weights_only=True` (`ipfs_utils.py:211`).
- Signature not bound to the `files` section; `expected_submitter` optional (Q2; PoC 6).
- IPFS trust:
  - Everything goes through the local daemon API via `ipfshttpclient==0.7.0` (`requirements.txt:2`; `ipfs_utils.py:58`).
  - SHA-256 checks only compare against manifest-listed hashes.
  - No CID re-derivation is done client-side. CIDs are trusted from the daemon.
  - Legacy save/load formats don't match (pickle vs JSON, `ipfs_utils.py:233` vs `:254`).
- Keys:
  - Raw hex private keys come from env vars, one per Ray rank (`worker.py:338-339`) and for the operator (`trainer.py:388`).
  - `env.example:13-22` ships well-known Hardhat keys, which is fine for dev only.
  - `blockchain_interface.py` logs full tx data (`:298-303`).
  - `hardhat.config.js:9-15` reads `PRIVATE_KEY` for Sepolia, while `env.example:35` names it `DEPLOYER_PRIVATE_KEY`, so the variable names don't match.
- Logging and stdout hijack: `StreamToLogger` rewrites any line containing "error"/"failed" as ERROR (`utils.py:39-46`), and the trainer redirects global stdout/stderr (`trainer.py:75`). Both are fragile.
- Merkle: no leaf/node domain separation, duplicate-last padding (`crypto.py:69-71`), and it mutates the caller's list (`crypto.py:71`; PoC showed a 3-element list grow to 4). The worker passes a copy (`worker.py:561`).
- Pre-hash input concatenation without length-prefixing (`crypto.py:175-181`) is ambiguous in principle.
- The secure-checkpoint save records `nonce`, `pre_hash`, and `seed` but reads `dpodl_state.get("pre_hash", "")` while the state key is `pre_hash_value` (`worker.py:142` vs `:638`). So `pre_hash` is always empty in uploaded metadata.

### Inferences
- The contracts can't be "fixed" with access control alone. The core issue is that nothing trustworthy feeds them. Any redesign needs a verification oracle (optimistic dispute, validator committee, TEE, or zk) before minting.

### Gaps
- I ran no static analyzers (Slither/Aderyn) or fuzzers. The findings come from manual review plus the 8 scratch PoCs.

---

## Q7. Engineering quality: tests, CI, dependencies, dead code, docs accuracy

### Takeaway
The Solidity unit tests are reasonable for happy paths (71 pass after a lockfile workaround) but miss the MTX↔registry integration and every adversarial case. Python coverage is close to zero: 6 of 7 test files are empty, and CI would fail. Dependencies are a 2024-era, partly unpinned mix with a broken npm lockfile. Docs substantially overstate what is built.

### Cited Findings
**Tests**
- `tests/test_blockchain_interface.py`, `test_crypto.py`, `test_data_loader.py`, `test_models.py`, `test_trainer.py`, `test_worker.py` are **0 bytes**. Only `tests/test_utils.py` (220 lines) has tests: 6 tests on checkpoint save/load (mocked IPFS) and collate.
- `old_tests/test_training.py` is `assert 1 + 1 == 2` (2 lines). `old_tests/test_blockchain.py` is 0 bytes.
- Results: `pytest tests old_tests` → 7 passed. Bare `pytest -q` → collection error on `scripts/test_mtx_processing_e2e.py` (ImportError without web3). That module also has import-time side effects: `sys.exit(1)` without deployments (`scripts/test_mtx_processing_e2e.py:55-62`), plus importing the trainer and blockchain_interface connects to a node at import (`blockchain_interface.py:88`).
- The E2E script uploads legacy pickled checkpoints (`scripts/test_mtx_processing_e2e.py:87, 115`), but the trainer now only accepts secure manifests (`trainer.py:289-307`). So the E2E path would likely skip those MTXs. This is from reading the code; I didn't run it.
- Hardhat tests: 71 passing (`blockchain/test/*.js`). Coverage gaps: `updateReferenceModelFromMtx` and `updateMtxStatus` have 0 references in the tests (grep count 0). No tests for overflow, arbitrary submission, or improvement-after-MTX. `blockchain/test/ModelRegistry.test.js` uses `t1Threshold = 50000` (`:26`), unlike the deployment.

**CI**
- `.github/workflows/main.yml` runs only Python: `actions/checkout@v3`, `setup-python@v4` with Python 3.10.15, `pip install -r requirements.txt` (which pulls tensorflow, deepspeed, and torch), then bare `pytest` (`main.yml:20-38`).
- It never runs Hardhat tests, and bare pytest hits the e2e collection error above. CI as written would fail or be very slow. I have no CI run history to confirm.

**Dependencies**
- `requirements.txt`: `deepspeed==0.16.2`, `ipfshttpclient==0.7.0`, `memray==1.15.0`, `pytest==8.3.4`, `ray==2.40.0`, `torch==2.5.1`, torchaudio/torchvision pins, unpinned `ray[air]`/`ray[tune]`/`tensorflow`/`tensorboardX`, `dotenv` (the PyPI `dotenv` package rather than `python-dotenv`), `web3>=6.0.0`, `safetensors>=0.4.0`, `eth-account>=0.9.0`, `datasets>=2.0.0`, `transformers>=4.0.0` — `requirements.txt:1-19`.
- grep shows deepspeed only in `old_tests/`. tensorflow, memray, and tensorboard are never imported.
- `web3>=6.0.0` is wrong: the code imports `ExtraDataToPOAMiddleware` (`blockchain_interface.py:8`), which only exists in v7+ (worked under web3 8.0.0).
- `ray.air.config` imports (`trainer.py:11`) are the older AIR namespace.
- Node: `blockchain/package.json` uses `"*"` for hardhat, ethers, toolbox, and others (`:15-30`); the lockfile pins hardhat 2.24.0 / ethers 6.14.0 / OZ 5.0.2, so `npm ci` fails as described. `@nomiclabs/hardhat-etherscan` is deprecated (npm warning) and redundant with `@nomicfoundation/hardhat-verify` (`package.json:19-20`).
- There is a second, unrelated root `package.json`/`package-lock.json` duplicating the devDeps with chai ^5 vs ^4 (`package.json:16-29` vs `blockchain/package.json:24`).
- The Solidity compiler is pinned to 0.8.20 with viaIR (`hardhat.config.js:19-27`). It compiled against OZ 5.6.1 in my run.

**Dead or placeholder code**
- `blockchain/scripts/deploy.js` and `interact.js` are 0 bytes.
- `merge_model_states` (`ipfs_utils.py:293`), Merkle proof helpers (`verification.py:26-127`), and `load_and_verify_checkpoint_state` (`:327`) are unused.
- `DebugStep` event (`ModelRegistry.sol:125`) and large commented blocks remain (`trainer.py:35-64, 378-386`).
- The deprecated `get_current_reference_cid` is still used in docs (`docs/architecture.md:41`).
- Committed build artifacts: `blockchain/deployments/localhost/*`, which Python reads for addresses (`blockchain_config.py:18`).
- The root contains `2023-1174.pdf` and `579857605.pdf`.

**Docs vs code**
- `docs/StateOfTheArt.md:44, 60` cites `submitterRewardShare`, which doesn't exist (grep: only in that doc). `:78` says the project "has successfully implemented the core mechanics of the D-PoDL framework" — contradicted by Q2/Q3.
- `docs/architecture.md:50, 81` say the worker uses `t1Threshold`/`t2Threshold` "stored in ModelRegistry", but Python uses hard-coded config (`config_utils.py:24-26`; no on-chain threshold read in `dpodl_core/`). `:58-61` describes a reference weight transfer that is non-functional (Q3). `:97` says the checkpoint is uploaded and its CID submitted; the worker actually submits the manifest CID (`worker.py:848`).
- `README.md:39` claims "training large-scale AI models". `README.md:386` references `train/trainer.py`, which doesn't exist. `docs/OneCommandStartup.md:612` correctly says not to use it for production.

### Inferences
- About 31k lines are tracked, but the substantive code is roughly 4.6k lines of Python and 1.15k of Solidity (per `wc -l`). A large share is logging, commented-out code, and docs. This looks like an iteratively LLM-assisted prototype that grew features faster than tests.

### Gaps
- Current upstream versions (Ray Train V2 status, Hardhat 3 adoption, web3.py v7/v8 API) can't be confirmed from the repo. Another researcher should check them on the web.

---

## Q8. Bottom line: component-by-component keep / refactor / replace

### Takeaway
Keep the conceptual skeleton and a few clean utilities. Rewrite the contracts around a real verification and settlement design. Replace the hand-rolled training, storage, and "proof" layers with established tools. The current code proves the flow can be wired end to end on localhost. It provides no security, decentralization, or scale, so nothing should be reused as-is.

### Cited Findings
| Component | Files | Verdict | Reasoning (evidence) |
|---|---|---|---|
| Concept: hash-training-hash + MTX + referencing | `579857605.md:81-104, 148` | **Keep (as spec)** | The paper's structure is sound as a design target. The code doesn't implement its security parts (Q3). |
| `DeeperTransformer` model | `dpodl_core/models.py` | **Replace** | Toy, no positional encoding, 2–31M params (Q5). Use a standard HF/torchtitan/nanoGPT-style model. |
| HtoA | `dpodl_core/crypto.py:225-288` | **Replace / re-scope** | Ignored parameters, overridden in test, meaningless for fixed-architecture LLMs (Q3, Q5). Keep only beacon-derived seed and data-order derivation. |
| Pre/post-hash functions | `crypto.py:161-185, 292-325` | **Refactor** | Formulas are fine. They need binding to the chain beacon and miner identity, length-prefixed encoding, and a meaningful T2. Grindable as is (PoC 4). |
| Merkle tree | `crypto.py:50-156` | **Replace** | No domain separation, mutates its input, never used for proofs (Q2, Q6). Use a vetted library (e.g., OZ-compatible Merkle) if needed at all. |
| Self-"verification" | `dpodl_core/verification.py` | **Replace** | Self-check only, passes fabricated state (PoC 3). Needs a real verifier: re-execution/dispute, TEE, or zk (zkDL is the referenced research path, `docs/StateOfTheArt.md:80-84`). |
| Ray orchestration | `dpodl_core/trainer.py` | **Replace** | Not DDP, not decentralized (Q4). Use torch DDP/FSDP or torchtitan inside a miner, and a low-communication protocol across miners. |
| Worker loop | `dpodl_core/worker.py` (1005 lines) | **Rewrite** | Broken `submit_block` call, dead referencing, undefined variable, shared checkpoint path, sprawling (Q2–Q4). |
| Data loader | `dpodl_core/data_loader.py` | **Refactor** | Simple and works, but gives the test split to miners. Partitioning should be beacon-derived and verifiable (Q2). |
| Safetensors + signed manifest | `ipfs_utils.py:347-647`, `crypto.py:345-520` | **Keep idea, refactor** | Safetensors and a dtype allow-list are the right choices. Must bind the signature to file CIDs and hashes (PoC 6), make `expected_submitter` mandatory, and drop the unsafe pickle fallbacks (`ipfs_utils.py:278-285`; `utils.py:270-276`). |
| IPFS client | `ipfshttpclient==0.7.0` | **Replace** | Talks only to a local daemon API. Use a maintained client or pinning service, or an object store with content hashes (Q6). |
| Web3 interface | `dpodl_core/blockchain_interface.py` | **Refactor** | The tx helper is serviceable. Remove the import-time connection (`:88`), the O(N) mempool scan (`:228`), and verbose logging. Use an indexer or events. |
| DPoDLToken | `blockchain/contracts/DPoDLToken.sol` | **Keep (minor refactor)** | Standard OZ ERC20 + AccessControl. Renounce deployer MINTER, cap supply or use emissions. |
| ModelRegistry | `blockchain/contracts/ModelRegistry.sol` | **Replace** | Unverified minting, overflow halt, MTX/block brick, finite lifetime, owner-centric (PoCs 1, 2, 7, 8). Needs commit / challenge / settle around a verification oracle. |
| MTXMempool | `blockchain/contracts/MTXMempool.sol` | **Replace** | Free permissionless spam, no paper fields, owner can rewrite status (Q6). |
| TaskRegistry | `blockchain/contracts/TaskRegistry.sol` | **Replace** | Unconnected, no escrow, no held-out test-set commitment, unbounded array (Q1, Q6). |
| Hardhat project / deploy scripts | `blockchain/hardhat.config.js`, `deploy/*` | **Refactor** | Works on Hardhat 2. Fix the lockfile, pin versions, dedupe the `004_` scripts, remove `"*"` ranges. Consider Foundry for fuzzing. |
| Tests / CI | `tests/`, `blockchain/test/`, `.github/workflows/main.yml` | **Rewrite** | 6 of 7 Python test files empty, CI broken, no adversarial tests (Q7). |
| Docs | `docs/*.md`, `README.md` | **Rewrite** | They overstate the implementation (Q7). |
| Dev scripts | `Makefile`, `scripts/dev_up.sh`, `dev_down.sh` | **Keep (light refactor)** | Useful one-command local stack (`scripts/dev_up.sh:99-153`). |

### Inferences
- The best foundations to carry forward are the role and lineage *vocabulary* (MTX, reference, reward split), the safetensors manifest pattern, and the dev-stack scripts. Everything that carries security or performance weight should be replaced.

### Gaps
- Which specific external tools to adopt (low-communication training frameworks, verification networks, storage layers) is outside this code review's evidence and needs web research.
