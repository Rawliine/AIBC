# Verifying contributions and securing collective training of one model on untrusted consumer GPUs (state as of 2026-11-05)

Scope notes:
- Research date is 2026-11-05. Every claim carries the date of its source.
- "Vendor claim" means self-reported by the project, with no independent replication.
- "Estimate" means my own arithmetic or judgement, not sourced.
- This file builds on two earlier notes and does not repeat their detail; read them alongside this one:
  - `research_notes/DPoDL revival research November 2026/verification.md` covers PoL attacks, Verde/RepOps, TOPLOC, Gauntlet, zkML, TEE.fail and OVIG.
  - `research_notes/DPoDL prior art and viability plan/prior_art_protocols.md` covers OPEN-1B, VISTA, PoTS, PoGO and Pearl.
- New primary-source work this session:
  - Full-text read of the Pluralis Agora report (arXiv 2607.13332) via pdftotext.
  - Shallow clones on 2026-11-05 of `PluralisResearch/agora` (last commit 2026-07-04), `PsycheFoundation/psyche` (last commit 2026-03-20, `0bdb13d`) and the BOINC wiki.
  - Full-text reads of SENTINEL (2603.03592), Backdoor Absorption (2607.06643) and Lu et al. (2312.00843).

---

## 1. Verification in pipeline / model-parallel training (SENTINEL, Pluralis Agora, SWARM, redundancy, audits, tolerance checks)

### Takeaway
As of Nov 2026, no permissionless consumer-GPU pipeline-parallel run has deployed Byzantine defenses:
- Pluralis's own Agora docs say adversarial-peer defense is "not yet implemented". Agora relies on admission control, a closed-source client-integrity hash, HuggingFace-account identity and revocable credentials.
- SWARM has no Byzantine mechanism at all.

The research menu is:
- (a) SENTINEL: cheap EMA statistical checks on inter-stage activations and gradients. No duplicate compute, roughly 80–100% F1, weak on some gradient attacks, no code.
- (b) Redundant or duplicated stage computation (Lu et al. ICML 2024; BOINC-style replication): about 2x on the replicated fraction.
- (c) Sampled re-execution by trusted auditors under calibrated cross-GPU tolerances (TAO, EuroSys 2026, 0.3% overhead on inference; OVIG, +14.3% for training replay).
- (d) Bitwise-reproducible replay (Gensyn OPEN-1B, several-fold GEMM slowdown).

A practical design layers (a) on everything, with (b) or (c) on a random sample.

