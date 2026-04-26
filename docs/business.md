# Business Model

## What we sell

**Managed treasury service** for European startups. The customer gets:
1. A brokerage account opened in their company's name (via Alpaca Broker API)
2. An AI treasurer they can chat with
3. Active management of their idle cash into T-bill ladders
4. A board-ready reporting bundle, monthly

**Pricing: 20 bps of AUM per year.**

## SKU clarity

We are **not** SaaS (no per-seat license).
We are **not** a bank (no banking license, no deposit insurance burden).
We are **not** a broker (Alpaca is).

We are an **AI-powered investment advisor** charging on AUM, exactly like:
- Wealthfront / Betterment (US, retail) — 25 bps
- Indexa Capital / Moneyfarm (EU, retail) — 30-50 bps
- Mercury Treasury (US, B2B) — variable, blended near 20 bps
- Scalable Capital (DE/EU) — 75 bps

We sit at the cheap end of advisory fees, justified because we're software-leveraged.

## Customer profile (ICP)

**Day-1 ICP** (Phase 1, direct):
- Stage: Series A → mid Series B
- Cash on balance sheet: **$300k – $15M**
- Geography: EU primary (Spain, France, Germany, NL, UK)
- Vertical: SaaS preferred (predictable burn = clean Forecaster)
- Bank: Qonto, Revolut Business, Wise Business, traditional EU banks
- Runway: 12+ months (otherwise yield is irrelevant)

**Buyer / champion:**
- **Pablo** (founder-CEO doing CFO duty between sales calls) — easiest to convert, biggest segment
- **Marie** (first Head of Finance at Series B) — bigger AUM, longer sales cycle
- **James** (COO with finance hat) — pragmatic, becomes reference customer

## Phase 1 GTM (Months 0–18): direct

We sign up startups one at a time. Self-serve onboarding with a sales call available for tickets >$1M AUM.

### Distribution channels (cheapest first)

| Channel | Cost | Leverage | When |
|---|---|---|---|
| **VC portfolio pushes** | low | very high | Day 1 — one partner emails 100 portcos |
| **Accelerator partnerships** | low | high | Month 1–3 — Antler, EF, Lanzadera, Wayra |
| **Founder-community content** | medium | high over time | Month 1+ — LinkedIn calculator, founder podcasts |
| **Cold outreach to recent raises** | medium | medium | Month 3+ — Crunchbase / Dealroom feed → email |
| **Conferences** | high | medium | Month 6+ — Slush, 4YFN, Web Summit |

### Day-1 channel

**One VC partner who likes us forwards a portfolio email** = 50–150 warm intros in a single send.

Targets: Atomico, Index, Accel, Seedcamp, Kfund, Samaipata, JME Ventures, Cherry Ventures. Especially anyone with SVB scar tissue from March 2023.

### Customer economics in Phase 1

- Average customer AUM: **$1–3M**
- Revenue per customer: **$2k–$6k/year** (20 bps)
- Cost per customer (Alpaca + cloud + LLM): ~$500/yr
- Gross margin: **~85–90%**
- CAC (organic via VC channels): $100–500
- CAC (cold outbound): $500–1500
- Customer lifetime: 3+ years (treasury is sticky)
- LTV / CAC ratio: 12× to 60×
- Payback: <6 months

## Phase 2 GTM (Months 18+): embed

Once we have 200+ direct customers and tens of millions in AUM, we approach business-banking platforms with leverage:

### Embed targets

| Tier | Examples | Why they want us |
|---|---|---|
| **Top** | Qonto, Revolut Business, N26 Business | Largest EU business-banking customer bases; competing with Mercury narrative |
| **High** | Pleo, Spendesk, Payhawk | Spend management → natural extension to treasury |
| **Medium** | Wise Business, Tide, Holvi | Smaller but underserved |
| **Adjacent** | Payfit, Personio | HR/payroll-side companies who want to offer treasury to their corporate customers |

