# Viability constraints for a small-team D-PoDL revival (costs, funding, legal, publication, team, participants), as of 2026-11-05

Scope note: these notes cover only what the earlier report (`reports/DPoDL revival research November 2026.md`) did not. That report already gives RTX 5090 at about $0.53/h and H100 SXM at about $2.40/h, a 16-node 24-h test at about $200, Base/Arbitrum fees of about $0.02–0.04/tx, HF Buckets at $12/TB/month, Filecoin Onchain Cloud at $2.50/TiB/month, and a subnet registration cost of about 225–435 TAO in late October 2026. The prices below supersede the GPU figures. "EST" marks this researcher's own estimates. Every other line cites a source, tagged [P] for primary and [S] for secondary or aggregator.

## 1. Costs: verifier runs, red-team day, validators, gas/storage, agent API, Bittensor

### Takeaway
The cash cost of running the protocol is small if the flagship task is an autoresearch-style one: a single GPU, about 5 minutes per seed, 8 seeds. Each verification then costs a few dollars, a red-team day $270–770, and an on-demand validator under $100/month. The cost that kills participation is on the miner side. A Prime-Intellect-style agent run uses an 8×H200 node for 1–9 days, which is about $700–1,000 of GPU per day plus $180–1,000 of API tokens. Task size, not chain fees, decides who can take part. A Bittensor subnet costs six figures to register and the burn is not refunded, so it is out of reach for this team in 2026–27.

