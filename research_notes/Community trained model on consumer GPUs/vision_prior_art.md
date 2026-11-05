# Vision prior art: who is building a "people's datacenter" (consumer-contributed pre-training of one model, with remuneration, ownership and inference rights), as of 2026-11-05

Scope: this file checks competitors against the whole vision. The test has five parts: consumer hardware, ONE shared model, trained from scratch, contributors paid, and contributors getting ownership or inference rights. Algorithm facts (Pluralis-8B, Covenant-72B, Psyche, Prime Intellect, Gensyn) are already in `research_notes/DPoDL revival research November 2026/decentralized_training.md` and `.../DPoDL prior art and viability plan/*.md`, and are not repeated here. A sibling file in this folder, `contributor_inference.md`, covers distributed inference. Tags: [P] primary source, [S] secondary or aggregator, [SELF] self-reported or unaudited, [CLAIM] marketing claim.

## Q1. Pluralis "Protocol Learning": what exactly is the ownership, remuneration and inference model, and how close is it to finished?

### Takeaway
Pluralis comes closest to the full vision, both in its stated thesis and in demonstrated consumer-GPU pre-training. Its thesis covers collectively owned, unextractable models, value flowing back from downstream use, and a node-held model that inference must go through. As of Nov 2026, though, the economic layer does not exist. Contributors earn only non-financial FLOP "points", under an explicit "No financial incentive yet" notice. No token, ownership instrument, revenue share or contributor-inference right has been specified or launched. Pluralis-8B weights are not publicly released. Joining needs at least a 24 GB GPU, 70–80 GB RAM, 200/100 Mbps, and under 80 ms to North-American peers. Pluralis has finished roughly the "technical proof" half of the vision and none of the "people's ownership/remuneration/inference" half.

