# Closest overlaps, verified from primary sources (as of 2026-11-05)

Scope: this note checks, against primary sources, seven projects that might pre-empt our design. Our design is an open, threat-modelled protocol for validator-verified useful-work ML research, settled on an Ethereum L2. It has a frozen multi-seed verifier, commit-reveal, stake, a challenge window with bisection, slashing, and recursive lineage royalties paid along causal ancestry.

Method:
- About 20 search and fetch calls were run on 2026-11-05.
- "[P]" marks a primary source: the project's own repo, site, docs or paper. "[S]" marks a secondary source.
- The GitHub REST API was blocked in this session (HTTP 403). Repo facts therefore come from the rendered GitHub pages and raw files, so exact last-commit dates are mostly unavailable.
- Overlap % is my own estimate [est], scored against the design's eight components:
  1. validator re-measurement
  2. frozen multi-seed statistical acceptance
  3. commit-reveal
  4. stake
  5. challenge window or bisection
  6. slashing
  7. lineage royalties
  8. open L2 settlement and open threat model

**Bottom line: we are not scooped.** No project combines L2 settlement, stake, challenge with bisection, slashing, and recursive causal lineage royalties. The closest live market is **Refinery SN125**, at about 55%; it is close to our "verifiable autoresearch" market minus the dispute and economic layer. The closest paper designs are **MAGNET**, at about 40% (it has bonds, slashing and notary disputes, but no lineage and no code), and **PoIm**, at about 30% (a toy). **PoLChain** is the only one running on an Ethereum L2, but it is an MNIST testnet toy with no stake and no disputes.

---

## Q1. Bittensor SN125 "Refinery"

### Takeaway
Refinery is live and is the nearest existing version of our flagship market. It pays for optimizer code, and since October 2026 for "refiner" data-selection programs. Validators re-run each submission on a frozen model, dataset and compute budget, with commit-reveal, a confirmation run and a cumulative frontier. It has no stake, no slashing, no dispute or bisection game, and no ancestor royalties; its credit decays over time. Overlap is about 55% [est].