### Embed pricing

- **Setup fee**: $50k–$150k per partner
- **Revenue share**: 25/75 split in their favor on AUM bps. They distribute, they get the bigger cut. We get scale.

### Worked example: Qonto embed

- Qonto has ~500k business customers
- ~10% have $500k+ idle cash → 50k addressable
- 30% adopt the embedded treasury feature in Year 1 → 15k accounts
- Average AUM per account: $1.2M → $18B AUM total
- Total fee at 20 bps = $36M/yr
- Our 25% share = **$9M/yr from one partner**

## Total addressable market

- **EU SME and startup operating cash**: estimated $1.5T+ sitting at <1% interest rates
- 0.1% market share at 20 bps = **$30M ARR**
- 1% market share = **$300M ARR**

The math works at any reasonable adoption.

## Competitive positioning

| Competitor | What they do | Why they lose |
|---|---|---|
| **Status quo (do nothing)** | Cash in checking at 0–0.5% | Loses to inflation; founder feels guilty |
| **DIY brokerage (Interactive Brokers, etc.)** | Open it yourself, buy T-bills manually | 5–10 hours of setup, no policy, no reporting, no monthly maintenance |
| **Wealth manager / private bank** | Treasury management as a service | $5k–50k/year minimum, weeks of onboarding, $5M+ AUM minimum, opaque |
| **Mercury Treasury / Brex Vault** | B2B treasury for US startups | Not in Europe — entire EU market is unaddressed |
| **Wise Interest / Revolut Vaults** | "Boosted" savings account | 1–2% yield, capped, not real treasury |
| **BlackRock / iShares direct** | T-bill ETFs retail | Institutional only; $10M+ minimum |
| **Indexa, Moneyfarm, Scalable** | Robo-advisor for retirement | B2C only — no corporate KYB, no treasury features, no AR/AP integration |
| **Internal tooling (build in-house)** | CFO writes scripts | Doesn't happen at Series A — wrong stage |

## Why we win

1. **30-minute onboarding** vs. weeks (private banking) or hours (DIY)
2. **Chat AI interface** vs. static questionnaire (robo-advisors) or no UI (broker DIY)
3. **B2B-purpose-built**: KYB, treasury reporting, AR/AP-aware forecasting
4. **No AUM minimum** vs. $100k–$5M minimums of wealth managers
5. **20 bps** vs. 50–150 bps of wealth managers
6. **EU-native** vs. Mercury (US-only) and Indexa (B2C-only)
7. **Embeddable** — the long-term moat that incumbents can't easily replicate

## Risk register

| Risk | Mitigation |
|---|---|
| **Regulatory uncertainty** (we advise on investments) | Operate as MiFID II tied agent under Alpaca's umbrella in Y1; full advisory authorisation in Y2 (~€100–300k legal cost) |
| **Rates collapse** (T-bill yield → 0%) | Pivot to corporate IG bonds, EUR money market, structured products — agent flexibility = our moat |
| **Big bank competition** (BlackRock launches treasury for SMEs) | Speed, AI-native UX, EU focus, depth in startup vertical, embed moat |
| **Customer trust in AI** | Approval gates on every trade, full audit trail, transparent reasoning, gradual autonomy ("auto-approve trades under $X") |
| **Distribution cost** | VC channel + content + accelerator partnerships keep CAC organic; embed strategy is the long-term defence |
| **Embedded partners building it themselves** | Same reason Plaid still exists despite banks: switching costs, 18 months of head start, agent quality is non-trivial to replicate |

## Why this is a venture-scale business

- TAM is $1.5T+ in addressable EU operating cash
- 20 bps × $1B AUM = $2M ARR; reaching $1B AUM takes ~500 mid-size or 5,000 small customers — both achievable
- 90% gross margin
- Sticky (treasury changes are friction-heavy)
- Phase 2 embed is a defensible distribution moat
- Defendable IP: the agents, the IPS engine, the customer base