### Cited Findings
**Thesis (what they promise)**
- [P, Mar 2025, Alexander Long, "A Third Path: Protocol Learning"]:
  - Trainers "must have a way to profit from their contribution". The proposal is to "incentivize through partial model ownership", with "programmatic value flow from downstream use of the model".
  - "no participant can ever obtain a full weight set", and "Extraction is not possible - no one has a full model checkpoint to share."
  - The post mentions no token, no payment mechanism, no inference pricing, and no rule for who receives revenue.
  - Source: [Pluralis blog](https://pluralis.ai/blog/a-third-path-protocol-learning/)
- [P, 2026, homepage] Models are "developed, trained and served across global networks of many participants" and "owned by the collective". The page gives no mechanism, no token and no inference terms. — [pluralis.ai](https://pluralis.ai/)
- [S, Mar 2025, USV investor post, via search summary] Models are "protocol-owned", and ongoing usage revenue is to be distributed back to contributors. — [USV blog](https://blog.usv.com/pluralis-towards-actually-open-ai-1)
- [S, undated aggregator] Tokenintel describes Pluralis as offering "partial ownership stakes proportional to training contribution, granting revenue share and governance rights". The page says "Last reviewed: January 2025", and I found no Pluralis primary source specifying this, so treat it as an aspiration, not a launched mechanism. — [tokenintel.org](https://tokenintel.org/learn/protocols/decentralized-training-landscape)

**Mechanism research (unextractability)**
- [P, arXiv 2605.23464, submitted 2026-05-22; the page also lists NeurIPS 2025 / NeurIPS 38, which is inconsistent] "Unextractable Protocol Models". The method injects "time-varying, random, invertible transforms at participant boundaries" so that "a full weight set is never available to any one participant".
  - Inference overhead with a transform every 30 s: about 3% latency, 0.1% bandwidth and 10% GPU memory.
  - Training overhead: about 1.6% time.
  - Reconstructing the model by fine-tuning stitched partitions needs at least 60% of the tokens required to train from scratch.
  - The page gives no collusion threshold.
  - Source: [arXiv 2605.23464](https://arxiv.org/abs/2605.23464)
- [P, arXiv 2607.13332, Jul 2026] The Agora paper frames value as retained "within the network of contributors that created it" and the goal as "collectively trained, collectively owned models … with economic sustainability". In Pluralis-8B, "no single party ever possesses the full weights". UPMs are cited as the future step to make weights unextractable from a node. — [arXiv 2607.13332](https://arxiv.org/html/2607.13332)

**Remuneration today**
- [P, docs, undated, checked 2026-11-05] "No financial incentive yet. Points reflect contribution only. There is no financial reward tied to your score at this stage."
  - Points are FLOPs processed, plus 1 PFLOP of "presence" per active hour, tied to a HuggingFace identity with a cap of 5 active peers per account.
  - There is no statement that points convert to tokens, equity, ownership or inference access.
  - Source: [Pluralis Points docs](https://pluralis.ai/docs/quick-start/points/)
- [S, Mar 2025] $7.6M seed led by USV and CoinFund, with Topology, Variant, Eden Block, Bodhi, Balaji Srinivasan and Clem Delangue. One secondary source says it was equity "with warrants for future cryptocurrencies", which implies a token is contemplated but not launched. I found no 2026 raise. — [GlobeNewswire](https://www.globenewswire.com/news-release/2025/03/19/3045635/0/en/Pluralis-Research-Pioneers-Protocol-Learning-to-Scale-Decentralized-AI-Announces-7-6M-Seed-Round-Led-by-USV-and-CoinFund.html); [search summary of Gate/aggregators](https://www.gate.com/news/detail/9980909)

**Who can contribute (hardware and permission)**
- [P, docs, checked 2026-11-05]
  - GPU: "24 GB VRAM" minimum, listing the RTX 4090, 5090, 6000 Ada, PRO 4500/6000 and L40S.
  - RAM: 70 GB per GPU. Disk: 80 GB.
  - Network: 200 Mbps down / 100 Mbps up, and under 80 ms RTT to NA peers. A North-American instance is "effectively required today".
  - OS: Linux or WSL2. "macOS is not supported."
  - Identity: a free HF token. There is an "authorization phase" with no manual whitelist described.
  - Source: [Pluralis requirements](https://pluralis.ai/docs/quick-start/requirements/)
- [P, Agora paper, Pluralis-8B]
  - Admission floor: at least 24 GB VRAM, 80 GB RAM, 200 Mbit/s download, at most 80 ms latency. Participation was "restricted to consumer GPU models" plus the L40S.
  - GPU mix: RTX 5090 and 4090 were 55% of nodes, L40S 22%, RTX 6000 Ada and PRO 6000 23%.
  - Host RAM median 504 GB (range 80 GB to 2 TB). Download bandwidth median 703 Mbit/s.
  - At most 60 contributors at a time. 669 joins and 607 departures. 99.98% of 3,334,054 join requests were turned away.
  - Head and tail stages ran on Pluralis cloud nodes. Contributors held body stages only.
  - 176 unique node operators.
  - Source: [arXiv 2607.13332](https://arxiv.org/html/2607.13332)

**Status, roadmap and openness**
- [P, Agora repo README] "The Pluralis-8B run has … successfully completed after training 500B tokens over 7 weeks." The paper says 40 days.
  - The last commit is "finish-run", 2026-07-04.
  - Code: Apache-2.0, built on Hivemind (MIT).
  - The node "downloads the model weights" for its stage at join.
  - Sources: [github.com/PluralisResearch/agora](https://github.com/PluralisResearch/agora) (shallow clone 2026-11-05); Node0 repo Apache-2.0, last commit 2025-09-23; Stoa (Mac RL) MIT, last commit 2026-07-15 ([stoa](https://github.com/PluralisResearch/stoa))
- [P, X, 2026-06-13, date decoded from the post ID] Mid-run: "350B tokens in", "133 external contributors total", and the 104-node max capacity was "filled almost immediately". [SELF] — [Pluralis on X](https://x.com/Pluralis/status/2065899910080115117)
- [P, dashboard checked 2026-11-05] "Pluralis-13B-Test" is "Finished".
  - 101 participants, 62.4B tokens, train loss 3.006, no evals published.
  - Mean MFU 14.9%, "protocol overhead 61%".
  - 1,215 total nodes ever. Top GPU: RTX 5090 (332).
  - Compute split: 90% contributors, 10% Pluralis.
  - 0 nodes active, so no live run on 2026-11-05.
  - Source: [agora.pluralis.ai](https://agora.pluralis.ai/)
- [P, docs] The run list is Node0-7.5B (Sep 2025, 36.6B tokens), Pluralis-8B (May 2026, 531.8B tokens; the paper says 500B), and Pluralis-13B (Sep 2026, 62.4B tokens, "systems test"). No public roadmap. The homepage invites applications to help "plan future runs". — [Pluralis docs](https://pluralis.ai/docs/); [pluralis.ai](https://pluralis.ai/)
- [P, HF API query 2026-11-05] No models under `PluralisResearch` or `Pluralis` on Hugging Face, and no "Pluralis-8B" repo found. Weights appear unreleased, which fits the protocol-owned thesis. — [HF API](https://huggingface.co/api/models?author=PluralisResearch)
- [P] All 12 Agora paper authors are listed as "Pluralis Research", with Alexander Long as founder or lead. — [arXiv 2607.13332](https://arxiv.org/html/2607.13332)

### Inferences
- Pluralis has publicly claimed the conceptual vision: collective ownership, unextractable weights, and inference that requires the network. Any "people's model" pitch built on that thesis alone will be read as derivative. Differentiation has to come from what Pluralis has not shipped: concrete economics, legal ownership, contributor inference rights, lower hardware floors, and non-NA geography.
- The hardware data suggests many "consumer GPU" contributors were rented cloud or colocated boxes (median host RAM 504 GB, median 703 Mbit/s down). Pluralis-8B proves consumer-class GPUs work. It does not prove households with home broadband and 8–16 GB cards can take part.
- Being "permissionless" was capped in practice: about 60 concurrent contributor slots, and 99.98% of join requests rejected. That signals strong unmet demand from would-be contributors, even with zero financial reward.
- Pluralis is not "finished". The 13B systems test shows 61% protocol overhead and 14.9% MFU, no live run is going, and the economic layer is entirely undefined. They are roughly at "technical proof at 8B" plus "token/economics TBD".

### Gaps
- No primary source gives Pluralis's intended token, ownership instrument (equity, NFT or token), revenue-share formula, or contributor inference-access terms. Whether Pluralis-8B weights will ever be released or served (and under what license) is unknown.
- Pluralis's headquarters and jurisdiction, team size, and any 2026 funding are unconfirmed. The commit timezone is +0930 (Adelaide), which hints at an Australian base; this is an inference only.
- UPM collusion thresholds were not read from the full paper.

## Q2. Macrocosmos IOTA (Bittensor SN9) "Train at Home": consumer hardware, model size, results, payouts, inference access

### Takeaway
IOTA has the most "consumer-first" product of any project. A one-click Mac app opened to all on 2026-02-10, with layer-sharded (pipeline) training of one shared model and TAO/alpha emissions as pay. Its demonstrated consumer runs are small: 1.5B parameters with 815 participants [SELF]. The 100B Orion run used 48 datacenter A100s. Its newest public model (Oct 2026) is a Qwen3.5-4B fine-tune trained on 4 A6000s, not a consumer-pretrained base. I found no ownership or inference rights for contributors; they are paid in emissions and the outputs are open-weight. IOTA is a real but early competitor for the "consumer app plus pay" piece, and it is not pursuing contributor ownership.

### Cited Findings
- [P, 2026-02-19 post] "As of Tuesday 10th February, we've officially opened Iota's Train at Home network to all" (first unveiled 2025-12-09).
  - Mac only at launch, with Linux then Windows planned.
  - 16 GB RAM minimum and 10–30 GB disk. Machine must stay plugged in and awake.
  - Users "collaborate … all aimed at the same model".
  - Rewards: "you may also earn rewards from the Bittensor Protocol". No amounts given.
  - No ownership, inference or licence terms. Classic SN9 needs a CUDA GPU with at least 16 GB VRAM.
  - Source: [Macrocosmos Substack](https://macrocosmosai.substack.com/p/welcome-to-train-at-home)
- [SELF, X, about 2026-02-23 decoded from post ID; seen in a search snippet only, page paywalled] First Train at Home run: "Model Size: 1.5B", "13 days", "815" unique participants. — [IOTA_SN9 on X](https://x.com/IOTA_SN9/status/2025987505473085896)
- [S, search snippet] Over 2,500 downloads in the first two weeks and about 500 active nodes [SELF, unverified]. — [TAO Daily X article](https://x.com/taodaily_io/article/2062601833596747979)
- [S, 2026-02-10] TAO Daily says the app lets "anyone with a Mac" mine, that "models stay open-source", and that SN9 is "winner-takes-most … top models can take over 95% of rewards". This last description looks like the pre-IOTA SN9 competition design and may be outdated or confused. — [TAO Daily](https://taodaily.io/train-at-home-is-now-open-to-everyone-heres-how-to-mine/)
- [P, 2026-06-01] Orion-100B:
  - 100B params (modified Llama-3.2), about 1.1B tokens over about 2 days, stopped for cost. Described as "a system-viability proof".
  - 16 pipeline stages × 3 replicas = 48 A100-80GB peers in 5 US datacenters.
  - About 65% of co-located speed, 30.8% MFU, ResBM 64× activation compression.
  - Roadmap: heterogeneous hardware, spot instances, permissionless, then consumer "4090/5090/M Series".
  - No payout, ownership or licence detail.
  - Source: [Macrocosmos Substack](https://macrocosmosai.substack.com/p/orion-100b-distributed-pretraining)
- [P, HF model card, 2026-10-21 to 10-29] `macrocosm-os/iota-decide-4b` (versions v0.3 and v0.4):
  - Apache-2.0, base model `Qwen/Qwen3.5-4B-Base`.
  - "Trained on disaggregated compute: independent single-GPU machines". Compute: "4 independent single-GPU machines (NVIDIA A6000), about 26 hours".
  - The "IOTA SDK … will be released publicly soon".
  - Source: [HF model card](https://huggingface.co/macrocosm-os/iota-decide-4b)
- [S] Third-party guides conflict on Linux support (one says Linux with 16 GB VRAM is supported; another lists the RTX 4090 and Ubuntu 22.04 as the reference miner). Not verified at primary source. — [simplytao](https://simplytao.ai/blog/your-simple-guide-to-iota-sn9); [bittensor.ai SN9](https://bittensor.ai/subnets/9)

### Inferences
- IOTA's commercial direction in late 2026 looks like an "IOTA SDK" for disaggregated training and enterprise decision models, not a community-owned frontier base model. Train at Home looks like a top-of-funnel and emissions mechanism.
- Remuneration exists (Bittensor emissions), but it is token emissions with no claim on the model and no inference privileges. That is the "pay but no ownership" corner of the map.

### Gaps
- Current (Nov 2026) Train at Home status, run sizes, active node counts, NVIDIA/Windows support, and per-contributor TAO earnings were not found at primary source. The IOTA site and docs did not expose them.
- Whether any Train at Home checkpoint was released, and under what licence, is unconfirmed.

## Q3. Nous Psyche: consumer participation, Consilience, ownership and inference for contributors

### Takeaway
Psyche is not consumer-open and not contributor-owned. Runs are permissioned (an admin authorizes each node key), the Solana coordination is on devnet, and there is no token reward, points or revenue share. Consilience-40B pre-training appears stalled: last public checkpoint 2025-08-14, tokens unpublished, and the 20T claim withdrawn. Psyche's live use is post-training of Hermes models (Hermes 4.3 on 24 nodes). Nous is a venture-funded corporate lab: a $50M Series A in Apr 2025 at a SAFT-implied $1B, and a reported $90M Series B in Oct 2026 at $1.5B. Inference revenue flows to the company. Models are open-weight and anyone can run them locally.

### Cited Findings
- [S, ownyourmind.ai review, checked 2026-10-27; quotes primary docs]
  - "NousNet runs are permissioned"; a run admin authorizes each node key. Coordinator programs are on Solana devnet, and "mainnet" is not claimed.
  - Repo renamed nousnet, last push 2026-03-24.
  - "Hermes 4.3 was post-trained entirely on Psyche", 24 nodes, 144k tok/s (Nous blog, 2026-10-07 as cited).
  - No token reward pre-TGE; token design still open (SOL vs proprietary, per Fortune).
  - Consilience-40B: tokens consumed unpublished, latest checkpoint 2025-08-14, "reached 20T tokens" claim withdrawn.
  - No ownership, revenue share or value accrual for contributors. Nous Portal API revenue goes to the company.
  - Licences: Psyche Apache-2.0; Consilience CC0-1.0 and MIT.
  - Funding: $50M Series A (Paradigm, Apr 2025); reported $90M Series B (Oct 2026, Robot Ventures, $1.5B).
  - Source: [ownyourmind.ai](https://ownyourmind.ai/projects/nous-research/)
- [P, HF API 2026-11-05] The newest PsycheFoundation Consilience repos are `consilience-dm-init` (2025-09-10) and `consilience-40b-*` (May 2025). No newer pre-training checkpoints were found by search. — [HF API search](https://huggingface.co/api/models?search=consilience)
- [S] A third-party guide lists 40 GB VRAM node minimums and very high bandwidth, which conflicts with "consumer GPU" marketing. — [Spheron guide](https://www.spheron.network/blog/decentralized-llm-training-pluralis-prime-intellect-nous-psyche/)
- [P, background] The Psyche architecture page markets "democratizing" development, with consumer GPUs alongside datacenter GPUs. — [Nous Psyche](https://nousresearch.com/nous-psyche); docs.psyche.network returned HTTP 503 on 2026-11-05.

### Inferences
- Psyche competes for the "open model trained over the internet" narrative, not for the "people own it" one. Its governance and value capture are corporate.

### Gaps
- Primary Nous confirmation of the Series B, the Oct 2026 blog, and current Psyche permissioning was not fetched (docs returned 503). These rely on one secondary review.

## Q4. Everyone else: Prime Intellect, Gensyn, Templar/Teutonic, 0G, historical volunteer projects, compute/bandwidth DePINs, public-good models, federated, newcomers

### Takeaway
None of these combines consumer hardware, one from-scratch model, pay and contributor ownership or inference. The well-funded decentralized-training players moved away from live consumer networks in 2026: Prime Intellect archived its protocol and went enterprise, Gensyn paused its swarms for Delphi, and Templar ran on 8×B200 peers before leaving Bittensor. The historical volunteer projects (DeDLOC, SWARM, Petals, GPT-JT) proved feasibility but had no economics. Compute DePINs and Grass pay consumers but train nothing collective (Grass: about 8.5M registered users [SELF], which is the consumer-acquisition precedent). Public-good models (Apertus 1.5, Jul 2026, Apache-2.0) offer openness without consumer compute or ownership. I found no operating member-owned cooperative that trains its own LLM on pooled compute.

### Cited Findings
**Decentralized-training players**
- **Prime Intellect**
  - [P] The p2p "protocol" repo, which powered INTELLECT-2 and SYNTHETIC-2, was archived 2026-01-27. — [GitHub PrimeIntellect-ai/protocol](https://github.com/PrimeIntellect-ai/protocol)
  - [P] A $130M Series A on 2026-07-08 to help enterprises build their own agents. — [TechCrunch](https://techcrunch.com/2026/07/08/prime-intellect-raises-130m-series-a-to-help-enterprises-build-their-own-ai-agents/)
  - [BG, 2024] It originally aimed at "collective ownership of AI models" (per search summary). — [Prime Intellect intro](https://primeintellect.ai/blog/introducing-prime-intellect)
  - Inference workers in INTELLECT-2 could be consumer GPUs. — [arXiv 2505.07291](https://arxiv.org/html/2505.07291)
  - Inference: Prime Intellect abandoned the ownership thesis.
- **Gensyn**
  - [P] Docs list RL Swarm under "Testnet Archive (Legacy)": "No official swarms are running at this time". Delphi (information markets) launched 2026-04-22. "open-1b: the first model you don't have to trust" launched 2026-09-15. — [Gensyn docs](https://docs.gensyn.ai/testnet); [gensyn.ai](https://www.gensyn.ai/)
  - Conflict: BlockEden blog posts (2026-05-05) [S] describe RL Swarm as "live". Primary docs say paused; prefer primary. — [BlockEden](https://blockeden.xyz/blog/2026/05/05/gensyn-rl-swarm-decentralized-ml-training-ethglobal/)
- **Templar/Covenant → Teutonic (SN3)**
  - Covenant-72B needed at least 8×B200 per peer, so it was not consumer. Templar exited Bittensor around April 2026.
  - Teutonic-I 10B (2026-06-02 to 08-10) is king-of-the-hill. Pay is TAO emissions to the current and recent "kings"; contributors get no ownership. No licence file was found.
  - Source: see `DPoDL prior art and viability plan/prior_art_markets.md` and `closest_overlaps_verified.md`; [Teutonic blog](https://blog.teutonic.ai/)
- **0G Labs**
  - [P, 2026-03-24 press release] 0G began "publicly retraining DiLoCoX-107B" on decentralized clusters (China Mobile partnership, 1 Gbps). This is not consumer and not permissionless [CLAIM]. — [GlobeNewswire](https://www.globenewswire.com/news-release/2026/03/24/3261890/0/en/0G-Labs-Decentralized-AI-Model.html)

**Historical volunteer training (no economics)**
- DeDLOC: collaborative pretraining with 40 volunteers. — [arXiv 2106.10207](https://arxiv.org/pdf/2106.10207)
- Petals: last release 2.2.0.post1 on 2023-11-20, dormant. — [PyPI](https://pypi.org/project/petals/)
- Hivemind: maintenance mode. Pluralis Agora is built on it. — [agora README](https://github.com/PluralisResearch/agora)
- BLOOM (BigScience, 2022): trained on the Jean Zay public supercomputer, not on consumer volunteers. — [arXiv 2211.05100](https://arxiv.org/abs/2211.05100)
- Together GPT-JT (Nov 2022): a fine-tune of GPT-J on decentralized, but not consumer-volunteer, compute. — [Together blog](https://www.together.ai/blog/releasing-v1-of-gpt-jt-powered-by-open-source-ai)
- These show feasibility, but none paid contributors or gave them rights.

**Federated (organisations, not consumers)**
- Flower/Photon: federated LLM pretraining up to 7B in the paper (2024). The MLSys 2025 blog claims "tens of billions" [CLAIM]. No 2026 release found. The participants are institutions or data silos, not paid consumers. — [arXiv 2405.10853](https://arxiv.org/abs/2405.10853); [Flower blog 2025-05-09](https://flower.ai/blog/2025-05-09-photon)

**Hyperspace**
- [S, 2026-05-07] A P2P agent network claims "32 anonymous" consumer nodes trained a model in 24 h with DiLoCo, SparseLoCo and "Parcae", at about 28 KB per round.
- Model size is not stated. The leaderboard has no significance testing, and no Sybil or poisoning defenses are documented.
- It has a custom chain with micropayment channels, but no contributor ownership is described [CLAIM, unverified].
- Source: [Starlog review](https://starlog.pages.dev/articles/llm-engineering/hyperspaceai-agi)

**Consumer-pay DePIN precedents (no collective training)**
- **Grass**
  - About 8.5M registered users in 190 countries (May 2026), or 2.5M nodes; figures conflict [SELF/S].
  - The GRASS token launched Oct 2024, with Season 1 airdropping 100M tokens (10% of supply). Season 2 timing is unconfirmed.
  - It pays for idle bandwidth used to scrape web data. It is the strongest precedent that passive-income consumer apps can reach millions.
  - Source: [search summary: dextools 2026 guide](https://www.dextools.io/news/what-is-grass-crypto-depin-bandwidth-ai-training-guide-2026); [OKX explainer](https://web3.okx.com/learn/what-is-grass)
- **Akash and io.net**: rent GPUs; io.net revenue is self-reported. Neither trains a collective model. See `DPoDL revival research November 2026/protocols_incentives.md`.
- **Salad, Nosana, Kaito, Nesa**: not investigated within budget. They are compute rental, inference or attention-market networks, not collective pretraining (see Gaps).
- **exo labs**: distributed inference across Macs. It claims Apple features exo on M5 Ultra Mac Studio pages (2026-08-25, [SELF]). It is an inference stack, not training. — [EXO Labs on X](https://x.com/exolabs/status/2092320487019880735) (see sibling `contributor_inference.md`)

**Public-good open models (the non-crypto alternative)**
- [P, HF API] `swiss-ai/Apertus-v1.5-70B` was created 2026-07-24, licence apache-2.0, 8,238 downloads. An 8B sibling exists.
- [S] The original Apertus (8B/70B) launched Sep 2025 from EPFL, ETH and CSCS, trained on the CSCS supercomputer. It is a public-good model, but citizens contribute no compute and get no ownership.
- Sources: [HF API](https://huggingface.co/api/models/swiss-ai/Apertus-v1.5-70B); [llmreference](https://www.llmreference.com/model/apertus-1.5-70b); [Public AI](https://publicai.co/apertus)

**Cooperatives**
- I found no confirmed member-owned cooperative training its own LLM on pooled member compute.
- Existing examples are data co-ops (Karya, READ-COOP/Transkribus, Mozilla Data Collective, Jun 2026), proposals (Harvard Ash Center "cooperative paradigms"), and pre-launch projects (FinnG "in formation").
- Sources: [Hypha "The Other AI"](https://hypha.coop/dripline/the-other-ai/); [SiliconANGLE 2026-06-13](https://siliconangle.com/2026/06/13/mozilla-data-collective-seeks-build-ais-data-economy-around-trust/); [Ash Center](https://ash.harvard.edu/resources/cooperative-paradigms-for-artificial-intelligence); [FinnG](https://finng-project.pages.dev/)

### Inferences
- The 2026 pattern is that projects with serious capital (Prime Intellect, Gensyn, Nous) chose enterprise or corporate value capture over contributor ownership. The "by the people" niche is under-served because it lacks a business model investors like, not because the technology is lacking.
- Grass and IOTA show consumers will install a passive app for token emissions. Pluralis shows consumer-class GPUs will turn up for zero pay. Nobody has yet joined consumer acquisition, collective pre-training and an ownership or inference claim.

### Gaps
- Salad, Nosana, Kaito, Nesa, io.net consumer-node programmes, Distributed Llama, BOINC/Folding@home-style AI projects, LAION and EleutherAI 2026 activity were not checked within the tool budget. From background knowledge, none is known to run collective consumer pretraining, but this is unverified for 2026.
- Hyperspace's primary sources (repo, paper) were not read.

## Q5. Competitor map and bottom line: is the full vision taken, and what is still uniquely open?

### Takeaway
The full vision is not yet taken, but its intellectual framing is: Pluralis owns the "Protocol Learning / collectively owned unextractable model" narrative and the only consumer-GPU pretraining proof at 8B. The parts nobody had shipped as of 2026-11-05 are:
1. A concrete, legally real ownership and remuneration instrument for contributors (cooperative shares, revenue share or a token with a model claim).
2. Contributor-privileged inference access as a defined right.
3. Genuinely household-grade participation: 8–16 GB GPUs, home upload of 10–50 Mbps, Macs and AMD for pretraining.
4. Non-North-American (for example EU) participation; Pluralis effectively needs NA latency.
5. Verification of honest work in a model-parallel or pipeline setting at consumer scale.

The window is real but probably narrow. Pluralis has stated intent, investors with crypto warrants, and an eager waiting list.

### Cited Findings (map; dated status as of 2026-11-05)

| Project | Consumer HW? | One shared model, from scratch? | Remuneration | Contributor ownership / inference rights | Status and traction | Openness |
|---|---|---|---|---|---|---|
| **Pluralis (Agora)** | Yes, but 24 GB+ GPU, 70–80 GB RAM, ≥200/100 Mbps, <80 ms to NA; no Mac ([req](https://pluralis.ai/docs/quick-start/requirements/)) | Yes: 8.6B/500B tokens (Jul 2026), 13B systems test (Sep 2026) ([arXiv](https://arxiv.org/html/2607.13332); [dash](https://agora.pluralis.ai/)) | None: "No financial incentive yet"; FLOP points ([points](https://pluralis.ai/docs/quick-start/points/)) | Stated thesis ("owned by the collective", unextractable), no instrument; weights not on HF ([site](https://pluralis.ai/)) | 176 operators, 330 nodes; 99.98% of join requests rejected; no live run on 11-05 | Code Apache-2.0 / Stoa MIT; weights closed so far |
| **Pluralis Stoa (Mac RL)** | Yes, 14 Macs on home internet ([blog](https://pluralis.ai/blog/rl-post-training-on-macs/)) | No: RL post-training of an existing 8.3B MoE | None | None stated | Demo Jul 2026 | MIT |
| **Macrocosmos IOTA / Train at Home** | Yes: Mac app (16 GB RAM), CUDA ≥16 GB for classic SN9 ([post](https://macrocosmosai.substack.com/p/welcome-to-train-at-home)) | Yes, pipeline/layer-sharded, but small: 1.5B consumer run, 815 participants [SELF]; 100B on A100s only | Bittensor TAO/alpha emissions (amounts unpublished) | None found; "open-source" outputs | Opened 2026-02-10; latest public model is a 4B Qwen fine-tune on 4×A6000 (Oct 2026) ([HF](https://huggingface.co/macrocosm-os/iota-decide-4b)) | Apache-2.0 model; SDK "soon" |
| **Nous Psyche** | Marketed yes; in practice permissioned, high-spec ([S](https://ownyourmind.ai/projects/nous-research/)) | Consilience-40B stalled (last ckpt 2025-08-14); now post-training | None pre-TGE | None; API revenue goes to company | Hermes 4.3 on 24 nodes; $1.5B valuation (reported) | Apache-2.0 / CC0 |
| **Templar→Teutonic (SN3)** | No (Covenant ≥8×B200); Teutonic open to any HW but competitive | Covenant-72B yes; Teutonic king-of-hill on one checkpoint | TAO emissions | None | Templar exited Apr 2026; Teutonic-I 10B Jun–Aug 2026 | Teutonic: no licence found |
| **Prime Intellect** | Rollout workers only | INTELLECT-1 10B (2024); RL since | Was testnet tokens | Abandoned "collective ownership" | Protocol archived 2026-01-27; enterprise pivot | OSS libs |
| **Gensyn** | Was yes (RL Swarm) | No (RL swarms, small models; open-1b audit demo) | $AI token (Apr 2026) | None | Swarms paused; Delphi focus ([docs](https://docs.gensyn.ai/testnet)) | Mixed |
| **0G DiLoCoX-107B** | No (clusters) | Yes [CLAIM] | 0G token ecosystem | None found | "Publicly retraining" (Mar 2026) | Promised OSS |
| **Hyperspace** | Yes [CLAIM] | Tiny DiLoCo runs [CLAIM] | Custom chain micropayments | None described | 32-node demo (May 2026, S) | Unclear |
| **Flower/Photon** | No (orgs) | Yes, ≤7B (paper) | None | Org-level | No 2026 release found | Apache-2.0 framework |
| **Petals / Hivemind / DeDLOC / GPT-JT / BLOOM** | Partly (volunteers) or no (supercomputer) | Yes (DeDLOC, BLOOM) / fine-tune (GPT-JT) / inference (Petals) | None | None | Dormant or historical | Open |
| **Apertus 1.5 (Swiss AI)** | No (CSCS supercomputer) | Yes, 8B/70B | Public funding | Public good, no individual rights | Released 2026-07-24 | Apache-2.0 |
| **Grass** | Yes (millions, bandwidth) | No training | GRASS token airdrops | None | ~8.5M registered [SELF] | Closed |
| **exo / Petals-style inference** | Yes (Macs) | No (inference only) | None | n/a | Active | Open |

- Key gating facts behind "what's open":
  - Pluralis needs 24 GB VRAM, 70–80 GB RAM and NA latency ([requirements](https://pluralis.ai/docs/quick-start/requirements/)).
  - Pluralis pays nothing so far ([points](https://pluralis.ai/docs/quick-start/points/)).
  - Pluralis's 13B test shows 61% protocol overhead ([dashboard](https://agora.pluralis.ai/)).
  - No operating LLM-training cooperative was found ([Hypha](https://hypha.coop/dripline/the-other-ai/)).
  - Sustained participation below about 85% "substantially impairs convergence" in Agora's failure ablation, so consumer churn is a design constraint ([arXiv 2607.13332](https://arxiv.org/html/2607.13332)).

### Inferences
- **Taken or crowded:**
  - The thesis "collectively owned, unextractable protocol model" (Pluralis, since Dec 2024 / Mar 2025).
  - The proof that consumer-class 24–32 GB GPUs can pretrain 8B (Pluralis).
  - A one-click consumer training app paid in emissions (IOTA).
  - Decentralized RL rollouts on Macs (Pluralis Stoa, Prime Intellect).
- **Uniquely open, ranked by defensibility:**
  1. **A real ownership and remuneration instrument with contributor inference rights.**
     - Examples: member shares in an EU cooperative (SCE) or a Swiss Genossenschaft; compute-weighted, non-transferable usage credits redeemable for inference on the network; revenue share from external API users.
     - Nobody has shipped this. Pluralis explicitly hasn't. IOTA and Teutonic pay emissions with no model claim. Nous and Prime Intellect are corporate.
     - This also avoids the token-securities and governance fragility that hit Templar and Gensyn.
  2. **"Truly household" hardware tier.**
     - 8–16 GB NVIDIA/AMD cards and Apple Silicon for pre-training, not just RL rollouts, on asymmetric home broadband.
     - Pluralis's floor (24 GB, 70–80 GB RAM, 100 Mbps up) excludes most gamers. Their real fleet's median 504 GB RAM and 703 Mbps suggests hosted boxes.
     - This is technically hard: it needs smaller stages, more pipeline depth, and more compression.
  3. **Geography/sovereignty.** An EU-latency swarm, or multiple regional swarms, aligned with EU public-AI sentiment (Apertus-style legitimacy plus citizen compute). Pluralis currently needs NA latency.
  4. **Verification for model-parallel consumer training.** Pluralis has SENTINEL research (see prior notes), but there is no production slashing or verifiable payout for pipeline stages. This is the natural bridge to the AIBC/DPoDL reward contracts.
  5. **Transparent, released weights plus privileged access.** One hybrid: open-weight release after a lag, with contributors getting early or free inference. This differs from Pluralis's never-materialize stance and may appeal to open-source purists.
- **Risk:** Pluralis could announce a token or ownership scheme at any time. Its 2025 seed reportedly included token warrants, and its waiting list shows demand. Competing head-on on "same algorithm, same thesis" is weak. Partnering, building on Apache-2.0 Agora, or differentiating on legal structure, hardware floor and region are stronger options.

### Gaps
- I could not confirm whether any project plans contributor inference credits. Pluralis's undocumented future token is the main unknown.
- Per-contributor earnings on IOTA/SN9 and Teutonic (in USD) were not found.
- EU-based decentralized-training efforts (beyond Apertus and Flower) were not systematically searched. There may be small EU academic or co-op projects not indexed.
