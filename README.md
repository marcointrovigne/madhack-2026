# Treasury AI

Multi-agent AI treasurer for European startups — built for the **MADHACK FinTech Hackathon** (April 26, 2026).

A startup with idle cash chats with the agent. Behind the scenes a team of seven specialised agents (CFO Router, Forecaster, Strategist, Risk Officer, Executor, CFO Synthesis, plus a Portfolio Reader for status queries) collaborates to forecast cashflow, build a US-Treasury-bill ladder using live Alpaca quotes, validate against a written investment policy, and execute paper trades after explicit approval.

> **Mercury Treasury for Europe — AI-native, embeddable, 20 bps of AUM.**

## Architecture

- **LangGraph** orchestrates 7 nodes through a shared state object
- **Bank data** comes via an MCP server (`bank-mcp/`) — emulates a customer's bank account with 3 years of categorised transactions
- **Brokerage** is opened on the customer's behalf via **Alpaca Broker API** (sandbox) — Treasury AI never holds funds; Alpaca custodies in the customer's own account
- **Market data** uses Alpaca paper Trading + Market Data APIs
- **Execution** goes through `submit_order_for_account(account_id, ...)` on the customer's brokerage account
- **Orca** hosts the public-facing chat agent
- **Anthropic Claude Sonnet 4.6** is the reasoning engine

See `docs/agents.md` for the agent-by-agent design and `docs/concept.md` for the product story.

## Project layout

```
.
├── main.py                    # Orca-facing entry point (process_message)
├── agents/                    # LangGraph multi-agent system
│   ├── state.py               # TreasuryState — shared across all nodes
│   ├── nodes.py               # The 7 node functions
│   ├── graph.py               # Graph builder + run_graph()
│   ├── broker.py              # Alpaca Broker API: account creation, funding, on-behalf-of orders
│   ├── tools.py               # Market Data tools + bank MCP client + broker tool re-exports
│   ├── llm.py                 # Shared ChatAnthropic + prompt loader
│   └── prompts/               # System prompts (markdown)
├── config/
│   ├── policy.yaml            # Investment Policy Statement (Risk Officer's bible)
│   └── company_profile.yaml   # Customer profile (Acme)
├── bank-mcp/                  # Local copy of the bank-account-mock MCP server
│   ├── mcp_server.py          # FastMCP stdio server
│   ├── main.py                # Optional FastAPI HTTP server (port 8010)
│   ├── bank_service.py        # SQLite-backed mock bank
│   └── data/bank_mock.sqlite3 # Pre-seeded with 3 years of Acme transactions
├── scripts/
│   ├── setup_account.py       # One-shot: open + fund Acme's brokerage account
│   └── smoke.py               # End-to-end smoke test
├── docs/                      # Pitch + landing-page + agents docs
└── .env                       # Alpaca paper keys + Anthropic key
```

## Running locally

### 1. Install dependencies

```bash
uv sync
```

### 2. Confirm `.env` has the required keys

```bash
# Market Data + Trading (paper) — used for live quotes
APCA_API_KEY_ID=...
APCA_API_SECRET_KEY=...

# Broker API (sandbox) — used for customer account ops + execution
BROKER_API_KEY_ID=...
BROKER_API_SECRET_KEY=...

# Anthropic
ANTHROPIC_API_KEY=...
```

The bank MCP is auto-spawned as a subprocess by the agent — no separate startup needed.

### 3. Open + fund Acme's brokerage account (one-time)

```bash
uv run python scripts/setup_account.py
```

This idempotently creates a sandbox brokerage account via Broker API, then requests an INCOMING ACH transfer ($50k — the sandbox daily cap). The account_id is persisted to `config/acme_account.json` so subsequent runs reuse it.

### 4. Smoke test

```bash
uv run python scripts/smoke.py "What's my current cash situation?"
```

Try the full deploy flow:

```bash
uv run python scripts/smoke.py "We just got 50,000 extra cash. What do we do?"
```

### 5. Run the Orca-facing app

```bash
uv run python main.py
# → http://localhost:8000
```

Then in a separate terminal, expose it via the Orca tunnel and connect from the Orca admin panel:

```bash
orca tunnel 8000
```

Copy the public URL into Orca admin → Connect Agentic System → endpoint `/api/v1/send_message`.

## Demo script (3-minute)

```
User: Hi, show me where my cash is.
        → Portfolio Reader returns bank + Alpaca status

User: What's my burn rate, and what can I deploy long-term?
        → Forecaster reads 3 years of MCP data + projects forward

User: We just got $50k extra cash. What do we do?
        → Forecaster + Strategist + Risk Officer + CFO Synthesis
        → "Approve?" prompt presented

User: What if rates drop 50bps next quarter?  (sidebar simulation)
        → What-If node re-runs Forecaster with adjusted assumption

User: approve
        → Executor places live paper trades on Alpaca
        → Confirmation with fill prices

User: Show me my new portfolio.
        → Portfolio Reader confirms positions
```

## Key files for the pitch

- `docs/concept.md` — what we're building and why
- `docs/agents.md` — agent-by-agent technical design
- `docs/example_questions.md` — the 6 question types the agent handles
- `docs/user_journey.md` — onboarding through ongoing operation
- `docs/business.md` — GTM, pricing, market, competitors
- `docs/pitch.md` — slide-by-slide deck content
- `docs/landing_page.md` — hero/section/CTA copy for the marketing site

## Stack

| Layer | Tool |
|---|---|
| Multi-agent orchestration | LangGraph |
| LLM | Anthropic Claude Sonnet 4.6 (`claude-sonnet-4-6`) |
| Bank data | Bank-account-mock MCP (FastMCP, stdio) |
| Brokerage / market data | Alpaca paper Trading + Market Data APIs |
| Hosting / mesh | Orca |
| Web framework | FastAPI |
| State persistence | LangGraph `MemorySaver` (per-thread checkpointer) |
| Config | YAML (`policy.yaml`, `company_profile.yaml`) |