### Cited Findings
**SENTINEL** (Pluralis; Dolatabadi, Ajanthan, Ramasinghe, …, Long), arXiv 2603.03592, v1 2026-03-03, 70 pp., CC BY 4.0 — [arXiv abs](https://arxiv.org/abs/2603.03592); details from [arXiv HTML](https://arxiv.org/html/2603.03592), read 2026-11-05:
- **Mechanism.** Dedicated "verifier nodes" sit between pipeline stages, and all inter-stage activations and gradients pass through them. Each verifier keeps per-stage exponential-moving-average (momentum) reference statistics and flags deviations. The authors say verifiers can run on CPU. In SWARM they extended existing trainer nodes to act as verifiers. It runs "without computation duplication."
- **Attacks evaluated:**
  - constants (zeros/ones), random values, scaling (α=−1);
  - random sign flips (1/10/30%), bias/noise addition;
  - delay (100-step stale values);
  - ALIE-style "invisible noise";
  - an adaptive attack that mimics the verifier's EMA;
  - mixed activation-plus-gradient attacks.
- **Results.** Most activation attacks give F1 = 100% on Llama-3-0.6B (C4). Bias addition gives 88%. **Some gradient attacks give 0% F1.** Mixed attacks give 86.7–89.5% F1.
- **Scale.** Runs went up to about 4B params on 176 workers, where F1 = 79.6% (precision 94.9%, recall 68.6%). Other runs: 0.6B on 128 and 256 workers, 1.2B on 64 workers, and MoE (Llama-4-0.4B, DeepSeek-V3-1B).
- **On detection.** The signal is dropped and the EMA is not updated. A deviation more than 100x above threshold triggers an immediate ban; otherwise a ban follows 5 violations, with the counter decaying after 100 clean steps. Backward passes use the stored gradient EMA.
- **Overhead.** O(m) per signal. **No measured throughput or bandwidth overhead is reported.**
- **Stated limitations and assumptions:**
  - an honest warm-up of about 1k steps, and honest first and last stages;
  - fewer than half the workers malicious per stage, with detection holding up to about 60% collusion;
  - manually tuned thresholds;
  - backdoor and membership-inference attacks not addressed;
  - DP-side (all-reduce) attacks out of scope, though a Krum/Bulyan swap gave 86.6% / 82.9% F1 on mixed attacks;
  - false positives under activation-delay attacks at 1.2B.
- **No code link.** SOTAVerified lists it as not independently reproduced — [sotaverified](https://sotaverified.org/papers/260303592).

**Pluralis Agora / Pluralis-8B**, arXiv 2607.13332, 2026-07-14; full text read 2026-11-05 — [arXiv PDF](https://arxiv.org/pdf/2607.13332):
- **Run.** 8.6B params, 500B FineWeb-Edu tokens, 40 days. 330 contributor nodes, "predominantly consumer GPUs", plus a small set of operator nodes. 669 joins and 607 departures. About 170k tokens/s, 4.2 tokens/TFLOP, 63% of a centralized H100 baseline's efficiency.
- **Fleet.** RTX 5090 and 4090 were 55% of nodes, L40S 22%, RTX 6000 Ada and RTX PRO 6000 23%. Admission floor: ≥24 GB VRAM, ≥80 GB RAM, ≥200 Mbit/s down, ≤80 ms latency. Ablations at 1B tolerate 10:1 heterogeneity, degrading when all-reduce participation drops below about 85%.
- **Trust model (§3.6.1 "Authorizer").** A single admission and trust authority (FastAPI + PostgreSQL + Redis) checks four things:
  - capability (RAM, VRAM, bandwidth, latency, allowed GPU list);
  - **integrity**: "verifies that a joining node runs a legitimate, unmodified build of the client rather than altered code, protecting the run against participants that might otherwise corrupt gradients or poison the shared model state";
  - reachability;
  - accountability: "every node authenticates before admission, so a participant that misbehaves can be identified and barred".
- **Stage assignment and credentials.** The Authorizer, not the contributor, assigns pipeline stages. It issues short-lived signed credentials that peers verify locally, and revocation works by not renewing them.
- **Health Monitor.** It reconciles DHT stage announcements with admission records and accepts loss and batch reports only from signed trainer nodes.
- **No Byzantine defense in the run.** The report's intro mentions UPMs as an *extension*. The only other UPM mention is the reference list; I found no statement that UPMs were active in the Pluralis-8B run.
- Agora docs: "Adversarial peers (roadmap)… It is **not yet implemented** in Agora today" — [Agora docs overview](https://pluralis.ai/docs/agora-system/overview/); same text in repo `docs/agora-system/overview.md` (cloned 2026-11-05).
- **Repo** [github.com/PluralisResearch/agora](https://github.com/PluralisResearch/agora): Apache-2.0, last commit 2026-07-04 ("finish-run"). The integrity check ships only as a compiled binary, `agora/src/agora/security/integrity_check.cpython-311-x86_64-linux-gnu.so`. Identity is a HuggingFace token ("doesn't need any read/write permissions as it will only be used for authorization"). Contributors need inbound port 49200 open.

**SWARM** (Ryabinin, Dettmers, Diskin, Borzunov; ICML 2023), arXiv 2301.11913:
- Full text grepped 2026-11-05. It has **no discussion of Byzantine or malicious peers, or verification**; it covers fault tolerance and stochastic routing only — [arXiv 2301.11913](https://arxiv.org/pdf/2301.11913).
- SENTINEL was layered onto SWARM and prevented the divergence seen without verification in a 128-worker preemptible run — [SENTINEL HTML](https://arxiv.org/html/2603.03592).

**Pipeline poisoning and the duplicated-block defense.** Lu, Dai, Tao, Yuan, Sun, Zhou, "Position: Exploring the Robustness of Pipeline-Parallelism-Based Decentralized Training", ICML 2024 (arXiv 2312.00843, Dec 2023) — [arXiv HTML](https://arxiv.org/html/2312.00843v1); [PMLR](https://proceedings.mlr.press/v235/lu24c.html); code [github.com/dcx001016/pipeline_attack](https://github.com/dcx001016/pipeline_attack):
- **Attack.** One malicious middle stage flips activation signs on the forward pass, or replaces backward gradients with N(0,1) noise. At a 0.7 attack rate, OPT-350M wikitext perplexity goes from 29.77 to 2,128.
- **Defense.**
  - Each stage holds a **redundant copy of the previous stage's layers** and checks consistency.
  - A "jumping connection" sends each stage's output two stages ahead, for knowledgeable attackers.
  - After an alert, a central server relays data and skip-layer bypasses the suspect stage.
- **Gaps in the evidence.** **No detection-rate, false-positive or overhead numbers** are given; the paper only says it needs "additional GPU storage". It assumes trusted first and last stages, a trusted server, and one malicious stage at a time.

**BTARD-SGD** (Gorbunov, Borzunov, Diskin, Ryabinin; ICML 2022 spotlight; arXiv 2106.11257) — [arXiv](https://arxiv.org/pdf/2106.11257); [ICML](https://icml.cc/virtual/2022/spotlight/17142):
- A Byzantine-tolerant all-reduce (Butterfly All-Reduce + CenteredClip) in which randomly chosen validators **recompute peers' gradients** to detect discrepancies. Its extra communication is independent of parameter count.
- It includes a Sybil heuristic.
- ALBERT-large on 64 machines with 31 Byzantine peers: all attackers banned within 100–150 steps.
- This is data-parallel, from the Hivemind/SWARM group. Details come from search snippets.

**Tolerance-based cross-GPU checking:**
- **TAO** (Yao, Su, Liao, Cheng, H. Zhang, X. Wang, Viswanath), arXiv 2510.16028 (v1 2025-10-15, v4 2026-06-06), **EuroSys 2026** pp. 1515–1532 — [arXiv](https://arxiv.org/abs/2510.16028):
  - Per-operator acceptance regions combine IEEE-754 worst-case bounds with **empirical percentile profiles calibrated across A100, H100, RTX 6000 and RTX 4090**.
  - Disputes use a Merkle-anchored dispute game that recursively splits the graph down to one operator, judged by the bound or by a small honest-majority vote.
  - **0.3% overhead on Qwen3-8B**, with unmodified vendor FP32 kernels. Empirical thresholds are 10²–10³x tighter than theoretical bounds. 0% success for bound-aware adversarial attacks. Deployed as a contract layer on the Holesky testnet.
  - It targets **inference** (model swap, quantization, graph rewrites). No code link.
- **OVIG** (same Viswanath group), arXiv 2606.21045 (2026-06/09): training replay with honest-replay-calibrated gradient-difference boundaries on heterogeneous hardware. +14.3% compute and 0% attack success on Qwen3. No code — [arXiv](https://arxiv.org/abs/2606.21045) (detail in the earlier verification.md).
- **OPEN-1B** (Gensyn, arXiv 2609.17380, 2026-09-15): bitwise-reproducible training across heterogeneous commodity hardware, where any single step can be replayed on one machine. Int8 QAT GEMMs run "several times slower" than bf16. A secondary source reports low audit coverage — [arXiv](https://arxiv.org/abs/2609.17380) (detail in prior_art_protocols.md).

**Activation fingerprinting.** TOPLOC v2 extended locality-sensitive activation hashing to *pipeline-parallel inference* (SYNTHETIC-2, 2025) — [Prime Intellect blog](https://www.primeintellect.ai/blog/synthetic-2). I found no paper applying TOPLOC-style fingerprints to *training-time* stage outputs or gradients.

**Redundancy cost baseline (BOINC wiki, cloned 2026-11-05)** — [BOINC Adaptive Replication](https://github.com/BOINC/boinc/wiki/Adaptive-Replication):
- Default replication spends "at least 50% of total CPU time… checking result validity".
- Adaptive replication targets "perhaps only 5% or 10%". A host is untrusted until it has 10 consecutive valid results for that app version, then trusted with probability 1−1/CV.
- **Homogeneous redundancy** compares replicas only within "numerical equivalence classes" (OS/CPU classes), so strict equality can be used — [BOINC Homogeneous Redundancy](https://github.com/BOINC/boinc/wiki/Homogeneous-Redundancy).

### Inferences
- **Threat surface in pipeline mode (inference).** If data-holding "trainer" nodes (Agora: CPU-only trainers that route microbatches) and the first and last stages are operator-run, consumer workers never choose data. Their attack surface is then (i) corrupting activations and gradients they emit, (ii) corrupting their stage weights or optimizer state during the DP all-reduce within a stage, (iii) laziness (returning cached or stale outputs), and (iv) exfiltration. SENTINEL covers (i) and partly (iii). Robust intra-stage all-reduce (CenteredClip, Krum, median-norm) covers (ii). Exfiltration is section 6.
- **Redundant stage assignment, estimate.** Sending a random fraction r of microbatches to two workers of the same stage and comparing outputs costs about r extra stage compute plus bandwidth.
  - With heterogeneous GPUs the comparison must be tolerance-based (TAO/OVIG-style profile per SKU pair), or limited to same-SKU pairs (BOINC homogeneous-redundancy analog).
  - Agora already keeps several DP replicas per stage, so pairing two of them is architecturally natural.
  - Detection probability for a worker cheating on k microbatches is 1−(1−r)^k. With r=5% and k=100 that is about 99.4% (my arithmetic). So 5–10% replication catches persistent cheaters but not one-shot, well-timed poisoning. That is why SENTINEL-style always-on statistics are still needed.
- SENTINEL's 0% F1 on some gradient attacks and 68.6% recall at 4B mean it **cannot be the only layer**. It is a cheap first filter.
- Agora's "unmodified build" integrity check is a closed-source binary computing a hash on the contributor's machine. Without hardware attestation (consumer RTX cards have none; section 5) this is obfuscation that raises cheating cost, not cryptographic assurance. That Pluralis also lists adversarial defense as unimplemented is consistent with this reading.

### Gaps
- SENTINEL has no measured overhead and no code. I did not read its last ~115k characters (appendix).
- No published end-to-end cost exists for redundant-stage verification on a consumer pipeline run.
- I found no training-time activation-fingerprint (TOPLOC-for-training) paper.
- I did not check whether Pluralis's later runs (post-8B) added defenses.

---

## 2. Verification in data-parallel / DiLoCo training; Byzantine-robust aggregation; poisoning and backdoors

### Takeaway
For DiLoCo-style pseudo-gradient exchange, the deployed state of the art is Templar's Gauntlet:
- validator-measured loss reduction on the peer's assigned data versus random data;
- sync and liveness checks;
- OpenSkill ranking, top-k (≤20) selection, and median-norm normalization.

Covenant-72B was trained this way in Mar 2026, but its "permissionless" peers each had about 8×B200, not consumer GPUs.

Classical Byzantine-robust aggregators (Krum, Bulyan, CenteredClip, geometric median, trimmed mean) remain the toolbox. I found **no 2025–26 paper evaluating them specifically on DiLoCo/LLM pseudo-gradients**.

The poisoning threat is real at small doses: about 250 documents backdoored models from 600M to 13B (Anthropic/UK AISI/Turing, Oct 2025). A 2026 result (backdoor absorption) gives formal support for random scheduling plus about 10% lazy verification, but only in a toy single-trainer setting.

### Cited Findings
**Gauntlet / Covenant-72B** (arXiv 2603.08163 v2, Mar 2026), read 2026-11-05 — [arXiv HTML](https://arxiv.org/html/2603.08163v2):
- **LossScore.** It evaluates "only a subset of peers on a small subset of data". A peer that improves loss on random data more than on its assigned data "receives a negative score", which deters copying.
- **Other checks.** Liveness and sync checks run on all peers, and OpenSkill provides persistent ranking. Submissions are normalized to the median norm for robustness to "peers with errors or adversarial behavior".
- **Participation.** At most 20 contributors per round, averaging 16.9 contributing and 24.4 active. At least 70 unique UIDs, a lower bound because UIDs change hands.
- **Hardware.** Peers were "expected to have at least 8×8 NVIDIA B200 GPUs". Bandwidth was limited to 500 Mb/s down and 110 Mb/s up via Cloudflare R2.
- **Not reported.** No observed cheating incidents and no validator compute cost.
- **Incident (secondary, unverified).** A guide describes an undated "Christmas Day" attack in which a miner sent pseudo-gradients with very large values and disrupted the subnet for about 48 h. It also describes "bucket copying" by lazy miners — [learnbittensor.org SN3](https://learnbittensor.org/subnets/3). The Templar repo says the protocol is dormant, and SN3 now runs Crusades — [github.com/one-covenant/templar](https://github.com/one-covenant/templar).

**Robust aggregation (general FL; not LLM-specific):**
- Krum and Bulyan used as DP-side defenses inside SENTINEL's pipeline experiments gave 86.6% / 82.9% F1 on mixed attacks — [SENTINEL HTML](https://arxiv.org/html/2603.03592).
- BTARD (CenteredClip + validator recomputation) — [arXiv 2106.11257](https://arxiv.org/pdf/2106.11257).
- 2026 FL aggregators are designed for FL, not LLM pretraining:
  - DRAG divergence-based aggregation with pseudo-gradient extrapolation, Jan 2026 — [arXiv 2601.06903](https://www.arxiv.org/pdf/2601.06903);
  - meta-layer aggregation, Mar 2026 — [arXiv 2603.16846](https://arxiv.org/html/2603.16846v1);
  - Giskard, Byzantine-robust plus confidential decentralized aggregation, Jun 2026 — [arXiv 2606.19129](https://arxiv.org/html/2606.19129v1).
- Byzantine/Sybil attacks exploiting GRPO group statistics in decentralized RL post-training, Jul 2025 — [arXiv 2507.14928 (via ResearchGate)](https://www.researchgate.net/publication/393890623_Byzantine-Robust_Decentralized_Coordination_of_LLM_Agents).

**Poisoning and backdoors:**
- **About 250 poisoned documents suffice** to backdoor models from 600M to 13B params, a near-constant count independent of model or data size (Anthropic, UK AISI, Alan Turing Institute, Oct 2025) — [Anthropic](https://www.anthropic.com/research/small-samples-poison); [arXiv 2510.07192](https://arxiv.org/pdf/2510.07192).
- Persistent pretraining poisoning (ICLR 2025): 0.1% poisoning gives strong effects that survive SFT and DPO, with rates as low as 0.001% tested — [ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/file/4dade38eae8c007f3a564b8ea820664a-Paper-Conference.pdf).
- "Agentic backdoors via pretraining poisoning" (arXiv 2610.37741, Oct 2026; secondary summary): 0.1% of corpus gives about 92% ASR on Qwen3-4B, persisting through post-training — [emergentmind](https://www.emergentmind.com/papers/2610.37741).
- **Backdoor absorption** (Seddik, Souihi, Tamaazousti, Tucci Piergiovanni — CEA-LIST), arXiv 2607.06643, 2026-07-07 — [arXiv](https://arxiv.org/abs/2607.06643); [HTML](https://arxiv.org/html/2607.06643):
  - **Setting.** Sequential: one trainer is chosen per step by weight-based random scheduling. Weight is multiplied by (1−S) when a trainer is caught. A lazy verification oracle audits each step with probability v and detection rate d=0.9, modeled on PoTS at about 30% per-step cost.
  - **Results.** ResNet-18/CIFAR-10 BadNet, N=100, f=50%, 10k steps. Single-trainer ASR 99.80%; absorption alone 99.52%; **absorption + 10% verification 7.20% ASR**, with clean accuracy unchanged (80.06%) and 2.76% wall-clock overhead.
  - **Limitations (authors).** Central owner, one attack, one model and dataset, finite horizons. Not LLM, not data-parallel, not pipeline.
- No 2025–26 paper found on poisoning *specifically* via malicious DiLoCo pseudo-gradients; searches on 2026-11-05 returned only centralized-corpus work.

### Inferences
- **Data poisoning versus update poisoning (inference).** If the coordinator owns the curated corpus and assigns shards deterministically from a seed (Templar, Psyche, Agora all do), contributors cannot inject *documents*. They can only craft *updates* that act like poisoned data. The 250-document result implies a small number of crafted updates could implant a backdoor. Loss-delta scoring on clean held-out data will not see a trigger-conditional backdoor, so random sampled exact or tolerance replay of a contributor's step is the stronger defense: it compares the submission with what the assigned data would have produced.
- Median-norm normalization (Templar) blocks the "huge values" attack cheaply. It should be mandatory along with norm clipping.
- Top-k selection (≤20 per round) wastes honest compute in a consumer setting with hundreds of peers. A consumer DiLoCo design should accept all updates that pass checks, weighted, rather than pay only winners.

### Gaps
- I found no evaluation of robust aggregators on DiLoCo/LLM pseudo-gradients and no adaptive-attack analysis of Gauntlet (copy plus noise, assigned-data gaming).
- I did not verify the agentic-backdoor numbers beyond a secondary summary.

---

## 3. Measuring contribution for payment: compute-based vs utility-based; how projects do it; BOINC and Folding@home lessons; free-riders

### Takeaway
Every live or recent consumer-facing project pays (or awards points) for **compute or presence, not utility**:
- **Pluralis Agora**: points = node-reported PFLOPs plus 1 PFLOP per active hour, capped at 2 peers per HuggingFace account, no money yet.
- **Psyche**: an equal share of an epoch's point pool per client that finished the epoch. Its "Verifier" and "TieBreaker" committee roles are `todo!()` in code.
- **Prime Intellect's protocol**: active time.
- **Templar**: the one utility-based scheme (loss-delta ranking), with datacenter-class peers.

The 20-year volunteer-computing record (SETI@home/BOINC) shows that self-reported or benchmark-based credit is gamed by modified clients. The fix is server-computed credit from job size plus replication or adaptive replication. Shapley-style utility attribution is too expensive at LLM scale. The practical answer is **verified-compute base pay** (server-side FLOP formula × accepted work units) with **utility multipliers only where measurable cheaply** (DiLoCo loss-delta).

### Cited Findings
**Pluralis Agora points** (repo `docs/quick-start/points.md`, cloned 2026-11-05) — [github.com/PluralisResearch/agora](https://github.com/PluralisResearch/agora):
- "Every node accrues **compute points** equal to the raw pflops it has processed", plus "**presence points**: a baseline 1 PFLOP for each hour the peer is active".
- "Every node periodically reports to the metrics server", so accrual is based on node reports.
- "We allow up to **2 active peers per account**." Identity is a HuggingFace username.
- "There is no financial reward tied to your score at this stage."

**Psyche** (Nous), `psyche-book/src/explain/rewards.md` and code at commit `0bdb13d` (2026-03-20), cloned 2026-11-05 — [github.com/PsycheFoundation/psyche](https://github.com/PsycheFoundation/psyche):
- **Rewards.** "Each client is rewarded at the end of an epoch if the client successfully completed the whole epoch. A pool of reward 'points' is shared equally among all the finishing clients." A Solana `Treasurer` escrow converts points to tokens at a fixed rate, and a Mining Pool contract lets users pool funds to rent compute.
- **Witnesses.** Randomly elected witnesses (from the same seed as data assignment) send bloom-filter "witness proofs" recording *which commitments (SHA-256 of results) they received* from which clients, building a quorum. This shows liveness and availability, not correctness.
- **Unimplemented verification.** `shared/coordinator/src/coordinator.rs` lines ~701–702 read `Committee::TieBreaker => todo!(), Committee::Verifier => todo!()`. A `verification_percent` config exists but verifier-role handling is unimplemented in this commit.
- **Slashing and permissions.** A `slashing_rate_per_client` exists for ejected clients. Runs can be "Permissioned" (whitelisted keys via a Solana Authorizer program) or "Permissionless".
- **Status.** A review updated 2026-10-27 says Psyche is still on devnet — [ownyourmind](https://ownyourmind.ai/projects/nous-research/).

**Prime Intellect.**
- The protocol repo was last committed 2025-11-09, with a RewardsDistributor paying by active time and no slashing documented (earlier note) — [github.com/PrimeIntellect-ai/protocol](https://github.com/PrimeIntellect-ai/protocol).
- TOPLOC verifies inference rollouts (INTELLECT-2) — [arXiv 2505.07291](https://arxiv.org/pdf/2505.07291).
- INTELLECT-3 trained on a centralized 512×H200 cluster — [arXiv 2512.16144](https://arxiv.org/html/2512.16144v1).

**Gensyn.**
- The RL Swarm README describes reward by bets judged by "Judge", a verifiable evaluation framework built on Verde. Gensyn docs say RL Swarm and Gensyn-hosted nodes are paused (status conflicts across sources) — [github.com/gensyn-ai/rl-swarm](https://github.com/gensyn-ai/rl-swarm); [Gensyn testnet](https://www.gensyn.ai/testnet); [docs.gensyn.ai](https://docs.gensyn.ai/testnet).

**BOINC CreditNew** (wiki, cloned 2026-11-05) — [BOINC CreditNew](https://github.com/BOINC/boinc/wiki/CreditNew):
- **Formula.** Credit = elapsed time × scheduler-estimated *peak* FLOPS: Whetstone for CPUs, and for GPUs a manufacturer formula that "may be wrong". It is scaled to "cobblestones" and normalized across app versions and hosts. Credit is tied to the most efficient version.
- **Host normalization.** It "mostly eliminates the incentive to cheat by claiming excessive credit".
- **Defenses.** A sanity cap (`fpops_bound`) handles one-time cheats. Cherry-picking (aborting long jobs) is handled by requiring evidence before host scaling, with a scaling cap of about 10. Per-host daily job quotas halve on errors and double on success.
- **With replication**, it grants the average of reliable replicas' claims.

**SETI@home cheating history** (news and forum level, secondary):
- Director David Anderson acknowledged rising credit cheating in classic SETI@home and pointed to BOINC as the cheat-resistant successor — [Neowin](https://www.neowin.net/news/setihome-to-investigate-cheating/).
- Forum accounts say optimized or hacked clients claimed more credit. Quorum trimming (drop high and low claims, average the rest) stopped most but not all inflation — [Rosetta forum](https://boinc.bakerlab.org/forum_thread.php?id=743). These are forum sources; treat the details as anecdotal.

**Folding@home** — [F@H points overview](https://foldinghome-client-documentation.readthedocs.io/en/latest/points_overview.html); [F@H passkey/stats](https://foldingathome.org/faq/stats):
- Points are set per project by a **benchmark machine** (server-side, not client-claimed).
- The Quick Return Bonus requires a passkey, ≥10 bonus-eligible work units returned, ≥80% return rate, and return before timeout, with k-factor baseline 0.75.
- Time counts from download to Work Server acceptance.

**Utility-based attribution cost:**
- Shapley-value FL methods are reported as "prohibitively expensive" and biased by topology in decentralized settings (DFL-Shapley/DFL-MR line) — [arXiv 2505.23246](https://arxiv.org/html/2505.23246v1).
- SurrogateSHAP (ICML 2026) offers retraining-free attribution (earlier note) — [ICML](https://icml.cc/virtual/2026/poster/63145).
- A Jul 2026 compensation-design paper studies payment rules when agents commit before contributions are known — [arXiv 2607.14438](https://arxiv.org/pdf/2607.14438).

**Free-riders:**
- The "delta weights" attack (Lin et al. 2019) fabricates updates from the difference of the last two global models and evades DAGMM detection — [arXiv 1911.12560](https://arxiv.org/pdf/1911.12560).
- WEF-defense (weight-evolving frequency) struggles against dynamic free-riders and global-model-mimicking attacks. S2-WEF (Apr 2026) simulates mimic patterns server-side; ADWA adds Gaussian noise to delta-weight updates — [arXiv 2604.04611](https://arxiv.org/abs/2604.04611).
- Templar's assigned-versus-random data loss check is the deployed LLM-scale free-rider test — [arXiv 2603.08163](https://arxiv.org/html/2603.08163v2).

### Inferences
- **Do not pay on node-reported FLOPs (inference).** Agora's points accrue from node-reported metrics, which the SETI/BOINC record shows a modified client will inflate. In pipeline mode the coordinator or trainers *know* how many microbatches each worker returned and the model's FLOPs per microbatch per stage. Credit should be computed **server-side** = (accepted microbatches) × (analytic FLOPs per microbatch for that stage), the F@H benchmark-machine analog.
- **Paying for presence.** "Presence" points are cheap to farm and should be small or need a liveness challenge.
- **Heterogeneous hardware.** Pay per *accepted work unit*, not per GPU-hour. A 4090 that does fewer units then earns proportionally less, with no benchmark claims needed. Add a latency or QRB-style bonus, because pipeline throughput is bottlenecked by the slowest stage. A capability benchmark is useful only for *admission and stage placement* (Agora does this), not for pay.
- **Utility pay.** In pipeline or expert parallelism, a single stage's utility cannot be separated from the others, so utility attribution is meaningless per worker and payment should be compute-based. In DiLoCo, loss-delta (Gauntlet) is a usable *multiplier*, but avoid winner-take-all.
- **Free-riding forms in pipeline mode.**
  - Returning stale or cached activations: SENTINEL's delay attack, plus replication.
  - Returning zeros: caught by SENTINEL.
  - Outsourcing to a cheaper GPU: acceptable if correct.
  - Running a smaller or quantized stage: TAO-style tolerance replay catches it.

### Gaps
- No primary source gives Folding@home's full points equation or a documented cheating incident.
- I found no Pluralis statement on how points will convert to ownership or tokens.
- I found no Prime Intellect 2026 payment documentation.

---

## 4. Sybil resistance for consumers (stake, proof-of-personhood, phone/KYC, reputation) and EU privacy/legal trade-offs

### Takeaway
Current projects use weak, cheap identity:
- Pluralis: a HuggingFace account, capped at 2 peers.
- Psyche: a Solana keypair with an optional whitelist and slashing.
- Templar: Bittensor UID registration.
- BTARD: a heuristic.

For a *paid* EU consumer network the realistic options are:
- (1) whitelisted, known participants (MVP);
- (2) payout-rail KYC, which comes almost for free if payouts go through a regulated provider and is already mandated for crypto CASPs by DAC8 from 2026-01-01;
- (3) EUDI Wallet attestations, which member states must offer by about late Nov–Dec 2026, with private-sector acceptance around 2027;
- (4) stake or escrowed earnings.

Biometric proof-of-personhood (World ID) carries EU legal risk: the Bavarian DPA ordered deletion of iris data in Dec 2024 and World appealed.

Note that Sybils matter less when pay is per verified work unit. Sybils matter for (a) voting or majority assumptions (SENTINEL's below-half-per-stage assumption, honest-majority tolerance votes in TAO), (b) per-account caps and presence bonuses, and (c) collusion to reassemble weights.

### Cited Findings
- **Pluralis.** HuggingFace token identity, with "up to 2 active peers per account" — [Agora repo points.md](https://github.com/PluralisResearch/agora). The Authorizer can bar "an individual node or an entire identity" — [arXiv 2607.13332](https://arxiv.org/pdf/2607.13332).
- **Psyche.** Solana master and delegate keys, Permissioned (whitelisted) or Permissionless runs, and `slashing_rate_per_client` — [Psyche repo authentication.md](https://github.com/PsycheFoundation/psyche).
- **BTARD.** "Proposes a heuristic for resisting Sybil attacks" (summary-level) — [arXiv 2106.11257](https://arxiv.org/pdf/2106.11257).
- **World ID / Worldcoin in the EU.** The Bavarian DPA (BayLDA, lead GDPR authority) in Dec 2024 ordered deletion of iris codes collected without a sufficient legal basis. It required a GDPR-compliant deletion procedure within one month and explicit consent for certain processing. World appealed and says it no longer stores iris codes centrally — [The Block](https://www.theblock.co/post/331713/german-authority-orders-eyeball-scanning-world-project-to-delete-data-after-investigation); [Decrypt](https://decrypt.co/298090/german-watchdog-cracks-down-on-worldcoin-over-biometric-data). I did not find the appeal outcome.
- **EUDI Wallet (eIDAS 2.0, Reg. (EU) 2024/1183).** Member states must provide at least one free, interoperable wallet by late 2026. Sources disagree on the date (21 Nov, 24 Dec or 31 Dec 2026), and private-sector mandatory acceptance comes roughly 12 months later — [fintech.global 2026-07-13](https://fintech.global/2026/07/13/eidas-2-0-deadlines-loom-two-tracks-one-trust-chain/); [Gataca timeline](https://gataca.io/resources/blog/eIDAS2-timeline). Persona announced support for the French and German EUDI wallets on 2026-06-18 — [Persona](https://withpersona.com/blog/persona-supports-france-and-germany-eudi-wallets-for-secure-private-identity-verification).
- **DAC8** (Directive 2023/2226). It applies from 2026-01-01. Crypto-asset service providers must collect names, addresses, tax IDs and tax residence at onboarding, with first reports in 2027. Dates and national transposition vary; Luxembourg adopted it 2026-03-19 — [Grant Thornton NL](https://www.grantthornton.nl/en/insights-en/articles/dac8-reporting-requirements-for-crypto-and-digital-asset-service-providers-in-the-eu/); [Harneys](https://www.harneys.com/our-blogs/regulatory/luxembourg-transposes-dac8/); [Gemini help](https://support.gemini.com/hc/en-gb/articles/45254773783195-EU-Tax-Reporting-The-Crypto-Asset-Reporting-Framework-DAC8).

### Inferences
- **Identity is a payout problem as much as a security problem (inference).** Anyone paid in fiat or via an exchange will be KYC'd by the payout rail anyway. Leveraging that (one verified payee = one account, unlimited nodes) gives Sybil resistance for caps and bonuses without the project storing ID documents itself, which reduces GDPR exposure. Data minimization: store only a payee pseudonym or token from the provider.
- **Do not rely on honest-majority-per-stage assumptions in permissionless mode.** Use operator-run or randomly assigned auditors and random stage assignment (Agora's Authorizer already assigns stages), so a Sybil cannot choose where to sit.
- **Escrowed earnings are "stake" consumers can tolerate.** Hold back, say, 14–30 days of earnings, forfeited on proven cheating. This avoids upfront crypto stake, which is a barrier for consumers.
- Biometric PoP (World ID) is GDPR Art. 9 special-category data. It has an active enforcement history in the EU and is not recommended for the MVP.

### Gaps
- Phone-number verification cost and effectiveness (SMS farms) was not researched.
- No legal source was gathered on whether paying consumers for compute triggers DAC7 platform reporting, employment or self-employment classification, or VAT. **Needs counsel.**
- The EUDI wallet pseudonym and unlinkability features (ARF) were not checked.

---

## 5. Hardware/software trust on consumer machines; anti-tamper clients; sandboxing; protecting the volunteer

### Takeaway
Consumer GeForce RTX cards have no confidential-computing or attestation capability. NVIDIA CC covers Hopper and Blackwell datacenter parts, plus, per a secondary source, the RTX PRO 6000 *Server* Edition. TEE-based trust is therefore unavailable for the consumer fleet, and even datacenter TEEs are physically breakable (TEE.fail, 2025).

"Unmodified client" checks such as Agora's binary integrity hash are obfuscation, not proof. Correctness must come from *output* verification (sections 1–2).

For the volunteer, the bigger risk runs the other way. Containers running GPU code have had critical escapes: NVIDIAScape, CVE-2025-23266, CVSS 9.0, a three-line Dockerfile, fixed in Container Toolkit 1.17.8 in Jul 2025. gVisor's nvproxy adds a syscall sandbox, but GPU isolation still rests on the NVIDIA driver. Contributors should run only signed, operator-built images, no third-party task code, and no pickle-format weights.

### Cited Findings
- **NVIDIA CC scope.** Hopper (H100 PCIe/NVL/HGX) and Blackwell, requiring a CPU VM-TEE (SEV-SNP or TDX) — [NVIDIA dev blog](https://developer.nvidia.com/blog/confidential-computing-on-h100-gpus-for-secure-and-trustworthy-ai/); [NVIDIA CC page](https://www.nvidia.com/en-sg/data-center/solutions/confidential-computing/).
- RTX PRO 6000 Blackwell **Server Edition** TEE driver support from R580 TRD1 (secondary) — [Super Protocol](https://superprotocol.com/resources/gpu-cpu-tee-requirements).
- No source lists GeForce support. NVIDIA's supported-platform docs are at [docs.nvidia.com/confidential-computing](https://docs.nvidia.com/confidential-computing/).
- **TEE.fail** (DDR5 interposer, under $1k): forges TDX quotes and relays NVIDIA GPU attestation — [tee.fail](https://tee.fail/) (detail in verification.md).
- **Agora integrity check.** Shipped as a compiled CPython extension (`integrity_check.cpython-311-x86_64-linux-gnu.so`). The Authorizer sends the resulting `integrity_hash` at registration. Code path: `agora/src/agora/security/authorizer.py` lines 90–111, cloned 2026-11-05 — [github.com/PluralisResearch/agora](https://github.com/PluralisResearch/agora).
- **NVIDIAScape, CVE-2025-23266** (Wiz, Jul 2025). CVSS 9.0. An `LD_PRELOAD` in a Dockerfile makes the privileged nvidia-ctk `createContainer` hook load an attacker library, giving full host takeover. It affects Container Toolkit ≤1.17.7 and GPU Operator ≤25.3.0, fixed in 1.17.8 / 25.3.1. Wiz says it affects 37% of cloud environments — [The Hacker News](https://thehackernews.com/2025/07/critical-nvidia-container-toolkit-flaw.html).
- **gVisor GPU (nvproxy).** It forwards CUDA ioctls to the host driver. gVisor's blog says GPU isolation "is enforced by the GPU driver and hardware itself" rather than by gVisor, and that old drivers are insecure. Some ioctls are unimplemented, and there are open issues on DRA GPU scoping and checkpoint/restore — [gVisor GPU docs](https://gvisor.dev/docs/user_guide/gpu); [gVisor blog 2023-06-20](https://gvisor.dev/blog/2023/06/20/gpu-pytorch-stable-diffusion/).
- **Firecracker** lacks GPU passthrough, so most microVM sandboxes are CPU-only — [Northflank](https://northflank.com/blog/gpu-sandboxes) (vendor blog).
- **Agora networking.** Contributors must open inbound port 49200 — [Agora README](https://github.com/PluralisResearch/agora).

### Inferences
- **Volunteer protection checklist (inference, from the above):**
  - The client runs only operator-signed, reproducibly built images. It never executes contributor- or third-party-supplied code; the model architecture and kernels are fixed per run.
  - Keep the NVIDIA Container Toolkit ≥1.17.8 and enforce a minimum driver version at admission (Agora already gates on hardware).
  - Use rootless Docker or Podman, plus gVisor (`runsc --nvproxy`) where compatible.
  - Load weights and checkpoints only in safetensors format.
  - Publish an authenticated, minimal network surface, ideally outbound-only via relay or NAT traversal instead of an open inbound port.
  - Cap GPU power and temperature, and show the user what runs.
  - Pickle deserialization risk is well known but not sourced this session.
- **Anti-tamper.** Treat client integrity checks as a speed bump: they raise the cost for casual cheaters, as BOINC's experience with optimized clients suggests. Publish the client as open source so the contributor can audit it. The asymmetry is uncomfortable: a closed integrity binary protects the operator but asks the volunteer to trust opaque code.

### Gaps
- No primary NVIDIA statement explicitly excluding GeForce from CC was retrieved; the exclusion is inferred from supported-product lists.
- Windows and WSL2 client security (most consumer GPUs run Windows) was not researched.
- No source was found on GPU memory isolation for multiple processes on consumer cards (e.g., leftover VRAM leakage between jobs).

---

## 6. Protecting the model itself: weight exfiltration (Pluralis "protocol models") and data privacy

### Takeaway
Pipeline or model parallelism means no single participant holds all the weights. Pluralis's **Unextractable Protocol Models** (NeurIPS 2025; arXiv 2605.23464) add periodic random invertible transforms at stage boundaries, so shards from different times do not stitch together. Evidence:
- function preserved (ΔPPL < 0.01 after 10k transforms on 0.5B–1B models);
- about 1.6% training-time overhead;
- the authors' estimate that fine-tuning stitched partitions needs ≥60% of from-scratch tokens.

The collusion threshold is not specified in the abstract. I found no evidence UPMs were active in the Pluralis-8B run. Weights still leave the operator: Agora contributors download stage checkpoints from cloud storage.

A Sybil holding nodes in every stage *at the same time* would get a coherent snapshot, and UPMs defend only against stitching across time. Non-extractability is a cost-raising measure, not a guarantee. If the project intends an open-weights release anyway, it matters little except for staging releases.

### Cited Findings
- **UPMs** (Long, Hewa Koneputugodage, Ajanthan, Zuo, Avraham, Shevchenko, Dolatabadi, Ramasinghe), arXiv 2605.23464 (posted 2026-05-22; NeurIPS 2025, Adv. NeurIPS 38 pp. 18677–18713) — [arXiv](https://arxiv.org/abs/2605.23464):
  - Mechanism: time-varying random invertible transforms at participant boundaries that preserve the network function but make shards from different time steps incompatible.
  - Evidence: Qwen-2.5-0.5B and Llama-3.2-1B, with 10k transforms giving ΔPPL < 0.01 and JS drift < 4×10⁻⁵. Gradient fine-tuning of stitched partitions needs ≥60% of from-scratch tokens.
  - Overhead: inference about 3% latency, 0.1% bandwidth and 10% GPU memory; training about 1.6% time and under 1% memory.
  - The colluding-party assumptions were not stated in the abstract.
- **Agora.** "Each participant holds only one stage of the model, and no single party ever possesses the full weights". UPMs "extend this so the weights can never be extracted from a node at all". Contributors "get the state from periodically refreshed checkpoints stored in cloud object storage", with checkpoints every 500 steps to S3 — [arXiv 2607.13332](https://arxiv.org/pdf/2607.13332).
- Pluralis's conceptual framing (value retained by contributors, "no-off problem") — [arXiv 2412.07890](https://web3.arxiv.org/pdf/2412.07890).
- **Data privacy.** In Agora, CPU-only "trainer" nodes sample batches from a dataset shard and route them through stages ("A trainer has light system requirements and does not require a GPU") — [arXiv 2607.13332](https://arxiv.org/pdf/2607.13332). With a public corpus (FineWeb-Edu, ODC-BY) data privacy is moot. With private data, middle-stage workers see only activations, but SENTINEL explicitly does not address membership-inference attacks — [SENTINEL HTML](https://arxiv.org/html/2603.03592).

### Inferences
- **Simultaneous-snapshot weakness (inference).** UPMs make *temporal* stitching useless, but an attacker holding a replica in *every* stage at the same moment, possible with HuggingFace-account Sybils and random stage placement given enough nodes, gets a consistent model. Mitigations:
  - strong identity (section 4);
  - limiting the number of stages any one payee can occupy;
  - operator-held first and last stages (embeddings and LM head), which also matches SENTINEL's honest-first/last assumption.
- For a "people's datacenter" that plans to release open weights, exfiltration risk mainly affects pre-release value capture. Decide policy first; don't over-engineer.
- Private-data training on untrusted consumer GPUs has no practical protection in 2026, since consumer GPUs have no TEE (section 5). Restrict the MVP to public or licensed-open corpora.

### Gaps
- The UPM full paper was not read: attack catalogue, collusion threshold, and behavior at 8B+ and low precision.
- No independent evaluation of UPM extractability was found.
- No source was found on the Pluralis-8B weight-release status. A web search on 2026-11-05 found nothing.

---

## 7. Recommended layered design: MVP (permissioned) → permissionless scale, with overhead estimates

### Takeaway
No single primitive suffices on consumer GPUs: no TEEs, heterogeneous numerics, home links. The defensible 2026 design is **defense in depth with economic deterrence**:
1. Identity and admission.
2. Server-computed compute credit, not self-reported.
3. Always-on cheap statistical checks (SENTINEL-style for pipeline stages; norm, sync and assigned-data checks for DiLoCo).
4. Random sampled redundancy and replay under calibrated tolerances (TAO/OVIG style, per GPU class), with the sample rate adaptive per host (BOINC adaptive replication).
5. Escrowed earnings forfeited on proven cheating.
6. Operator-run first and last stages and auditors in the MVP, decentralized later.

Total verification overhead is estimated at about 5–15% of compute in steady state (estimate, section breakdown below). That is against more than 100% for full replication and 10⁴x for ZK.

### Cited Findings (the menu; costs as published)

| Mechanism | What it catches | Published cost | Maturity / repo (date) |
|---|---|---|---|
| Admission + signed short-lived credentials + stage assignment by coordinator (Agora Authorizer) | Unauthorized peers, stage self-selection, revocation | Negligible | Deployed in Pluralis-8B (Jul 2026); Apache-2.0 [agora](https://github.com/PluralisResearch/agora) |
| Client integrity hash (closed binary) | Casual client modification | Negligible | Agora (Jul 2026); not attestation |
| SENTINEL EMA checks on inter-stage activations/gradients | Corrupted, stale or zero activations; many gradient attacks (not all) | "No duplication"; overhead unmeasured; CPU verifiers | Preprint Mar 2026, F1 ~80–100%, no code [arXiv](https://arxiv.org/abs/2603.03592) |
| Duplicated previous-stage block / jumping connections | Single malicious middle stage | Extra GPU memory and compute (unquantified) | ICML 2024, code [pipeline_attack](https://github.com/dcx001016/pipeline_attack) |
| Replication (BOINC) / adaptive replication | Wrong or lazy results | ≥50% (full) vs ~5–10% (adaptive) | 20+ years in BOINC [wiki](https://github.com/BOINC/boinc/wiki/Adaptive-Replication) |
| Homogeneous redundancy (compare only within numeric class) | Bitwise compare despite heterogeneity | Scheduling constraint | BOINC [wiki](https://github.com/BOINC/boinc/wiki/Homogeneous-Redundancy) |
| TAO tolerance-aware dispute (per-op empirical bounds over A100/H100/RTX6000/RTX4090) | Model swap, quantization, graph rewrite (inference) | 0.3% (Qwen3-8B) | EuroSys 2026, no code [arXiv](https://arxiv.org/abs/2510.16028) |
| OVIG gradient-replay with calibrated boundary | Shortcut and adaptive training attacks | +14.3% compute | Preprint 2026, no code [arXiv](https://arxiv.org/abs/2606.21045) |
| Bitwise replay (OPEN-1B / RepOps) | Any deviation, exact | GEMMs "several times slower" | Gensyn Sep 2026 [arXiv](https://arxiv.org/abs/2609.17380) |
| Random scheduler + lazy verification at 10% of steps | Backdoor persistence | 2.76% wall-clock (toy sim) | CEA preprint Jul 2026 [arXiv](https://arxiv.org/abs/2607.06643) |
| Gauntlet LossScore + assigned/random data + median-norm + sync checks (DiLoCo) | Free-riding, copying, huge-norm updates, stale peers | Validator eval on a subset of peers and data (unquantified) | Covenant-72B Mar 2026; MIT, dormant [templar](https://github.com/one-covenant/templar) |
| Robust all-reduce (CenteredClip/BTARD, Krum, Bulyan) | Byzantine DP updates | BTARD comms independent of param count | ICML 2022 [arXiv](https://arxiv.org/pdf/2106.11257) |
| Psyche witnesses (bloom filters of received commitments) | Liveness, availability, non-delivery | Small | Devnet; verifier role `todo!()` (code 2026-03-20) [psyche](https://github.com/PsycheFoundation/psyche) |
| UPM transforms | Temporal stitching of stolen shards | ~1.6% training time | NeurIPS 2025 [arXiv](https://arxiv.org/abs/2605.23464) |
| GPU TEE attestation | Environment integrity | ~3–7% (vendor) | Not available on GeForce; broken by TEE.fail [tee.fail](https://tee.fail/) |
| zkML proof of training | Exact | ~10⁴x; ≤10M params demonstrated | Research (verification.md) |

### Inferences (recommended design; all overhead figures are my estimates unless cited)

**Phase 0 — MVP, permissioned (10–100 known participants: friends, community members with verified payee identity).**
1. **Identity.** Whitelisted keys (Psyche-style Permissioned run or Agora-style Authorizer). One payee maps to many nodes; payee KYC is done by the payout provider.
2. **Topology.**
   - Operator-run data and trainer routing nodes.
   - **Operator-run first and last pipeline stages** (embedding and LM head). This satisfies SENTINEL's and Lu et al.'s trusted-ends assumption and limits weight-snapshot risk.
   - Consumers serve middle stages, with the coordinator assigning stages.
   - Public corpus only.
3. **Always-on checks.** SENTINEL-style EMA statistics on every inter-stage tensor, run by operator CPU nodes. Robust intra-stage averaging: median-norm clip plus CenteredClip or trimmed mean.
4. **Sampled redundancy.** Send r ≈ 5–10% of microbatches to a second replica of the same stage. Pair same-SKU where possible (homogeneous redundancy). Otherwise compare under per-SKU-pair tolerance profiles calibrated from honest replays (TAO/OVIG method). The calibration set should include RTX 3090/4090/5090 and the target bf16 kernels.
   - Cost ≈ r of middle-stage compute.
   - Persistent cheating over 100 microbatches is caught with probability above 99% at r=5% (1−0.95¹⁰⁰ ≈ 99.4%).
   - Use BOINC-style adaptive rates: new hosts get r=25% until 10 consecutive clean checks, then decay toward 5%.
5. **Audits.** An operator GPU audit node replays a further about 1% of microbatches from logged inputs. This is also the tie-breaker when a replica pair disagrees.
6. **Payment.**
   - Credit = Σ accepted microbatches × analytic FLOPs/microbatch for the stage (server-computed), times an on-time factor.
   - No credit for presence beyond a small liveness stipend.
   - Hold back 14–30 days of earnings as escrow, forfeited on a proven violation, and ban the payee.
   - This replaces Agora's node-reported PFLOPs.
7. **Volunteer safety.** Signed images only, Container Toolkit ≥1.17.8, rootless plus gVisor nvproxy where it works, safetensors only, outbound-only networking.
8. **Estimated steady-state overhead:** about 6–12% extra compute (r=5–10% redundancy plus 1% audits), CPU-only EMA verifiers, and a few percent bandwidth for duplicated microbatches. Plus the pipeline inefficiency Agora already pays (63% of H100-cluster efficiency).

**Phase 1 — open sign-up, still curated (hundreds to thousands of nodes).**
- Identity: payout-rail KYC or EUDI wallet attestation (available from late 2026 to 2027), with an account cap per payee on *stages occupied*, not on nodes.
- Make audit rates adaptive per payee reputation. Add the backdoor-absorption-style random scheduling: random microbatch-to-replica routing, as SWARM and Agora already do, which an attacker cannot predict.
- Publish per-host verdict logs, Merkle-committed per round, so contributors can contest bans, with a manual appeal process.
- For any DiLoCo sub-component (e.g., replicas syncing across regions), add Gauntlet-style assigned-versus-random-data loss checks and accept-all-passing (not top-20) weighting.

**Phase 2 — permissionless scale.**
- Decentralize auditors: randomly selected, staked or escrowed audit committees from high-reputation hosts, with an operator TEE or cloud referee as a fallback.
- Run a TAO-style dispute game (bisect to one operator, adjudicate by bound or honest-majority vote) on contested results. Consider OPEN-1B-style bitwise kernels if their slowdown becomes acceptable on consumer GPUs.
- On-chain or ledger settlement is optional. Verde notes the EVM cannot referee floating point (verification.md), so verdicts come from an off-chain committee.
- Consider UPM transforms if weights must stay non-extractable until release.
- Expected added overhead is a further 1–5% for disputes and escrow bookkeeping (estimate). The dominant cost remains sampled redundancy.

**Residual risks to state honestly in any pitch:**
- Trigger-conditional backdoors crafted to pass statistics and low-rate sampling. These are bounded only probabilistically, and the backdoor-absorption evidence is toy-scale.
- Collusion of a payee controlling both replicas in a redundancy pair. Mitigate with coordinator-chosen pairs across different payees.
- SENTINEL's weak recall on some gradient attacks.
- Unverified FLOP-equivalence of different GPUs' numerics in bf16.
- Legal classification of paying consumers (Gaps, section 4).

### Gaps
- No published system combines pipeline-stage verification with payment on consumer GPUs. All overhead numbers above are estimates assembled from component papers.
- The tolerance calibration for bf16 training on GeForce cards (RTX 3090/4090/5090) is not published. TAO calibrated FP32 inference on RTX 4090 and RTX 6000, but not bf16 training.
- No code exists for SENTINEL, TAO or OVIG as of 2026-11-05 (no links found), so an MVP must re-implement them.
