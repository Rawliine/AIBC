# Feasibility of Collectively Pre-training One Competitive LLM on Consumer GPUs over Home Internet (as of 2026-11-05)

Scope: consumer-hardware specifics (8–32 GB NVIDIA gaming GPUs first; Apple/AMD/Intel later), parallelism choice, heterogeneity, compute math, architecture, data pipeline, client practicality, fine-tuning/RL as an earlier milestone, and a recommended MVP. Builds on (does not repeat) `research_notes/DPoDL revival research November 2026/decentralized_training.md` (DiLoCo family, SparseLoCo, DeMo, MuLoCo, Decoupled DiLoCo, Covenant-72B, Pluralis-8B headline numbers, torchft/PCCL/Hivemind).

Labels: **[EST]** = my own calculation/estimate, not from a source. **[MEM]** = from my background knowledge, not re-verified in this session (treat as needing a check). **[CLAIM]** = self-reported by vendor/project. Dates in brackets are the source's publication date.

Method note: ~25 tool calls (search + fetch). The most important primary source for this question, the Agora paper (arXiv 2607.13332, Jul 2026), was read for ~200k of its ~275k characters; its hardware/churn tables are cited directly below.

---

## 1. Parallelism options when the model doesn't fit one consumer GPU — and which fits 8–32 GB GPUs on 10–100 Mbps uplinks

### Takeaway
Only two families have been demonstrated over the internet at >1B scale: (a) **data-parallel DiLoCo/SparseLoCo**, where every node holds a full replica (proven at 72B, but on 8xB200 peers), and (b) **pipeline-parallel with compressed activations** (Pluralis Agora: 8.6B, 7 stages, but in practice it required ≥24 GB GPUs, ≥70 GB system RAM per GPU, 100 Mbps up / 200 Mbps down, <80 ms RTT and inbound port-forwarding; head/tail stages ran on Pluralis-owned cloud nodes; MFU on contributor stages was ~19–22%). Tensor/FSDP/expert-parallel all-to-all over WAN is not viable. For true home gaming PCs (8–32 GB, 10–100 Mbps up, NAT), the best near-term fit is **DiLoCo-style full-replica training of a ≤1.5–3B dense model with CPU-offloaded optimizer state and 8-bit compute**, with Agora-style pipelining reserved for a later, curated tier of 24–32 GB nodes on good links, and BTX/FlexOlmo-style "train experts independently, merge into MoE" as the scale-up path to a larger model.

### Cited Findings

