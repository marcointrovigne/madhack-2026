# Alpaca Skills Design

**Date:** 2026-04-25
**Author:** marco (with Claude)
**Context:** MADHACK AI FinTech Hackathon, Sunday 2026-04-26
**Status:** Design — pending user review

## Goal

Build a set of Claude Code skills that let Claude fluently understand the Alpaca platform and generate working Python code against it during the MADHACK hackathon. The skills must cover all four Alpaca APIs because the team's hackathon track is decided on-site, so any subset risks being unhelpful.

The skills are **code-generator-first** with reference/Q&A as a secondary use. They activate when the user asks for Alpaca-related work in this project.

## Non-Goals

- Multi-language support (JS/Node). Python only via `alpaca-py`.
- A polished, distributable plugin. Project-local skills are enough for a one-day hackathon. A plugin wrapper can come later.
- Automated test suite for the skills. Manual smoke-tests are sufficient.
- Bundled offline copy of all 399 Alpaca doc pages. The skill uses curated references plus live fallback (Context7 / WebFetch).

## Architecture

### Four independent, sibling skills

```
mad-hack/.claude/skills/
├── alpaca-trading/        # orders, positions, watchlists, account
├── alpaca-market-data/    # stocks, crypto, options, news, historical/realtime
├── alpaca-broker/         # KYC, accounts, funding, ACH
└── alpaca-connect/        # OAuth flows
```

Each skill is fully self-contained. Authentication setup (~30 lines) is duplicated across all four — accepted as the cost of clean independence and reliable activation.

### Why project-local instead of user-level

- Lives with the hackathon codebase; can be committed and shared with teammates via git
- Auto-discovered when working in `/Users/marco/workspace/mad-hack`
- Easy to iterate during the build sprint without polluting the global skill space
- Scoped to this repo, no leakage into unrelated projects

### Why per-API split rather than one mega-skill

- Each skill activates only when relevant, keeping context lean
- Triggers can be specific (e.g. "place order" → trading; "latest quote" → market-data)
- Each skill stays small enough to read end-to-end without progressive disclosure overhead
- A teammate can disable or fork one without touching the others

## Skill Internal Structure

Each skill follows the same shape:

```
alpaca-{api}/
├── SKILL.md                 # entry: trigger + how-to-use
├── references/
│   ├── auth-setup.md        # env vars, install, paper vs live
│   ├── sdk-reference.md     # alpaca-py classes/methods for this API
│   └── recipes.md           # 5–8 canonical Python code patterns
└── scripts/
    └── check_setup.py       # smoke-test: 1 read-only API call
```

### SKILL.md contract

- ~80 lines, focused on triggering and routing
- Frontmatter:
  - `name`: the skill name
  - `description`: rich trigger phrases tailored to that API's vocabulary
