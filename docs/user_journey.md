# User Journey

End-to-end flow of a customer using Treasury AI, from discovery to ongoing operation.

## Persona: Pablo, founder of Acme

- 32 years old, founded Acme Software SL (Madrid) in 2023
- 20 employees, just closed a $4M Series A from Kfund
- $325k currently in Qonto checking, ~$65k/month burn
- Wears the CFO hat between sales calls — knows he's leaving money on the table
- Heard about us from a portfolio email from his lead investor

## Day 0: Discovery

Pablo lands on our website (`treasuryai.example`). Hero copy:

> *Stop losing money on your idle cash. Earn 4% on it, automatically.*

He scrolls. Sees:
- A **calculator**: "Paste your cash balance and burn rate; we'll show how much you're leaving on the table."
- He types: $325,000 cash, $65,000/mo burn.
- The calculator shows: *"You're earning ~$1,600/yr. We'd target ~$13,000/yr at zero risk to capital. That's $11,400 you're missing every year."*
- Below: *"Setup takes 30 minutes. We charge 20bps of AUM. You can withdraw any time. Backed by Alpaca, the same infrastructure as Stash and Public."*

He clicks **"Try it."**

## Day 1: Sign-up (10 minutes)

1. Email + company name → magic-link login.
2. **Company profile**: legal name, jurisdiction, employees, stage (Series A), industry (SaaS).
3. **Connect bank** (production: PSD2 OAuth via Tink/GoCardless). For the demo, the bank MCP already has 3 years of seeded `main-company` data.
4. **KYB documents**: articles of incorporation, beneficial owner ID, board resolution authorising treasury investing. Uploaded.
5. **Investment policy**: confirm or customize defaults — max % per ETF, max duration, min liquidity. Pablo accepts the default conservative policy.
6. **Sign the investment management agreement** (digital signature).

## Day 2: Account opening (24h, async)

Behind the scenes:
- Alpaca processes the KYB and opens a brokerage account in Acme's name.
- We receive a webhook: `account.created`.
- We email Pablo: *"Your treasury account is ready. Here are the wire instructions."*

## Day 3-4: Funding (1-2 days)

Pablo logs into Qonto, makes a wire transfer:
- Beneficiary: Alpaca Securities LLC FBO Acme SL
- Amount: $50,000 (small pilot)
- Reference: `ACME-PILOT-2026Q2`

Money in transit ~24-48h. Webhook fires when it lands. We email Pablo: *"$50,000 received — open the chat to plan your first allocation."*

## Day 4: First conversation (10 minutes)

Pablo opens the chat. The agent introduces itself:

> **CFO:** Hi Pablo, I'm your treasury AI. I see $50k just landed. Before I propose how to invest it, I want to understand your cash situation. **What's your runway plan and any big planned outflows in the next 12 months?**

Pablo: *"We have ~12 months of runway, planning to hire 4 engineers in July, and there's a $600k office buildout in September."*

The agent asks 3 more onboarding questions (revenue trajectory, hiring plans, fundraising plans). Then runs the **deploy** flow:

```
1. Forecaster: pulls 3 years of MCP data, computes
   - balance: $325,000 (incl. the $50k pilot)
   - monthly burn: $65,000
   - liquid required (30d/90d/180d): $30k / $90k / $180k
   - lockable long-term: $145,000

2. Strategist: pulls live yields (BIL 4.31%, SGOV 4.32%, SHV 4.25%, SHY 4.18%)
   Builds a 3-rung ladder:
   - SGOV: $25,000 (50%) — 0-3mo bucket
   - BIL: $15,000 (30%) — 1-3mo bucket
   - SHV: $9,500 (19%) — 3-12mo bucket
   - $500 cash buffer (1%)

3. Risk Officer: validates ✓ — no rules violated.

4. CFO Synthesis: composes proposal:
   "Here's what I'd do with the $50k — split across SGOV/BIL/SHV
    earning ~$2,150/yr blended. Approve?"
```

Pablo reads, types **"approve"**.

```
5. Executor places 3 market orders on Alpaca paper.
   3 fills returned in 5 seconds.

6. CFO Synthesis confirms:
   "Done. $49,500 deployed across 3 ETFs. Cash buffer: $500.
    First yield realisation in 30 days."
```

## Steady state: Ongoing operation

### Daily (automatic)
- Forecaster updates its model with new MCP transactions if any landed.
- No agent action unless thresholds breached.

### Weekly
- Pablo gets a brief email summary: "Yield earned this week: $215. Portfolio steady. No action needed."

### Monthly
- Strategist proposes rebalance if yields have shifted >25bps OR liquidity bucket has drifted from target.
- Pablo gets a chat notification: "Monthly review ready — want to see it?"
- He approves (or skips) — execution is in his control.

### Quarterly
- Reporting bundle: PDF with positions, yield realised, weighted duration, policy compliance attestation. Suitable for board pack.

## Cash withdrawal (when needed)

Pablo: *"I need $30k by Friday for the office buildout deposit."*

Agent:
1. Forecaster checks current liquidity: SGOV is fully liquid (T+1 settle).
2. Executor proposes: sell 290 shares of SGOV (~$30,000 at $103.45/share).
3. Pablo approves.
4. Sell order placed → settled T+1 → cash in Alpaca account → wire to Qonto initiated.
5. ETA in chat: "Cash will land in your Qonto account in 2 business days."

## Expansion path

After 6 months:
- Pablo is happy → bumps from $50k pilot to $250k (after he closed a customer).
- Recommends us to a peer founder at a Madrid founder dinner.
- His lead investor (Kfund) starts mentioning us in their portfolio emails.

After 12 months:
- Acme has $2M deployed, earning ~$85k/year.
- Pablo is a reference customer for our case study.
- We pitch Qonto on a white-label embed: *"200 of your customers already use us. Embed and stop them having two apps."*

## Phase 2: After embed launch

When we partner with Qonto (or similar):
- The wire-funding step disappears entirely. Pablo's cash is already at Qonto. He clicks "Enable Treasury" — Qonto sweeps to Alpaca internally.
- The whole onboarding is 30 seconds, not 30 minutes.
- Customer relationship stays with Qonto; we are infrastructure.
