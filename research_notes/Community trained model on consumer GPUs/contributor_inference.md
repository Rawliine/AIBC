# Contributor Inference: Making a Community-Trained Model Useful on Consumer Hardware, and Allocating It Fairly (as of 2026-11-05)

Scope note: this covers the AIBC "people's datacenter" pivot, where consumers contribute GPUs to train one large model and get inference back. Notes compiled 2026-11-05 from 18 search/fetch calls. Many performance numbers come from community or vendor posts rather than controlled benchmarks, and each one is labelled. Some 2026 search results name models or hardware released after my knowledge cutoff (Kimi K2.6/K2.7/K3, GLM-5.3, Qwen3.5, M5 Ultra). I report these as the sources state them and did not verify them myself.

---

## 1. Running big models on a single consumer machine in 2026 (MoE offload, quantization, tok/s)

### Takeaway
Big sparse MoE models are now practical on one consumer machine. The working pattern keeps attention, shared layers and KV cache on the GPU and puts the routed experts in system RAM (llama.cpp `--n-cpu-moe`, KTransformers). Measured results: gpt-oss-120b (5.1B active) on one RTX 5090 runs at about 25–85 tok/s. Qwen3-235B-A22B runs at about 14 tok/s on a 4090 with a server CPU. A 512 GB Mac Studio M3 Ultra runs DeepSeek-V3/R1-class at about 17–20 tok/s and Kimi-K2-class at about 13–26 tok/s. The binding constraints are **active parameters × bits per weight ÷ RAM bandwidth**, and total RAM.

