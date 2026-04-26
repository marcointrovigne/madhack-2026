# Treasury AI — Concept

## One-line

**An AI treasurer for European startups — they earn 4%+ on idle cash, automatically, without becoming finance experts.**

## The problem

Every European Series A startup has €1M–€10M sitting in a checking account at 0–0.5% interest. T-bills currently yield 4%+. That's hundreds of thousands of dollars per year of free yield being left on the table — but founders don't capture it because:

1. Opening a brokerage account is paperwork-heavy (KYB, weeks of work)
2. Writing an investment policy is a board-level conversation
3. Picking instruments (BIL, SHV, SHY, SGOV, money-market funds) requires expertise
4. Forecasting cashflow to know what's "lockable" requires a CFO they don't have
5. Manual rebalancing each month is brain damage

So the cash sits idle. **Inflation eats 3% per year. The company quietly loses money.**

## The product

A multi-agent AI system that acts as an outsourced corporate treasurer. The customer chats with it; behind the scenes a team of specialised agents collaborates:

- **Forecaster** reads the company's bank transaction history and projects cash needs forward 30/90/180 days.
- **Strategist** pulls live US Treasury yields from Alpaca and constructs a maturity-laddered portfolio of T-bill ETFs (SGOV, BIL, SHV, SHY).
- **Risk Officer** validates every proposal against a written Investment Policy Statement (IPS) — single-ETF caps, duration limits, asset-class allowlist, liquidity floors. Has veto power.
- **Executor** places the actual paper trades via Alpaca after the founder approves.
- **CFO Synthesis** translates structured outputs into a friendly natural-language reply.

The customer wires money once. The agents do everything else, monthly, indefinitely.

## Why now

- **€35T of European household + corporate deposits** are sitting in near-zero-yield accounts.
- **Mercury Treasury** has captured the US startup market post-SVB — but they don't operate in Europe.
- **PSD2 / Open Banking** has matured: aggregators like Tink, GoCardless, TrueLayer make bank-data integration a 2-week ticket, not a multi-year build.
- **Alpaca's Broker API** lets a fintech open brokerage accounts for end customers without becoming a broker-dealer themselves — the same path Stash, Public, M1 Finance used.
- **AI agents are now reliable enough** to do the analytical work a junior CFO would do, at 1/100th the cost, with full transparency.

## What we are NOT

- We are not a bank. Customer money is custodied at Alpaca's regulated banking partner.
- We are not a broker-dealer. Alpaca is. We're a software/advisory layer on top.
- We are not a retail robo-advisor. We're B2B-purpose-built for corporate treasury, not individual retirement.
- We are not a black box. Every recommendation has a reasoning trail. Every trade has explicit user approval.

## Regulatory positioning

We operate the same model as **Indexa Capital, Moneyfarm, Wealthfront, Betterment**:
- Investment advisor (not a broker)
- Customer money custodied at the regulated broker (Alpaca, in our case)
- Charged on AUM (basis points)

EU-side, this means **MiFID II investment advisory firm** — operating either independently (≈€100–300k of legal/regulatory cost) or as a *tied agent* of an existing licensed entity in Year 1.

## Distribution philosophy

**Year 1: direct to startups.** A startup founder signs up online, the agent is onboarded, money flows. No bank involvement. We charge 20 bps of AUM annually.

**Year 2+: embed in business banks.** Once we have hundreds of startup customers as proof points, we white-label into Qonto, Revolut Business, Pleo, Spendesk. They distribute, we share revenue. The wire-funding friction disappears (the cash is already at Qonto; sweep is one click).

This is the same wedge → expansion playbook as Notion (individual → team → enterprise), Stripe (developer → SMB → enterprise), and Mercury (founder → fintech → enterprise).
