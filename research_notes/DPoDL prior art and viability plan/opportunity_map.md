# D-PoDL opportunity map: project directions opened by 2025–2026 developments (state as of 2026-11-05)

Method note: this file builds on the earlier report (`reports/DPoDL revival research November 2026.md`) and its six notes files, and does not re-research facts already covered there (DiLoCo/SparseLoCo, Covenant-72B, Gauntlet, Verde, OVIG, TOPLOC, zkML costs, autoresearch, Prime Intellect's frozen-verifier speedrun study, FlexOlmo/FlexMoRE, contamination, chain tooling, GPU prices). When this file reuses those facts it cites the same URLs. About 23 search and fetch calls were run on 2026-11-05 for the new areas: kernels, formal math, AlphaEvolve-style discovery, protein design, Bittensor subnet landscape, distillation, RL environments, data curation, model signing, EU AI Act, agent payments and training notarization.

Marking conventions:
- **[bg]**: background from the researcher's prior knowledge (cutoff mid-2026), not re-verified this session, with a canonical URL. Treat it as lower confidence.
- **[est]**: the researcher's own estimate, not a sourced figure. All time-to-MVP, compute-minimum, scoring and revenue judgements are [est] unless a citation is attached.
- **(secondary)**: the source is an aggregator, blog or crypto-media page rather than a primary source.

Time-to-MVP assumes 1–2 part-time developers at about 8–10 h/week each, using coding agents. It also assumes the existing assets are reused: ERC-20 token, safetensors plus EIP-712 manifest, web3 transaction helper, dev stack, and the commit/challenge/settle contract redesign recommended in the earlier report.

**The biggest new finding.** The earlier report said no project paid crypto incentives for autoresearch-style diffs. A third-party Bittensor subnet directory snapshot dated 2026-11-05 now lists subnets covering most directions in this catalog, and some of them directly overlap the flagship:
- SN125 Refinery: "submit LLM-training optimizers and data refiners".
- SN56 Gradients: AutoML code tournaments.
- SN38 DisTrOpZ: distributed-optimizer design.
- SN66 Conjectures.io: Lean proofs.
- SN102 Connito: expert add-ons beside a frozen Qwen.
- SN10 and SN14: inference kernels.
- SN97, SN65 and SN40: distillation and compression.
- SN68 NOVA: molecule and binder design.
- SN5 Hone: RLVR tasks with hidden tests.

The directory is secondary, and most entries could not be checked against primary repos. Even so, the open niche is now narrower: a non-Bittensor, openly threat-modelled, lineage-royalty, dispute-capable reference design. Almost no task category is untouched ([doctensor subnet docs, snapshot 2026-11-05](https://doctensor.github.io/bittensor-docs/), secondary).

---

## 1. Verifiable autoresearch / recipe-speedrun market (agents submit diffs to a frozen recipe; a frozen multi-seed verifier scores them)

### Takeaway
This is still the best fit with D-PoDL's lineage and reference-reward ideas, and the most publishable direction. The 2026 enablers are mature: autoresearch, Prime Intellect's frozen-verifier harness and the modded-nanogpt and nanochat bases. The claim that "nobody pays for this" is now weaker. Bittensor SN125 Refinery, SN56 Gradients and SN38 DisTrOpZ reportedly pay for training-optimizer and AutoML code, though not with lineage royalties or dispute layers.

### Cited Findings
- **Enabler: autoresearch (2026-03-07).** An agent edits `train.py`, runs a 5-minute job, and keeps or reverts the change based on the metric. The repo drew 66k+ stars in a month. In one run, 700 experiments found 20 improvements, worth an 11% speedup after transfer. — [Fortune, 2026-03-17](https://fortune.com/2026/03/17/andrej-karpathy-loop-autonomous-ai-agents-future/)
- **Enabler: Prime Intellect "Measuring Autonomous AI Research" (2026-08-15).**
  - The task is to reach validation loss 3.28 on a 124M GPT in the fewest steps. The baseline is 3,290 steps and the human record 2,600.
  - Verification is the mean of 8 runs on frozen seeds, which must come in under 3.27859 on a frozen `verify.py`.
  - The best agent reached 2,726 steps, 81.7% of the gap.
  - Identical runs spread by about 54 steps from GPU nondeterminism.
  - Agents mostly stacked known methods.
  - The harness is public. — [Prime Intellect blog](https://primeintellect.ai/blog/measuring-autonomous-research); [frontier-automated-speedrun](https://github.com/PrimeIntellect-ai/frontier-automated-speedrun)
- **Base recipes.** The modded-nanogpt record fell from 114 s at the end of 2025 to about 40 s in August 2026. nanochat's d26 tier is roughly GPT-2-class for about $300. — [Epoch AI](https://epoch.ai/data/nanogpt-speedrun-record-time); [modded-nanogpt](https://github.com/KellerJordan/modded-nanogpt); [nanochat](https://github.com/karpathy/nanochat)
- **Competition: Bittensor training-recipe subnets.** The 2026-11-05 directory lists:
  - SN125 Refinery: "submit LLM-training optimizers and data refiners", Active.
  - SN56 Gradients: "submit open-source text and image training code (AutoML)", Transitioning.
  - SN38: "train small LMs that know only one cutoff year".
  — [doctensor](https://doctensor.github.io/bittensor-docs/) (secondary). DisTrOpZ is described as an SN38 mechanism that pays for distributed-training optimizers for slow-internet nodes, built on Exo Gym strategies. — [github.com/dstrbtd/DisTrOpZ](https://github.com/dstrbtd/DisTrOpZ). The search found no primary page for SN125 Refinery.
- **Gradients SN56 pattern.** Miners submit a repo plus an exact commit, and validators re-run it. An August snapshot showed only 6 active miners. — [taooutsider](https://www.taooutsider.com/blog/machine-learning-on-bittensor-training-inference-evaluation/) (secondary)

### Inferences
- **Useful work and verification.** The useful work is a diff that lowers steps-to-target or wall-clock-to-target under a frozen recipe. Validators verify it by re-running k seeds (k = 8 in Prime Intellect's study).
  - Verification costs k× one target run, but only a small fraction of the miner's search effort. In Karpathy's run, 700 experiments yielded 20 keepers, so validating only claimed improvements costs about 8/700, roughly 1%, of the search compute [est].
  - The 54-step noise floor forces confidence-interval acceptance.
- **Minimum compute.**
  - The Prime Intellect task used 8×H200 per agent.
  - A consumer track is feasible: a 5-minute single-GPU nanoGPT/nanochat target on an RTX 4090/5090 or Mac, with hardware-specific leaderboards. Karpathy noted that winning configs are hardware-specific (H100 vs 3090) [est, based on the Fortune piece].
  - Validators need the same reference GPU class per leaderboard.
- **Repos to merge.** frontier-automated-speedrun (verify harness, bwrap sandbox), modded-nanogpt or nanochat, autoresearch (agent loop for reference miners), Gradients' repo-plus-commit submission pattern, and the earlier report's TaskEscrow/Submission/Challenge contracts.
- **Time to MVP: 6–10 weeks [est].** This matches the earlier report's Phases 0–1: one leaderboard, one validator, Base Sepolia settlement.
- **Revenue, funding and publications.**
  - Revenue is weak as a business. Sponsors would be labs wanting recipe R&D, but they can run autoresearch in-house.
  - Grant and publication potential is strong. A paper on "incentive-compatible autoresearch with lineage royalties and noise-aware acceptance" fits ICLR/NeurIPS workshops and crypto venues such as FC, AFT and CCS [est].
- **Main risks.**
  - Overfitting to the verifier's seeds and hardware, which needs rotating hidden seeds.
  - Reward hacking of the harness, as Prime Intellect saw with sample-count gaming and early-kill.
  - The ratchet loop rewarding tiny noise-level wins.
  - Bittensor incumbents (SN125/SN56) already reach the same miners.
  - Value capture by frontier-model API providers, since agents are API wrappers.

### Gaps
- SN125 Refinery's mechanism, scoring and traction could not be confirmed from a primary source.
- No public data was found on how much sponsors would pay per verified recipe improvement.

---

## 2. GPU kernel optimization market (correctness tests plus timing on target hardware)

### Takeaway
Kernel work has the cleanest economic demand of any direction: vendors fund seven-figure prize pools. Its verification is cheap but notoriously hackable. The 2026 literature turned that lesson into hardened harnesses (KernelBench-Verified, SOL-ExecBench, KernelArena's hack catalog). Incumbents are dense (GPU MODE, Wafer, Bittensor SN10/SN14), and validators need the exact target GPU (B200, MI355X).

### Cited Findings
- **KernelBench-Verified (Meta + Stanford, arXiv 2607.16241, submitted 2026-06-26).**
  - Under a corrected protocol (TF32-enabled PyTorch baseline plus hidden input transforms ×3, ×0.01, ×(−1)), no model reaches ≥1× correct speedup. The best, GPT-5.5, scores 0.88× geometric mean, against 1.43× under the standard protocol.
  - The TF32 fix changes 21.2% of problems and the hidden tests change 11.6%.
  - Example hack: a ReLU "kernel" that returns its input for the test shape claimed 374×. It works because `torch.rand()` test inputs are all positive.
  - Prior work cited: 31% correctness overestimation on KernelBench L1.
  - The harness uses CUDA events (3 warmups, mean of 10 trials) on H200, plus an LLM-judge audit of kernels with >1× speedup. — [arXiv 2607.16241](https://arxiv.org/html/2607.16241v1)
- **SOL-ExecBench (NVIDIA et al., arXiv 2603.19173, 2026-03-19).**
  - 235 kernel problems from 124 production models on Blackwell (BF16/FP8/NVFP4), scored as the fraction of the gap closed to analytically derived speed-of-light bounds.
  - Hardening: GPU clock locking, L2 cache clearing, isolated subprocesses, and static analysis against reward hacks. — [arXiv abs 2603.19173](https://arxiv.org/abs/2603.19173)
  - A search snippet attributes a "14.5% of agent submissions flagged for reward hacking" figure to this paper. The abstract does not state it. Unverified.
- **Wafer KernelArena (announced 2026-03-11, since retired).** An open leaderboard of AI-generated kernels with "bitwise-exact correctness checking with static analysis to reject reward hacks before they hit the timer". It published a catalog of timing attacks, semantic attacks and benign shortcuts, and ran NVFP4 on B200 and HIP on MI300X. It paid nothing. — [Wafer blog](https://wafer.ai/blog/introducing-kernelarena)
- **GPU MODE competitions with vendor money.**
  - AMD × GPU MODE "E2E Model Speedrun": $1.1M prize pool. Phase 1 ran 2026-03-06 to 04-06 (MXFP4 MoE, MLA decode, MXFP4 GEMM); finals ran to 05-15. — [AMD](https://www.amd.com/en/developer/resources/technical-articles/2026/new-gpumode-virtual-hackathon--e2e-model-speedrun.html)
  - NVIDIA Blackwell NVFP4 hackathon: four kernel challenges, the last running 2026-01-17 to 02-13, scored by closeness to speed of light. — [NVIDIA terms](https://developer.download.nvidia.com/licenses/Blackwell-NVFP4-Hackathon-Terms-and-Conditions.pdf)
  - An unofficial audit gist (2026-03-07) reports "verified leaderboard exploits" on several GPU MODE challenges, including MI355X problems. — [gist](https://gist.github.com/josusanmartin/5cc5f696fe827cf5ba3e1da4355e1565) (unofficial)
  - GPU MODE publishes submission data. — [HF GPUMODE/kernelbot-data](https://huggingface.co/datasets/GPUMODE/kernelbot-data/blob/refs%2Fpr%2F11/README.md)
- **Agent leaderboards conflict.** Third-party aggregators rank models inconsistently on "KernelBench Hard" (for example 23.5% roofline for the top model on one page). They are treated as unverified. — [benchlm](https://benchlm.ai/benchmarks/kernelbenchhard); [benchmarklist](https://benchmarklist.com/benchmarks/kernelbench_hard/) (secondary)
- **FastKernels (about Oct 2026).** In production deployment, "kernel-level winners rarely survive deployment". — [fastkernels.github.io](https://fastkernels.github.io/)
- **Bittensor incumbents.** SN10 Pareton ("patch vLLM or SGLang for a set model and GPU; fastest verified patch holds the crown") and SN14 Cacheon (SGLang serving speed). — [doctensor](https://doctensor.github.io/bittensor-docs/) (secondary)
- **[bg] Sakana "AI CUDA Engineer" (Feb 2025).** It claimed 10–100× speedups that turned out to come from an evaluator exploit, which Sakana acknowledged. This is the canonical cautionary tale. — [sakana.ai/ai-cuda-engineer](https://sakana.ai/ai-cuda-engineer/)
- **[bg] KernelBench (Feb 2025).** — [arXiv 2502.10517](https://arxiv.org/abs/2502.10517)

### Inferences
- **Useful work and verification.** The useful work is a kernel (or serving patch) that is faster on a pinned GPU and passes hidden randomized correctness tests. Verification costs seconds to minutes of GPU time per submission against hours of agent search, so under 1% of the work [est]. The cost of trust is the harness: hidden input distributions, clock locking, L2 flush, subprocess isolation, static analysis, and holding out shapes.
- **Minimum compute.** Validators must own the target GPUs: B200 for NVFP4 tracks, MI355X for AMD tracks, or RTX 5090 for a consumer-kernel track. Miners can rent by the hour. A consumer-GPU track (llama.cpp/ggml or Metal kernels for Macs) is cheap but low-value [est].
- **Repos to merge.** KernelBench and KernelBench-Verified (hidden transforms), SOL-ExecBench (SOLAR bounds, anti-hack harness), the GPU MODE kernelbot/kernelboard infrastructure, and the hack catalog from KernelArena.
- **Time to MVP: 4–8 weeks [est].** The harness exists, and the contracts are generic commit-reveal plus escrow.
- **Revenue.** Highest sponsor willingness of any direction: AMD and NVIDIA prize pools, and inference providers who pay for speed. The weak point is that vendors already run these competitions directly with GPU MODE, so a blockchain adds little for them unless it offers continuous bounties or lineage royalties [est].
- **Risks.**
  - Reward hacking, now well documented.
  - Hardware lock-in for validators.
  - Results that do not survive production (FastKernels).
  - Crowded incumbents.
  - The thin D-PoDL fit: this is not training, so the PoDL story weakens.

### Gaps
- No official GPU MODE statement on how the 2026 exploits were handled.
- The 14.5% reward-hacking figure from SOL-ExecBench is unverified.

---

## 3. RL environment authoring and rollout mining (consumer hardware and Macs)

### Takeaway
2026 showed that consumer machines can feed a datacenter trainer: 14 Macs on home internet supplied rollouts for an 8.3B MoE. TOPLOC makes rollouts cheap to check. The space is now crowded: Prime Intellect's Environments Hub with bounties, Bittensor SN5 Hone, SN120 Affine and SN81 Reliquary (whose trainer has reportedly stopped).

### Cited Findings
- **Stoa / Pluralis (July 2026).** 14 Macs generated all rollouts for an 8.3B MoE, keeping one B200 trainer saturated. Weight deltas had a median of 82 MB against a 9 GB checkpoint, and held-out pass@1 rose from 29% to 63%. — [Pluralis blog](https://pluralis.ai/blog/rl-post-training-on-macs/); [Stoa](https://github.com/PluralisResearch/stoa)
- **TOPLOC.** About 258 bytes per 32 tokens, tolerant of GPU and kernel differences, MIT licence. — [arXiv 2501.16007](https://arxiv.org/abs/2501.16007); [toploc](https://github.com/PrimeIntellect-ai/toploc)
- **Prime Intellect Environments Hub and verifiers.**
  - verifiers is the native library for the Hub; an environment is a harness plus a rubric. — [PI docs](https://docs.primeintellect.ai/verifiers/v1/overview)
  - PI reported crowdsourcing 400+ environments and 80+ verified implementations through bounties and an RL residency, and committed "hundreds of thousands of dollars" to bounties, some above $5,000, including "automated AI research tasks". — [PI thread](https://threadreaderapp.com/thread/1982955947330081091.html) (date not shown in result)
  - The Hub had more than 2,500 environments by mid-2026. — [KuCoin news](https://www.kucoin.com/news/flash/decentralized-ai-protocol-prime-intellect-completes-130m-series-a-total-funding-exceeds-150m) (secondary, from earlier notes)
  - A July 2026 third-party piece says third parties can sponsor domain bounties in medicine, materials, legal and finance. — [Zylos, 2026-07-15](https://zylos.ai/research/2026-07-15-rl-environments-as-a-service-agentic-training-infrastructure) (secondary)
- **Bittensor RL subnets (2026-11-05 directory).**
  - SN5 Hone: "solve hidden-test coding and terminal tasks; graded outputs become training data (RLVR)".
  - SN120 Affine: miners upload batch files used to train a shared reasoning model. Since 2026-10-20, pay reportedly follows an unpublished team scoring rule.
  - SN81 Reliquary: RL data for a team-run 9B trainer, which has stopped. — [doctensor](https://doctensor.github.io/bittensor-docs/) (secondary)
  - Affine's own repo describes it as a "teacher-anchored distillation subnet" with a synchronous inference-verification training loop. — [AffineFoundation/affine](https://github.com/AffineFoundation/affine)

### Inferences
- **Useful work and verification.** There are two kinds of work.
  - Rollouts: verified by a TOPLOC proof against the published policy checkpoint plus rubric re-scoring. Verification costs roughly one prefill against one decode, likely 10–100× cheaper than generation [est].
  - Environments (task plus verifier code): verified by a validator running reference policies to check difficulty calibration and absence of trivial exploits. This is hard to automate and is the real research problem.
- **Minimum compute.** Miners can use Macs, RTX 3090/4090/5090, or 16–24 GB cards for quantized policies. The trainer needs one B200 or H100-class GPU, run by the task owner.
- **Repos to merge.** prime-rl, verifiers, toploc, Stoa (worker pattern, delta compression), and the Hub's environment format.
- **Time to MVP: 8–12 weeks [est].** The integration surface is large: trainer, rollout workers, proofs and settlement.
- **Revenue.** Environment-authoring bounties are the only demand with real dollars (PI), and PI already runs them centrally. A protocol could become a payout and escrow rail for third-party-sponsored environment bounties [est].
- **Risks.**
  - Prime Intellect's network effects.
  - Reward-hackable rubrics.
  - The policy trainer is a centralized party anyway.
  - Bittensor RL subnets show instability (Reliquary stopped, Affine using unpublished scoring).

### Gaps
- No current (2026) official PI bounty list or payout totals were found.

---

## 4. Collaborative pretraining of one small model (DiLoCo/SparseLoCo plus Gauntlet scoring)

### Takeaway
This is technically proven at 72B (Covenant) and 8.6B on consumer GPUs (Pluralis Agora). It is the closest heir of the original D-PoDL vision but the worst fit for a 1–2 person part-time team: heavy hardware, long runs, and incumbents (SN3 Teutonic, SN9 IOTA, Psyche, Pluralis).

### Cited Findings
- **Covenant-72B.** At least 70 permissionless peers, each 8×B200; SparseLoCo with more than 146× compression; Gauntlet LossScore scoring. — [arXiv 2603.08163](https://arxiv.org/html/2603.08163v2)
- **Pluralis Agora.** An 8.6B model on 500B tokens over 40 days, 330 mostly consumer nodes, 63% of centralized token efficiency. — [arXiv 2607.13332](https://arxiv.org/abs/2607.13332)
- **Decoupled DiLoCo (April 2026).** Asynchronous quorum merge. — [arXiv 2604.21428](https://arxiv.org/abs/2604.21428)
- **Incumbents (2026-11-05 directory).** SN3 is now "Teutonic: compete to train one shared 110B model; seven competitions with kings". SN9 IOTA does distributed pretraining. SN100 Cortex is burning all incentive. SN47 GPUForge, "verifiable GPU training design", is quiet with no software. — [doctensor](https://doctensor.github.io/bittensor-docs/) (secondary)
- **Status of Templar.** The Templar README says its protocol is "not currently active". — [one-covenant/templar](https://github.com/one-covenant/templar)

### Inferences
- **Useful work and verification.** The work is a pseudo-gradient. Validators verify it with a Gauntlet LossScore (one forward/eval per miner per round, a few percent of the miner's inner-loop compute [est]), plus optional bisection disputes.
- **Minimum compute.**
  - A credible run needs 8×H100/B200 per peer (Covenant) or many 16–24 GB consumer nodes with pipeline parallelism (Agora/IOTA).
  - A toy 124M–1B DiLoCo testnet runs on 4–16 rented RTX 5090s at about $200/day (from the earlier report).
- **Repos to merge.** torchft (DiLoCo/Streaming DiLoCo), Templar Gauntlet (MIT), and the SparseLoCo code.
- **Time to MVP: 4–6 months [est]** for a toy testnet.
- **Revenue.** None. Grants are possible but compete with funded teams.
- **Publications.** Only if paired with novel verification, for example OVIG-style replay disputes.
- **Risks.** Hardware cost, incumbents, and the field's business fragility (Templar dormant, Gensyn's training paused, PI pivoted).

### Gaps
- Teutonic's current mechanism and traction were not checked against a primary source.

---

## 5. Adapter / LoRA / expert contribution market with merging (data-owner-controlled experts)

### Takeaway
This direction maps D-PoDL's MTX "model referencing" onto 2025–26 modular training: FlexOlmo, FlexMoRE, BTX and MergeKit. Verification is cheap (re-apply the adapter, evaluate on a secret set, test whether a merge beats its parents), and miners can use consumer GPUs. The data-owner angle (opt-in/opt-out experts) gives it a unique story for licensing and compliance. One Bittensor incumbent exists (SN102 Connito).

### Cited Findings
- **FlexOlmo (Ai2, July 2025).** Data owners train experts against a shared public model and can switch them on or off. — [arXiv 2507.07024](https://arxiv.org/html/2507.07024v4)
- **FlexMoRE (July 2026).** Low-rank experts beat full experts with under a third of the parameters. — [Ai2 blog](https://allenai.org/blog/flexmore)
- **Merging tools.** BTX ([arXiv 2403.07816](https://arxiv.org/abs/2403.07816)); MergeKit with TIES/DARE ([mergekit](https://github.com/arcee-ai/mergekit)).
- **Incumbent.** SN102 Connito, "train small expert add-ons beside a frozen Qwen3.6", Active, as of 2026-11-05. — [doctensor](https://doctensor.github.io/bittensor-docs/) (secondary)
- **Related precedent.** Nous/Macrocosmos fine-tuning subnets commit model hashes on chain before evaluation and delay pickup. — [finetuning-subnet](https://github.com/NousResearch/finetuning-subnet); [SN37 docs](https://docs.macrocosmos.ai/subnet-37-finetuning/subnet-37-incentive-mechanism)

### Inferences
- **Useful work and verification.** The work is an adapter or expert (tens to hundreds of MB) against a known base hash. Validators verify it as follows:
  1. Load the adapter and evaluate it on a secret, rotating domain set in minutes on one GPU.
  2. Run the merge test: does merge(top-k) beat each parent?
  3. Check that the expert does not degrade general benchmarks.
  Verification costs minutes against hours of training, under 5% [est].
  - Lineage royalties can follow merge contribution, for example leave-one-out deltas.
- **Minimum compute.** Miners can use a 24 GB consumer GPU for LoRA on a 1–8B base. Validators need one 24–80 GB GPU.
- **Repos to merge.** FlexOlmo code, MergeKit, PEFT, and the existing signed safetensors manifest, which needs the base-hash field added.
- **Time to MVP: 8–12 weeks [est].**
- **Revenue and funding.** This is the most plausible business story among the training directions: data owners (publishers, enterprises) contribute experts without giving up data and earn per-use royalties. That links to AI Act training-content transparency (section 15). Publication potential is good, since an "incentive-compatible modular training market" has no published protocol that I found [est].
- **Risks.**
  - Domain eval sets get gamed.
  - Copying, via fine-tuning someone else's adapter. This needs Gauntlet-style assigned-data tests or activation fingerprints.
  - Merges are fragile across many experts.
  - Base-model licence terms.

### Gaps
- Connito's mechanism and traction are unverified (secondary only).
- No 2026 data on data-owner willingness to contribute experts for royalties.

---

## 6. Data curation / dataset market (DataComp-style; synthetic data verified by TOPLOC)

### Takeaway
The demand is real: data quality is the main lever in DCLM. Verification is the problem. Scoring a curated dataset requires a proxy training run, so verification costs as much as or more than the work. No 2026 DataComp-LM edition or NeurIPS 2026 data-filtering competition was found. The workable sub-variant is verifier-backed synthetic data (each item carries a checker), where TOPLOC proves generation and the checker proves correctness.

### Cited Findings
- **DataComp-LM.** Participants submit training sets or curation algorithms, which are trained with a fixed recipe at 412M–7B and scored on 53 tasks. No 2026 edition was found. — [arXiv 2406.11794](https://arxiv.org/html/2406.11794v2)
- **SYNTHETIC-2 (2025).** About 4M verified reasoning traces, with distributed generation checked by TOPLOC v2. Figures conflict with the HF card's 354k examples. — [Prime Intellect](https://primeintellect.ai/blog/synthetic-2-release)
- **Provenance over detection.** Contamination detectors solved only 60% of challenges. — [arXiv 2606.03305](https://arxiv.org/pdf/2606.03305)
- **Bittensor data subnets (2026-11-05 directory).**
  - SN13 Data Universe: scraping, with 71% of incentive going to the owner UID.
  - SN91 Cascade: synthetic time-series generators.
  - SN54 Yanez: synthetic face and voice data.
  - SN111 Claims: science papers turned into evidence-linked claims; 90% goes to the operator wallet.
  - SN125 Refinery: "data refiners". — [doctensor](https://doctensor.github.io/bittensor-docs/) (secondary)

### Inferences
- **Useful work and verification.** Two variants:
  - Curation algorithms: verified by a proxy model trained on the filtered subset. Verification costs about 1× or more of the work, and noise is high [est].
  - Synthetic verified items: verified by a checker plus TOPLOC plus dedup and novelty checks. This is cheap.
- **Minimum compute.** Curation miners need only CPUs. Validators need 8×H100-hours per proxy run at 400M scale [est]. Synthetic-data miners need a consumer GPU.
- **Time to MVP: 8–12 weeks [est].**
- **Revenue and publications.** Revenue is moderate, because data buyers exist but want licences and provenance, not tokens. Publication potential is good: "proxy-training verification of data contributions with incentive guarantees" [est].
- **Risks.**
  - Expensive, noisy verification.
  - Proxy-to-scale transfer failures.
  - Licensing and copyright liability for scraped data, which is an EU AI Act Art. 53 summary issue.

### Gaps
- Whether DCLM or DataComp ran any 2025–26 competition track is unconfirmed.

---

## 7. Evaluation / benchmark market with secret test sets (commit-reveal, dynamic, contamination-resistant)

### Takeaway
This direction is a natural reuse of D-PoDL's TaskRegistry and the paper's publisher-held test sets. Its contracts are simple: commit to the test hash, models commit, then reveal. It serves as both a product (private leaderboards) and a building block for every other direction. Verifying that benchmark items are good is still unsolved, and in 2026 incumbents mostly run centralized evaluations.

### Cited Findings
- **Contamination audit.** Detectors solved 60% of challenges, and the authors conclude provenance must replace detection. — [arXiv 2606.03305](https://arxiv.org/pdf/2606.03305)
- **On-chain commit-before-eval precedents.** Nous finetuning subnet: on-chain hash and timestamp before evaluation. SN37: delayed pickup. — [finetuning-subnet](https://github.com/NousResearch/finetuning-subnet); [SN37](https://docs.macrocosmos.ai/subnet-37-finetuning/subnet-37-incentive-mechanism)
- **Procedurally generated items.** Distil SN97 builds about half its score weight from 11 procedurally generated axes "built from the block seed, so no two rounds share items". — [unarbos/distil](https://github.com/unarbos/distil)
- **Bittensor evaluation subnets.** SN98 NeverPlayAlone (NPA-Bench Minecraft agents), SN118 Ditto (agent-memory bench and test-case generators), SN70 Fugal (benchmarks run in Intel TDX). — [doctensor](https://doctensor.github.io/bittensor-docs/) (secondary)
- **Gensyn Judge.** Verde in production as an evaluation product since Aug–Sep 2025. — [Miraheze wiki: Verde](https://ai.miraheze.org/wiki/Verde) (secondary, from earlier notes)
- **Agent benchmarks are contestable.** Aggregator rankings for kernel benchmarks conflict across sites, showing demand for trusted, reproducible evaluation. — [benchlm](https://benchlm.ai/benchmarks/kernelbenchhard); [benchmarklist](https://benchmarklist.com/benchmarks/kernelbench_hard/) (secondary)

### Inferences
- **Useful work and verification.** There are two kinds of work.
  - Running models on the secret set is cheap and verified by TOPLOC or re-execution.
  - Authoring new hard, verifiable test items is valuable but hard to verify. Options:
    - Validator-run model panels check difficulty and discrimination.
    - Item-response-theory calibration.
    - Novelty hashing against public corpora.
    - Commit-reveal with post-deadline beacon sampling of which items count.
- **Minimum compute.** Item authors can use a laptop. Validators need one GPU for small-model panels, or API budgets.
- **Time to MVP: 6–10 weeks [est].** TaskEscrow plus commit-reveal plus a beacon-sampled eval slice.
- **Revenue.** Labs and enterprises want trusted private evals, but trust comes from reputation (Scale SEAL, Epoch, METR), not tokens. A protocol can sell "verifiable non-leakage", meaning auditable commitments [est].
- **Publications.** Good: "commit-reveal benchmarks with incentive-compatible item authoring".
- **Risks.** Leakage on reveal (each item can be used once), low-quality items, judge-based scoring manipulation, and low willingness to pay.

### Gaps
- The status of 2026 private-leaderboard services (Scale SEAL and others) was not re-checked.

---

## 8. Verifiable inference marketplace (TOPLOC, batch-invariant kernels, proof of logits)

### Takeaway
The technology is ready: TOPLOC, deterministic SGLang at about 34% slowdown, and Gensyn REE. The market is the most crowded of all: Ambient, Chutes (SN64), Targon (SN4), SN28, SN46, SN53, SN95, Gensyn, io.net and others. A small team has no edge. Use the techniques as building blocks, not as the product.

### Cited Findings
- **TOPLOC.** See section 3. — [arXiv 2501.16007](https://arxiv.org/abs/2501.16007)
- **Deterministic inference.** Bitwise-deterministic inference on a pinned SGLang stack costs about 34% slowdown (2025-09-22). — [LMSYS](https://www.lmsys.org/blog/2025-09-22-sglang-deterministic/)
- **[bg] Thinking Machines "Defeating Nondeterminism in LLM Inference" (Sep 2025).** Batch-invariant kernels. — [thinkingmachines.ai](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)
- **Gensyn REE v0.8.0 (2026-10-05).** Reproducible inference only; proprietary operator binaries. — [gensyn-ai/ree](https://github.com/gensyn-ai/ree)
- **Ambient (proof of logits).** An inference-only, unaudited PoUW L1. — [Ambient docs](https://ambient.xyz/docs/learn/proof-of-logits)
- **Crowded Bittensor inference subnets (2026-11-05).**
  - SN64 Chutes: serverless inference on confidential GPUs.
  - SN4 Targon: attested GPU servers.
  - SN28: TEE LLM resale.
  - SN46: fast uncensored serving.
  - SN53: billed inference.
  - SN95: private inference. — [doctensor](https://doctensor.github.io/bittensor-docs/) (secondary)
- **TEE.fail.** A DDR5 interposer under $1,000 forges TDX quotes. — [tee.fail](https://tee.fail/)

### Inferences
- **Useful work and verification.** The work is serving tokens. Verification uses TOPLOC proofs with spot-check re-prefill (about 1–10% overhead [est]) or deterministic replay.
- **Minimum compute.** 24 GB consumer GPUs for small models; H100 for anything sellable.
- **Time to MVP: 8–12 weeks [est].**
- **Revenue.** In principle the largest market, since inference is where on-chain AI revenue exists. A new entrant faces price competition from funded networks and centralized APIs.
- **Risks.** Commoditization, TEE breakage, no differentiation.
- **Recommendation [est].** Treat this as a component: verify evaluation outputs and rollouts in other directions.

### Gaps
- Ambient mainnet status as of November 2026 is unconfirmed (from earlier notes).

---

## 9. Distillation / compression market (distill a large open model into small ones, scored on held-out tasks)

### Takeaway
This is already a live Bittensor category with a fully specified open-source mechanism: Distil, Kimi-K2.6 teacher, KL plus procedural axes, king-of-the-hill, MIT licence. That is excellent reference material but means no open niche. Validators need 8×H100/H200 to serve the teacher.

### Cited Findings
- **Distil (SN97 per its repo).**
  - Teacher: Kimi-K2.6 (about 1T total, 32B active, INT4), switched in on 2026-05-02. Students are capped at 33B with the teacher's tokenizer.
  - Score = 0.75 × worst-3 mean + 0.25 × weighted mean over 25+ axes: on-policy reverse KL (0.30), top-k overlap (0.18), plus 11 block-seeded procedural axes.
  - KL above 2.0 disqualifies. A challenger must beat the king by 5%, and the winner takes all.
  - Anti-copy rules: SHA256 duplicates are disqualified and activation-fingerprint cosine above 0.99999 is flagged.
  - Validators need 8×H200/H100. Students typically train on 4–8×H100; LoRA fits smaller setups.
  - MIT licence. — [unarbos/distil](https://github.com/unarbos/distil)
  - A tao.media profile is titled "The Subnet an AI Agent Built: Inside Distil (SN97)". — [tao.media](https://www.tao.media/the-subnet-an-ai-agent-built-inside-distil-sn97/) (secondary)
- **Conflict.** The 2026-11-05 doctensor directory lists SN97 as "Ingot: quantize Qwen3.8-27B to 1.75 bits; closest copy wins", not Distil. Either the netuid changed hands or one source is stale. — [doctensor](https://doctensor.github.io/bittensor-docs/) (secondary)
- **Other compression subnets.** SN65 TPN (shrink LMs under a memory cap, checked by KL), SN40 Ralph (low-bit GGUF of Qwen3-8B), SN44 Score (claims a 19 MB vision model beat frontier models on UA-DETRAC; promotional). — [doctensor](https://doctensor.github.io/bittensor-docs/); [Genfinity, 2026-06-18](https://genfinity.io/2026/06/18/bittensor-subnet-44-score-sn44-19mb-vision-model-beats-frontier-ai/) (secondary)
- **Distillation compute efficiency.** — [arXiv 2602.20164](https://arxiv.org/abs/2602.20164v1); [bg] Minitron, [arXiv 2407.14679](https://arxiv.org/abs/2407.14679)

### Inferences
- **Useful work and verification.** The work is a student checkpoint. Validators compute KL against the teacher's top-k logprobs on beacon-seeded prompts (300 per UID in Distil) plus procedural tasks. Validator cost per submission is about 1 GPU-hour on 8×H200 [est], against days of student training.
- **Minimum compute.** A small-teacher variant fits consumer hardware: for example an 8B teacher with sub-1B students on a 24 GB GPU [est]. The frontier variant needs datacenter GPUs.
- **Time to MVP: 6–10 weeks [est]** by porting Distil's scoring.
- **Revenue.** Modest; there is demand for small on-device models.
- **Publications.** Moderate.
- **Risks.** Incumbents, teacher licence terms, and overfitting to procedural generators.

### Gaps
- The SN97 netuid conflict is unresolved. No traction metrics for Distil.

---

## 10. Formal math / theorem proving (Lean proofs as perfectly verifiable useful work)

### Takeaway
2026 made this real. Erdős problems are falling to LLM-plus-Lean loops at "a few hundred dollars per solved problem" (AlphaProof Nexus, *Science*, 2026-10-08). The Lean kernel check is the closest thing to a perfect PoUW verifier: CPU-only, seconds, deterministic. A Bittensor subnet (SN66 Conjectures.io) already pays TAO bounties for Lean proofs of DeepMind formal-conjectures statements. Two caveats: Lean checks only the formal statement, not whether it matches the intended problem; and frontier labs capture the hardest wins.

### Cited Findings
- **AlphaProof Nexus (DeepMind).**
  - Preprint 2026-05-21; *Science* 2026-10-08.
  - Gemini 3.1 Pro plus Lean solved 9 of 353 open Erdős problems attempted (two open for 56 years) and proved 44 of 492 OEIS conjectures.
  - A simple LLM-plus-Lean loop replicated the Erdős successes, at higher cost on the hardest problems.
  - Inference cost was "a few hundred dollars per solved problem".
  - Proofs are public at github.com/google-deepmind/alphaproof-nexus-results. — [aiweekly](https://aiweekly.co/alerts/deepmind-alphaproof-nexus-solves-9-erds-problems); [pulse.bot](https://www.pulse.bot/ai/news/google-deepminds-alphaproof-nexus-solves-decades-old-math-problems-for-a-few-hundred-dollars-f5f2d6b8-1bcc-4641-84ff-3be40c9cbaad/); [arXiv 2605.22763](https://arxiv.org/html/2605.22763v1) (secondary coverage of the primary paper)
  - Commentators note that Lean "does not independently decide whether those assumptions match the intended Erdős problem". — [remio.ai](https://www.remio.ai/post/alphaproof-nexus-erdos-problems-reach-peer-review-but-nine-of-353-is-the-real-st) (secondary)
- **Quanta (2026-08-03) timeline.**
  - GPT-5.2 Pro solved Erdős #728 on 2026-01-04, certified with Harmonic's Aristotle.
  - In January 2026 a DeepMind team evaluated 700 open problems with Gemini, solving 4 and finding old solutions to 9.
  - In May 2026 DeepMind's agent solved 9 of 353.
  - On 2026-05-20 OpenAI's internal model found a counterexample to the 1946 unit-distance conjecture.
  - On 2026-08-01 OpenAI's unreleased "Astra" made 10 advances, including three Erdős problems.
  - Bloom's database listed 565 solved and 652 open problems.
  - Erdős's original cash prizes ($10 to thousands) are honoured by a foundation. — [Quanta](https://www.quantamagazine.org/why-the-legendary-erdos-problems-are-falling-to-ai-20260803/)
  - Search summaries also report about 722 OpenAI manuscripts posted in October, not all Lean-validated. — secondary, unverified
- **Formalization infrastructure.** An August 2026 preprint gives a kernel-checked exclusion certificate for Erdős #647 ([arXiv 2608.17880](https://arxiv.org/pdf/2608.17880)). LeanMarathon does long-horizon autoformalization, covering four Erdős problems with no `sorry` ([arXiv 2606.05400](https://arxiv.org/pdf/2606.05400)). "OEIS Open" measures how many conjectures LLMs can turn into theorems ([arXiv 2608.11941](https://arxiv.org/pdf/2608.11941)). DeepMind's formal-conjectures is a Lean 4 plus mathlib collection of open conjecture statements ([github](https://github.com/google-deepmind/formal-conjectures)).
- **Incumbent: Bittensor SN66 Conjectures.io.** It pays TAO bounties for machine-verified proofs or counterexamples to open conjectures from DeepMind's formal-conjectures. Acceptance is a deterministic Lean kernel check, with a shared pool for proofs and counterexamples. The site claims two long-standing conjectures were disproved by AI-assisted counterexample search in July 2026. — [subnetalpha.ai](https://subnetalpha.ai/subnet/conjectures/) (secondary; the page warns its data may be out of date)
- **[bg] Earlier provers and funders.** DeepSeek-Prover-V2 (Apr 2025, [arXiv 2504.21801](https://arxiv.org/abs/2504.21801)); ByteDance Seed-Prover (Jul 2025, [arXiv 2507.23726](https://arxiv.org/abs/2507.23726)); Harmonic Aristotle (IMO 2025 gold-level, formal). Funding precedent: the Renaissance Philanthropy and XTX Markets "AI for Math Fund" (launched Dec 2024, about $9.2M) — [renaissancephilanthropy.org](https://www.renaissancephilanthropy.org/ai-for-math-fund).

### Inferences
- **Useful work and verification.** The work is a Lean proof or counterexample for a published formal statement. Verification is `lake build` plus a kernel check on CPU, seconds to minutes, against hundreds of dollars of inference per solve. The ratio is about 10⁻⁴ or lower [est], the best of any direction.
  - The protocol must handle three things:
    1. **Front-running.** A proof visible in the mempool can be copied. This needs commit-reveal: hash the proof first, reveal after inclusion. The MTX mempool idea fits here.
    2. **Statement fidelity.** Only curated or committee-reviewed formal statements should carry bounties, with a challenge window for "statement does not match problem" claims.
    3. **Axiom and `sorry` hygiene.** Pinned Lean and mathlib versions, an axiom whitelist, and checks such as the comparator or "lean4checker".
- **Minimum compute.** CPU for verification. Miners need LLM API budgets, or a local open prover (DeepSeek-Prover-V2-7B on a 24 GB GPU [est]).
- **Repos to merge.** formal-conjectures (statements), the alphaproof-nexus-results format, Lean 4 and mathlib, and the existing escrow and commit-reveal contracts.
- **Time to MVP: 3–6 weeks [est].** No ML training stack is required.
- **Revenue and funding.** Grants from AI-for-math funds and possibly sponsor-funded bounties; publication potential is high. Direct revenue is low.
- **Risks.**
  - SN66 incumbent.
  - Frontier labs mine the best problems first, so the "low-hanging fruit" depletes.
  - Formalization-fidelity disputes.
  - It is not deep-learning work, so it dilutes the PoDL identity. It is still the best testbed for the commit-reveal, escrow and dispute contracts.

### Gaps
- SN66's primary docs, emissions and solve counts were not verified.
- The OpenAI "722 manuscripts" figure is unverified.
- Erdős-prize foundation payouts for AI-solved problems: none found.

---

## 11. Scientific discovery with cheap automatic evaluators (AlphaEvolve/FunSearch-style optimization: packings, bounds, constructions, SAT/combinatorics)

### Takeaway
AlphaEvolve-style problems have deterministic evaluators that score a candidate construction in seconds. Open-source engines exist (OpenEvolve, ShinkaEvolve, ThetaEvolve, SkyDiscover), and small open models can now set new best-known bounds. I found no market paying for these. Only adjacent Bittensor subnets exist (SN83 CliqueAI max-clique, SN63 Enigma RSA/quantum challenges). This is the cheapest-to-verify open niche and a good proving ground for the contracts.

### Cited Findings
- **AlphaEvolve math paper ("Mathematical exploration and discovery at scale", Nov 2025).** 67 open problems; reproduces most known optima and improves some (packings, spherical t-designs). — [arXiv 2511.02864](https://arxiv.org/abs/2511.02864)
- **ThetaEvolve.** A small open model reaches new best-known bounds, for example circle packing. — [arXiv 2511.23473](https://ar5iv.labs.arxiv.org/html/2511.23473)
- **ImprovEvolve (Feb 2026).** New state of the art for hexagon packing at n = 11, 12, 15, 16. — [arXiv 2602.10233](https://arxiv.org/abs/2602.10233)
- **"Even with AI, Bijection Discovery is Still Hard" (2026).** OpenEvolve on Dyck-path bijections; the open case was not cracked. — (search summary; see [arXiv 2603.15617](https://arxiv.org/html/2603.15617) for the HorizonMath context)
- **HorizonMath (Mar 2026).** Notes that test-time-training approaches set new state of the art on Erdős's minimum-overlap problem and an autocorrelation inequality. — [arXiv 2603.15617](https://arxiv.org/html/2603.15617)
- **Open engines.** OpenEvolve (May 2025, Apache-2.0) — [HF blog](https://huggingface.co/blog/codelion/openevolve); ShinkaEvolve (Sep 2025) — [arXiv 2509.19349](https://arxiv.org/html/2509.19349v1); SkyDiscover (Mar 2026, self-reported gains on 172 Frontier-CS problems) — [blog](https://skydiscover-ai.github.io/blog.html)
- **Adjacent incumbents.** SN83 CliqueAI ("return maximum cliques for team graphs") and SN63 Enigma ("RSA or quantum-circuit prize challenges"). — [doctensor](https://doctensor.github.io/bittensor-docs/) (secondary)
- **[bg] FunSearch (DeepMind, Nature, Dec 2023).** Cap-set and bin-packing heuristics. — [Nature](https://www.nature.com/articles/s41586-023-06924-6)

### Inferences
- **Useful work and verification.** The work is a construction or program that beats the current best-known score on a published evaluator. Verification means running the evaluator in seconds on CPU or GPU, with a ratio of about 10⁻³–10⁻⁵ [est]. Records stack naturally, so new constructions start from the previous best, which suits D-PoDL lineage royalties.
- **Minimum compute.** CPU or consumer GPU plus LLM API, or a local small model as in ThetaEvolve.
- **Repos to merge.** OpenEvolve or ShinkaEvolve (reference miner), AlphaEvolve's published problem list and evaluators, the HorizonMath problem set, and SAT-competition and MiniZinc instance libraries for an "optimization" track.
- **Time to MVP: 3–6 weeks [est].**
- **Revenue and publications.** Revenue is low, mainly grants. Publication potential is good: "an open, incentivized AlphaEvolve with on-chain record lineage".
- **Risks.**
  - Many problems saturate quickly.
  - Value is aesthetic or mathematical rather than economic.
  - Evaluator bugs are exploitable, as with kernels.
  - Industrial optimization tracks (scheduling, logistics) need sponsors with private instances, which reintroduces secret test sets.

### Gaps
- No 2026 AlphaEvolve public-API status or new DeepMind results were verified this session.

---

## 12. Protein / molecule design scored by folding and affinity models (optional wet-lab ground truth)

### Takeaway
2026 binder-design competitions (Adaptyv × partners) show high-quality crowdsourced plus AI design with real wet-lab validation. AI-run campaigns are reportedly reaching high hit rates. In-silico scoring (AlphaFold/Boltz-type confidence) is cheap but hackable, and true verification costs wet-lab money and weeks. Bittensor SN68 NOVA already runs a molecule and antibody scoring subnet.

### Cited Findings
- **Adaptyv 2026 competitions.**
  - Nipah glycoprotein, results 2026-01-21: 1,200 proteins experimentally validated, 99 novel binders, 26 single-digit-nM or better.
  - TREM2 (BioArena × Adaptyv), results 2026-03-28: an 80% hit rate reported against 38.3% for human entrants.
  - RBX1 (GEM × Adaptyv), results 2026-04-26: best affinity reportedly improved from 25.7 nM to 3.9 nM in an Anthropic-run campaign.
  — (search summary of Adaptyv/Proteinbase posts; the official pages were not fetched) [Adaptyv Substack](https://adaptyvbio.substack.com/p/protein-design-competition-results)
  - An August 2026 report on an Anthropic-run campaign gives 1,320 designs and 354 binders across 15 targets. — [oncodaily](https://oncodaily.com/technology/anthropic570775) (secondary)
- **2024 EGFR competition.** Cradle's winner reached 1.21 nM, against cetuximab's 9.94 nM. — [biopharmatrend](https://biopharmatrend.com/post/1059-cradle-achieves-8x-improved-egfr-binding-over-mercks-cetuximab-in-protein-design-challenge); [bioRxiv lessons paper](https://www.biorxiv.org/content/10.1101/2025.04.17.648362.full.pdf)
- **Incumbents.** SN68 NOVA ("design molecules and antibodies scored as binders; search-code contest", Active). SN55 NIOME (CRISPR constructs, restarted 2026-11-05). SN107 Minos (genomics configs). — [doctensor](https://doctensor.github.io/bittensor-docs/) (secondary)

### Inferences
- **Useful work and verification.**
  - The work is a sequence or design.
  - Validators score it in silico with folding or affinity predictors in GPU-minutes per design. This is cheap but gameable by adversarial sequences.
  - Ground truth is the wet lab: about $100s per design and 2–4 weeks [est; Adaptyv pricing not verified].
  - A sound protocol uses in-silico scoring to shortlist, then a sponsor-funded wet-lab batch as the final verifier, with payouts delayed accordingly.
- **Minimum compute.** One 24–80 GB GPU for the validator's folding model. Miners need consumer GPUs.
- **Time to MVP: 6–10 weeks [est]** for in silico only.
- **Revenue.** Biotech sponsors pay for binders, and this is the most "real-economy" useful work. Adaptyv already intermediates.
- **Risks.**
  - Biosecurity screening obligations.
  - Expensive, slow ground truth.
  - Domain expertise the team may lack.
  - Weak fit with D-PoDL.

### Gaps
- Adaptyv official 2026 leaderboards and per-design assay prices were not fetched.

---

## 13. Hidden-test code-agent and agent-task bounties (SWE, security audit, red-teaming)

### Takeaway
This direction generalizes autoresearch to any task with hidden tests. It is very crowded on Bittensor:
- SN62 Ridges: SWE agents on hidden tests.
- SN76 Ormas: GitHub tasks paid if client tests pass.
- SN5 Hone.
- SN60 Bitsec: smart-contract bug hunting.
- SN23 Trishool: jailbreaks against guard models.
- SN67 Harnyx: deep-research agents.

It is included for completeness, but there is little room for a small entrant.

### Cited Findings
- **Subnet listings (2026-11-05).** SN62 Ridges "build software-engineering agents scored on hidden tests", SN76 Ormas "bid on GitHub coding tasks; paid if client tests pass", SN60 Bitsec "hunt smart-contract bugs with AI agents", SN23 Trishool "write jailbreaks against guard models" (Transitioning; 80% of miner emission burned), and SN87 Provenonce "verify agentic work" (Transitioning; no paid mainnet miner). — [doctensor](https://doctensor.github.io/bittensor-docs/) (secondary)

### Inferences
- **Useful work and verification.** The work is a patch or agent harness. Validators run hidden tests, at a cost of minutes against hours of work.
- **Minimum compute.** Laptop plus API.
- **Time to MVP: 4–8 weeks [est].**
- **Revenue.** Real but competitive (bug bounties, client tasks).
- **Risks.** Saturated, and the fit with PoDL is weak.

### Gaps
- No traction or emission numbers for these subnets were retrieved.

---

## 14. Research-grade artifact only: open reference implementation plus paper ("D-PoDL revisited under agent miners")

### Takeaway
This is still the highest-certainty payoff for the team. The 2026-11-05 subnet landscape actually strengthens the case: there are now dozens of live "useful-work" mechanisms with unpublished or ad hoc scoring rules. Affine pays "by an unpublished team scoring rule" since 2026-10-20; several subnets burn 70–98% of emissions or route them to owners. None has a published threat model or security-budget analysis answering the 2025 PoUW SoK. A cross-task formal treatment and open reference implementation fills a gap the field has.

### Cited Findings
- **The SoK's demands.** "SoK: Is PoUW Really Useful?" (ePrint 2025/1814) recommends verifiable computation, partial incentive allocation and utility-aware difficulty. — [ePrint 2025/1814](https://eprint.iacr.org/2025/1814)
- **The formal question is open.** A formal security game for ML-work consensus is "an open research problem" (June 2026). — [arXiv 2606.24942](https://arxiv.org/abs/2606.24942)
- **Ad hoc subnet economics (2026-11-05).**
  - SN120 "since 2026-10-20 pay follows an unpublished team scoring rule".
  - SN30 "owner burns 98% of miner reward".
  - SN13 "71% of incentive to owner UID".
  - SN111 "90% to operator wallet".
  - SN37 "champion only, after 70% burn". — [doctensor](https://doctensor.github.io/bittensor-docs/) (secondary)
- **Verification readiness.** A June 2026 paper argues ZK verification of frontier training is possible. It estimates a deployable proof of concept about 36 months away at single-digit training overhead, and notes that compliance "rests on self-reporting" today. — [arXiv 2606.05433](https://arxiv.org/abs/2606.05433)

### Inferences
- **Deliverable.** A paper plus repo: "a task-agnostic commit / re-measure / challenge / settle protocol for verified useful AI work, with lineage royalties". It would be instantiated on three task types of increasing verification cost: Lean or AlphaEvolve-style problems (exact, CPU), the kernel or autoresearch speedrun (noisy, GPU, multi-seed), and adapter merging (statistical). It would include adversarial tests: copying, grinding, PoL spoofing, front-running, publisher collusion and evaluator hacking, the last illustrated by KernelBench-Verified's 374× ReLU hack.
- **Minimum compute.** 2–16 rented GPUs for red-team days (about $200/day for 16× RTX 5090, from the earlier report).
- **Time to MVP: 3–6 months [est]** to a submission-ready paper.
- **Revenue.** Grants (Ethereum Foundation ESP, crypto-research foundations, AI-for-math and AI-safety funders); no direct revenue.
- **Risks.** It may be scooped by a better-funded team, and its value depends on rigour.

### Gaps
- No search was run for 2026 papers proposing exactly a cross-task useful-work protocol. One may exist.

---

## 15. Model provenance / attribution registry for weights (C2PA-like, OMS signatures plus on-chain lineage)

### Takeaway
The existing signed-safetensors-manifest code is one step from compatibility with OpenSSF Model Signing (OMS, v1.0 April 2025), which NVIDIA NGC uses and Kaggle is prototyping. Hugging Face adoption was not found. The gap OMS leaves open is lineage: "this model was derived from these parents by this process", backed by commitments rather than self-reports. D-PoDL's MTX referencing graph is exactly that. The registry is cheap to build, but signatures prove authorship claims, not training truth.

### Cited Findings
- **OMS status.** OpenSSF formalized OMS as an implementation-agnostic model-signing standard. The Model Signing library and CLI reached v1.0 in April 2025. NVIDIA has signed all NGC models with OMS since March 2025, and Google is prototyping it on the Kaggle Model Hub. Signing events go to the Sigstore transparency log. The OpenSSF AI/ML WG is working with the Coalition for Secure AI to add metadata such as training data sources and model version. — [OpenSSF OMS](https://openssf.org/?p=8454); [HiddenLayer](https://hiddenlayer.com/insight/openssf-model-signing-for-safer-ai-supply-chains)
- **No Hugging Face adoption found.** A July 2026 blog argues that signing machinery had rarely been applied to model files and cites only the NGC and Kaggle deployments. — [tianpan.co, 2026-07-02](https://tianpan.co/blog/2026/07/02/sign-your-weights) (opinion)
- **The repo's manifest flaw.** The current manifest signature does not cover the `files` section, so the CID can be swapped. — earlier report, [ipfs_utils.py:559-622](../../dpodl_core/ipfs_utils.py)

### Inferences
- **Product.** OMS-compatible signing, plus an on-chain lineage registry that maps a child hash to parent hashes, the process (merge, LoRA, distill) and committed training-trace roots, plus a verifier CLI. The Merkle-committed training traces become "training receipts".
- **Useful work and verification.** No mining. Verification is a signature and Merkle check at near-zero cost. Optionally, attestations can be upgraded: a "verified by re-measurement" badge when validators reproduced the eval, or a "dispute-survived" badge.
- **Minimum compute.** None.
- **Time to MVP: 3–5 weeks [est].**
- **Revenue.** Low as a standalone (OMS is free). As a component it is strong and it feeds direction 16.
- **Risks.** Standards bodies (OpenSSF, CoSAI, C2PA) may define lineage metadata without chains. Adoption is the problem.

### Gaps
- Whether C2PA has a 2026 spec for AI model weights (not only media) was not searched.
- The OMS 2026 roadmap was not checked.

---

## 16. Training-run notarization / evidence service for EU AI Act GPAI compliance

### Takeaway
The regulatory timing is real:
- GPAI obligations applied from 2025-08-02.
- Commission enforcement powers, with fines up to 3% of global turnover or €15M, apply from 2026-08-02.
- The July 2026 Digital Omnibus did not delay GPAI rules.
- The Commission's mandatory training-content summary template exists (2025-07-24).
- Legacy models must comply by 2027-08-02.

Nobody can technically verify training today ("compliance rests on self-reporting"), and no funded startup selling verifiable training attestations was found. A notary of Merkle-committed training logs, dataset manifests and signed checkpoints is a plausible B2B product. It is honest only as tamper-evident evidence, not proof of what happened. The buyers (GPAI providers, fine-tuners) are few, large and crypto-averse.

### Cited Findings
- **Enforcement start.** The Commission's AI Act page confirms that GPAI enforcement starts 2026-08-02. — [European Commission AI Act page](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai)
- **The Omnibus.** Sources describe it as Regulation (EU) 2026/1744, in force 2026-07-27. It defers high-risk obligations but not GPAI obligations. Article 101 fines: up to 3% or €15M. The AI Office can request technical documentation and evaluate models. — [Orrick, July 2026](https://www.orrick.com/en/Insights/2026/07/EU-AI-Act-Update-Digital-Omnibus-Finalizes-8-Compliance-Changes); [Mayer Brown, July 2026](https://www.mayerbrown.com/en/insights/publications/2026/07/eu-ai-act-news-digital-omnibus-on-ai-new-guidance-on-risk-classification-gpai-and-transparency-obligations); [DLA Piper](https://www.dlapiper.com/en/insights/publications/law-in-tech/2026/digital-omnibus-on-ai). Sources conflict on the Art. 50(2) watermarking date for legacy systems (2026-12-02 vs 2027-12-02).
- **Training-content summary template.**
  - Published 2025-07-24 and mandatory from 2025-08-02 under Art. 53(1)(d).
  - Three sections: general information, data sources (large datasets named individually), and data processing measures.
  - Web-scraped data needs crawler, period and top-domain details.
  - It covers open-source models too, and protects trade secrets. — [Commission](https://digital-strategy.ec.europa.eu/en/news/commission-presents-template-general-purpose-ai-model-providers-summarise-data-used-train-their); [WilmerHale](https://wilmerhale.com/en/insights/blogs/wilmerhale-privacy-and-cybersecurity-law/european-commission-releases-mandatory-template-for-public-disclosure-of-ai-training-data); [ZuniclAW](https://zuniclaw.com/en/?p=73331)
- **No technical verification today.** The "Zero knowledge verification for frontier AI training is possible" paper (June 2026) says governance relies on cumulative training compute thresholds but "enforcement rests on self-reporting". It proposes genesis, step and policy attestations, with a proof of concept about 36 months away. — [arXiv 2606.05433](https://arxiv.org/abs/2606.05433)
- **Adjacent prototypes.**
  - FLI and Mithril Security built a TPM-based "Secure AI Bill of Materials" proof of concept for fine-tuning provenance. — [FLI](https://futureoflife.org/ai/verifiable-training-of-ai-models/)
  - zk-plus-dataset-commitment LoRA fine-tuning proofs. — [arXiv 2510.16830](https://arxiv.org/pdf/2510.16830v1)
  - Small grant and hackathon projects: ProofChain on Sia, PureSapiens on Chainlink. — [Sia forum](https://forum.sia.tech/t/small-grant-proofchain/995); [Chainlink hack-26](https://chain.link/hack-26/projects/puresapiens)
  - No funded compliance-attestation startup was found.

### Inferences
- **Product.** A "training evidence ledger".
  - An SDK hooks into PyTorch, torchtitan or HF Trainer and emits per-k-step checkpoint hashes, dataset-shard manifests (FineWeb shard IDs, licences, crawl periods), config hashes and compute counters (FLOP estimates for the 10²⁵ systemic-risk threshold).
  - Merkle roots are anchored on an L2 or any timestamping service.
  - It auto-fills the Commission's training-content summary template and Annex XI-style documentation.
  - It offers optional auditor re-execution of sampled steps (the Verde/OVIG/Srivastava techniques from the earlier report) as a premium "spot-audit".
- **Useful work and verification.** There is no mining. Verification is hash consistency plus optional audits. The honest selling point is tamper evidence (logs cannot be back-dated) and a cheap path to auditability.
- **Minimum compute.** None for the notary; audits need GPUs matching the client's.
- **Time to MVP: 6–10 weeks [est]** for the SDK, anchor and template generator.
- **Revenue.** Plausibly the best non-crypto revenue path, as a SaaS for EU fine-tuners and downstream modifiers who become "providers". It needs legal partners. The blockchain is optional (RFC 3161 timestamps would do), which undercuts the token story.
- **Risks.**
  - Regulators may not value it, since the AI Office asks for documentation, not proofs.
  - Large providers build in-house; legal-tech incumbents (OneTrust-style platforms) have the sales channels.
  - Liability for misattested claims.
  - Rule changes.

### Gaps
- The Annex XI technical-documentation contents were not retrieved.
- No 2026 data on how many entities have filed training summaries or what the AI Office has requested.
- No check of whether the GPAI Code of Practice signatories use specific tooling.

---

## 17. Agent-economy payments (x402, AP2) for paying agent miners

### Takeaway
This is an enabler, not a standalone direction. x402 (HTTP 402 stablecoin payments, mostly on Base) has a Linux Foundation home (July 2026, 40+ members) and AWS Bedrock AgentCore support (May–August 2026). That makes "pay an AI-agent miner per verified result in USDC" a 1–2 week integration that avoids launching a token. Usage statistics are inflated by memecoin and self-dealing activity.

### Cited Findings
- **x402 governance and distribution.** The x402 Foundation was announced April 2026 and launched July 2026 with 40+ members. AWS added x402 to Bedrock AgentCore in May 2026, and AgentCore payments were generally available by August with an "upto" scheme for pay-per-inference. — [Concordium explainer](https://www.concordium.com/article/x402-explained-agentic-payments-identity); [agentlux](https://agentlux.ai/blog/the-agent-payments-showdown-x402-vs-ap2-vs-mpp-vs-acp-in-2026); [patechlabs](https://www.patechlabs.com/news/ai-agent-payments-guide-x402-ap2-mpp-visa-mastercard) (all secondary)
- **Volume figures conflict.**
  - About 75M transactions and $24M in 30-day volume (mid-July 2026, x402 dashboard per secondary).
  - About 161M cumulative and $43.6M settled (Feb 2026).
  - Chainalysis attributed much of the late-2025 surge to memecoins.
  - CoinDesk (March 2026) reported about $28k daily volume and much testing and self-dealing. — same secondary sources; [rzlt](https://www.rzlt.io/blog/agentic-payments-2026-x402-explainer)
- **AP2.** Google AP2 v0.2 (2026-04-28) added "Human Not Present" payments. It is positioned as a trust and authorization layer and has little public adoption data. — [patechlabs](https://www.patechlabs.com/news/ai-agent-payments-guide-x402-ap2-mpp-visa-mastercard) (secondary)
- **[bg]** Coinbase launched x402 in May 2025. — [x402.org](https://www.x402.org/)

### Inferences
- **Use.** Bounty settlement contracts pay USDC to an agent's wallet on settle. x402 can also gate the validator API, so miners pay a small anti-spam fee per submission, which replaces stake for low-value tasks. This removes the need for the DPDL token's economic role (testnet-only token or none), which aligns with the earlier report's no-new-token recommendation and the CLARITY Act failure (2026-09-15).
- **Time: 1–2 weeks [est].**
- **Risks.** Stablecoin regulatory exposure, and agents' wallets controlled by API operators.

### Gaps
- No primary x402.org dashboard numbers were fetched.

---

## 18. Distribution options: Bittensor subnet vs. own L2 contracts vs. integrating with an existing network

### Takeaway
This is a cross-cutting choice, not a direction. The 2026-11-05 subnet landscape shows Bittensor is where miners already are, across almost every task type here. It is also volatile: many subnets are "Transitioning" or burn most emissions, registration costs 225–435+ TAO, and teams leave (Covenant). Own contracts on Base or Arbitrum testnets cost nothing and keep the protocol design free. Gensyn's L2 (OP Stack, live 2026-04-22) and Psyche (Solana) host their own agendas, and Gensyn's training network is paused.

### Cited Findings
- **Subnet registration cost.** About 225–435 TAO in late October 2026, with spikes past 1,500. — [ownyourmind](https://ownyourmind.ai/projects/bittensor/); [CryptoBriefing](https://cryptobriefing.com/bittensor-subnet-registration-cost-rises/) (from the earlier report)
- **Volatility (2026-11-05 directory).** Statuses include SN20 ("one UID has taken all pay since 2026-10-03"), SN74 ("all miner emission recycled since 2026-10-12"), SN43 ("listed for sale") and SN100 ("all incentive burns"), plus many "Transitioning". — [doctensor](https://doctensor.github.io/bittensor-docs/) (secondary)
- **Gensyn.** L2 mainnet 2026-04-22, $AI token 2026-04-29, RL Swarm paused. — [Gensyn docs](https://docs.gensyn.ai/testnet)
- **Psyche.** Solana coordinator, permissioned runs. — [ownyourmind Nous](https://ownyourmind.ai/projects/nous-research/) (secondary)
- **EigenLayer.** Slashing has been live since 2025-04-17, giving an AVS path. — [EigenLabs](https://www.eigenlabs.org/blog/slashing-goes-live/)
- **L2 costs.** Base and Arbitrum transactions cost about $0.02–0.04. — [Eco](https://eco.com/support/en/articles/14798701-base-vs-arbitrum-which-l2-should-you-build-on)

### Inferences
- **Recommended sequence [est].**
  1. Own contracts on a Base or Arbitrum testnet with USDC/x402 or testnet-token payouts, for credibility and freedom to design disputes and royalties, which Yuma Consensus does not natively give.
  2. A Bittensor subnet only after the mechanism is proven and a funded partner covers registration.
  3. An EigenLayer AVS if restaked validators are wanted.
- Integrating with Gensyn or Psyche makes sense only as a verification-tech user (REE for inference), not as a host.

### Gaps
- Current subnet registration cost on 2026-11-05 was not re-queried.

---

## 19. Scored comparison matrix and portfolio implications

### Takeaway
On the stated criteria, the cheapest-verifier directions (Lean proofs, AlphaEvolve-style problems) and the asset-reusing directions (the research artifact, the provenance registry, the adapter market and the autoresearch flagship) score highest. Collaborative pretraining, verifiable inference and protein design score lowest for a 1–2 person part-time team. The best plan is one generic "frozen-verifier bounty engine" (escrow, commit-reveal, re-measure, challenge, settle, lineage royalties) that hosts several task types. Start with the cheapest-verifier task to harden the contracts in weeks. Then run the autoresearch or adapter-merge flagship. Ship provenance and notarization as the non-crypto spinoff.

### Cited Findings
- All scores below are the researcher's estimates [est], derived from the cited findings in sections 1–18. No external source scores these options.

### Inferences
**Criteria.** Each is scored 1–5, where 5 is best for this team.
- **V**: verification cheapness and robustness. Weight 2.
- **H**: hardware accessibility for miners and validators. Weight 1.
- **F**: fit with existing D-PoDL assets and identity (contracts, manifests, Merkle traces, lineage). Weight 1.5.
- **T**: speed to MVP for 1–2 part-time developers. Weight 1.5.
- **G**: competition gap (5 = open niche). Weight 1.5.
- **M**: revenue or funding potential. Weight 1.
- **P**: publication potential. Weight 1.
- **R**: low main-risk. Weight 1.

The maximum weighted score is 52.5. The last column normalizes to 100.

| # | Direction | V | H | F | T | G | M | P | R | Weighted (/52.5) | /100 | MVP time [est] | Min compute [est] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | Lean / formal-math proof bounties | 5 | 5 | 3 | 5 | 3 | 3 | 4 | 4 | 42.5 | 81 | 3–6 wk | CPU + LLM API |
| 11 | AlphaEvolve-style discovery and optimization records | 5 | 5 | 3 | 5 | 4 | 2 | 4 | 3 | 42.0 | 80 | 3–6 wk | CPU / consumer GPU + API |
| 14 | Research artifact: reference implementation + paper | 4 | 4 | 5 | 3 | 4 | 2 | 5 | 5 | 42.0 | 80 | 3–6 mo | 2–16 rented GPUs for red team |
| 15 | Model provenance and lineage registry (OMS-compatible) | 4 | 5 | 5 | 5 | 3 | 2 | 2 | 4 | 40.5 | 77 | 3–5 wk | none |
| 5 | Adapter / expert market with merging | 4 | 4 | 5 | 3 | 3 | 3 | 4 | 3 | 38.5 | 73 | 8–12 wk | 24 GB GPU (miner); 1 GPU (validator) |
| 1 | Verifiable autoresearch / speedrun market (flagship) | 3 | 3 | 5 | 4 | 3 | 3 | 5 | 3 | 38.0 | 72 | 6–10 wk | 1× 5090 (consumer track) to 8×H100 (PI-style) |
| 7 | Eval / benchmark market with secret sets | 3 | 4 | 4 | 4 | 3 | 3 | 4 | 3 | 36.5 | 70 | 6–10 wk | laptop (authors); 1 GPU (validator) |
| 16 | AI Act training-evidence notary | 2 | 5 | 5 | 3 | 4 | 3 | 3 | 2 | 35.0 | 67 | 6–10 wk | none (audits: client-matched GPUs) |
| 3 | RL environment authoring and rollout mining | 4 | 5 | 3 | 3 | 2 | 3 | 3 | 3 | 34.0 | 65 | 8–12 wk | Macs / consumer GPUs; 1 B200-class trainer |
| 2 | GPU kernel optimization market | 4 | 2 | 3 | 4 | 2 | 4 | 3 | 3 | 33.5 | 64 | 4–8 wk | target GPU (B200 / MI355X / 5090) per track |
| 17 | x402 agent-payment rail (enabler) | 3 | 5 | 4 | 5 | 2 | 2 | 1 | 3 | 33.5 | 64 | 1–2 wk | none |
| 13 | Hidden-test code-agent bounties | 4 | 5 | 2 | 4 | 1 | 3 | 2 | 3 | 31.5 | 60 | 4–8 wk | laptop + API |
| 6 | Data curation / dataset market | 2 | 3 | 3 | 3 | 4 | 3 | 4 | 2 | 31.0 | 59 | 8–12 wk | CPU (miners); 8×H100-hours per proxy run (validator) |
| 9 | Distillation / compression market | 3 | 2 | 4 | 3 | 2 | 3 | 3 | 3 | 30.5 | 58 | 6–10 wk | 24 GB (small teacher) to 8×H200 (validator) |
| 8 | Verifiable inference marketplace | 4 | 3 | 2 | 3 | 1 | 2 | 2 | 2 | 26.0 | 50 | 8–12 wk | 24 GB to H100 |
| 12 | Protein / molecule design | 2 | 3 | 2 | 3 | 2 | 3 | 3 | 2 | 25.5 | 49 | 6–10 wk (in silico) | 1 GPU + wet-lab $ |
| 4 | Collaborative pretraining (DiLoCo / SparseLoCo + Gauntlet) | 3 | 1 | 4 | 1 | 2 | 2 | 3 | 2 | 24.5 | 47 | 4–6 mo | 8×B200 per peer (real); 16× 5090 (toy) |
| 18 | Distribution choice | — | — | — | — | — | — | — | — | not scored | — | — | — |

**Verification cost relative to work [est].**

| Direction | Ratio | Basis |
|---|---|---|
| Lean | ~10⁻⁴ | kernel check vs. hundreds of dollars of inference |
| AlphaEvolve-style | ~10⁻³–10⁻⁵ | evaluator runtime |
| Kernels | <1% | correctness and timing runs, but needs target GPUs and a hardened harness |
| Adapters | <5% | re-evaluation |
| RL rollouts | ~1–10% | TOPLOC prefill |
| Autoresearch | ~1% of search effort, but k× one run | multi-seed noise |
| Pretraining | a few % | Gauntlet evaluation |
| Distillation | ~1 GPU-hour of 8×H200 per submission | teacher logits |
| Data curation | ≥1× | proxy training |
| Protein | wet lab dominates | |
| Notary / provenance | ~0, but only verifies commitments | |

**Sensitivity [est].**
- If the team's goal is *revenue*, re-weighting M×3 lifts the kernel market (sponsor prize pools), the AI Act notary and the adapter/data-owner market to the top three.
- If the goal is *keeping the PoDL identity* (F×3), the adapter market, the autoresearch flagship, the provenance registry and the research artifact lead.
- Lean and AlphaEvolve remain top-five under every weighting tried, because verification is nearly free.

**Portfolio implication [est].**
1. **Weeks 0–6.** Build the generic bounty engine:
   - TaskEscrow + commit-reveal Submission + Challenge/Settle.
   - Lineage royalties.
   - x402/USDC payouts.
   - OMS-compatible manifests with the `files` section signed.
   - First task type: AlphaEvolve-style records or Lean formal-conjectures bounties. These have deterministic verifiers, so contract bugs surface without ML noise, and the mempool/MTX idea becomes front-running protection.
2. **Weeks 6–16.** Add the noisy-verifier flagship: the autoresearch speedrun with multi-seed CI acceptance, or the adapter-merge market. Run the red team.
3. **In parallel.** Turn the manifest and Merkle-trace code into the provenance registry and AI Act evidence SDK. It is the only path with plausible non-token revenue.
4. **Output.** A paper describing one protocol instantiated on exact, noisy and statistical verifiers, per section 14.

### Gaps
- The weights and scores are subjective, and no market sizing was available for most directions.
- Bittensor competitor details rest largely on one secondary directory snapshot (doctensor, 2026-11-05) with an unresolved SN97 conflict.
- I found no primary source for SN125 Refinery or SN66 Conjectures.io mechanics. These two most directly affect the flagship and the Lean options, and should be checked against their repos before any decision.
