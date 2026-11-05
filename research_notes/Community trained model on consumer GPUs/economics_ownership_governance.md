# People's datacenter on consumer GPUs: contributor economics, remuneration, ownership, governance and EU legal options (as of 2026-11-05)

Conventions:
- [P] means a primary or official source. [S] means a secondary source such as press, a blog or an aggregator.
- EST means my own estimate or arithmetic. "Background" means general knowledge that was not re-verified this session.
- Nothing here is legal advice. Legal points are flagged with their uncertainty.
- Earlier notes are not repeated here: the MiCA Art. 4(3) exemptions, DAC8, the grants stack (NLnet, EuroHPC Fast Lane, ESP) and the Bittensor/Gensyn/Pluralis landscape are in `DPoDL prior art and viability plan/viability_constraints.md` and `DPoDL revival research November 2026/protocols_incentives.md`.

---

## 1. Contributor unit economics: electricity cost vs rental value vs what networks actually pay

### Takeaway
At late-2026 prices, the electricity for a 4090 at training load costs about:
- €0.09–0.11/h in France on the regulated tariff;
- about €0.20/h in Germany;
- about $0.10/h in the US (all EST).

Marketplace rental for the same card clears at only about $0.31–0.52/h gross, before platform fees and idle time.

So contributing is clearly net-positive only in cheap-power countries. In Germany it is roughly break-even at Salad-style rates.

A people's model should pay a floor of about €0.12–0.25 per verified 4090-hour, set by country. That covers power plus a margin. Equity, credits or ownership can then sit on top of it.

