# Protocols and incentive mechanisms that reward AI training or useful work: landscape as of 2026-11-05 (context for D-PoDL revival)

Method note: about 19 search and fetch calls, all run on 2026-11-05. Many 2026 sources are crypto-media or affiliate blogs (bex.co, blockeden, hoge.gg, ownyourmind.ai, kucoin/bitget news). Each is flagged as secondary where used. Primary sources fetched in full: the Covenant-72B paper (arXiv 2603.08163, HTML v2) and the abstract page of IACR ePrint 2025/1814. Items marked "[background, not re-verified this session]" come from the researcher's prior knowledge (cutoff mid-2026) and carry canonical URLs. The report writer should treat them as lower confidence.

## 1. Live networks: mechanisms, status and traction in 2026. Which ones actually reward training?

### Takeaway
By Nov 2026 only a few live systems pay tokens for permissionless pre-training or fine-tuning. The clear leader is Bittensor: Templar SN3 (Covenant-72B, Mar 2026), IOTA SN9 and Gradients SN56. Qubic claims "useful PoW" for its own Aigarth research. Most other "decentralized AI" tokens pay for inference, compute rental or prediction markets. Gensyn launched its token and L2 in Apr 2026, but its training testnet (RL Swarm) is paused. Prime Intellect archived its p2p protocol in Jan 2026 and pivoted to a centralized post-training/RL SaaS. Ambient (proof of logits) is about inference, not training.

### Cited Findings

