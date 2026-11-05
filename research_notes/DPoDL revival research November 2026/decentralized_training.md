# Low-Communication, Internet-Scale Decentralized AI Training: State of the Art as of 2026-11-05

Scope: algorithms, landmark runs, decentralized RL/post-training, fault-tolerance libraries, integrable open-source repos, and implications for the D-PoDL project (miners train tiny transformer on AG News with Ray Train DDP on LAN; checkpoints to IPFS; Ethereum ModelRegistry). Every claim is dated. "[BG]" = background, pre-2026. "[2026]" = 2026 development. "[CLAIM]" = self-reported / marketing / not independently verified.

Method note: GitHub API was blocked in this session, so star counts come from fetching GitHub HTML pages (rounded numbers shown on the page) and release dates come from the PyPI JSON API (queried 2026-11-05). Several secondary sources (crypto blogs, AI-generated paper summaries) were consulted only for leads; primary sources are cited wherever possible.

---

## 1. Algorithms and their current status/results (DiLoCo family, DeMo/DisTrO, SparseLoCo, MuLoCo, Decoupled DiLoCo, Protocol Models, SWARM, 2026 newcomers)

### Takeaway
By late 2026 the DiLoCo family (local inner steps + infrequent compressed pseudo-gradient sync) is the de-facto standard for internet data-parallel pre-training; compression stacks now reach >100x on top of DiLoCo's ~H-fold step reduction (Covenant-72B: >146x compression, 94.5% compute utilization at 72B on 110 Mb/s uplinks), and DeepMind's April 2026 Decoupled DiLoCo removes the lock-step barrier (asynchronous, quorum-based, token-weighted merging). The parallel track for models too big for one node is pipeline/model-parallel over the internet with compressed activations (Pluralis Protocol Models / Subspace Networks, ~100x activation compression), now demonstrated on an 8.6B permissionless run in 2026.

### Cited Findings