### Cited Findings
- [P, repo checked 2026-11-05] Refinery describes itself as "an incentivized research network for improving the algorithms behind language-model training." Miners submit Python optimizer code against a supplied interface. Challenge 2 adds a "refiner", a program plus optional weight file that selects what the student trains on. — [github.com/Barbariandev/Refinery](https://github.com/Barbariandev/Refinery)
- [P] The frozen setup:
  - Model: a Llama-style model of about 360M parameters.
  - Data: manifest-pinned FineWeb-Edu with the SmolLM2 tokenizer.
  - Shape: sequence length 2,048, batch size 32.
  - Compute: one B200, capped at 20 hours or 188,000 steps.
  - Objective: lower validation loss from clean checkpoint scoring.
  - Source: [Refinery repo](https://github.com/Barbariandev/Refinery)
- [P] Acceptance rules:
  - A candidate must beat the current frontier by more than an **adaptive bar with a 0.03-nat floor**; Challenge 2 uses a floor of 0.02 suite points.
  - A **second confirmation run** must also qualify.
  - The confirmed frontier is set from the **worse loss of the two runs**.
  - No seed count or formal statistical test is stated.
  - Source: [Refinery repo](https://github.com/Barbariandev/Refinery)
- [P] Anti-copy relies on **commit-reveal of a source hash**, sandboxing (`gate.py`, `sandbox.py`, `seccomp_sandbox.py`) and attribution scripts (`verify.py`, `prove_authorship.py`). — [Refinery repo](https://github.com/Barbariandev/Refinery)
- [P] Payout rules:
  - Confirmed improvements earn credit proportional to their size, which **decays with a 14-day half-life**.
  - Recent network progress decides how much emission is paid versus burned. The launch burn floor is 0%.
  - Weights split 50/50 between the optimizer and refiner pools, and each pool burns its unearned share.
  - Miners pay evaluation fees in TAO to a treasury, priced at the estimated GPU rental cost plus 10% (reference price $250/TAO).
  - The repo describes no slashing and no dispute process.
  - Source: [Refinery repo](https://github.com/Barbariandev/Refinery)
- [P] Status:
  - The site says Refinery is "live on Bittensor subnet 125."
  - Challenge 1 (optimizer) has run since September 2026, and Challenge 2 (refiner) since October 2026.
  - "The winner becomes the baseline for the next challenger."
  - Confirmed entries beat AdamW on held-out perplexity, but no figures are given.
  - LLM research agents are explicitly invited, and the repo ships a `MINING_AGENTS.MD`.
  - Source: [refinery125.com](https://refinery125.com/); [repo](https://github.com/Barbariandev/Refinery)
- [P] Repo stats: 15 commits on main, 2 stars, no releases, and no license shown on the page. The README also says "this source release is not proof of an active deployment." — [Refinery repo](https://github.com/Barbariandev/Refinery)
- Correction to earlier notes: "data refiners" (from the doctensor directory) means Challenge 2's data-selection programs, not a separate miner role. — [refinery125.com](https://refinery125.com/)

### Inferences
- Refinery already has "frozen recipe, agent-submitted diffs, re-run by validators, cumulative frontier." It occupies the market concept we planned to pitch as novel, so our novelty claim must move to the **settlement, dispute and lineage layer** and to the **open, chain-agnostic threat model**.
- Its credit is proportional to improvement with recency decay; it is not a causal-ancestry royalty. A record built on a previous frontier optimizer pays nothing to that optimizer's author.
- Two runs taking the worse loss is weaker than a k-seed, α-calibrated spec. Our "published acceptance spec with a measured noise floor" remains a contribution.

### Gaps
- No license, emission size, miner count or numeric results were found. The Mechanism, Verify and Dashboard pages and `MINING_AGENTS.MD` were not fetched.

---

## Q2. Bittensor SN66 "Conjectures.io"

### Takeaway
SN66 is live. It pays first-accepted-answer bounties for Lean-kernel-checked proofs or counterexamples of DeepMind formal-conjectures statements, with a human review step. It also runs Lean-proven-equivalent code-speed competitions, such as TorchLean kernels. It overlaps strongly with our Lean option and weakly with the ML-training flagship. It has no stake, no slashing, no disputes, no commit-reveal stated and no recursive lineage. Overlap is about 30% [est] with our overall design and about 60% with a "Lean bounty" side track.

### Cited Findings
- [P, site checked 2026-11-05] Problems are exact Lean statements; the site says the solver is "Paid when Lean accepts the proof". A solver may prove or refute, and **one reward is paid per problem**. The pipeline is "Lean kernel check, then human review, then payment", paid in alpha. Checking a file is free, and submitting costs one credit and must include the AI chat logs. — [conjectures.io](https://conjectures.io)
- [P] Results listed on the site:

  | Date | Result | Reward | Solver |
  |---|---|---|---|
  | 2026-10-28 | Erdős Critical Minimum Degree | $970 | EthanYang |
  | 2026-10-28 | Fourth planar Dirichlet Pólya inequality | $2,230 | Jordan |
  | 2026-10-14 | Wilf inequality for proper numerical semigroups | $1,907 | Elias |
  | 2026-10-14 | Six-speed bound | $1,789 | Elias |

  - Open bounties shown at the time were about $5,523 each, and the site reports $95,769 paid to solvers in total.
  - Source: [conjectures.io](https://conjectures.io)
- [S, subnetalpha, "data may be out of date"] Further mechanism details:
  - Bounty schedule: a new problem's bounty starts at 2.5% of the pool and rises to 12.5% over 15 days, and it locks when a proof is submitted.
  - **Partial work such as lemmas can earn a share.**
  - Mining opened 2026-08-05.
  - The catalogue holds 290 problems from Google DeepMind's Formal Conjectures, each audited as still open.
  - One credit costs 0.25 TAO. An earlier search snippet said 0.5 TAO, so this conflicts and is probably stale.
  - SN66 previously ran as "Ninja", an agent subnet, under the same owner.
  - Source: [Subnet Alpha: Conjectures](https://subnetalpha.ai/subnet/conjectures/)
- [P] Optimisation competitions:
  - DEFLATE (ended): 648 proved parsers accepted, the best 29× faster than zopfli.
  - Float kernels (ended): 8.7× faster, with 38 champions.
  - TorchLean kernels (live): twelve kernels across five neural networks, raced on six boards.
  - Each submission must carry a Lean proof of equivalence to the spec.
  - Source: [conjectures.io](https://conjectures.io)
- [P/S] The code lives in the GitHub org `conjectures-io`, which holds the validator, miner CLI, task pool, contributions track and competition repos. No license was found. The site mentions no staking, disputes or commit-reveal. — [conjectures.io](https://conjectures.io); [Subnet Alpha](https://subnetalpha.ai/subnet/conjectures/)

### Inferences
- With a deterministic verifier and a first-accepted-answer rule, SN66 needs no dispute game, which is why it has none. For the Lean track, the incumbent already works, so we have little to add beyond L2 settlement and lemma-level lineage. The "partial credit for lemmas" rule is a primitive, non-recursive form of lineage.
- The Lean-proved kernel competitions overlap our possible kernel track.

### Gaps
- No primary source was found for front-running protection; it is unclear how a revealed proof is protected before payout. No license or emission data was found.

---

## Q3. "Proof of Improvement" L2 paper (AFT 2025, arXiv 2510.16024)

### Takeaway
The paper is "On-Chain Decentralized Learning and Cost-Effective Inference for DeFi Attack Mitigation" by Alhaidari, Palanisamy and Krishnamurthy (University of Pittsburgh), posted to arXiv on 2025-10-15 and published at AFT 2025. PoIm is a narrow, toy-scale scheme:
- updates are single-sample micro-steps
- a small classifier is evaluated on a DAO-curated test set
- an update is accepted if it improves at least one of accuracy, precision, recall or F1 without degrading the others
- the reward is the returned stake plus a weighted metric gain
- stake is lost on failure, and there is a rollback vote

It has no lineage, no bisection, no multi-seed noise handling, no agents and no released code, and was evaluated only on local Hardhat/Anvil forks. Overlap is about 30% [est]. This is citable prior art for "proof of improvement on an L2", not a scoop.

### Cited Findings
- [P, arXiv full text read 2026-11-05] Training and governance run on L2 (an Optimism example), and inference runs on L1. The authors describe PoIm as follows: "governs the training process and verifies each decentralized micro update as a self-verifying training transaction." — [arXiv 2510.16024](https://arxiv.org/html/2510.16024)
- [P] Acceptance and economics:
  - An update is accepted if it improves at least one of accuracy, precision, recall or F1 without degrading the others, measured on a canonical test set 𝒟test.
  - Stakers govern the test set through a DAO vote.
  - Reward: R = s + Σ αk(Mk′ − Mk). The αk weights are unspecified.
  - A failed proposal loses its stake.
  - Peers can vote to roll back within a window of under 7 days.
  - The notation table lists a challenge window Δt of about 1 day.
  - Algorithm 2 is `proposeModelUpdate(Θfixed(new), stake s)`, with no stake amounts given.
  - Source: [arXiv 2510.16024](https://arxiv.org/html/2510.16024)
- [P] L2 to L1 propagation uses commit-verify: a keccak256 hash of the parameters goes over the bridge, the full parameters follow, and L1 recomputes the hash. Table 1 calls this "commit-reveal". Weights are fixed-point scaled (10⁶ to 10¹⁸), and Z3 proves that on-chain and off-chain outputs agree. — [arXiv 2510.16024](https://arxiv.org/html/2510.16024)
- [P] Evaluation:
  - Data: 298 real exploits (2020 to April 2025) across 8 EVM chains, about $3.74B in losses.
  - Models: LR, SVM, decision tree, MLP, 15 CNN variants and RNNs, all using 7 features.
  - Best CNN: accuracy 0.9004 and F1 0.82. The abstract claims ">97%", which the body does not support.
  - L1 inference gas runs from 57.6k (linear models) to 506k (CNN).
  - L2-to-L1 updates cost from about 96k to more than 22M gas.
  - Stress test: label-flip or noise poisoning at 50% of training size.
  - Environment: Hardhat fork of Optimism plus Anvil only, with no live deployment.
  - Source: [arXiv 2510.16024](https://arxiv.org/html/2510.16024)
- [P] Absent from the paper: no lineage or royalty, no bisection, and no code repository or artifact link. The authors list as future work the local-optimum problem (they suggest simulated annealing), front-running, backdoors, and governance capture through voting tokens. — [arXiv 2510.16024](https://arxiv.org/html/2510.16024)
- [S] The AFT 2025 venue is confirmed by search metadata. — [arXiv abs](https://arxiv.org/abs/2510.16024)

### Inferences
- The overlap is in the vocabulary ("proof of improvement", L2, stake, rollback window), not in the mechanism. PoIm's deterministic, single-sample, small-model setting avoids every hard problem we target: stochastic training noise, multi-seed acceptance, fraud proofs and lineage. We should cite it and position against it.

### Gaps
- The LIPIcs camera-ready version was not compared with arXiv v1.

---

## Q4. MAGNET (arXiv 2603.25813, Holo Studio, 2026-03-26)

### Takeaway
On paper, MAGNET is the most complete combination of autoresearch and crypto-economics. Its on-chain module provides commit-reveal, bonds, slashing scaled by severity, notary-quorum disputes with challenge windows, and epoch reward pools weighted by contribution. It has **no lineage or ancestor rewards**, verifies by evaluator consensus and notaries rather than by re-execution or bisection, runs on its own HOOTi (Cosmos-SDK EVM) chain, and **its code has not been released**. Overlap is about 40% [est]. This is design-level prior art, not a working competitor.

### Cited Findings
- [P, arXiv full text read 2026-11-05] MAGNET has four components:
  - an autoresearch loop: error analysis, strategy design, config sweeps, evaluation, and stop-on-plateau
  - BitNet b1.58 ternary models
  - DiLoCo merging, with outer-update weights based on on-chain metrics; this is designed but "not experimentally validated" at scale
  - an on-chain Cosmos SDK module on the HOOTi EVM chain
  - Source: [arXiv 2603.25813](https://arxiv.org/html/2603.25813)
- [P] Verification works per contribution type:
  - Data: held-out loss improvement.
  - Compute: steps × model size, checked by checkpoint hash.
  - Model quality: benchmark scores by **evaluator consensus**.
  - Commit-reveal uses a hash of the result plus a nonce, and a mismatched reveal is slashed.
  - Data records go through a **challenge window in which notaries check them**.
  - Source: [arXiv 2603.25813](https://arxiv.org/html/2603.25813)
- [P] Economics:
  - A fixed pool is paid per 10-minute epoch, in proportion to tier multiplier × verified score. The tiers are: claude_session 3.0×, gpu_compute 1.0×, storage/cpu 0.3×, mobile 0.1×.
  - Annual emission is capped.
  - Every node posts a bond, and notaries must post a minimum bond.
  - Slashing runs from 0.1 to 1.0 by severity.
  - Disputes go to a "bootstrap notary quorum".
  - The paper argues incentive compatibility as bond loss plus forfeited rewards exceeding the attack gain.
  - **Lineage or ancestor reward propagation is not addressed.**
  - Source: [arXiv 2603.25813](https://arxiv.org/html/2603.25813)
- [P] Status:
  - The on-chain module is "implemented and unit-tested" and "not deployed on a public mainnet"; a test-chain deployment is mentioned.
  - The repo `github.com/holostudio/magnet-core` is "forthcoming", and the license is not finalized.
  - The planned split keeps the research core open and runs the platform layer on HOOTi.
  - Source: [arXiv 2603.25813](https://arxiv.org/html/2603.25813)
- [P] Evaluation used internal data:
  - Zevor video-safety: balanced accuracy 0.9287 → 0.9851. The paper gives inconsistent false-negative counts (9→0 vs 11→0).
  - StockClaw: hit rate 41.0% → 54.9%.
  - BitNet hyperparameter search: validation loss −16.7%.
  - Genkidama: a 618M model pretrained on 3.8B tokens.
  - None of these tests the on-chain incentive layer adversarially.
  - Source: [arXiv 2603.25813](https://arxiv.org/html/2603.25813)

### Inferences
- MAGNET pre-empts "stake + commit-reveal + slashing + disputes for autoresearch contributions" at the level of a written design. It does not pre-empt causal lineage royalties, re-execution or bisection fraud proofs, a frozen multi-seed acceptance spec, or settlement on a public Ethereum L2. Its notary-quorum adjudication is a trusted committee, which is the weakness our bisection game removes.

### Gaps
- Whether `holostudio/magnet-core` exists yet could not be checked, because the GitHub API was blocked. Treat it as unreleased as of the paper (2026-03).

---

## Q5. PoLChain (github.com/jacksongeiger/polchain)

### Takeaway
PoLChain is a hobby-scale "proof-of-learning" chain **live on Base Sepolia, an Ethereum L2 testnet**. Miners prove MNIST inference quality on a sealed held-out batch with Halo2/EZKL zk proofs. The reward is proportional to improvement over the current merged baseline. Paid models are FedAvg-merged into the next block's base. It has no stake, no slashing and no disputes, and the merged base is not paired with any ancestor royalty. MIT license, 0 stars. Overlap is about 25% [est].

### Cited Findings
- [P, README checked 2026-11-05] How a block works:
  - A poster escrows 100 POL per block.
  - The challenge is one of 250 sealed batches of 8 MNIST digits, chosen by the parent block hash.
  - The baseline model is proven on the same verifier.
  - Each miner submits a Halo2 (EZKL) proof of a forward pass; proving takes about 31 s on a laptop and on-chain verification about 1.5M gas.
  - The contract computes the score from the public logits, so there is no self-reported score.
  - Nullifiers block replay.
  - Source: [polchain README](https://github.com/jacksongeiger/polchain)
- [P] Reward: `reward_i = pool × max(0, score_i − base) / Σ_j max(0, score_j − base)`. Paid weights are FedAvg-merged, gated on a 2,000-image test set, and the merge becomes the next base. — [polchain README](https://github.com/jacksongeiger/polchain)
- [P] Contracts: `TaskManagerV3` (ownerless after `seal()`, with `postTask`/`postFiltered`/`establishBase`/`submitWithProof`), `DifficultyPoster`, the `POLToken` ERC-20, and a Halo2 verifier. — [polchain README](https://github.com/jacksongeiger/polchain)
- [P] Self-stated limits:
  - A proof attests to inference quality, not training effort.
  - The 250-batch pool can be precomputed.
  - The poster chooses batches.
  - Era 1 (595 blocks) relied on self-reported scores.
  - Source: [polchain README](https://github.com/jacksongeiger/polchain)
- [P] Status:
  - Recorded run on 2026-09-08: blocks #159 to #173, accuracy 8.55% → 96.65%.
  - Repo: 46 commits, 0 stars, 0 forks, MIT license; "paper in preparation".
  - No stake, slashing or disputes are described.
  - Source: [polchain README](https://github.com/jacksongeiger/polchain)

### Inferences
- PoLChain is a useful existence proof for "improvement-proportional payout on an Ethereum L2", and for zk-scored inference on tiny models, which does not scale to LLM training. It is not a threat. Its "pool precomputable" admission is a known weakness to cite in our threat model.

### Gaps
- The last-commit date is unavailable because the GitHub API was blocked.

---

## Q6. Gradients SN56 rules and Teutonic SN3: lineage payout and anti-copy

### Takeaway
Both are now confirmed from primary sources, and **neither pays causal-lineage royalties**.
- **Gradients** pays only current-tournament ranks (about 76/19/5) plus a non-decaying champion weight. It uses a three-tier duplicate check that ends in an LLM (Claude) pairwise review, burns its fees, and is Apache-2.0.
- **Teutonic** pays the current king plus up to 4 previous kings at 20% each. Its primary sources describe no anti-copy mechanism beyond immutable checkpoints and block-hash eval sampling, and no license file was found.

### Cited Findings
- [P, docs/miner.md checked 2026-11-05] Gradients boss round:
  - Text has 6 tasks: 3 instruct (one at 30B to 72B), 1 DPO, 1 GRPO and 1 continuous-SFT "per lineage".
  - The challenger must win at least 55% of decided samples **and** beat the boss's mean loss by max(0.01, 1%). Both tests use the lower bound of a one-sided 99% bootstrap over 10,000 resamples.
  - Samples within 0.01 nats are a dead zone, and an all-dead-zone task is a draw that the defender keeps.
  - To dethrone, a text challenger must win at least 5 of 6 tasks, including every continuous-SFT task.
  - Source: [G.O.D docs/miner.md](https://raw.githubusercontent.com/rayonlabs/G.O.D/main/docs/miner.md)
- [P] Gradients rewards:
  - Up to 3 ranks are paid with exponential decay (base 0.25), about 76/19/5, or 80/20 without a valid third place.
  - Each participant gets 0.0001 weight.
  - Champions above a 0.10 threshold get a 2× boost on the excess.
  - "A champion's weight does not decay over time."
  - The docs describe no payout to earlier champions or to code a winner built on.
  - Source: [G.O.D docs/miner.md](https://raw.githubusercontent.com/rayonlabs/G.O.D/main/docs/miner.md)
- [P] Gradients anti-copy:
  - T0: identical commit. T1: identical source after normalization. T2: "a Claude pairwise review of code deltas". Renames, reformatting and "noise hyperparameters" count as duplicates, and "Confirmed duplicates are eliminated."
  - Winning repos are re-uploaded to github.com/gradients-opensource.
  - Fees are 0.7 TAO (text) and 0.4 TAO (image), burned, with one entry per coldkey.
  - Tournaments run on Mondays.
  - Source: [G.O.D docs/miner.md](https://raw.githubusercontent.com/rayonlabs/G.O.D/main/docs/miner.md); [G.O.D repo](https://github.com/rayonlabs/G.O.D)
- [P] Gradients repo: Apache-2.0 (LICENSE.md), 1,152 commits. The gradients.io rules page is behind a sign-in. — [G.O.D repo](https://github.com/rayonlabs/G.O.D); [gradients.io/rules](https://gradients.io/rules)
- [P, blog "Published Aug 2026"] Teutonic gives weights to "the current king and up to four previous kings, provided that their hotkeys remain registered". The shares are an equal 20% each and are renormalized if a former king leaves. The blog mentions "various attempts to copy models" but describes no counter-measure. — [blog.teutonic.ai](https://blog.teutonic.ai/)
- [P, repo checked 2026-11-05] Teutonic repo:
  - Immutable checkpoints, paired cross-entropy scoring on a remote GPU evaluator, and token-weighted bootstrap LCB acceptance for MIX competitions.
  - One ready submission per hotkey, Ed25519 hotkeys, and encrypted, prefix-scoped upload credentials.
  - No hashing, commit-reveal or similarity check is described.
  - 314 commits and 12 stars.
  - No license is shown, and `LICENSE` returns 404 on main.
  - Source: [github.com/unarbos/teutonic](https://github.com/unarbos/teutonic); [raw LICENSE 404](https://raw.githubusercontent.com/unarbos/teutonic/main/LICENSE)

### Inferences
- Teutonic's 5-king flat window, Refinery's 14-day decaying credit and Conjectures' lemma shares are the only live "lineage-ish" payouts. All three pay by recency or by a one-hop share, never along a causal DAG.
- Gradients' LLM-judge duplicate review is a practical anti-copy precedent we can adopt, though it is not adversarially robust.
- Without a license, Teutonic's code is all-rights-reserved by default, so it should not be forked.

### Gaps
- The meaning of Gradients' "per lineage" in the continuous-SFT task was not resolved; it probably refers to a model family, not contributor lineage. Teutonic-II's reward split is not confirmed.

---

## Q7. Sweep for 2026 items the earlier notes missed

### Takeaway
No 2026 paper or project titled "verifiable autoresearch", "lineage royalties" or "proof of improvement" combined with blockchain turned up beyond the items above. The adjacent hits are verification components, not competing protocols.

### Cited Findings
- No results were found for the exact phrases "verifiable autoresearch" or "lineage royalties", or for autoresearch with on-chain bounties on `train.py`. — searches 2026-11-05 ([search hit list incl. OVIG](https://arxiv.org/abs/2606.21045))
- OVIG (arXiv 2606.21045, 2026-06): optimistic verification of training integrity from gradient signals, reporting 0% attack success. It is already covered in earlier notes and is a component, not a market. — [arXiv 2606.21045](https://arxiv.org/abs/2606.21045)
- TAO: Tolerance-Aware Optimistic Verification for Floating-Point Neural Networks (arXiv 2510.16028, 2025-10). Only reference-list text was seen, so its contents are unverified. It is likely relevant to our floating-point bisection design. — [arXiv 2510.16028](https://arxiv.org/pdf/2510.16028)
- Optimistic TEE-Rollups (arXiv 2512.20176) covers verifiable generative-AI *inference* on-chain and is off-scope for training. — [arXiv 2512.20176](https://arxiv.org/pdf/2512.20176)
- AutoBounty: AI agents verify GitHub contributions and release escrow on Avalanche through GenLayer consensus. It is generic code bounties with no ML metric. — [auto-bounty.vercel.app](https://auto-bounty.vercel.app/)

### Inferences
- The "lineage royalties" and "verifiable autoresearch" labels are unclaimed as of 2026-11-05. The overlap table, with overlap % as [est]:

  | Project | Status (2026-11-05) | Overlap | Has | Missing vs ours |
  |---|---|---|---|---|
  | Refinery SN125 | live since 2026-09 | ~55% | frozen budget, re-run, commit-reveal, 2-run confirm, frontier | stake, slash, challenge or bisection, causal lineage, L2, multi-seed spec |
  | Gradients SN56 | live, weekly | ~45% | repo re-run, 99% bootstrap, LLM dedup, burn | stake, slash, disputes, lineage |
  | Teutonic SN3 | live (Teutonic-II) | ~45% for the model-delta track | bootstrap LCB, 5-king window | anti-copy, stake, slash, disputes, causal lineage, license |
  | MAGNET | paper, code unreleased | ~40% | commit-reveal, bonds, slashing, notary disputes | lineage, re-execution or bisection, public L2, code |
  | Conjectures SN66 | live since 2026-08-05 | ~30% (60% for a Lean track) | deterministic Lean check, bounties, lemma shares | stake, disputes, recursive lineage, ML training |
  | PoIm (AFT'25) | paper, simulation only | ~30% | L2, stake loss, rollback window, improvement reward | lineage, bisection, noise handling, code |
  | PoLChain | Base Sepolia testnet | ~25% | Ethereum L2, improvement-proportional pay, zk scoring | stake, slash, disputes, lineage, scale |

- Decision: **not scooped**. The defensible novel core is:
  1. recursive causal-lineage royalties
  2. a bisection fraud-proof game over stochastic training under a frozen multi-seed, hash-committed acceptance spec
  3. permissionless Ethereum L2 settlement with stake and slashing
  4. a published threat model comparing Refinery, Gradients, Teutonic, MAGNET and PoIm
- The main competitive risk is Refinery adding stake or lineage; nothing announced suggests it will.

### Gaps
- The sweep covered only about 3 queries. Model-provenance or attribution-royalty work, such as data-attribution markets, was not searched.
