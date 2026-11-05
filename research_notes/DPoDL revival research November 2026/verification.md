# Verifying that ML training and inference were actually and honestly performed by untrusted nodes (state as of 2026-11-05)

Scope note: research done 2026-11-05. Dates are given for each claim. "Vendor claim" means self-reported by a company or project and not independently benchmarked. GitHub API access was blocked in this session, so repo metadata (stars, licenses) comes from WebFetch of the GitHub HTML pages. Commit dates were not visible in those captures unless a changelog was present.

IMPORTANT CITATION FINDING FOR THE REVIEW: IACR ePrint **2023/1174 is zkDL** ("zkDL: Efficient Zero-Knowledge Proofs of Deep Learning Training", Haochen Sun, Tonghe Bai, Jason Li, Hongyang Zhang, Univ. of Waterloo; received 2023-07-30, revised 2023-12-08). It is **not** a "Distributed Proof-of-Deep-Learning" paper — [IACR ePrint 2023/1174](https://eprint.iacr.org/2023/1174). The repo's citation of "D-PoDL, IACR ePrint 2023/1174" looks wrong or conflated. The PoDL lineage that does exist: "Energy-recycling Blockchain with Proof-of-Deep-Learning" (arXiv 1902.03912) — [arXiv](https://arxiv.org/pdf/1902.03912); Boyang Li's Notre Dame dissertation "Proof-of-Deep-Learning Consensus in Blockchain Systems" (2022), which has a two-phase design and extends to proof-of-federated-learning subchains — [Notre Dame CurateND](https://curate.nd.edu/articles/thesis/Proof-of-Deep-Learning_Consensus_in_Blockchain_Systems/24869664); and a PoDL survey (Salhab & Mershad, Aug 2023) — [arXiv 2308.16730](https://arxiv.org/abs/2308.16730).

---

## 1. Proof-of-Learning (Jia et al. 2021), spoofing attacks and fixes to 2026; proof-of-training; how D-PoDL-style Merkle traces relate

### Takeaway
Plain PoL, meaning logged checkpoints plus a verifier that re-executes a sample of segments within a tolerance, has been shown to be spoofable more cheaply than honest training (2021–2023). Unfixed, it is not a security primitive. Later work makes cheating unprofitable rather than impossible ("incentive security"), or replaces tolerance-based checks with bitwise-reproducible re-execution (Verde/RepOps, Srivastava et al.) or with calibrated gradient-difference audits (OVIG, 2026). D-PoDL's Merkle roots over model-state hashes and a training-trace hash are only the commitment half of these schemes. Without a re-execution or challenge path they prove nothing about honest work.

### Cited Findings
- Zhang et al. (2021/2022) "'Adversarial Examples' for Proof-of-Learning" spoof a PoL using adversarial-example-style optimization of fake checkpoints — [arXiv 2108.09454](https://arxiv.org/pdf/2108.09454). A CleverHans Lab review (2022-05-22) notes the attack was described conceptually but convergence was hard. It also shows the root weaknesses: the verifier's error tolerance must exceed the worst stochastic error over the whole run, which an adversary can exploit, and the verifier checks only a subset of states — [CleverHans blog](https://cleverhans.io/2022/05/22/pol-attack.html).
- Fang et al., "Proof-of-Learning is Currently More Broken Than You Think" (IEEE EuroS&P 2023). They give the first practical, reproducible attacks across PoL configurations, with spoofing far cheaper than honest training, which contradicts PoL's original claim. Code is public — [arXiv 2208.03567](https://arxiv.org/abs/2208.03567v2).
- Zhao, Fang, Wang, Chen, Zhou, "Proof-of-Learning with Incentive Security" (arXiv 2404.09005, v1 Apr 2024, later revisions through v7). It changes the goal to making cheating not increase utility, claims security against the Zhang 2022 and Fang 2023 attacks, and claims verifier overhead improves from Θ(1) to O(log E / E) — [arXiv 2404.09005](https://arxiv.org/html/2404.09005v7). These are the authors' own claims; I did not verify them independently.
- 2025 thesis (Embry-Riddle): PoL combined with model watermarking, reporting 0.6% runtime overhead (parameter perturbation) up to about 11–17% (feature-based schemes). Not peer-reviewed — [ERAU Commons](https://commons.erau.edu/edt/905/).
- Srivastava, Arora, Boneh (Stanford), "Optimistic Verifiable Training by Controlling Hardware Nondeterminism" (ICML/NeurIPS-listed 2024, arXiv v3 Nov 2024). An auditor retrains. Hardware nondeterminism is handled by training at higher precision, rounding intermediates, and sharing logged rounding decisions via adaptive thresholding. They get **exact FP32 replication across A40, Titan XP and RTX 2080 Ti** for ResNet-50 (23M) and GPT-2 (117M) full training and fine-tuning. Code is public — [arXiv 2403.09603](https://arxiv.org/html/2403.09603v3). Storage is about 106 KB and time about 7 s, versus 350 MB for a prior ZK logistic-regression proof-of-training system (summary in search snippet) — [arXiv 2403.09603 PDF](https://arxiv.org/pdf/2403.09603).
- OVIG, "Optimistic Verification of AI Training Integrity via Gradient Signals" (Su, Yao, Zhang, Wang, Viswanath; v1 2026-06-19, v2 2026-09-29; arXiv preprint). A verifier replays training and flags gradient differences beyond an empirical boundary calibrated from honest replays on heterogeneous hardware, so **bitwise determinism is not required**. Evidence is kept only at stride-s interval endpoints. On Qwen3, stride s=2000 cuts storage and transmission by 1996x with **0% attack success** against shortcut and adaptive targeted attacks, at **+14.3% compute** over unverified training. No code repo is listed — [arXiv 2606.21045](https://arxiv.org/abs/2606.21045).
- SENTINEL (arXiv 2603.03592, Mar 2026): stagewise integrity verification for pipeline-parallel decentralized training. It checks activation and gradient transmissions between stages without duplicating computation and reports >90% F1 with hundreds of workers (snippet-level only) — [arXiv 2603.03592](https://arxiv.org/abs/2603.03592).
- "Towards TEE-Certified DP" (arXiv 2609.20532, Sep 2026): gradient computation is offloaded to untrusted GPUs, and a CPU TEE spot-checks by recomputing selected steps — [arXiv 2609.20532](https://arxiv.org/abs/2609.20532v1). The SoK on verifiable federated learning (IACR ePrint 2025/2296) catalogs "re-execute randomly sampled rounds inside an enclave" as an established pattern — [ePrint 2025/2296](https://eprint.iacr.org/2025/2296.pdf).
- Verde's checkpoint design is directly comparable to D-PoDL's Merkle trace. Each training-step checkpoint is a Merkle tree whose leaves hash per-operator graph nodes (inputs, outputs, op, attributes, tensor hashes). Hashing cost on an Apple M3 CPU: under 1 s for DistilBERT, about 2.5 s for Llama-1B, and about 15 s for Llama-8B per checkpoint — [Verde arXiv 2502.19405](https://arxiv.org/html/2502.19405).

### Inferences
- The D-PoDL repo already has the hard-to-retrofit piece, Merkle-committed checkpoints. What it lacks is (a) a reproducible or tolerance-calibrated re-execution primitive, (b) a challenge protocol that uses it, and (c) economic consequences (stake and slashing). Self-reported accuracy is trivially forgeable and should be replaced by validator-measured metrics, as in Templar's LossScore (section 4).
- Tolerance-based PoL verification, the Jia et al. style, should be avoided because of Fang et al. 2023. Either use bitwise reproducibility (Verde/RepOps, Srivastava) or a calibrated boundary with adversarial evaluation (OVIG). Note that OVIG is a 2026 preprint with no code.

### Gaps
- I could not find the actual paper behind "D-PoDL" under ePrint 2023/1174 (it is zkDL). The repo owner should confirm the intended reference.
- No peer-reviewed 2025–2026 paper was found that fully "fixes" Jia-style PoL against all known spoofing attacks while keeping its original cost model.
- "Proof of training data" (Choi et al. 2023) was not researched in depth this session.

---

## 2. Optimistic / refereed verification: Gensyn Verde + RepOps, ORA opML, Truebit-style dispute games, bisection over checkpoints (status 2026)

### Takeaway
Verde (Gensyn, Feb 2025) is the most concrete published design matching D-PoDL's architecture. It uses two-level bisection, first over Merkle-committed training checkpoints and then over operator nodes, so the referee re-executes **one operator**. It needs bitwise reproducibility (RepOps) and at least one honest trainer. Total overhead is claimed under 10x versus about 10,000x for crypto proofs. Gensyn's open runtime in 2026 is REE (inference-only, mixed MIT/proprietary license). The open-source parts are not a drop-in training verifier. ORA opML is an inference-only optimistic oracle with no visible 2026 progress.

### Cited Findings
- **Verde paper**: Arun, St. Arnaud, Titov, Wilcox, Kolobaric, Brinkmann, Ersoy, Fielding, Bonneau; arXiv 2502.19405, 2025-02-26; preprint, not shown as peer-reviewed. Security holds if at least one compute provider is honest — [arXiv abs](https://arxiv.org/abs/2502.19405). Details from [arXiv HTML](https://arxiv.org/html/2502.19405):
  - Phase 1: trainers commit N checkpoint hashes per level (N<100, chosen over binary search) and recurse on the diverging segment down to one training step. Re-execution cost is about 1/N + 1/N² + …, which is under 6% at N=20 and under 1.1% at N=100. Storage for Llama-8B FP32 is a few hundred GB at N=20 and a few TB at N=100.
  - Phase 2: per-node hash sequences locate the first differing operator. Only an output-hash mismatch requires the referee to recompute one operator, which is about two orders of magnitude less compute than the model and needs tens of MB of memory.
  - Refereed delegation costs at least 2x (two providers). Total is claimed under 10x, versus about 10^4 x for cryptographic proofs.
  - Limitations: FP32 only. Reproducibility holds only for a single GPU per setup; multi-GPU and model parallelism are future work. IEEE-754 is assumed. **Incentive design is not done** (BoLD suggested as a template). Trainer diversity is needed. The referee is **not implemented as a smart contract** because the EVM lacks floating point.
- **RepOps overhead vs PyTorch/cuDNN (FP32)**, from Verde Table 1 and 2 — [arXiv HTML](https://arxiv.org/html/2502.19405):
  - Matmul: under 30% (intro) versus 30–60% (Sec. 4.1) for dimensions above 2^10; the paper is internally inconsistent here. About 60–70% on RTX 3090 and about 35% on T4. About 200% for 256-dim matrices.
  - DistilBERT 66M: inference +74% (T4) / +84% (A100); training +258% (T4) / +312% (A100).
  - Llama-3.2-1B: inference +218% (T4) / +58% (A100); training +374% (T4) / +67% (A100).
  - Llama-3.1-8B on A100-80GB: inference +98%, LoRA fine-tune +126%. Full FP32 training of 8B did not fit.
- **Gensyn REE (Reproducible Execution Environment)**, [github.com/gensyn-ai/ree](https://github.com/gensyn-ai/ree), fetched 2026-11-05:
  - Docker-based; produces a "receipt" others can re-verify. **The current release is reproducible LLM inference only.**
  - **License is mixed**: SDK under MIT, but the compiler and reproducible-operator binaries are proprietary under the "REE Binary License Agreement".
  - About 25 stars, 4 forks, 12 commits.
  - Changelog: v0.2.0 (2026-04-20), reproducible-mode overhead cut 3x; v0.3.0 (2026-05-15), compile-time overhead cut 50%; then v0.4.0 (06-04), v0.5.0 (07-10), v0.6.0 (08-27), v0.7.0 (09-30), v0.8.0 (2026-10-05).
  - Pipeline parallel up to 72B. Experimental quantized path is H100-only. Receipts from older versions may not re-verify on newer ones.
  - No absolute overhead numbers are published.
- Gensyn mainnet timing: a Binance Research page (secondary) says the Delphi app launched on mainnet 2026-04-22 and the TGE was 2026-04-29 — [Binance Research](https://www.binance.com/research/analysis/aigensyn). A news article dated 2026-06-03 reports the mainnet launch — [StartupFortune](https://startupfortune.com/gensyn-launches-its-mainnet-and-bets-that-ai-agents-can-fix-the-broken-economics-of-decentralized-compute/). Exact dates conflict slightly across secondary sources; I did not confirm whether Verde-style training disputes are live on mainnet.
- **ORA opML** (Hyper Oracle; arXiv 2401.17555): an interactive fraud-proof (optimistic-rollup-style) dispute game for **inference**. The ORA on-chain AI oracle launched on Ethereum mainnet (Blockworks, 2024) with Llama2, Stable Diffusion and Grok — [arXiv 2401.17555](https://arxiv.org/pdf/2401.17555v1); [Blockworks](https://www.blockworks.com/news/ora-on-chain-oracle-ethereum). The weaker security assumption and challenge-period latency are the trade-offs noted. **No 2025–2026 status updates were found.**
- Verde two-level bisection is also described in secondary Gensyn explainers: iteration-level, then operation-level, with only the disputed op re-run — [indiebuidl Gensyn report (secondary)](https://portfolio-indiebuidl.vercel.app/blog/gensyn_pretge_report).

### Inferences
- For a small team, the Verde *protocol* can be re-implemented on top of D-PoDL's existing Merkle checkpoints: commit per-step checkpoint roots on-chain, then run an N-ary bisection challenge. The *determinism layer* is the blocker:
  - RepOps/REE binaries are proprietary, inference-only in public, and single-GPU FP32 in the paper.
  - Realistic alternatives: (a) restrict to one GPU SKU and a deterministic PyTorch config, then re-execute the disputed *training step* rather than a single operator, off-chain by a committee; (b) use OVIG-style tolerance boundaries; (c) the Srivastava rounding-log approach (open code, but small models).
- On-chain refereeing of float ops is infeasible on the EVM (Verde says so). The practical design is an off-chain referee committee (or a TEE referee) that posts its verdict on-chain, with slashing triggered by the verdict.

### Gaps
- Gensyn has published no 2026 peer-reviewed RepOps training-overhead numbers. The REE changelog gives only relative improvements.
- No public Gensyn repo was found that open-sources a Verde training-dispute implementation.
- Truebit and Arbitrum BoLD were not re-researched for 2026. They are cited only as design templates via the Verde paper.
- ORA's 2026 status is unknown.

---

## 3. Determinism: Thinking Machines batch-invariant kernels (Sep 2025) and follow-ups; deterministic modes in PyTorch/vLLM/SGLang; cost

### Takeaway
Since Sep 2025, run-to-run bitwise-deterministic LLM *inference* on a fixed hardware/software stack is achievable in vLLM (beta flag) and SGLang. The cost is about 25–60% throughput depending on stack and workload. Cross-hardware bitwise determinism is a different, harder problem: RepOps or Srivastava-style rounding is needed. Deterministic distributed *training* across heterogeneous untrusted nodes remains unsolved in open source.

### Cited Findings
- Thinking Machines' original batch-invariant approach is cited as about **61.5% overhead** baseline by a 2026 arXiv paper on reproducible builds — [arXiv 2606.03019](https://arxiv.org/pdf/2606.03019). A secondary report: Qwen3-8B, 1,000 requests take 26 s default vLLM versus 42 s batch-invariant (improved version) — [daily.dev](https://daily.dev/posts/why-temperature-0-isn-t-deterministic-in-llm-inference-embg7tbdo).
- SGLang deterministic inference (LMSYS blog, 2025-09-22): integrated the batch-invariant kernels with CUDA graphs. Average slowdown is about 34.35% (range 24.4–46.0%). Remaining overhead is mostly in matmul and attention kernels. Motivated by reproducible RL — [LMSYS](https://www.lmsys.org/blog/2025-09-22-sglang-deterministic/); range figures via [Spheron](https://www.spheron.network/blog/vllm-batch-invariance-why-temperature-0-isnt-deterministic/).
- vLLM: the `VLLM_BATCH_INVARIANT=1` flag is listed as beta, and custom all-reduce is disabled under tensor parallelism when it is on — [daily.dev](https://daily.dev/posts/why-temperature-0-isn-t-deterministic-in-llm-inference-embg7tbdo); [Konishi blog](https://hidekazu-konishi.com/entry/reproducible_llm_inference.html).
- LLM-42 (arXiv 2601.17768, Jan 2026): decode–verify–rollback on SGLang. It reports SGLang deterministic mode at up to 56% overhead and says its own overhead scales with the fraction of traffic needing determinism — [arXiv 2601.17768](https://arxiv.org/html/2601.17768v1).
- MarginGate (arXiv 2605.30218, May 2026): sparse margin-triggered verification for batch-invariant inference — [arXiv 2605.30218](https://arxiv.org/pdf/2605.30218). Details were not read.
- DeepSeek-V4 tech report (arXiv 2606.19348, Jun 2026) reports batch-invariant deterministic kernels with "minimal" overhead via a dual-kernel decode strategy. No comparable percentage is given — [arXiv 2606.19348](https://arxiv.org/pdf/2606.19348).
- Commentary (secondary) says MoE coverage in vLLM and SGLang deterministic modes was lacking — [Perrone substack](https://theaiengineer.substack.com/p/what-makes-inference-nondeterministic). Treat this as possibly outdated.
- Cross-hardware training determinism: RepOps adds roughly +67% to +374% for training depending on model and GPU (section 2). Srivastava et al. reach exact FP32 cross-GPU replication only up to GPT-2 117M and ResNet-50 — [arXiv 2403.09603](https://arxiv.org/html/2403.09603v3).

### Inferences
- If D-PoDL nodes run heterogeneous GPUs, batch-invariant inference kernels alone do not make a challenger's re-execution match bit-for-bit. Either pin hardware and software for all nodes and the referee, or use tolerance-based comparison (OVIG, TOPLOC).
- For verifying *evaluation claims* (accuracy and loss reported by workers), deterministic inference on a pinned stack is cheap enough: about 1.3–1.6x on the verifier side only.

### Gaps
- The Thinking Machines blog post itself and any 2026 follow-up from Thinking Machines were not fetched. Figures come via secondary citations.
- PyTorch `torch.use_deterministic_algorithms` training overhead was not measured or sourced in this session.

---

## 4. Cheap probabilistic checks: TOPLOC, SYNTHETIC/GENESYS, Templar Gauntlet, spot-check re-execution, Ambient proof-of-logits

### Takeaway
The approaches actually deployed in 2025–2026 decentralized training are cheap statistical checks, not proofs:
- TOPLOC-style activation fingerprints for inference/rollouts: about 258 bytes per 32 tokens, validated faster than generation.
- Loss-improvement scoring of submitted gradients (Templar Gauntlet/LossScore, used to pretrain Covenant-72B permissionlessly).
- Logit-hash spot checks (Ambient; vendor claims).

These are open-source (MIT for TOPLOC and Templar) and are the most mergeable components for D-PoDL.

### Cited Findings
- **TOPLOC** (Ong, Di Ferrante, Pazdera, Garner, Jaghouar, Basra, Ryabinin, Hagemann; arXiv 2501.16007, v1 2025-01-27, v2 2025-05-30). It is a locality-sensitive hash of top-k last-hidden-state activations. It claims **100% detection** of unauthorized changes to model, prompt or precision with no false positives or negatives in the authors' evaluation. **About 258 bytes per 32 new tokens** versus 262 KB for raw embeddings (Llama-3.1-8B-Instruct), a 1000x reduction. It is robust across GPU types and algebraic reorderings — [arXiv 2501.16007](https://arxiv.org/abs/2501.16007). Prime Intellect's launch claim (2025-01): robust across GPU types, TP configs and attention kernels, with validation up to 100x faster than generation — [Prime Intellect on X](https://x.com/PrimeIntellect/status/1884343700245074092).
- TOPLOC repo [github.com/PrimeIntellect-ai/toploc](https://github.com/PrimeIntellect-ai/toploc): **MIT**, about 64 stars, 15 forks, 63 commits, no releases (fetched 2026-11-05). PyPI package: [pypi.org/project/toploc](https://pypi.org/project/toploc/). Inference-only.
- **TOPLOC v2** (SYNTHETIC-2 blog, 2025): extends to pipeline-parallel inference and uses reproducible Gumbel noise, so verifiers can check *sampling* faster than generation — [Prime Intellect SYNTHETIC-2](https://www.primeintellect.ai/blog/synthetic-2).
- INTELLECT-2 (arXiv 2505.07291, May 2025) used TOPLOC to verify rollouts from untrusted, globally distributed inference workers in decentralized RL — [arXiv 2505.07291](https://arxiv.org/pdf/2505.07291).
- **INTELLECT-3** (tech report arXiv 2512.16144, 2025-12-18): 106B-A12B MoE post-trained from GLM-4.5-Air. Trained **on a centralized 512×H200 cluster** (64 nodes; RL used 60 nodes, split 16 training / 44 inference) over two months. The report does **not** mention TOPLOC or untrusted-worker verification — [arXiv 2512.16144](https://arxiv.org/html/2512.16144v1). (I read the first ~100k of 117k characters.) Secondary commentary frames this as decentralization ambition meeting centralized reality — [implicator.ai](https://www.implicator.ai/prime-intellects-intellect-3-open-source-ambition-meets-centralized-reality/).
- **Templar / Gauntlet**:
  - "Incentivizing Permissionless Distributed Learning of LLMs" (arXiv 2505.21684, May 2025) introduced Gauntlet — [arXiv 2505.21684](https://arxiv.org/pdf/2505.21684).
  - Covenant-72B tech report (arXiv 2603.08163, Mar 2026): 72B params, about 1.1T tokens, permissionless on Bittensor subnet 3 over commodity internet. The Gauntlet validator scores pseudo-gradients and selects top contributors per round, and contributions are normalized by median norm — [arXiv 2603.08163v2](https://arxiv.org/html/2603.08163v2); [Templar on X](https://x.com/tplr_ai/status/2031388295972929720).
  - The core metric is LossScore, the loss reduction on specific batches. A free-rider check compares loss on assigned versus unassigned data, and peers must be synced to the latest model — [Lacuna summary](https://lacuna.tiptreesystems.com/work/covenant-72b-pre-training-a-72b-llm-with-trustless-peers-over-the-internet/wrk_d626afc659acb055d986585614c7fe7b); [alphaXiv](https://www.alphaxiv.org/abs/2603.08163).
  - Templar repo [github.com/one-covenant/templar](https://github.com/one-covenant/templar): **MIT**, about 163 stars, 55 forks, 2,321 commits. **The page says the protocol is dormant / "not currently active"** after Covenant-72B (fetched 2026-11-05). The README's validator loop: deterministic seeding chooses the miner's data subset, loss is measured before and after applying the miner's decompressed gradient, the score is the loss reduction (moving average), and it is set as on-chain weights. No re-execution or proofs.
- **Ambient Proof of Logits** (vendor docs): for each token the miner hashes the logits, and the proof is a hash over the list. A validator re-runs **a single token step** on the same context and compares hashes. Ambient claims **about 0.1% verification overhead** "in development contexts" and is explicit that it proves *which model ran*, not correctness — [Ambient docs](https://ambient.xyz/docs/learn/proof-of-logits); [Ambient verified inference](https://ambient.xyz/verified-inference). The 0.1% figure is a vendor claim and third parties note it must hold in production — [BlockEden 2026-02-11](https://blockeden.xyz/blog/2026/02/11/ambient-ai-powered-blockchain-proof-of-logits/). No audit or peer review was found. Architecture descriptions (own L1 vs. on Solana) conflict across sources.
- Exact logit-hash matching implicitly requires deterministic inference (section 3). TOPLOC instead tolerates nondeterminism by design — [arXiv 2501.16007](https://arxiv.org/abs/2501.16007).

### Inferences
- The highest-leverage, lowest-cost change for D-PoDL is to replace *self-reported* accuracy and steps with validator-recomputed metrics, Templar-style. Validators deterministically derive each worker's data shard from a seed, apply the worker's committed update to the committed prior state, and measure loss and accuracy themselves on held-out and assigned data. This catches lazy or free-riding workers without any determinism requirement.
- TOPLOC is the natural fit if D-PoDL also verifies *inference* (evaluation outputs, RL rollouts). It is MIT and pip-installable. It does not verify training steps.
- Loss-improvement scoring is an *incentive* mechanism, not proof of specific computation. It can reward copied or plagiarized updates unless combined with commitments (D-PoDL's Merkle trace) and sync/assigned-data checks.

### Gaps
- GENESYS / SYNTHETIC-1 validation details were not separately researched.
- I found no confirmation that TOPLOC was used in INTELLECT-3. The report suggests a centralized cluster.
- No independent security analysis of Gauntlet/LossScore against adaptive adversaries (e.g., gradient-copying with noise) was found this session.

---

## 5. zkML: zkDL follow-ups, zkLLM, zkPyTorch, DeepProve, EZKL, JOLT Atlas, others; proof of training feasibility in 2026

### Takeaway
In Nov 2026, ZK proving of LLM **inference** works up to about 8B parameters (and projected about 400B) but costs roughly 50–1,100x serving compute, or about 10^4x by other estimates. **ZK proof of training** has been demonstrated only for about 10M-parameter CNNs (zkDL, Kaizen), small DP-SGD, and LoRA fine-tuning claims. Full ZK proof of training for anything beyond toy or small models is not practical. zkDL, cited by the repo as "the future path", has itself been partly superseded (its zkReLU was replaced by zkLLM's tlookup) and has no known follow-up release.

### Cited Findings
- **zkDL** (Sun, Bai, Li, Zhang; Waterloo; arXiv 2307.16273 / ePrint 2023/1174, Dec 2023): zkReLU plus FAC4DNN circuits with aggregation across layers and steps. **Under 1 s per batch update for an 8-layer, 10M-param network, batch 64** — [arXiv 2307.16273](https://arxiv.org/pdf/2307.16273). The project page says the ReLU approach is superseded by zkLLM's tlookup — [zkDL project page](https://cs.uwaterloo.ca/~h299sun/project/zkdl). No "zkDL++" or 2025–26 follow-up was found.
- **Kaizen** (Abbaszadeh, Pappas, Papadopoulos, Katz; ePrint 2024/162): zkPoT for DNNs with recursive composition over SGD iterations. VGG-11 (10M params), batch 16: **proof 1.36 MB, verifier 103 ms independent of iteration count** — [ePrint 2024/162](https://ia.cr/2024/162). Prover cost was not captured.
- Garg et al. zkPoT (logistic regression) combines MPC-in-the-head and zkSNARKs — [zkPoT paper](https://assets.tina.io/1fb09d03-9237-4c49-aaa9-d024a83c7ac7/zkPoT-lightweight.pdf).
- **VeriDP** (PoPETs 2026): ZK proof of correct DP-SGD. Verifier 2–5 ms, proof 3–4 KB, prover linear in sample count — [PoPETs 2026-0070](https://petsymposium.org/popets/2026/popets-2026-0070.php).
- "Verifiable Fine-Tuning for LLMs" (arXiv 2510.16830, Oct 2025): claims end-to-end ZK verifiable **parameter-efficient (LoRA)** fine-tuning is "feasible today". It says gradients, optimizer state and sampling enlarge circuits, so scaling is the bottleneck — [arXiv 2510.16830](https://arxiv.org/pdf/2510.16830). Numbers were not retrieved.
- **LLM inference proving, Sep 2026 comparison** (SASH research note, "Towards Proving Frontier-Scale LLM Inference", aisafety.sg) — [aisafety.sg note](https://www.aisafety.sg/research/what-proving-llm-inference-actually-costs-research-note):
  - zkLLM (CCS 2024): Llama-2 13B, 2,048 positions in 803 s on A100, proof under 200 kB.
  - zkPyTorch (Polyhedra, 2025): Llama-3 8B, 150 s per position on 1 CPU thread.
  - OpenLLM (2026): Qwen-3 8B, 258.6 s per forward pass on 32-core CPU, verify 0.33 s, proof 55.7 MB.
  - DeepProve (2026): GPT-2 124M / Gemma-3 270M full decode at 174 / 86 tokens per minute on 16–24 CPU cores, proof 24 MiB.
  - VerInf (2026 draft): Llama-4 Maverick 400B MoE, 1,000 positions in 14.3 h on a DGX Spark, proof 93.6 GB.
  - "Attestable" (closed source, reported): Llama 8B at 195 tok/s on H100, and 53–77 tok/s for Gemma-4-31B.
  - SASH prototype: Llama-3.1 8B, 4,096+512 tokens, 1.0–1.5 h on one H100 ($3.37–5.01), CPU verify about 2 min, proof 18.5 GiB. Overhead is **about 1,100x vs vLLM** for the whole request and 46–122x for the answer tokens. Not ZK and not audited.
  - Projection: 405B at 16–24 h per request on one H100. Literature cost estimates range from about 10,000x (Petrie 2026) to 500,000x (Baker et al. 2025) the cost of inference. Proving a 0.01% random sample of requests changes the economics.
  - **No proofs of training are covered.**
- **DeepProve** repo [github.com/Lagrange-Labs/deep-prove](https://github.com/Lagrange-Labs/deep-prove) (fetched 2026-11-05):
  - **"Lagrange License"**, a custom license, not standard OSS. About 3.4k stars, 1,219 commits.
  - GPT-2, Gemma 3 and Llama 2 confirmed end-to-end, plus MLP/CNN.
  - Benchmarks on a 24-core / 504 GB CPU, 512 tokens: GPT-2 prove 7.6 min, verify 1.3 s, 10.7 MiB. Gemma 3 prove 19 min, verify 4.3 s, 27 MiB.
  - Inference only; no audit mentioned.
  - The launch claim of "54–158x faster than EZKL" (Mar 2025) is a vendor claim — [Lagrange blog](https://lagrange.dev/blog/announcing-deepprove-zkml).
- **JOLT Atlas** (arXiv 2602.17452, Feb 2026; ICME Labs, built on a16z's Jolt lookup-based zkVM): nanoGPT about 14 s versus EZKL about 237 s — [arXiv 2602.17452](https://arxiv.org/html/2602.17452). Repo [github.com/ICME-Lab/jolt-atlas](https://github.com/ICME-Lab/jolt-atlas): ONNX-based. GPT-2 125M proof 14.9 s, verify 1.0 s, end-to-end 16.9 s on a MacBook Pro M3 16 GB. About 81 stars, 378 commits. License file present but type not visible. Inference only.
- **EZKL** [github.com/zkonduit/ezkl](https://github.com/zkonduit/ezkl): about 1.2k stars, 860 commits, ©2026 footer, active PRs. v21.0.0 was audited by Trail of Bits (report dated Mar 2025). Quantized Halo2-based inference proofs. License type was not visible in the capture, and contributors sign a CLA to Zkonduit Inc. Practical only for small models.
- Secondary claims to discount: a johal.in "MLPerf-ZK 2025" benchmark could not be verified — [johal.in](https://www.johal.in/zkml-python-ezkl-proof-generation-for-models-2026). The aisafety.sg note warns that published "proving time" figures exclude witness or table generation and are not comparable.
- Verde authors estimate cryptographic proofs at about 4 orders of magnitude overhead, versus under 10x for refereed delegation — [arXiv 2502.19405](https://arxiv.org/html/2502.19405).

### Inferences
- Replacing D-PoDL's trust assumption with zkDL-style proofs of every training step is not realistic for useful models in 2026. Prover cost for training adds the backward pass, optimizer state and many steps on top of inference costs that are already 50–1,000x+.
- A realistic ZK role is narrow: (a) prove a *single disputed step or operator* at the end of a bisection game, where the dispute is on small tensors (Verde shows operators are tens of MB); or (b) prove *evaluation* (inference) of a small committed model on a committed test set to certify reported accuracy. EZKL and JOLT Atlas are the most practical open tools for small models. DeepProve's custom license needs legal review before merging.

### Gaps
- Polyhedra zkPyTorch repo, license and 2026 status were not fetched. Only the 150 s/token figure came via the SASH note.
- Modulus Labs and Giza/Orion/LuminAIR 2026 status was not researched (no data gathered).
- Kaizen prover time and hardware were not captured.
- No 2026 benchmark of ZK proof of training for models over 100M params was found.

---

## 6. TEEs: NVIDIA H100/H200/Blackwell CC + attestation, Intel TDX / AMD SEV-SNP; Phala, Secret, Atoma, NEAR AI; TEE.fail / WireTap / Battering RAM

### Takeaway
GPU TEEs (H100/H200 CC paired with TDX or SEV-SNP CVMs) give near-native performance for compute-heavy LLM workloads. Vendor claims are low-single-digit to about 7% overhead. They are deployed by NEAR AI, Phala and others. However, the 2025 memory-bus interposer attacks broke the attestation root on physically accessible machines:
- WireTap and Battering RAM target DDR4.
- TEE.fail (IEEE S&P '26) targets DDR5, costs under $1,000, forges TDX quotes passing Intel DCAP "UpToDate", and extracts SEV-SNP keys.
- Because NVIDIA GPU attestation is not bound to the CVM, a forged CPU attestation lets an operator relay borrowed GPU attestation reports.

For permissionless nodes that control their own hardware, TEE attestation is therefore **not** a sufficient sole guarantee in 2026. It is useful as a cost-raising layer, or when operators are known datacenters.

### Cited Findings
- **TEE.fail**, from Georgia Tech, Purdue and van Schaik LLC, building on WireTap — [tee.fail](https://tee.fail/); [paper](https://tee.fail/files/paper.pdf):
  - DDR5 memory-bus interposer, passive (observe only), estimated **under $1,000** in parts plus a logic analyzer.
  - Extracted the Intel provisioning certification key and forged SGX/TDX quotes that **passed Intel DCAP at "UpToDate"**. Extracted ECDSA keys from an **AMD SEV-SNP VM even with Ciphertext Hiding**.
  - **NVIDIA CC**: attestation isn't bound to a specific CVM/CPU, so attackers can relay GPU attestation reports from other machines. NVIDIA has no mitigation.
  - Intel (advisory 2025-10-28) and AMD (AMD-SB-3040) consider physical interposers out of scope.
  - Impacts named: Phala dstack (an operator can run non-confidential VMs while forging attestations, including borrowed GPU attestation); Secret Network (consensus seed extractable; network restricted to trusted operators); BuilderNet.
  - Requires physical access and root — [BleepingComputer](https://www.bleepingcomputer.com/news/security/teefail-attack-breaks-confidential-computing-on-intel-amd-nvidia-cpus/); [SecurityWeek](https://www.securityweek.com/new-attack-targets-ddr5-memory-to-steal-keys-from-intel-and-amd-tees/).
- WireTap and Battering RAM (2025) were the DDR4 predecessors. TEE.fail extends them to DDR5 — [SecurityWeek](https://www.securityweek.com/new-attack-targets-ddr5-memory-to-steal-keys-from-intel-and-amd-tees/); [Safeheron analysis](https://safeheron.com/blog/recent-advances-and-technical-analysis-in-tee-security/).
- A 2026 commentary piece frames it as "a $1,000 interposer broke the keys" — [ajayk.sh](https://www.ajayk.sh/blog/confidential-computing-tees-ai-agents-2026/). No 2026 vendor fix for interposer attacks was found.
- **NEAR AI private inference**:
  - Docs say inference runs in TEEs with NVIDIA CC and "minimal latency overhead" (vendor claim) — [NEAR AI docs](https://docs.near.ai/cloud/private-inference).
  - Open-source Private ML SDK targets H100/H200/B100 with Intel TDX and reports minimal overhead for Phi3-14B and Llama3.1-70B, with I/O overhead negligible for compute-heavy workloads — [private-ml-sdk (ecosyste.ms)](https://awesome.ecosyste.ms/projects/github.com%2Fnearai%2Fprivate-ml-sdk).
- Academic benchmark: "Confidential Computing on NVIDIA Hopper GPUs: A Performance Benchmark Study" (arXiv 2409.03992, Sep 2024) quantifies TEE-mode overhead for LLM inference — [arXiv 2409.03992](https://arxiv.org/pdf/2409.03992). Specific numbers were not retrieved this session.
- Vendor (VoltageGPU) blogs claim about 5.2% and 3–7% overhead for TDX + H200 inference. These are self-published and unreplicated — [dev.to VoltageGPU](https://dev.to/voltagegpu/private-ai-inference-in-2026-hipaa-gdpr-without-the-hyperscaler-tax-1l76).
- TEE spot-check pattern for training: a CPU TEE recomputes sampled steps from untrusted GPUs — [arXiv 2609.20532](https://arxiv.org/abs/2609.20532v1).

### Inferences
- For D-PoDL, a TEE requirement for workers would (a) restrict participation to CC-capable hardware (H100 and up, plus TDX/SEV-SNP hosts), contradicting permissionless mining; and (b) not stop a determined operator with physical access, given TEE.fail. TEE attestation fits best for the **referee or validator** role, run by known or reputable cloud operators, or as one signal combined with economic slashing.
- Treat TEE attestation as "raises cheating cost to physical-attack level" rather than "proves honest work". Bind GPU attestation to the CVM using nonce-in-report and per-session keys where the SDK allows it, but note TEE.fail shows the relay problem is not fully fixed by NVIDIA.

### Gaps
- NVIDIA Blackwell (B200) TEE-I/O and multi-GPU CC status and overheads for 2026 were not researched.
- Atoma and Secret AI inference status in 2026 was not researched.
- Phala GPU TEE benchmarks were not found.
- The numbers from arXiv 2409.03992 were not retrieved. From memory and unverified, the abstract reports under 7% overhead for most typical LLM queries, mainly from PCIe encryption. Verify before citing.

---

## 7. Best fit for a small team reviving D-PoDL in 2026 (pros/cons, repos, licenses, activity)

### Takeaway
The recommended architecture is a hybrid optimistic design with validator-recomputed metrics. It reuses D-PoDL's existing Merkle commitments and needs no new cryptography:
1. Workers commit per-step (or per-k-step) checkpoint Merkle roots, data-shard seeds and update hashes, and post stake.
2. Validators independently recompute loss and accuracy from committed states, Templar/Gauntlet LossScore-style, instead of trusting self-reports.
3. A challenge window allows N-ary bisection over the committed checkpoints (Verde Phase 1) down to one training step. That step is re-executed by a referee committee on a pinned hardware/software stack (or under an OVIG-style calibrated tolerance), with slashing.
4. Optionally, TOPLOC fingerprints for any inference or eval outputs, TEE attestation for referees, and small-model zk proofs (EZKL/JOLT Atlas) only for disputed operators or for eval on small models.

Full zkDL-style ZK proof of training should be dropped as the near-term path.

### Cited Findings
- Bisection re-execution cost is under 6% at N=20 and under 1.1% at N=100. The referee recomputes one op, and total overhead is under 10x versus about 10^4x for ZK. Weaknesses: needs one honest trainer and bitwise reproducibility; FP32 single-GPU only; no incentive layer; EVM can't referee floats — [Verde arXiv 2502.19405](https://arxiv.org/html/2502.19405).
- OVIG shows tolerance-based replay can work without bitwise determinism at +14.3% compute, with 0% attack success in its evaluation (preprint, no code) — [arXiv 2606.21045](https://arxiv.org/abs/2606.21045).
- Templar's validator-measured loss-improvement scoring trained a 72B model permissionlessly (Mar 2026). The repo is MIT but now dormant — [arXiv 2603.08163](https://arxiv.org/html/2603.08163v2); [github.com/one-covenant/templar](https://github.com/one-covenant/templar).
- TOPLOC: MIT, pip-installable, about 258 B per 32 tokens, inference only — [github.com/PrimeIntellect-ai/toploc](https://github.com/PrimeIntellect-ai/toploc); [arXiv 2501.16007](https://arxiv.org/abs/2501.16007).
- Gensyn REE: reproducible inference receipts, actively released (v0.8.0, 2026-10-05), but core operators are proprietary binaries — [github.com/gensyn-ai/ree](https://github.com/gensyn-ai/ree).
- Srivastava et al. rounding-log replication: public code, exact cross-GPU FP32 replication for models up to GPT-2 117M — [arXiv 2403.09603](https://arxiv.org/html/2403.09603v3).
- zkML options for small models:
  - EZKL: Trail of Bits audited v21, about 1.2k stars — [github.com/zkonduit/ezkl](https://github.com/zkonduit/ezkl).
  - JOLT Atlas: GPT-2 about 15 s on an M3 — [github.com/ICME-Lab/jolt-atlas](https://github.com/ICME-Lab/jolt-atlas).
  - DeepProve: custom Lagrange License, GPT-2 7.6 min — [github.com/Lagrange-Labs/deep-prove](https://github.com/Lagrange-Labs/deep-prove).
- TEE caveat: TEE.fail forges TDX and relays NVIDIA attestation with physical access — [tee.fail](https://tee.fail/).
- PoL incentive-security framing (make cheating unprofitable) is a formal basis for sampling-plus-slashing designs — [arXiv 2404.09005](https://arxiv.org/html/2404.09005v7).

Comparison summary (all from the sources above):

| Approach | Verifies training? | Overhead (sourced) | Determinism needed | Maturity Nov 2026 | Mergeable OSS |
|---|---|---|---|---|---|
| Self-report + Merkle (current D-PoDL) | No | ~0 | No | n/a | — |
| Validator-recomputed loss (Templar Gauntlet) | Usefulness of update, not exact compute | Validator eval cost per miner | No | Used for 72B run (Mar 2026); repo dormant | Templar, MIT |
| Optimistic bisection (Verde) | Yes (exact) | ≥2x replication; <10x total; RepOps +58% to +374% | Bitwise | Preprint 2025; REE inference-only | REE: MIT SDK + proprietary binaries |
| Calibrated gradient replay (OVIG) | Yes (tolerance) | +14.3% compute | No | Preprint Jun/Sep 2026 | No code |
| Rounding-log replication (Srivastava) | Yes (exact) | Small storage; tested ≤117M | Achieved cross-GPU | Peer-reviewed 2024 | Public code |
| TOPLOC | Inference/rollouts only | ~258 B / 32 tokens | No | Used in INTELLECT-2 (2025) | toploc, MIT |
| Proof of logits (Ambient) | Inference only | ~0.1% (vendor claim) | Yes (exact hash) | Vendor, unaudited | — |
| zkML inference | Inference | 46x–1,100x (SASH); ~10^4x estimates | No (quantized) | ≤8B measured | EZKL, JOLT Atlas, DeepProve (custom license) |
| ZK proof of training (zkDL, Kaizen) | Yes | <1 s/batch for 10M-param net (zkDL) | No | Research; ≤10M params | zkDL research code |
| GPU TEE | Attests environment | ~3–7% (vendor claims) | No | Deployed (NEAR AI, Phala) but broken by physical attacks | NEAR private-ml-sdk, Phala dstack |

### Inferences
- Suggested phased plan for a small team:
  - **Phase 0**, days to weeks: fix the trust hole. Stop trusting self-reported accuracy and steps, and have validators recompute eval metrics from committed weights (Templar pattern). Fix the zkDL/D-PoDL citation.
  - **Phase 1**: add stake, a challenge window, N-ary bisection over the existing Merkle checkpoint roots, and step-level re-execution by a referee committee on a pinned GPU SKU, deterministic PyTorch and the same container. Slash on mismatch.
  - **Phase 2**: tolerance-based comparison (OVIG-style calibration) to permit heterogeneous hardware. TOPLOC for any inference outputs. Optional TEE attestation for referees.
  - **Phase 3, research**: zk proof of the single disputed operator or step for small models. Watch REE in case Gensyn opens training reproducibility.
- The main residual risks:
  - Collusion between worker and challengers, since the protocol needs at least one honest challenger. Mitigate with random challenger assignment and challenger rewards.
  - Data availability of checkpoints. A few hundred GB to TB for 8B models (Verde), so the off-chain storage design matters.
  - The EVM can't do float refereeing, so verdicts come from an off-chain committee or TEE and need their own trust model.

### Gaps
- Recent commit dates for TOPLOC, Templar, EZKL, JOLT Atlas and DeepProve could not be retrieved, because the GitHub API was blocked and the HTML captures lacked dates. Only REE has a dated changelog, the latest entry 2026-10-05.
- The JOLT Atlas license type and EZKL's current license were not confirmed.
- No source gives an end-to-end cost for running a Verde-style dispute on a real decentralized training network in production. Gensyn's mainnet use of Verde for training is unconfirmed.