**Bittensor (TAO): mechanism changes**
- First TAO halving: mid-Dec 2025. Daily emissions fell from ~7,200 to ~3,600 TAO, and annualised inflation from ~10% to ~5%. — [crypto.com](https://crypto.com/us/market-updates/bittensor-halving-all-you-need-to-know); [crypto.news](https://crypto.news/bittensor-tao-price-prediction-december-halving-2026/) (secondary)
- Cross-subnet emissions under dTAO: sources disagree. One guide says the split is now flow-based ("Taoflow"): an EMA of net TAO staking inflows sets each subnet's share, and subnets with negative flow can be clipped to zero. Others (including a SubnetRadar correction note) say it follows a moving average of alpha price. — [tao.media guide 2026](https://www.tao.media/the-ultimate-guide-to-bittensor-2026/); [subnetradar](https://subnetradar.com/blog/bittensor-emissions-distribution) (conflict unresolved; check the Opentensor docs and subtensor GitHub)
- Within-subnet split: ~41% miners, 41% validators, 18% subnet owner. Yuma Consensus distributes rewards each tempo (~360 blocks). — [subnetradar](https://subnetradar.com/blog/bittensor-emissions-distribution); [hoge.gg on Yuma 2026](https://hoge.gg/yuma-consensus-2026-how-bittensor-decides-who-gets-paid/) (secondary)
- Yuma Consensus 3 is described as adding fixed-point bonds, per-pair bond scaling and "liquid alpha", aimed at fairer validator rewards. No primary rollout date was found. — [hoge.gg](https://hoge.gg/yuma-consensus-2026-how-bittensor-decides-who-gets-paid/)
- Ecosystem: Bittensor subnet tokens were worth ~$1.5B in Mar 2026, and TAO rose ~90% that month (CoinDesk, 2026-03-25). — [CoinDesk](https://www.coindesk.com/tech/2026/03/25/bittensor-ecosystem-tokens-value-hit-usd1-5-billion-as-jensen-huang-endorsement-supports-tao-rally). Yuma (a DCG subsidiary) published a "State of Bittensor" report on 2026-03-05. — [The Block](https://www.theblock.co/news/web3/2026-03-05-dcg-yuma-bittensor-report-392351)
- Possible subnet cap expansion from 128 to 256, and validator/owner governance voting planned for H1 2026. Status not confirmed. — [tao.media](https://www.tao.media/the-ultimate-guide-to-bittensor-2026/)

**Templar SN3 / Covenant-72B: the strongest substantiated result in the field** (primary: [arXiv 2603.08163](https://arxiv.org/abs/2603.08163), v1 2026-03-09)
- Model: 72.7B dense decoder, ~1.1T tokens, plus ~14.8B SFT tokens. Participation was permissionless and gated by a live blockchain protocol. At least 70 unique peers (a lower bound counted by UIDs). On average 24.4 submitters and 16.9 contributors per step, with contributors capped at 20. — [Covenant-72B HTML](https://arxiv.org/html/2603.08163v2)
- Each peer ran 8×B200, so the "home internet" framing in the media is misleading: these are datacenter-class nodes. Communication assumed 500 Mb/s down and 110 Mb/s up. Each round was ~20 min of compute plus ~70 s of communication (~94.5% utilization). SparseLoCo: 30 inner AdamW steps, chunk top-k (k=64 of 4096), 2-bit quantization, error feedback, >146× compression. — [Covenant-72B HTML](https://arxiv.org/html/2603.08163v2)
- Zero-shot MMLU: 67.1, vs LLaMA-2-70B 65.6, K2 65.5, INTELLECT-1 32.7 and Psyche Consilience 24.2. It trails LLaMA-2-70B on HellaSwag (80.6 vs 84.3), WinoGrande and OBQA. The authors say the comparisons are not fully controlled. — [Covenant-72B HTML](https://arxiv.org/html/2603.08163v2)
- Media framed it as Bittensor's "DeepSeek moment" (Mar–Apr 2026). Some commentary notes it does not show frontier parity. — [tao.media](https://www.tao.media/templar-makes-history-with-72b-decentralized-ai-training-run/); [blockeden](https://blockeden.xyz/blog/2026/04/11/bittensor-decentralized-ai-deepseek-moment-tao/) (hype-leaning)

**IOTA SN9 (Macrocosmos)**
- IOTA uses data- plus pipeline-parallel "SWARM" execution across heterogeneous, unreliable nodes. Mainnet launched 2025-06-02, with a technical primer at [arXiv 2507.17766](https://arxiv.org/pdf/2507.17766). — [Macrocosmos on X](https://x.com/MacrocosmosAI/status/1928491993338167573)
- "Train at Home" (consumer hardware) opened to everyone on 2026-02-10. The main SN9 needs a CUDA GPU with ≥16GB VRAM. One live run splits a 3B model into 7 layer-shards, so no node holds the full model. — [Macrocosmos Substack](https://macrocosmosai.substack.com/p/welcome-to-train-at-home); [taooutsider](https://www.taooutsider.com/blog/machine-learning-on-bittensor-training-inference-evaluation/)

**Gradients SN56**
- Gradients is a competition over training methods (AutoML/fine-tuning). Miners submit an open repository plus an exact commit. An Aug 28 snapshot showed only 6 active miners. — [taooutsider](https://www.taooutsider.com/blog/machine-learning-on-bittensor-training-inference-evaluation/)

**Gensyn**
- L2 mainnet (OP Stack, EVM) went live on 2026-04-22 together with Delphi, a permissionless AI prediction market. The $AI token TGE was 2026-04-29 (Binance Alpha, Coinbase, Kraken and others). A buyback-and-burn went live on 2026-05-01, using 0.5% of protocol fee revenue (70% burned, 30% to treasury). — [cryptonews](https://cryptonews.net/news/market/32750064/); [yellow.com](https://yellow.com/news/gensyn-ai-token-falls-17-percent-selling-pressure-may-2026); [ownyourmind](https://ownyourmind.ai/projects/gensyn/) (secondary)
- Price: about $0.019 in late Oct 2026, with only ~0.0014% of the 10B supply burned. — [cryptoticker](https://cryptoticker.io/en/prediction/gensyn-price-prediction/) (low-quality source)
- Official docs say RL Swarm and all Gensyn-hosted nodes are paused and Delphi is the current focus. The RL Swarm repo's last push was reportedly Jan 2026. — [Gensyn testnet docs](https://docs.gensyn.ai/testnet); [bestcloudmining](https://www.bestcloudmining.net/providers/gensyn/). A German review (Aug 2026) is headlined "Delphi verdient, das KI-Training pausiert" (Delphi earns, AI training paused). — [hoge.gg](https://hoge.gg/de/gensyn-2026-delphi-ki-training-pausiert/)
- Verde (refereed delegation that bisects a dispute to the first divergent step, with RepOps deterministic kernels) has been in production via the Judge evaluation product since Aug–Sep 2025. — [Miraheze wiki: Verde](https://ai.miraheze.org/wiki/Verde); [hoge.gg](https://hoge.gg/gensyn-verifiable-ai-compute-delphi-ai-token/)

**Prime Intellect**
- The p2p "protocol" GitHub repo was archived on 2026-01-27. It had powered INTELLECT-2 and SYNTHETIC-2. — [GitHub PrimeIntellect-ai/protocol](https://github.com/PrimeIntellect-ai/protocol)
- $130M Series A on 2026-07-08, at a $1B post-money valuation. The company reports >$100M ARR and >6,000 customers. It pivoted to post-training/RL infrastructure (Lab, opened May 2026; Environments Hub with >2,500 environments). — [KuCoin news](https://www.kucoin.com/news/flash/decentralized-ai-protocol-prime-intellect-completes-130m-series-a-total-funding-exceeds-150m); [Wikipedia](https://en.wikipedia.org/wiki/Prime_Intellect)
- INTELLECT-3 (106B MoE, 12B active) shipped in Nov 2025. No 2026 INTELLECT pre-training run was found. — [Bitget news](https://www.bitget.com/news/detail/12560605085055)

**Nous Research / Psyche**
- Psyche builds on DisTrO/DeMo and uses a Solana coordinator. — [Nous Psyche page](https://nousresearch.com/nous-psyche)
- A 2026 review says runs are still on Solana devnet and permissioned (a run admin authorizes nodes). Consilience 40B was pre-trained over the internet, but progress through its 20T-token target is undisclosed. Hermes 4.3 was reportedly trained across 24 Psyche nodes. — [ownyourmind](https://ownyourmind.ai/projects/nous-research/) (secondary; the same page mentions a "$1B SAFT")
- Consilience scored 24.2 on MMLU in Covenant's comparison table. — [Covenant-72B HTML](https://arxiv.org/html/2603.08163v2)

**Pluralis Research**
- Focus is "Protocol Learning": model-parallel training over low-bandwidth links, so that no node holds the full weights and models stay monetizable. Seed round $7.6M (USV, CoinFund), dated 2025-03-19. — [cryptorank](https://cryptorank.io/ico/pluralis-research); [Antoine Buteau essay](https://www.antoinebuteau.com/pluralis-is-a-bet-that-ai-needs-a-protocol-not-another-lab/)
- An Aug 2026 open multi-participant run is claimed by a third-party summary only. No token was confirmed. — [startupintros](https://startupintros.com/orgs/pluralis-research)

**Ambient (PoUW L1, proof of logits)**
- Ambient is an SVM (Solana) fork that replaces PoS with Continuous Proof of Logits. Miners run inference on a single large open model. Verification uses logit fingerprints and one-token spot checks, and cheating nodes are removed. — [Ambient litepaper](https://ambient.xyz/litepaper/); [Ambient docs](https://ambient.xyz/docs/learn/)
- Seed round $7.2M. Mainnet was targeted for "November" (unconfirmed), and the token was not released as of 2026-07-13. A Sep 2026 report claims 134B tokens served via a public API. The "~0.1% verification overhead" is unverified. — [blockeden](https://blockeden.xyz/blog/2026/02/11/ambient-ai-powered-blockchain-proof-of-logits/); [bex.co](https://bex.co/blog/2026/04/01/ambient-ai-l1-proof-of-logits-pow-blockchain-decentralized-inference) (secondary)
- Related: Pearl's "cuPOW" (useful PoW over matrix multiplication) is examined empirically in "The Usefulness Gap in PoUW" (arXiv 2606.04819, 2026). — [arXiv 2606.04819](https://arxiv.org/pdf/2606.04819)

**Qubic**
- Qubic is an L1 with "Useful PoW": CPU/GPU miners train neural nets for Aigarth (stated goal: AGI by 2027). Dogecoin ASIC mining launched 2026-04-01. "Outsourced Computing" went live Jul 29. A self-reported ARC-AGI-3 score of 0.38 was announced Sep 2026. — [CoinMarketCap AI](https://coinmarketcap.com/cmc-ai/qubic/what-is/); [Bitget/Paris Blockchain Week](https://www.bitget.com/news/detail/12560605291803); [Qubic blog Feb 2026](https://qubic.org/blog-detail/qubic-all-hands-recap-february-19-2026)
- Oct 2026: 1,404 wallets drained (~2.94T QU) through weak seed generation that had been reported in Feb. — [BlockSec Phalcon on X](https://x.com/Phalcon_xyz/status/2112059239829242142)

**Compute marketplaces (rental, not proof of training)**
- Akash Q1 2026: sources conflict. One headline says $5M compute spend. One analysis says lease revenue was ~$253k, down 45% QoQ. Q3 new leases were up 42% QoQ to 27k. AKT is ~90% below its peak. io.net revenue is self-reported (≈$20M annualized earlier, "4B tokens/day"), and IO is ~98% below its debut high. — [ownyourmind Akash](https://ownyourmind.ai/projects/akash/); [hoge.gg GPU race](https://hoge.gg/akash-vs-io-net-render-depin-gpu-race-2026/); [blockeden DePIN revenue](https://blockeden.xyz/blog/2026/04/12/depin-revenue-pivot-token-subsidies-ai-compute-akash-render-ionet/)
- AI×crypto sector valued at ~$26.2B (2026-10-29). Annualized on-chain revenue for decentralized GPUs is estimated at ~$180–220M. — [governance-research-reports](https://github.com/Ricosworks1/governance-research-reports/releases/tag/governance-ai-compute-governance-fragmentation-20261029) (low-provenance)
- Sentient: the token model is reportedly not yet operational, with 79% of tokens locked. — [pinkbrains](https://pinkbrains.io/blogs/the-state-of-decentralized-ai) (secondary)

### Inferences
- Classification by what is rewarded (Nov 2026):
  - **Pays for training (permissionless):** Bittensor SN3 Templar (pre-training), SN9 IOTA (pipeline pre-training), SN56 Gradients (fine-tuning/AutoML competition), and Qubic (its own Aigarth, self-reported).
  - **Training, permissioned or not token-paid yet:** Psyche (devnet, permissioned) and Pluralis (no token confirmed).
  - **Pivoted away from training:** Prime Intellect, which went centralized SaaS.
  - **Verification tech, product in prediction markets:** Gensyn.
  - **Inference or compute rental:** Ambient, Akash, io.net, Render, Hyperbolic, Nesa, Ritual, 0G, Allora and Sentient. Allora is prediction/inference aggregation.
- D-PoDL's competitor set is therefore narrow and dominated by Bittensor training subnets. None of them uses training as the consensus (block-production) mechanism. They all use PoS chains with validator-scored rewards. Ambient and Qubic are the only "useful work as consensus" L1s, and neither is a PoDL-style "train-a-model-to-mint-a-block" design.
- The Covenant-72B setup (8×B200 per peer) shows that "permissionless" in 2026 still means a datacenter-class minimum. D-PoDL's pre-hash/train/post-hash loop would face the same hardware reality.

### Gaps
- No primary-source data was retrieved for Flock.io (FLOCK, a federated-learning/AI Arena platform), Ritual, 0G, Hyperbolic, Nesa, Allora, Render, or Sentient's 2026 status. Two searches returned nothing on Flock.
- The exact current Bittensor emission formula (Taoflow vs alpha-price EMA) and the YC3 activation date are unresolved. taostats subnet-level emission numbers were not retrieved.
- Templar's post-Covenant activity (Jun–Nov 2026), and IOTA/Gradients emissions or traction numbers, were not found.
- The Ambient mainnet date is unconfirmed as of 2026-11-05.

## 2. Academic PoUW / PoDL work, 2024–2026, and whether D-PoDL's security model still holds

### Takeaway
PoUW research is active in 2025–2026: new proof-of-learning consensus proposals (SEDULity, PoUI, a 2025 IET "Proof of Distributed Deep Learning Work" paper), economics and usefulness critiques, and a skeptical SoK. The dominant 2025–26 critique (ePrint 2025/1814) is that utility does not add to the security budget. Older attack results (PoL spoofing) still stand. No source was found that directly analyzes or cites D-PoDL (ePrint 2023/1174). Its security model should be re-examined against these critiques rather than assumed sound.

### Cited Findings
- **"SoK: Is Proof-of-Useful-Work Really Useful?"** (Dikshit, Emami, Fridgen, Sedlmeir; IACR ePrint 2025/1814, received 2025-10-03). It reviews >50 PoUW constructions, builds a taxonomy (difficulty adjustment, verifiability, architecture, incentives) and a formal economic model (miner incentives, solution reusability, external market value). It concludes that PoUW is "not as useful as expected" because economic and societal utility does not contribute to the security budget. It recommends verifiable computation, partial incentive allocation and utility-aware difficulty adjustment. The abstract page does not list which schemes are covered, so it is unknown whether D-PoDL is among them. — [ePrint 2025/1814](https://eprint.iacr.org/2025/1814)
- **SEDULity** (arXiv 2512.13666, revised Jun 2026): a proof-of-learning framework that encodes the template block into training and designs a "hard to solve, easy to verify" useful function as a PoW substitute. This is conceptually the closest recent peer to D-PoDL's pre-hash design. — [arXiv 2512.13666](https://arxiv.org/abs/2512.13666)
- **"Blockchain Consensus Scheme Based on the Proof of Distributed Deep Learning Work"** (Zhi et al., IET Software, 2025): a near-namesake of D-PoDL. Contents were not reviewed. — [Wiley](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/sfw2/3378383)
- **Proof of Useful Intelligence (PoUI)** (arXiv 2504.17539, 2025): a hybrid of staking and useful computation. — [arXiv 2504.17539](https://arxiv.org/pdf/2504.17539)
- **SNARKChain** (arXiv 2510.09729, 2025): PoUW where the useful work is a SNARK-proving marketplace. — [arXiv 2510.09729](https://arxiv.org/html/2510.09729v2)
- **"The Economics of Proof-of-Useful-Work"** (arXiv 2606.06700, 2026) and **"The Usefulness Gap in PoUW: Pearl's cuPOW"** (arXiv 2606.04819, 2026). — [2606.06700](https://arxiv.org/pdf/2606.06700); [2606.04819](https://arxiv.org/pdf/2606.04819)
- **Quantum-resilient decentralized AI economies** (arXiv 2606.24942, Jun 2026): states that a formal (post-quantum) security game for ML-work consensus "remains an open research problem". — [arXiv 2606.24942](https://arxiv.org/abs/2606.24942)
- **BlockTrain** (arXiv 2606.24722, 2026): decentralized AI training and inference on a blockchain. Contents were not reviewed. — [arXiv 2606.24722](https://arxiv.org/pdf/2606.24722)
- **SENTINEL** (arXiv 2603.03592, 2026): stagewise integrity verification for pipeline-parallel decentralized training, covering activation and gradient manipulation. — [arXiv 2603.03592](https://arxiv.org/pdf/2603.03592)
- **IOTA primer** (arXiv 2507.17766, Jul 2025) and **Gauntlet**, "Incentivizing Permissionless Distributed Learning of LLMs" (arXiv 2505.21684, May 2025): the incentive designs behind SN9 and SN3. — [IOTA](https://arxiv.org/pdf/2507.17766); [Gauntlet](https://arxiv.org/html/2505.21684v1)
- **Governance angle:** "Distributed and Decentralised Training: Technical Governance Challenges" (arXiv 2507.07765, 2025). — [arXiv 2507.07765](https://arxiv.org/pdf/2507.07765)
- **PoL attacks:** Fang et al., "Proof-of-Learning is Currently More Broken Than You Think" (IEEE EuroS&P 2023). They give spoofing attacks that work across verification configurations at a fraction of honest-training cost. The weakness comes from verifiers checking only a subset of logged updates. They argue that provably robust PoL is unattainable without deeper theory of DL optimization. — [arXiv 2208.03567](https://arxiv.org/pdf/2208.03567). This targets Jia et al., "Proof-of-Learning: Definitions and Practice" (IEEE S&P 2021). — [arXiv 2103.05633](https://arxiv.org/pdf/2103.05633). Zhang et al. 2021, "Adversarial Examples for PoL", is the earlier attack. — [fugumt mirror of 2108.09454](https://fugumt.com/fugumt/paper_check/2108.09454v1_enmode)
- [background, not re-verified this session] Earlier foundations D-PoDL builds on:
  - Chenli et al., "Energy-recycling blockchain with proof-of-deep-learning" (IEEE DAPPCON 2019), [arXiv 1902.03912](https://arxiv.org/abs/1902.03912).
  - Ofelimos, "Combinatorial Optimization via Proof-of-Useful-Work" (Fitzi, Kiayias, Panagiotakos, Russell; CRYPTO 2022), [ePrint 2021/1379](https://eprint.iacr.org/2021/1379).

### Inferences
- The SoK's argument applies to D-PoDL. If miners would train the models anyway, or can reuse training across blocks or tasks, the training work no longer adds Sybil or 51% cost. The ePrint 2025/1814 recommendations amount to a critique of D-PoDL's current design. Partial incentive allocation means pairing useful work with stake or a hash component. Utility-aware difficulty means making training effort count only when it is bound to the block. D-PoDL's pre-hash/post-hash binding is one answer to the reuse problem. A revival should explicitly model:
  - reuse/precomputation: train once, then grind many architectures;
  - grinding of the Hash-to-Architecture mapping;
  - the PoL spoofing results above, when verifiers check only partial training;
  - plagiarism, i.e. resubmitting or fine-tuning someone else's registered model;
  - validator/task-publisher collusion, e.g. a publisher who leaks the test set.
- D-PoDL's "is the security model sound" question is open. No 2024–26 source validates or refutes it directly, and the field's consensus is skeptical of pure-PoUW security. The design trend is hybrid: PoS or a hash-based chain for consensus, with training rewarded as an application-layer incentive.

### Gaps
- Citation tracking for ePrint 2023/1174 (D-PoDL) and the Chenli PoDL line was not done (no Google Scholar or Semantic Scholar query). Whether the 2025 IET "Proof of Distributed Deep Learning Work" paper is a D-PoDL follow-up or an independent work is unknown.
- The full text of SoK 2025/1814 was not read, so it is unknown whether it explicitly treats PoDL or D-PoDL or lists ML-specific attacks.
- No 2024–26 survey dedicated to proof of training (separate from general PoUW) was located in this session.

## 3. Contribution-scoring and reward designs that could replace or improve D-PoDL's proposer/contributor split

### Takeaway
The 2025–26 designs proven at scale score each contribution by measured loss improvement on held-out or assigned data. They stabilize scores over time with skill ratings, use per-peer data assignment to detect copying, normalize update norms against domination, and aggregate validator weights with stake-weighted, clipped consensus (Yuma). These map directly onto D-PoDL's referenced-model reward split and its anti-plagiarism needs.

### Cited Findings
- **Gauntlet / Templar (primary):**
  - LossScore is the loss change from applying a peer's pseudo-gradient, measured on a small batch.
  - A persistent OpenSkill rating smooths per-round noise.
  - Fast checks cover liveness and sync with the current model.
  - The top contributors per round are selected, capped at 20 in Covenant.
  - A peer whose update improves loss more on random data than on its assigned data gets a negative score. This is the anti-copying and anti-duplicate mechanism.
  - Updates are normalized to the median norm so no single peer dominates aggregation.
  - There is no full Sybil or Byzantine-robustness analysis.
  — [Covenant-72B HTML](https://arxiv.org/html/2603.08163v2); [Gauntlet arXiv 2505.21684](https://arxiv.org/html/2505.21684v1)
  - Penalties apply for late, missing or malformed submissions. A third-party review flags inconsistent scoring equations and thin empirical support in the Gauntlet paper. — [Moonlight review](https://www.themoonlight.io/en/review/incentivizing-permissionless-distributed-learning-of-llms)
- **Yuma Consensus (Bittensor):** validators submit weight vectors over miners. Rewards are distributed per tempo by stake-weighted consensus, which clips weights that deviate from the stake majority, and validator bonds reward early agreement. YC3 adds fixed-point bonds, per-pair scaling and liquid alpha. — [hoge.gg Yuma 2026](https://hoge.gg/yuma-consensus-2026-how-bittensor-decides-who-gets-paid/) (secondary)
- **Gradients SN56:** miners submit repo plus commit hash, a commit-and-reproduce pattern. This makes copying observable and lets validators rerun the training method. — [taooutsider](https://www.taooutsider.com/blog/machine-learning-on-bittensor-training-inference-evaluation/)
- **Gensyn Verde:** refereed delegation. On dispute, both parties' training traces are bisected to the first divergent step, and only that step is recomputed. RepOps (deterministic kernels) makes the recomputation bit-exact. — [bex.co](https://bex.co/blog/2026/05/05/gensyn-rl-swarm-decentralized-ml-training-ethglobal); [Miraheze wiki: Verde](https://ai.miraheze.org/wiki/Verde)
- **Ambient:** logit fingerprints, one-token spot checks and work-credit penalties, i.e. probabilistic verification plus slashing of credits. — [Ambient docs](https://ambient.xyz/docs/learn/)
- **Pipeline integrity:** SENTINEL (2026) verifies stages in model-parallel training. — [arXiv 2603.03592](https://arxiv.org/pdf/2603.03592)
- **PoUW incentive recommendations:** partial incentive allocation and utility-aware difficulty. — [ePrint 2025/1814](https://eprint.iacr.org/2025/1814)
- [background, not re-verified this session] Byzantine-robust aggregation:
  - Krum, Blanchard et al., NeurIPS 2017 ([paper](https://papers.nips.cc/paper/2017/hash/f4b9ec30ad9f68f89b29639786cb62ef-Abstract.html)).
  - Coordinate-wise trimmed mean and median, Yin et al., ICML 2018 ([arXiv 1803.01498](https://arxiv.org/abs/1803.01498)).
  - Centered clipping, Karimireddy et al., ICML 2021 ([arXiv 2012.10333](https://arxiv.org/abs/2012.10333)).
- [background, not re-verified this session] Data-Shapley valuation, Ghorbani & Zou, ICML 2019 ([arXiv 1904.02868](https://arxiv.org/abs/1904.02868)). Exact Shapley is exponential in the number of players, and practical systems use Monte-Carlo or leave-one-out approximations. Gauntlet's LossScore is effectively a cheap leave-one-in marginal-contribution estimate.

### Inferences
Concrete upgrades for D-PoDL:
- **Replace the fixed proposer/contributor split.** Pay referenced-model contributors in proportion to a measured, validator-reproducible marginal improvement: loss delta on a hidden or rotating eval set, or a Monte-Carlo Shapley estimate over the referenced models. Smooth it with a rating (OpenSkill or EMA) so one lucky round does not dominate.
- **Defeat plagiarism of ModelRegistry/MTX submissions** with three mechanisms:
  1. Commit-reveal: commit H(model‖nonce‖miner) in block N and reveal in N+k. This is standard practice, and the Gradients repo+commit pattern is a variant.
  2. Assigned-data checks: improvement on miner-specific seeded data versus random data, as Gauntlet does. This fits D-PoDL well because the pre-hash can seed the data shard as well as the architecture.
  3. Similarity or fingerprint checks against registered models, penalizing near-duplicates.
- **Use Verde-style bisection disputes**, or partial-trace spot checks, instead of full retraining. Then explicitly address Fang et al.'s finding that partial checks invite spoofing. Randomness must be unpredictable, e.g. seeded from a future block hash.
- **Add staking and slashing for validators and task publishers**, and Yuma-style clipping of outlier validators, to resist collusion. Task publishers who post leaked or degenerate test sets should be bondable.

### Gaps
- No 2025–26 paper was found that benchmarks Krum, trimmed mean or centered clipping inside a live token-incentivized training network. Covenant uses only median-norm normalization plus scoring-based selection.
- No primary source for the YC3 specification was retrieved. The details above come from a secondary explainer.

## 4. Regulatory and market environment for launching an AI reward token (2026)

### Takeaway
US market-structure law (the CLARITY Act, H.R. 3633) stalled after a failed Senate cloture vote on 2026-09-15 (49–50). Passage this Congress is now seen as unlikely, so US token classification remains unsettled. The token market for AI/DePIN is weak: most 2025–26 launches trade 90%+ below their highs. Launching a new standalone reward token in late 2026 is high-risk.

### Cited Findings
- Senate cloture on the motion to proceed to H.R. 3633 failed 49–50 on 2026-09-15, with 60 votes needed. Sen. Tillis voted no to preserve a motion to reconsider, and Sen. Lummis declared the bill dead. The open disputes include the decentralization threshold for escaping securities treatment and ethics rules for officials. — [DLA Piper, Sep 2026](https://www.dlapiper.com/en/insights/publications/2026/09/senate-fails-to-advance-the-clarity-act); [Orrick, Oct 2026](https://www.orrick.com/en/Insights/2026/10/The-CLARITY-Act-Stalls-in-the-Senate-Whats-Next-for-Digital-Asset-Regulation); [coinpaprika](https://coinpaprika.com/news/4950-senate-stall-crypto-clarity-act-hinges)
- No post-midterm (after 2026-11-03) reporting on revival was found. — searched 2026-11-05
- Token-market signal: Gensyn's $AI is at ~$0.019 six months after TGE, AKT is ~90% below its peak, IO is ~98% below its debut high, and 79% of Sentient's tokens are locked. — [cryptoticker](https://cryptoticker.io/en/prediction/gensyn-price-prediction/); [hoge.gg](https://hoge.gg/akash-vs-io-net-render-depin-gpu-race-2026/); [pinkbrains](https://pinkbrains.io/blogs/the-state-of-decentralized-ai)
- [background, not re-verified this session] EU MiCA (Regulation (EU) 2023/1114) has applied to crypto-asset service providers since 2024-12-30. Member-state CASP transitional periods end by 2026-07-01 at the latest. Offering a non-stablecoin token to the public in the EU requires a MiCA Title II white paper. — [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2023/1114/oj)

### Inferences
- D-PoDL's ERC20 mint to miners is a reward for work rather than a sale, which lowers but does not remove securities and white-paper exposure. A research testnet token with no economic value, or rewards paid in an existing network's token (TAO alpha via a subnet), avoids most of this.

### Gaps
- MiCA 2026 enforcement specifics and any EU guidance on "mining-style" reward tokens were not researched this session.
- The SEC's 2026 posture (e.g., any "token taxonomy" or safe-harbor rulemaking) was not checked.

## 5. Where is the niche for D-PoDL in 2026?

### Takeaway
D-PoDL's most defensible niche is a rigorous research-grade reference implementation and testbed of training-as-consensus. It would include an explicit threat model and a security-budget analysis answering the SoK critique, deployable as a Bittensor subnet or appchain module rather than as a new L1 token. Practical training incentives are now owned by Bittensor subnets. A new "useful-work L1" would compete with Qubic and Ambient in a weak token market.

### Cited Findings (supporting evidence, see sections above)
- Bittensor subnets have demonstrated permissionless, token-incentivized pre-training at 72B scale with an existing validator, emission and market stack. — [Covenant-72B](https://arxiv.org/abs/2603.08163)
- Well-funded peers retreated from on-chain training: Prime Intellect archived its protocol (Jan 2026) and Gensyn paused RL Swarm in favor of Delphi. — [GitHub](https://github.com/PrimeIntellect-ai/protocol); [Gensyn docs](https://docs.gensyn.ai/testnet)
- The academic frontier still treats formal security of ML-work consensus as open. — [arXiv 2606.24942](https://arxiv.org/abs/2606.24942); [ePrint 2025/1814](https://eprint.iacr.org/2025/1814)
- Closest academic peers to the pre-hash/train design are SEDULity (2025–26) and Zhi et al. (IET 2025). — [arXiv 2512.13666](https://arxiv.org/abs/2512.13666); [Wiley](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/sfw2/3378383)

### Inferences
Options ranked by feasibility and differentiation:
1. **Open reference implementation plus paper.** This would be the only public, end-to-end D-PoDL codebase (Hash-to-Architecture, pre/post-hash, ModelRegistry/TaskRegistry, reward split) with benchmarks on grinding, reuse, plagiarism and PoL spoofing, and a security-budget model per ePrint 2025/1814. Low cost and high academic value. It could be compared directly with SEDULity.
2. **Bittensor subnet.** TaskRegistry maps to subnet task definitions, validators score models with loss delta or held-out eval, and Hash-to-Architecture acts as an anti-precomputation and anti-copy device: each miner's architecture or data seed is bound to a recent block hash. The subnet earns alpha and TAO emissions instead of minting its own ERC20. Competitive overlap: Gradients SN56 (training-method competition) and older model-competition subnets.
3. **Ethereum L2/appchain or restaked AVS** (e.g., EigenLayer-style). Validators restake to attest post-hash checks and model scores, with slashing. Keeps the Ethereum ModelRegistry design. Higher engineering and regulatory burden, and no evidence was found of a live AVS doing this (not searched).
4. **New standalone L1 or PoUW token.** Least attractive given the token market and US regulatory limbo, plus incumbents (Qubic, Ambient) and the SoK critique.

Reusable components:
- SparseLoCo / DeMo / DisTrO for communication-efficient training.
- Gauntlet scoring, including the assigned-vs-random data anti-copy test.
- Verde/RepOps-style deterministic replay for disputes.
- Commit-reveal model submission.
- Yuma-style stake-weighted validator consensus.

### Gaps
- No search was done on EigenLayer AVSs for ML verification, or on whether any group has implemented PoDL or D-PoDL code publicly since 2023.
- Template or cost data for launching a Bittensor subnet in 2026 (registration burn cost, the 128→256 cap) was not retrieved.
