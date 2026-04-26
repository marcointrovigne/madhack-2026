# Pitch deck (3–5 minute demo)

## Slide 1: The hook

> ### Every Series A startup loses ~3% of their cash to inflation every year.
> ### Treasury AI fixes that, automatically.

**Subhead:**
*An AI treasurer for European startups. They earn 4%+ on idle cash without becoming finance experts.*

**Visual:** chart showing (a) inflation eroding cash purchasing power vs (b) cash earning 4%+ in T-bills over 36 months.

---

## Slide 2: The problem

> ### European startups have €35T+ sitting in low-yield deposits.

A typical Series A:
- $4M raised, ~$3M in operating cash
- Earning 0.5% in checking → ~$15k/year
- Should earn 4%+ in T-bills → ~$120k/year
- **They're missing $105k of free yield, every year**

Why don't they capture it?
- Opening a brokerage = weeks of paperwork
- Writing an investment policy = board-level conversation
- Picking instruments = a finance expert they don't have
- Forecasting cashflow to know what's "lockable" = a CFO they can't afford
- Manual rebalancing = brain damage they don't have time for

**Result: cash sits idle. Inflation eats it. Founder feels vague guilt.**

---

## Slide 3: The product

> ### A multi-agent AI treasurer that does all of it.

**Visual:** the agent topology diagram (CFO Router → Forecaster → Strategist → Risk Officer → Executor → CFO Synthesis).

The customer chats with it. Behind the scenes, 7 specialised agents collaborate:

- **Forecaster** reads bank transactions and projects cash needs
- **Strategist** builds a T-bill ladder using live market yields
- **Risk Officer** enforces the Investment Policy Statement (veto power)
- **Executor** places trades on Alpaca paper account
- **CFO Synthesis** translates structured analysis into a friendly reply

**Approval gate:** every trade requires explicit founder confirmation. Full audit trail.

---

## Slide 4: Live demo (3 minutes)

Walk through:

1. *"Hi, show me where my cash is."* — Portfolio Reader fires, returns $325k status.
2. *"What's my burn rate, and what can I deploy?"* — Forecaster analyses 3 years of bank data.
3. *"We just got $50k extra. What do we do?"* — full pipeline. **Risk Officer catches a violation, forces revision.** Proposal presented with approval ask.
4. *"What if rates drop 50bps next quarter?"* — sidebar simulation, no commit.
5. *"Approve."* — Executor places live paper trades. Confirmation returned.
6. *"Show me my new portfolio."* — Portfolio Reader confirms positions in Alpaca.

**The wow moment:** the Risk Officer rejecting and forcing a revision. It looks like a real institution debating internally.

---

## Slide 5: Multi-agent on Orca

**Visual:** the Orca mesh with our agents queryable individually.

Treasury AI is purpose-built for the Orca mesh model:
- Each agent is a separate "specialist" judges can query directly
- "Show me the Risk Officer's policy" — instantly explains the rules
- "What does the Forecaster think about Q3?" — runs cashflow projection on demand
- The orchestrator (CFO) coordinates — but each piece can be inspected

This isn't a monolithic chatbot. It's an institution-style AI org chart.

---

## Slide 6: Market

> ### €1.5T+ in EU operating cash earning <1%.

- 1% market share at 20 bps = **$300M ARR**
- 0.1% market share = **$30M ARR**

Comparable success in the US: **Mercury Treasury captured ~$4B AUM in 2 years** of post-SVB demand.

Europe has no equivalent. **Vacant market**.

---

## Slide 7: Go-to-market

**Phase 1 (months 0–18):** direct to startups
- Channel: VC portfolio pushes, accelerator partnerships, founder content
- Pricing: 20 bps of AUM/year
- Target: 100–500 customers, $100M–$500M AUM

**Phase 2 (months 18+):** white-label embed in business banks
- Targets: Qonto, Revolut Business, Pleo, Spendesk, Payhawk
- Pricing: setup fee + 25/75 revenue share on AUM
- Single embed unlocks 10k+ accounts overnight

**Why the phasing works:** direct customers prove demand. Banks then embed because their customers are already defecting to us.

---

## Slide 8: Why we win

1. **30-minute onboarding** vs. weeks of private banking
2. **AI-native chat** vs. static questionnaires
3. **B2B-purpose-built** vs. retail robo-advisors
4. **EU-focused** vs. Mercury (US-only)
5. **No AUM minimum** vs. $100k+ at private banks
6. **20 bps** vs. 50–150 bps at wealth managers
7. **Embeddable** = long-term defensible distribution

---

## Slide 9: Stack

- **Alpaca** — Broker API (custody) + Trading API (execution) + Market Data API (live yields)
- **Orca** — multi-agent mesh, runtime, observability
- **LangGraph** — orchestration of 7 specialised agents
- **MCP** — bank data via standardised protocol (PSD2/Tink in production)
- **Anthropic Claude** — reasoning engine (Sonnet 4.6)
- **Python + FastAPI** — backend

---

## Slide 10: The ask / closing

- We're shipping the prototype today
- Looking for a design partner customer (Series A founder with $500k+ idle)
- And a fintech distribution partner (Qonto, Pleo, etc.)
- TAM is $1.5T. We're early. Let's go.

---

## One-liner versions for any audience

**5 seconds (elevator):**
> *"AI treasurer for European startups — 4% on idle cash, automatically."*

**30 seconds (founder dinner):**
> *"Every Series A has millions sitting at 0.5%. T-bills pay 4%, but no one wants to open a brokerage and write an IPS. We do it for them — multi-agent AI that forecasts cashflow, builds T-bill ladders, executes trades. 20 bps of AUM, 90% gross margin, embeddable into any neobank. Mercury for Europe."*

**3 minutes (judges):**
Open with the loss-aversion stat → describe the multi-agent product → live demo with Risk Officer revision → explain phased GTM → close with TAM and unit economics.

## Closing line

> ### "Stripe is an API for payments. Alpaca is an API for investing. We're the AI agent layer on top — drop us into any business banking product and your customers get an AI CFO that earns yield on their cash without anyone having to think about it."