### Cited Findings
**Electricity prices (2026)**
- EU household average price (all taxes) for S1 2026 was €0.2832/kWh. The highest were Ireland at €0.3871 and Germany at €0.3618, and the lowest was Hungary at €0.1139. The Eurostat article was updated around 2026-10-30 [P]. — [Eurostat, Electricity price statistics](https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Electricity_price_statistics)
  - The EU average fell about 2.2% from €0.29 in H2 2025 [S]. — [WAM](https://www.wam.ae/en/article/c30qh52-household-gas-electricity-prices-decrease-first)
- France's regulated EDF Tarif Bleu from 2026-08-01 (CRE délibération 2026-147, 2026-07-15), Base option at 3–6 kVA, is €0.2001/kWh TTC, up from €0.1940 (+3.14%). Other options [S]:
  - HP/HC at 6 kVA: €0.2142 peak / €0.1589 off-peak.
  - Tempo: €0.1356 (blue off-peak) to €0.7295 (red peak).
  - Subscription: €190.32/yr at 6 kVA.
  - Sources: [Kelwatt](https://www.kelwatt.fr/actu/tarif-edf-reglemente-1er-aout-2026); [Selectra](https://selectra.info/energie/actualites/marche/nouveaux-prix-electricite-tarif-bleu-1er-aout-2026)
- Spain H1 2026 is about €0.21/kWh (France €0.22), Eurostat band DC as relayed by a secondary site. UNVERIFIED: the Eurostat page retrieved did not list these countries [S]. — [euenergy.live](https://euenergy.live/articles/average-electricity-bill-europe)
- The US residential average forecast for 2026 is 18.2¢/kWh (EIA STEO). Monthly figures run 18.3–18.8¢, e.g. 18.83¢ in April 2026, +7.3% YoY [P/S]. — [EIA STEO](https://www.eia.gov/outlooks/steo/report/elec_coal_renew.php?sfnsn=mo); [Newsweek citing EIA](https://www.newsweek.com/map-electricity-prices-each-state-trump-deadline-passes-12222810)

**GPU power**
- Rated board power: RTX 3090 350 W, RTX 4090 450 W [S]. — [Lambda benchmark](https://lambda.ai/blog/nvidia-rtx-4090-vs-rtx-3090-deep-learning-benchmark)
- RTX 5090: 575 W, which is 28% above the 4090 [S]. — [Tom's Hardware](https://www.tomshardware.com/pc-components/gpus/leakers-revise-rtx-5090-and-rtx-5080-power-draw-to-575w-and-360w-respectively-up-to-27-percent-higher-than-last-generation-rtx-40-gpus); [Notebookcheck](https://www.notebookcheck.net/RTX-5090-vs-RTX-4090-tested-at-same-power-level-RTX-50-flagship-shows-efficiency-downgrade-vs-previous-gen.952084.0.html)
- Lambda found 4090 training throughput per watt at 0.92–1.5× the 3090 [S]. — [Lambda](https://lambda.ai/blog/nvidia-rtx-4090-vs-rtx-3090-deep-learning-benchmark)
- I found no measured wall-power figure for these cards under training load. This is a gap.

**Rental market value (what a renter pays)**

RTX 4090 on Vast.ai:
- Cheapest $0.36/h, and an A100 at $0.34 (Activepieces citing AI Compute Radar, Nov 2026).
- Vast median snapshots: $0.39–0.40.
- A June 2026 tracker: median $0.52, interruptible about $0.18–0.25.
- computeprices: from $0.309 (2026-08-05).
- [S]: [Activepieces](https://www.activepieces.com/blog/vast-ai-gpu-pricing-per-hour-in-2026-and-extra-fees.md); [Vast pricing snapshot](https://vast.ai/oldpricing); [computeprices](https://computeprices.com/providers/vast/gpus/rtx4090)

RTX 5090:
- Vast.ai: cheapest about $0.32–0.45, median about $0.60–0.63 [S]. — [Beam](https://www.beam.cloud/blog/nvidia-rtx-5090-pricing); [TechRadar](https://www.techradar.com/pro/security/you-can-now-rent-a-usd3000-nvidia-rtx-5090-gpu-from-just-usd0-25-hour-when-you-need-it-for-as-long-as-you-need-it); [computeprices](https://computeprices.com/providers/vast/gpus/rtx5090)
- SaladCloud: from $0.25 [S]. — [computeprices Salad 5090](https://computeprices.com/providers/salad/gpus/rtx5090)

RunPod RTX 4090: from $0.69/h [S, cited by Nosana 2026-05-06]. Nosana's own comparison lists a 3060 at $0.048/h and a 3080 at $0.096/h. — [Nosana blog](https://nosana.com/blog/cloud-gpu-providers-compared)

SaladCloud (customer side):
- Tiers as of 2026-09-12: High priority $0.330/h, Batch $0.160/h [S]. — [Spheron](https://www.spheron.network/blog/saladcloud-pricing-2026-gpu-cost-vs-spheron/)
- From 2026-11-01, the High-priority RTX 5090 rate rose 20% to $0.60/h. The Lowest tier was unchanged [S]. — [PricingSaaS diff 2026W45](https://pricingsaas.com/companies/salad/diffs/2026W45)

H100 benchmark:
- About $1.60–4.50 per GPU-hour on specialist clouds [S]:
  - Lium from about $1.60 (2026-10-28);
  - Vast H100 SXM $2.14;
  - Lambda $3.99;
  - Nebius $4.50 from 2026-10-01;
  - hyperscalers about $7–12.
- Sources: [IntuitionLabs 2026-10-11](https://intuitionlabs.ai/articles/h100-rental-prices-cloud-comparison); [tech-insider](https://tech-insider.org/what-renting-an-nvidia-h100-costs-per-hour-in-2026-and-when-renting-beats-buying/)

**What consumer networks actually pay contributors**
- **Salad (consumer "Chefs")** [P]:
  - Earnings are "Salad Balance". The page says "your PC is not creating or accruing actual currency".
  - It is redeemed for PayPal cash, crypto (RENDER etc.), prepaid cards, gift cards, games or charity.
  - Published rates are 7-day averages that include idle time ("chopping" hours with or without a job). Only machines averaging 4 h/day or more are included.
  - The tables did not render in my fetch, so per-GPU host rates are a gap.
  - Sources: [salad.com/download-high-end](https://salad.com/download-high-end); [salad.com/earning-rates](https://salad.com/earning-rates)
  - An anecdotal blog estimate (unsourced, treat as weak): 3080/4070 about $10–40/month, a 4090 in a cheap-power area "$100+/month" [S]. — [Medium](https://medium.com/@simon.swartout/can-salad-com-make-money-on-an-idle-gaming-pc-my-honest-setup-earnings-logic-and-tips-51d8a6d6993e)
- **io.net**:
  - The "Incentive Dynamic Engine" pays suppliers a stable USD amount rather than a token amount. Shortfalls are covered from reserves and, if needed, by new token issuance.
  - Self-reported network earnings rose from about $250k/month (Mar 2026) to about $1M/month (May 2026), a run rate of about $12M (Jun 2026).
  - IO trades about 96% below its June 2024 peak.
  - [S]: [CoinDesk research](https://coindesk.com/research/the-incentive-dynamic-engine-a-new-era-for-io-net-tokenomics); [Solana Compass](https://solanacompass.com/projects/ionet)
- **Nosana**: there is no public per-4090 payout figure. Hosts see NOS earnings in a dashboard. Total network earnings were "$2M+" by end-2025 [P]. — [Nosana 2025 review](https://nosana.com/blog/2025-at-nosana-a-year-in-review); [Nosana host docs](https://docs.nosana.com/hosts/grid.html)
- **Grass (bandwidth)**:
  - Points are based on uptime and bandwidth, weighted by regional demand.
  - Reported about $33M annualized USDC revenue in 2025 and about $17M in H1 2026. Management projects $65–75M for 2026 (unverified company claims).
  - Season 2 rewards are paid in USDC rather than newly minted tokens, with claims from 2026-07-22.
  - A 2026-07-07 governance vote routes a share of USDC revenue to GRASS stakers.
  - There is no reliable per-user earnings figure.
  - [S]: [hokanews](https://www.hokanews.com/2026/07/grass-reveals-season-2-claim-date-as.html); [stakin](https://stakin.com/blog/grass-rewards-and-token-utility-explained); [weusecoins](https://www.weusecoins.com/what-is-grass/)
- **Bittensor**:
  - The first halving in Dec 2025 cut emissions from 7,200 to 3,600 TAO/day.
  - Under dTAO, subnet emissions split 41/41/18 between miners, validators and the subnet owner.
  - Headlines warn that about $52M in subsidies outpace organic revenue.
  - I found no reliable consumer-GPU miner profitability figure [S]. — [OnFinality](https://blog.onfinality.io/bittensor-halving/); [KuCoin news](https://www.kucoin.com/news/flash/bittensor-faces-valuation-risk-as-52m-subsidies-outpace-organic-revenue)

### Inferences
**Wall-power assumption (EST).** Training draw at the wall is the GPU plus about 100 W for the platform and PSU losses:
- 3090 ≈ 0.45 kW;
- 4090 ≈ 0.55 kW;
- 5090 ≈ 0.70 kW.

Power-limiting a card to about 70% typically costs about 10–15% throughput. That is background knowledge, not verified.

**Electricity cost per GPU-hour (EST).**

| €/kWh → | FR TRV HC 0.159 | FR TRV Base 0.200 | ES ~0.21 (unverified) | EU avg 0.283 | DE 0.362 | US $0.182 |
|---|---|---|---|---|---|---|
| 3090 (0.45 kW) | €0.07 | €0.09 | €0.09 | €0.13 | €0.16 | $0.08 |
| 4090 (0.55 kW) | €0.09 | €0.11 | €0.12 | €0.16 | €0.20 | $0.10 |
| 5090 (0.70 kW) | €0.11 | €0.14 | €0.15 | €0.20 | €0.25 | $0.13 |

Running 24/7 for 720 h a month, a 4090 costs about €79 in France, €143 in Germany and $72 in the US.

**Net margin (EST).** Assume a gross market value of about $0.31–0.52/h for a 4090 and about 25% platform take. That take rate is my assumption: Vast's host fee was not verified this session. Assume utilization of 50–70%.
- Expected host revenue is about $0.12–0.27 per powered hour.
- In France that is net-positive, at about +€0–0.15/h.
- In Germany it is break-even to negative, unless the GPU idles at low power when it has no job.
- This matches the anecdotal "$100+/month only in cheap-power areas".

**Pay floor for the people's model (EST).** To be attractive, pay per verified GPU-hour at least electricity × about 1.3–1.5, plus a wear margin:
- 3090: €0.10–0.20;
- 4090: €0.12–0.25;
- 5090: €0.16–0.32.

The lower end of each range is for France/Spain, the upper end for Germany.

Paying a flat EU-wide rate at the German level overpays French contributors by about 2×. Paying country-indexed "electricity-plus" is fairer but more complex. An alternative is to pay a flat €/kWh-equivalent from a declared wattage, verified by measured throughput.

**What it costs to train a model (EST).**
- Assumptions: about 20% realized MFU over consumer links, and a 4090 at about 165 dense BF16 TFLOPS (background spec), giving about 33 TFLOPS effective ≈ 1.2×10^17 FLOP/h.
- A 10^23 FLOP run, which is the AI Act GPAI indicator and roughly a 1B model on about 16T tokens, needs about 0.85M 4090-hours:
  - at €0.15/h, about €125k of payouts;
  - at €0.25/h, about €210k;
  - about 470 MWh of energy.
- A 10^24 FLOP run (about 7–8B params at about 20T tokens) is about 8.5M GPU-hours, i.e. €1.3–2.1M.
- A 10^25 run is out of reach at about €13–21M.
- Compare H100s at about $2/h with about 40% MFU on about 990 TFLOPS: 10^23 FLOP needs about 70k H100-h, or about $140k.

So consumer GPUs are cost-competitive only if they are paid near electricity cost. A people's datacenter is economically justified by ownership and legitimacy, not by cheaper FLOPs.

**Retention.** Salad's "4 h/day" inclusion threshold and its idle-time averaging show that payout per powered hour is what contributors feel. Publish expected € per powered hour net of electricity, not "up to" job rates.

### Gaps
- Per-GPU Salad host payouts. The tables rendered empty in the fetch, so they need a manual check of salad.com/earning-rates.
- Vast.ai's host fee percentage and real host utilization.
- Measured training wall-power for 3090/4090/5090.
- Verified Eurostat S1 2026 figures for France and Spain. Use dataset nrg_pc_204.
- Bittensor consumer-GPU miner returns. Taostats was not checked.
- The EUR/USD rate was not sourced. Conversions assume about 1.15–1.17 (EST).

---

## 2. Remuneration designs: what worked and what failed; who ultimately pays

### Takeaway
Pure token emissions have failed as a durable pay mechanism in 2024–2026:
- IO is about 96% off its peak and AKT about 90% (see prior notes);
- Helium's market cap fell about 81% YoY despite revenue growth;
- Bittensor's subsidies exceed its organic revenue.

The 2025–2026 trend is toward revenue-backed, stable-value payouts. Grass now pays rewards in USDC, io.net pays suppliers USD-stable amounts, and Helium burns 100% of mobile revenue.

For a people's model, the robust pattern has three layers:
1. stable fiat/stablecoin pay for verified compute, from grants or customer revenue;
2. non-transferable contribution records that convert into membership, governance and inference credits;
3. optional upside through cooperative patronage or revenue rebates, not a tradable profit token.

Volunteer-only (Folding@home/BOINC) works for mission-driven science but churns heavily.

### Cited Findings
- **Pluralis "Protocol Learning"** [P, 2025-03]:
  - "Training participants must have a way to profit from their contribution."
  - It proposes "incentivizing contribution via ownership of the resulting model" through "partial model ownership".
  - Value capture relies on unextractable weights: "no participant can ever obtain a full weight set", which "allows programmatic value flow" of usage revenue to contributors.
  - Sources: [Pluralis, A Third Path](https://pluralis.ai/blog/a-third-path-protocol-learning/)
  - Funding was an equity seed ($7.6M) with a warrant for a future token [S, 2025-03-19]. — [Fortune](https://fortune.com/crypto/2025/03/19/pluralis-research-7-6-million-openai-coinfund-union-square-ventures)
  - I found no public contributor ownership percentage or payout data as of 2026-11.
- **Helium (DePIN lessons)**:
  - HIP 138 ended IOT/MOBILE emissions in Jan 2025.
  - HIP 147 reallocates up to 60% of emissions to data rewards, i.e. usage over coverage-gaming.
  - In Aug 2025 Helium decided to burn HNT equal to 100% of Helium Mobile subscriber revenue.
  - Annualized revenue was about $18.3M in Q3 2025 and about $20M in Dec 2025. Subscribers rose from about 461.5k to about 602k.
  - The market cap was down about 81% YoY despite this.
  - [S]: [Sarson Funds](https://sarsonfunds.com/depins-leading-edge-why-heliums-growth-metrics-demand-attention/); [blockeden](https://blockeden.xyz/blog/2026/02/26/helium-burn-mint-equilibrium-depin-wireless/); [FalconX](https://www.falconx.io/newsroom/the-3-depin-protocols-seeing-record-activity)
  - Sources conflict on mobile's share of burns: about 10% (Messari, early 2025) versus "nearly all" (Oct 2025).
- **Grass**: moved from token airdrops to USDC rewards in Season 2 (2026). A revenue-share to stakers was voted on 2026-07-07 [S]. — [hokanews](https://www.hokanews.com/2026/07/grass-reveals-season-2-claim-date-as.html); [stakin](https://stakin.com/blog/grass-rewards-and-token-utility-explained)
- **io.net**: USD-stable supplier pay via the IDE, backstopped by reserves and token issuance [S]. — [CoinDesk research](https://coindesk.com/research/the-incentive-dynamic-engine-a-new-era-for-io-net-tokenomics)
- **Numerai**:
  - Staking is skin-in-the-game: positive scores earn NMR and negative scores burn the stake. Unstaked models get no payout and no weight in the meta-model [P]. — [Numerai docs](https://docs.numer.ai/numerai-tournament/staking)
  - 2026: stakes moved back on-chain ("Atomic Blockchain Staking", from Aug 2026), plus a $1M NMR buyback [P]. — [Numerai blog](https://blog.numer.ai/numerai-monthly-numercon-agents-staking-risk-1m-nmr-buyback/)
  - About 870k NMR were staked across more than 5,000 models (third-party, May 2026; figures conflict) [S]. — [securities.io](https://www.securities.io/investing-in-numeraire-nmr-everything-you-need-to-know/)
- **Volunteer computing**:
  - Main motives are a desire to help science, recognition, and feeling useful [S/academic]. — [Nov et al. via ICWSM](https://ojs.aaai.org/index.php/ICWSM/article/download/14113/13962); [MalariaControl.net study](https://ictlogy.net/works/reports/projects.php?idp=1484)
  - Folding@home also attracts hardware enthusiasts and overclockers (Curtis 2018). — [Citizen Science: Theory & Practice](https://theoryandpractice.citizenscienceassociation.org/article/10.5334/cstp.109)
  - Churn: by April 2010, about 5 in 6 registered BOINC volunteers no longer participated (Darch & Carusi 2010). — [Darch & Carusi PDF](https://www.dhi.ac.uk/san/waysofbeing/data/health-jones-darch-2010.pdf)
- **Public-interest model funding is grant/government-driven**:
  - Apertus, the Swiss public model, was released 2025-09-02 in 8B and 70B sizes, with weights, data and recipes open, under Apache 2.0. One outlet cites a custom AUP, so check the HF card. It was built by EPFL, ETH Zurich and CSCS. Apertus 1.5 has since been released [P/S]. — [swiss-ai.org/apertus](https://www.swiss-ai.org/apertus); [itsfoss](https://itsfoss.com/news/apertus/); [EPFL Apertus 1.5](https://ai.epfl.ch/?p=18637)
  - Serving is done by the nonprofit Public AI Inference Utility (Metagov-supported, government and corporate donors). It serves Apertus and SEA-LION. Access through HF Inference Providers is free "at the time of writing", with pricing subject to change [P]. — [publicai.co/utility](https://publicai.co/utility); [HF blog](https://huggingface.co/blog/inference-providers-publicai)

### Inferences
**Comparison of designs (EST judgment, based on the evidence above):**

| Design | Contributor appeal | Sustainability | EU legal load | Verdict |
|---|---|---|---|---|
| Emission token (Bittensor-style) | High at launch, collapses with price | Poor; subsidy exceeds revenue | MiCA white paper unless Art. 4(3)(b) mining-reward exemption; CASP for any exchange role | Avoid for MVP |
| Points → later token conversion | Strong speculative pull (Grass S1) | Defers the problem; disappointment risk | Points are low-risk; a promised conversion may pull the scheme into MiCA as an "offer" (uncertain) | Use points only as non-transferable reputation; don't promise a token |
| Stable pay (EUR/USDC) per verified GPU-hour | Predictable; covers electricity | Needs a payer (grant or revenue) | Payments are income to individuals (tax, see §4); no MiCA issuer duty for paying in an existing EMT | Core of every package |
| Revenue share from API sales via token | Attractive | Revenue small for a 1–8B model | Profit rights ⇒ likely a transferable security (MiFID II, prospectus) | Only via legal equity or coop shares |
| Fractional model ownership (Pluralis) | Strong narrative | Requires unextractable weights, which conflicts with open weights | Securities if transferable | Research-grade; not for an open-weights mission |
| Inference credits ∝ contribution | Moderate (usable, non-speculative) | Cost is the serving GPU-hours | Non-transferable credits are likely outside MiCA (uncertain) | Good secondary reward |
| Coop membership + patronage rebate | Moderate; strong for the mission-driven | Tied to real surplus | Coop-law governed; shares not freely transferable | Best for "people-owned" |
| NFT/licence badges | Low beyond collectors | n/a | Unique NFTs mostly outside MiCA; fractionalized ones are not | Cosmetic only |

**Who pays (EST).**
- Grants and public compute (EuroHPC, NLnet, Current AI-type foundations) are the realistic payers for pre-training a small EU model.
- API revenue for a 1–8B open-weights model is likely to be small, because it competes with free Apertus, Llama, Qwen and similar models.
- Enterprise and public-sector fine-tunes, sovereign hosting, and data or eval services are more plausible.
- The Grass example shows data sales, not model sales, generated the revenue.

**Contribution metric.** Remunerate verified useful work: accepted gradient contributions or throughput-weighted GPU-hours. Do not remunerate raw uptime. Helium HIP 147 and Numerai staking show that gaming follows whatever is easy to fake.

### Gaps
- BigScience/BLOOM and LAION governance and contributor experience were not researched this session. Background: BLOOM was released under the BigScience RAIL licence in 2022, and LAION is a German nonprofit e.V.
- I found no data on whether Folding@home volunteers would accept or prefer pay.
- I found no real ARPU or revenue numbers for any community-trained model.

---

## 3. Ownership, governance and licensing structures

### Takeaway
For an EU/France owner, the best fit is a French SCIC (multi-stakeholder cooperative). Contributors, users, the founders, partner organisations and public bodies sit in separate voting colleges. At least 57.5% of surplus goes to indivisible reserves.

A loi-1901 association is the simplest MVP vehicle.

DAO LLC wrappers add little for an EU team, and Wyoming/Marshall Islands case law is thin. A Swiss association or foundation is the crypto-friendly alternative if a token is ever issued.

Licensing is constrained by the AI Act. Only a genuinely free, open licence with no monetisation earns the GPAI open-source documentation exemption. Contributor-only or delayed access forfeits it once the model exceeds about 10^23 FLOP.

### Cited Findings
- **French SCIC** [S, French official/ESS guides]:
  - It is a cooperative company with variable capital, formed as a SARL, SAS or SA. One guide says an SCIC SARL or SAS has 3–100 associates; the upper bound may apply only to the SARL, so verify it.
  - At least 57.5% of annual surplus goes to impartible reserves. These cannot be distributed or incorporated into capital, and are deductible from corporate tax. A later finance-bill change narrowing that deduction was proposed in 2018, and its final outcome is unverified.
  - The remainder can partly pay interest on shares, after deducting public aid.
  - If voting colleges are used, there must be at least 3, no college may hold a majority alone, and a maximum of 10 is cited.
  - Sources: [Bpifrance Création SCIC](https://bpifrance-creation.fr/pid804/scic.html?espace=1); [Avise fiche SCIC](https://www.avise.org/sites/default/files/atoms/files/20150105/201412_avise_scic.pdf); [leblogdudirigeant](https://www.leblogdudirigeant.com/scic/); [Assemblée nationale amendment 2018](https://www.assemblee-nationale.fr/dyn/15/amendements/1255A/CION_FIN/CF573.pdf)
- **DAO wrappers** [S, law-firm and vendor blogs]:
  - The Wyoming DAO LLC has existed since March 2021, and the Wyoming DUNA (nonprofit association) since July 2024.
  - The Marshall Islands DAO LLC dates from 2022. Sources conflict on whether it may distribute profit.
  - Marshall Islands is suggested for non-US decentralized DAOs and Wyoming for US-nexus DAOs. There is little precedent for either.
  - Sources: [Legal Nodes, Wyoming](https://legalnodes.com/article/wyoming-dao-llc); [Legal Nodes, Marshall Islands](https://legalnodes.com/article/marshall-islands-llc-as-a-dao-legal-wrapper); [frblaw DUNA](https://frblaw.com/the-wyoming-duna-and-the-future-of-dao-legal-frameworks/)
- **Public/sovereign model examples**:
  - Apertus: Swiss public universities and CSCS, Apache 2.0, fully open.
  - OpenEuroLLM: €37.4M budget, of which about €20.6M from the Digital Europe Programme, a consortium of about 20 organisations. First multilingual models were targeted for mid-2026 (around 2026-07-31) and final iterations for 2028. I could not verify the release as of 2026-11 [S]. — [Slator](https://tech.slator.com/enter-openeurollm-open-compliant-diverse-series-of-foundation-models/); [innfactory](https://innfactory.ai/en/ai-models/openeurollm/)
  - Current AI: launched 2025-02-10 at the Paris AI Action Summit with $400M initial funding from France, philanthropies (MacArthur, McGovern, Ford, etc.) and companies (Google, Salesforce). It targets $2.5B over 5 years and funds open datasets, tools and infrastructure. Founder: Martin Tisné. I found no 2026 status update [S]. — [Fortune](https://fortune.com/2025/02/10/france-tech-companies-and-philanthropies-back-400-million-foundation-to-support-public-interest-ai); [techUK](https://www.techuk.org/insights/news/what-were-the-outcomes-of-the-paris-ai-action-summit)
  - The Public AI Inference Utility is a nonprofit, open-source serving layer for public models [P]. — [publicai.co/utility](https://publicai.co/utility)
- **Licensing vs AI Act**: the open-source exemption needs a free and open-source licence, no monetisation, and public weights, architecture and usage information. Proportionate, non-discriminatory safety-oriented use restrictions are allowed, which is relevant to OpenRAIL-style licences [S, Commission guidelines 2025-07-18]. — [WilmerHale](https://www.wilmerhale.com/en/insights/blogs/wilmerhale-privacy-and-cybersecurity-law/20250724-european-commission-issues-guidelines-for-providers-of-general-purpose-ai-models)

### Inferences
**Structure options (EST; background facts marked):**

| Structure | Fit | Pros | Cons |
|---|---|---|---|
| Association loi 1901 (FR) | MVP | Fast (about €0–50 to declare), grant-eligible, members vote | Cannot distribute profit; paying "volunteers" flat amounts risks requalification as salary (background, uncertain) |
| SCIC (SAS form) | Scale, "people-owned" | Multi-stakeholder colleges; contributors become members; public bodies can join as members (background: up to 50% of capital); reserves lock value into the commons; ESS label | Share interest capped; slower capital raising; cooperative accounting/revision; still a company, so it pays tax on non-reserved surplus |
| SCOP | Poor fit | — | Worker-majority model; contributors aren't employees |
| SCE (EU cooperative, Reg. 1435/2003) | Pan-EU membership | European label | Background, unverified this session: needs ≥5 persons from ≥2 member states and €30k minimum capital; rarely used, heavier |
| Swiss association / foundation | Crypto or token path | Familiar to crypto (Stiftung model); Apertus ecosystem nearby | Swiss foundation supervision; no member ownership in a foundation |
| Dutch stichting | Neutral IP holder | Cheap, can hold model IP and trademarks | No members |
| Wyoming DUNA / DAO LLC, Marshall Islands DAO LLC | Only if US/crypto-native | On-chain governance recognized | Little precedent; EU members still subject to EU law; adds a foreign entity to a 1–2 person team |
| Delaware PBC | VC path | Investable | Not "people-owned"; mission enforcement weak (background) |

**Recommended governance pattern (EST).** Use an IP-holding nonprofit or SCIC that owns the weights and trademark. Contributors elect a college. Model-release policy (licence, safety gating) is a member vote with a founders' veto during the MVP period.

**Licensing trade-off.**
- Apache-2.0/MIT open weights maximize legitimacy, grant fit and AI Act exemption.
- Contributor-first access, such as a 3–6-month embargo or members-only API credits, is the main exclusive benefit compatible with eventual open release.
- Dual licensing (open plus a commercial-support or indemnity tier) is compatible with "open" in spirit. But charging for the model may count as monetisation, which voids the AI Act exemption; see §4.

### Gaps
- No concrete AI-specific SCIC or platform cooperative training a model in 2024–2026 was found this session. Data cooperatives (e.g. MIDATA in Switzerland) and Mozilla.ai/Open Future were not checked.
- The SCE minimum-member and capital figures need verification.
- The status of the French SCIC reserves tax deduction after 2018 needs verification.

---

## 4. EU legal: MiCA/MiFID, tax of payouts, consumer/GDPR, AI Act GPAI

### Takeaway
The cleanest legal path is:
- no transferable token;
- stable EUR or EMT payouts under a contract;
- non-transferable points and credits;
- open weights under a free licence.

A revenue-share token is very likely a MiFID II transferable security under ESMA's 2025 guidelines. Individuals receiving payouts in France have taxable income, likely under the micro regime.

The AI Act GPAI duties (documentation, copyright policy, public training-data summary) apply once training compute exceeds about 10^23 FLOP. That is roughly a 1B model on a large dataset, so a "people's model" of any useful size will be a GPAI model.

The open-source exemption removes only the documentation and representative duties, and only without monetisation. Fines apply from 2026-08-02.

### Cited Findings
**Securities and MiCA**
- ESMA's guidelines on qualifying crypto-assets as financial instruments take a substance-over-form approach. Most national authorities treat profit rights attached to a token as sufficient for a transferable security. A governance-plus-profit-share token is "likely" a financial instrument.
- Dates: final report 2024-12-17 or 2025-03-17 depending on source; applies from 2025-05-19 [S]. — [Kramer Levin](https://kramerlevin.com/en/perspectives-search/esma-and-eba-assess-whether-crypto-assets-are-regulated-under-existing-eu-rules-and-advise-the-european-commission-to-consider-an-eu-level-regulation.html); [BDO Malta](https://bdo.com.mt/en-gb/news/news-in-2025/understanding-the-esma-guidelines-on-crypto-assets-as-financial-instruments); [CONSOB copy of ESMA final report](https://www.consob.it/documents/d/asset-library-1912910/esma75453128700-1323)
- MiCA Art. 4(3), CASP and DAC8 are covered in the prior notes and not repeated.

**French tax of payouts**
- Micro-BNC turnover ceiling for 2026 is €77,700 excl. VAT, revalued for 2026–2028 by the 2026 finance law, with a 34% flat allowance (minimum €305) [S]. — [Finalib](https://finalib.fr/blog/fiscalite/micro-bic-micro-bnc-seuils-obligations-2026); [CCI Paris IdF](https://www.entreprises.cci-paris-idf.fr/actualites/micro-entrepreneur-revalorisation-des-seuils-pour-2026-2028)
- Micro-entrepreneur BNC social contributions in 2026 are about 25.6%, up from 24.6%. Sources conflict, with 26.1% also cited. They are due on turnover collected [S]. — [SalaireClair](https://salaireclair.fr/blog/charges-auto-entrepreneur-2026); [Finactuel](https://finactuel.fr/cotisations-auto-entrepreneur-2026-calcul/)
- Crypto capital gains: the PFU is 31.4% from 2026-01-01 (12.8% income tax + 18.6% social charges, after a 1.4-pt CSG rise in LFSS 2026). One guide disputes this and says 30%. There is an exemption for annual disposals of €305 or less [S]. — [Meilleurtaux](https://placement.meilleurtaux.com/placement-financier/actualites/2026-avril/flat-tax-a-31-4-ce-qui-change-depuis-janvier-2026.html); [Finalib](https://finalib.fr/blog/fiscalite/cryptomonnaie-fiscalite-2026-declaration)

**AI Act GPAI**
- A model is indicatively GPAI if training compute exceeds 10^23 FLOP and it generates language, text-to-image or text-to-video. This "roughly matches" training a 1B-parameter model on large datasets [P].
- Obligations, which applied from 2025-08-02 [P]:
  - technical documentation for the AI Office;
  - information for downstream providers;
  - a copyright policy;
  - a public "sufficiently detailed" training-content summary;
  - an EU representative if established outside the EU.
- Full enforcement including fines starts 2026-08-02. Models placed before 2025-08-02 have until 2027-08-02 [P].
- Open-source exemption: only the documentation, downstream-information and representative duties are waived. The copyright policy and training summary remain. There is no exemption for systemic-risk models. The FAQ does not define "monetisation" [P]. — [EC GPAI FAQ](https://digital-strategy.ec.europa.eu/en/faqs/guidelines-obligations-gpai-providers)
- Systemic-risk presumption above 10^25 FLOP. Modifiers who make "significant" changes become providers, using one-third of the threshold. The draft's 10^22 indicator was raised to 10^23 in the final guidelines (2025-07-18) [S]. — [Stibbe](https://www.stibbe.com/publications-and-insights/the-guidelines-for-providers-of-general-purpose-ai-models-are-here-the); [Freshfields](https://technologyquotient.freshfields.com/post/102kxqo/eu-ai-act-unpacked-27-guidelines-on-the-scope-of-obligations-for-general-purpos)

### Inferences (uncertain, not legal advice)
**Token risk.**
- A tradable token carrying a claim on model API revenue triggers MiFID II/Prospectus and needs authorised intermediaries. That is out of scope for 1–2 people.
- A pure "reward for useful work" token might fit MiCA Art. 4(3)(b) (see prior notes). Its market value would still depend on speculation, given the 2026 token-market weakness.
- Cooperative parts sociales are a regulated but familiar alternative for the upside. They are typically non-freely-transferable, so they are not MiFID transferable securities (background, uncertain). Public offers of SCIC shares have specific French rules that need checking.

**Tax and classification of payouts.**
- Renting out a GPU is arguably income from leasing movable property (BIC, "location de matériel") rather than BNC. Which regime and threshold applies is unclear; ask an expert-comptable or seek a rescrit fiscal.
- Small occasional amounts are still taxable.
- Platform reporting: DAC7 covers "personal services". Whether GPU rental counts is unverified.
- If paying in USDC, contributors face a crypto taxable event on conversion, and CASPs report under DAC8.
- Being a contractor-payer means collecting payee identity and tax ID, screening sanctions, and issuing annual statements.
- There is no employment relationship if contributors control when and whether they run (background: subordination test). Avoid quotas or schedules that look like direction.

**Volunteer reimbursement in an association.** Pay only documented actual expenses, such as electricity measured by declared wattage × hours × tariff. Flat "indemnités" risk requalification (background, uncertain).

**GDPR.**
- Contributor identity, IP addresses, hardware telemetry and wallet addresses are personal data. One commentary argues blockchain addresses are personal data (see the prior note's López Kurtz cite).
- Use a contract lawful basis (Art. 6(1)(b)) for payouts and a legitimate-interest basis for anti-fraud telemetry.
- Keep payout identities off-chain. Immutable on-chain personal data conflicts with erasure rights.
- Training-data GDPR issues apply separately and are a larger risk than contributor data.

**Consumer and contract law.**
- Contributors are consumers dealing with a professional platform. The unfair-terms rules (Directive 93/13) apply to ToS clauses such as unilateral payout-rate changes or forfeiture of points.
- Write clear rate-change notice and points-expiry terms (background).

**AI Act.**
- Any useful community model of 1B parameters or more on large data will be GPAI.
- Even fully open, it must have a copyright policy, including respecting TDM opt-outs per the Code of Practice (background), and must publish the Commission-template training-data summary.
- Charging for API access, or making access contingent on payment, may count as "monetisation" and lose the documentation exemption. Then full Art. 53 technical documentation applies, which is roughly a few person-weeks with the Code of Practice templates (EST).
- An EU-established provider (the coop or association) needs no representative.
- 10^25 FLOP (systemic risk) is far beyond the realistic budget (see §1).

### Gaps
- The French AMF/URSSAF position on GPU-rental income was not found.
- I did not check whether the EU "Digital Omnibus" (proposed late 2025) changed GPAI timelines or obligations by Nov 2026. Re-check this.
- The exact Commission definition of "monetisation" in the GPAI guidelines text was not retrieved. Secondary sources say paid services and monetised support can count; verify.

---

## 5. Public funding fit for a sovereign, people-owned EU model

### Takeaway
Money for EU sovereign or public models flows to consortia (OpenEuroLLM €37.4M), institutions (Swiss AI/Apertus) and giga-scale infrastructure (Gigafactories, up to €10B public). A 1–2 person project cannot lead these.

The realistic fits are:
- free compute (AI Factories Fast Lane, 50k GPU-hours; see prior notes);
- NLnet/NGI-type grants;
- partnering as a "citizen compute" pilot with OpenEuroLLM or Current AI grantees;
- serving through the Public AI Inference Utility.

### Cited Findings
- **AI Gigafactories call**: opened 2026-07-30 and closes 2026-11-12. Up to €10B of EU and national support is expected to unlock about €20B private, for more than €30B total. Up to about 7 sites (one lot: 4 medium-scale). The EuroHPC JU Governing Board decides, with awards expected early 2027 and operation within 18 months of signature. Consortia or SPVs of companies, public entities and investors may apply. This scales back the €20B InvestAI announcement of Feb 2025 [P/S]. — [EU Digital Skills news](https://digital-skills-jobs.europa.eu/en/latest/news/eu-ai-gigafactories-call-open-until-12-november-targeting-over-eu30-billion-investment); [StorageNewsletter 2026-08-18](https://www.storagenewsletter.com/2026/08/18/eu-launches-ai-gigafactories-call-to-boost-europes-computing-capacity-and-unlock-more-than-e30-billion-in-investment/); [TED notice](https://ted.europa.eu/ro/notice/529135-2026/pdf)
- **OpenEuroLLM**: €37.4M, about 20 partners, Digital Europe-funded. Model targets were mid-2026 to 2028 [S]. — [Slator](https://tech.slator.com/enter-openeurollm-open-compliant-diverse-series-of-foundation-models/)
- **Current AI**: $400M initial, $2.5B 5-year target, for public-interest open AI goods (2025-02) [S]. — [Fortune](https://fortune.com/2025/02/10/france-tech-companies-and-philanthropies-back-400-million-foundation-to-support-public-interest-ai)
- **Public AI Inference Utility**: the nonprofit serving layer is donor-funded [P]. — [publicai.co/utility](https://publicai.co/utility)
- Prior notes cover EuroHPC Fast Lane (≤50k GPU-h, about 4-day approval), NLnet (calls paused after 2026-06-01, reopening "after summer 2026"), France 2030 "Pionniers de l'IA", Bpifrance and Google TRC. — see `viability_constraints.md` §2.

### Inferences (EST)
**Grant-funded payout pool.** A €50–150k grant pool (NLnet-scale milestones or a Current AI/philanthropy grant) at €0.15/4090-hour buys about 0.3–1M GPU-hours. That is enough for a credible 10^22–10^23 FLOP demonstration run (see §1).

**Pitch positioning.** Pitch it as "citizen-owned compute" complementary to public HPC, not as an OpenEuroLLM competitor. Offer a fine-tune, continued-pretraining or evaluation run on a public base model (Apertus or OpenEuroLLM). This avoids the cost of pre-training from scratch, and AI Act provider status only shifts to the modifier above one-third of the original compute.

**Gigafactories** are irrelevant as an applicant. They may be relevant as a future customer or partner for "edge" capacity narratives.

### Gaps
- Current AI's 2026 grant calls and eligibility were not found.
- Whether OpenEuroLLM released models by Jul 2026 is unverified.
- The AI Continent Action Plan (Apr 2025) and Apply AI funding lines for SMEs were not researched this session.
- France 2030 calls open in Nov 2026 were not re-checked.

---

## 6. Bottom line: recommended contributor-economics + legal-structure packages

### Takeaway
Run a phased progression. Start with Package A (MVP, about 0–12 months). Graduate to Package B (scale) once there is a revenue or grant base and at least about 500 active contributors.

Hold Package C (token) in reserve. Use it only if a regulated partner exists and the token market recovers.

All three pay stable money for verified work. None issues a profit-bearing tradable token.

### Cited Findings
(Synthesis of §§1–5. Key anchors:)
- Stable-value payouts are the 2026 norm (Grass USDC, io.net IDE). — [hokanews](https://www.hokanews.com/2026/07/grass-reveals-season-2-claim-date-as.html); [CoinDesk](https://coindesk.com/research/the-incentive-dynamic-engine-a-new-era-for-io-net-tokenomics)
- Profit tokens are likely securities. — [BDO Malta](https://bdo.com.mt/en-gb/news/news-in-2025/understanding-the-esma-guidelines-on-crypto-assets-as-financial-instruments)
- The AI Act open-source exemption requires no monetisation. — [EC FAQ](https://digital-strategy.ec.europa.eu/en/faqs/guidelines-obligations-gpai-providers)
- SCIC: 57.5% reserves, multi-stakeholder colleges. — [Avise](https://www.avise.org/sites/default/files/atoms/files/20150105/201412_avise_scic.pdf)

### Inferences (EST; all numbers are planning estimates)

**Package A: "Open Commons MVP" (association + grant-funded electricity-plus pay + points)**
- **Entity:** a French association loi 1901, or a fiscally hosted project under an existing nonprofit. It owns the weights and trademark.
- **Pay:**
  - EUR via SEPA, or USDC, per verified GPU-hour, country-indexed at electricity × 1.3: about €0.10–0.25 for a 4090.
  - Monthly cap per person, e.g. €150, to stay in "small income" territory and limit fraud exposure.
  - Contract framed as a compute-services or contest agreement; contributors self-declare tax.
- **Non-cash:** non-transferable contribution points serving as reputation and governance weight. Explicitly no promise of token conversion.
- **Benefits:** first access to checkpoints, free inference quota, and name in the model card.
- **Model:** a fine-tune or continued pretraining of Apertus or OpenEuroLLM, Apache-2.0, released immediately. This qualifies for the GPAI open-source exemption if the training run exceeds the modifier threshold, and avoids monetisation.
- **Budget:** €50–150k grant gives about 0.3–1M 4090-hours.
- **Pros:** minimal legal load (no MiCA, no securities); grant-eligible; mission-credible.
- **Cons:** no upside, so retention relies on mission plus pay (BOINC-style churn risk, about 5 in 6 lapse); payouts end when the grant ends.

**Package B: "People's Model Cooperative" (SCIC + patronage + member credits + dual-track licence)**
- **Entity:** SCIC SAS with at least 4 colleges:
  - compute contributors, e.g. 30–40% of votes;
  - users and customers;
  - founders and staff;
  - partners, including public bodies, universities and NGOs.
- Contributors buy one €10–50 share to become members. Shares are non-transferable and redeemable at par.
- **Pay:** stable per-GPU-hour payment (as in A) from customer revenue and grants.
- **Year-end surplus:**
  - at least 57.5% to impartible reserves, funding the next training run;
  - the remainder as capped share interest and/or patronage-style rebates proportional to verified GPU-hours. The ristourne mechanics in an SCIC need checking with counsel.
- **Exclusive member benefits:** inference credits ∝ contribution; a 3–6-month members-first window on new checkpoints; votes on release and safety policy.
- **Revenue sources:** sovereign or enterprise fine-tunes, hosted API (possibly via a separate commercial subsidiary), public-sector contracts and grants.
- **AI Act:** a paid API or embargo probably counts as monetisation, so budget full Art. 53 documentation, a copyright policy and a training summary. That is a few person-weeks per release.
- **Pros:** genuine collective ownership; the legally familiar cooperative form avoids MiCA/MiFID; aligns with ESS and public-funder values; can admit municipalities and regions.
- **Cons:** slower and heavier governance (AG, statutory auditor/révision); limited capital raising; upside is modest and capped; French-centric (an SCE is heavier for pan-EU).

**Package C: "Protocol token track" (Swiss association/foundation + MiCA-exempt useful-work token + stable floor)**
- **Entity:** a Swiss association or foundation, or an EU entity with a MiCA white paper.
- **Pay:** token minted as a reward for verified training work, relying on the MiCA Art. 4(3)(b) exemption, plus a USD-stable floor from revenue (io.net IDE pattern). Revenue is used for buy-and-burn, not dividends.
- **Pros:** global reach; liquid incentive; fits the existing AIBC ERC20 and model-registry contracts.
- **Cons:**
  - token prices in 2026 are about 90–98% off peak for comparables;
  - counsel and white paper about €20–60k (prior notes);
  - DAC8 and CASP interactions for any exchange role;
  - a speculative contributor base;
  - credibility cost with public funders;
  - any revenue-share feature pushes it into securities law.
- **Use only** if a regulated partner handles distribution.

**Default recommendation.** Start with A, using the existing ERC20 code only for a non-transferable or testnet points ledger. Pre-register an SCIC conversion path (B) in the association's statutes or roadmap. Revisit C only after product-market fit.

### Gaps
- No precedent was found for an SCIC paying patronage to compute providers. Counsel should confirm ristourne rules and offer-to-public rules for SCIC shares.
- Contributor willingness to pay or accept cooperative shares instead of tokens is unmeasured. A survey of the target community (r/LocalLLaMA, French gaming communities) is recommended.