### Cited Findings
**MoE expert offloading, NVIDIA + system RAM**
- gpt-oss-120b is a 59 GB model in native MXFP4. It does not fit in 32 GB of VRAM, but with llama.cpp `--n-cpu-moe` (attention on the GPU, experts in system RAM) only 5.1B of its 117B parameters are active per token. One user reported about 47 tok/s generation and about 473 tok/s prompt processing at 512 context on an RTX 5090 (single-user report, 2026). — [witcheer on X](https://x.com/witcheer/status/2062103386615398642)
- The official llama.cpp gpt-oss guide suggests starting a 5090 at `--n-cpu-moe 20–21` and adjusting until VRAM is nearly full (discussion #15396, Aug 2025 onward). — [llama.cpp Discussion #15396](https://github.com/ggml-org/llama.cpp/discussions/15396)
- Hardware-Corner benchmarks of MoE-offload on RTX 3090/5090 show about 82–85 t/s for short prompts on a 5090. The extracted table was hard to parse, so these figures should be checked on the page. — [Hardware Corner](https://www.hardware-corner.net/gpt-oss-offloading-moe-layers/)
- An estimate (not a measurement) puts gpt-oss-120b at about 25 tok/s on an RTX 5090 with partial offload and 64 GB of system RAM. — [LLaMA Builds](https://www.llamabuilds.ai/models/gpt-oss-120b/requirements)
- Decode speed falls with context. A community figure for gpt-oss-120b on a DGX Spark is about 60.6 tok/s at empty context and about 40.6 tok/s at 32K context (2026 roundup, secondary). — [presenc.ai benchmarks 2026](https://presenc.ai/research/local-llm-tokens-per-second-benchmarks-2026)
- KTransformers (kvcache-ai / Tsinghua MadSys, SOSP '25, Oct 13–16 2025) is a CPU/GPU hybrid MoE engine with AMX CPU kernels. It reports prefill speedups of 4.62–19.74× and decode speedups of 1.25–4.09× over prior hybrid systems. On DeepSeek-V3-0324, V2.5 and Qwen2-57B, decode is 2.42–4.09× faster than Fiddler and 1.25–1.76× faster than llama.cpp at full precision. The "Expert Deferral" technique adds about 33% decode throughput with under 0.5% accuracy loss. These figures come from secondary copies of the abstract and a SGLang upstreaming issue; I did not read the full paper (DOI 10.1145/3731569.3764843). — [SGLang issue #11425](https://github.com/sgl-project/sglang/issues/11425); [CSDN abstract copy](https://adg.csdn.net/695337cd5b9f5f31781be1ca.html)
- KTransformers claims DeepSeek-R1/V3 runs on a single 24 GB GPU with 382 GB DRAM. The team reported up to 286 tok/s prefill and 14 tok/s decode on 2× Xeon plus a 24 GB GPU (Feb 2025). — [KTransformers DeepSeek tutorial](https://kvcache-ai.github.io/ktransformers/en/DeepseekR1_V3_tutorial.html); [r/LocalLLaMA thread, Feb 10 2025](https://redlib.ssps.io/r/LocalLLaMA/comments/1ilzcwm/671b_deepseekr1v3q4_on_a_single_machine_2_xeon/mc6xv03)
- Qwen3-235B-A22B on KTransformers with a 4th-gen Xeon and an RTX 4090 reaches 13.8 tok/s for a single request and 24.4 tok/s aggregate with 4 parallel requests (2025 community post citing the KTransformers AMX doc; I could not verify the exact 235B figures in the doc itself). The project says consumer CPUs (i9-14900KF, dual-channel DDR5-4000 + 4090) can run 235B-A22B, but gives no tok/s figure for that setup. — [cyberbus post](https://cyberbus.net/post/539); [KTransformers AMX.md](https://github.com/kvcache-ai/ktransformers/blob/main/doc/en/AMX.md)
- KTransformers' Qwen3.5 guide (2026) lists 4× RTX 4090 and at least 800 GB of system RAM as the minimum. Newer frontier-open MoEs have therefore grown beyond a single consumer box. — [KTransformers Qwen3.5.md](https://github.com/kvcache-ai/ktransformers/blob/main/doc/en/Qwen3.5.md)
- A later system targeting OSDI '26 (arXiv 2606.10493, June 2026) reports 28 tok/s on INT4 DeepSeek-R1, 1.25× faster than KTransformers. — [arXiv 2606.10493](https://arxiv.org/html/2606.10493)
- At INT4, Qwen3-235B is about 117 GB, which exceeds any consumer card's VRAM. Running it on consumer hardware therefore requires RAM offload. — [Spheron guide](https://www.spheron.network/blog/deploy-qwen3-gpu-cloud/)

**Apple Silicon (unified memory)**
- DeepSeek-V3-0324 in 4-bit runs at more than 20 tok/s via mlx-lm on a 512 GB Mac Studio M3 Ultra (Mar 2025). — [VentureBeat](https://venturebeat.com/ai/deepseek-v3-now-runs-at-20-tokens-per-second-on-mac-studio-and-thats-a-nightmare-for-openai)
- DeepSeek R1-0528 4-bit MLX: 20.3 tok/s with 380.7 GB peak RAM on an M3 Ultra 512 GB (measured, July 2026). The same source measured Kimi K2.7 Code at 24.6 tok/s on llama.cpp. — [ai-kizai.com benchmarks](https://ai-kizai.com/benchmarks/512gb)
- Another source puts DeepSeek 4-bit at 17–18 tok/s on MLX under 200 W, against about 6 tok/s with llama.cpp on the same Mac. — [localaimaster.com](https://localaimaster.com/blog/apple-silicon-ai-buying-guide)
- Kimi K2.6 at about 3.4–3.6 bpw on one M3 Ultra: about 20–26 tok/s on fresh context, about 13 tok/s past 7–13K tokens, and under 7 tok/s at longer contexts (2026 reviewer). — [rentamac.io](https://rentamac.io/run-kimi-k2-on-mac/)

**Quantization and native low-bit**
- OpenAI shipped gpt-oss natively in MXFP4, so a 117B model is about 59 GB at release with no community re-quantization step. — [witcheer on X](https://x.com/witcheer/status/2062103386615398642); [NVIDIA RTX AI Garage blog](https://blogs.nvidia.com/blog/rtx-ai-garage-openai-oss)
- Gemma 3 QAT (Apr 2025): about 5,000 fine-tuning steps of quantization-aware training, using the BF16 model's probabilities as targets. The 27B int4 model needs 14.1 GB for weights (54 GB in BF16) and the 12B needs 6.6 GB, small enough for an 8 GB RTX 4060 Laptop. Releases come in int4/Q4_0 for Ollama and llama.cpp. — [Google Developers Blog](https://developers.googleblog.com/en/gemma-3-quantized-aware-trained-state-of-the-art-ai-to-consumer-gpus/); [Gemma 3 Technical Report](https://arxiv.org/pdf/2503.19786)
- NVFP4 QAT for Gemma 3 12B/27B is available via TorchAO + Axolotl and is labelled "prototype". The headline numbers are from B200, not RTX 50. — [PyTorch blog](https://pytorch.org/?p=47934)
- BitNet b1.58 2B4T (Microsoft, Apr 2025): the technical report gives about 29 ms per output token on an i7-13800H with 8 threads (about 34 tok/s by my arithmetic), against 48 ms for Llama 3.2 1B and 65 ms for Qwen2.5 1.5B (secondary summaries). bitnet.cpp claims a synthetic 100B BitNet config runs at about 5–7 tok/s on one CPU (6.58 tok/s on an M2 Ultra), with 1.37–5.07× speedups on ARM. No large natively ternary model has been released. — [wavect.io](https://wavect.io/blog/bitnet-cpu-llm-ram-requirements/); [emelia.io](https://emelia.io/hub/bitnet-1bit-llm-cpu-inference); primary report: [arXiv 2504.12285](https://arxiv.org/html/2504.12285v1) (not fetched)

### Inferences
- Rule of thumb (estimate): decode tok/s ≈ effective memory bandwidth ÷ (active params × bytes/param). Dual-channel DDR5 is about 80–100 GB/s and GPU VRAM is about 1–1.8 TB/s. A model with about 3–5B active parameters at about 4 bits (about 2–3 GB read per token) stays fast even when most experts sit in DDR5. A 22–37B-active model at 4 bits drops to roughly 5–15 tok/s on desktop RAM. This is why gpt-oss-120b (5.1B active) is far more usable on a 5090 than Qwen3-235B (22B active) or DeepSeek (37B active).
- Total RAM is the other limit. 64–128 GB of desktop RAM plus 24–32 GB of VRAM holds about 100–200B total parameters at 4 bits. Kimi-class (about 1T) and DeepSeek-class (671B) models do not fit on typical gaming PCs and need 512 GB Macs or multi-node setups.
- For AIBC, if the flagship has more than about 200B total parameters or more than about 10B active, most contributors with 8–32 GB of VRAM cannot run it locally. A distilled or nested family is needed (Section 3).

### Gaps
- No primary, controlled 2026 benchmark found for Qwen3-235B-A22B on an RTX 5090 with 128–256 GB DDR5, or for DeepSeek/Kimi on a single 4090/5090.
- Not researched within the call budget: ik_llama.cpp numbers, EXL3/QTIP quality-vs-bpw data, PowerInfer-2 and Fiddler 2026 status, NVFP4 inference throughput on RTX 50 consumer cards, and speculative-decoding speedups (EAGLE-3/MTP) on consumer hardware. These are open items and should not be filled from memory.

---

## 2. Distributed inference across contributors' machines

### Takeaway
Pooling consumer machines works well over **LAN/Thunderbolt** (exo with RDMA on Macs, prima.cpp on home Wi-Fi clusters). Over the **public internet** it adds capacity, not speed. Petals-style swarms reached about 6 tok/s for 70B models. Gradient's Parallax (2025) is the best current scheduler design for heterogeneous volunteer GPUs. Pluralis's Unextractable Protocol Models (May 2026) make the swarm *required* for inference by design, with about 3% latency overhead. Prompt privacy across untrusted nodes is still unsolved without TEEs.

### Cited Findings
- **Petals:** throughput "reaching 6 tokens/sec for a 70B model" (as characterized in the 2026 UPM paper). Petals has no protection against model extraction. I found no 2026 Petals release or status update. — [UPM paper, arXiv 2605.23464](https://arxiv.org/pdf/2605.23464); [Petals paper](https://arxiv.org/pdf/2209.01188)
- **prima.cpp** (Li et al., arXiv 2504.08791, Apr 2025; ICLR 2026): runs 30–70B models on heterogeneous home devices with mixed CPU/GPU, low RAM/VRAM, slow disks and Wi-Fi. It uses pipelined-ring parallelism to overlap disk I/O, compute and communication, and the Halda scheduler for device selection and placement. A 70B model on 4 home devices reaches **674 ms/token TPOT (about 1.5 tok/s)** with under 6% memory pressure per device. TPOT is 5–17× lower than llama.cpp, exo and dllama (distributed-llama), and the system stays OOM-free. The code was at Lizonghang/prima.cpp; the ICLR listing points to a Gitee mirror, and the author's GitHub account was reportedly blocked. — [ICLR 2026 proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/e991e5587c1daa49bbf9a818b3f02f9a-Abstract-Conference.html); [arXiv v1](https://arxiv.org/html/2504.08791v1); [HF paper page](https://huggingface.co/papers/2504.08791)
- **Parallax** (Gradient, HKUST, NUS; arXiv 2509.26182, Sep 30 2025; code GradientHQ/parallax): a decentralized serving system with a two-phase scheduler. Phase 1 places each replica's layers across heterogeneous GPUs under memory and bandwidth limits. Phase 2 selects a GPU pipeline per request, stitching layers from different replicas into end-to-end chains. Tested on real volunteer nodes, it "consistently reduces latency and increases throughput relative to decentralized baselines". The abstract gives no numbers. — [arXiv 2509.26182](https://arxiv.org/abs/2509.26182); [Gradient Parallax PDF (also covers Mac/MLX clusters)](https://gradient.network/parallax.pdf)
- Gradient claimed "100K+ requests served by Parallax in 2 weeks, 6 continents… a handful of consumer GPUs" (company post, unaudited). — [Gradient on X](https://x.com/Gradient_HQ/status/1940938259682808319)
- **exo** (exo-explore/exo): exo 1.0 added RDMA over Thunderbolt 5 (needs macOS Tahoe 26.2 or later). The release date conflicts across sources: Dec 2025 in one, Apr 2026 in another. Reported inter-Mac latency drops from about 300 µs to about 3 µs. Every node must connect directly to every other with TB5 cables, all on the same macOS build. — [exo GitHub](https://github.com/exo-explore/exo); [Macfax guide](https://macfax.com/blog/at-home-mac-inference-cluster-the-complete-2026-guide); [runaihome RDMA guide](https://runaihome.com/blog/mac-studio-cluster-rdma-thunderbolt5-trillion-parameter-2026/)
- Four 512 GB M3 Ultra Studios (about 2 TB pooled, about $40K) ran Kimi K2 Thinking at about 25 tok/s with about 2 s TTFT and under 450 W (single reviewer). DeepSeek V3.1 on 4 nodes ran at about 32.5 tok/s, and a single Studio is "simpler and slightly faster per token" when the model fits. — [Creative Strategies](https://creativestrategies.com/research/running-a-1t-parameter-model-on-a-40k-mac-studio-cluster/); [runaihome](https://runaihome.com/blog/mac-studio-cluster-rdma-thunderbolt5-trillion-parameter-2026/)
- EXO Labs says Apple features exo on M5 Ultra Mac Studio / M5 Pro Mac Mini pages. It claims 4× M5 Ultra reaches about 4.8 TB/s aggregate bandwidth and runs "Kimi K3 and GLM-5.3 at API speeds" (company post, 2026, unverified). — [EXO Labs on X](https://x.com/exolabs/status/2092320487019880735)
- On NVIDIA (pooling RTX 3090s), exo "adds capacity, not speed", and cost comparisons against NVIDIA boxes are less favorable than before (2026 commentary). — [runaihome exo 2026](https://www.runaihome.com/blog/exo-framework-distributed-vram-local-ai-2026/)
- **Pluralis Unextractable Protocol Models** (Long et al., arXiv 2605.23464, May 22 2026): the model is split across participants and random invertible transforms are injected at shard boundaries over time, so shards from different times cannot be combined and no one holds usable full weights. Inference overhead with a transform every 30 s: about **3% latency, 0.1% bandwidth, 10% GPU memory**. Training overhead is 1.6% time and under 1% memory. Tested only on Qwen2.5-0.5B and Llama-3.2-1B, with ΔPPL under 0.01 in FP32. An earlier Pluralis blog says unextractability at inference relies on a trusted authority assigning layers and neighbors. **So inference requires the swarm, by design.** — [arXiv 2605.23464](https://arxiv.org/abs/2605.23464); [Pluralis blog](https://pluralis.ai/blog/protocol-learning-protocol-models/)
- Pluralis's live run reportedly reached 18–25% MFU across consumer RTX 4090s and 6000s in 50 cities (newsletter, unverified). — [TLDR Crypto 2026-05-25](https://tldr.tech/crypto/2026-05-25)

### Inferences
- Internet pipeline parallelism estimate: each token crosses every pipeline stage. With about 20–80 ms RTT per home-to-home hop and 4–8 stages, the network alone costs about 0.1–0.6 s per token, which matches Petals' ~6 tok/s best case and prima.cpp's ~1.5 tok/s for 70B. This is acceptable for batch or agent jobs and poor for chat. Running **whole replicas on one machine or LAN, with requests routed across the internet** (data parallel at the request level) is much better than splitting one model over the WAN.
- The UPM model makes training-time IP protection depend on swarm inference. That locks consumers into the slow WAN path and conflicts with the local-first value proposition. AIBC should decide explicitly whether its weights are open, which allows local inference, or protocol-locked, which requires swarm-only serving.
- Prompt privacy: in pipeline-split serving every stage sees hidden states, which leak prompt content. Without TEEs (secondary commentary pairs Pluralis with TEEs), local inference on one's own machine is the only strong privacy option.

### Gaps
- Not researched within budget: distributed-llama numbers, llama.cpp RPC backend throughput, Nesa (claimed privacy-preserving distributed inference), and current Petals or Parallax production throughput figures. The Parallax paper body was not read, so its quantitative results are missing here.
- No primary measurement found of WAN latency for multi-hop consumer pipelines in 2026.

---

## 3. Training-time design choices that ease consumer inference later

### Takeaway
The most effective levers are decided at training time. (a) Low **active** parameters (about 3–6B) inside an MoE whose total size fits 64–128 GB of RAM at 4 bits. (b) **Native or QAT low-bit release** (MXFP4/int4/NVFP4), as gpt-oss and Gemma 3 QAT show. (c) **Nested or elastic training** (MatFormer / Gemma 3n, Nemotron Elastic) or distillation, so one run yields a family sized to contributor tiers.

### Cited Findings
- gpt-oss-120b (117B total / 5.1B active, native MXFP4, 59 GB) shows that a small active budget plus native 4-bit makes a frontier-ish open model run on one gaming GPU with RAM offload at tens of tok/s. — [witcheer on X](https://x.com/witcheer/status/2062103386615398642); [llama.cpp #15396](https://github.com/ggml-org/llama.cpp/discussions/15396)
- Gemma 3 QAT recovers quality at int4 with only about 5,000 extra steps distilled from the BF16 model's probabilities. QAT is therefore cheap to add at the end of a community run. — [Gemma 3 Technical Report](https://arxiv.org/pdf/2503.19786); [Google Developers Blog](https://developers.googleblog.com/en/gemma-3-quantized-aware-trained-state-of-the-art-ai-to-consumer-gpus/)
- **Nemotron Elastic** (NVIDIA, arXiv 2511.16664, Nov 20 2025): nests 9B and 6B submodels inside a 12B reasoning parent (Nemotron Nano V2 12B). Submodels share weights and are extracted zero-shot with no extra training. It uses a two-stage curriculum with 49K-token extended-context training, 110B tokens for the family, and claims over 360× lower cost than training a family from scratch. Deployment memory stays constant as the number of family members grows. Reported 5-task averages are 77.41 (12B), 75.95 (9B) and 70.61 (6B), from a secondary summary. — [arXiv 2511.16664](https://arxiv.org/abs/2511.16664); [HF papers](https://huggingface.co/papers/2511.16664)
- **Gemma 3n MatFormer** (Google, 2025): E2B was trained as a sub-model inside E4B and can be used standalone. "Mix-n-Match" lets developers pick per-layer sizes for their hardware, and the MatFormer Lab notebook slices custom sizes. E2B/E4B have about 5B/8B total parameters, with about 2B/4B needed in accelerator memory. — [HF Gemma 3n blog mirror](https://hf-2025.pages.dev/blog/gemma3n); [Google AI Gemma 3n docs](https://ai.google.dev/gemma/docs/3n?hl=hi)
- BitNet b1.58 2B4T shows natively ternary training works at 2B / 4T tokens with fast CPU decode (about 29 ms/token on a laptop CPU). It has not been demonstrated at frontier scale. — [wavect.io](https://wavect.io/blog/bitnet-cpu-llm-ram-requirements/)

### Inferences
- Proposed AIBC family, mapped to contributor tiers (estimate):
  - **Tier S (8–12 GB VRAM, 16–32 GB RAM):** 2–4B dense nested submodel, or about 20–30B-A3B MoE at 4 bits.
  - **Tier M (16–24 GB VRAM, 64 GB RAM):** about 30–60B-A3–5B MoE.
  - **Tier L (32 GB VRAM, 128 GB+ RAM, or 128–512 GB Mac):** a flagship of about 100–200B total / 5–10B active at native 4-bit.
  - **Swarm only:** anything larger.
- Expected sizes: about 30B-A3B at 4 bits is about 16–18 GB, and about 120B-A5B at MXFP4 is about 60 GB, matching gpt-oss.
- Nested or elastic training (MatFormer-style FFN width plus depth elasticity) on the community model avoids N separate distillation runs. Contributors download one checkpoint and slice it to their tier, which also simplifies verification (Section 4).
- Do QAT (or train natively in MXFP4/NVFP4) in the final phase, and publish GGUF/MLX artifacts on day 0.

### Gaps
- No evidence found yet of elastic or MatFormer training applied to MoE at more than 100B scale, or of elastic training in decentralized or low-communication (DiLoCo-style) settings.
- EXL3/QTIP/IQ-quant quality curves were not gathered.

---

## 4. Allocation: credits, priority, contributor-served network, pricing, verifiable inference

### Takeaway
Open-model inference is now very cheap on the market: about $0.03–0.15 per million tokens for gpt-oss-120b and about $0.09–0.55 for Qwen3-235B on OpenRouter in 2026. Credits for contributors therefore only matter if they come with privacy, priority or specialization. Integrity of a contributor-run serving market is technically achievable with TOPLOC-style activation commitments plus deterministic (batch-invariant) inference for spot-check replay.

### Cited Findings
**Pricing benchmarks (OpenRouter, 2026, varies by provider)**
- gpt-oss-120b: the cheapest endpoints are about $0.03/M input and $0.15/M output, and the most expensive are about $0.35/$0.75. The `:free` variants of gpt-oss-120b and Qwen3 Coder were removed. — [OpenRouter gpt-oss-120b page](https://openrouter.ai/openai/gpt-oss-120b); [benchlm.ai OpenRouter Oct 2026](https://benchlm.ai/hosts/openrouter)
- Qwen3-235B-A22B Instruct 2507: about $0.09–0.14/M input and about $0.55/M output. The Thinking variant is about $0.45/M in one listing. — [pricepertoken DeepInfra vs OpenRouter](https://pricepertoken.com/endpoints/compare/deepinfra-vs-openrouter); [pricepertoken OpenRouter vs Together](https://pricepertoken.com/endpoints/compare/openrouter-vs-together)
- DeepSeek V3.2: about $0.26–0.28/M input and $0.38–0.42/M output. One DEV guide lists $0.27/$1.10, an outlier. — [pricepertoken](https://pricepertoken.com/endpoints/compare/deepinfra-vs-openrouter); [DEV Community](https://dev.to/kuldeep_paul/openrouter-models-compared-2026-guide-to-speed-and-cost-i0e)
- OpenRouter passes through provider prices and charges about 5.5% on credit purchases (Standard plan, as of Oct 29 2026, secondary). — [maximem.ai](https://www.maximem.ai/blog/openrouter-pricing-2026)

**Verifiable inference**
- **TOPLOC** (Prime Intellect, arXiv 2501.16007, ICML 2025): commits to the top-k values of the last hidden state with polynomial encoding. Each 32 generated tokens produce a 258-byte commitment, versus 262 KB for raw embeddings (1000× smaller). Validation is up to 100× faster than original inference because it uses prefill only. The authors report 100% detection of changed model, prompt or precision, and robustness to hardware and kernel reordering (authors' evaluation, no independent audit found). It is packaged as `toploc` on PyPI with vLLM and SGLang (fork) integrations. — [arXiv 2501.16007](https://arxiv.org/html/2501.16007v1); [Prime Intellect blog](https://primeintellect.ai/blog/toploc); [PyPI toploc](https://pypi.org/project/toploc/0.0.1/)
- **Batch-invariant inference** (Thinking Machines, "Defeating Nondeterminism in LLM Inference", Sep 2025): nondeterminism comes mainly from batch size varying with load. Batch-invariant RMSNorm, matmul and attention kernels (repo thinking-machines-lab/batch_invariant_ops) make vLLM deterministic. On Qwen3-235B-A22B-Instruct-2507, 1000 sampled completions went from 80 unique outputs to 1 identical output. The throughput cost in the example was 26 s → 55 s, improved to 42 s with an optimized attention kernel; other coverage cites 34–60%. — [Simon Willison summary](https://simonwillison.net/2025/Sep/11/defeating-nondeterminism); [morphllm](https://www.morphllm.com/defeating-nondeterminism-llm-inference)
- The Petals paper included a simple points-for-servers incentive proposal, but had no verification or extraction protection. — [Petals paper](https://arxiv.org/pdf/2209.01188)

### Inferences (proposed allocation mechanism, estimate-level design)
- **Unit of account:** "contribution points" for verified training work (from the training protocol's proof system) and for verified serving work (tokens served × model tier, verified with TOPLOC).
- **Rights from points:** (1) the open weights, free to everyone and run locally with no metering; (2) priority-queue access to the hosted flagship (large-context, Tier L/swarm) on the contributor network, with weighted-fair-queueing shares proportional to a decaying sum of points (for example a 90-day half-life) so early contributors cannot lock in priority forever; (3) a free monthly token quota, for example proportional to points but capped, with external API users paying near market price (about $0.10–0.60/M tokens for comparable open models) and that revenue paid out to serving and training contributors.
- **Serving market:** contributors who serve earn points or revenue per verified token. Pair TOPLOC commitments on every response with random spot-check re-execution by validators running batch-invariant vLLM/SGLang. Slash or reduce reputation on mismatch.
- **Fairness:** a cap per identity and a minimum free tier, so small-GPU contributors still get meaningful access. Sybil resistance comes from tying points to verified compute rather than to accounts.
- **Economics caveat:** at about $0.15/M tokens for gpt-oss-120b-class models, a heavy user consuming 10M tokens a month is worth about $1.50 at market prices. Inference credits alone are weak compensation, so non-price value (Section 5) must carry the proposition.

### Gaps
- No primary 2026 data found on deployed contributor-credit schemes (for example Bittensor subnets, Prime Intellect, Gradient or Nous inference credit mechanics) or their uptake.
- No independent audit of TOPLOC's robustness against adaptive adversaries found. Applicability to MoE models with CPU expert offload, where numerics may differ, is unverified.

---

## 5. What makes it "really valuable" versus frontier APIs and existing open models; evidence of demand

### Takeaway
Local-LLM demand is large and growing. Ollama says it has about 8.9M monthly developer users (July 2026, company figure), and r/LocalLLaMA has about 0.8M members (2026). The winning differentiators are those that frontier APIs and cheap open-model APIs cannot match: private local-first use, the community's own fine-tunes or LoRAs, specialization (for example EU languages), and censorship-resistance. Raw price per token is not a differentiator, because open-model API tokens already cost cents.

### Cited Findings
- Ollama raised $65M (July 9 2026) and says it is used by over 8.9M developers monthly. This is company-reported and unverified. — [TechCrunch 2026-07-09](https://techcrunch.com/2026/07/09/popular-open-source-ai-developer-tool-ollama-raises-65m-grows-to-nearly-9m-users/); [dutchstartup.ai](https://www.dutchstartup.ai/en/news/ollama-raises-65-million-for-platform-that-lets-developers-run-ai-models-locally)
- A widely repeated, unsourced figure says Ollama had about 52M monthly downloads in Q1 2026, up from about 100K in Q1 2023. I could not trace it to a primary source. — [DEV Community](https://dev.to/pooyagolchian/local-ai-in-2026-ollama-benchmarks-0-inference-and-the-end-of-per-token-pricing-32e7)
- r/LocalLLaMA membership is about 686K–861K depending on the tracker and snapshot date (2026). About 800K+ is a reasonable working figure. — [viralhunt (850.3K)](https://viralhunt.io/reddit/communities/localllama); [reddapi (816,957)](https://reddapi.dev/subreddits/localllama/insights); [gummysearch](https://gummysearch.com/r/LocalLLaMA/)
- Gemma 3 QAT explicitly targets "consumer GPUs", for example the 12B on an 8 GB laptop GPU. Major labs are designing for the same consumer tier AIBC contributors own. — [Google Developers Blog](https://developers.googleblog.com/en/gemma-3-quantized-aware-trained-state-of-the-art-ai-to-consumer-gpus/)
- Newer large open models need 4× 4090 plus 800 GB RAM (Qwen3.5 on KTransformers) or multi-Mac clusters (Kimi K2/K3). The best open models are drifting out of consumer reach, which is the gap AIBC targets. — [KTransformers Qwen3.5.md](https://github.com/kvcache-ai/ktransformers/blob/main/doc/en/Qwen3.5.md); [Creative Strategies](https://creativestrategies.com/research/running-a-1t-parameter-model-on-a-40k-mac-studio-cluster/)

### Inferences
- Value levers ranked by defensibility (judgment):
  1. **Runs well on the hardware contributors already own** (tiered family, day-0 GGUF/MLX, tuned offload presets). This is the gap left by 235B–1T open models.
  2. **Privacy and local-first**, with no prompts leaving the device for Tier S–L use.
  3. **Community ownership and governance** over data and alignment, including censorship-resistance and transparent data.
  4. **Personal and community LoRA adapters** trained on the same network, cheap to serve because many adapters can share one base.
  5. **Specialization**, for example EU languages or domain experts, where frontier models are weaker.
- On cost the project cannot beat frontier or open APIs per token. It must win on "yours, private, runs at home, and shaped by you".

### Gaps
- No primary download numbers found for LM Studio, or for llama.cpp/GGUF on Hugging Face, in 2026.
- No survey data found on willingness to contribute GPUs in exchange for inference access.

---

## 6. Bottom line: recommended inference architecture and allocation mechanism (MVP and at scale)

### Takeaway
Treat **local inference of an open, tiered model family** as the default contributor benefit. Use a **contributor-run serving network** (Parallax-style scheduling, whole replicas per node or LAN, TOPLOC plus deterministic spot checks) only for the flagship and long-context work that does not fit locally. Allocate priority and quota on that network by decaying verified-contribution points, and sell surplus capacity to external users at market rates to fund payouts.

### Cited Findings (basis for the recommendation)
- MoE expert offload makes about 100–120B-total / about 5B-active native-4-bit models run at about 25–85 tok/s on a single RTX 5090 with 64 GB+ RAM (2025–2026). — [llama.cpp #15396](https://github.com/ggml-org/llama.cpp/discussions/15396); [witcheer](https://x.com/witcheer/status/2062103386615398642); [Hardware Corner](https://www.hardware-corner.net/gpt-oss-offloading-moe-layers/)
- Splitting one model over the WAN or home links is slow: about 6 tok/s for Petals 70B, and about 1.5 tok/s for prima.cpp 70B on home Wi-Fi clusters. — [UPM paper](https://arxiv.org/pdf/2605.23464); [prima.cpp ICLR 2026](https://proceedings.iclr.cc/paper_files/paper/2026/hash/e991e5587c1daa49bbf9a818b3f02f9a-Abstract-Conference.html)
- Parallax shows how to schedule heterogeneous volunteer GPUs (layer allocation plus per-request pipeline selection). — [arXiv 2509.26182](https://arxiv.org/abs/2509.26182)
- Nested training yields many sizes from one run at about 360× lower cost (Nemotron Elastic). Short QAT recovers int4 quality (Gemma 3). — [arXiv 2511.16664](https://arxiv.org/abs/2511.16664); [Gemma 3 report](https://arxiv.org/pdf/2503.19786)
- TOPLOC: 258 bytes per 32 tokens, validation up to 100× cheaper than inference. Batch-invariant kernels give bitwise-reproducible vLLM outputs at about 1.6–2× slowdown. — [TOPLOC](https://arxiv.org/html/2501.16007v1); [Thinking Machines via Simon Willison](https://simonwillison.net/2025/Sep/11/defeating-nondeterminism)

### Inferences (recommendation)
**MVP (0–12 months):**
1. **Model:** train or derive a small family, not one giant model. For example, a MatFormer/elastic dense model of about 4B with nested 1–2B, plus about 30B-A3B MoE (fits 16–24 GB VRAM plus 32–64 GB RAM at 4 bits). Finish with QAT to int4/MXFP4 and ship GGUF + MLX on day 0. If the community flagship is larger, distil into these sizes.
2. **Inference path:** local by default. Ship a one-click client wrapping llama.cpp, or Ollama-compatible packaging, with auto-tuned `--n-cpu-moe` per hardware profile, for NVIDIA first and then MLX on Mac. No metering is needed for local use.
3. **Hosted fallback:** a small pool of high-RAM contributor nodes (5090 + 128–256 GB, or 512 GB Macs) serving whole replicas behind an OpenAI-compatible router (vLLM/SGLang/llama.cpp server). Contributors get a free monthly quota and a priority queue proportional to decaying points.
4. **Integrity:** TOPLOC commitments on every served response, plus about 1–5% random re-execution by validators running batch-invariant kernels.

**At scale (12+ months):**
1. **Flagship:** about 100–200B total / 5–10B active MoE, natively low-bit (MXFP4/NVFP4), elastic depth and width so Tier L users run it locally and smaller tiers run nested slices.
2. **Serving network:** Parallax-style scheduler. Route each request to a node or LAN cluster that holds a full replica. Use WAN pipeline splitting only for over-sized models or batch jobs. Mac clusters via exo/RDMA act as "super-nodes".
3. **Market:** sell external API access at about market price for comparable open models (about $0.10–0.60/M output tokens, 2026). Distribute revenue to serving and training contributors by verified work. Allocate contributor priority by weighted fair queueing on decayed points, with a guaranteed minimum free tier per verified human or contributor.
4. **Personalization:** multi-LoRA serving (many personal or community adapters on one base). Train adapters on the network and run them locally.
5. **Weights policy:** if AIBC adopts Pluralis-style unextractable training, inference becomes swarm-only: about 3% overhead, but WAN latency and no local use. That conflicts with the local-first benefit. Recommendation: release the open tiered family for local use even if the largest flagship stays protocol-locked.

### Gaps
- No primary data found on real-world throughput or cost per token of contributor-run serving networks (Parallax, Prime Intellect, Nous, Bittensor) to benchmark the hosted fallback's economics.
- Prompt-privacy options for hosted serving (TEEs on consumer GPUs, split-learning obfuscation) were not researched. Currently, local inference is the only strong privacy guarantee.
