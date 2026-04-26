# Treasury AI · Business brief

A plain-English overview of what we're building, who buys it, how we sell it, and how each piece works.
**Not a pitch script.** This is the doc you send a curious VC associate, an early hire, or a journalist.

---

## 1. The product in one paragraph

Treasury AI is an AI-native treasury manager for European startups and SMBs. Customers chat with it like a CFO. Behind the scenes a multi-agent system reads their bank account, projects their cash needs, builds a US-Treasury-bill ladder via Alpaca, validates against an investment policy, and executes paper trades after explicit approval. We charge **20 bps of AUM** and never custody money — funds sit at Alpaca's regulated banking partner. **T-bill exposure is via SGOV / BIL / SHV / SHY ETFs**, which hold US Treasuries directly and are tradeable via Alpaca's API.

---

## 2. The agent system, explained simply

Treasury AI isn't one chatbot — it's **nine specialised agents** orchestrated by LangGraph that share a single state object. Each agent mirrors a real corporate treasury function. The customer types one message. Internally, between two and six agents collaborate, then a single agent composes the reply.

### Why a multi-agent design?

Three reasons:

1. **Inspectable reasoning.** Each agent has a single job and produces typed output. When a judge or investor asks "why did it pick SGOV over BIL?", the answer isn't "the LLM decided" — it's "the Strategist's `Allocation.lines` chose SGOV because the Forecaster reported `liquid_required_90d = €1.8M` and SGOV had the highest yield in the 0–3 month bucket".
2. **Veto power.** A single LLM proposing trades is hard to constrain. With a separate **Risk Officer** that reads typed JSON and validates against `policy.yaml` rules, we get a hard guardrail in code. The LLM can't override it.
3. **Orca-mesh-native.** Each agent is a separately addressable specialist. Customers (and judges) can sidebar any one of them: "Show me what the Risk Officer is enforcing." That's a UX feature you literally can't deliver with a monolithic chatbot.

### The nine agents · what they actually do

#### CFO Router · the dispatcher
Reads the user's message and classifies it into one of seven intents: `deploy`, `withdraw`, `status`, `what_if`, `education`, `approve`, `unknown`. No tools, no math. Just: "is this person asking to invest, asking a question, or approving something?". This saves 80% of the tokens vs. running every pipeline blindly.

#### Portfolio Reader · the status agent
Answers "where's my cash?", "what did I earn this month?", "show me my positions". Reads from the bank MCP server (current bank balance + recent transactions) and from Alpaca (portfolio holdings + monthly P&L). Composes its own one-paragraph reply — doesn't go through the synthesis layer.

#### Forecaster · the financial analyst
This is the agent that gives Treasury AI its real edge. Reads **3 years** of bank transactions via the MCP server. Categorises inflows/outflows. Identifies recurring patterns (monthly payroll, quarterly tax, vendor commitments). Projects cash needs at **30, 90, and 180-day horizons**. Outputs `liquid_required_30d`, `liquid_required_90d`, `liquid_required_180d`, and `lockable_long_term` — the four numbers that drive everything else.

Without the Forecaster, you'd have to manually tell the system "I need to keep €X liquid for the next Y months". With it, the system reads your past behaviour and figures it out.

#### Strategist · the portfolio constructor
Receives the Forecaster's liquidity buckets, queries **live US Treasury yields via Alpaca Market Data**, and constructs a 3-rung ladder:

| Rung | Tickers | What it covers |
|---|---|---|
| Short (0–3 mo) | SGOV, BIL | Cash that might be needed in the next 90 days |
| Mid (3–12 mo) | SHV | Cash free between 90–180 days |
| Long (12–36 mo) | SHY | The "lockable" surplus the Forecaster identified |

Outputs a typed `Allocation` object with specific tickers, USD amounts per line, and the blended yield. Every line is a real ticker tradeable on Alpaca.

#### Risk Officer · the IPS enforcer (★ veto power)
The agent that makes the demo land. Reads the Strategist's proposal and validates against `policy.yaml` — the customer's Investment Policy Statement. Rules include: max % per single ETF, max duration, allowed asset classes, minimum liquidity floor, minimum credit rating.

If anything fails, it **vetos and returns a violation list** — e.g. `{"rule": "max_pct_single_etf=60", "actual": 100, "field": "BIL"}`. The Strategist then revises with surgical fixes (split BIL into BIL+SGOV, reduce SHY allocation, etc.) and resubmits. **Up to 3 revisions, then it surrenders and asks the user.**

This loop is what makes the live demo look like a real institution debating with itself.

#### Executor · the broker hand
Only invoked when the user types `approve` AND there's a stored proposal awaiting approval. Places real **paper trades** on Alpaca for each line of the allocation, polls fills, returns confirmations with `order_id`. Critical guard: it can't run unless the proposal is on the state object — no surprise trades, ever.

