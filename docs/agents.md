# Agent Architecture

Treasury AI is a multi-agent system orchestrated with **LangGraph**. Each agent has a narrow, well-defined role with explicit inputs and outputs. Agents don't call each other — they share a state object that the graph routes through.

## Why multi-agent

A real-world corporate treasury function is naturally split across multiple specialists:
- A cashflow analyst (Forecaster)
- A portfolio manager (Strategist)
- A compliance officer / risk manager (Risk Officer)
- An execution trader (Executor)
- A communications layer / CFO (Synthesis)

Modeling it as a single monolithic agent would conflate responsibilities, weaken auditability, and make the demo feel less like a real institution. By splitting roles:
- Each agent's prompt is focused and shorter (better LLM performance)
- Each is independently testable
- Conflicts (Risk Officer rejects Strategist's proposal) become first-class graph events
- Each can be queried separately via the Orca mesh ("let me ask the Risk Officer directly about your policy")

## State object

All inter-agent communication flows through a single shared state (`agents/state.py`). Each node reads the slice it needs and writes its slice. There are no direct function calls between agents.

Key fields:
- `user_message`, `conversation_history` — the conversation
- `company_profile`, `policy` — static context loaded once
- `intent` — classified by CFO Router
- `forecast` (ForecastOutput) — Forecaster's output
- `proposal` (Allocation) — Strategist's output
- `risk_verdict` (RiskVerdict) — Risk Officer's verdict
- `execution_result` (ExecutionResult) — Executor's fills
- `cfo_response` — final natural-language reply
- `awaiting_approval` — flag set when a proposal is pending user approval

## The seven agents

### 1. CFO Router

**Role:** Entry node. Classifies the user's intent into one of 7 buckets and routes accordingly.

**Implementation:** Single LLM call with structured output (Pydantic). Uses a hot-path heuristic to skip the LLM when the user's awaiting-approval reply is a simple "approve" / "yes" / "go".

**Intents:**
- `deploy` — invest new cash
- `withdraw` — pull cash back
- `status` — show current state
- `what_if` — simulation question
- `education` — explain a concept
- `approve` — user confirming a proposal
- `unknown` — fallback

When `intent == "deploy"`, the router also resets transient state (`forecast`, `proposal`, `risk_verdict`, `proposal_revision`, `execution_result`, `awaiting_approval`) so a fresh deploy doesn't reuse stale data from a prior turn.

### 2. Portfolio Reader

**Role:** Read-only status agent. Answers "what's my balance", "show positions", "recent transactions".

**Implementation:** ReAct-style tool-calling loop. The LLM has access to:
- Bank MCP tools (`get_client`, `list_movements`, `get_statement`, `list_company_policies`)
- Alpaca read tools (`alpaca_get_account`, `alpaca_list_positions`, `alpaca_get_latest_quote`)

It decides which tools to call based on the question, then composes a clean markdown response.

**Output:** Direct natural-language reply (skips CFO Synthesis).

### 3. Forecaster

**Role:** Analyses the company's historical cashflow and projects future liquidity needs.

**Implementation:**
1. **Python pre-fetches** the data (deterministic):
   - `get_client(client_id)` — current balance
   - `get_statement(last 90 days)` — recent transactions
   - `get_statement(90-360 days back)` — older history for trend analysis
   - `get_company_policy(client_id)` — the bank-side policy (DCA, target reserves)
2. **LLM analyses** the raw data and produces a structured `ForecastOutput`:
   - `current_balance_usd`
   - `monthly_burn_usd`, `monthly_recurring_inflow_usd`
   - `liquid_required_30d/90d/180d` — cumulative cash needs by horizon
   - `lockable_long_term` — what's free to lock up >180d
   - `key_outflows_next_180d` — list of significant scheduled outflows
   - `confidence` (high/medium/low) and `reasoning`

The bank MCP movements are **pre-categorised** (revenue, ops, payroll, tax, financing, safeguard) by the bank service, so the Forecaster doesn't re-classify — it trusts the categories.

### 4. Strategist

**Role:** Constructs a T-bill ladder optimised for yield given the Forecaster's liquidity constraints.

**Implementation:**
1. **Python pre-fetches** live quotes for SGOV, BIL, SHV, SHY via Alpaca Market Data.
2. **LLM constructs** the optimal allocation respecting:
   - Forecaster's liquidity constraints
   - Policy: max single-ETF %, max duration months, min liquidity %, allowed tickers
   - On revisions: the Risk Officer's specific violations from the previous proposal
3. Outputs structured `Allocation`:
   - `lines: [{ticker, amount_usd, duration_bucket, est_yield_pct}]`
   - `total_deployed_usd`, `cash_buffer_usd`
   - `blended_yield_pct`, `annual_yield_usd`
   - `rationale`

### 5. Risk Officer

**Role:** Validates the Strategist's proposal against the IPS. Has veto power.

**Implementation:**
- **Pure Python rule engine** (deterministic, defendable, no LLM needed for the validation logic):
  - Allowed tickers whitelist
  - Single-ETF cap (`max_pct_single_etf`)
  - Weighted-average duration cap (`max_duration_months`)
  - Liquidity floor (`min_daily_liquidity_pct`)
  - Lockup ceiling (`max_total_lockup_pct`)
- LLM only used for phrasing the verdict in user-friendly language.

**Output:** `RiskVerdict { passed, violations[], suggestions }`.

When `passed=False`, the graph routes back to the Strategist with the violations attached. The Strategist revises. Up to 3 iterations before giving up.

### 6. Executor

**Role:** Places the trades on Alpaca paper account after user approval.

**Implementation:**
- **Pure Python** (no LLM needed — this is mechanical execution):
  - Read account buying power (`alpaca_get_account`)
  - For each line in `proposal.lines`:
    - Get latest ask price (`alpaca_get_latest_quote`)
    - Compute fractional share count
    - Submit market order (`alpaca_submit_order`)
  - Aggregate fills, compute remaining cash, capture errors

**Output:** `ExecutionResult { fills, total_deployed_usd, remaining_cash_usd, errors }`.

### 7. CFO Synthesis

**Role:** The human-facing voice. Composes the natural-language reply from structured agent outputs.

**Implementation:** LLM call with the full state as context, no tools. Friendly tone. Markdown tables for numbers. **Bold** key amounts. Ends deploy-flow responses with an explicit approval ask.

Two specialised variants:
- `education_node` — for explaining concepts (no tools, no state, just a quick LLM reply)
- `what_if_node` — runs the Forecaster with a hypothetical scenario before synthesis

## Graph topology

```
START → CFO Router →
  ├─ deploy   → Forecaster → Strategist → Risk Officer → ┬─ PASS    → CFO Synthesis (asks for approval) → END
  │                                                       └─ REJECT  → (if rev<3) Strategist
  │                                                                  → (if rev≥3) CFO Synthesis (apologetic) → END
  ├─ status   → Portfolio Reader → END
  ├─ what_if  → What-If → CFO Synthesis → END
  ├─ education → Education → END
  ├─ approve  → Executor → CFO Synthesis (confirms execution) → END
  └─ unknown  → CFO Synthesis (asks for clarification) → END
```

## State persistence across turns

The graph is compiled with `MemorySaver` checkpointer. Each Orca conversation gets a unique `thread_id`. State persists across user turns within the same thread.

This is what enables the two-turn approval flow:

- **Turn 1**: user says *"deploy €8M"* → graph runs deploy pipeline → CFO Synthesis produces "Approve?" → state persists with `awaiting_approval=True` and the validated proposal.
- **Turn 2**: user says *"approve"* → CFO Router sees `awaiting_approval=True` and message="approve" → intent=`approve` → Executor uses the persisted proposal → CFO Synthesis confirms execution.

## Sidebar queryability (Orca mesh)

In the MVP, only the CFO is registered as an Orca agent endpoint. The other six are internal LangGraph nodes.

In a Year 2 build-out, each agent would be a separately registered Orca agent — judges/users can query Forecaster directly ("what's my burn rate?") or Risk Officer directly ("show me your policy") without going through the orchestrator.