**DiLoCo core and scaling (background)**
- [BG, Mar 2025] "Scaling Laws for DiLoCo" (Charles et al., Google; arXiv 2503.09799, NeurIPS 2025): fitted scaling laws for models 35M-2.4B; at 10B scale DiLoCo outperformed data-parallel as predicted while reducing total communication by >100x; also reports larger optimal batch sizes and better downstream generalization — [arXiv 2503.09799](https://arxiv.org/abs/2503.09799); [Google Research page](https://research.google/pubs/communication-efficient-language-model-training-scales-reliably-and-robustly-scaling-laws-for-diloco/)
- [BG, Jan 2025] Streaming DiLoCo (arXiv 2501.18512): syncs parameter subsets in sequence, overlaps communication with compute, quantizes exchanged data; on a 1B model matches well-tuned data-parallel with ">400x less bandwidth" (abstract: "two orders of magnitude") — [arXiv 2501.18512](https://arxiv.org/abs/2501.18512)
- [BG, Dec 2025] Epoch AI analysis: DiLoCo allows up to ~500 inner steps (~500x bandwidth reduction) with small performance loss; scaling DiLoCo 1->8 nodes costs ~1.5x compute; naive extrapolation to 10,000 nodes ~6x; 8/4-bit quantization gives 2-4x; Streaming DiLoCo + 4-bit ~100x vs naive DP; with 10-minute syncs at 60 Mbps and fp32 gradients, naive DP caps model size at ~600M params — [Epoch AI, 2025-12-29](https://epoch.ai/gradient-updates/how-far-can-decentralized-training-over-the-internet-scale)

**Decoupled DiLoCo [2026]**
- [2026-04-23] "Decoupled DiLoCo for Resilient Distributed Pre-training" (Douillard, Rush, ... Ranzato, Jeff Dean; arXiv 2604.21428): splits compute into independent "learners" that run inner steps and asynchronously send parameter fragments to a central synchronizer, which uses a minimum quorum, adaptive grace window, and dynamic token-weighted merging to route around failed/straggling learners; reports "strictly zero global downtime" in simulations of "millions of simulated chips" and competitive quality on text and vision, dense and MoE — [arXiv 2604.21428](https://arxiv.org/abs/2604.21428)
- [2026-04] Secondary coverage reports 88% goodput vs 27% for standard data-parallel under high failure rates (simulated 1.2M chips) and a 12B production-scale training run across four U.S. regions; DeepMind blog says real Gemma 4 experiments matched conventional training benchmarks — [MarkTechPost summary via search snippet](https://www.marktechpost.com/2026/04/23/google-deepmind-introduces-decoupled-diloco-an-asynchronous-training-architecture-achieving-88-goodput-under-high-hardware-failure-rates/); [DeepMind blog mirror](https://hn.jakechampion.name/reader/https://deepmind.google/blog/decoupled-diloco/). (Note: the MarkTechPost page returned 403 to direct fetch; numbers from search-result summary only.)
- Note: Decoupled DiLoCo targets datacenter-to-datacenter ("compute islands") with a trusted central syncer, not untrusted peers — [arXiv 2604.21428](https://arxiv.org/abs/2604.21428)

**SparseLoCo (Templar/Covenant + Mila)**
- [BG, Aug 2025; NeurIPS 2025] SparseLoCo (Sarfi, Thérien, Lidin, Belilovsky; arXiv 2508.15706; later retitled "Overcoming the Communication-Performance Tradeoff in LLM Pretraining"): Top-k sparsification (97-99% sparsity) + 2-bit quantization + error feedback, with the error-feedback accumulator replacing DiLoCo's global outer momentum; outperforms DiLoCo and DeMo across 178M-2B dense and a 645M-A273M MoE; sparse aggregation can beat dense aggregation; 2-bit quantization negligible loss degradation — [arXiv 2508.15706](https://arxiv.org/abs/2508.15706); [NeurIPS 2025 listing](https://neurips.cc/virtual/2025/124278)
- [2026-03] Production config in Covenant-72B: chunk-wise Top-k (chunk 4096, k=64), 2-bit values, >146x compression vs dense, H=30 inner AdamW steps, error-feedback decay 0.95, outer LR 1 -> 0.65; ~70 s comms per 20-min round => ~94.5% compute utilization (vs INTELLECT-1 ~82.1%, SparseLoCo 8B paper ~95.7%) — [Covenant-72B paper, arXiv 2603.08163v2](https://arxiv.org/html/2603.08163v2)

**MuLoCo (Muon inside DiLoCo)**
- [BG, May 2025; ICML 2026 presentation] MuLoCo (Thérien, Huang, Rish, Belilovsky; arXiv 2505.23725): Muon as the *inner* optimizer (outer stays Nesterov SGD); "significantly outperforms DiLoCo while communicating 8x less", identical memory; with error feedback the delta compresses to 2 bits; tested 150M-3.1B. (Correction to the brief: Muon is inner, not outer.) — [arXiv 2505.23725](https://arxiv.org/html/2505.23725v2); [ICML 2026 slides](https://icml.cc/media/icml-2026/Slides/64378.pdf)

**DeMo / DisTrO (Nous)**
- [BG, Nov 2024; peer-reviewed ICLR 2026] DeMo (Peng, Quesnelle, Kingma; arXiv 2411.19870): drops gradient all-reduce, keeps momentum local, synchronizes only fast-moving momentum components (DCT-based extraction); ICLR 2026 version reports up to 85x less data per GPU than AdamW-DDP at 300M and 1B scale — [ICLR 2026 proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/17790fc9b4828206f99a0dea35da3657-Abstract-Conference.html); [arXiv 2411.19870](https://arxiv.org/abs/2411.19870)
- [BG, Feb 2025] FlexDeMo (arXiv 2502.06728) argues DeMo's gather step scales poorly with accelerator count; combines intra-node FSDP with decoupled momentum — [arXiv 2502.06728](https://arxiv.org/pdf/2502.06728v3)
- [BG] Psyche uses DisTrO (successor to DeMo); Nous claims "several orders of magnitude" less data transfer but gives no specific figure [CLAIM] — [Nous "Next Phase of Psyche", 2025-09-29](https://nousresearch.com/the-next-phase-of-psyche)

**Pipeline/model-parallel over the internet (Pluralis)**
- [BG, Jun 2025; NeurIPS 2025] "Protocol Models: Scaling Decentralized Training with Communication-Efficient Model Parallelism" (arXiv 2506.01260) introduces Subspace Networks: constrains activations at stage boundaries to a low-rank subspace; Pluralis states ~100x inter-stage compression — [Pluralis Agora docs](https://pluralis.ai/docs/); [Epoch AI](https://epoch.ai/gradient-updates/how-far-can-decentralized-training-over-the-internet-scale)
- [2026] Agora stack: data + pipeline parallel, one stage per device, multiple replicas per stage so peers can join/leave; AsyncMesh replaces per-step exact gradient AllReduce with asynchronous sparse parameter averaging between same-stage peers; SPARTA async sparse averaging introduced for Pluralis-8B; SWARM (ICML 2023) is the basis for stochastic peer-to-peer routing — [Pluralis Agora docs](https://pluralis.ai/docs/)
- [2026, NeurIPS 2026] "Unextractable Protocol Models: Collaborative Training and Inference without Weight Materialization" — no participant holds full weights (Pluralis listing; not read in full) — [Pluralis site via search](https://pluralis.ai/)

**DiLoCoX (0G Labs / China Mobile)**
- [BG, Jun 2025] DiLoCoX (arXiv 2506.21263): DiLoCo + pipeline parallel + dual optimizer policy + one-step-delay overlap + adaptive gradient compression; claims pre-training a 107B model over 1 Gbps; reported 357x throughput vs AllReduce (3,728 vs 10.4 tokens/s on Qwen1.5-107B) — ambiguous metric — [arXiv 2506.21263](https://arxiv.org/abs/2506.21263); [Douillard on X](https://x.com/Ar_Douillard/status/1938550098683723866). This was a *decentralized cluster* (A800 40GB clusters linked at 1 Gbps), not permissionless.

**Governance/simulation evidence [2026]**
- [2026-05-28] Rahman (MIRI), "Does Distributed Training Undermine Compute Governance?" (arXiv 2605.29359): simulator raised its default compression from 16x to 150x after Covenant-72B; at 100 Mbps distributed training costs ~3x more than centralized at 1e25 FLOP; latency has no significant effect (transmission dominates RTT); modeled 1e25 FLOP over US-average links with 34 nodes x 16 GH200 for ~$30.7M (simulation, not a run) — [arXiv 2605.29359](https://arxiv.org/html/2605.29359)

### Inferences
- The algorithmic bottleneck has shifted from "can we train over the internet?" to "can we verify/incentivize untrusted contributions and handle churn?" Compression is effectively solved for data-parallel at 10B-100B scale given each peer can hold the full model.
- For peers that cannot hold the full model (consumer GPUs), pipeline-parallel with activation compression (Pluralis) is the only demonstrated route; it is more complex and less mature than DiLoCo.
- Decoupled DiLoCo's quorum/grace-window/token-weighted merge is conceptually very close to a blockchain "block": a syncer accepts whichever contributions arrived by a deadline and weights them — a natural fit for D-PoDL's block model, but it assumes honest learners.

### Gaps
- Exact Decoupled DiLoCo bandwidth figures, 12B-run specifics and whether code is released were not verifiable (primary PDF not read; MarkTechPost 403). No open-source Decoupled DiLoCo implementation found.
- No independent replication found of DisTrO's production compression ratio.
- I did not find a distinct "2026 newcomer" algorithm beyond Decoupled DiLoCo, AsyncMesh/SPARTA (Pluralis) and MuLoCo's ICML 2026 presentation; a broader arXiv sweep might find more.

---

## 2. Landmark runs and their numbers (permissionless vs whitelisted)

### Takeaway
2026 delivered the first large *permissionless* pre-training runs: Covenant-72B (Templar, Bittensor SN3; completed ~2026-03-10; 72.7B params, ~1.1T tokens, >=70 unique peers each with >=8xB200, MMLU 67.1 vs LLaMA-2-70B 65.6) and Pluralis-8B (Agora; May 2026; 8.6B params, 500B tokens, 330 mostly-consumer nodes, 40 days, 63% of centralized H100 efficiency). But the field is also consolidating away from decentralization: Templar's training protocol is now inactive, Covenant left Bittensor (Apr 2026), Gensyn paused RL Swarm, and Prime Intellect's flagship INTELLECT-3 (Nov/Dec 2025) was trained on a centralized 512xH200 cluster. Decentralized runs remain ~1,000x below frontier compute.

### Cited Findings

**Templar / Covenant-72B [2026]**
- [2026-03, arXiv 2603.08163v2 revised 2026-03-10] Covenant-72B: 72,747,327,488 params dense, 80 layers, width 8192; ~1.09T DCLM tokens + ~14.2B annealing tokens; permissionless; >=70 unique peers (lower bound), avg 16.9 contributing per round (cap 20), 24.4 active per step; each peer >=8x B200 using dynamic FSDP; per-node limit 500 Mb/s down / 110 Mb/s up; SparseLoCo >146x compression; 94.5% compute utilization — [arXiv 2603.08163v2](https://arxiv.org/html/2603.08163v2)
- Benchmarks (0-shot) Covenant-72B vs K2-65B vs LLaMA-2-70B: ARC-C 56.8/53.8/57.4; ARC-E 80.9/76.0/79.6; MMLU 67.1/65.5/65.6; HellaSwag 80.6/82.9/84.3; WinoGrande 75.9/76.4/80.4 (baselines used 1.4T and 2T tokens). Covenant-72B-Chat (~14.8B SFT tokens): GSM8K 63.9 (K2-Chat 79.0), IFEval 64.7, MATH 26.3 — [arXiv 2603.08163v2](https://arxiv.org/html/2603.08163v2)
- Gauntlet incentive/validation: validator on Bittensor SN3 scores each pseudo-gradient by LossScore (loss change on a small batch); scores on assigned vs unassigned data (better on random than assigned => negative score, anti-copying); OpenSkill ratings smooth noise; liveness/sync checks; pseudo-gradients normalized to median norm so no peer dominates; submissions stored in peers' Cloudflare R2 buckets — [arXiv 2603.08163v2](https://arxiv.org/html/2603.08163v2)
- Compute: 4.8e23 FLOP; MIRI calls it the largest published DiLoCo-based run — [arXiv 2605.29359](https://arxiv.org/html/2605.29359). Epoch measured Templar throughput ~9e17 FLOP/s (~300x smaller than frontier data centers' ~3e20) — [Epoch AI, 2025-12-29](https://epoch.ai/gradient-updates/how-far-can-decentralized-training-over-the-internet-scale)
- Weights: Apache-2.0 on Hugging Face — [HF model card](https://huggingface.co/1Covenant/Covenant-72B/blob/main/README.md). Note mirror cards list differing intermediate checkpoints (e.g., MMLU 61.09 at 1T tokens) — check which checkpoint a number refers to.
- [2026, current] Templar repo README: "Templar's decentralized training protocol is not currently active, but may return in the future"; Subnet 3 now runs "Crusades", an MFU-optimization competition — [one-covenant/templar](https://github.com/one-covenant/templar)
- [2026-04-10] Covenant AI publicly withdrew from Bittensor citing governance concerns (secondary/crypto press; details disputed) — [FalconX](https://www.falconx.io/newsroom/state-of-bittensor-subnet-adoption-trends-network-mechanics-and-covenants-departure); [ownyourmind.ai](https://ownyourmind.ai/tokenomics/templar-bittensor-covenant-exit/)

**Pluralis [2025-2026]**
- [BG, Sep 2025] Node0-7.5B: 36.6B tokens; predecessor to Agora using Subspace Networks — [Pluralis docs](https://pluralis.ai/docs/)
- [2026-07-14, arXiv 2607.13332] "Agora: Collective and Permissionless Internet-Scale Pretraining of LLMs": Pluralis-8B = 8.6B params, 500B FineWeb-Edu tokens, 40 days, 330 contributor nodes (predominantly consumer GPUs on internet connections, churning), ~170k tokens/s sustained, 4.2 tokens/TFLOP of pooled compute = 63% of a centralized H100 baseline, "converged to within a small margin" of centralized reference; permissionless; each participant holds one stage only — [arXiv 2607.13332](https://arxiv.org/abs/2607.13332)
- Discrepancy: Pluralis docs list Pluralis-8B (May 2026) at 531.8B tokens vs paper's 500B — [Pluralis docs](https://pluralis.ai/docs/)
- [2026-09] Pluralis-13B: 62.4B tokens; systems test of Metadata Store peer coordination and P2P microbatch routing — [Pluralis docs](https://pluralis.ai/docs/)
- [2026-09-29 to 12-01] Protocol NanoGPT speedrun competition; winners at CODEC-FM workshop, NeurIPS 2026 — [Pluralis Protocol NanoGPT](https://pluralis.ai/protocol-nanogpt/)

**Nous Research / Psyche**
- [BG, 2025-05-14] Psyche testnet launched with Consilience 40B pre-training (FineWeb, FineWeb-2, Stack v2; target 20T tokens); Nous called it "the largest distributed pre-training run ever" [CLAIM] — [Nous on X](https://x.com/NousResearch/status/1922744483571171605); [Import AI 413](https://jack-clark.net/2025/05/19/import-ai-413-40b-distributed-training-run-avoiding-the-one-true-answer-fallacy-of-ai-safety-google-releases-a-content-classification-model/)
- [BG, 2025-09-29] "Next Phase of Psyche": no tokens-completed or results for Consilience 40B published; pivot to ablations/recipe building, new data mix (FineWeb-Edu, FineWeb2-HQ, FinePDFs, DCLM, Stack-Edu, Nemotron-CC-Math), and SFT then RL via a "full trainer abstraction"; Hermes 4 to be trained on Seed-OSS-36B over Psyche — [Nous blog](https://nousresearch.com/the-next-phase-of-psyche)
- [late 2025, date conflicting] Hermes 4.3 36B: "first Hermes model trained in a decentralized manner over the internet using Psyche"; model card benchmarks Psyche vs centralized control, e.g., AIME24 71.9 (Psyche) vs 70.6 (centralized); secondary sources report 24 nodes and ~144k tokens/s average [not verified against primary blog] — [HF model card](https://huggingface.co/NousResearch/Hermes-4.3-36B). Note this was post-training on an existing base, not pre-training.
- Psyche participation is permissioned (secondary source says runs are permissioned, Solana programs on devnet); Nous's own pages do not state this — [ownyourmind.ai review](https://ownyourmind.ai/projects/nous-research/); [Nous blog](https://nousresearch.com/the-next-phase-of-psyche)
- Epoch places Consilience 40B in the 6e22-6e23 FLOP range — [Epoch AI](https://epoch.ai/gradient-updates/how-far-can-decentralized-training-over-the-internet-scale)

**Prime Intellect**
- [BG, late 2024] INTELLECT-1: 10B params, 1T tokens, ~6e22 FLOP; would score ~98 on Epoch Capabilities Index (~Qwen2.5-Coder 1.5B) — [Epoch AI](https://epoch.ai/gradient-updates/how-far-can-decentralized-training-over-the-internet-scale); ~82.1% compute utilization — [Covenant-72B paper](https://arxiv.org/html/2603.08163v2). Contributors were whitelisted.
- [BG, 2025-05-12] INTELLECT-2: 32B reasoning model via fully asynchronous RL across a "dynamic, heterogeneous swarm of permissionless compute contributors"; components PRIME-RL, TOPLOC (verifies untrusted inference workers), SHARDCAST (weight broadcast); improves on QwQ-32B — [arXiv 2505.07291](https://arxiv.org/abs/2505.07291). Epoch notes 800+ nodes — [Epoch AI](https://epoch.ai/gradient-updates/how-far-can-decentralized-training-over-the-internet-scale). Only rollouts were permissionless; training nodes were Prime Intellect's.
- [BG, 2025-11/12; arXiv 2512.16144 dated 2025-12-18] INTELLECT-3: 106B MoE (12B active), RL post-trained on GLM-4.5-Air-Base with prime-rl, 512 H200 across 64 nodes (centralized); environments from verifiers/Environments Hub (i3-math, i3-code, i3-science, i3-logic, deepdive, deepswe) all public; Apache-2.0 — [Prime Intellect blog](https://www.primeintellect.ai/blog/intellect-3); [arXiv 2512.16144](https://arxiv.org/abs/2512.16144v1); critique: [Implicator](https://www.implicator.ai/prime-intellects-intellect-3-open-source-ambition-meets-centralized-reality/)
- [2026-07-08] $130M Series A at ~$1B valuation (Radical Ventures; NVIDIA, Intel Capital, Dell); TechCrunch reports focus shifted from aggregating distributed compute to selling environments/training/eval/deployment to enterprises — [TechCrunch](https://techcrunch.com/2026/07/08/prime-intellect-raises-130m-series-a-to-help-enterprises-build-their-own-ai-agents/)
- [2026-10] Acquired Moondream (vision models) — [Prime Intellect on X](https://x.com/PrimeIntellect/status/2110081907358904392)
- No INTELLECT-4 or new decentralized Prime Intellect run found for 2026.

**Gensyn**
- [BG, 2025] RL Swarm testnet reportedly ~12,000 nodes (secondary, date unclear) — [bex.co](https://bex.co/blog/2026/05/05/gensyn-rl-swarm-decentralized-ml-training-ethglobal)
- [2026] Gensyn docs: RL Swarm listed under "Testnet Archive (Legacy)", "no longer actively maintained"; "No official swarms are running at this time" — [Gensyn docs](https://docs.gensyn.ai/)
- [2026-04-22, secondary] Gensyn mainnet launched with Delphi (AI prediction/information market) as first app; training mainnet not launched — [Startup Fortune](https://startupfortune.com/gensyn-launches-its-mainnet-and-bets-that-ai-agents-can-fix-the-broken-economics-of-decentralized-compute/); [hoge.gg](https://hoge.gg/de/gensyn-2026-delphi-ki-training-pausiert/)

**0G Labs**
- [BG, Jul 2025] DiLoCoX-107B over 1 Gbps with China Mobile (decentralized clusters, not permissionless) — [arXiv 2506.21263](https://arxiv.org/abs/2506.21263); [0G blog](https://0g.ai/blog/dilocox-107b-decentralized-ai-training)
- [2026-03-24] Press release: 0G "begun publicly retraining DiLoCoX-107B" with commitment to open-source; positions it as "48% larger" than Covenant-72B; 95% cost reduction claim unverified [CLAIM] — [GlobeNewswire](https://www.globenewswire.com/news-release/2026/03/24/3261890/0/en/0G-Labs-Decentralized-AI-Model.html). No released weights/benchmarks found.

**Trend context**
- [2025-12-29] Decentralized training compute grew ~20x/yr (600,000x since 2020) vs frontier ~5x/yr; largest runs ~1,000x below frontier (e.g., Grok 4); Epoch thinks decentralized developers unlikely to amass frontier compute this decade; open-weight models likely beneficiary — [Epoch AI](https://epoch.ai/gradient-updates/how-far-can-decentralized-training-over-the-internet-scale)

### Inferences
- "Permissionless" in 2026 practice means permissionless *for well-capitalized peers*: Covenant required >=8xB200 per peer and capped contributors at 20 per round. Pluralis-8B is the only large run where consumer GPUs dominated.
- The three most-cited decentralized-training orgs all retreated from live public networks in 2026 (Templar protocol inactive, Gensyn swarms paused, Prime Intellect pivoted to enterprise RL stack); Pluralis is the most active live network. Business/token-economics, not algorithms, appear to be the binding constraint.
- The most transferable artifact for D-PoDL is Gauntlet's loss-delta scoring + assigned/unassigned-data anti-copy test: a concrete, published "proof of useful training" that is cheaper than recomputation.

### Gaps
- Consilience 40B final token count and outcome never published (as of sources found); unclear if the run was stopped.
- Covenant-72B wall-clock duration and total cost not found in the portion of the paper read.
- 0G's 2026 retrain status/results unknown.
- No reliable 2026 figures on Gensyn's on-chain verification (Verde) in production.

---

## 3. Decentralized RL / post-training

### Takeaway
RL post-training is the most practical decentralized workload because rollout generation (inference) is embarrassingly parallel, needs only periodic weight broadcast (which can be delta-compressed ~110x), and rewards are verifiable; the training step can stay centralized. Demonstrations span INTELLECT-2 (2025, permissionless rollouts), Gensyn SAPO (2025, swarm sampling), Hermes 4.3 on Psyche (late 2025, post-training) and Pluralis' July 2026 run where 14 consumer Macs in 4 countries generated all rollouts for an 8.3B MoE (pass@1 29% -> 63%).

### Cited Findings
- [BG, 2025-05] INTELLECT-2 architecture: PRIME-RL async RL, TOPLOC validators check rollouts from untrusted inference workers, SHARDCAST broadcasts policy weights; permissionless rollout contributors — [arXiv 2505.07291](https://arxiv.org/abs/2505.07291)
- [BG, Jan 2025] TOPLOC (arXiv 2501.16007): locality-sensitive hashing commitments over inference activations to verify an untrusted provider used the claimed model; low overhead — [arXiv 2501.16007](https://arxiv.org/html/2501.16007v1). Limitation: addresses model substitution, not verifiable training — [HN discussion](https://news.ycombinator.com/item?id=43958898)
- [BG, Sep 2025] Gensyn SAPO (Swarm sAmpling Policy Optimization): fully decentralized, asynchronous RL post-training where nodes share rollouts; Gensyn self-reports ~94% improvement in cumulative reward vs training in silo [CLAIM, self-reported] — [Gensyn research](https://www.gensyn.ai/research/sapo-efficient-lm-post-training-with-collective-rl)
- [2026-07] Pluralis "RL Post-Training on Macs" (Erfan Miahi): LFM2.5-8B-A1B (8.3B MoE); 14 Macs (Paris x2, Zurich x7, Dublin x4, Toronto x1) generate int8 rollouts on Apple MLX; one B200 trains in bf16 with Megatron; ~100 Mbps home internet; weight updates delta-compressed to median 82 MB per version vs 9 GB checkpoint (~110x); Cloudflare R2 storage, outbound HTTPS only; workers can join/leave/crash without stalling; PaperSearchQA held-out pass@1 29% -> 63%, pass@8 60% -> 83% by weight version 100 (optimizer step 444); 14 Macs saturated one B200; code: Stoa — [Pluralis blog](https://pluralis.ai/blog/rl-post-training-on-macs/); [github.com/PluralisResearch/stoa](https://github.com/PluralisResearch/stoa)
- [2026] prime-rl v0.10.0 + verifiers v0.4.0 made IPO the default loss, designed to stabilize async training when trainer and inference engine assign different token probabilities (off-policy mismatch) — [Digg summary](https://digg.com/ai/2mw3h184); [AlphaSignal](https://alphasignal.ai/news/prime-intellect-s-ipo-stops-ai-training-crashes-that-derailed-long-runs)
- [2026] prime-rl: "Agentic RL Training at Scale", fully async, scales to 1000+ GPUs, FSDP2 trainer + vLLM inference, Slurm multi-node, integrates verifiers environments; ~2.2k stars; Apache-2.0; no explicit decentralized mode advertised on README — [GitHub prime-rl](https://github.com/PrimeIntellect-ai/prime-rl)
- [2026-11-03] verifiers 0.4.1 released on PyPI (environment/reward library used by Environments Hub) — [PyPI verifiers](https://pypi.org/project/verifiers/)
- [BG, 2025-11] INTELLECT-3 environments and evals publicly available on Environments Hub — [Prime Intellect blog](https://www.primeintellect.ai/blog/intellect-3)
- [BG, 2025-09-29] Psyche roadmap explicitly moving to SFT and RL via "full trainer abstraction" — [Nous blog](https://nousresearch.com/the-next-phase-of-psyche)

### Inferences
- RL rollout work maps cleanly onto a mining model: a "task" = (policy version hash on IPFS, environment ID, seed); the "proof" = rollouts + reward + a TOPLOC-style activation commitment; validators re-run a random sample. Rewards are verifiable for math/code environments from verifiers/Environments Hub.
- Off-policy staleness is the core technical risk for async decentralized RL; IPO-style losses (prime-rl 0.10) and bounded staleness windows are the current mitigations.
- Consumer hardware (Macs, gaming GPUs) is genuinely usable for rollouts, unlike for pre-training of >1B models.

### Gaps
- No 2026 paper found that solves verification of untrusted *training* updates in RL (TOPLOC covers inference only).
- Stoa repository stars/license/maturity not checked (GitHub API blocked).
- No public numbers found for how many permissionless rollout workers prime-rl supports in 2026, or whether Prime Intellect still runs a public decentralized RL network.

---

## 4. Fault tolerance and elastic training libraries (torchft, Hivemind, Petals, PCCL/prime, iroh/libp2p, Ray)

### Takeaway
torchft (now under meta-pytorch, releases weekly through Nov 2026) is the most actively maintained PyTorch-native option and already ships LocalSGD/DiLoCo/Streaming DiLoCo with a Lighthouse quorum server, but it is designed for datacenters, not untrusted WAN peers. PCCL (Prime Intellect, MIT) is the WAN-oriented fault-tolerant collective library but has had no PyPI release since May 2025. Hivemind is in maintenance mode (last release Jan 2026); Petals is effectively dormant (last release Nov 2023).

### Cited Findings
- [2026-11-03] torchft 0.3.1 on PyPI; torchft-nightly 2026.11.4 (2026-11-04); repo moved to github.com/meta-pytorch/torchft — [PyPI torchft](https://pypi.org/project/torchft/)
- [2026] torchft: "Fault tolerance for PyTorch (HSDP, LocalSGD, DiLoCo, Streaming DiLoCo)"; 551 stars; BSD-3-Clause; fault-tolerant DDP/HSDP, reinitializable ProcessGroups, per-step heartbeats, live checkpoint recovery from healthy peers, Lighthouse server for step-level membership changes, parameter-server example; LocalSGD/DiLoCo "currently experimental"; requires PyTorch 2.7+; no WAN guidance — [GitHub meta-pytorch/torchft](https://github.com/meta-pytorch/torchft)
- [BG, 2025-05-20] PCCL technical report (arXiv 2505.14065): fault-tolerant collectives over public internet; dynamic peer join, failure recovery (abort + retry with reduced membership), bit-identical shared state under churn; multiple TCP connections reach up to 45 Gbit/s across Europe and 25 Gbit/s NA<->EU; C99 API, C++ internals, Python bindings compatible with PyTorch/FSDP; MIT — [arXiv 2505.14065](https://arxiv.org/abs/2505.14065); [pccl.primeintellect.ai](https://pccl.primeintellect.ai/)
- [2025-05-21] pypccl 1.0.0 is the latest PyPI release (no 2026 releases) — [PyPI pypccl](https://pypi.org/project/pypccl/)
- [2026-01-03] hivemind 1.1.12 latest PyPI release; MIT — [PyPI hivemind](https://pypi.org/project/hivemind/); [GitHub learning-at-home/hivemind](https://github.com/learning-at-home/hivemind)
- [BG, 2023-11-20] petals 2.2.0.post1 is still the latest PyPI release (no releases in ~3 years) — [PyPI petals](https://pypi.org/project/petals/)
- [2026-11-04] Prime Intellect "prime" CLI 0.19.4 on PyPI (platform CLI, not the old `prime` training framework) — [PyPI prime](https://pypi.org/project/prime/)
- [2026-10-22] iroh (n0 QUIC P2P transport) 1.2.0 Python package on PyPI — [PyPI iroh](https://pypi.org/project/iroh/); [iroh.computer](https://iroh.computer)
- [2026-11-04] ray 2.60.0 on PyPI, Apache-2.0 — [PyPI ray](https://pypi.org/project/ray/)
- [2026] Psyche (Rust, P2P networking, Solana coordination) repo PsycheFoundation/nousnet ~977 stars, Apache-2.0, "distributed training of transformer-based AI models over the internet ... collaboration between untrusted parties" — [GitHub PsycheFoundation](https://github.com/PsycheFoundation/psyche)
- [2026] Covenant/Pluralis both used Cloudflare R2 object storage (HTTPS) as the exchange medium for pseudo-gradients / weight deltas instead of P2P transports — [Covenant-72B](https://arxiv.org/html/2603.08163v2); [Pluralis blog](https://pluralis.ai/blog/rl-post-training-on-macs/)

### Inferences
- Production 2026 systems favor object-storage-mediated async exchange (R2/S3) over live all-reduce; this matches D-PoDL's IPFS checkpoint model, but IPFS's latency/pinning reliability would need to be checked against R2-like throughput for ~hundreds-of-MB deltas per round.
- Ray Train DDP on a LAN is the wrong primitive for internet training; torchft's DiLoCo (within trusted clusters) or a custom DiLoCo outer loop exchanging compressed pseudo-gradients via storage is the realistic replacement.

### Gaps
- Ray-specific 2025-2026 changes relevant to WAN/elastic training were not researched in depth (only latest version confirmed).
- Hivemind GitHub activity (commits in 2026) not confirmed beyond the Jan 2026 release.
- py-libp2p maturity not checked.

---

## 5. Actively maintained, integrable repos (URLs, stars, last release, license)

### Takeaway
For a Python/PyTorch project, the best-maintained integrable pieces (Nov 2026) are torchft (DiLoCo/Streaming DiLoCo, BSD-3), prime-rl + verifiers (async RL + verifiable environments, Apache-2.0, releases this week), and Templar's SparseLoCo/Gauntlet code (MIT; protocol inactive but code is the only open, battle-tested 72B permissionless incentive implementation). Pluralis Stoa is the most relevant new code for consumer-device RL rollouts.

### Cited Findings (stars as shown on GitHub page; release dates from PyPI on 2026-11-05)
| Repo | URL | Stars | Latest release | License | Status / fit |
|---|---|---|---|---|---|
| torchft | https://github.com/meta-pytorch/torchft | 551 | 0.3.1, 2026-11-03 | BSD-3 | Active; DiLoCo/Streaming DiLoCo experimental; datacenter-oriented — [GitHub](https://github.com/meta-pytorch/torchft), [PyPI](https://pypi.org/project/torchft/) |
| prime-rl | https://github.com/PrimeIntellect-ai/prime-rl | ~2.2k | v0.10.0 (date not visible) | Apache-2.0 | Active; async RL, FSDP2+vLLM — [GitHub](https://github.com/PrimeIntellect-ai/prime-rl) |
| verifiers | https://github.com/PrimeIntellect-ai/verifiers | not checked | 0.4.1, 2026-11-03 | not stated on PyPI | Active; RL environments/rewards — [PyPI](https://pypi.org/project/verifiers/) |
| PCCL | https://github.com/PrimeIntellect-ai/pccl | not checked | pypccl 1.0.0, 2025-05-21 | MIT | Stale on PyPI since 2025 — [PyPI](https://pypi.org/project/pypccl/), [arXiv](https://arxiv.org/abs/2505.14065) |
| Templar (SparseLoCo, Gauntlet) | https://github.com/one-covenant/templar | 163 | none visible | MIT | Protocol "not currently active"; SN3 now Crusades — [GitHub](https://github.com/one-covenant/templar) |
| Psyche | https://github.com/PsycheFoundation/psyche (shows as nousnet) | 977 | none visible | Apache-2.0 | Rust + Solana; heavy to integrate in Python — [GitHub](https://github.com/PsycheFoundation/psyche) |
| DisTrO | https://github.com/NousResearch/DisTrO | not checked | — | — | Mostly docs/pointers — [GitHub](https://github.com/NousResearch/DisTrO) |
| Hivemind | https://github.com/learning-at-home/hivemind | not checked | 1.1.12, 2026-01-03 | MIT | Maintenance — [PyPI](https://pypi.org/project/hivemind/) |
| Petals | https://github.com/bigscience-workshop/petals | not checked | 2.2.0.post1, 2023-11-20 | — | Dormant — [PyPI](https://pypi.org/project/petals/) |
| Pluralis Stoa | https://github.com/PluralisResearch/stoa | not checked | — | not checked | New (Jul 2026); Mac/consumer RL rollouts — [Pluralis blog](https://pluralis.ai/blog/rl-post-training-on-macs/) |
| Pluralis Agora test | https://github.com/PluralisResearch/agora-test | not checked | — | not stated | Agora client — [Pluralis docs](https://pluralis.ai/docs/) |
| Gensyn RL Swarm / GenRL | https://github.com/gensyn-ai | not checked | gensyn-genrl 0.3.0, 2025-11-06 | — | Legacy / not maintained — [Gensyn docs](https://docs.gensyn.ai/), [PyPI](https://pypi.org/project/gensyn-genrl/) |
| iroh (P2P QUIC) | https://github.com/n0-computer/iroh | not checked | Python 1.2.0, 2026-10-22 | — | Active transport — [PyPI](https://pypi.org/project/iroh/) |
| Ray | https://github.com/ray-project/ray | not checked | 2.60.0, 2026-11-04 | Apache-2.0 | Active — [PyPI](https://pypi.org/project/ray/) |
| Covenant-72B weights | https://huggingface.co/1Covenant/Covenant-72B | — | 2026-03 | Apache-2.0 | Model + checkpoints — [HF](https://huggingface.co/1Covenant/Covenant-72B/blob/main/README.md) |
| INTELLECT-3 weights | https://huggingface.co/PrimeIntellect/INTELLECT-3 | — | 2025-11 | Apache-2.0 | Model — [HF](https://huggingface.co/PrimeIntellect/INTELLECT-3) |

### Inferences
- Lowest-effort integration path for D-PoDL: (a) replace Ray DDP with a DiLoCo outer loop (torchft's implementation or a ~200-line custom one), (b) port SparseLoCo compression + Gauntlet LossScore from Templar (MIT) as the proof-of-useful-work verifier, (c) keep IPFS as the pseudo-gradient/checkpoint store and Ethereum ModelRegistry as the round ledger. For RL, embed verifiers environments and adopt Stoa/prime-rl's rollout-worker pattern.
- Psyche is Rust/Solana and would be a rewrite rather than a merge.

### Gaps
- Star counts for several repos, and exact release dates for prime-rl, Templar, Psyche, Stoa could not be retrieved (GitHub API blocked; HTML pages hid release info). Licenses for verifiers and Stoa not confirmed.

---

## 6. Implications for the D-PoDL project's design

### Takeaway
What changed since the project stalled (Sep 2025): permissionless collaborative training of *one* shared model with on-chain incentives and loss-based contribution scoring is now proven at 72B (Covenant, Mar 2026) and on consumer GPUs at 8.6B (Pluralis, Jul 2026), and decentralized RL rollouts on consumer hardware are proven (Pluralis Macs, Jul 2026). Per-miner independent training of separate architectures on AG News has no analogue in any successful 2026 system; the evidence favors redesigning around (a) DiLoCo/SparseLoCo-style collaborative training of a single model with Gauntlet-like scoring, or (b) verifiable RL rollout mining, which fits heterogeneous/consumer miners best.

### Cited Findings
- Covenant's Gauntlet demonstrates on-chain-coordinated, loss-delta-scored acceptance of untrusted pseudo-gradients with anti-copy checks and median-norm normalization — [arXiv 2603.08163v2](https://arxiv.org/html/2603.08163v2)
- Communication budget that worked at 72B: ~70 s per 20-minute round on 110 Mb/s uplink, >146x compression — [arXiv 2603.08163v2](https://arxiv.org/html/2603.08163v2)
- Consumer-GPU pre-training needs model parallelism (one stage per device) and achieved 63% of centralized H100 efficiency at 8.6B — [arXiv 2607.13332](https://arxiv.org/abs/2607.13332)
- Decentralized RL: one B200 trainer saturated by 14 Macs on home internet; deltas 82 MB vs 9 GB — [Pluralis blog](https://pluralis.ai/blog/rl-post-training-on-macs/)
- Decoupled DiLoCo's quorum + grace window + token-weighted merge provides a template for block-time-bounded aggregation — [arXiv 2604.21428](https://arxiv.org/abs/2604.21428)
- Sustainability risk: Templar protocol inactive and Covenant exited Bittensor (Apr 2026); Gensyn swarms paused; Prime Intellect pivoted to enterprise — [one-covenant/templar](https://github.com/one-covenant/templar); [Gensyn docs](https://docs.gensyn.ai/); [TechCrunch](https://techcrunch.com/2026/07/08/prime-intellect-raises-130m-series-a-to-help-enterprises-build-their-own-ai-agents/)

### Inferences
- Concrete redesign A (collaborative pre-/fine-training): one global model per "epoch"; each block = one DiLoCo outer round; miners run H inner steps on assigned data shards, upload SparseLoCo-compressed pseudo-gradients to IPFS, post CID to ModelRegistry; validators compute LossScore on assigned vs unassigned batches, select top-k contributors, aggregate, publish new model CID; rewards proportional to score. This turns "Proof-of-Deep-Learning" into a verifiable contribution-to-shared-loss proof.
- Concrete redesign B (RL rollout mining): ModelRegistry publishes policy CID + environment set (verifiers); miners return rollouts with rewards + TOPLOC-style commitments; validators spot-check by recomputation; a trainer (initially trusted) consumes rollouts. Lowest hardware barrier, highest near-term viability.
- AG News + tiny transformer is fine as a CI/testnet workload, but credibility requires at least a ~100M-1B model on FineWeb-Edu-class data or a verifiers math/code RL task.
- Token-economics/governance, not algorithms, killed or paused several 2026 networks; D-PoDL's Ethereum registry design should budget for validator cost and anti-Sybil from the start.

### Gaps
- No public evidence that IPFS (vs Cloudflare R2/S3) has been used successfully as the exchange layer in a large 2026 run; throughput/pinning reliability unverified.
- No published, robust defense against colluding validators or gradient-poisoning at scale was found beyond Gauntlet's heuristics.
- Compute/storage cost for validator re-evaluation per round at small scale was not quantified in sources found.
