# Prior art for a D-PoDL revival: blockchain protocols where deep-learning training is the useful work (state as of 2026-11-05)

Scope note: items the earlier report already covered ([DPoDL revival research November 2026.md](../../reports/DPoDL%20revival%20research%20November%202026.md)) get one line each in Q2. Here "our design" means validator-re-measured useful-work training (V), commit-reveal (C), stake/challenge/bisection (S), lineage royalties (L) and L2 settlement (L2). Closeness ratings (High/Med/Low) are my own judgements, not sourced.

## Q1. Who has cited D-PoDL, what venue was it published in, and what have the authors done since?

### Takeaway
D-PoDL was published at NSS 2023 (LNCS). Its citers are few, and none implements D-PoDL. The closest citers are BagChain (IEEE TMC 2025), a 2026 inference-as-PoW paper from Edinburgh, and an IOG paper on Ofelimos-style local search. I found no D-PoDL follow-up, implementation or IOG/Cardano product from Su or Larangeira dated 2024–2026. The authors appear to have left the line, so nobody is likely to scoop a revival from the original team.

### Cited Findings
- **Venue.** "Provably Secure Blockchain Protocols from Distributed Proof-of-Deep-Learning" (Su, Larangeira, Tanaka) appeared at the 17th Int'l Conf. on Network and System Security (NSS '23), Springer LNCS, DOI 10.1007/978-3-031-39828-5_7. The preprint is IACR ePrint 2023/1059 — [Springer](https://link.springer.com/chapter/10.1007/978-3-031-39828-5_7); [ePrint 2023/1059](https://eprint.iacr.org/2023/1059); [IOG paper page](https://www.iog.io/papers/provably-secure-blockchain-protocols-from-distributed-proof-of-deep-learning). It was also presented at SocialSec 2023 — [slides](https://socialsec2023.cyber.kent.ac.uk/presentations/3-2.pdf).
- **Earlier work by the same trio.** "How to Prove Work: With Time or Memory", IEEE Access 2022 — [dblp (via search snippet)](https://dblp.org/pid/62/6540.html).
- **Citing papers indexed by Semantic Scholar (queried 2026-11-05; 8 entries, likely incomplete)** — [Semantic Scholar API](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/978-3-031-39828-5_7/citations?fields=title,year,venue,authors,externalIds&limit=100):
  - **Proof-of-Machine-Learning-Inference: Mining Knowledge, Not Hashes** (Wan-Ki Wong, Michele Ciampi, Rik Sarkar), arXiv 2610.26713, submitted 2026-10-19. Miners run user-requested ML *inference* (LLMs, diffusion) in place of hashing. Security reduces to the Bitcoin Backbone model, and a simulation shows block times near target. No code link and no venue — [arXiv 2610.26713](https://arxiv.org/abs/2610.26713). Closeness: Med on the consensus formalism, Low on our design (inference rather than training; no stake, disputes or lineage).
  - **BagChain: A Dual-Functional Blockchain Leveraging Bagging-Based Distributed ML** (Cui, Ling, Zhou, Wang, Ding, Gao), IEEE Trans. Mobile Computing 2025, DOI 10.1109/TMC.2025.3624804; arXiv 2502.11464; workshop version at IEEE Globecom Wkshps 2024 — [Semantic Scholar](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/978-3-031-39828-5_7/citations?fields=title,year,venue,authors,externalIds&limit=100). Closeness: Med, as ML-as-consensus that is peer-reviewed and published. Its group (Southeast Univ./UC Davis) overlaps with the authors of "Optimization-based PoUW" (arXiv 2405.19027) and SEDULity — [arXiv listing](https://arxiv.org/abs/2405.19027).
  - **Efficient and Proof-of-Useful-Work Friendly Local-Search for Distributed Consensus** (Fitzi, Kiayias, Michel, Panagiotakos, Russell — IOG), ePrint 2025/2091, received 2025-11-13. It introduces FRLS, a distributed local-search algorithm "consistent with the Ofelimos architecture", benchmarked on cumulative scheduling and warehouse location — [ePrint 2025/2091](https://eprint.iacr.org/2025/2091); [IOG library](https://www.iog.io/papers/efficient-and-proof-of-useful-work-friendly-local-search-for-distributed-consensus). IOG's PoUW research thus continues on combinatorial optimisation (Ofelimos), not deep learning.
  - **Can Blockchains Reliably Train Machine Learning Models?** (Li, Dahmani), arXiv 2307.07066, 2023 — [arXiv](https://arxiv.org/pdf/2307.07066).
  - Two IoT blockchain papers (Elsaadany & Bégin, Cluster Computing 2024) cite D-PoDL only tangentially.
- A 2025 systematic literature review on PoUW consensus (ScienceDirect, *Blockchain: Research and Applications*) also cites Su et al. as a "learning-based PoUW with better accuracy" — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2096720925001149).

### Inferences
- The original authors show no sign of reviving D-PoDL, and IOG's PoUW effort sits on the Ofelimos/local-search track. Being scooped by the original team is unlikely.
- Most of D-PoDL's citers in 2024–2026 ask "what PoUW can replace hashing" (inference, bagging, local search). None of them builds the market/dispute/lineage stack we plan.

### Gaps
- dblp (bot wall) and the Semantic Scholar author search (HTTP 429) were unavailable. The 2024–2026 publication lists for Xiangyu Su and Mario Larangeira are therefore unverified: "no follow-up found" is an absence of evidence. Google Scholar "cited by" was not checked and probably lists more citers (theses, Chinese-language journals).
- Whether Xiangyu Su finished a PhD thesis on PoUW at Tokyo Tech (now Institute of Science Tokyo) is unknown.

## Q2. 2025–2026 papers and preprints closest to our design

### Takeaway
The literature splits into four strands. None of them combines all of V+C+S+L+L2:
- (a) PoUW-consensus theory: SEDULity, Pearl/cuPOW, PoML-Inference, Pass's economics.
- (b) Verifiable or auditable training without a chain: Gensyn OPEN-1B/Verde, optimistic verifiable training, SENTINEL, OVIG, PoTS.
- (c) Incentive mechanisms without verification infrastructure: VISTA, the truthful distributed-SGD payment mechanism, PoL with incentive security, the quantum-resilient token economy.
- (d) Attribution/royalty work that is off-chain or conceptual: Shapley-FL, Content ARCs, MAGNET.

The closest single item to the *mechanism* is OPEN-1B (Sep 2026), which provides bitwise-replayable steps plus collective per-step auditing, with no chain or incentives. The closest to the *product shape* is a hobby repo, PoLChain (Base Sepolia, Sep 2026).

### Cited Findings
**Already covered (1 line each):**
- PoUW SoK, ePrint 2025/1814: utility does not add to security budget — [ePrint](https://eprint.iacr.org/2025/1814).
- SEDULity (Cao, Doger, Ulukus), arXiv 2512.13666, Dec 2025: template block encoded into training — [arXiv](https://arxiv.org/abs/2512.13666).
- "Proof of Distributed Deep Learning Work", IET Software 2025 — [Wiley](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/sfw2/3378383).
- PoUI, SNARKChain (arXiv 2510.09729), SENTINEL (arXiv 2603.03592, Pluralis, pipeline-parallel integrity), OVIG (arXiv 2606.21045), Gensyn Verde, Ambient proof-of-logits, Qubic: see the earlier report.

**New items, by strand:**

*(a) PoUW consensus where ML is the work*
- **Pearl / cuPOW.** Komargodski & Weinstein, "Proofs of Useful Work from Arbitrary Matrix Multiplication", arXiv 2504.09971 (2025-04-14, v4), is the basis of the **Pearl L1** — [arXiv](https://arxiv.org/abs/2504.09971); [Pearl repo README](https://github.com/pearl-research-labs/pearl).
  - Status and repo: mainnet launched 2026-04-27 — [onebullex](https://www.onebullex.com/news/articles/pearl-research-labs-launches-proof-of-useful-work-mainnet-on-april-27-2026). The monorepo contains the full node, a vLLM miner, a Plonky2 ZK-PoW circuit and XMSS post-quantum signatures. Last commit 2026-10-28 ("security: harden orphan handling…"), checked by shallow clone on 2026-11-05 — [GitHub](https://github.com/pearl-research-labs/pearl).
  - Forks and partners (secondary source, approximate): an MoE hard fork 2026-06-12, a salted noise-seed hard fork 2026-08-11, and an FP8 upgrade announced 2026-09-14. A Together AI Gemma-4-31B "pearl" endpoint launched 2026-05-15 — [hashrateindex/KuCoin/pearlcoinguide via search](https://hashrateindex.com/blog/pearl-prl-ai-compute-cryptocurrency/); figures conflict across sources.
  - **Critique.** Basu, "The Usefulness Gap in PoUW: An Empirical Study of Pearl's cuPOW", arXiv 2606.04819 (2026-06-03). It finds that the 24 EH/s network (~320k GPU-equivalents, ~112 MW) "produces zero useful AI computation": the verification "accepts random matrices by design", and the dominant miner contains no inference code. The authors had 44 pool-accepted shares from their own miner — [arXiv](https://arxiv.org/abs/2606.04819).
  - Follow-ups: Ding, "On Pearl Blockchain's PoUW: Systematization and Flexibility", arXiv 2610.25347 (2026-10-18) — [arXiv](https://arxiv.org/abs/2610.25347). Rafael Pass, "The Economics of Proof-of-Useful-Work", arXiv 2606.06700 (2026-06-04), a competitive-equilibrium model with "Bitconia/Fortessia/Duplexia" regimes — [arXiv](https://arxiv.org/abs/2606.06700). Bar-On, Komargodski, Weinstein, "Proof of Work With External Utilities", arXiv 2505.21685 (2025-05-27): miners with external AI rewards may concentrate useful tasks in a single block — [arXiv](https://arxiv.org/abs/2505.21685).
  - Closeness: High as "deployed PoUW-for-AI L1", Low on our mechanism. Pearl verifies matmul hardness, not training progress, and has no lineage or disputes.
- **PoGO** (Orlicki), arXiv 2504.07540 (2025-04-10). Proof of Gradient Optimization: 4-bit quantised gradients plus Merkle proofs over the full 32-bit model, with random leaf checks and a cost analysis for GPT-3-scale models. A design only, with no code link — [arXiv](https://arxiv.org/abs/2504.07540). Closeness: Med (training-as-consensus with sampling verification). Single-author preprint.
- **Proof of Training** (ICCS 2025): delegates ML training to a blockchain network, with training confirmations recorded on a public chain — [ICCS PDF](https://www.iccs-meeting.org/archive/iccs2025/papers/159040203.pdf).
- **Rafid & Sakib**, arXiv 2508.12138 (2025-08-16): replaces Bitcoin PoW with *centralised* cloud training scored by parameters trained and loss reduction, plus a weighted lottery — [arXiv](https://arxiv.org/abs/2508.12138). Closeness: Low, because it is trusted-server.
- **Proof-of-Learning with Incentive Security** (Zhao, Fang, Wang, et al.), arXiv 2404.09005, v8 updated 2026-05-04: an "incentive-secure" PoL where honest training maximises a rational prover's utility — [arXiv](https://arxiv.org/abs/2404.09005). Related: "It Takes Two" peer-prediction for the verifier's dilemma, arXiv 2406.01794 — [arXiv](https://arxiv.org/html/2406.01794). Closeness: Med-High on incentive theory. These are the papers a threat-model section must engage with.

*(b) Verifiable or auditable training (no chain)*
- **OPEN-1B: A Fully Auditable Training Run** (Donaghy, Wilcox, Ersoy, …, Fielding, Grieve — Gensyn), arXiv 2609.17380 (2026-09-15).
  - Every training op is bitwise-reproducible across heterogeneous commodity hardware, with ordering imposed on kernel reductions, batch ordering and collectives. Any single step of a distributed run can be replayed on one machine. A "collective verification scheme" has many independent auditors each certify individual steps.
  - Release: dataset, every intermediate checkpoint, training code and audit harness — [arXiv](https://arxiv.org/abs/2609.17380).
  - Costs: int8 QAT GEMMs run "several times slower" than a bf16 baseline. One secondary write-up says only a small share of the 80,957 steps had an accepted audit and no 100-step segment had been confirmed at the time of writing — [pebblous](https://blog.pebblous.ai/blog/open-1b-auditable-training-run/en/); [runtimewire](https://runtimewire.com/article/gensyn-open-1b-auditable-ai-model-training).
  - Closeness: **High for S** (step-level replay is exactly what our bisection referee needs) but no on-chain settlement, stake or lineage. It also weakens our planned "pinned-stack replay" kill criterion, since cross-hardware bitwise replay is now shown at 1B scale.
- **Optimistic Verifiable Training by Controlling Hardware Nondeterminism** (Srivastava et al.), arXiv 2403.09603 (2024): adapts the interactive verification game to training steps — [arXiv](https://arxiv.org/pdf/2403.09603). Already the basis of our rounding-log plan.
- **opML** (Conway / Hyper Oracle-ORA), arXiv 2401.17555: an optimistic fraud-proof bisection game for ML, inference-focused — [arXiv](https://arxiv.org/html/2401.17555v1). Repo `ora-io/opml` last commit 2024-12-11, so dormant — [GitHub](https://github.com/ora-io/opml).
- **Optimistic TEE-Rollups** (Chan et al.), arXiv 2512.20176 (2025-12-23): TEE plus an optimistic dispute that bisects over Transformer layers, then matmuls; inference only — [arXiv](https://arxiv.org/abs/2512.20176).
- **PoTS: Proof-of-Training-Steps** (Seddik, Souihi, Tamaazousti, Tucci Piergiovanni — CEA-LIST), arXiv 2510.15106, FLLM 2025: an auditor checks that an LLM developer followed the declared recipe — [arXiv](https://arxiv.org/abs/2510.15106).
- **The Power of Backdoor Absorption in Community Training** (same group), arXiv 2607.06643 (2026-07-07). A DTMC proof that a randomised scheduler plus a lazy verification oracle invoked on 10% of steps drives bounded-adversary success toward zero — [arXiv](https://arxiv.org/abs/2607.06643). Useful formal support for spot-check rates in our challenge game.
- **Unextractable Protocol Models** (Pluralis), arXiv 2605.23464, NeurIPS 2025 — [arXiv](https://arxiv.org/abs/2605.23464). About model-parallel protocol ownership, not verification.

*(c) Incentive-compatible decentralised training*
- **VISTA** (Akbari Nodehi, Moradi, Mohajer, Maddah-Ali), arXiv 2605.07841 (2026-05-08). Reports are accepted and rewarded only if mutually consistent within an adaptive threshold. The authors prove SGD-like convergence *without* an honest majority against rational adversaries. No chain and no code link — [arXiv](https://arxiv.org/abs/2605.07841).
- **Gradient Manipulation in Distributed SGD with Strategic Agents** (Chen, Wang), arXiv 2603.27962 (2026-03-30): a fully distributed payment mechanism claimed to guarantee truthfulness and accurate convergence — [arXiv](https://arxiv.org/abs/2603.27962).
- **Quantum-Resilient Decentralized AI Economies** (Barbaccia, Vhaduri, Dibbo), arXiv 2606.24942 (2026-06-22): a three-layer compute/validation/economics architecture, a (θc, θw, W) closed-loop token economy and a sufficient-stake condition for honest participation — [arXiv](https://arxiv.org/abs/2606.24942). Closeness: Med, since it supplies a stake condition but is not a training-verification protocol.

*(d) Lineage, attribution, autoresearch*
- **MAGNET** (Kim, Park), arXiv 2603.25813 (2026-03-26): autoresearch pipeline, BitNet b1.58 training, DiLoCo-based merging and **on-chain contribution tracking on the "HOOTi EVM chain"** — [arXiv](https://arxiv.org/abs/2603.25813). Closeness: Med-High on concept (agent-driven research plus on-chain contribution records). It does not appear to have adversarial verification, stake or disputes, and it is a 2-author preprint with no venue.
- **Economics Model for Federated LLM Training via Blockchain** (ACM WWW Companion 2026): Shapley contribution scoring plus a tokenised reward layer — [ACM DL](https://dl.acm.org/doi/10.1145/3774905.3794694). TRIP-Shapley (arXiv 2505.23246) handles attribution in P2P-FL but relies on a trusted coordinator — [arXiv](https://arxiv.org/html/2505.23246). SurrogateSHAP (ICML 2026 poster) offers retraining-free contributor attribution — [ICML](https://icml.cc/virtual/2026/poster/63145). Content ARCs (arXiv 2503.14519) proposes provenance metadata for royalties and calls attribution at scale "an open research challenge" — [arXiv](https://arxiv.org/pdf/2503.14519).

### Inferences
- **Not scooped on the combination.** I found no paper, preprint or workshop item through 2026-11-05 that has all of these together: validator re-measurement of training improvements, commit-reveal submissions, a stake/challenge/bisection dispute down to a training step, lineage royalties and L2 settlement.
- The pieces now exist separately and are citable. Bisection-to-step and replay come from Srivastava 2024 and OPEN-1B 2026. Incentive-security comes from Zhao et al., VISTA and Chen-Wang. Spot-check rates come from Seddik 2026. On-chain contribution logs come from MAGNET. A new paper would be judged as *integration plus a security argument*, not as a new primitive.
- Pearl is the cautionary precedent. The first live "PoUW for AI" L1 was shown empirically to do no useful work. That strengthens the case for our design choice to *measure* utility (validator re-measured loss) rather than prove *hardness*.

### Gaps
- I did not systematically search NeurIPS 2026 workshop proceedings (most are posted around December), FC 2027 or AFT 2026 accepted lists, or IACR ePrint by keyword. There may be in-review items I missed.
- I did not read the full text of PoGO, MAGNET or the IET paper, so the absence of disputes or stake in them is inferred from abstracts.
- The "Proof-of-Intelligence" claim for Lightchain AI (Mainnet V2, ~April 2026) comes from a promotional KuCoin blog and is unverified — [KuCoin](https://www.kucoin.com/blog/what-is-proof-intelligence-vs-proof-of-work).

## Q3. Open-source implementations and their activity

### Takeaway
No maintained open-source codebase implements D-PoDL or a full verifiable-training market with disputes. The closest public code is:
- PoLChain, a tiny hobby prototype on Base Sepolia (Sep 2026) with ZK-verified MNIST scoring and marginal-improvement rewards, which mirrors our Phase 1.
- Gensyn's OPEN-1B release (audit harness, Sep 2026), whose repo location I could not confirm.
- Pearl (active, but matmul PoUW, not training).
- Templar/Crusades (scoring-based training, no disputes; activity slowed after Covenant's April 2026 exit from Bittensor).

### Cited Findings
Commit dates were checked by shallow `git clone` on 2026-11-05. The GitHub REST API was blocked in this session.
- **jacksongeiger/polchain**, last commit 2026-09-10 ("Era 2: contract-computed scores, marginal rewards, difficulty filter"), 0 stars. Per the README:
  - It runs live on Base Sepolia (`TaskManagerV3` at 0x471e…2992). Each block, four miners train MNIST, generate an EZKL/Halo2 proof of a forward pass on one of 250 sealed challenge batches drawn from the parent block hash, and the contract computes scores from the proof's logits.
  - Reward is `pool × max(0, score_i − base)/Σ`, and paid models are merged by FedAvg. The contract is ownerless after `seal()`.
  - The README discloses its residuals: the batch pool can be precomputed, the poster can grind batches, and "a proof attests inference quality, not training effort" — [GitHub](https://github.com/jacksongeiger/polchain).
  - Closeness: **High to our Phase 1 product shape** (escrow, chain-bound challenge selection, measured-improvement reward, L2 testnet). It has no stake, disputes, bisection or lineage beyond merging, and it is toy-scale.
- **NeptoLab/POL** ("Proof of Learning Blockchain AGI Implementation"), last commit 2025-07-09, 0 stars, dormant — [GitHub](https://github.com/NeptoLab/POL).
- **pearl-research-labs/pearl**, last commit 2026-10-28, active: a production L1 node, vLLM miner and ZK-PoW — [GitHub](https://github.com/pearl-research-labs/pearl).
- **ora-io/opml**, last commit 2024-12-11, dormant — [GitHub](https://github.com/ora-io/opml).
- **PrimeIntellect-ai/protocol**, last commit 2025-11-09 ("adjust readme"), apparently stale. Earlier sources describe Base Sepolia contracts and a RewardsDistributor paying by active time. I found no slashing documented — [GitHub](https://github.com/PrimeIntellect-ai/protocol); [Gate explainer](https://www.gate.com/learn/articles/open-ai-founding-members-invest-a-quick-dive-into-the-decentralized-ai-breakthrough-prime-intellect/7323).
- **PsycheFoundation/psyche** (Nous), default-branch last commit 2026-03-20 — [GitHub](https://github.com/PsycheFoundation/psyche). A review updated 2026-10-27 says coordination is on Solana *devnet*, none of the four program IDs existed on mainnet, and the programs record attestations rather than run consensus — [ownyourmind](https://ownyourmind.ai/projects/nous-research/). Uncertain: development may have moved to another branch or repo.
- **one-covenant/crusades** (Templar successor competition), last commit 2026-04-05 ("exploit detection, TUI fixes…") — [GitHub](https://github.com/one-covenant/crusades).
- **Gensyn OPEN-1B**: the paper says code and the audit harness were released, and HF hosts base/mid/SFT checkpoints. No `gensyn-ai/open-1b`, `repops` or `verde-repops` repo was clonable under those names — [arXiv](https://arxiv.org/abs/2609.17380); [search summary](https://runtimewire.com/article/gensyn-open-1b-auditable-ai-model-training).
- I found no public Ofelimos implementation (ePrint 2021/1379 / 2025/2091 are paper-only as far as the search showed) — [ePrint 2025/2091](https://eprint.iacr.org/2025/2091).

### Inferences
- PoLChain is the item most likely to look like prior art to a reviewer or the public for a Base Sepolia "train-to-mine" demo. It is worth citing and differentiating from: we have training-effort verification, disputes and lineage; it has inference-only ZK scoring at MNIST scale.
- OPEN-1B's audit harness, if licensed permissively, could become our referee's replay engine. Its licence and repo still need checking.

### Gaps
- I did not check Ritual, Cartesi ML, Truebit, EigenLayer ML AVSs or 0G/Nesa repos (GitHub API blocked; time budget). The earlier report covered EigenLayer slashing.
- Repo licences and contributor counts are unverified.

## Q4. Well-funded companies building the exact combination

### Takeaway
No funded company publicly ships V+C+S+L+L2 for training as of 2026-11-05:
- Gensyn is closest on verification (Verde, REE, OPEN-1B), but its training network is paused and it monetises Delphi.
- Covenant/Templar has the best validator-scored training (Gauntlet, Covenant-72B) but no disputes, and left Bittensor in April 2026.
- Nous Psyche is still on devnet with attestations only.
- Pluralis is research-stage (protocol models, SENTINEL).
- Prime Intellect's on-chain protocol looks stale while its RL tooling thrives.
- Pearl is live but does matmul PoUW, not training.

### Cited Findings
- **Gensyn.** OP-Stack L2 and $AI token launched April 2026; the training network is paused (earlier report). OPEN-1B (2026-09-15) is its newest verification artefact, self-described as the "industry's first auditable AI model" — [runtimewire](https://runtimewire.com/article/gensyn-open-1b-auditable-ai-model-training).
- **Covenant AI (Templar SN3).** It exited Bittensor around 2026-04-09/10, citing governance concentration. It allegedly sold ~37,000 TAO of alpha, and other sources say ~$10M, so the figures conflict. Covenant-72B was completed March 2026. Steeves *alleges* Covenant is raising for its own venture, which is unconfirmed — [FalconX](https://www.falconx.io/newsroom/state-of-bittensor-subnet-adoption-trends-network-mechanics-and-covenants-departure); [ownyourmind](https://ownyourmind.ai/tokenomics/templar-bittensor-covenant-exit/); [tao.media](https://www.tao.media/covenant-ais-bittensor-exit-what-happened-how-bittensor-responded-and-whats-next-for-the-network/). I found no Covenant chain announcement.
- **Nous Research / Psyche.** Devnet only, semi-permissioned; reported $155M total after an October 2026 Series B — [ownyourmind (updated 2026-10-27)](https://ownyourmind.ai/projects/nous-research/); [Nous Psyche page](https://nousresearch.com/nous-psyche).
- **Pluralis.** $7.6M seed (USV, CoinFund) in March 2025 and a Protocol Learning workshop in April 2026. Its output is research (UPMs at NeurIPS 2025, SENTINEL in March 2026), and it is moving from an 8B run toward larger scale — [GlobeNewswire](https://www.globenewswire.com/news-release/2025/03/19/3045635/0/en/pluralis-research-pioneers-protocol-learning-to-scale-decentralized-ai-announces-7-6m-seed-round-led-by-usv-and-coinfund.html); [Pluralis workshop](https://pluralis.ai/events/protocol-learning-workshop/); [arXiv 2605.23464](https://arxiv.org/abs/2605.23464).
- **Prime Intellect.** TOPLOC verification and Base Sepolia contracts; no 2026 sources on protocol launch or slashing found — [arXiv 2505.07291](https://arxiv.org/pdf/2505.07291); [protocol repo](https://github.com/PrimeIntellect-ai/protocol).
- **Pearl Research Labs.** Mainnet 2026-04-27, active repo, matmul PoUW. Empirically criticised as yielding zero useful compute — [arXiv 2606.04819](https://arxiv.org/abs/2606.04819).
- **0G.** A blog argues verification is necessary for decentralised training (no product details checked) — [0G blog](https://0g.ai/blog/why-verification-matters-decentralized-ai-training).

### Inferences
- The most plausible fast follower is **Gensyn**. It already has Verde (refereed delegation with bisection), REE/OPEN-1B (cross-hardware replay) and an L2, so it could assemble the same stack. That is a scoop risk on the *verification-dispute* component, not on lineage royalties or the D-PoDL hash binding. Covenant raising for an independent venture is the second risk on validator-scored training, and it is unconfirmed.

### Gaps
- I did not verify Ambient, Macrocosmos, Nesa or 0G 2026 roadmaps beyond the earlier report.
- There are no primary-source Gensyn 2026 roadmap statements about resuming training.

## Q5. Bottom line: what novelty remains publishable (as of 2026-11-05)

### Takeaway
The open, publishable contribution is an **end-to-end, open-source, formally argued useful-work *training* market** built from these parts:
- D-PoDL's chain-bound pre-hash/post-hash binding repurposed as anti-precomputation for task seeds and shards;
- commit-reveal submissions;
- validator re-measurement;
- an optimistic stake/challenge game that bisects to one training step, refereed by bitwise replay (citing Srivastava 2024 and OPEN-1B 2026);
- lineage royalties with a dispute-proof attribution rule;
- L2 settlement;
- a stated security game against rational/agent miners that answers the PoUW SoK and the Pearl "usefulness gap" critique.

No single item found combines these. The pieces are individually citable, so the paper's novelty must be integration, the security argument and adversarial evaluation.

### Cited Findings
- A 2026 paper calls a formal security game for ML-work consensus "an open research problem" (earlier report; [arXiv 2606.24942](https://arxiv.org/abs/2606.24942)).
- Attribution at scale for royalties is "an open research challenge" — [Content ARCs, arXiv 2503.14519](https://arxiv.org/pdf/2503.14519).
- The first deployed PoUW-for-AI L1 does no useful work because verification checks hardness, not utility — [arXiv 2606.04819](https://arxiv.org/abs/2606.04819).
- Cross-hardware step replay now exists at 1B scale, but with several-fold GEMM slowdown and incomplete community audit coverage — [arXiv 2609.17380](https://arxiv.org/abs/2609.17380); [pebblous](https://blog.pebblous.ai/blog/open-1b-auditable-training-run/en/).
- Incentive mechanisms without an honest majority exist only off-chain and without verification infrastructure — [VISTA](https://arxiv.org/abs/2605.07841); [Chen & Wang](https://arxiv.org/abs/2603.27962).

### Inferences
Candidate novelty claims, ranked by defensibility (my judgement):
1. **Lineage royalties with dispute-proof attribution.** A diff/adapter DAG where royalties flow only through validator-re-measured marginal improvements, and attribution can be challenged on chain. No prior item does this with adversarial verification; MAGNET only logs contributions.
2. **Formal security game for training-as-useful-work under rational/agent miners.** This would combine D-PoDL's ledger proofs with incentive-security (Zhao et al.) and a Seddik-style spot-check bound, and explicitly answer SoK 2025/1814 and Pass 2026.
3. **First open end-to-end reference implementation** with a full threat model (grinding, reuse, PoL spoofing, plagiarism, publisher collusion) and red-team results. PoLChain is the only comparable public code and is MNIST/inference-only.
4. **Optimistic bisection-to-step on an L2 with replay referee.** This is the weakest claim, because it is mostly Verde + OPEN-1B + opML engineering. It is still publishable as a systems/measurement paper if it reports gas, latency and replay-tolerance numbers.

Scoop-risk summary:

| Actor | What they hold or might announce | Risk |
|---|---|---|
| Gensyn | The dispute layer, using Verde and OPEN-1B | Medium |
| Covenant | Validator-scored training on its own chain (unconfirmed) | Low-Medium |
| BagChain / SEDULity group | Another consensus-theory paper | Low on our combination |
| Original D-PoDL authors | — | Low |

### Gaps
- Unreleased in-review submissions (FC 2027, AFT, CCS 2026 cycle 2) cannot be seen. Re-check IACR ePrint and arXiv cs.CR monthly.
- I did not verify OPEN-1B's audit harness licence or repo, nor whether Gensyn plans on-chain settlement of OPEN-1B audits.
