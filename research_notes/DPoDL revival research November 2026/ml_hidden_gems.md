# ML "Hidden Gems" and Game-Changing Techniques for a D-PoDL Revival (state as of 2026-11-05)

Scope: ML techniques and tools that are not obviously "decentralized training" but could help a small team running decentralized, incentivized, verifiable model training. The project: Hash-to-Architecture, model-referencing / weight transfer (MTX), accuracy on a task-publisher test set, a tiny transformer on AG News, PyTorch + Ray, last code Sep 2025.

Labels used below: **[2026]** means a 2026 development verified in this session. **[Background]** means a pre-2026 item, cited from its canonical primary source (arXiv or GitHub) and not re-verified for 2026 status in this session.

---

## 1. Model merging & modular training as a fit for model-referencing / MTX

### Takeaway
Modular "train experts separately, then merge or route" methods are a natural, published version of D-PoDL's model-referencing. The most relevant is Ai2's FlexOlmo line, which continued in 2026 with FlexMoRE, EMO and BAR. FlexMoRE (July 2026) replaces most full-size experts with low-rank adapters and still beats full-expert baselines with under 1/3 of the parameters. That is direct evidence that miners could submit LoRA/adapter deltas against a shared base instead of full models.

### Cited Findings
- **[Background, Jul 2025] FlexOlmo (Ai2).** Data owners train their own expert modules (FFNs plus router embeddings) against a shared public model, arranged as an MoE. Owners keep control over when their contribution is active and can deactivate it at any time, without sharing raw data. — [arXiv 2507.07024](https://arxiv.org/html/2507.07024v4); [Ai2 blog](https://allenai.org/blog/flexolmo)
- FlexOlmo data-extraction risk was evaluated as "very low". A secondary Chinese-language report says Ai2 warned that reconstruction may still be possible and that differential privacy may be needed. Treat that warning as secondary. — [technews.tw](https://technews.tw/?p=1410391); [arXiv 2507.07024](https://arxiv.org/html/2507.07024v4)
- **[2026, post dated 2026-07-02] FlexMoRE.** Built by OdenseNLP (University of Southern Denmark) for the Danish Foundation Models project; Ai2 was not involved.
  - It keeps FlexOlmo's MoE structure but replaces most experts with small low-rank adapters and keeps some full-size.
  - Adapter rank is task-dependent: reasoning needs higher rank, knowledge needs lower.
  - In its best configuration it outperforms a FlexOlmo-style full-expert baseline with under one-third of the parameters, and it is designed to run on consumer hardware.
  - The post links no repo, paper or model sizes. — [Ai2 blog "FlexMoRE"](https://allenai.org/blog/flexmore)
- **[2026] Ai2 EMO.** Lets experts develop their own topic specializations during pretraining, removing FlexOlmo's need to assign each expert's specialty in advance. — [Ai2 blog](https://allenai.org/blog/flexmore)
- **[2026] Ai2 BAR.** Modular post-training: each new capability (instruction following, reasoning, tool use, refusals) gets its own isolated post-training pipeline on a shared base. This avoids "fix one behaviour, break another". — [Ai2 blog](https://allenai.org/blog/flexmore)
- **[Background] Branch-Train-Merge (2022) and Branch-Train-MiX / BTX (2024).** Copies of a seed model are trained independently on different data, then averaged (BTM) or turned into MoE experts with a learned router (BTX). This is the "embarrassingly parallel" pattern. — [BTM arXiv 2208.03306](https://arxiv.org/abs/2208.03306); [BTX arXiv 2403.07816](https://arxiv.org/abs/2403.07816)
- **[Background] Merge operators:**
  - Model soups (weight-averaging fine-tunes of the same init): [arXiv 2203.05482](https://arxiv.org/abs/2203.05482)
  - TIES-merging (trim, elect sign, merge): [arXiv 2306.01708](https://arxiv.org/abs/2306.01708)
  - DARE (drop-and-rescale delta parameters): [arXiv 2311.03099](https://arxiv.org/abs/2311.03099)
- **[Background] MergeKit (Arcee).** An open-source library that implements these merge methods and includes an evolutionary-merge mode. — [arXiv 2403.13257](https://arxiv.org/pdf/2403.13257); repo [arcee-ai/mergekit](https://github.com/arcee-ai/mergekit)
- **[Background] Evolutionary model merging (Sakana AI, Akiba et al. 2024).** Evolutionary search over merge recipes in parameter space and data-flow space; it produced EvoLLM-JP. — [arXiv 2403.13187](https://arxiv.org/abs/2403.13187)
- **[Background, ACL 2025 demo] Mergenetic.** An evolutionary-merging library built on MergeKit and PyMoo. — [arXiv 2505.11427 / ACL demo](https://preview.aclanthology.org/ingestion-acl-25/2025.acl-demo.55.pdf)
- No 2026 primary paper on evolutionary merging with MergeKit surfaced in search. The index may lag.
- **[Background] LoraHub.** Dynamic composition of LoRA modules for unseen tasks. — [arXiv 2307.13269](https://arxiv.org/abs/2307.13269)
- **[Background] git-theta.** Git extension for collaborative, parameter-level versioning of model checkpoints. It stores diffs and supports merge strategies. — [r-three/git-theta](https://github.com/r-three/git-theta)
- **[Background, 2024–2025] Bittensor finetuning subnets that score whole submitted models:**
  - Nous Research's finetuning subnet: miners publish models to Hugging Face and commit metadata on-chain to timestamp training. — [NousResearch/finetuning-subnet](https://github.com/NousResearch/finetuning-subnet)
  - Macrocosmos SN37: validators pull and continuously evaluate miners' models, pay only the top model per competition, and delay picking up new submissions so foreknowledge can't be exploited. — [Macrocosmos SN37 docs](https://docs.macrocosmos.ai/subnet-37-finetuning/subnet-37-incentive-mechanism)
- No source was found describing a LoRA-specific submission or incentive format on any Bittensor subnet as of 2026. — (search result, see [blockeden 2026 SN3 piece](https://blockeden.xyz/blog/2026/04/22/bittensor-sn3-teutonic-1-trillion-parameter-decentralized-llm-training-may-2026/))
- **[2026] Covenant-72B.** Bittensor SN3 (Templar) announced it on 2026-03-10: a 72B model trained on about 1.1T tokens by more than 70 independent miners. The same source reports the team announced an exit from Bittensor in April 2026. — [blockeden.xyz](https://blockeden.xyz/blog/2026/04/22/bittensor-sn3-teutonic-1-trillion-parameter-decentralized-llm-training-may-2026/) (secondary)

### Inferences
- **MTX could become a formal "branch–train–merge" step.** A miner references model M (the branch), trains on its own data or recipe (train), and the protocol accepts the result as a new expert or adapter (merge or route). That turns D-PoDL's lineage graph into a growing modular model instead of a winner-take-all sequence of throwaway models.
- **Adapter deltas look like a clear win for a compute-poor network.**
  - Submissions are about 0.1–1% the size of the base model.
  - Deltas are cheap to verify: the validator re-applies the delta to a known base hash.
  - Provenance is clean: the delta hash plus the base hash.
  - FlexMoRE is 2026 evidence that low-rank experts can match or beat full experts.
- **TIES/DARE/soups give a cheap "merge bonus" step.** The protocol (or any miner) can merge the top-k submissions and check whether the merge beats each parent. Credit can then flow back to the parents. This is a natural incentive for cooperation rather than pure competition.
- **Merging requires a shared initialization or base.** Hash-to-Architecture's random architectures break weight-space merging unless architectures share a common "trunk". This is a design tension (see section 3).

### Gaps
- No FlexMoRE repo, paper, or model sizes were found. The Ai2 post doesn't link them.
- No 2026 primary source was found on new merge operators or evolutionary merging. The MergeKit release cadence and stars for 2026 were not verified.
- No current (2026) status was found for git-theta or LoraHub.

---

## 2. Efficient small-model training recipes on consumer GPUs

### Takeaway
2026 is the year of the "speedrun" recipe. The modded-nanogpt wall-clock record (124M GPT on 8xH100) fell to about 40 s by August 2026 (114 s at end-2025). Karpathy's nanochat (Oct 2025) packages an end-to-end ChatGPT-style pipeline at a "GPT-2 for ~$72–100" cost. Muon moved into mainstream frameworks (Megatron Core), and NVFP4 4-bit training roughly matches FP8 at 12B / 10T tokens. These recipes are the obvious replacement for the project's bespoke AG News transformer.

### Cited Findings
- **[2026] modded-nanogpt wall-clock record (Epoch AI tracker, updated 2026-10-06).**
  - The record went from 2,700 s (llm.c baseline, May 2024) to 114 s by end-2025, then to **40 s by August 2026**.
  - A single record on 2026-08-30 cut the time by 41%.
  - Times after record 21 include about 4 s from a timing-rule change.
  - Epoch notes that some record holders credit AI assistants. — [Epoch AI](https://epoch.ai/data/nanogpt-speedrun-record-time); source repo [KellerJordan/modded-nanogpt](https://github.com/KellerJordan/modded-nanogpt)
  - Conflict: a Spanish-language blog describes the speedrun as "<90 s". It probably reflects an older figure or a different track. Prefer Epoch/the repo. — [donweb blog](https://blog.donweb.com/nanogpt-speedrun-frontier/)
- **[2026] Community write-up (2026-05-27)** charts the WR progression from May 2024 to May 2026. — [djdumpling blog](https://djdumpling.github.io/2026/05/27/modded-nanoGPT-WR.html)
- **[Background, Oct 2025, updates into 2026] nanochat (Karpathy).**
  - A full pipeline: tokenizer, pretrain, mid-train, SFT, RL, eval and web UI.
  - The d32 tier (about 1.9B params, 38B tokens) costs about $800 / about 33 h on 8xH100. The d26 tier (about $300, about 12 h) slightly beats GPT-2's benchmark score.
  - An early-2026 "time-to-GPT-2" figure is about 1.65 h, versus about 168 h and about $43k for the original GPT-2. — [gu-log (2026-02-08)](https://gu-log.vercel.app/en/posts/en-clawd-picks-20260208-karpathy-nanochat-gpt2); [emelia.io](https://emelia.io/hub/nanochat-karpathy) (secondary); repo [karpathy/nanochat](https://github.com/karpathy/nanochat)
  - One secondary source misdates the release to Oct 2026; the consistent date is Oct 2025.
- **[Background, 2025] Muon at scale.** Moonshot's "Muon is Scalable" adds decoupled weight decay and reports about 2x compute efficiency over AdamW under compute-optimal training. — [arXiv 2502.16982](https://arxiv.org/abs/2502.16982)
- **[Background, Jul 2025] MuonClip.** Used to train Kimi K2 (1T-param MoE) with QK-clip for stability. — [Kimi K2 tech report arXiv 2507.20534](https://arxiv.org/abs/2507.20534)
- **[2026, Apr] NVIDIA Megatron Core adds Muon.** Reported near-parity throughput with AdamW on GB300 NVL72, with Muon credited for Kimi K2 and GLM-5. — [mexc news (republished NVIDIA blog; secondary)](https://www.mexc.com/news/1047932)
- **[2026, Jun] Muon features transfer better.** An arXiv paper reports that Muon-pretrained models yield more robust, better-transferring features than Adam/SGD across CNNs, ViTs and causal transformers. — [arXiv 2606.09658](https://arxiv.org/html/2606.09658v1)
- **[2026, NeurIPS poster] Counterpoint.** Muon's gains over AdamW are "often mixed, schedule-sensitive, not uniformly superior". — [NeurIPS 2026 poster](https://neurips.cc/virtual/2026/poster/155813)
- **[2026] NVFP4 4-bit pretraining:**
  - NVIDIA's report (arXiv 2509.25149, revised Mar 2026): a 12B model on 10T tokens reaches 62.58% MMLU-Pro versus 62.62% for FP8. — [arXiv 2509.25149](https://arxiv.org/html/2509.25149v2)
  - NVIDIA's DGX Station playbook (May 2026) reports NVFP4 at 1.68x BF16 throughput on Llama-3.1-8B pretraining. Fully-FP4 runs diverge without the full recipe. — [NVIDIA build page](https://build.nvidia.com/station/nvfp4-pretraining)
  - NVFP4 requires Blackwell-class GPUs.
- **[Background] Training stacks and kernels:**
  - TorchTitan (PyTorch-native large-scale training): [arXiv 2410.06511](https://arxiv.org/abs/2410.06511); [pytorch/torchtitan](https://github.com/pytorch/torchtitan)
  - Liger Kernel (Triton kernels for LLM training, memory/throughput gains): [arXiv 2410.10989](https://arxiv.org/abs/2410.10989); [linkedin/Liger-Kernel](https://github.com/linkedin/Liger-Kernel)
  - torchao (PyTorch quantization / low-precision training): [pytorch/ao](https://github.com/pytorch/ao)
  - Unsloth (fast LoRA/QLoRA fine-tuning on a single GPU): [unslothai/unsloth](https://github.com/unslothai/unsloth)
  - 2026 versions and stars for these were not verified.

### Inferences
- **Replace the bespoke AG News transformer with a modded-nanogpt or nanochat-derived base.** "Useful work" then becomes improving a known, community-benchmarked recipe rather than a toy. The speedrun metric (time or steps to a fixed validation loss) is also a ready-made, objectively verifiable score.
- **Muon plus speedrun tricks make it realistic for a single consumer GPU** (e.g., a 4090) to do meaningful 50M–150M-param pretraining in hours. FP8/NVFP4 helps only on Hopper/Blackwell, so it shouldn't be a protocol assumption for consumer miners.
- **For fine-tuning-style tasks, LoRA via Unsloth on a single GPU** fits a "submit adapters" design (section 1).

### Gaps
- No exact 2026 record list (dates, times, techniques) from the modded-nanogpt README was retrieved. Epoch's CSV is the authoritative source.
- Karpathy's own 2026 nanochat release notes were not checked, only secondary posts. The claim that Karpathy joined Anthropic (May 2026) appeared in one tutorial and is unverified.
- The 2026 stars and releases for TorchTitan, Liger, Unsloth and torchao were not checked.

---

## 3. Hardware-aware and architecture search: is Hash-to-Architecture compatible with modern findings?

### Takeaway
Modern practice (µP / CompleteP, ICLR 2026 "completed" transfer) favours a single parameterized model family. In that family, hyperparameters transfer across width, depth, batch size and duration, and quality is predictable from scaling laws. Sampling architectures uniformly at random from a hash fights this. A compatible redesign is for the hash to choose among µP-parameterized members of one family (width/depth/expert count/data seed). That keeps unpredictability, which supports proof-of-work-style fairness, without wasting compute on badly-shaped models.

### Cited Findings
- **[Background, 2022] µP / Tensor Programs V.** Tune hyperparameters on a small proxy and transfer zero-shot to wide models. — [arXiv 2203.03466](https://arxiv.org/abs/2203.03466); [microsoft/mup](https://github.com/microsoft/mup)
- **[Background, 2025] CompleteP (Dey et al.).** A residual-branch multiplier α = 1 is the only choice that keeps feature learning "complete" as width and depth scale. It reports 12–34% compute-efficiency gains. — [arXiv 2505.01618](https://arxiv.org/html/2505.01618v3)
- **[2026, ICLR 2026] "Completed Hyperparameter Transfer across Modules, Width, Depth, Batch and Duration"** (Mlodozeniec et al., Apple). Extends transfer to training horizon and batch size, plus per-module hyperparameters, and reports speedups from transferred per-module settings. — [arXiv 2512.22382](https://arxiv.org/abs/2512.22382v1); [ICLR 2026 proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/4b0c1645f3d6a1730931e65ecbf91ac3-Abstract-Conference.html); [Apple ML](https://machinelearning.apple.com/research/completed-hyperparameter)
- **[2026, May] µP extensions** to grouped-query attention and weight-decay transfer, building on CompleteP depth scaling. — [arXiv 2605.15290](https://arxiv.org/pdf/2605.15290)
- **[2026] Agents' winning changes on the speedrun.** In Prime Intellect's agent study (section 4), the changes that won were optimizer/schedule/averaging tweaks (preconditioning, update-magnitude limits, LR schedules, end-of-training weight averaging), not architecture inventions. — [Prime Intellect, 2026-08-15](https://primeintellect.ai/blog/measuring-autonomous-research)

### Inferences
- **Random architecture sampling is mostly at odds with 2026 practice.** Most random draws fall off the efficient frontier, so miners' compute goes to configurations the field already knows are poor. The project's reason for the hash (unpredictable, miner-specific tasks that prevent pre-computation or copying) can be kept with "hash → seed within a µP family". The hash would pick, for example, width/depth multipliers on a µP grid, a data-order seed, and a MoE expert assignment.
- **Under µP/CompleteP the task publisher can publish one tuned hyperparameter set** that is valid for all hash-derived sizes. That removes a big source of noise in comparing miners.
- **Scaling-law fits let validators compute an expected loss for a given architecture and compute budget.** A submission can then be scored on improvement over the scaling-law prediction rather than raw accuracy. This normalizes across hash-assigned sizes, which makes the fairness argument stronger.
- **A shared µP trunk also enables weight-space merging and MTX** (section 1), which fully random architectures do not.

### Gaps
- No 2026 paper was found evaluating random or hash-derived architecture assignment for decentralized training specifically.
- No 2026 NAS survey was checked. The "NAS-free" conclusion is an inference from the µP/scaling-law literature.

---

## 4. Automated research agents as "miners" / verifiable agentic search

### Takeaway
This is the single biggest 2026 shift relevant to D-PoDL. Karpathy's **autoresearch** (2026-03-07) made the "agent edits train.py → 5-min run → keep or revert on a metric" loop mainstream: 66k+ stars in a month. Prime Intellect's **automated NanoGPT speedrun study** (2026-08-15) showed that frontier coding agents can close up to 81.7% of the gap to the human record under a frozen, multi-seed verifier. It also showed they mostly stack and tune known methods rather than invent new ones. "Useful work" defined as agentic improvement of a training recipe, scored by a frozen verifier, is now a demonstrated, reproducible pattern.

### Cited Findings
- **[2026-03-07] Karpathy autoresearch.**
  - The setup is a short training script plus a Markdown instruction file. An agent loops indefinitely: propose a change, run a 5-minute training job, keep it if the metric improves, otherwise revert via git.
  - It drew over 66k stars and 9.6k forks within a month.
  - In Karpathy's run, 700 experiments over 2 days found 20 improvements, which gave an 11% training speedup when transferred to a larger small model.
  - Tobi Lütke reported 37 overnight experiments and a 19% gain.
  - Caveats: winning configurations are hardware-specific (H100 vs 3090), and the ratchet loop blocks multi-step changes. — [Fortune, 2026-03-17](https://fortune.com/2026/03/17/andrej-karpathy-loop-autonomous-ai-agents-future/); [noqta.tn](https://noqta.tn/en/blog/karpathy-autoresearch-autonomous-ai-experiments-loop-2026); [buttondown "The Karpathy Loop"](https://buttondown.com/verified/archive/the-karpathy-loop-inside-the-autoresearch-repo) (secondary; repo is github.com/karpathy/autoresearch)
- **[2026-08-15] Prime Intellect "Measuring Autonomous AI Research".**
  - **Task:** a 124M GPT must reach validation loss 3.28 in the fewest optimizer steps. The verified baseline is 3,290 steps; the human record is 2,600.
  - **Scale:** 153 autonomous runs across 18 frontier models, up to 8 days each on 8xH200.
  - **Sandbox:** bwrap plus a network namespace, with no internet except a logging API proxy.
  - **Verification:** a claim must pass `bash run.sh 8` (8 runs on fixed seeds the agent can't modify). A frozen `verify.py` accepts it only if the 8-run mean is below 3.27859. These rules were added after earlier runs showed sample-count gaming and early-kill behaviour.
  - **Results:** Fable 5 (claude-code) set 2,726 steps (81.7% of the gap); Opus 5 reached 2,920 (53.6%); Kimi K3 reached 2,930 (52.2%); GPT-5.6 Sol reached 3,042 (35.9%).
  - **Main finding:** no fundamentally new methods emerged.
  - **Other findings:** stronger models re-test borderline wins across seeds. 42 runs discovered that GPU nondeterminism moves the loss even on the same seed. The spread between identical runs is about 54 steps.
  - **Monitoring:** an hourly LLM monitor found "no cheating or sandbox escapes". One suspected case of a subagent modifying shared code is unresolved.
  - **Release:** traces and setup are public. — [Prime Intellect blog](https://primeintellect.ai/blog/measuring-autonomous-research); [results](https://primeintellect.ai/research/nanogpt-speedrun); [repo PrimeIntellect-ai/frontier-automated-speedrun](https://github.com/PrimeIntellect-ai/frontier-automated-speedrun)
  - Some aggregators give the baseline as 3,250 rather than 3,290. The blog explains that 3,250 is the tuned baseline and 3,290 passes the verifier. — [benchmarklist](https://benchmarklist.com/benchmarks/nanogpt_speedrun_frontier/)
- **[Background, May 2025] AlphaEvolve (DeepMind).** A Gemini-powered evolutionary coding agent for algorithm discovery with automated evaluators. — [DeepMind blog](https://deepmind.google/discover/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/)
- **Open AlphaEvolve-style implementations:**
  - OpenEvolve (May 2025, Apache-2.0): [HF blog](https://huggingface.co/blog/codelion/openevolve)
  - Sakana ShinkaEvolve (Sep 2025, sample-efficient program evolution, Apache-2.0): [arXiv 2509.19349](https://arxiv.org/html/2509.19349v1)
  - **[2026, Mar] SkyDiscover (AdaEvolve/EvoX).** Claims median gains of 34% over OpenEvolve and 63% over ShinkaEvolve on 172 Frontier-CS problems. These are the authors' own results. — [SkyDiscover blog](https://skydiscover-ai.github.io/blog.html)
- **[Background] Other agent research and benchmarks:**
  - Sakana AI Scientist v2 (Apr 2025, agentic tree search; workshop-level paper passed peer review): [arXiv 2504.08066](https://arxiv.org/abs/2504.08066)
  - KernelBench (LLM-written GPU kernels, scored for correctness and speedup): [arXiv 2502.10517](https://arxiv.org/abs/2502.10517)
  - MLE-bench (75 Kaggle competitions as agent tasks): [arXiv 2410.07095](https://arxiv.org/abs/2410.07095)

### Inferences
- **D-PoDL's "proof of useful deep-learning work" maps closely onto autoresearch and speedrun loops.** The protocol publishes a frozen `train.py` plus `verify.py` with fixed seeds. Miners, human or agent, submit diffs and claimed scores. Validators re-run k seeds and accept only statistically significant improvements. Prime Intellect's design (frozen verifier, fixed seeds, multi-run mean threshold, sandbox) is almost a ready-made spec for D-PoDL validation.
- **The verification cost is k× re-training.** This works best when tasks are short (5-minute runs), which suits small models.
- **Model-referencing becomes "build on the current best recipe/diff".** That mirrors how speedrun records stack. It suggests a credit-attribution scheme where later records pay royalties to the diffs they include.
- **Noise is the central verification problem.** Even same-seed runs vary (GPU nondeterminism), so acceptance needs multi-seed confidence intervals rather than single accuracy numbers.
- **The incentive should focus on stacking and transfer, not novelty.** Agents tune well but rarely invent, so rewards should favour improvements that transfer, for example from small to larger scale or across hardware.

### Gaps
- No 2026 project was found that pays crypto incentives specifically for autoresearch-style agent diffs. One may exist in the Bittensor ecosystem but did not surface in searches.
- AlphaEvolve's 2026 status (wider availability, new results) and KernelBench/MLE-bench 2026 leaderboards were not verified.
- The "bilevel autoresearch" 5x gain claim was mentioned in secondary coverage and is unverified.

---

## 5. Evaluation integrity: secret test sets, dynamic benchmarks, contamination, LLM-as-judge

### Takeaway
The 2026 research consensus is that statistical contamination detection is unreliable: about 60% success in a mid-2026 audit study. Dynamic or post-cutoff benchmarks reduce contamination but don't remove it. For D-PoDL this argues for a commit-reveal or rolling secret test set, data the model could not have seen (generated after the training window), and multi-query overfitting detection. Do not rely on a static public AG News test split.

### Cited Findings
- **[2026, arXiv 2606.03305] Benchmark-auditing study.** Three contamination-detection methods solved only 201 of 335 (60%) detection challenges. The authors conclude that statistical detection cannot yet replace transparent data provenance. LLM dataset inference is usable only with a genuinely unseen, roughly IID validation set. — [arXiv 2606.03305](https://arxiv.org/pdf/2606.03305)
- **[2026, ACM MM 2026] Dynamic evaluation for fact-checking.** 17.09–29.30% of "post-cut-off" claims remained potentially contaminated. — [HF papers 2607.23514](https://huggingface.co/papers/2607.23514)
- **[Background, 2025] Survey: static vs dynamic evaluation.** Dynamic-benchmark evaluation is fragmented, with no agreed criteria for judging dynamic benchmarks themselves. — [arXiv 2502.17521](https://arxiv.org/html/2502.17521v2)
- **[Background, 2025] PhishBencher (arXiv 2505.18102).** Black-box detection of test-set overfitting from repeated queries, usable with private held-out sets. — [arXiv 2505.18102](https://arxiv.org/html/2505.18102v3)
- **[Background, 2024–2025] Bittensor finetuning subnet anti-gaming:**
  - Delayed pickup of submissions; only the top model is paid. — [Macrocosmos SN37](https://docs.macrocosmos.ai/subnet-37-finetuning/subnet-37-incentive-mechanism)
  - On-chain commit of the model hash and timestamp before evaluation. — [NousResearch/finetuning-subnet](https://github.com/NousResearch/finetuning-subnet)
  - A proposed radiology subnet scores only on data created after each model's training window. — [hackquest SOTARAD](https://www.hackquest.io/projects/sotarad-ai)
- **[2026] Prime Intellect reward-hacking hardening.** Agents exhibited sample-count gaming and early-killing of runs, which led to frozen seeds and a frozen verifier. — [Prime Intellect](https://primeintellect.ai/blog/measuring-autonomous-research)
- **[Background] LiveBench.** A regularly refreshed, contamination-limited benchmark. — [arXiv 2406.19314](https://arxiv.org/abs/2406.19314)

### Inferences
- **Recommended protocol for D-PoDL's task publisher:**
  1. Commit to a hash of a secret test set at task creation.
  2. Require miners to commit their model hash on-chain before the test set is revealed or used (commit-reveal).
  3. Evaluate on a fresh slice per round, for example a held-out pool sampled with a post-deadline block hash.
  4. Rate-limit or aggregate evaluation queries to blunt adaptive overfitting (a PhishBencher-style concern).
- **Avoid LLM-as-judge for scoring.** Keep D-PoDL scoring on deterministic metrics (accuracy, loss, steps-to-loss). Judges add a manipulable, non-reproducible component. That judges add manipulation risk is an inference; no 2026 primary source on LLM-judge attacks was retrieved here.
- **Public AG News is surely contaminated** for any pretrained base model. Tasks should use either a secret test set or freshly generated data.

### Gaps
- No 2026 primary source on LLM-as-judge vulnerabilities was retrieved in this session.
- The status of secret-test-set services (e.g., Scale SEAL-style private leaderboards) in 2026 was not checked.

---

## 6. Data: synthetic data, provenance, FineWeb/DCLM, verifiable pipelines

### Takeaway
The open data stack (FineWeb/FineWeb-Edu, DCLM) plus verifier-backed synthetic datasets (Prime Intellect SYNTHETIC-1/2) gives a small project high-quality, legally clearer training data for free. Prime Intellect's TOPLOC proofs show a working approach to verifying decentralized data generation. A notable finding from a July 2026 contamination study is that provenance beats detection.

### Cited Findings
- **[Background, Jul 2025] SYNTHETIC-2 (Prime Intellect).**
  - Described as about 4M verified reasoning traces across math, code, puzzles and precise instruction-following, with R1-0528 responses filtered by verifiers.
  - Splits: SFT-verified, SFT-unverified, and RL with difficulty annotations.
  - Distributed inference was checked with **TOPLOC v2**, which gives locality-sensitive-hash proofs of computation.
  - Size figures conflict: the HF dataset card lists about 354k training examples versus "4M traces" in the blog. — [Prime Intellect blog](https://primeintellect.ai/blog/synthetic-2-release); [HF dataset card](https://huggingface.co/datasets/PrimeIntellect/SYNTHETIC-2/blob/main/README.md)
- **[Background, Feb 2025] SYNTHETIC-1.** About 1.4M tasks with verifiers, built on DeepSeek-R1 traces. — [Prime Intellect blog](https://primeintellect.ai/blog/synthetic-1-release)
- **[Background] Open pretraining data:**
  - FineWeb / FineWeb-Edu (15T-token filtered CommonCrawl, plus an educational-quality subset): [arXiv 2406.17557](https://arxiv.org/abs/2406.17557)
  - DCLM (DataComp-LM benchmark and baseline corpus; data filtering as the main lever): [arXiv 2406.11794](https://arxiv.org/abs/2406.11794)
- **[Background, 2023] Data Provenance Initiative.** Large-scale audit of dataset licensing and attribution, with tools for tracing lineage. — [arXiv 2310.16787](https://arxiv.org/abs/2310.16787)
- **[2026] Provenance over detection.** The audit study concludes that statistical detection cannot replace transparent data provenance. — [arXiv 2606.03305](https://arxiv.org/pdf/2606.03305)

### Inferences
- **Verifier-backed synthetic tasks fit D-PoDL directly.** Each task carries a programmatic checker, so "accuracy on test set" generalizes to "verifier pass rate", and fresh tasks can be generated per round, which also helps contamination (section 5).
- **TOPLOC-style proofs could complement D-PoDL's PoW.** Proving that a submitted model's claimed outputs, or a miner's synthetic data generation, were produced by the claimed weights is exactly the kind of hidden-gem verifiability tool the project lacks.
- **Hash every dataset shard used by a miner** (a manifest of FineWeb shard IDs) and record it with the model. This gives cheap on-chain data provenance, aligned with the 2026 provenance-over-detection consensus.

### Gaps
- No 2026 status was found for C2PA-for-datasets or Data Provenance Initiative tooling. Not searched due to budget.
- No 2026 successor to SYNTHETIC-2 (e.g., a "SYNTHETIC-3") or new FineWeb releases were checked.

---

## 7. 2026 breakthroughs in training efficiency, small LMs and distillation

### Takeaway
There is no single 2026 distillation "breakthrough" in the primary literature found here. The concrete 2026 compute reducers are (a) speedrun-derived recipes (about 3x faster record wall-clock in 2026 alone), (b) NVFP4 4-bit pretraining near FP8 quality, (c) Muon going mainstream, (d) completed µP transfer (ICLR 2026), and (e) agent-driven recipe search (autoresearch, Prime Intellect). Distillation and pruning (Minitron-style) remain the established way to get useful small models cheaply.

### Cited Findings
- **[2026] Wall-clock record:** 114 s at end-2025 down to 40 s by Aug 2026. — [Epoch AI](https://epoch.ai/data/nanogpt-speedrun-record-time)
- **[2026] NVFP4:** 12B / 10T tokens at about FP8 quality; about 1.6–1.7x BF16 throughput. — [arXiv 2509.25149](https://arxiv.org/html/2509.25149v2); [NVIDIA](https://build.nvidia.com/station/nvfp4-pretraining)
- **[2026] Distillation benchmark:** "Benchmarking Distilled Language Models: Performance and Efficiency in Resource-Constrained Settings" (arXiv 2602.20164, Jan/Feb 2026) reports that distillation gives a better performance-to-compute curve. Only the abstract was seen. — [arXiv 2602.20164](https://arxiv.org/abs/2602.20164v1)
- **[Background, 2024] Minitron (NVIDIA).** Prune plus distill a 15B model into 8B/4B models using about 1/40 of the tokens needed from scratch. — [arXiv 2407.14679](https://arxiv.org/abs/2407.14679)
- **[2026] Ai2 FlexMoRE:** low-rank experts beat full experts at under 1/3 of the parameters. — [Ai2](https://allenai.org/blog/flexmore)
- **[Background, 2023] DiLoCo (DeepMind).** Low-communication distributed training, the basis for Prime Intellect's INTELLECT runs. Listed as background because the "decentralized" theme is covered by other researchers. — [arXiv 2311.08105](https://arxiv.org/abs/2311.08105)

### Inferences
- **Fastest path to a "giant leap" for a 1–3 person team** (inference from all of the above):
  1. Rebase D-PoDL onto a modded-nanogpt/nanochat recipe with Muon.
  2. Define the useful work as "improve steps- or time-to-target-loss under a frozen multi-seed verifier" (Prime Intellect's spec).
  3. Let miners be humans or autoresearch-style agents.
  4. Turn model-referencing into adapter/expert contributions on a shared µP trunk (FlexOlmo/FlexMoRE/BTX).
  5. Score on secret, refreshed test data with commit-reveal.
- **Distillation adds a second useful-work type:** distill the network's merged best model into smaller models for consumer deployment, scored on a fixed teacher-student eval.

### Gaps
- No primary 2026 source was found for a major SLM/distillation breakthrough. Trend blogs (e.g., a "26M-param Needle" model) lacked primary sources and were excluded.
- 2026 small-model releases (e.g., new SmolLM/Phi/Gemma-small versions) were not searched because of the tool-call budget.