- Body sections:
  - **When invoked** — checklist: confirm `alpaca-py` installed; verify env vars; load relevant reference; fall back to Context7 / WebFetch for niche specifics
  - **Quick reference** — 10–15 lines naming the most-used SDK entry points so Claude can answer simple questions without loading reference files
  - **Pointer to references/** — explicit instructions on which file to read for which class of question

### Tools each skill needs

- `Read` — load reference files
- `Edit`, `Write` — produce code
- `Bash` — `uv add alpaca-py`, run `check_setup.py`
- `WebFetch` — live doc lookup against `docs.alpaca.markets`
- Context7 MCP tools — alternative live doc lookup for `alpaca-py`

## Content Sourcing

### `auth-setup.md` (hand-written, small, stable)

- Env var names: `APCA_API_KEY_ID`, `APCA_API_SECRET_KEY` (paper) / `APCA_API_KEY_ID_LIVE` etc. for live
- Paper vs live base URLs
- Install: `uv add alpaca-py` (project uses `pyproject.toml`)
- Minimal "first call" snippet that proves keys work
- Source material: `docs/Alpaca_Starter_Guide.pdf` + the per-API getting-started pages on `docs.alpaca.markets`

### `sdk-reference.md` (extracted from `alpaca-py`)

- Source: `alpaca-py` GitHub repo — README, `__init__.py` exports, public class/method signatures, request/response Pydantic models for that API
- Trading: `TradingClient`, order request models (`MarketOrderRequest`, `LimitOrderRequest`, `StopOrderRequest`, `StopLimitOrderRequest`, `TrailingStopOrderRequest`), `Position`, `Asset`, `Watchlist`, `OrderSide`, `TimeInForce`
- Market Data: `StockHistoricalDataClient`, `CryptoHistoricalDataClient`, `OptionHistoricalDataClient`, `*StreamClient`, request types (`StockBarsRequest`, `CryptoLatestQuoteRequest`, etc.), `Bar`, `Quote`, `Trade`, `News`
- Broker: `BrokerClient`, `Account`, `Contact`, `Identity`, `Disclosures`, `Agreement`, `ACHRelationshipRequest`, `TransferRequest`, `JournalRequest`
- Connect: OAuth helpers and constants

### `recipes.md` (hand-written, hackathon-aimed)

5–8 working snippets per skill, drawn from the MADHACK idea list in `docs/pre_event_prep.md`.

**alpaca-trading recipes**
1. Connect & verify (`TradingClient(...).get_account()`)
2. Place market / limit / bracket order (with stop-loss + take-profit)
3. Stream order updates over WebSocket
4. Get / close all positions, get position by symbol
5. DCA scheduler skeleton (buy €X every N days)
6. Natural-language → order parser pattern (LLM tool call → `MarketOrderRequest`)

**alpaca-market-data recipes**
1. Latest quote / trade / bar for a symbol (stocks + crypto)
2. Historical bars (range, timeframe, adjustments)
3. Real-time stream: stocks, crypto, news (WebSocket)
4. Multi-symbol snapshot for a dashboard
5. News feed ingestion → sentiment hook
6. Options chain + greeks fetch

**alpaca-broker recipes**
1. Create account (KYC payload: contact, identity, disclosures, agreements)
2. Fund account: ACH relationship + transfer
3. List accounts, get account, update account
4. Place trade on behalf of an end-user account
5. Journal cash between accounts (round-ups, allowances)
6. Webhooks for account events

**alpaca-connect recipes**
1. OAuth2 authorization flow (auth URL → token exchange)
2. Refresh token handling
3. Use an access token with `TradingClient` on behalf of an OAuth user

### Live fallback

When the skill's references don't cover the user's specific question:

1. **Context7** — `mcp__plugin_context7_context7__query-docs` for the `alpaca-py` library
2. **WebFetch** — `https://docs.alpaca.markets/reference/<endpoint>` for niche REST details

The skill instructions explicitly tell Claude when to escalate to live fallback so it doesn't try to fabricate signatures.

## Activation / Triggering

Skill descriptions are written so the right one fires for the right job:

- `alpaca-trading` — "place order", "bracket order", "buy stock", "alpaca position", "Trading API", "alpaca-py orders", "stop loss"
- `alpaca-market-data` — "latest quote", "historical bars", "alpaca stream", "market data", "options chain", "news feed"
- `alpaca-broker` — "Broker API", "create alpaca account", "ACH", "KYC", "fund account", "journal"
- `alpaca-connect` — "Alpaca OAuth", "Connect API", "third-party Alpaca app"

Multiple skills can co-activate when a task spans APIs (e.g. "build a robo-advisor that takes a deposit and places orders" pulls in broker + trading).

## Error Handling

The skills themselves don't run code — they instruct Claude on patterns. The error-handling expectations Claude should generate into produced code:

- Always check `APCA_API_KEY_ID` / `APCA_API_SECRET_KEY` are set before constructing a client
- Default to paper environment unless the user explicitly says live
- Wrap network calls in try/except for `alpaca.common.exceptions.APIError`
- For streaming clients, surface reconnect/heartbeat patterns from `alpaca-py` rather than reinventing them

`check_setup.py` script, when run, exits non-zero with a clear message if env vars are missing or `get_account()` fails — this catches the most common hackathon-day setup mistake.

## Testing & Validation

Skills are prompt artifacts; "tests" are real-conversation smoke tests.

**Per-skill manual verification (after build):**
- Open a fresh chat, ask for a recipe-covered task — verify the right skill activates and produces working code
- Ask for an off-recipe specific endpoint — verify it falls back to Context7 / WebFetch correctly

**Connectivity check (per skill):**
- `python .claude/skills/alpaca-{api}/scripts/check_setup.py` runs one read-only call and reports success/failure

**No automated test suite.** Cost/value doesn't justify it for a one-day hackathon artifact.

## Build Sequence

1. Create `.claude/skills/` directory structure for all four skills
2. Write `auth-setup.md` once, copy to all four (with per-API client class adjusted)
3. Build `alpaca-trading` end to end (SKILL.md + sdk-reference.md + recipes.md + check_setup.py)
4. Smoke-test alpaca-trading in a fresh chat
5. Repeat 3–4 for `alpaca-market-data`, `alpaca-broker`, `alpaca-connect`
6. Final smoke test: a multi-skill task that pulls in two skills (e.g. broker + trading)

Estimated effort: 2–3 hours total.

## Open Questions

None blocking. Build can start immediately after user spec review.
