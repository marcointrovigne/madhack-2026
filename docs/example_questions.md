# Example Questions

How a user (or judge) interacts with Treasury AI. Each question type maps to a specific path through the agent graph.

## 1. Status / Read — "show me"

Routes to the Portfolio Reader. Fast path — no Forecaster, no Strategist, no Risk Officer.

| User question | What happens |
|---|---|
| *"What's my current balance?"* | MCP `get_client` + Alpaca `get_account` → "$325k in Qonto, $0 invested" |
| *"Show me my positions."* | Alpaca `list_positions` → markdown table of holdings + P&L |
| *"What did I spend on payroll last month?"* | MCP `get_statement(last 30d)` filtered by category=payroll |
| *"How much yield have I earned to date?"* | Alpaca `list_positions` + price history → cumulative gains |
| *"Last 10 transactions."* | MCP `list_movements(limit=10)` → table |

**Latency:** 2–4 seconds (one tool round-trip + one short LLM composition).

## 2. Forecasting / Analysis — "explain"

Routes to the Forecaster. Pulls 90 days + 360 days of categorised transactions, projects forward.

| User question | What happens |
|---|---|
| *"What's my monthly burn?"* | Forecaster averages last 90 days of negative ops + payroll + tax |
| *"How much runway do I have?"* | balance / monthly_burn_usd |
| *"When's my next big outflow?"* | Forecaster scans planned_outflows + recurring patterns |
| *"How much cash can I lock up for 6 months?"* | Forecaster's `lockable_long_term` |
| *"Is my burn trending up or down?"* | Forecaster compares last 90d vs prior 90d |

**Latency:** 8–15 seconds (multiple MCP tool calls + analysis LLM call).

## 3. Strategy / Advice — "what should I do?"

Full deploy pipeline: Forecaster → Strategist → Risk Officer → CFO Synthesis. May trigger the revision loop.

| User question | What happens |
|---|---|
| *"We just got $50k extra cash, what do we do?"* | Full pipeline. Forecast updates, Strategist proposes ladder, Risk validates, founder asked to approve. |
| *"BIL or SHY — which is better right now?"* | Strategist alone with explain mode. Compares yield curves and explains tradeoff. |
| *"Is my current allocation optimal?"* | Strategist re-analyses existing positions vs. forecast. May propose rebalance. |
| *"Should I increase my long-term lockup?"* | Strategist + Risk Officer. Considers policy lockup ceiling. |

**Latency:** 15–30 seconds (multiple LLM calls + market data fetch + possible revision loop).

## 4. Action / Execution — "do it"

Routes to the Executor. Requires a previously approved proposal in state.

| User question | What happens |
|---|---|
| *"Approve."* / *"Yes, go."* / *"Execute the proposal."* | Executor places trades via Alpaca paper Trading API. |
| *"Sell $50k of BIL."* | Manual sell flow (MVP routes to Portfolio Reader → user clarifies → Executor) |
| *"Rebalance to current targets."* | Strategist (rebalance mode) → Risk Officer → Executor |

**Latency:** 5–10 seconds for execution.

## 5. What-if / Simulation — "what if..."

Routes to the What-If node — runs Forecaster with a hypothetical applied.

| User question | What happens |
|---|---|
| *"What if interest rates drop 50bps next quarter?"* | Strategist re-runs with adjusted yield assumptions |
| *"What if we lose our biggest customer?"* | Forecaster re-runs with reduced revenue inflow |
| *"What if our Series B gets pushed to Q4?"* | Forecaster re-runs with delayed cash injection |
| *"What happens if I withdraw $200k tomorrow?"* | Forecaster's liquidity check + which positions to sell |

**Latency:** 8–15 seconds (Forecaster with adjusted assumptions).

## 6. Education / Q&A — "explain"

Routes to the Education node. Pure LLM, no tools, fast.

| User question | What happens |
|---|---|
| *"What's a T-bill?"* | Short, founder-friendly explanation |
| *"Why are you recommending BIL over SGOV?"* | Strategist explanation mode with the actual numbers |
| *"What's duration risk?"* | Concept explanation, possibly tied to current portfolio |
| *"Show me my investment policy."* | Risk Officer explanation mode — dumps the IPS in markdown |
| *"Why can't we put 100% in SHY?"* | Risk Officer explains the relevant rule |

**Latency:** 2–5 seconds.

## Suggested demo script (3-minute pitch)

A high-impact 5-question script that exercises every major path:

1. **(Status)** *"Hi, I'm Pablo, the founder of Acme. Show me where my cash is."*
   - Demonstrates: live MCP integration, Alpaca account read, clean status report.

2. **(Forecasting)** *"What's my burn rate, and how much can I safely invest?"*
   - Demonstrates: Forecaster's depth (3 years of categorised history), structured liquidity analysis.

3. **(Strategy)** *"We just got $50k extra cash. What do we do with it?"*
   - Demonstrates: full multi-agent pipeline, the **Risk Officer catching a violation and forcing the Strategist to revise** (this is the wow moment), proposal presented for approval.

4. **(What-if — sidebar)** *"What if rates drop 50bps next quarter?"*
   - Demonstrates: simulation capability without committing trades.

5. **(Action)** *"Approve."*
   - Demonstrates: live paper-trade execution, fill confirmations.

6. **(Verification)** *"Show me my new portfolio."*
   - Demonstrates: closed loop — proposal → execution → confirmation visible in Alpaca.

## Hardballs judges may throw

Be ready for these — each maps to an existing capability:

| Hardball | Path |
|---|---|
| *"Show me your investment policy and explain each rule."* | Risk Officer explanation mode |
| *"What if regulators force you to liquidate everything tomorrow?"* | Forecaster + Executor (sell all) |
| *"Why should I trust an AI with my money?"* | Education mode + every trade requires explicit approval |
| *"Walk me through how you make a buy decision."* | CFO Synthesis recaps the Forecast → Proposal → Risk verdict reasoning trail |
| *"What if I want to change the policy?"* | We update `config/policy.yaml` and the Risk Officer immediately validates against the new rules |