**Pluralis Agora / Pluralis-8B (pipeline + data parallel, the only consumer-GPU pre-training run at scale)**
- [2026-07] Model: 32 transformer blocks split into 7 pipeline stages — head = 6 blocks + embeddings, 5 body stages × 4 blocks each, tail = 6 blocks + de-embedding; ~310M params per block (so a body stage ≈ 1.24B params **[EST: 4×310M]**); ~8.6B trainable, ~12B "dense-equivalent"; hidden d = 5120 — [Agora, arXiv 2607.13332](https://arxiv.org/html/2607.13332)
- [2026-07] Contributors join **only body stages**; head and tail run on "stable cloud compute" (head: 8 Pluralis nodes, tail: 16 Pluralis nodes, each body stage: 4 Pluralis nodes + contributors; median ~15 nodes per body stage; first 5,000 steps ran on Pluralis nodes only) — [arXiv 2607.13332](https://arxiv.org/html/2607.13332)
- [2026-07] Activation compression: Subspace Networks cut inter-stage communication "by two orders of magnitude"; rank ≈51 at d=5120 (rank 40 at d=2048 for 1B) — [arXiv 2607.13332](https://arxiv.org/html/2607.13332)
- [2026-07] Same-stage replica sync = AsyncSPARTA: averaging interval A=20 steps, sparse fraction 5% per round (every parameter covered once per 400 steps), 2 MiB chunks, 40 s matchmaking window, 30 s/60 s sender/reducer timeouts, staleness threshold 3 steps, global batch 2,048 samples/step; **AdamW offloaded to CPU**, optimizer states not exchanged — [arXiv 2607.13332](https://arxiv.org/html/2607.13332)
- [2026-07] Bandwidth: paper's estimate ~113 Mbit/s needed with BF16 all-reduce (~186 Mbit/s FP32); stability tests at 200 Mbit/s, 80 ms RTT ceiling; **measured contributor download median 703 Mbit/s (range 213 Mbit/s–7.7 Gbit/s), latency median 28 ms** — [arXiv 2607.13332](https://arxiv.org/html/2607.13332)
- [2026-07] Utilization (peak window, steps 20k–30k): MFU all stages 24.2% — head 38.9%, tail 36.0%, body stages 18.6–22.4%; GPU utilization 54.4% overall, body stages 42–50%; pooled spec compute 39,749 TFLOP/s (dense BF16); 745 active trainers at ~170k tokens/s; 63% of a centralized H100 FSDP2 Llama-3.1-8B baseline; total 3.08e22 FLOP — [arXiv 2607.13332](https://arxiv.org/html/2607.13332)
- [2026-07] Stated limitations: all-reduce payload and state loading grow with stage size; sparse averaging constrains replica count; bandwidth model ignores jitter/packet loss; a mass contributor departure caused a loss perturbation near step 40k; ~540 steps of drift from optimizer sync — [arXiv 2607.13332](https://arxiv.org/html/2607.13332)
- [2026-11, current docs] Contributor requirements: **≥24 GB VRAM** (RTX 4090, RTX 5090, RTX 6000 Ada, RTX PRO 4500/6000, L40S), **70 GB RAM per GPU**, 80 GB disk, **200 Mbps down / 100 Mbps up** (speed-tested at join), RTT <80 ms to NA peers ("a North American instance is effectively required"), Linux or Windows 10/11 + WSL2, **macOS unsupported (no CUDA)**, **inbound TCP port 49200 per GPU** (home users need router port forwarding; WSL2 needs a port proxy), max 5 peers per HuggingFace account — [Pluralis requirements](https://pluralis.ai/docs/quick-start/requirements/)
- Runs list: Node0-7.5B (Sep 2025, 36.6B tokens); Pluralis-8B (May 2026, 531.8B tokens per docs vs 500B per paper); Pluralis-13B (Sep 2026, 62.4B tokens, systems test of Metadata Store + P2P microbatch routing) — [Pluralis docs](https://pluralis.ai/docs/)

**SWARM parallelism (background)**
- [BG, Jan 2023, ICML 2023] SWARM trained a Transformer LM with "1B shared parameters (approximately 13B before sharing)" on **preemptible T4 GPUs** over "less than 200Mb/s network"; stochastic wiring/rebalancing of pipeline stages across unreliable peers — [arXiv 2301.11913](https://arxiv.org/abs/2301.11913). SWARM's routing is the basis of Agora's stochastic peer-to-peer routing — [Pluralis docs](https://pluralis.ai/docs/)

**DiPaCo (DeepMind, distributed path composition)**
- [BG, Mar 2024] DiPaCo: model = shared modules composed into **256 possible paths of ~150M params each**; modules synchronized with DiLoCo ("drastically reduced communication"); designed for poorly connected, heterogeneous workers, tolerant of failures/preemptions; on C4 it "exceeds the performance of a 1 billion-parameter dense transformer" for the same number of steps in less wall-clock; at inference only one path runs per input — [arXiv 2403.10616](https://arxiv.org/abs/2403.10616)

**Independently trained experts merged into MoE**
- [BG, Mar 2024] Branch-Train-MiX (BTX, Meta): branch a seed model, train domain experts "in an embarrassingly parallel fashion", then merge their FFNs as MoE experts (other params averaged) and fine-tune token-level routing; "best accuracy-efficiency tradeoff" vs alternatives (no numbers on abstract page) — [arXiv 2403.07816](https://arxiv.org/abs/2403.07816)
- [BG, Jul 2025; NeurIPS 2025] FlexOlmo (Ai2): each data owner trains an expert independently against a **frozen public anchor model**, then experts are combined via a learned router with no joint training; up to **37B total / 20B active**, 31 tasks; ~41% average relative gain over public-only model; +10.1% vs prior merging methods; beats a standard MoE trained without data restrictions at equal training FLOPs; experts can be opted in/out at inference — [arXiv 2507.07024](https://arxiv.org/abs/2507.07024); [NeurIPS 2025 poster](https://neurips.cc/virtual/2025/poster/120189)

**Single-GPU memory reach on consumer cards (relevant to full-replica DiLoCo)**
- [2025-12-17] LLMQ (Schultheis & Alistarh, ISTA): end-to-end CUDA/C++ 8-bit pre-training for workstation/consumer GPUs with activation checkpointing, offloading and copy-engine collectives; can train/fine-tune a **7B model on a single 16 GB mid-range gaming card**; **32B on 4× RTX 4090**; ~50% FLOP utilization — [arXiv 2512.15306](https://arxiv.org/abs/2512.15306). Search-result summary of the paper: single RTX 4090 7B at ~4,300 tokens/s, 61% MFU; 4× RTX 4090 14B at 7,800 tok/s (54% MFU), 32B at 3,400 tok/s (51% MFU); L40S reference 29% MFU — [arXiv PDF 2512.15306](https://www.arxiv.org/pdf/2512.15306) (detail numbers from search snippet; not verified in full text)

### Inferences
- **[EST] Memory arithmetic (mixed-precision AdamW ≈ 16 B/param: bf16 weights 2 + bf16 grads 2 + fp32 master 4 + Adam m,v 8).** All-on-GPU full replicas: 8 GB ≈ 0.3–0.4B, 12 GB ≈ 0.5B, 24 GB ≈ 1–1.2B, 32 GB ≈ 1.5B (after activations). With optimizer + master weights offloaded to CPU RAM (as Agora does), GPU needs ~4 B/param + activations → 24 GB ≈ 4B, 32 GB ≈ 5–6B, 12 GB ≈ 2B, 8 GB ≈ 1B; system RAM needs ~12 B/param (e.g., 3B model → 36 GB RAM, beyond many gaming PCs with 16–32 GB). LLMQ-style 8-bit + offload pushes 7B onto 16 GB but implies heavy PCIe/host-RAM traffic and ≥64 GB RAM.
- **[EST] Note on LLMQ's "61% MFU":** 6 × 7e9 × 4,300 tok/s ≈ 1.8e14 FLOP/s, which exceeds the RTX 4090's 165 TFLOPS BF16(FP32-acc) dense peak, so the MFU must be measured against the 8-bit (≈330 TFLOPS dense) peak. Practical meaning: 8-bit training roughly doubles usable throughput on Ada/Blackwell vs BF16 — but not on Ampere (RTX 30, no FP8).
- **[EST] FSDP/ZeRO-3 over WAN is ruled out:** it all-gathers parameters every step; for a 7B bf16 model that is ~14 GB per node per step → ~19 minutes per step at 100 Mbps. Tensor parallel (per-layer all-reduce) and expert-parallel all-to-all (per-layer, latency-bound) are worse.
- **[EST] Pipeline over home links is marginal:** Agora's own bandwidth estimate (~113 Mbit/s for the replica all-reduce alone) already exceeds typical home uplinks of 10–50 Mbps, and its real contributors had median 703 Mbit/s down and 504 GB RAM (see §2) — i.e., datacenter-class hosts. Pipelining also makes every step depend on the slowest stage replica set, and body-stage MFU was only ~20%.
- **[EST] DiLoCo full-replica with SparseLoCo-class compression fits home uplinks for ≤3B:** a 1.5B model's dense bf16 pseudo-gradient is ~3 GB; at ~146× compression ≈ 20 MB upload per outer round (≈16 s at 10 Mbps). The harder side is **download**: merging top-k updates from many peers approaches dense density (Covenant capped contributors at 20/round), so a 1.5B model may need ~1–3 GB down per round → 1.5–4 min at 100 Mbps; with 20–30 min rounds that is ~5–15% overhead. For 7B the download (~6–14 GB/round) becomes the binding constraint for 100 Mbps-down homes unless aggregation is hierarchical or the merged update is re-sparsified.
- **Ranking for 8–32 GB / 10–100 Mbps-up homes [EST]:** (1) DiLoCo/SparseLoCo/MuLoCo full replica, ≤1.5B (8–16 GB) or ≤3B (24–32 GB with offload) — simplest, NAT-friendly (outbound HTTPS to object storage), tolerant of churn; (2) BTX/FlexOlmo/DiPaCo-style "experts as units of work" — each expert trained by a DiLoCo group, merged into an MoE later; natural sharding unit, no per-step cross-group comms; (3) Agora-style pipeline for a curated "pro tier" (≥24 GB, ≥100 Mbps up, regional latency); (4) FSDP/TP/EP over WAN — no.

### Gaps
- Agora per-stage memory footprint and why 70–80 GB RAM per GPU is needed were not stated in the portion read.
- No published DiPaCo perplexity/compute tables were read (abstract only); no evidence DiPaCo was ever run on consumer hardware or over real WAN.
- No 2025–2026 demonstration found of "expert-parallel MoE over WAN" with per-token routing across home nodes; BTX/FlexOlmo were run in datacenters.
- No study found combining ZeRO-Infinity/NVMe offload with DiLoCo on consumer GPUs (LLMQ is single-node).

---

## 2. Heterogeneity: GPU generations, stragglers, async methods, cross-vendor, precision

### Takeaway
Mixed NVIDIA generations are handled in practice by asynchronous/quorum schemes (Agora tolerates 10:1 speed heterogeneity at 1B in ablations; HeLoCo, May 2026, reports +22.1% vs synchronous DiLoCo). But the "consumer" Agora run was in reality dominated by prosumer/datacenter hosts (RTX 5090/4090 55%, L40S 22%, RTX 6000 Ada/RTX PRO 6000 23%; median 504 GB RAM). **No public 2025–2026 run co-trained one model across NVIDIA + AMD + Apple**; cross-vendor is demonstrated only for RL rollouts (Apple MLX inference + NVIDIA trainer) and vendor-specific DiLoCo (AMD MI300). Precision support diverges: BF16 from Ampere (RTX 30) onward, FP8 only on Ada (RTX 40) and Blackwell (RTX 50), FP4 only on RTX 50 — so the shared recipe must be BF16 with optional per-node 8-bit inner compute.

### Cited Findings
- [2026-07] Agora fleet composition: RTX 5090 + RTX 4090 = 55% of nodes, L40S 22%, RTX 6000 Ada + RTX PRO 6000 23%. Over the run RTX 4090 share fell ~32% → ~9%, RTX 5090 rose 17% → 31%, L40S 29% → 35%, RTX PRO 6000 17% → 23%. No RTX 3090 mentioned. Min 24 GB VRAM, min 80 GB RAM, **median RAM 504 GB (up to 2 TB)** — [arXiv 2607.13332](https://arxiv.org/html/2607.13332)
- [2026-07] Agora straggler/churn handling: senders missing per-chunk timeout banned from the round; worker failing 2 of last 3 all-reduce rounds self-terminates; joining nodes pass weight-sync then optimizer-sync phases; trainers route microbatches to least-loaded worker by speed-weighted virtual runtime; 1B ablations: tolerates **up to 10:1 heterogeneity**, degrades only when all-reduce participation falls **below ~85%** — [arXiv 2607.13332](https://arxiv.org/html/2607.13332)
- [2026-05] HeLoCo (arXiv 2606.00271): asynchronous low-communication training under data and device heterogeneity; up to +7.5% vs async-DiLoCo baselines at fixed token budget and up to +22.1% vs synchronous baseline — [arXiv 2606.00271](https://arxiv.org/html/2606.00271v1)
- [BG, Jan 2024] Async Local-SGD (Liu et al., DeepMind): vanilla async DiLoCo "struggles even with homogeneous devices"; Delayed Nesterov (DN) + Dynamic Local Updates (DyLU, faster workers do more inner steps) "consistently excels across all heterogeneity levels" — [arXiv 2401.09135](https://arxiv.org/pdf/2401.09135)
- [BG, ICML 2025] HALoS: hierarchical async local SGD for geo-distributed training; notes DiLoCo's synchronous design underutilizes heterogeneous accelerators due to stragglers — [NSF PAR copy](https://par.nsf.gov//servlets/purl/10613791)
- [2025] Biased Local SGD (arXiv 2508.08540): lets slower CPUs work alongside GPUs (RTX 4090 + AMD EPYC), not cross-GPU-vendor — [arXiv 2508.08540](https://arxiv.org/html/2508.08540v2)
- [2026] Forgather DiLoCo docs: supports heterogeneous hardware (different GPU types/counts per machine) with DN momentum and DyLU — [Forgather docs](https://forgather.readthedocs.io/en/latest/trainers/diloco/)
- [2025-12] AMD ROCm blog: step-by-step DiLoCo decentralized training with Prime Intellect's framework on AMD Instinct MI300 (datacenter AMD, not consumer Radeon) — [ROCm blog](https://rocm.blogs.amd.com/artificial-intelligence/decentralized-training/README.html)
- [2026-07] Cross-vendor RL: 14 Macs (MLX, int8 rollouts) + one B200 trainer (bf16, Megatron) — [Pluralis blog](https://pluralis.ai/blog/rl-post-training-on-macs/)
- [2025–2026] exo (Apple Silicon/MLX distributed, heterogeneous Macs, RDMA over Thunderbolt 5 on macOS 26.2+) is **inference-only**; secondary guides state it is not built for training — [noqta guide 2026](https://noqta.tn/en/blog/exo-distributed-ai-cluster-apple-silicon-local-llm-2026); [noqta exo labs guide](https://noqta.tn/en/blog/exo-labs-local-ai-cluster-frontier-models-guide-2026)
- FP8 on consumer GPUs: torchao's official float8 training table lists H100/B200 only; downstream Forgather states FP8 works on Ada (RTX 4090, compute capability ≥8.9) with torchao tensorwise recipe; PyTorch forum: sm_89 missing from some standard builds, and FP8 `_scaled_mm` kernels need sm_89 explicitly — [torchao workflows](https://docs.pytorch.org/ao/stable/_sources/workflows/index.md.txt); [Forgather FP8](https://forgather.readthedocs.io/en/latest/trainers/fp8-training/); [PyTorch forum](https://discuss.pytorch.org/t/sm-89-not-listed-in-the-torch-cuda-get-arch-list/215827)
- GeForce FP32-accumulate tensor throughput is half the FP16-accumulate rate (forum + spec tables), which is why GeForce BF16 training peaks are half the marketing FP16 figure — [NVIDIA dev forum](https://forums.developer.nvidia.com/t/rtx-5090-peak-bf16-tensor-tflops/350543); [Club386 5090 review](https://www.club386.com/nvidia-geforce-rtx-5090-review/)
- Blackwell 5th-gen tensor cores support FP4 (Hot Chips 2025, RTX 5090 FLUX example) — [Hot Chips 2025 NVIDIA slides](https://hc2025.hotchips.org/assets/program/conference/day1/33_nvidia_blackstein_final.pdf)

### Inferences
- **[EST] Practical heterogeneity policy:** DiLoCo is vendor-agnostic at the protocol level because only compressed pseudo-gradients cross the wire (no NCCL/RCCL collectives), so an RTX 3090, a Radeon (ROCm/PyTorch) and an M-series Mac (MLX or PyTorch MPS) could in principle each run inner steps on the same BF16 weights. Use DyLU (tokens-per-round proportional to speed) + token-weighted merging (Decoupled DiLoCo) so a 3060 contributes fewer tokens rather than stalling a 5090.
- **[EST] Precision:** standardize the exchanged state on BF16 weights/pseudo-gradients; let each node choose its inner-step compute (FP8 on RTX 40/50 via torchao/LLMQ-like kernels, BF16 on RTX 30/Apple/AMD). This is untested at scale — FP8 vs BF16 inner steps produce slightly different update statistics; validate with small ablations before admitting mixed precision.
- **[EST] Verification implication:** cross-vendor/cross-precision runs make bitwise reproducibility impossible, so verification must be statistical (Gauntlet-style loss-delta scoring), not recomputation-hash-based.
- **[EST] Apple Silicon has a real memory advantage** (unified memory 32–192 GB lets a full replica + optimizer fit) but lower BF16 throughput than an RTX 4090; best used first for RL rollouts/inference (proven), later as DiLoCo workers if an MLX inner-loop is written.
- The Agora fleet shift (4090 share fell from 32% to 9%) suggests 24 GB consumer cards were the least competitive participants even within a curated ≥24 GB pool.

### Gaps
- No cross-vendor (NVIDIA+AMD+Apple) LLM pre-training demonstration found for 2025–2026; HetSeq not checked; Prime Intellect heterogeneous-vendor runs not found.
- No source measured BF16-vs-FP8 inner-step mixing inside DiLoCo.
- Official NVIDIA whitepaper numbers were not fetched directly; consumer peak figures below rely on spec aggregators that conflict.

---

## 3. Compute math: sustained TFLOPs, utilization, contributor × months, reachable quality tier

### Takeaway
An RTX 4090 peaks at ~165 TFLOPS dense BF16 (FP32 accumulate); decentralized runs achieve ~20–25% MFU on contributor stages (Agora) and the whole system ~63% of centralized efficiency, and volunteer machines are online only part of the day. **[EST]** A realistic average is ~13–60 effective TFLOPS per RTX 4090-class volunteer, i.e. ~2e20–9e20 FLOP per node per 6 months. 1k nodes × 6 months ≈ 1–6e23 centralized-equivalent FLOP (SmolLM3-3B / OLMo-2-7B / Covenant-72B tier); 10k nodes ≈ 1–6e24 (Llama-3-8B / Qwen3-8B / Apertus-70B tier); 100k nodes ≈ 1–6e25 (Llama-3-70B tier and above) — but no consumer network has yet sustained more than ~60–100 concurrent contributors in a single model run.

### Cited Findings

**Consumer GPU peak throughput (dense, tensor cores)**
- RTX 4090: FP16/BF16 with FP32 accumulate **165.2 TFLOPS dense** (330.4 sparse); FP16-accumulate ~330 dense; FP32 non-tensor 82.6 — [aiwiki RTX 4090](https://aiwiki.ai/wiki/nvidia_geforce_rtx_4090/raw); [Flopper RTX 4090](https://flopper.io/gpu/nvidia-geforce-rtx-4090-24gb/spec-sheet); conflicting: HMC-Tech lists 330.3 for FP32-acc — [HMC-Tech](https://hmc-tech.com/gpu/nvidia-2x-geforce-rtx-4090)
- RTX 3090: FP16/BF16 with FP32 accumulate **71.2 TFLOPS dense** (142.4 sparse); RTX 5090: **209.5 TFLOPS dense** FP32-acc (419 sparse); several sites list 419 dense without stating accumulate mode — [Spheron 5090 specs](https://www.spheron.network/blog/nvidia-rtx-5090-specs/); [NVIDIA dev forum](https://forums.developer.nvidia.com/t/rtx-5090-peak-bf16-tensor-tflops/350543); [Flopper 5090](https://flopper.io/gpu/nvidia-geforce-rtx-5090-32gb)
- RTX 5090 FP8 ~838 TFLOPS and FP4 ~1,676 TFLOPS (dense, as reported by spec aggregators; FP4 sparse 3,352) — [Flopper 5090 vs RTX PRO 6000](https://flopper.io/compare/nvidia-geforce-rtx-5090-32gb-vs-nvidia-rtx-pro-6000-blackwell-workstation-edition); [Flopper spec sheet](https://flopper.io/gpu/nvidia-geforce-rtx-5090-32gb/spec-sheet)
- RTX 3060/4060 (8–12 GB): not looked up this session **[MEM: roughly 25 and 45–60 TFLOPS dense FP16-acc respectively; halve for FP32-acc on GeForce]** — needs verification.

**Achieved utilization**
- Agora/Pluralis-8B: contributor (body) stages MFU 18.6–22.4%, overall 24.2%, 63% of centralized H100 baseline — [arXiv 2607.13332](https://arxiv.org/html/2607.13332)
- Covenant-72B: 94.5% compute utilization (communication-overlap metric, not MFU) on 8×B200 peers — [arXiv 2603.08163v2](https://arxiv.org/html/2603.08163v2)
- MIRI simulation: at 100 Mbps, distributed training costs ~3× more than centralized at 1e25 FLOP — [arXiv 2605.29359](https://arxiv.org/html/2605.29359)
- Centralized reference: SmolLM3 ~29.4% MFU on 384 H100s (secondary) — [LearnOpenCV](https://learnopencv.com/smollm3-explained/); single-node consumer 8-bit: ~50% (LLMQ) — [arXiv 2512.15306](https://arxiv.org/abs/2512.15306)

**Reference model compute budgets**
| Model | Params | Tokens | Compute | Source / basis |
|---|---|---|---|---|
| Pluralis-8B (Jul 2026) | 8.6B | 500B | 3.08e22 (reported) | [arXiv 2607.13332](https://arxiv.org/html/2607.13332) |
| INTELLECT-1 (2024) | 10B | 1T | ~6e22 | [Epoch AI](https://epoch.ai/gradient-updates/how-far-can-decentralized-training-over-the-internet-scale) |
| SmolLM3-3B (Jul 2025) | 3B | 11.2T | ~2.0e23 **[EST 6ND]**; 384 H100 × 24 days | [HF blog mirror](https://hn.jakechampion.name/reader/https://huggingface.co/blog/smollm3); [model card](https://huggingface.co/HuggingFaceTB/SmolLM3-3B-Base/blob/refs%2Fpr%2F4/README.md) |
| OLMo 2 7B | 7B | ~4T **[MEM]** | ~1.8e23 **[EST]** | not verified this session |
| Covenant-72B (Mar 2026) | 72.7B | ~1.1T | 4.8e23 | [arXiv 2605.29359](https://arxiv.org/html/2605.29359) |
| Llama-3-8B (Apr 2024) | 8B | >15T | 6ND ≈ 7.2e23 **[EST]**; 1.3M H100-hours (≈1.9e24 at 40% MFU **[EST]**) | [Llama 3 model card](https://huggingface.co/meta-llama/Meta-Llama-3-8B) |
| Apertus-8B (Sep 2025) | 8B | 15T | ~7.2e23 **[EST 6ND]** | tokens: [Apertus report](https://arxiv.org/pdf/2509.14233) |
| Qwen3-4B (May 2025) | 4B | ~36T | ~8.6e23 **[EST]** | tokens: [Qwen3 report](https://arxiv.org/html/2505.09388v1) |
| Qwen3-30B-A3B | 30B / 3.3B active | ~36T | ~7e23 **[EST, active params]** | tokens: [Qwen3 report](https://arxiv.org/html/2505.09388v1) |
| Qwen3-8B | 8.2B | ~36T | ~1.8e24 **[EST]** | tokens: [Qwen3 report](https://arxiv.org/html/2505.09388v1) |
| Llama-3-70B | 70B | >15T | 6.4M H100-hours; 6ND ≈ 6.3e24 **[EST]** | [Llama 3 model card](https://huggingface.co/meta-llama/Meta-Llama-3-8B) |
| Apertus-70B (Sep 2025) | 70B | 15T | **6.74e24** (reported); ~90 days on 4,096 GPUs | [Apertus report](https://arxiv.org/pdf/2509.14233) |

Note: the brief's "Llama-3-8B ~1.3e24" is between the 6ND estimate (7.2e23) and the GPU-hour-derived estimate (~1.9e24); the 1.3M figure in the model card is GPU-hours, not FLOP.

### Inferences — contributor × time table **[EST, all rows]**

Assumptions: RTX 4090-class node, 165 TFLOPS BF16 dense peak; 6 months = 1.58e7 s. Three scenarios combine MFU while online × fraction of time online (duty cycle):
- Conservative: 20% MFU (Agora body stages) × 40% online → 13 TFLOPS avg → **2.1e20 FLOP/node/6 mo**
- Middle: 30% MFU × 60% online → 30 TFLOPS → **4.7e20**
- Optimistic: 45% MFU (8-bit kernels, DiLoCo with little comm stall) × 80% online → 59 TFLOPS → **9.4e20**
"Centralized-equivalent" applies a further 0.5–0.65 decentralization penalty (Agora 63%; MIRI ~1/3 at 100 Mbps for very large runs).

| Active nodes (4090-class) | Raw FLOP in 6 months (cons / mid / opt) | Centralized-equivalent (≈×0.5–0.65) | Comparable reference budget | Plausible quality tier |
|---|---|---|---|---|
| 100 | 2.1e22 / 4.7e22 / 9.4e22 | ~1–6e22 | Pluralis-8B (3e22), INTELLECT-1 (6e22) | Good 0.5–1.5B dense (≈SmolLM2-1.7B-class, mid-2024); "first credible run" |
| 1,000 | 2.1e23 / 4.7e23 / 9.4e23 | ~1–6e23 | SmolLM3-3B (2e23), OLMo-2-7B (~1.8e23), Covenant-72B (4.8e23) | SOTA-for-size **as of mid-2025** at 3B (needs SmolLM3-quality data); ~Qwen3-4B (8.6e23) at the optimistic end |
| 10,000 | 2.1e24 / 4.7e24 / 9.4e24 | ~1–6e24 | Llama-3-8B, Qwen3-8B (1.8e24), Apertus-70B (6.7e24) | Competitive 8B dense, or a ~30B-A3B MoE at Qwen3-30B-A3B budget; a 70B Apertus-class model only at the high end |
| 100,000 | 2.1e25 / 4.7e25 / 9.4e25 | ~1–6e25 | Llama-3-70B (~6e24) to Llama-3.1-405B class **[MEM ~3.8e25]** | Frontier-of-2024 open-weights; but no system has shown coordination at this size |

Cross-checks and caveats **[EST]**:
- A 4090 at middle-scenario 30 TFLOPS average trains a 1.5B model at ~3,300 tokens/s while online → ~0.17B tokens/day/node when averaged. 100 nodes ≈ 17B tokens/day → 1T tokens in ~2 months.
- Electricity: RTX 4090 TGP ~450 W **[MEM]**, RTX 5090 ~575 W **[MEM]** (igor'sLAB titles its review "the 600 watt powerhouse" — [igor'sLAB](https://www.igorslab.de/en/nvidia-geforce-rtx-5090-founders-edition-review-the-600-watt-powerhouse-in-gaming-and-lab-tests/)). At 60% duty, a 4090 PC (~550 W at the wall) uses ~240 kWh/month → ~$35–75/month at $0.15–0.30/kWh. 10k nodes ≈ $4–9M/year of donated electricity — the incentive design must cover this.
- "SOTA" realistically means **SOTA-for-its-size at small scale (1–4B) or a competitive small-active-parameter MoE**, not frontier. Dense 1–4B SOTA moves fast (Qwen3-4B used 36T tokens), so the bar in late 2026/2027 will be above the 2025 references in the table.
- The largest node count Agora admitted was ~60–63 concurrent (cap 60) and ~745 trainer GPUs — 1k–10k concurrent home nodes would be 15–150× beyond anything demonstrated.

### Gaps
- No primary NVIDIA whitepaper fetched; spec aggregators conflict on FP32-accumulate figures (esp. RTX 5090: 209.5 vs 419 TFLOPS dense).
- No measured duty-cycle (hours online/day) for gaming-GPU volunteers in an ML run; 40–80% is my assumption.
- OLMo 3 7B/32B token counts and FLOP not found this session; OLMo 2 numbers are from memory.
- No public MFU figure for full-replica DiLoCo on consumer GPUs over home internet.

---

## 4. Architecture choice for consumer training AND consumer inference

### Takeaway
For decentralized training on 8–32 GB nodes, a **small dense model (0.5–3B) is the only architecture that fits a full DiLoCo replica per node** and is the right MVP. For the scale-up target, a **sparse MoE with small active parameters** (Qwen3-30B-A3B-like, ~3B active) is the best inference fit for consumer hardware and its experts are natural units of work, but trained as a whole it does not fit one consumer GPU and expert-parallel all-to-all over WAN is unproven — so the realistic path is **dense seed → branch experts trained by independent DiLoCo groups (BTX/FlexOlmo) → merge + router fine-tune**. Native ternary (BitNet b1.58) is proven only to 2B/4T tokens and does not reduce training memory; prefer BF16/FP8 pre-training plus a late quantization-aware phase.

### Cited Findings
- [BG, Mar 2024] BTX: dense seed → embarrassingly parallel expert training → FFNs merged as MoE experts, router fine-tuned — [arXiv 2403.07816](https://arxiv.org/abs/2403.07816)
- [BG, 2025] FlexOlmo: independently trained experts anchored to a frozen public model, merged without joint training; up to 37B total / 20B active; beats standard MoE at equal FLOPs — [arXiv 2507.07024](https://arxiv.org/abs/2507.07024)
- [BG, 2024] DiPaCo: 256 paths × 150M params; only one path runs at inference — inference-friendly for small devices — [arXiv 2403.10616](https://arxiv.org/abs/2403.10616)
- [BG, 2025] SparseLoCo validated on a 645M-A273M MoE (not just dense) — [arXiv 2508.15706](https://arxiv.org/abs/2508.15706) (cited in prior notes)
- [2026-04] Decoupled DiLoCo reports competitive quality on dense and MoE — [arXiv 2604.21428](https://arxiv.org/abs/2604.21428)
- [BG, JMLR 2025] BitNet b1.58 matches FP16 Transformers at equal size/tokens on perplexity and end tasks in the paper's range; gap shrinks with scale — [JMLR BitNet](https://jmlr.org/papers/v26/24-2050.html); [HF paper 2402.17764](https://huggingface.co/papers/2402.17764)
- [BG, 2025] BitNet b1.58 2B4T: first open native 1-bit model trained from scratch at 2B on 4T tokens (Microsoft) — [Azure AI Labs page](https://labs.ai.azure.com/?p=900)
- [BG, ACL Findings 2025] Starting in 16-bit and switching to 1.58-bit later beat full 1.58-bit-from-scratch across 11 tasks; hybrid stays closer to 16-bit baselines — [ACL Findings 2025.694](https://preview.aclanthology.org/display_plenaries/2025.findings-acl.694.pdf)
- No 2026 BitNet-from-scratch scaling results found in search — [search, 2026-11-05; see gaps]
- [2026-07] Pluralis used LFM2.5-8B-A1B (8.3B total, ~1B active MoE) for consumer-Mac RL — an example of the "small-active MoE" class used on consumer hardware — [Pluralis blog](https://pluralis.ai/blog/rl-post-training-on-macs/)

### Inferences **[EST]**
- **Inference fit:** a 30B-A3B MoE at 4-bit is ~16–18 GB of weights → runs on a 24 GB GPU or 32 GB Mac with ~3B-active speed; an 8B dense at 4-bit (~5 GB) runs on 8 GB cards. So "train small dense now, train a 20–30B-total / 2–4B-active MoE later" gives the community a model its own members can run.
- **Training fit:** an expert-group design maps well to the volunteer population: e.g., 16–64 experts each trained (as a dense "branched" FFN-augmented copy of a ~1–3B seed) by its own DiLoCo cohort of 50–500 nodes, merged centrally. Each cohort only exchanges deltas of its own branch; cross-cohort communication happens once (at merge). This turns "data/domain shards" into "expert shards" and naturally supports opt-in data (FlexOlmo).
- **Ternary/BitNet:** native ternary training keeps full-precision latent weights and optimizer state, so it does not relieve consumer-GPU training memory; its payoff is inference. Recommended: BF16 (or FP8 on RTX 40/50) pre-training, then a QAT/ternary-conversion phase on the final ~10% of tokens (consistent with the ACL 2025 hybrid finding).
- **Optimizer:** Muon inner steps (MuLoCo) store one momentum buffer instead of Adam's two, saving ~4 B/param of offloaded state and compressing pseudo-gradients to 2 bits (prior notes) — a good fit for RAM-limited gaming PCs.

### Gaps
- No public evidence of BTX/FlexOlmo-style expert training performed by volunteers or over WAN.
- gpt-oss-20b/120b and LFM2-8B-A1B architecture/training-FLOP details not researched this session.
- No 2026 status found for BitNet beyond 2B4T (search found nothing newer).

---

## 5. Data pipeline: shards, bandwidth, storage, tokenization

### Takeaway
Data is not the bottleneck: at realistic consumer throughput a node consumes only ~0.1–0.6B tokens/day (~0.2–1.2 GB/day pre-tokenized), far below model-update traffic. Pre-tokenize centrally, publish deterministic shard assignments (which also enables Gauntlet-style assigned-vs-unassigned anti-copy checks), and stream from object storage/HF.

### Cited Findings
- Pluralis-8B trained on FineWeb-Edu (500B tokens) — [arXiv 2607.13332](https://arxiv.org/html/2607.13332); Covenant-72B on DCLM (~1.09T tokens) with assigned data per peer and a penalty if a peer scores better on random data than its assigned data — [arXiv 2603.08163v2](https://arxiv.org/html/2603.08163v2)
- Psyche's 2025 data mix: FineWeb-Edu, FineWeb2-HQ, FinePDFs, DCLM, Stack-Edu, Nemotron-CC-Math — [Nous blog](https://nousresearch.com/the-next-phase-of-psyche)
- SmolLM3 used 11.2T tokens in three stages mixing web, math and code — [HF blog mirror](https://hn.jakechampion.name/reader/https://huggingface.co/blog/smollm3)
- Pluralis requires 80 GB free disk per contributor — [Pluralis requirements](https://pluralis.ai/docs/quick-start/requirements/)

### Inferences **[EST]**
- Storage per token pre-tokenized: 2 bytes (uint16, vocab ≤65,536) or 4 bytes (larger vocabs such as Llama-3/Qwen ~128–152k). Raw text is ~4 bytes/token; gzip/zstd parquet ~1–2.
- Per-node consumption: a 4090 training a 1.5B model at ~30 effective TFLOPS ≈ 3,300 tok/s online → ~0.17–0.3B tokens/day → ~0.7–1.2 GB/day with 4-byte tokens. A 10 GB rolling cache suffices; total corpus never needs to be on any node.
- Choose a ≤65k vocab for the MVP to halve data bytes and embedding/LM-head memory (the embedding of a 150k vocab × 2048 dim is 0.3B params — a large fraction of a 1B model).
- Validators need held-out shards; keep a public "unassigned" pool for anti-copy scoring.

### Gaps
- Exact FineWeb-Edu/DCLM on-disk sizes and licenses were not re-checked this session **[MEM: FineWeb-Edu ≈1.3T tokens; DCLM-baseline ≈3.8–4T tokens]**.

---

## 6. Node software practicality: client, sandboxing, power/thermals, churn

### Takeaway
The state of the art client (Pluralis Agora) is Linux/WSL2-only, needs inbound port forwarding, 70 GB RAM/GPU and a NA location — far from "one-click" for gamers. The RL client pattern (Pluralis Stoa: outbound HTTPS only, object storage, join/leave/crash freely) is the friendlier template. Churn is heavy: Agora saw 669 joins / 607 departures with ~61 live nodes over 40 days (**[EST]** mean session ≈ 3–4 days), and BOINC data show volunteer hosts churn "several times a day" with average host lifetime ~91 days.

### Cited Findings
- Agora client: Linux or Windows 10/11 + WSL2 with CUDA; macOS unsupported; inbound TCP 49200+ per GPU, router port forwarding + WSL2 port proxy for home machines; 200/100 Mbps speed test at join; HF token for identity; ≤5 peers per HF account — [Pluralis requirements](https://pluralis.ai/docs/quick-start/requirements/)
- Agora admission: concurrent admissions capped at 60 (live fleet avg ~61, peak 63); ~70 distinct contributors on a typical day, 108 on the busiest; **3,334,054 join requests from 612 clients, 99.98% rejected; 208 clients admitted at least once; median wait 5.8 h** — [arXiv 2607.13332](https://arxiv.org/html/2607.13332)
- Stoa (Pluralis RL): outbound HTTPS only, Cloudflare R2, workers join/leave/crash without stalling, ~100 Mbps home internet — [Pluralis blog](https://pluralis.ai/blog/rl-post-training-on-macs/)
- BOINC: 330,000+ hosts analyzed; average host lifetime ~91 days (undercounted method); client resets create "new" hosts — [Anderson & Fedak, arXiv cs/0602061](https://arxiv.org/abs/cs/0602061)
- BOINC CPU-availability traces from ~230,000 hosts (Apr 2007–Jan 2009); volunteer resources show frequent churn (several times a day), best suited to high-throughput workloads — [Javadi et al. MASCOTS 2009](https://staff.cdms.westernsydney.edu.au/~bjavadi/papers/javadi_mascots09.pdf); [Javadi IPCCC 2013](https://staff.cdms.westernsydney.edu.au/~bjavadi/papers/javadi_ipccc13.pdf); [Kondo, Andrzejak, Anderson 2008](https://aip.ifi.uni-heidelberg.de/fileadmin/papers/2008/Grid_2008_-_Kondo__Andrzejak__Anderson.pdf)
- Unsloth (fine-tuning) supports NVIDIA CUDA capability ≥7.0 (incl. RTX 20–50, Blackwell, DGX Spark), AMD and Intel GPUs; Apple/MLX training listed in Unsloth Studio but "in the works" for Unsloth Core — [Unsloth requirements](https://unsloth.ai/docs/get-started/beginner-start-here/unsloth-requirements)

### Inferences **[EST]**
- **Client design:** ship (a) a Windows-native or WSL2-bundled installer with a pinned CUDA/PyTorch build (sm_86/89/120 arch lists verified, since FP8 kernels need sm_89), (b) Linux Docker image with NVIDIA Container Toolkit, (c) no inbound ports — all exchange via outbound HTTPS to object storage/aggregators (Covenant and Stoa both did this). Pipeline-parallel (Agora) needs peer-to-peer activation traffic and therefore inbound connectivity/NAT traversal — another reason to start with DiLoCo.
- **Sandboxing:** run the trainer in a container with no host filesystem access except a cache dir; signed model/code bundles; the protocol should never execute contributor-supplied code. (No source found documenting a decentralized-training client security model.)
- **Churn design:** DiLoCo outer rounds of 15–30 min with DyLU mean a node that disappears loses at most one round of its own work; Decoupled-DiLoCo-style quorum + grace window means the global step never waits for it. Assume 40–60% duty cycle, sessions of hours-to-days, and a long tail of one-time joiners.
- **Thermals/power:** gaming PCs at 100% GPU load 24/7 hit fan noise/heat limits; expose a power-limit slider (e.g., 70% TGP costs typically ~10–15% throughput **[MEM]**) and "only when idle" scheduling — this directly lowers duty cycle in the compute table.
- **Demand signal:** Agora had ~10× more would-be clients (612) than slots (60), so willingness exists; the constraint was protocol capacity, not volunteer supply.

### Gaps
- No Folding@home-specific uptime/session statistics found; no GPU-volunteer duty-cycle data.
- No published security/sandbox design for Agora, Psyche or Templar clients found.
- Pluralis Points/rewards mechanics not read.

---

## 7. Fine-tuning / RL on consumer hardware as an earlier milestone

### Takeaway
Fine-tuning and RL are much easier and already proven on consumer hardware: QLoRA fits an 8B model in ~6 GB and a 32B in ~26 GB (Unsloth), and decentralized RL with consumer Macs generating rollouts for a central trainer is demonstrated (Pluralis, Jul 2026). This is the right first public milestone before pre-training.

### Cited Findings
- Unsloth minimum VRAM: QLoRA 4-bit / LoRA 16-bit — 3B: 3.5 / 8 GB; 7B: 5 / 19 GB; 8B: 6 / 22 GB; 14B: 8.5 / 33 GB; 27B: 22 / 64 GB; 32B: 26 / 76 GB; 70B: 41 / 164 GB — [Unsloth requirements](https://unsloth.ai/docs/get-started/beginner-start-here/unsloth-requirements)
- LLMQ: 7B full train/fine-tune on a single 16 GB gaming card (8-bit) — [arXiv 2512.15306](https://arxiv.org/abs/2512.15306)
- Pluralis RL on Macs: 14 Macs saturated one B200 trainer; 82 MB median deltas vs 9 GB checkpoint; pass@1 29% → 63% — [Pluralis blog](https://pluralis.ai/blog/rl-post-training-on-macs/); prime-rl/verifiers environments (prior notes) — [prime-rl](https://github.com/PrimeIntellect-ai/prime-rl)
- Hermes 4.3 36B post-training over Psyche (late 2025) matched/beat a centralized control on some benchmarks (prior notes) — [HF model card](https://huggingface.co/NousResearch/Hermes-4.3-36B)

### Inferences **[EST]**
- Milestone ladder: (M0) RL rollout mining on gaming GPUs/Macs for an existing open model (e.g., a Qwen3-4B/8B or 30B-A3B at 4-bit) with verifiable math/code rewards; (M1) DiLoCo-merged LoRA/QLoRA fine-tuning across nodes (LoRA deltas are tiny: tens of MB); (M2) full fine-tuning / continued pre-training of a ≤3B model via DiLoCo; (M3) from-scratch pre-training.
- RL rollout generation needs only inference VRAM (a 4-bit 8B model ~5–6 GB), so 8 GB RTX 3060/4060 cards are useful here even though they are marginal for pre-training.

### Gaps
- No public data on DiLoCo-merged LoRA across volunteers; GRPO VRAM on consumer GPUs not documented on the Unsloth page.

---

## 8. Bottom line: realistic MVP and scale-up path

### Takeaway
**[EST]** The most realistic MVP is a **DiLoCo/SparseLoCo(-MuLoCo) data-parallel run of a ~1–1.5B dense model (≤65k vocab) on ~100–200 NVIDIA nodes with ≥12–16 GB VRAM and ≥32–64 GB RAM, ~1–2T tokens of FineWeb-Edu/DCLM, over ~2–4 months** (~1–3e22 FLOP, i.e., Pluralis-8B/INTELLECT-1 compute scale) — preceded by an RL-rollout/fine-tuning milestone. Scale-up: 1k nodes → 3B SOTA-for-size attempt (~2e23); then 10k nodes → expert cohorts merged into a ~20–30B-total / 2–4B-active MoE (~1e24), with an optional Agora-style pipeline "pro tier" for 24–32 GB nodes on fast links.

### Cited Findings (anchors used)
- Demonstrated consumer-ish ceiling: 8.6B / 500B tokens / 40 days / ~60 concurrent contributors + Pluralis-run head/tail / 3.08e22 FLOP / 63% efficiency — [arXiv 2607.13332](https://arxiv.org/html/2607.13332)
- Bandwidth that worked for full-replica compressed DiLoCo: ~70 s comms per 20-min round on 110 Mb/s uplinks with >146× compression — [arXiv 2603.08163v2](https://arxiv.org/html/2603.08163v2)
- 7B trainable on a 16 GB gaming card with 8-bit + offload (single node) — [arXiv 2512.15306](https://arxiv.org/abs/2512.15306)
- SmolLM3-3B budget: 11.2T tokens, 384 H100 × 24 days — [HF blog mirror](https://hn.jakechampion.name/reader/https://huggingface.co/blog/smollm3)

### Inferences **[EST]**
**MVP spec (Phase 1, ~3 months):**
- Model: 1.2–1.5B dense decoder (Llama/Qwen-style, GQA, ≤65k vocab, 2–4k context), BF16 master weights; FP8 inner compute optional on RTX 40/50.
- Nodes: 100–200 NVIDIA (RTX 3090/4090/5090 preferred; 4060 Ti 16 GB/3060 12 GB admissible with smaller micro-batch and offload); ≥32 GB system RAM (≥64 GB recommended); 10 Mbps up / 50–100 Mbps down minimum.
- Algorithm: DiLoCo outer loop, H≈30–100 inner steps (~15–30 min rounds), SparseLoCo top-k + 2-bit + error feedback (or MuLoCo for lower optimizer RAM), DyLU for heterogeneity, Decoupled-DiLoCo quorum/grace window, Gauntlet loss-score validation, exchange via object storage (outbound HTTPS only).
- Expected compute: 150 nodes × ~30 TFLOPS avg × 7.9e6 s (3 months) ≈ 3.5e22 raw → ~2e22 centralized-equivalent → ~2–3T tokens for 1.5B (≈Chinchilla ×70; SmolLM2-1.7B-class target, which used ~11T tokens **[MEM]**, so expect somewhat below it unless the run extends).
- Per-round traffic (1.5B): ~20 MB up, ~1–3 GB down (merged sparse update) → feasible on 100 Mbps-down homes at ~5–15% overhead.
- Success criterion: loss curve within a few % of a centralized reference of equal tokens (Agora's "small margin"), plus standard 1–2B benchmarks (HellaSwag/ARC/MMLU) versus SmolLM2-1.7B/Qwen2.5-1.5B.

**Scale-up path:**
1. Phase 0 (now–3 mo): RL rollout + QLoRA/DiLoCo-LoRA fine-tuning network on existing open models (8 GB cards and Macs useful).
2. Phase 1 (3–6 mo): 1–1.5B from-scratch MVP above.
3. Phase 2 (6–12 mo, ~1k nodes): 3B dense, ~6–10T tokens, ~2e23 FLOP → attempt "SOTA-for-3B" (SmolLM3-class); requires offloaded optimizer and ≥24 GB nodes or LLMQ-style 8-bit on 16 GB.
4. Phase 3 (12–24 mo, ~5–10k nodes): BTX/FlexOlmo expert cohorts branched from the 3B seed → merge into ~20–30B-total / ~3B-active MoE (~1e24 FLOP, Qwen3-30B-A3B budget class) that members can run at 4-bit on 24 GB GPUs/32 GB Macs. Add Apple (MLX) and AMD (ROCm) DiLoCo workers once a vendor-neutral inner loop is validated.
5. Optional pro tier: Agora-style pipeline for 8B+ dense among 24–32 GB nodes with ≥100 Mbps up in one latency region.

**Key risks:** (i) coordination beyond ~60–200 concurrent nodes is undemonstrated; (ii) download bandwidth of merged updates, not upload, binds at ≥7B full replicas; (iii) donated electricity (~$35–75/node/month) needs an incentive; (iv) the "SOTA" bar for small models keeps rising (36T-token Qwen3-4B); (v) cross-vendor and mixed-precision DiLoCo is unvalidated.

### Gaps
- No public consumer-home (not cloud/marketplace) pre-training run exists to calibrate duty cycle and MFU; all MVP throughput figures are estimates.
- Download-side bandwidth of SparseLoCo aggregation at 100+ peers was not found quantified in sources; my 1–3 GB figure is an estimate.