#### CFO Synthesis · the translator
Reads every typed output upstream (forecast, proposal, risk verdict, execution result) and turns dense JSON into one paragraph the founder can actually read in three seconds. Asks for explicit approval if there's a pending proposal. Sets the conversation flag so the next user turn maps to the `approve` intent.

#### What-If · the simulator
Side-channel agent for hypotheticals. "What if rates drop 50bps next quarter?" "What if we close another round?" Re-runs the Forecaster and Strategist with adjusted parameters but **commits nothing**. Useful for the demo question: "what if rates drop?" — agent shows the projected impact without touching the live portfolio.

#### Education · the explainer
Pure exposition. "What's a T-bill ladder?" "Why duration risk?" "What's an IPS?" No tools, no state changes — just a teaching response. Lets the customer learn without leaving the chat.

---

## 3. Target customers

We sell to **any small EU company with €500k+ idle cash**. We don't gate by stage, sector, or funding status.

### The three personas we design for

#### Founders & owners
Bootstrapped, funded, profitable — doesn't matter. They have €500k–€10M sitting in a checking account and they know it should work harder. They don't have time to read a fixed-income textbook and can't afford a fractional CFO.

**What they care about:** getting it set up in under an hour, not screwing up something legal, knowing they can pull cash back if needed.

#### First-time finance hires
Recently joined a growing company as Head of Finance / VP Finance. The board wants a treasury memo. They want a quick, defensible win. Public T-bill ladder is the textbook conservative choice — but constructing one is annoying.

**What they care about:** an audit trail they can show the board, a customisable IPS they can defend, ability to interrogate every decision.

#### Operations leaders
COO or Head of Ops at a 50–200 person company. Finance is one of five hats. They want a tool that just works without weeks of evaluation.

**What they care about:** zero ongoing maintenance, embeddable into their existing stack, no surprises.

### Customer signals (the qualifying criteria)

A customer is a fit if **all four** are true:

1. **EU-based** (single jurisdiction, single currency, single regulator path)
2. **€500k+ idle cash** that's not earmarked for the next 90 days
3. **No existing treasury function** (no in-house CFO with a Bloomberg terminal)
4. **Receptive to AI** (founder/team has used Cursor, Claude, or similar — won't reflexively reject "AI" branding)

If any of those is false, we politely defer and revisit later.

---

## 4. Go-to-market strategy

We do this in two phases. Each phase has a different motion, a different unit economics profile, and a different moat.

### Phase 1 (months 0–18) · Direct to startups & SMBs

**Goal:** prove demand, capture €100M–€500M AUM, build the case study muscle.

**Channels (in priority order):**

1. **Founder-network / VC portfolios.** Single biggest channel. Get one or two well-respected European VCs to share us in their portfolio Slack / quarterly portfolio email. ROI is enormous because it's pre-qualified (Series A founder + warm intro = ~30% conversion in private banking, we expect ~10% direct).
2. **Accelerator partnerships.** Y Combinator (EU companies), Seedcamp, Antler, Techstars Berlin. We offer their portfolio companies a discounted rate (15 bps instead of 20) for the first 12 months. The accelerator gets to say "your treasury is solved" as part of their value prop.
3. **Founder content.** One sharp essay per month on the actual mathematics of corporate cash management — *"Why your accountant won't tell you about the 4% you're losing"*, *"The 3-rung ladder explained"*. Distribute via Hacker News, EU founder Twitter, LinkedIn. Goal: capture the technically-curious founder who'd self-build otherwise.
4. **Programmatic / partnerships with neobanks.** Soft co-marketing with Qonto / Pleo / Spendesk *before* phase 2 embed. They list us in their "marketplace" / "trusted partners" page in exchange for revenue share on referred customers.

**Pricing:** 20 bps of AUM, no minimum, no setup fee, no subscription.

**Targets at end of phase 1:**
- 100–500 paying customers
- €100M–€500M AUM
- ARR of €200k–€1M (margin >90%)
- 2–3 design partners willing to be public references

**Why this matters:** direct customers are how we get **proof points and case studies**. Every 6 months we publish "European startups using Treasury AI saved €X in 2026". That data is the wedge that makes phase 2 trivial.

### Phase 2 (months 18+) · White-label embed in business banks

**Goal:** become invisible infrastructure. The product nobody sees, but every neobank ships.

**Targets:** Qonto · Revolut Business · Pleo · Spendesk · Payhawk · N26 Business · Memo Bank.

**The motion:** instead of acquiring customers one by one, we sign one bank that has 10,000+ business customers. We embed a "Treasury" button inside their existing dashboard. When a customer clicks it, they're chatting with our agent — branded as the bank's product.

**Pricing:** modest setup fee (€50k–€100k) + **25/75 revenue share** on the AUM fee. Bank takes 75% (their customer relationship), we take 25%. On €1B AUM that's €500k ARR for us per partner — and we have multiple partners.

**Why banks embed us instead of building it:**
- Building a multi-agent treasury manager from scratch is a 6–12 month project. We did it in a weekend. Their CTO won't, their engineers shouldn't.
- Their customers are already defecting to us in phase 1. Banks notice the churn and capitulate.
- Regulatory liability is on us, not them — we're the investment advisor, they're just the distribution channel.

**What this unlocks:** a single Qonto deal puts us in front of 500,000+ EU businesses overnight. Capture 5% of those = 25,000 customers. At an average €2M AUM each = €50B AUM. At our 25% share of 20 bps = **€25M ARR from one bank.**

### Why phase 1 → phase 2 is the right sequence

You can't sell white-label to a neobank without proof points. They'll ask: "show me your customer references." Phase 1 generates those. Phase 1 also gives us the data — *"our average customer earns €87k more than they did in checking"* — that makes the embed pitch undeniable.

---

## 5. Customer acquisition unit economics (rough)

| Metric | Phase 1 (direct) | Phase 2 (embed) |
|---|---|---|
| CAC | €500–€2,000 (founder content + warm intros) | €50k–€100k setup + 12mo of integration |
| Customer LTV | €30k–€100k (€3M AUM × 20bps × 5–15yr) | €5k+/account × 10k+ accounts |
| Payback | 3–6 months | 6–12 months per bank deal |
| Gross margin | ~92% (pure software, Alpaca takes execution fees, Anthropic takes inference) | ~80% (rev share with bank) |
| Churn | <5%/yr (high switching cost — they trust the IPS enforcement) | <2%/yr (embedded in bank's UX) |

**The economics argument to investors:** phase 1 funds itself by month 12. Phase 2 multiplies AUM by 10–100x with no proportional increase in cost.

---

## 6. Competitive landscape (honest version)

### Direct EU competitors

**None at this exact intersection.** EU has robo-advisors for retail (Indexa, Moneyfarm, Scalable) but they don't do **business** treasury. They don't read bank transactions. They don't have an approval workflow. They don't expose individual agents. They charge 30–43 bps.

### Adjacent competitors

- **Mercury Treasury** (US-only) — closest analog, captured $4B AUM in 2 years post-SVB. Doesn't operate in Europe.
- **Brex Treasury** (US-only) — same.
- **Wise Interest / Revolut Vault** — capped 1–2% yields, not real treasury, retail-grade.
- **Private bank treasury services** — €1M+ minimums, opaque pricing, slow.
- **Interactive Brokers + spreadsheet** — DIY. Always available. Most of our customers tried this for 2 weeks and gave up.

### What protects us

1. **Speed to market.** We shipped this in a weekend. By the time a competitor reads this brief, we have 50 paying customers.
2. **Multi-agent UX is genuinely different.** Customers can sidebar agents. That's a real product feature; copying it requires re-architecting from scratch.
3. **Phase 2 lock-in.** Once embedded in Qonto / Pleo, we're the default for anyone using those banks. Switching out us = the bank ripping out a feature their users like.
4. **EU regulatory familiarity.** Mercury would need 18 months of regulatory work to enter EU. We're EU-native from day 1.

---

## 7. Stack & operational reality

| Layer | Tool | Why |
|---|---|---|
| Multi-agent orchestration | **LangGraph** | Stateful, checkpointed, built for branching workflows. |
| LLM | **Anthropic Claude Sonnet 4.6** | Best reasoning for structured-output extraction; lowest hallucination rate on financial JSON. |
| Brokerage | **Alpaca Trading API + Broker API** | Same infra as Stash/Public/M1. Paper environment is identical to prod. |
| Bank data | **MCP server** (FastMCP, stdio) | Demo uses pre-seeded SQLite of Acme's 3 years of transactions. Production: PSD2 / Tink / Plaid. |
| Hosting | **Orca** | Multi-agent mesh runtime. Each agent queryable individually. |
| Web | **FastAPI + Python** | Single `/api/v1/send_message` endpoint. |
| Config | YAML (`policy.yaml`, `company_profile.yaml`) | Customer's IPS lives in code, not in someone's head. |
| State | LangGraph `MemorySaver` | Per-thread checkpointer; proposals persist across user turns. |

---

## 8. The simplest version of the pitch

> *Every small European company has €500k–€10M sitting in checking earning under 1%. T-bills pay 4%+. The gap is real money but no one captures it because brokerage paperwork, IPS drafting, cashflow forecasting, and monthly rebalancing add up to weeks of work no one has. We do all of it with a multi-agent AI that reads your bank account, builds a T-bill ladder, validates it against your investment policy, and executes after you approve. 20 bps, no minimum, EU-native. Phase 1: direct to startups. Phase 2: embed inside every European business bank.*

That's the company.

---

*Last updated 2026-04-26 · MADHACK build · Madrid*