### Cited Findings
**GPU prices (dated)**
- RunPod, "Updated November 4, 2026" [P]. Community/Secure Cloud per GPU-hour: H100 SXM $2.69/$3.99; H100 PCIe $1.99/$2.89; H100 NVL $2.59/$3.19; H200 $3.59/$5.29; B200 $5.98/$7.99; RTX 5090 $0.69/$1.19; RTX 4090 $0.34/$0.89. Network storage costs $0.07/GB/month under 1 TB, and volume disk $0.10/GB/month while running and $0.20 idle. — [RunPod pricing](https://www.runpod.io/pricing)
- An October 2026 comparison puts on-demand list prices between $1.99 (RunPod Community H100 PCIe) and $12.29 per H100-hour (Azure ND96isr H100 v5). AWS p5.48xlarge Capacity Blocks rose from $5.191 to $5.970 per H100-hour between August and October 2026, so prices are rising, not falling [S]. — [IntuitionLabs H100 price comparison 2026](https://intuitionlabs.ai/articles/h100-rental-prices-cloud-comparison)
- CloudRift's rate sheet lists the RTX 5090 at $0.60/h and the RTX 4090 at $0.39/h. Spot RTX 5090 was seen at about $0.18/h (data dated 2026-07-30) [S, aggregator]. — [getdeploying H100 vs RTX 5090](https://getdeploying.com/gpus/nvidia-h100-vs-nvidia-rtx-5090); [Spheron H100 price 2026](https://www.spheron.network/blog/h100-price-per-hour-2026/)

**Verifier protocol reference (Prime Intellect, 2026-08-15) [P]**
- The study ran 153 autonomous runs across 18 frontier models. Each agent had "a GPU node (8xH200s)". Runs lasted 0.6–8.7 days, and the main comparison used a 24-h budget. A claim counted only if an 8-seed mean on fixed seeds beat 3.27859, which the post says makes passing by luck "roughly one-in-a-thousand". Fable 5 used about 800M total tokens, of which about 1.1M were output. **The post reports no dollar cost per run and no total compute budget.** — [Prime Intellect, Measuring autonomous research](https://primeintellect.ai/blog/measuring-autonomous-research)
- The repo README gives 8×H200 as the hardware but no wall-clock time per seed, no cost and no visible licence. Its files are `train_gpt_simple.py`, `program.md`, `program-serial.md` and `traces/` [P]. — [frontier-automated-speedrun](https://github.com/PrimeIntellect-ai/frontier-automated-speedrun)
- Karpathy's autoresearch loop uses one GPU and 5-minute jobs. Two days of agent tuning found about 20 improvements, an 11% cut in nanochat leaderboard time [S]. — [Bitcoin Street Journal, 2026-03-11](https://thebitcoinstreetjournal.com/karpathy-reports-11-improvement-in-nanochats-leaderboard-time-via-autoresearch); [Fortune 2026-03-17](https://fortune.com/2026/03/17/andrej-karpathy-loop-autonomous-ai-agents-future/)

**Frontier model API pricing (Anthropic first-party, reference table cached 2026-10-06) [P]**
- Fable 5 and Fable 5.1 cost $10/$50 per MTok (input/output), and Fable 5.1 cache reads cost $0.25/MTok. Opus 5.5 costs $4/$20 with cache reads at $0.20. Opus 5 costs $5/$25. Sonnet 5.5 costs $2/$10 with cache reads at $0.20. Haiku 5.5 costs $0.10/$0.50. Batch processing is 50% off. — [Anthropic API pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- No OpenAI, Google, Kimi or other vendor 2026 prices were collected in this pass (see Gaps).

**Bittensor**
- Subnet registration rose from 230 to 1,500 TAO, about $470k, around 2026-05-12/06-13. An April 2026 Taostats reading put it at about 1,245 TAO [S]. The price doubles with each registration and then decays. — [ValueTheMarkets](https://www.valuethemarkets.com/cryptocurrency/news/bittensors-subnet-registration-costs-soar-to-470000-implications-for-investors); [CryptoBriefing](https://cryptobriefing.com/bittensor-subnet-registration-cost-rises/). The live figure is available from `btcli query subnet-registration-cost --json` [P]. — [Bittensor docs](https://preview.bittensor.com/llms.mdx/docs/query/subnet-registration-cost/content.md)
- Current docs set the immunity period at **4 months** from the registration block, down from 6 months under the October 2025 changes. At the cap (128 subnets, though some pages say 256), the non-immune subnet with the lowest EMA price is deregistered, at most one every 4 days. **Lock costs are burned with no refund** for subnets registered after the 2025-10-01 rollout, so the owner keeps only owner emissions already received [P]. — [Bittensor docs, subnet deregistration](https://docs.learnbittensor.org/subnets/subnet-deregistration)
- In April 2026, 67 of 128 monitored subnets were burning 99%+ of incentives, according to Taostats data cited by FalconX [S]. — [FalconX State of Bittensor](https://falconx.io/newsroom/state-of-bittensor-subnet-adoption-trends-network-mechanics-and-covenants-departure)

**Smart-contract audit pricing (vendor blogs; treat as marketing) [S]**
- Most standard pre-launch reviews cost $15k–40k, within a wider range of $5k to $250k+. — [Sherlock 2026 pricing reference](https://www.sherlock.xyz/post/smart-contract-audit-pricing-a-market-reference-for-2026)
- Zealynx charges about $6,000 per auditor-week, adds 30–50% for rush work and 20–40% for post-audit retainers, and puts simple tokens from $5k. — [Zealynx audit pricing 2026](https://www.zealynx.io/blogs/audit-pricing-2026)
- A well-documented contract under 500 LOC "may cost only a few thousand dollars". — [DEV: audit cost for small protocols](https://dev.to/juan23z/what-does-a-smart-contract-audit-actually-cost-an-honest-breakdown-for-small-protocols-5gfm)

### Inferences (EST unless cited)
- **Verifier cost per submission (EST), at RunPod Community prices of 2026-11-04:**
  - (a) Autoresearch-style task (1 GPU × 5 min × 8 seeds = 40 GPU-min): about $1.80 on H100 SXM, about $0.50 on RTX 5090 if the run fits in 32 GB, and roughly ×1.5 at Secure Cloud.
  - (b) A modded-nanogpt 124M target at baseline-recipe speed: if one seed takes about 3–10 min on an 8×H100 node, 8 seeds take 0.4–1.3 node-hours, about $9–29 per verification. Record-speed recipes, at about 40 s per run on 8×H100 per the earlier report, cost about $2.
  - (c) A nanochat d26-class target, at about $300 per run, costs about $2,400 per 8-seed verification. That is not viable as a per-submission check; use it only as a monthly "transfer test" of accepted diffs.
  - Recommendation: make (a) the default market task and (b) the prestige track.
- **Red-team day (EST):** 16× RTX 5090 × 24 h costs $265 at Community prices or $457 at Secure. One 8×H100 SXM node for 24 h costs $516–766. A two-day exercise mixing both comes to about $1–2k, which replaces the earlier report's $200.
- **Continuous validators (EST):**
  - An always-on 1× H100 costs about $1,960/month (730 h × $2.69). An always-on RTX 5090 costs about $500/month.
  - On-demand verification is far cheaper. At 200 submissions/month under task (a), it costs about $360–540/month on H100 or about $100 on RTX 5090. Add a CPU VPS for the indexer and L2 relayer at about €5–20/month (EST, not sourced).
  - Two independent validators, which is the minimum for a credible "not self-verified" claim, double these figures.
- **Chain and storage (EST):**
  - Testnet gas is $0. A Base or Arbitrum mainnet anchor costs $0.02–0.04/tx per the earlier report, so 1,000 settlements cost about $40.
  - A bf16 124M checkpoint is about 0.25 GB, and diffs are kilobytes. A year of checkpoints, about 1 TB, costs about $12/month on HF or about $2.50/month per copy on Filecoin. Storage is negligible.
- **AI-agent miner cost per run (EST), from Prime Intellect's token counts and Anthropic prices:**
  - Fable 5 with about 800M tokens, nearly all of them cache reads: roughly $800 of cache reads at about $1/MTok (assumed 10% of input price, not sourced for Fable 5), plus about $55 of output, plus cache writes, for about $850–1,000.
  - The same profile costs about $250–400 on Fable 5.1 ($0.25 cache reads) and about $180–250 on Opus 5.5.
  - GPU for the 8×H200 node costs $689–1,016 per 24 h (Community to Secure), so the 8.7-day Fable 5 run cost about $6–9k.
  - **GPU, not tokens, dominates.** A market whose task needs 8×H200 days will attract only labs. A 1-GPU, 5-minute task brings an agent-miner's daily cost down to about $20–60 of GPU (EST) plus tokens.
- **Bittensor (EST):**
  - At 225–1,500 TAO, which is $70k–470k on the June 2026 implied rate of about $313/TAO, registration is unaffordable without an accelerator.
  - The 4-month immunity window plus lowest-EMA-price pruning means a research subnet without token-holder demand faces deregistration risk soon after month 4.
  - Defer Bittensor until after the testnet unless Yuma or another backer pays the burn.
- **Audit (EST):** A TaskEscrow plus Submission plus Challenge set of about 500–900 nSLOC needs about 1–2 auditor-weeks, about $6–15k, or a competitive audit. **A testnet with no real value needs no paid audit.** Free tooling (Slither, Aderyn, Medusa/Echidna invariants) and an explicit "unaudited research prototype" label are enough.

### Gaps
- Bittensor's subnet owner/miner/validator emission split (commonly cited as 18/41/41) and current owner-take rules were not re-verified in this pass. Check the live `btcli subnet hyperparameters` output.
- The Nov 2026 TAO price and live registration cost were not fetched. The earlier report gave 225–435 TAO in late October.
- No per-agent-run dollar cost was published by Prime Intellect, and the cost of OpenAI and Google models was not collected.
- Wall-clock time per seed for the frontier-automated-speedrun baseline is not documented in its README.
- No 2026 Base or Arbitrum fee figure for November was refreshed.

## 2. Funding and grants open late 2026–2027

### Takeaway
No single program fits cleanly, and several EU programs are paused or between calls. The most realistic stack for a 1–2 person EU team is:
- EuroHPC AI Factories Fast Lane, for free GPU-hours if incorporated as an SME/startup, or AI-for-Science if academic-affiliated;
- an Ethereum Foundation ESP application, via the Wishlist or RFP or as an academic grant;
- Optimism Retro Funding after shipping;
- the NLnet/NGI successor call when it reopens;
- Google TRC for TPU time, which requires publishing.

Bittensor accelerators fund subnet teams, not research prototypes.

### Cited Findings
**Ethereum Foundation ESP**
- On 2025-11-03 ESP moved from open intake to a Wishlist and RFP structure. Open applications remain possible. An example RFP, on LLMs for protocol security research, was due 2026-02-03 [S]. — [crypto.news](https://crypto.news/ethereum-foundation-unveils-new-esp-grants-program/); [CoinMarketCap Academy](https://coinmarketcap.com/academy/article/ethereum-foundation-launches-new-grant-program-structure)
- ESP allocated $9.856M in Q1 2026, focused on cryptography, ZK and security [S]. — [KuCoin news](https://www.kucoin.com/news/flash/ethereum-foundation-announces-9-85m-q1-2026-ecosystem-funding)
- ESP runs an annual Academic Grants Round and pays grants in ETH by default [S]. — [Gitcoin ESP page](https://gitcoin.co/apps/ethereum-foundation-esp); live entry point [P]: [esp.ethereum.foundation/applicants](https://esp.ethereum.foundation/applicants)

**Optimism**
- About 40M OP of Retro Funding has been paid since 2022 [P]. — [retrofunding.optimism.io](https://retrofunding.optimism.io/)
- "Backstop grants" top up Retro Funding payouts as "a temporary bootstrapping experiment" [P]. — [Optimism gov forum](https://gov.optimism.io/t/introducing-backstop-grants/8031)
- FY5 (May 2026–Apr 2027) Retro Funding is a Budget Board draft forecast, not final [S]. — [tokenradar](https://tokenradar.ai/tokens/optimism/tokenomics?time=30d)

**NLnet / NGI Zero (EU)**
- The 12th Commons Fund call closed 2026-04-01 and the 13th closed 2026-06-01. NLnet then stopped accepting general proposals while it transitions to an "Open Internet Stack" effort. Only two topics stayed open (deadline 2026-08-01), and the regular call was to reopen "after summer 2026" [P]. — [NLnet news 2026-06-01](https://nlnet.nl/news/2026/20260601-call.html); [Cyprus funding portal, 13th call](https://www.fundingprogrammesportal.gov.cy/en/call/ngi-zero-commons-fund-13th-open-call-reclaim-the-public-nature-of-the-internet-en-2026/)
- The NGI Zero Commons programme term runs 2024-01-01 to 2027-06-30 [S]. — [Inventya](https://www.inventya.com/calls/ngi-zero-commons-fund)

**EuroHPC AI Factories (EU compute)**
- Fast Lane gives up to 50,000 GPU-hours for at most 3 months, approved in about 4 working days. Large Scale covers more than 50,000 GPU-hours with two cut-offs a month and 10-working-day approval. Leonardo Booster is currently unavailable for Large Scale. Playground is "temporarily closed". Industrial Innovation access is **free for AI SMEs, including startups**. Academic and public users go through the separate "AI for Science and Collaborative EU projects" mode [P]. — [EuroHPC Fast Lane](https://www.eurohpc-ju.europa.eu/ai-factories/ai-factories-access-modes/fast-lane-access-ai-factories_en); [EuroHPC Large Scale](https://eurohpc-ju.europa.eu/large-scale-access-ai-factories_en); [Playground closed](https://www.eurohpc-ju.europa.eu/playground-access-ai-factories-temporarily-closed_en)
- An aggregator lists Large Scale cut-offs on 2026-10-15/30 and continuing allocations due 2027-01-04 [S]. — [Granted AI](https://grantedai.com/grants/eurohpc-ai-factories-european-commission-967b0f73)
- There are 19 AI Factories and 13 antennas [S]. — [EUACC](https://www.euacc.ai/programmes/ai-factories)

**France**
- France 2030's "Pionniers de l'IA" call launched in September 2025, and 28 more winners from its 2nd round were announced on 2026-06-18 [P]. — [entreprises.gouv.fr press release](https://www.entreprises.gouv.fr/files/files/presse/2026/807%20-%20CP%20-%20France%202030%2028%20nouveaux%20laur%C3%A9ats%20de%20l%E2%80%99Appel%20%C3%A0%20projets%20%C2%AB%20Pionniers%20de%20l%E2%80%99IA%20%C2%BB.pdf)
- Bpifrance plans €10B for AI by 2029 [P/S]. — [Bpifrance](https://www.bpifrance.com/2025/03/27/bpifrance-deploys-e10-billion-to-develop-the-ai-ecosystem-and-facilitate-the-adoption-of-artificial-intelligence-by-french-companies)
- The Bourse French Tech Emergence targets deeptech companies registered in France for **less than 1 year**. Its amount was not shown on the page retrieved [S]. — [les-aides.fr](https://les-aides.fr/cci_creation/aide/VCEv3w/bpifrance/bourse-french-tech-emergence.html)

**Compute programs**
- Google TPU Research Cloud gives free access to a cluster of more than 1,000 Cloud TPUs. Participants must share their work publicly and follow Google's AI Principles [P]. — [TRC about](https://sites.research.google/trc/about/)
- Google Cloud research credits are about $5k for faculty and postdocs and about $1k for PhD students [S]. — [Granted AI](https://grantedai.com/grants/google-cloud-research-credits-faculty-phd-students-nonprofit-researchers-ai-workloads-google-2026)

**Bittensor ecosystem**
- Yuma (DCG) has accelerated 20 subnets, and its 2026 cohort's market cap rose 134%. It offers capital, technical guidance and community access [S]. — [Pulse 2.0](https://pulse2.com/yuma-reaches-200-million-in-staked-assets-as-accelerator-portfolio-grows-134/)
- DSV Fund appears only as an investor in regulated subnet products, with no grant program found [S]. — same search

### Inferences (EST)
- **Best first applications, Nov 2026–Q1 2027:**
  1. EuroHPC Fast Lane, if a French SAS/SASU or micro-entreprise counts as an "AI SME" (verify eligibility). 50k GPU-hours would cover thousands of verifications and all red-team days.
  2. EF ESP, pitched as "verifiable useful-work / anti-gaming settlement research on Ethereum L2", or via the academic round if a university co-author is involved.
  3. NLnet's next call, if the Open Internet Stack scope admits it. It typically funds €5–50k milestones, but that figure is not re-verified here.
- **After a public testnet:** Optimism Retro Funding (deploy on OP Sepolia/Base to qualify) and Gitcoin rounds.
- Horizon Europe and EIC are mismatched to 1–2 part-time people because of consortium overhead and full-time expectations. This is a judgment, not sourced.
- Bpifrance BFTE requires a company less than 1 year old, which fits only if the owner incorporates for this.

### Gaps
- Not verified in this pass, so check before relying on any of them: Arbitrum grants 2026 (Questbook/DDA status); Base Builder Grants amounts; Gitcoin GG24/GG25 dates; Protocol Labs/FFDW grant status; a16z crypto CSX 2026 cohort and terms; Prime Intellect, Gensyn or Nous grant programs; Hugging Face compute grants (ZeroGPU/community grants); NVIDIA Inception credits; EIC Pathfinder/Accelerator 2027 cut-offs; Horizon Europe Cluster 4 AI calls; Bpifrance BFTE amount (historically up to about €30k, rising to about €90k for some profiles, unverified).
- EuroHPC eligibility for a sole trader, as opposed to an incorporated SME, is unclear.
- No found evidence that any 2026 funder explicitly funds "decentralized verifiable training".

## 3. Legal and regulatory (EU/France default; US notes)

### Takeaway
A no-token testnet is legally simple: points, valueless test tokens, or fiat/USDC bounties paid as contest prizes or contractor fees. An issued token triggers MiCA Title II white-paper duties unless an Art. 4(3) exemption applies, and that exemption fails if recipients must hand over personal data (KYC) or the team signals intent to list. The EU AI Act's GPAI obligations almost certainly do not bite on 124M-parameter speedrun models, which sit orders of magnitude below the 10^23 FLOP indicator. They become a selling point ("compliance-grade training logs") only for a later collaborative pre-training track.

### Cited Findings
**MiCA**
- Under Art. 4(3), offers are exempt from the white-paper duty if the crypto-assets are offered **for free**, **automatically created as a reward for DLT maintenance or transaction validation**, are utility tokens for an existing good or service, or work in a limited network. An offer is *not* free if the offeror requires **personal data** or receives fees or any benefit in exchange. Under Art. 4(4), the exemptions are **lost if the offeror communicates an intention to seek admission to trading**, with an ESMA carve-out for listing only on non-EU platforms [P/S]. — [ESMA Interactive Single Rulebook, MiCA Art. 4](https://www.esma.europa.eu/publications-and-data/interactive-single-rulebook/mica/article-4-offers-public-crypto-assets-other); [springlex MiCA Art. 4 text](https://www.springlex.eu/en/packages/mica/mica-regulation/article-4/)
- One commentary argues that blockchain addresses may themselves be personal data, which could take airdrops out of the "free" exemption [S]. — [López Kurtz, "Are airdrops actually exempt under MiCA?"](https://davidlopezkurtz.substack.com/p/guest-post-are-airdrops-actually)
- The white-paper duty covers most "other crypto-assets", including utility tokens. Utility-token offers for services that do not yet exist are capped at 12 months from white-paper publication [S]. — [Legal Bison](https://legalbison.com/blog/mica-white-paper-requirements)
- The MiCA CASP transitional period ends EU-wide on 2026-07-01, and the MiCA review consultation ran to 2026-08-31 [S]. — [Salvus Funds roadmap](https://salvusfunds.com/?p=21823)

**Tax and reporting**
- DAC8 applies from 2026-01-01. CASPs must collect TINs and identities and report transfers, including withdrawals to self-custody. Sources disagree on whether first reports are due 2027-01-31 or the first exchange happens by 2027-09-30 [S]. — [Mondaq DAC8](https://www.mondaq.com/tax-authorities/1730346/dac8-and-the-eu-framework-for-crypto-asset-tax-transparency); [Whale Alert summary](https://whale-alert.io/stories/a17705a51a49/EUs-DAC8-from-Jan-1-2026-forces-crypto-platforms-to-report-identities-TINs-and-withdrawals-to-selfcustody-addresses)

**US token classification**
- The CLARITY Act failed cloture 49–50 on 2026-09-15 (from the earlier report), so US token classification remains unsettled. — [DLA Piper](https://www.dlapiper.com/en/insights/publications/2026/09/senate-fails-to-advance-the-clarity-act)

**EU AI Act (GPAI)**
- Art. 53 obligations apply to all GPAI providers from 2025-08-02. They cover technical documentation, information for downstream providers, a **copyright policy**, and a **public training-content summary using the Commission template** (published 2025-07-24). **Commission enforcement powers start 2026-08-02.** The Code of Practice is voluntary and has Transparency, Copyright and Safety & Security chapters [S, law-firm]. — [Mayer Brown 2025-08](https://www.mayerbrown.com/ja/insights/publications/2025/08/eu-ai-act-news-rules-on-general-purpose-ai-start-applying-guidelines-and-template-for-summary-of-training-data-finalized); [artificialintelligenceact.eu GPAI guidelines overview](https://artificialintelligenceact.eu/gpai-guidelines-overview/)
- Thresholds and exemptions:
  - The GPAI indicator is **10^23 training FLOP**, raised from 10^22 in the draft.
  - Systemic risk starts at 10^25 FLOP.
  - Downstream modifiers use one-third of those thresholds.
  - The open-source exemption is partial: the copyright policy and training summary are still required, and the exemption is lost if the model is monetised [S]. — same sources; [Arnold & Porter 2025-08](https://www.arnoldporter.com/en/perspectives/advisories/2025/08/does-your-company-have-eu-ai-act-compliance-obligations)

### Inferences (EST)
- **GPAI scope (EST).** A 124M model trained on about 1–3B tokens uses about 6·N·D ≈ 10^18–10^19 FLOP, 4–5 orders of magnitude below 10^23. Speedrun and autoresearch models are not GPAI models, and the project has no Art. 53 duties for them. A nanochat d26 (about $300 of compute) is also far below the line.
  - Collaborative pre-training of about 1B+ models on 100B+ tokens approaches 10^21. A Covenant-class 72B run is about 5×10^23, which is in scope.
  - Opportunity: the protocol's commitments (data shard seeds, dataset hashes, per-step roots) map directly onto the training-content summary and copyright-policy evidence. Offer a "compliance export" as a differentiator for the later track.
- **No-token designs (EST, not legal advice).**
  - Points and valueless testnet tokens with no stated listing intent are the cleanest option: no MiCA offer, no CASP role.
  - Paying USDC bounties is paying with an existing e-money token, not issuing a crypto-asset, so MiCA issuer duties do not apply. The payer still has ordinary obligations: invoices or prize terms, contractor tax treatment, and sanctions screening.
  - Paying in fiat via a platform that already does KYC and payouts (e.g., Open Collective, Gitcoin, or a bounty platform) offloads most of the compliance work.
  - Any future token minted as a "reward for validation" might use the Art. 4(3)(b) exemption. Requiring KYC and announcing a listing would both erode it, so budget €20–60k (EST, unsourced) for a MiCA white paper and counsel if a token ever launches.
- **Sanctions and KYC (EST).** EU and US sanctions law bars payments to listed persons and regions regardless of size. A minimal bounty program needs name/country declarations, sanctions-list screening for payees above a threshold, and geo-exclusion of comprehensively sanctioned jurisdictions. Payees' exchanges will report under DAC8.
- **Data licensing (EST, unverified this pass).** FineWeb and FineWeb-Edu are generally distributed under ODC-By with Common Crawl terms of use. Attribution requirements and opt-out handling should go into the task spec, and the AI Act copyright policy becomes relevant only for the GPAI-scale track.

### Gaps
- The exact current ESMA Q&A wording on airdrops and "free" offers was not retrieved, and the EUR-Lex Art. 4(3) full text was not fetched directly; ESMA rulebook and springlex pages are linked.
- The FineWeb, FineWeb-Edu and DCLM licence texts were not fetched in this pass.
- French specifics were not researched: AMF PSAN/CASP regime post-MiCA, URSSAF/BNC treatment of bounty income, and the legal status of prize contests (jeux-concours) for skill-based contests.
- Whether the Nov 2025 EU "Digital Omnibus" changed GPAI timelines was not checked.
- Practical OFAC/EU screening tools and their costs were not researched.

## 4. Publication paths and 2027 deadlines

### Takeaway
Most crypto and security deadlines for 2027 venues have passed or are too close: FC'27 (17 Sep 2026), ICLR 2027 (25 Sep 2026), MLSys 2027 (30 Oct 2026), and probably S&P 2027 (about 10–17 Nov 2026). For a team that starts in November 2026, the realistic first targets are:
1. an arXiv/ePrint preprint plus open artifact around month 3 (Feb 2027);
2. **NeurIPS 2027** (projected mid-May 2027), main or Datasets & Benchmarks track, or **AFT 2027** (likely about May 2027 by pattern), for the full protocol and threat model;
3. **ICML 2027 workshops** (summer 2027) for an early version;
4. FC'28 (about Sep 2027) or USENIX Security '28 cycles for the security-hardened version.

USENIX Security '27 cycle 2 (26 Jan 2027) is possible only if the system already exists.

### Cited Findings
**Crypto and security venues**
- **FC'27** [P]: papers were due 17 Sep 2026 ("firm"), with notification 5 Nov 2026 and pre-proceedings 22 Dec 2026. The conference is 8–12 Feb 2027 in Barbados. Workshop proposals were due 1 Sep 2026. Page limits are 15 pages regular, 8 short and 20 SoK, plus references. — [FC27 CFP](https://fc27.ifca.ai/cfp.html)
- **AFT 2026** [P]: abstracts were due 20 May 2026 and papers 27 May 2026, and the conference ran 6–9 Oct 2026 at LSE. No AFT 2027 call was found. — [AFT26 CFP](https://aft.ifca.ai/aft26/CFP.html)
- **USENIX Security '27** (11–13 Aug 2027, Denver) [P]:
  - Cycle 1: registration 18 Aug 2026, papers 25 Aug 2026.
  - **Cycle 2: registration 19 Jan 2027, papers 26 Jan 2027, artifacts 29 Jan 2027**, notification 6 May 2027.
  - A 13-page body limit applies, and an **"Open Science" appendix is mandatory**.
  - — [USENIX Sec '27 CFP](https://www.usenix.org/node/321195); [CFP PDF](https://www.usenix.org/sites/default/files/sec27_cfp-070826.pdf)
- **IEEE S&P 2027** (Montreal, about 18 May 2027): trackers list a deadline of 10 or 17 Nov 2026, unconfirmed and in conflict, with notification about 5 Mar 2027 [S]. — [sec-deadlines](https://sec-deadlines.github.io); [PaperPilot](https://www.getpaperpilot.com/deadlines/s-p-2027.html); official site [sp2027.ieee-security.org](https://sp2027.ieee-security.org/cfposters.html)
- **ACM CCS 2027**: no paper call was found, only the hosting-proposal page [P]. — [SIGSAC](https://sigsac.org/proposal/ccs.html)

**ML venues**
- **ICLR 2027** [P]: abstracts were due 18 Sep 2026 and papers 25 Sep 2026, and both have passed. Reviews are released 5 Nov 2026, and the conference is 26–30 Apr 2027. New rules include an AI-use statement and a cap of 20 papers per author. — [ICLR 2027 dates](https://iclr.cc/Conferences/2027/Dates); [AI Weekly](https://aiweekly.co/alerts/iclr-2027-caps-authors-at-20-papers-mandates-ai-use-statement)
- **MLSys 2027** [P]: papers were due 30 Oct 2026, which has passed. The conference is 21–25 Jun 2027 in Bellevue. — [mlsys.org](https://mlsys.org); [mldeadlines](https://mldeadlines.com/conference/mlsys-2027/)
- **ICML 2027**: no official call yet. Projections put abstracts at about 16 Jan 2027 and papers at about 22–29 Jan 2027 [S]. — [OpenCurious](https://www.opencurious.com/ai-conference-deadlines/icml-2027)
- **NeurIPS 2027**: no official call yet. Projections put abstracts at about 14 May 2027 and papers at about 15–21 May 2027, with the conference possibly in Europe in Dec 2027 [S]. — [OpenCurious](https://www.opencurious.com/ai-conference-deadlines/neurips-2027); [Bibby](https://trybibby.com/conference-deadlines/may-2027)

**Closest published analogue**
- METR's April 2026 note on AI R&D progress via NanoGPT counts four speedrun records crediting an AI agent with a human co-contributor, all "shallow-to-moderate". This is a likely related-work anchor. — [METR note 2026-04-21](https://metr.org/notes/2026-04-21-ai-rd-nanogpt-progress/)

### Inferences (EST)
- **Best fit by contribution:**
  - The protocol, threat model and security-budget answer to the SoK fit AFT, FC or USENIX Security (systems security).
  - The "verifiable autoresearch market" fits as a benchmark/dataset plus a study of agent gaming under a frozen verifier and incentives. That suits NeurIPS Datasets & Benchmarks, or ICML/NeurIPS workshops on agents, AI for science or decentralized ML.
  - The cleanest split is two papers: a security/protocol paper and a benchmark/empirical paper.
- **Artifact expectations:** USENIX requires an Open Science appendix, with artifacts due 3 days after papers. Security artifact-evaluation committees expect a container, scripts reproducing the key tables, and modest hardware. Design the reproduction around RTX 5090/H100-hour budgets of at most $50, with seeds and pinned containers, from day one.
- **Preprints:** Post to IACR ePrint for the protocol and arXiv cs.CR/cs.LG for the benchmark at about month 3. Preprints are allowed at all the above venues.

### Gaps
- Not found: official S&P 2027 deadlines, CCS 2027 deadlines (historically two cycles, about January and April), NDSS 2027 or 2028 deadlines, AFT 2027 dates, and FC'27 workshop deadlines (e.g., WTSC, DeFi, which usually run Nov–Jan).
- ICML and NeurIPS 2027 dates are projections.

## 5. Team/time constraints with 2026 coding agents

### Takeaway
Rigorous evidence on agentic-coding speedups in 2026 is weak and contested. METR's 2026 follow-up gives confidence intervals that straddle zero, and METR itself flags its design as unreliable. Agents are, however, demonstrably good at tuning and stacking known methods. For an 8–10 h/week owner, 3 months is about 100–130 hours. Plan Phase 0 plus Phase 1 (testnet, frozen verifier, one task) and a preprint, not the dispute layer.

### Cited Findings
- **METR, Feb 2026 follow-up** [S; METR's own post not reached]:
  - 57 developers, 800+ tasks and 143 repositories.
  - Reported results are in conflict. One source gives −18% for returning developers and −4% for new ones. Another gives 18% faster with a CI from 38% faster to 9% slower, and 4% faster for new recruits. Either way the intervals straddle zero.
  - METR says the 2025 design "can't be reliably replicated" now that AI use is ubiquitous, and developers declined to work without AI.
  - In the original 2025 study, developers expected a 24% speedup, perceived 20%, and were measured 19% slower.
  - — [dev.to summary](https://dev.to/vibehackers/ai-coding-tools-and-productivity-what-the-controlled-evidence-shows-1emf); [engineered.at](https://engineered.at/articles/metr-s-developer-productivity-research-2026-update); [codercops](https://blog.codercops.com/blog/ai-coding-productivity-2x-not-10x-metr-2026)
- **Research-capability evidence** [P/S]:
  - Prime Intellect: agents "mostly stacked and tuned known methods", winning on steps but producing no new optimizer. — [Prime Intellect](https://primeintellect.ai/blog/measuring-autonomous-research); [StartupHub](https://www.startuphub.ai/news/agents-beat-humans-on-speedruns-still-can-t-invent)
  - Intology's NanoGPT-Bench (May 2026) found Codex, Claude Code and autoresearch recovered only 9.3% of human progress, mostly through hyperparameter tuning [S]. — [benchmarklist NanoGPT-Bench](https://benchmarklist.com/benchmarks/nanogpt_bench/)
- **Contract-security cost anchors**: see §1 audit pricing.

### Inferences (EST)
- **Realistic 3-month solo output (about 110 h, EST):**
  - Weeks 1–2: CI green, legacy branch, PoC regression tests.
  - Weeks 3–8: port Prime Intellect's harness to a 1-GPU 5-minute task with a frozen `verify.py` (8 seeds, pinned container), plus a Submission/Escrow contract on Base Sepolia (about 300–500 LOC with Foundry invariants) and a single validator service.
  - Weeks 9–12: an internal red-team with 3–5 known gaming attacks, a public leaderboard, and the preprint.
  - **Not feasible in 3 months part-time (EST):** bisection disputes, referee replay, lineage royalties, a second validator operator.
- **Agent risk for contracts:** agents speed up boilerplate and tests but should not be trusted on economic logic such as escrow accounting or challenge timing. Mitigate with invariant fuzzing, a small codebase, valueless testnet assets, and one paid 1-week review before any real value ($6k-class, §1).
- **Second person:** the highest-leverage hire or collaborator is an academic co-author (PhD student or postdoc). That unlocks ESP academic grants, the EuroHPC AI-for-Science mode, TRC and venue know-how.

### Gaps
- No 2026 RCT specifically on solo greenfield projects or Solidity with agents was found.
- METR's primary 2026 post was not retrieved.
- No data was found on AI-written contract exploit rates.

## 6. Miner and participant acquisition benchmarks

### Takeaway
Participation in verified ML contests comes either from sustained cash payouts (Numerai pays about $180–530k/month to a few hundred staked accounts) or from prestige plus a public leaderboard (the nanoGPT speedrun and Karpathy's autoresearch, which drew 66k+ GitHub stars in a month with no prize). Bittensor emissions do not guarantee real miners: more than half of subnets burned 99%+ of incentives in April 2026. A small team should lean on prestige and leaderboards, with a modest USDC pool. No data on minimum prize pools was found.

### Cited Findings
- **Numerai** [S]:
  - A late-May 2026 snapshot showed about 870k NMR staked, more than 5,000 staked models and about 600 staked accounts.
  - Monthly payouts are typically $180k–530k, and $182,039 was paid in January 2026.
  - On-chain staking, including a USDC staking option, was slated for 2026-07-04.
  - — [Numerai blog](https://blog.numer.ai/numerai-monthly-numercon-agents-staking-risk-1m-nmr-buyback/); [Numerai docs](https://docs.numer.ai/)
- **Autoresearch** [S]: 66k+ stars in a month, and one 700-experiment run found 20 improvements (from the earlier report). — [Fortune](https://fortune.com/2026/03/17/andrej-karpathy-loop-autonomous-ai-agents-future/)
- **NanoGPT speedrun records**: four records from late 2025 to early 2026 credit an AI agent with a human co-contributor [P]. — [METR](https://metr.org/notes/2026-04-21-ai-rd-nanogpt-progress/)
- **Prime Intellect speedrun study** [P]: 153 runs over 18 models. Participants were labs' models run by Prime Intellect itself, not external miners. — [Prime Intellect](https://primeintellect.ai/blog/measuring-autonomous-research)
- **Bittensor**: 67 of 128 subnets were burning 99%+ of incentives in April 2026 [S]. — [FalconX](https://falconx.io/newsroom/state-of-bittensor-subnet-adoption-trends-network-mechanics-and-covenants-departure)
- **Templar**: it bootstrapped 70+ peers for Covenant-72B only with Bittensor emissions and an 8×B200-per-peer barrier, and its protocol is now inactive (from the earlier report). — [arXiv 2603.08163](https://arxiv.org/html/2603.08163v2); [one-covenant/templar](https://github.com/one-covenant/templar)
- **Autoresearch bounties**: no 2026 crypto-paid autoresearch bounty or prize pool was found. The closest are the AgentX–AgentBeats competition (Mar 2026) and a concept page with no live program. — [Berkeley RDI](https://berkeleyrdi.substack.com/p/agentic-ai-weekly-berkeley-rdi-march-629); [openresearchh](https://openresearchh.vercel.app/)

### Inferences (EST)
- **Bootstrap plan (EST):**
  1. Seed the leaderboard with the team's own agent runs (about $20–60 GPU plus $50–250 tokens per agent-day, §1) so it is never empty.
  2. Pitch the task to modded-nanogpt, autoresearch and Prime Intellect communities, since it is the first leaderboard with cheat-resistant, independently verified 8-seed acceptance.
  3. Fund a pool of $2–10k in USDC or fiat via a grant, e.g., $500–1,000 per verified record, plus small lineage royalties.
  4. Invite labs to run their agents, framed as a benchmark-for-agents that produces paper co-authorship.
- **Kill-criterion calibration:** the earlier report's kill criterion is "no outside verified improvement within 2 months". Given Numerai's scale requires sustained six-figure payouts, success should be judged as at least 5–10 external submitters and at least 1 accepted record, not as miner counts.

### Gaps
- No data on Kaggle 2026 prize pools versus participant counts.
- No published minimum prize threshold that reliably draws ML participants.
- No numbers on Prime Intellect, Gensyn or Nous community bounty programs.
- No figures on the participant funnel for IOTA SN9 "Train at Home".
