# Infrastructure and Developer Tooling for Reviving D-PoDL (state as of 2026-11-05)

Scope note: research done 2026-11-05 through web search and fetch. Many 2026 web results are SEO-style or aggregator blogs, so primary sources (official blogs, docs, pricing pages) are marked **[primary]**. Figures from secondary sources are marked **[secondary]** and should be treated as indicative. When sources conflict, both are listed.

---

## 1. Chain choice in 2026 (L2s, app-rollups, Solana, appchains, Bittensor), testnets, gas costs, Ethereum upgrades

### Takeaway
For a small team with existing Solidity contracts, the cheapest low-risk path is to deploy on an existing EVM L2 (Base or Arbitrum One, with Arbitrum Stylus as an option for Rust/WASM verification hot paths) and test on Sepolia plus the L2's Sepolia testnets. Fusaka (live 2025-12-03) and the later BPO blob increases pushed L2 fees down to cents or fractions of a cent. Polygon Mumbai and Ethereum Holesky are both dead: use Amoy only if Polygon PoS is a hard requirement. Running a dedicated app-rollup (OP Stack, Orbit, or a RaaS provider) or a Bittensor subnet only makes sense after product-market fit. A subnet also needs a large upfront TAO burn.

### Cited Findings

**Ethereum upgrades relevant to the project**
- **Pectra** activated on mainnet 2025-05-07 10:05 UTC (epoch 364032) **[primary]**. It brought:
  - **EIP-7702**, which lets an EOA run smart-contract code through a new transaction type. This enables batching, gasless (sponsored) transactions and alternative recovery. Useful for onboarding GPU contributors who hold no ETH.
  - **EIP-7691**, which raised the blob target/max from 3/6 to 6/9.
  - **EIP-2537**, a BLS12-381 precompile. Cheap BLS signature verification makes aggregate attestations from many validators or evaluators feasible.
  - **EIP-7623**, which raises calldata cost only for data-heavy transactions (">99% of txs unaffected").
  — [ethereum.org Pectra](https://ethereum.org/roadmap/pectra/)
- **Fusaka** went live on mainnet 2025-12-03, with **PeerDAS** (nodes sample blob data instead of downloading all of it). Blob parameters then rose through Blob-Parameter-Only (BPO) forks:
  - BPO1 on 2025-12-09: target 10 / max 15
  - BPO2 on 2026-01-07: target 14 / max 21
  — [DL News](https://www.dlnews.com/articles/defi/ethereum-fusaka-brings-eightfold-increase-in-blob-capacity/); [EIPsInsight](https://eipsinsight.com/upgrade) **[secondary]**
- **Glamsterdam** is the next fork: Gloas (consensus layer) plus Amsterdam (execution layer). Headline features are enshrined PBS (EIP-7732) and block-level access lists (EIP-7928) — [Everstake](https://everstake.com/resources/blog/ethereum-glamsterdam-upgrade-explained); [Chainstack](https://chainstack.com/ethereum-glamsterdam-upgrade/).
  - Testnet schedule from the EF blog **[primary]**: Sepolia activation 2026-10-06; Hoodi 2026-10-26 17:42:48 UTC. **Mainnet date still TBD** as of the 2026-10-16 post — [EF Glamsterdam testnet announcement 2026-09-17](https://blog.ethereum.org/2026/09/17/glamsterdam-testnet-announcement); [EF Glamsterdam Hoodi announcement 2026-10-16](https://blog.ethereum.org/2026/10/16/glamsterdam-hoodi-announcement)
  - Some third-party sites cite a specific November 2026 mainnet date. That conflicts with the EF post. Candidate dates of Dec 1/8/9 have been floated but are unconfirmed — [KuCoin](https://www.kucoin.com/news/flash/ethereum-s-glamsterdam-upgrade-activated-on-hoodi-testnet-mainnet-date-undetermined); [CryptoTicker](https://cryptoticker.io/en/ethereum-glamsterdam-mainnet-date/) **[secondary]**

**Testnets (deprecations flagged)**
- **Holešky: DEPRECATED.** The EF announced its sunset; support ended after Fusaka, with shutdown about two weeks after Fusaka finalized on Holesky — [EF blog 2025-09-01](https://blog.ethereum.org/2025/09/01/holesky-shutdown-announcement); [CoinMarketCap Academy](https://coinmarketcap.com/academy/article/ethereum-shuts-down-holesky-testnet-after-fusaka-upgrade).
- **Hoodi** is the validator/staking testnet; **Sepolia** is the recommended testnet for apps and contracts — [EF blog](https://blog.ethereum.org/2025/09/01/holesky-shutdown-announcement). Sepolia's long-term end-of-life is unclear: one secondary source claimed Sepolia "replaced in March 2026"; it conflicts with the EF statements and is likely stale — [Unchained](https://unchainedcrypto.com/ethereum-to-sunset-its-largest-testnet-holesky/).
- **Polygon Mumbai: DEPRECATED** (the project README is out of date). **Amoy** (chain ID 80002, anchored to Sepolia) replaced it — [Alchemy](https://alchemy.com/blog/polygon-amoy-is-live); [Polygon](https://go.polygon.technology/49QAS6i).
- An August 2026 guide says Polygon now runs only Amoy, after shutting down the zkEVM mainnet sequencer in July 2026; the Cardona testnet was removed — [Datawallet](https://www.datawallet.com/es/cripto/c%C3%B3mo-conseguir-fichas-de-polygon-testnet) **[secondary, single source]**
- L2 Sepolia testnets (Arbitrum Sepolia, Optimism Sepolia, Base Sepolia, Linea Sepolia) are listed as standard testnets by infra providers — [Axelar](https://www.axelar.network/blog/axelar-adds-support-for-polygon-amoy-and-linea-sepolia)

**L2 fees**
- April 2026 median per-transaction fees: Base $0.02, OP Mainnet $0.03, Arbitrum One $0.04, zkSync Era $0.05, Scroll $0.06. A USDC transfer costs $0.02 on Base and $0.04 on Arbitrum — [Eco](https://eco.com/support/en/articles/14798701-base-vs-arbitrum-which-l2-should-you-build-on) **[secondary]**
- growthepie reports the cross-L2 median user fee at **0.06¢ per tx** (2026-04). That is about 30x lower than Eco, probably due to a different methodology — [growthepie](https://www.growthepie.com/answers/are-ethereum-l2-fees-getting-cheaper)

**Arbitrum Stylus**
- Stylus runs a second, coequal WASM VM next to the EVM; Rust/C contracts interoperate fully with Solidity.
  - Official docs claim about 10x improvements for WASM contracts and describe the gas unit "ink" as thousands of times smaller than gas — [Arbitrum docs](https://docs.arbitrum.io/stylus/stylus-gentle-introduction) **[primary]**
  - Benchmarks cited secondhand (RedStone, Nov 2025) claim 10–100x faster crypto hashing and bigint arithmetic — [BlockEden 2026-02](https://blockeden.xyz/es/blog/2026/02/01/arbitrum-2026-roadmap-arbos-dia-gaming-catalyst-stylus/) **[secondary]**
- Caveats:
  - Deploying is generally more expensive than in the EVM — [Arbitrum AIP (ArbOS 30)](https://forum.arbitrum.foundation/t/aip-activate-stylus-and-enable-next-gen-webassembly-smart-contracts-arbos-30/22970)
  - Stylus contracts must be **reactivated every 365 days** — [arbitrum-docs PR](https://github.com/OffchainLabs/arbitrum-docs/pull/2893.diff)

**Rollup-as-a-service**
- Conduit charges monthly per chain with usage-based autoscaling; no public 2026 dollar figures were found — [Conduit platform](https://conduit.xyz/platform)
- Caldera supports OP Stack and Arbitrum Orbit; no public pricing found — [Vocal roundup](https://vocal.media/01/top-rollup-as-a-service-providers-to-watch-in-2026) **[secondary]**
- An older Cointelegraph headline advertised L3 rollups "for $50 a month" (undated, probably stale) — [TradingView/Cointelegraph](https://vn.tradingview.com/news/cointelegraph:78be5cdd3094b:0-you-can-now-deploy-your-own-l3-rollup-for-50-a-month)

**Solana / Nous Psyche**
- Psyche coordinates decentralized training on Solana — [Nous Psyche](https://nousresearch.com/nous-psyche) **[primary]**
- A 2026 review says Psyche's Solana programs run on **devnet**, and runs are permissioned (a run admin authorizes nodes) — [ownyourmind.ai](https://ownyourmind.ai/projects/nous-research/) **[secondary]**
- Code: PsycheFoundation/nousnet (per the same review). The flagship run is Consilience-40B (about 20T tokens).

**Bittensor (alternative to own chain)**
- Subnet registration cost is set by a dynamic algorithm: it doubles with each registration and decays over time.
- Recent paid registrations: SN70 at about 224.64 TAO (2026-10-26) and SN103 at about 434.68 TAO (2026-10-20) — [ownyourmind.ai Bittensor](https://ownyourmind.ai/projects/bittensor/) **[secondary, chain-derived]**
- Historical spikes reached 1,500 TAO (May 2026) — [CryptoBriefing](https://cryptobriefing.com/bittensor-subnet-registration-cost-rises/) — and an earlier spike of 10,127 TAO — [DL News](https://www.dlnews.com/articles/defi/ai-hype-in-crypto-pushes-bittensor-subnet-tao-fees/). Live cost: [taostats](https://taostats.io/subnets)
- Templar (SN3) completed **Covenant-72B** on 2026-03-10: 72.7B parameters, about 1.1T tokens, more than 70 permissionless miners, MMLU 67.1.
  - The founder left on 2026-04-10, the subnet was reportedly rebranded "Teutonic", and it announced a 1T-parameter run — [BlockEden 2026-03-13](https://blockeden.xyz/blog/2026/03/13/templar-covenant-72b-bittensor-largest-decentralized-llm-pretraining/); [BlockEden 2026-04-22](https://blockeden.xyz/blog/2026/04/22/bittensor-sn3-teutonic-1-trillion-parameter-decentralized-llm-training-may-2026/) **[secondary]**

### Inferences
- **Gas cost of storing CIDs or emitting events.** Computed from the standard EVM gas schedule (evm.codes), not from a 2026 source:
  - Event cost formula: LOG = 375 base + 375 per topic + 8 gas per data byte.
  - Emitting an event with a 32-byte digest (CIDv1 sha2-256 multihash, stored as bytes32) and two indexed topics costs about 1.4k gas plus about 21k transaction base.
  - `SSTORE` of a new bytes32 slot is about 22.1k gas.
  - At L2 median fees of about $0.001–$0.04 per tx (above), anchoring a checkpoint CID costs well under $0.05 on Base or Arbitrum.
  - Recommendation: store `bytes32` digests and Merkle roots, emit full CIDs in events, and avoid string CIDs in storage.
- Pectra/Fusaka features map directly onto D-PoDL needs:
  - EIP-7702 allows sponsored transactions for contributors.
  - The BLS12-381 precompile allows aggregate signatures from validators/evaluators, replacing many EIP-712 ECDSA checks with one pairing check.
  - Cheaper blobs make an app-rollup cheaper to operate.
- Suggested sequencing:
  1. Deploy on Base Sepolia or Arbitrum Sepolia, then mainnet L2.
  2. Move hot verification loops (e.g., Merkle proof batches) to Stylus only if gas profiling shows they dominate.
  3. Consider an OP Stack or Orbit chain via RaaS only if fee sovereignty or custom precompiles become necessary.
- **Bittensor as a "distribution channel".** A subnet gives instant miner/validator supply and emissions, but costs hundreds of TAO and means abandoning the ERC20 token design. Templar/Teutonic shows permissionless pretraining is possible but also shows team and governance fragility.

### Gaps
- No official current (Nov 2026) Base/Arbitrum fee snapshot was retrieved; check [growthepie.com/fees](https://www.growthepie.com/) and [L2Beat](https://l2beat.com) live.
- Optimism Superchain 2026 status (interop, membership, Base's relationship) and Arbitrum Orbit/BoLD details were not researched in depth.
- Cosmos SDK appchain 2026 state was not researched.
- No public 2026 RaaS price lists were found (quote-based).
- Glamsterdam mainnet date is unknown as of the latest EF post (2026-10-16).

---

## 2. Restaking / verification markets and zkVMs

### Takeaway
EigenLayer slashing has been live on mainnet since 2025-04-17, with Operator Sets and Unique Stake. A "D-PoDL verification AVS" is technically realistic, but operator recruitment and economic security make it a large undertaking for a small team. A better first step is buying cheap ZK proofs for deterministic checks (Merkle, hash, small-model evaluation) from Succinct's Prover Network (SP1 Hypercube, live 2026-02-19) or RISC Zero's Boundless (live since September 2025).

### Cited Findings

**EigenLayer**
- Slashing went live on mainnet **2025-04-17** **[primary]**:
  - It is opt-in: Operators choose Operator Sets with AVS-specific slashing conditions.
  - "Unique Stake" earmarks stake so only one AVS can slash it.
  - Redistribution of slashed funds was "coming soon" at launch — [EigenLabs blog](https://www.eigenlabs.org/blog/slashing-goes-live/)
- Later docs, as summarized secondarily, say slashed funds are burned or, for redistributable operator sets, sent to an AVS-named recipient — [Coinpaprika](https://coinpaprika.com/education/eigenlayer-restaking-how-ethereum-restaking-unlocks-extra-eth-yield) **[secondary]**
- One BlockEden piece dates the slashing activation to 2026-04-17. This **conflicts** with the primary post (2025) and is likely an error — [BlockEden](https://blockeden.xyz/blog/2026/04/18/eigenlayer-avs-slashing-activation-15b-restaking-reality-check/)
- EigenCloud now bundles EigenDA, EigenAI and EigenCompute — [Coin Bureau](https://coinbureau.com/review/eigenlayer-review) **[secondary]**
- ELIP-012 (incentives overhaul) was approved by the Protocol Council on 2026-03-12 — [web3wagmi](https://blog.web3wagmi.com/eigenlayer-guide) **[secondary]**
- One source reports **zero slashing events through May 2026** — [web3wagmi](https://blog.web3wagmi.com/eigenlayer-guide) **[secondary, single source]**
- AVS developer guide: [Intro to Slashing: AVS Edition](https://blog.eigencloud.xyz/intro-to-slashing-on-eigenlayer-avs-edition/)

**Symbiotic**
- Symbiotic shipped a feature-complete shared-security protocol with slashing; it supports any ERC-20 as collateral — [Blockworks](https://blockworks.co/news/symbiotic-shared-security-slashing); [DEXTools 2026](https://www.dextools.io/tutorials/what-is-symbiotic-protocol-permissionless-restaking-guide-2026-de) **[secondary]**

**Succinct SP1 Hypercube**
- Live on mainnet and in the Succinct Prover Network, per a post dated **2026-02-19** **[primary]**:
  - Proved 99.7% of Ethereum blocks in under 12 s on 16 RTX 5090s (Nov 2025).
  - Claimed 4x faster than SP1 Turbo on compute-heavy workloads.
  - All 62 RISC-V opcodes formally verified against the Sail spec (with Nethermind and the EF); multiple audits completed.
  - **No per-proof pricing was published** — [Succinct blog](https://blog.succinct.xyz/sp1-hypercube-is-now-live-on-mainnet/)
- One estimate puts Hypercube proofs as low as about $0.02 with about 2-minute latency — [Hazeflow](https://research.hazeflow.xyz/p/proof-generation-on-succinct-and) **[secondary]**

**RISC Zero / Boundless**
- Boundless has been on mainnet since September 2025, with 542T cycles and 399K orders processed — [BlockEden 2026-01-14](https://blockeden.xyz/blog/2026/01/14/boundless-risc-zero-decentralized-proof-market-zk/) **[secondary]**
- RISC Zero claims to be at least 7x cheaper than SP1, and up to 60x for small workloads. Succinct disputes this as a CPU-vs-GPU comparison — same source.

### Inferences
- **Realistic D-PoDL verification design for 2026.** Split verification into three tiers:
  1. **Deterministic, cheap checks.** Merkle inclusion of shard hashes, checkpoint hash equality, signature aggregation. Run these on-chain directly on an L2, or as SP1/RISC Zero proofs verified on-chain (a few hundred thousand gas per Groth16-wrapped proof; typical figure, not re-verified here).
  2. **Small-model evaluation** (e.g., loss on a fixed held-out batch with a tiny model). This is feasible in a zkVM but cycle-heavy. Prototype with SP1 and measure cycles before committing.
  3. **Large-model gradient/quality claims.** Use optimistic verification: stake, random spot-check, challenge-response. Here an EigenLayer or Symbiotic AVS (operators re-run spot checks and get slashed for false attestations) is the natural fit.
- **Starting an AVS is premature.** An AVS needs operators to opt in, so it is more of a go-to-market than an engineering problem. With zero observed slashing events reported (single source), the economic-security market is still immature. Start with the project's own staking/slashing contract on an L2 and keep the interface AVS-compatible.

### Gaps
- No official 2026 price sheets were found for the Succinct Prover Network (PROVE token auctions) or Boundless (ZKC). Get live quotes from their explorers or docs.
- 2026 EigenLayer redistribution status was not confirmed from a primary source.
- Symbiotic 2026 AVS ("network") adoption numbers were not found.

---

## 3. Storage for large model checkpoints and data availability

### Takeaway
Use a two-tier design:
- **Hot, mutable checkpoints:** Hugging Face Storage Buckets ($8–18/TB/mo, egress included, Xet content-defined-chunking dedup) or Cloudflare R2 ($15/TB/mo, zero egress).
- **Verifiable, decentralized persistence:** Filecoin Onchain Cloud (about $2.50/TiB/mo per copy, PDP proofs, live on mainnet), with IPFS CIDs anchored on-chain.

Arweave (one-time permanent fee) and Walrus (about $23/TB/mo list before 4.5x encoding overhead) are poor fits for frequently replaced multi-GB checkpoints. DA layers such as EigenDA and Celestia are not checkpoint storage; they are only relevant if the project runs its own rollup.

### Cited Findings

**Hugging Face Storage Buckets** **[primary]**

| Tier | Public | Private |
|---|---|---|
| Base | $12/TB/mo | $18/TB/mo |
| 50TB+ | $10 | $16 |
| 200TB+ | $9 | $14 |
| 500TB+ | $8 | $12 |

- Egress and CDN are included up to an 8:1 egress-to-storage ratio.
- Xet does content-defined chunking with bucket-wide dedup. Billing on deduplicated bytes requires an Enterprise plan. Example on the page: 66 TB stored, billed 41 TB. HF claims "4x less data per upload".
  — [HF Storage](https://huggingface.co/storage)
- Buckets are non-versioned and mutable, designed for checkpoints. Successive checkpoints with frozen layers benefit from chunk dedup — [HF docs Storage Buckets](https://huggingface.co/docs/hub/en/storage-buckets); [HF blog](https://huggingface.co/blog/storage-buckets)

**Cloudflare R2** **[primary]**
- Standard storage $0.015/GB-mo (about $15/TB-mo); Infrequent Access $0.01/GB-mo.
- Class A ops $4.50/M; Class B ops $0.36/M; egress free.
- Free tier: 10 GB plus 1M Class A / 10M Class B operations per month.
  — [Cloudflare R2 pricing](https://developers.cloudflare.com/r2/pricing/)

**Filecoin Onchain Cloud (FOC)**
- Announced 2025-11-19 — [Filecoin blog](https://filecoin.io/blog/posts/introducing-filecoin-onchain-cloud/); [CoinDesk PR](https://www.coindesk.com/press-release/2025/11/19/introducing-filecoin-onchain-cloud-verifiable-developer-owned-infrastructure)
- Live on mainnet with 49.41 TiB stored across 478 datasets — [Filecoin blog](https://www.filecoin.io/blog/filecoin-onchain-cloud-is-live-on-mainnet); [Blockchain.News](https://blockchain.news/news/filecoin-onchain-cloud-mainnet-launch-ai-storage)
- Pricing **[primary docs]**:
  - **$2.50/TiB/month per copy**, minimum 2 copies (so about $5/TiB/mo effective)
  - $0.12 per data set per month for proof (PDP) verification
  - Retrieval egress via Filecoin Beam up to $14/TiB
  - Paid in USDFC or ERC-20 through Filecoin Pay
  — [docs.filecoin.cloud](https://docs.filecoin.cloud/introduction/about/)
- A Bitget report of "25,000 USD per TiB" is almost certainly a typo — [Bitget](https://www.bitget.com/news/detail/12560605309044)

**Storacha Forge**
- $5.99/TB, running on the Filecoin network — per Storacha's launch announcement, as relayed in search results **[secondary]**

**Walrus (Sui)**
- List price about $0.023/GB/mo, with a **4.5x encoding multiplier**: effective about $0.10/GB/mo, or about $100/TB/mo of raw data. There is also a fixed 64 MB per-blob overhead — [bestcloudmining review](https://www.bestcloudmining.net/providers/walrus/) **[secondary]**
- Subsidized rates are mostly for Sui-ecosystem builders — [GCR](https://globalcoinresearch.com/research/walrus-vs-legacy-web3-storage)

**Arweave**
- One-time permanent fee; quotes vary from about $5–8/GB to about $9,747/TB — [0G blog](https://0g.ai/blog/0g-storage-vs-filecoin-arweave); [GCR](https://globalcoinresearch.com/research/walrus-vs-legacy-web3-storage) **[secondary, conflicting]**

**DA layers (Celestia)**
- Celestia DA about $0.07/MB vs about $3.83/MB on Ethereum blobs (Eclipse data). Eclipse accounted for about 84% of Celestia blob share (May 2026) — [BlockEden 2026-01-16](https://blockeden.xyz/es/blog/2026/01/16/celestia-blob-economics-data-availability-rollup-costs/) **[secondary]**

### Inferences
- **Concrete pipeline**
  1. Save safetensors.
  2. Compute per-tensor hashes and a Merkle root (already in the project).
  3. Upload to an HF Bucket (dedup across successive checkpoints and deltas).
  4. Pin to IPFS/Kubo or FOC for the canonical CID.
  5. Anchor the root plus CID on the L2.
  Keeping Kubo for CIDs is fine, but self-hosted Kubo pinning of multi-TB data is operationally costly. Filecoin Onchain Cloud with PDP proofs gives on-chain verifiability for about $5/TiB-mo.
- **Rough monthly cost of 10 TB of checkpoints**
  - FOC: about $50 (2 copies)
  - HF public bucket: about $120
  - R2: about $150
  - Walrus: about $1,000 effective
  - Arweave: tens of thousands of dollars one-time
- **Hidden gem:** Xet's content-defined chunking means checkpoint deltas (fine-tunes, LoRA merges, frozen layers) are stored once. This partially replaces custom delta-encoding code.

### Gaps
- Retrieval latency numbers (time to first byte or throughput) were not found for any provider; benchmark locally.
- No official Walrus 2026 pricing page was retrieved (verify at docs.wal.app).
- EigenDA 2026 pricing was not found.
- Storacha pricing was not verified from its primary page.
- Kubo 2026 release status was not researched.

---

## 4. Smart-contract tooling (Hardhat 3 vs Foundry, OpenZeppelin, analysis, fuzzing, AI auditors, Python and TypeScript clients)

### Takeaway
Migrate from Hardhat 2 to **Hardhat 3** (Foundry-compatible Solidity tests, viem toolbox, built-in coverage, OP-chain simulation) or add **Foundry** alongside. Many teams use both. Upgrade to **OpenZeppelin Contracts 5.5–5.7**, noting the breaking EIP712 change in 5.7. Upgrade the Python interface to **web3.py 8.0.0** (released about 2026-08-31). The CI gate should be Slither plus Aderyn, Medusa/Echidna invariant fuzzing, and an LLM-orchestrated triage pass.

### Cited Findings

**Hardhat 3** **[primary]**
- Features:
  - Foundry-compatible Solidity tests (unit, fuzz, invariant), with TypeScript tests kept alongside
  - Multichain simulated networks with first-class Ethereum Mainnet and OP Mainnet chain types
  - ESM-first, declarative configuration with lazy config variables
  - Built-in `--coverage`, hook-based plugins, typed artifacts
  — [Hardhat 3 What's new](https://hardhat.org/docs/hardhat3/whats-new)
- Requires Node ≥ 22.13; recommends pnpm and `hardhat-toolbox-viem` — [Hardhat getting started](https://hardhat.org/docs/getting-started)
- Release status: one source says it was a production-ready beta in August 2025 and stable in June 2026 — [metlabs](https://metlabs.io/en/blog/hardhat-vs-foundry/) **[secondary; not confirmed from primary]**
- Benchmarks: a September 2026 rerun found Foundry builds faster while Hardhat 3's test command was faster on the same suite — [rick.build](https://www.rick.build/blog/foundry-vs-hardhat-performance-benchmark) **[secondary]**

**Foundry**
- 1.0 released in February 2025; another source cites v1.7.1 — [dev.to](https://dev.to/pavelespitia/foundry-vs-hardhat-in-2026-which-solidity-toolchain-wins-20jd) **[secondary]**

**OpenZeppelin Contracts**
- v5.5.0 stable:
  - `_validateUserOp` gets a signature argument.
  - Initializable and UUPSUpgradeable now import from the main package.
  - Adds Arrays slice/splice.
- Then v5.6.0/5.6.1 and **v5.7.0**. Breaking in 5.7: EIP712 name and version must each fit a ShortString (≤31 bytes); an ERC2771Forwarder error was renamed — [OZ releases](https://github.com/OpenZeppelin/openzeppelin-contracts/releases); [newreleases 5.5.0](https://newreleases.io/project/github/OpenZeppelin/openzeppelin-contracts/release/v5.5.0)

**web3.py**
- **8.0.0** is on PyPI (artifacts verified 2026-08-31; Python 3.10+). The prior line ended at 7.16.0 (2026-05-01) — [PyPI web3](https://pypi.org/pypi/web3); [CERN mirror](https://simple-repository.app.cern.ch/project/web3)

**Static analysis, fuzzing and AI auditing**
- Slither: 90+ detectors. Aderyn: Rust, AST-based. Medusa: parallel, Echidna-inspired fuzzer with CLI/Go API. Halmos: symbolic testing.
- Recommended practice: run Slither/Aderyn first and feed the output to an LLM for triage. MCP pipelines have Claude or GPT orchestrate Slither, Aderyn and Foundry fuzzing — [dev.to MCP pipeline](https://dev.to/ohmygod/ai-powered-smart-contract-auditing-in-2026-building-an-mcp-security-pipeline-that-actually-works-1fh8); [Aderyn vs Slither 2026](https://hashnode.com/posts/aderyn-vs-slither-2026-rust-python-static-analysis-cicd/69ca74b446cdcbdc649798f8) **[secondary]**
- OpenAI and Paradigm's **EVMbench** reported GPT-5.3-Codex autonomously exploiting 71% of benchmark vulnerabilities. BlockSec's March 2026 re-evaluation argued the scaffold inflated the scores — [dev.to EVMbench](https://dev.to/ohmygod/evmbench-deep-dive-can-ai-agents-actually-find-smart-contract-bugs-better-than-human-auditors-we-2g39) **[secondary]**
- Commercial AI auditors compared include Sherlock AI, Olympix, Almanax and QuillShield — [dev.to comparison](https://dev.to/ohmygod/ai-smart-contract-auditors-compared-sherlock-ai-vs-olympix-vs-almanax-vs-quillshield-which-one-h64) **[secondary]**

### Inferences
- **Migration path**
  - Keep Hardhat as the project shell (TypeScript and Ignition deploys), but move to Hardhat 3 with viem.
  - Rewrite tests as `.t.sol` so they run under both Hardhat 3 and Foundry.
  - Add `forge` for invariant tests on DPoDLToken/ModelRegistry and Medusa for long fuzz campaigns.
- **Audit pass before mainnet:** the OZ 5.7 EIP712 ShortString constraint, plus EIP-712 domain separators on the new chain ID.
- **Python side:** web3.py v8 is a major version, so expect breaking changes and pin the version. Alternatives for typed/fast clients are viem (TypeScript) or Ape; not deeply researched here.

### Gaps
- Hardhat 3 stable release date and Hardhat 2 end-of-support policy were not confirmed from primary sources.
- web3.py v8 changelog (breaking changes) was not retrieved.
- Latest Foundry version and date were not confirmed from GitHub.
- No credible, independently verified accuracy numbers were found for AI auditors.

---

## 5. Networking for P2P training

### Takeaway
**iroh 1.0** (stable 2026-06-15) is the simplest modern choice: dial by public key, QUIC with multipath, relay fallback, stable wire protocol, Python bindings. It fits a Python/Ray stack better than assembling rust-libp2p. libp2p remains the choice for IPFS/Kubo interop. Browser (WebGPU/WebRTC) contributors remain impractical for training as of 2026; WebGPU is mainly an inference technology.

### Cited Findings
- iroh 1.0 shipped after four years and 65 pre-releases, reportedly stable on 2026-06-15:
  - Stable wire protocol and APIs, with Python, Node.js, Swift and Kotlin bindings covered by the guarantee.
  - QUIC multipath and relay fallback.
  — [iroh blog](https://iroh.computer/blog/the-road-to-iroh-1-0); [pinggy](https://pinggy.io/blog/iroh_1_0_dial_keys_not_ips/); [byteiota](https://byteiota.com/iroh-1-0-peer-to-peer-networking/)
- Hole-punch success claims vary: iroh about 90–95% vs libp2p about 70% — **unverified** secondary figures.
- WebGPU is available in over 90% of browser sessions, but Firefox has it behind a flag and Safari support is still progressing. Browser LLM work (LlamaWeb, WebLLM, Transformers.js) is inference-only. A Hacker News discussion found browser distributed training "possible but impractical" — [arXiv 2605.20706 LlamaWeb](https://arxiv.org/html/2605.20706); [online-clipboard 2026-05](https://online-clipboard.online/blog/2026/05/10/webgpu-browser-ai/)

### Inferences
- **Practical stack**
  - iroh, with iroh-blobs for content-addressed transfer of shards and gradients, for node-to-node traffic.
  - Ray only within trusted clusters.
  - Kubo/libp2p only at the IPFS boundary.
- **Low-bandwidth algorithms** (DiLoCo-style, as used by Prime Intellect/Psyche/Templar) matter more than the transport.

### Gaps
- rust-libp2p 2026 releases were not researched.
- Whether Nous Psyche uses iroh for its P2P transport (commonly reported) was not confirmed in any source retrieved this session.
- No 2026 browser-based decentralized training system was found.
- MLX distributed training on Apple M-series was not researched successfully.

---

## 6. Compute supply (GPU rental and consumer GPUs)

### Takeaway
Realistic-scale testing is cheap in late 2026:
- RTX 5090 at about $0.48–0.69/hr (Vast.ai, RunPod community)
- H100 SXM at about $2.2–2.7/hr on marketplaces and community clouds, about $4/hr on secure clouds
- **Example test:** 16 heterogeneous RTX 5090 nodes for a 24-hour network test cost about $200

### Cited Findings
- Live index (about 2026-11-03): cheapest secure on-demand H100 SXM is **$2.40/GPU-hr (Vast.ai)**, 30-day median $2.22. **RTX 5090 is $0.53/hr on Vast.ai** (30-day average $0.48) — [gpuperhour.com](https://gpuperhour.com/) **[secondary aggregator]**
- RunPod pricing page **[primary]**:
  - H100 SXM: $2.69/hr community, $3.99/hr secure
  - H100 PCIe: from $1.99/hr
  - RTX 5090: $0.69/hr community, $1.19/hr secure
  — [RunPod pricing](https://www.runpod.io/pricing)
- October 2026 comparison: RunPod H100 $3.99; Vast.ai H100 $6.43 (single-host outlier) — [Thunder Compute](https://www.thundercompute.com/blog/nvidia-h100-pricing)
- Cross-provider H100 range of $1.49–$6.98/hr across 15+ providers (2026) — [IntuitionLabs](https://intuitionlabs.ai/articles/h100-rental-prices-cloud-comparison) **[secondary]**
- Prime Intellect's compute layer is a meta-cloud marketplace aggregating centralized and decentralized providers — [PI blog compute](https://primeintellect.ai/blog/compute)
- Prime Intellect reportedly raised a $130M Series A on 2026-07-08 — [ai2.work](https://ai2.work/blog/prime-intellect-s-130m-bet-on-enterprise-owned-ai-training) **[secondary, unverified]**

### Inferences
- **Use cheap consumer GPUs for heterogeneity tests.** Vast.ai/RunPod community RTX 5090s give realistic heterogeneity: varied NAT, bandwidth and reliability, much like real D-PoDL contributors.
- **Use H100s only for a reference baseline.**

### Gaps
- SF Compute, Lambda, Akash and io.net 2026 prices were not retrieved.
- AMD (MI300/MI355, consumer RDNA) rental prices and ROCm maturity were not researched.
- Apple M-series/MLX distributed capability was not confirmed.

---

## 7. AI-assisted development and templates/boilerplates

### Takeaway
2026 coding agents can carry most of the migration work:
- Hardhat 2 → Hardhat 3 / Foundry
- OZ v5.7 upgrades
- web3.py v8 port
- test generation
- Slither/Aderyn triage via MCP

Human review is still needed for economic and business-logic security; benchmark exploit claims (EVMbench) are contested. Reusable open-source building blocks to study or reuse:
- Psyche (Solana coordination plus P2P training)
- Prime Intellect's PRIME-RL and Verifiers (open source)
- Templar/Teutonic subnet code (Bittensor)

### Cited Findings
- AI is a force multiplier in human-in-the-loop review, not a replacement; static tools cannot reason about business logic — [dev.to 2026 toolkit](https://dev.to/ohmygod/the-2026-smart-contract-security-audit-toolkit-a-practitioners-guide-to-catching-what-ai-and-47me) **[secondary]**
- MCP pipelines with Claude or GPT orchestrating Slither, Aderyn and Foundry — [dev.to](https://dev.to/ohmygod/ai-powered-smart-contract-auditing-in-2026-building-an-mcp-security-pipeline-that-actually-works-1fh8)
- PRIME-RL (asynchronous RL) and Verifiers are open source. INTELLECT-3 (106B MoE, November 2025) was trained centrally on 512 H200s, not on PI's decentralized network — [implicator.ai](https://www.implicator.ai/prime-intellects-intellect-3-open-source-ambition-meets-centralized-reality/); [latent.space wiki](https://latent.space/wiki/prime-intellect/) **[secondary]**
- PI's protocol is described as a peer-to-peer GPU marketplace with **TOPLOC** verification (locality-sensitive hashing of inference/activation outputs). No token has launched — [aitoolsatlas](https://aitoolsatlas.ai/tools/prime-intellect) **[secondary]**
- Psyche's open codebase is PsycheFoundation/nousnet — [ownyourmind.ai](https://ownyourmind.ai/projects/nous-research/)

### Inferences
- **Hidden gems for D-PoDL**
  - **TOPLOC-style** locality-sensitive hashing of activations: a cheap, probabilistic "proof of computation" that complements Merkle trees of model state.
  - **Xet dedup** for checkpoint deltas.
  - **EIP-2537 BLS aggregation** for validator attestations.
  - **iroh-blobs** for verified, content-addressed transfer.
  - **Hardhat 3 OP-chain simulation** for L2-accurate local tests.
- **Agent workflow for a solo developer**
  1. Have the agent produce a migration plan.
  2. Port the toolchain.
  3. Generate invariant tests from the spec.
  4. Run Slither, Aderyn and Medusa in CI.
  5. Do LLM triage.
  6. Budget for one human audit or a competitive audit (Sherlock, Code4rena) before mainnet value is at risk.

### Gaps
- An official Bittensor subnet template repository with 2026 status was not retrieved.
- Primary-source descriptions of Prime Intellect protocol/testnet components in 2026 were not found.
- Official Claude Code and Codex 2026 capability or pricing details were not researched in this session.
