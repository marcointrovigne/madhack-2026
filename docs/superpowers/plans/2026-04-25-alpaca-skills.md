# Alpaca Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build four project-local Claude Code skills (`alpaca-trading`, `alpaca-market-data`, `alpaca-broker`, `alpaca-connect`) that let Claude generate working Python code against Alpaca's APIs during the MADHACK hackathon.

**Architecture:** Four sibling, self-contained skills under `.claude/skills/`. Each ships a lean `SKILL.md` plus three `references/` files (auth setup, SDK reference, recipes) and one `scripts/check_setup.py` smoke-test. Heavy content lives in references and is loaded only when needed; live fallback uses Context7 / WebFetch against `docs.alpaca.markets`.

**Tech Stack:** Python 3.11+, `alpaca-py` SDK, `uv` for dep management, Claude Code skill format.

**Spec:** `docs/superpowers/specs/2026-04-25-alpaca-skills-design.md`

---

## File Structure

```
mad-hack/
└── .claude/
    └── skills/
        ├── alpaca-trading/
        │   ├── SKILL.md
        │   ├── references/
        │   │   ├── auth-setup.md
        │   │   ├── sdk-reference.md
        │   │   └── recipes.md
        │   └── scripts/
        │       └── check_setup.py
        ├── alpaca-market-data/      # same shape
        ├── alpaca-broker/           # same shape
        └── alpaca-connect/          # same shape
```

**Responsibilities per file:**
- `SKILL.md` — trigger description + routing instructions (~80 lines)
- `references/auth-setup.md` — env vars, install, paper vs live, "first call" snippet
- `references/sdk-reference.md` — class names, method signatures, request/response models for that API
- `references/recipes.md` — 5–8 hackathon-aimed code patterns
- `scripts/check_setup.py` — single read-only API call that validates keys/connectivity

---

## Source Material (referenced throughout)

- `docs/Alpaca_Starter_Guide.pdf` — local PDF, has env var conventions and first-call examples
- `docs/pre_event_prep.md` — local, idea list informs recipe choices
- `https://github.com/alpacahq/alpaca-py` — canonical SDK source for `sdk-reference.md`
- `https://docs.alpaca.markets` — getting-started + REST reference, fall back via WebFetch
- Context7 MCP: query `alpaca-py` for live doc lookup

---

# Phase 1: Scaffolding

### Task 1: Create skills directory tree

**Files:**
- Create: `.claude/skills/alpaca-trading/references/`, `.claude/skills/alpaca-trading/scripts/`
- Create: same under `alpaca-market-data/`, `alpaca-broker/`, `alpaca-connect/`

- [ ] **Step 1: Create all directories**

```bash
cd /Users/marco/workspace/mad-hack
for api in trading market-data broker connect; do
  mkdir -p ".claude/skills/alpaca-$api/references"
  mkdir -p ".claude/skills/alpaca-$api/scripts"
done
```

- [ ] **Step 2: Verify**

```bash
find .claude/skills -type d | sort
```

Expected:
```
.claude/skills
.claude/skills/alpaca-broker
.claude/skills/alpaca-broker/references
.claude/skills/alpaca-broker/scripts
.claude/skills/alpaca-connect
.claude/skills/alpaca-connect/references
.claude/skills/alpaca-connect/scripts
.claude/skills/alpaca-market-data
.claude/skills/alpaca-market-data/references
.claude/skills/alpaca-market-data/scripts
.claude/skills/alpaca-trading
.claude/skills/alpaca-trading/references
.claude/skills/alpaca-trading/scripts
```

---

### Task 2: Confirm `alpaca-py` is installed in the project

**Files:**
- Modify (if needed): `pyproject.toml`

- [ ] **Step 1: Check current deps**

```bash
cd /Users/marco/workspace/mad-hack
grep -E "alpaca" pyproject.toml uv.lock 2>/dev/null || echo "NOT INSTALLED"
```

- [ ] **Step 2: Install if missing**

If the previous step printed "NOT INSTALLED":

```bash
uv add alpaca-py
```

- [ ] **Step 3: Verify import works**

```bash
uv run python -c "from alpaca.trading.client import TradingClient; print('ok')"
```

Expected output: `ok`

---

# Phase 2: alpaca-trading skill

### Task 3: Write `alpaca-trading/SKILL.md`

**Files:**
- Create: `.claude/skills/alpaca-trading/SKILL.md`

- [ ] **Step 1: Write the file**

```markdown
---
name: alpaca-trading
description: Use when writing Python code that places orders, manages positions, fetches account info, closes positions, or works with watchlists via Alpaca's Trading API (alpaca-py). Triggers include "place order", "bracket order", "buy stock", "sell stock", "alpaca position", "Trading API", "alpaca-py orders", "stop loss", "limit order", "DCA", "trading bot", "robo-advisor".
---

# Alpaca Trading API

Generate Python code against Alpaca's Trading API using the `alpaca-py` SDK.

## When invoked

1. Confirm `alpaca-py` is installed (check `pyproject.toml`; install with `uv add alpaca-py` if missing)
2. Confirm env vars `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY` are set; if not, point user at `references/auth-setup.md`
3. Default to **paper trading** unless the user explicitly says live (`paper=True` on `TradingClient`)
4. If the task matches a known pattern, read `references/recipes.md`
5. If the task needs class/method details, read `references/sdk-reference.md`
6. For uncovered specifics, escalate via Context7 (`mcp__plugin_context7_context7__query-docs` with library `alpacahq/alpaca-py`) or WebFetch against `https://docs.alpaca.markets/reference/`

## Quick reference

- Client: `from alpaca.trading.client import TradingClient`
- Order requests: `MarketOrderRequest`, `LimitOrderRequest`, `StopOrderRequest`, `StopLimitOrderRequest`, `TrailingStopOrderRequest`
- Enums: `OrderSide`, `TimeInForce`, `OrderClass`
- Models: `Position`, `Asset`, `Watchlist`, `Order`
- Streams: `from alpaca.trading.stream import TradingStream`

Bracket orders: pass `order_class=OrderClass.BRACKET` plus `take_profit=TakeProfitRequest(...)` and `stop_loss=StopLossRequest(...)`.

## Files

- `references/auth-setup.md` — keys, env vars, first-call check
- `references/sdk-reference.md` — full class/method index
- `references/recipes.md` — common code patterns
- `scripts/check_setup.py` — runs `get_account()` to validate setup
```

- [ ] **Step 2: Verify file is in place**

```bash
ls -la .claude/skills/alpaca-trading/SKILL.md
```

---

### Task 4: Write `alpaca-trading/references/auth-setup.md`

**Files:**
- Create: `.claude/skills/alpaca-trading/references/auth-setup.md`

- [ ] **Step 1: Read the local Alpaca starter PDF for canonical env var names**

Use the Read tool on `docs/Alpaca_Starter_Guide.pdf` and confirm the env var convention. The expected names are `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY`.

- [ ] **Step 2: Write the file**

```markdown
# Trading API — Auth & Setup

## Install

```bash
uv add alpaca-py
```

## Environment variables

Add to `.env` (paper credentials are fine for the hackathon):

```
APCA_API_KEY_ID=your_paper_key_id
APCA_API_SECRET_KEY=your_paper_secret
```

Load with `python-dotenv` or your shell.

## First call (verifies keys work)

```python
import os
from alpaca.trading.client import TradingClient

client = TradingClient(
    api_key=os.environ["APCA_API_KEY_ID"],
    secret_key=os.environ["APCA_API_SECRET_KEY"],
    paper=True,  # NEVER set False unless the user explicitly asks for live
)
account = client.get_account()
print(f"status={account.status} cash=${account.cash} equity=${account.equity}")
```

## Paper vs live

- Paper: `paper=True`, base URL `https://paper-api.alpaca.markets/v2`
- Live: `paper=False`, base URL `https://api.alpaca.markets/v2`
- **Default to paper.** Only switch to live if the user says so explicitly.
```

- [ ] **Step 3: Verify**

```bash
ls -la .claude/skills/alpaca-trading/references/auth-setup.md
```

---

### Task 5: Write `alpaca-trading/references/sdk-reference.md`

**Files:**
- Create: `.claude/skills/alpaca-trading/references/sdk-reference.md`

- [ ] **Step 1: Pull current `alpaca-py` Trading module surface**

Use Context7 with library `alpacahq/alpaca-py` and topic "trading client orders positions" — or WebFetch `https://github.com/alpacahq/alpaca-py/tree/master/alpaca/trading` and read `client.py`, `requests.py`, `models.py`, `enums.py`, `stream.py`.

Goal: capture the public class names, constructor args, method names, and the major request/response models. Do not paste full source — just signatures.

- [ ] **Step 2: Write the file**

The file MUST cover:

1. **`TradingClient`** — constructor (`api_key`, `secret_key`, `paper`, `raw_data`, `url_override`) and methods grouped by area:
   - Account: `get_account()`, `get_account_configurations()`, `set_account_configurations()`, `get_portfolio_history()`
   - Orders: `submit_order(order_data)`, `get_orders(filter)`, `get_order_by_id(order_id)`, `cancel_orders()`, `cancel_order_by_id(order_id)`, `replace_order_by_id(order_id, order_data)`
   - Positions: `get_all_positions()`, `get_open_position(symbol_or_asset_id)`, `close_all_positions(cancel_orders)`, `close_position(symbol_or_asset_id, close_options)`
   - Assets: `get_all_assets(filter)`, `get_asset(symbol_or_asset_id)`
   - Watchlists: `create_watchlist(...)`, `get_watchlists()`, `get_watchlist_by_id(...)`, `update_watchlist_by_id(...)`, `delete_watchlist_by_id(...)`, `add_asset_to_watchlist(...)`, `remove_asset_from_watchlist(...)`
   - Calendar/clock: `get_calendar(filters)`, `get_clock()`
   - Corporate actions: `get_corporate_announcements(filter)`

2. **Order request models** with their key fields:
   - `MarketOrderRequest(symbol, qty|notional, side, time_in_force, extended_hours?, client_order_id?, order_class?, take_profit?, stop_loss?)`
   - `LimitOrderRequest(... + limit_price)`
   - `StopOrderRequest(... + stop_price)`
   - `StopLimitOrderRequest(... + stop_price + limit_price)`
   - `TrailingStopOrderRequest(... + trail_price | trail_percent)`
   - `GetOrdersRequest(status?, limit?, after?, until?, direction?, nested?, side?, symbols?)`
   - `ReplaceOrderRequest(qty?, time_in_force?, limit_price?, stop_price?, trail?, client_order_id?)`
   - `ClosePositionRequest(qty?, percentage?)`
   - `TakeProfitRequest(limit_price)` and `StopLossRequest(stop_price, limit_price?)` (used inside bracket orders)

3. **Enums** with their values:
   - `OrderSide`: BUY, SELL
   - `TimeInForce`: DAY, GTC, OPG, CLS, IOC, FOK
   - `OrderClass`: SIMPLE, BRACKET, OCO, OTO
   - `OrderStatus`: NEW, PARTIALLY_FILLED, FILLED, CANCELED, EXPIRED, REPLACED, etc.
   - `AssetClass`: US_EQUITY, CRYPTO, US_OPTION
   - `PositionSide`: LONG, SHORT
   - `QueryOrderStatus`: OPEN, CLOSED, ALL

4. **Streaming** — `TradingStream(api_key, secret_key, paper=True)`
   - `subscribe_trade_updates(handler)` where handler is `async def handler(data: TradeUpdate)`
   - `run()` to start the loop, `stop()` to end it
   - `TradeUpdate` fields: `event`, `order`, `timestamp`, `position_qty`, `price`

Format each section with a short prose intro and a code block showing the import + constructor/usage. Keep total file under ~400 lines.

- [ ] **Step 3: Verify**

```bash
wc -l .claude/skills/alpaca-trading/references/sdk-reference.md
```

Expected: between 200 and 500 lines.

---

### Task 6: Write `alpaca-trading/references/recipes.md`

**Files:**
- Create: `.claude/skills/alpaca-trading/references/recipes.md`

- [ ] **Step 1: Write the file with all six recipes below**

````markdown
# Trading API — Recipes

All snippets assume:

```python
import os
from alpaca.trading.client import TradingClient

client = TradingClient(
    api_key=os.environ["APCA_API_KEY_ID"],
    secret_key=os.environ["APCA_API_SECRET_KEY"],
    paper=True,
)
```

## 1. Connect & verify

```python
account = client.get_account()
print(account.status, account.cash, account.equity, account.buying_power)
```

## 2. Market / limit / bracket order

```python
from alpaca.trading.requests import (
    MarketOrderRequest, LimitOrderRequest,
    TakeProfitRequest, StopLossRequest,
)
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass

# Market buy 1 share of AAPL
client.submit_order(MarketOrderRequest(
    symbol="AAPL", qty=1,
    side=OrderSide.BUY, time_in_force=TimeInForce.DAY,
))

# Limit sell at $200
client.submit_order(LimitOrderRequest(
    symbol="AAPL", qty=1, limit_price=200,
    side=OrderSide.SELL, time_in_force=TimeInForce.GTC,
))

# Bracket: buy with take-profit and stop-loss
client.submit_order(MarketOrderRequest(
    symbol="AAPL", qty=1,
    side=OrderSide.BUY, time_in_force=TimeInForce.GTC,
    order_class=OrderClass.BRACKET,
    take_profit=TakeProfitRequest(limit_price=210),
    stop_loss=StopLossRequest(stop_price=180, limit_price=179),
))
```

## 3. Stream order updates

```python
import asyncio
from alpaca.trading.stream import TradingStream

stream = TradingStream(
    os.environ["APCA_API_KEY_ID"],
    os.environ["APCA_API_SECRET_KEY"],
    paper=True,
)

async def on_update(data):
    print(data.event, data.order.symbol, data.order.status)

stream.subscribe_trade_updates(on_update)
stream.run()  # blocking; use stream.stop() to end
```

## 4. Get / close positions

```python
# All open positions
positions = client.get_all_positions()
for p in positions:
    print(p.symbol, p.qty, p.unrealized_pl)

# Single position
aapl = client.get_open_position("AAPL")

# Close everything
client.close_all_positions(cancel_orders=True)

# Close part of a position
from alpaca.trading.requests import ClosePositionRequest
client.close_position("AAPL", ClosePositionRequest(percentage="50"))
```

## 5. DCA scheduler skeleton

```python
import time
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

SYMBOL = "VOO"
NOTIONAL = 10  # dollars per cycle
INTERVAL_SECONDS = 7 * 24 * 3600  # weekly

while True:
    client.submit_order(MarketOrderRequest(
        symbol=SYMBOL, notional=NOTIONAL,
        side=OrderSide.BUY, time_in_force=TimeInForce.DAY,
    ))
    time.sleep(INTERVAL_SECONDS)
```

For production: replace the `while/sleep` with `cron` or `apscheduler`, and only fire when `client.get_clock().is_open`.

## 6. Natural-language → order parser pattern

When wiring an LLM tool call to Alpaca:

```python
from pydantic import BaseModel, Field
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

class PlaceOrderArgs(BaseModel):
    symbol: str = Field(..., description="Ticker, e.g. AAPL")
    side: str = Field(..., description="'buy' or 'sell'")
    qty: float | None = None
    notional: float | None = None
    limit_price: float | None = None

def place_order(args: PlaceOrderArgs):
    side = OrderSide.BUY if args.side.lower() == "buy" else OrderSide.SELL
    common = dict(symbol=args.symbol, side=side, time_in_force=TimeInForce.DAY)
    if args.qty is not None:
        common["qty"] = args.qty
    elif args.notional is not None:
        common["notional"] = args.notional
    else:
        raise ValueError("must supply qty or notional")
    if args.limit_price is None:
        return client.submit_order(MarketOrderRequest(**common))
    return client.submit_order(LimitOrderRequest(limit_price=args.limit_price, **common))
```

Expose `place_order` to the LLM via your agent framework's tool/function-calling API.
````

- [ ] **Step 2: Verify**

```bash
wc -l .claude/skills/alpaca-trading/references/recipes.md
```

Expected: 100–250 lines.

---

### Task 7: Write `alpaca-trading/scripts/check_setup.py`

**Files:**
- Create: `.claude/skills/alpaca-trading/scripts/check_setup.py`

- [ ] **Step 1: Write the script**

```python
"""Verify Alpaca Trading API credentials and connectivity.

Run: uv run python .claude/skills/alpaca-trading/scripts/check_setup.py
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    key = os.environ.get("APCA_API_KEY_ID")
    secret = os.environ.get("APCA_API_SECRET_KEY")
    if not key or not secret:
        print("ERROR: APCA_API_KEY_ID and APCA_API_SECRET_KEY must be set.")
        return 1

    try:
        from alpaca.trading.client import TradingClient
    except ImportError:
        print("ERROR: alpaca-py not installed. Run: uv add alpaca-py")
        return 1

    try:
        client = TradingClient(api_key=key, secret_key=secret, paper=True)
        account = client.get_account()
    except Exception as exc:
        print(f"ERROR: get_account() failed: {exc}")
        return 1

    print(f"OK  status={account.status}  cash={account.cash}  equity={account.equity}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run it (assumes `.env` has been loaded into shell)**

```bash
uv run --env-file .env python .claude/skills/alpaca-trading/scripts/check_setup.py
```

Expected: line starting with `OK status=ACTIVE cash=...`

If it errors with missing env vars, that means `.env` isn't being loaded — the script itself is fine.

---

### Task 8: Smoke-test alpaca-trading

**Files:** none (manual test)

- [ ] **Step 1: Open a fresh chat (`/clear` or new terminal session in the project)**

- [ ] **Step 2: Prompt with a recipe-covered task**

Send:
> Place a bracket buy on AAPL: 1 share, take-profit at $210, stop-loss at $180.

Expected: Claude activates `alpaca-trading`, reads `references/recipes.md`, and produces code matching recipe 2 with appropriate values.

- [ ] **Step 3: Prompt with an off-recipe task**

Send:
> How do I retrieve the corporate actions feed for a symbol via the Trading API?

Expected: Claude looks at `sdk-reference.md`, finds `get_corporate_announcements`, and either generates code or escalates to Context7/WebFetch for filter details.

- [ ] **Step 4: If either fails, fix the relevant file and retry**

Common issues:
- Skill didn't activate → strengthen `description` triggers in `SKILL.md`
- Wrong reference loaded → add explicit routing in SKILL.md "When invoked" section

---

# Phase 3: alpaca-market-data skill

### Task 9: Write `alpaca-market-data/SKILL.md`

**Files:**
- Create: `.claude/skills/alpaca-market-data/SKILL.md`

- [ ] **Step 1: Write the file**

```markdown
---
name: alpaca-market-data
description: Use when writing Python code that fetches prices, quotes, trades, bars, options chains, or news from Alpaca's Market Data API (alpaca-py). Triggers include "latest quote", "historical bars", "alpaca stream", "market data", "options chain", "news feed", "crypto price", "stock bars", "minute bars", "candles", "OHLC", "snapshot".
---

# Alpaca Market Data API

Generate Python code against Alpaca's Market Data API using the `alpaca-py` SDK.

## When invoked

1. Confirm `alpaca-py` is installed
2. Confirm env vars `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY` are set (same keys as Trading)
3. Pick the right client:
   - Stocks → `StockHistoricalDataClient` / `StockDataStream`
   - Crypto → `CryptoHistoricalDataClient` / `CryptoDataStream`
   - Options → `OptionHistoricalDataClient` / `OptionDataStream`
   - News → `NewsClient` (via `StockHistoricalDataClient` in newer versions) / `NewsDataStream`
4. If the task matches a known pattern, read `references/recipes.md`
5. If the task needs class/method details, read `references/sdk-reference.md`
6. For uncovered specifics, escalate via Context7 (`alpacahq/alpaca-py`) or WebFetch against `https://docs.alpaca.markets/reference/`

## Quick reference

- Historical: `StockHistoricalDataClient`, `CryptoHistoricalDataClient`, `OptionHistoricalDataClient`
- Streams: `StockDataStream`, `CryptoDataStream`, `OptionDataStream`, `NewsDataStream`
- Common request types: `*BarsRequest`, `*LatestQuoteRequest`, `*LatestTradeRequest`, `*SnapshotRequest`, `NewsRequest`
- Enum: `TimeFrame`, `TimeFrameUnit`, `Adjustment`, `DataFeed`, `Sort`

## Files

- `references/auth-setup.md`
- `references/sdk-reference.md`
- `references/recipes.md`
- `scripts/check_setup.py`
```

- [ ] **Step 2: Verify**

```bash
ls -la .claude/skills/alpaca-market-data/SKILL.md
```

---

### Task 10: Write `alpaca-market-data/references/auth-setup.md`

**Files:**
- Create: `.claude/skills/alpaca-market-data/references/auth-setup.md`

- [ ] **Step 1: Write the file**

```markdown
# Market Data API — Auth & Setup

## Install

```bash
uv add alpaca-py
```

## Environment variables

Same keys as Trading API (paper or live both work for market data; data quality may differ):

```
APCA_API_KEY_ID=your_key_id
APCA_API_SECRET_KEY=your_secret
```

## First call (verifies keys work)

```python
import os
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest

client = StockHistoricalDataClient(
    api_key=os.environ["APCA_API_KEY_ID"],
    secret_key=os.environ["APCA_API_SECRET_KEY"],
)
quote = client.get_stock_latest_quote(StockLatestQuoteRequest(symbol_or_symbols="AAPL"))
print(quote["AAPL"].ask_price, quote["AAPL"].bid_price)
```

## Data feeds

- Free SIP feed: limited symbols
- IEX feed: free, full coverage but lower depth
- SIP full: paid

Pass `feed=DataFeed.IEX` (default) or `feed=DataFeed.SIP` on requests where it matters.
```

- [ ] **Step 2: Verify file is in place**

```bash
ls -la .claude/skills/alpaca-market-data/references/auth-setup.md
```

---

### Task 11: Write `alpaca-market-data/references/sdk-reference.md`

**Files:**
- Create: `.claude/skills/alpaca-market-data/references/sdk-reference.md`

- [ ] **Step 1: Pull current `alpaca-py` data module surface**

Use Context7 (`alpacahq/alpaca-py`, topic "data historical stream") or WebFetch on `https://github.com/alpacahq/alpaca-py/tree/master/alpaca/data`. Read `historical/stock.py`, `historical/crypto.py`, `historical/option.py`, `live/stock.py`, `live/crypto.py`, `requests.py`, `models/`, `enums.py`.

- [ ] **Step 2: Write the file**

The file MUST cover:

1. **`StockHistoricalDataClient`**
   - Constructor: `(api_key, secret_key, raw_data, url_override)`
   - Methods: `get_stock_bars(StockBarsRequest)`, `get_stock_quotes(StockQuotesRequest)`, `get_stock_trades(StockTradesRequest)`, `get_stock_latest_quote(StockLatestQuoteRequest)`, `get_stock_latest_trade(StockLatestTradeRequest)`, `get_stock_latest_bar(StockLatestBarRequest)`, `get_stock_snapshot(StockSnapshotRequest)`

2. **`CryptoHistoricalDataClient`**
   - Methods: `get_crypto_bars`, `get_crypto_quotes`, `get_crypto_trades`, `get_crypto_latest_quote`, `get_crypto_latest_trade`, `get_crypto_latest_bar`, `get_crypto_snapshot`, `get_crypto_orderbook`

3. **`OptionHistoricalDataClient`**
   - Methods: `get_option_bars`, `get_option_trades`, `get_option_latest_quote`, `get_option_latest_trade`, `get_option_chain`, `get_option_snapshot`

4. **News (`NewsClient` or news methods)**
   - `get_news(NewsRequest)`

5. **Request types** with key fields:
   - `StockBarsRequest(symbol_or_symbols, timeframe, start?, end?, limit?, adjustment?, feed?, sort?)`
   - `StockQuotesRequest(...)`, `StockTradesRequest(...)`
   - `StockLatestQuoteRequest(symbol_or_symbols, feed?)`
   - `StockSnapshotRequest(symbol_or_symbols, feed?)`
   - Crypto/Option mirrors of the above
   - `NewsRequest(symbols?, start?, end?, sort?, include_content?, exclude_contentless?, limit?)`

6. **Streams**
   - `StockDataStream(api_key, secret_key, raw_data, feed, websocket_params)`
   - Subscriptions: `subscribe_quotes(handler, *symbols)`, `subscribe_trades(...)`, `subscribe_bars(...)`, `subscribe_updated_bars(...)`, `subscribe_daily_bars(...)`
   - Lifecycle: `run()`, `stop()`, `unsubscribe_*`
   - `CryptoDataStream`, `OptionDataStream`, `NewsDataStream` follow the same shape (`subscribe_news(handler, *symbols)`)

7. **Models** (just name + key fields):
   - `Bar`: symbol, timestamp, open, high, low, close, volume, trade_count, vwap
   - `Quote`: symbol, timestamp, ask_price, ask_size, ask_exchange, bid_price, bid_size, bid_exchange
   - `Trade`: symbol, timestamp, price, size, exchange
   - `Snapshot`: latest_quote, latest_trade, minute_bar, daily_bar, previous_daily_bar
   - `News`: id, headline, summary, content, url, symbols, created_at

8. **Enums**:
   - `TimeFrame`: factory + `Minute`, `Hour`, `Day`, `Week`, `Month` shortcuts (`TimeFrame.Minute`, `TimeFrame(5, TimeFrameUnit.Minute)`)
   - `TimeFrameUnit`: Minute, Hour, Day, Week, Month
   - `Adjustment`: RAW, SPLIT, DIVIDEND, ALL
   - `DataFeed`: IEX, SIP, OTC
   - `Sort`: ASC, DESC

Format with code-block imports + brief usage. Cap at ~500 lines.

- [ ] **Step 3: Verify**

```bash
wc -l .claude/skills/alpaca-market-data/references/sdk-reference.md
```

Expected: 250–600 lines.

---

### Task 12: Write `alpaca-market-data/references/recipes.md`

**Files:**
- Create: `.claude/skills/alpaca-market-data/references/recipes.md`

- [ ] **Step 1: Write the file**

````markdown
# Market Data API — Recipes

All snippets share auth setup:

```python
import os
KEY = os.environ["APCA_API_KEY_ID"]
SECRET = os.environ["APCA_API_SECRET_KEY"]
```

## 1. Latest quote / trade / bar

```python
from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, CryptoLatestQuoteRequest

stock = StockHistoricalDataClient(KEY, SECRET)
crypto = CryptoHistoricalDataClient(KEY, SECRET)

stock_q = stock.get_stock_latest_quote(StockLatestQuoteRequest(symbol_or_symbols=["AAPL", "MSFT"]))
print(stock_q["AAPL"].ask_price, stock_q["MSFT"].bid_price)

crypto_q = crypto.get_crypto_latest_quote(CryptoLatestQuoteRequest(symbol_or_symbols="BTC/USD"))
print(crypto_q["BTC/USD"].ask_price)
```

## 2. Historical bars

```python
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.enums import Adjustment

client = StockHistoricalDataClient(KEY, SECRET)

req = StockBarsRequest(
    symbol_or_symbols="AAPL",
    timeframe=TimeFrame(5, TimeFrameUnit.Minute),
    start=datetime.utcnow() - timedelta(days=5),
    end=datetime.utcnow(),
    adjustment=Adjustment.ALL,
)
bars = client.get_stock_bars(req).df  # DataFrame
print(bars.tail())
```

## 3. Real-time stream (stocks + crypto + news)

```python
import asyncio
from alpaca.data.live import StockDataStream, CryptoDataStream, NewsDataStream

stocks = StockDataStream(KEY, SECRET)
crypto = CryptoDataStream(KEY, SECRET)
news = NewsDataStream(KEY, SECRET)

async def on_bar(bar):
    print("BAR", bar.symbol, bar.close)

async def on_news(item):
    print("NEWS", item.headline, item.symbols)

stocks.subscribe_bars(on_bar, "AAPL", "MSFT")
crypto.subscribe_quotes(on_bar, "BTC/USD")
news.subscribe_news(on_news, "AAPL")

async def main():
    await asyncio.gather(stocks._run_forever(), crypto._run_forever(), news._run_forever())

asyncio.run(main())
```

For simpler single-stream use, just call `stocks.run()` (blocking).

## 4. Multi-symbol snapshot for a dashboard

```python
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockSnapshotRequest

client = StockHistoricalDataClient(KEY, SECRET)
snap = client.get_stock_snapshot(StockSnapshotRequest(
    symbol_or_symbols=["AAPL", "MSFT", "NVDA", "TSLA", "META"],
))
for sym, s in snap.items():
    print(sym, s.latest_trade.price, s.daily_bar.open, s.daily_bar.close)
```

## 5. News feed → sentiment hook

```python
from alpaca.data.historical import NewsClient
from alpaca.data.requests import NewsRequest
from datetime import datetime, timedelta

news = NewsClient(KEY, SECRET)
items = news.get_news(NewsRequest(
    symbols=["AAPL"],
    start=datetime.utcnow() - timedelta(days=1),
    include_content=True,
    limit=20,
)).news

# Hand off to your sentiment model
for item in items:
    score = your_sentiment_fn(item.summary or item.headline)
    print(item.headline, score)
```

(If `NewsClient` is unavailable in your version, use `StockHistoricalDataClient.get_news(...)` per the SDK reference.)

## 6. Options chain + greeks

```python
from alpaca.data.historical import OptionHistoricalDataClient
from alpaca.data.requests import OptionChainRequest

opt = OptionHistoricalDataClient(KEY, SECRET)
chain = opt.get_option_chain(OptionChainRequest(underlying_symbol="AAPL"))
for symbol, snapshot in chain.items():
    print(symbol, snapshot.latest_quote.ask_price, snapshot.greeks)
```
````

- [ ] **Step 2: Verify**

```bash
wc -l .claude/skills/alpaca-market-data/references/recipes.md
```

Expected: 100–250 lines.

---

### Task 13: Write `alpaca-market-data/scripts/check_setup.py`

**Files:**
- Create: `.claude/skills/alpaca-market-data/scripts/check_setup.py`

- [ ] **Step 1: Write the script**

```python
"""Verify Alpaca Market Data API credentials and connectivity."""

from __future__ import annotations

import os
import sys


def main() -> int:
    key = os.environ.get("APCA_API_KEY_ID")
    secret = os.environ.get("APCA_API_SECRET_KEY")
    if not key or not secret:
        print("ERROR: APCA_API_KEY_ID and APCA_API_SECRET_KEY must be set.")
        return 1

    try:
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockLatestQuoteRequest
    except ImportError:
        print("ERROR: alpaca-py not installed. Run: uv add alpaca-py")
        return 1

    try:
        client = StockHistoricalDataClient(api_key=key, secret_key=secret)
        result = client.get_stock_latest_quote(
            StockLatestQuoteRequest(symbol_or_symbols="AAPL")
        )
    except Exception as exc:
        print(f"ERROR: latest quote fetch failed: {exc}")
        return 1

    quote = result["AAPL"]
    print(f"OK  AAPL bid={quote.bid_price}  ask={quote.ask_price}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run it**

```bash
uv run --env-file .env python .claude/skills/alpaca-market-data/scripts/check_setup.py
```

Expected: line starting with `OK AAPL bid=...`

---

### Task 14: Smoke-test alpaca-market-data

**Files:** none

- [ ] **Step 1: Fresh chat, prompt:**

> Stream 1-minute bars for BTC/USD and ETH/USD and print each one as it arrives.

Expected: Claude activates `alpaca-market-data`, reads recipes, produces code using `CryptoDataStream.subscribe_bars`.

- [ ] **Step 2: Off-recipe prompt:**

> Get the order book for BTC/USD with 5 levels of depth.

Expected: Claude consults `sdk-reference.md` (sees `get_crypto_orderbook`) or escalates to Context7 if not detailed enough.

- [ ] **Step 3: Fix any miss by tightening triggers or adding to references**

---

# Phase 4: alpaca-broker skill

### Task 15: Write `alpaca-broker/SKILL.md`

**Files:**
- Create: `.claude/skills/alpaca-broker/SKILL.md`

- [ ] **Step 1: Write the file**

```markdown
---
name: alpaca-broker
description: Use when writing Python code that creates end-user brokerage accounts, submits KYC, manages ACH funding, transfers cash, journals between accounts, or trades on behalf of customer accounts via Alpaca's Broker API (alpaca-py). Triggers include "Broker API", "create alpaca account", "ACH", "KYC", "fund account", "journal", "neo-broker", "embedded investing", "trade on behalf of user", "round-up", "savings app".
---

# Alpaca Broker API

Generate Python code against Alpaca's Broker API using the `alpaca-py` SDK.

## When invoked

1. Confirm `alpaca-py` is installed
2. Broker API uses **separate credentials** from Trading/Market Data — typically `BROKER_API_KEY_ID` and `BROKER_API_SECRET_KEY` (Basic Auth). Verify both exist.
3. Default to **sandbox** environment (`sandbox=True`)
4. If the task matches a known pattern, read `references/recipes.md`
5. If the task needs class/method details, read `references/sdk-reference.md`
6. Live fallback: Context7 (`alpacahq/alpaca-py`) or WebFetch `https://docs.alpaca.markets/reference/` (broker reference URLs are different from trading)

## Quick reference

- Client: `from alpaca.broker.client import BrokerClient`
- Account creation: `CreateAccountRequest`, `Contact`, `Identity`, `Disclosures`, `Agreement`
- Funding: `CreateACHRelationshipRequest`, `CreateACHTransferRequest`, `CreateBankRequest`, `CreateBankTransferRequest`
- Journals: `CreateJournalRequest`
- Trading on behalf of: `BrokerClient.submit_order_for_account(account_id, order_data)`

## Files

- `references/auth-setup.md`
- `references/sdk-reference.md`
- `references/recipes.md`
- `scripts/check_setup.py`
```

- [ ] **Step 2: Verify**

```bash
ls -la .claude/skills/alpaca-broker/SKILL.md
```

---

### Task 16: Write `alpaca-broker/references/auth-setup.md`

**Files:**
- Create: `.claude/skills/alpaca-broker/references/auth-setup.md`

- [ ] **Step 1: Write the file**

```markdown
# Broker API — Auth & Setup

## Install

```bash
uv add alpaca-py
```

## Environment variables

Broker API uses separate credentials from Trading. Generate at https://broker-app.alpaca.markets:

```
BROKER_API_KEY_ID=your_broker_key_id
BROKER_API_SECRET_KEY=your_broker_secret
```

## First call

```python
import os
from alpaca.broker.client import BrokerClient

client = BrokerClient(
    api_key=os.environ["BROKER_API_KEY_ID"],
    secret_key=os.environ["BROKER_API_SECRET_KEY"],
    sandbox=True,  # NEVER set False unless the user explicitly says live
)
accounts = client.list_accounts()
print(f"got {len(accounts)} sandbox accounts")
```

## Sandbox vs production

- Sandbox: `sandbox=True`, base URL `https://broker-api.sandbox.alpaca.markets/v1`
- Production: `sandbox=False`, base URL `https://broker-api.alpaca.markets/v1`
- **Default to sandbox.** Production requires onboarding paperwork.
```

- [ ] **Step 2: Verify**

```bash
ls -la .claude/skills/alpaca-broker/references/auth-setup.md
```

---

### Task 17: Write `alpaca-broker/references/sdk-reference.md`

**Files:**
- Create: `.claude/skills/alpaca-broker/references/sdk-reference.md`

- [ ] **Step 1: Pull current `alpaca-py` broker module surface**

Use Context7 (`alpacahq/alpaca-py`, topic "broker accounts funding journals") or WebFetch `https://github.com/alpacahq/alpaca-py/tree/master/alpaca/broker`. Read `client.py`, `requests.py`, `models/`, `enums.py`.

- [ ] **Step 2: Write the file**

The file MUST cover:

1. **`BrokerClient`**
   - Constructor: `(api_key, secret_key, sandbox, raw_data, url_override)`
   - Account methods: `create_account(CreateAccountRequest)`, `get_account_by_id(account_id)`, `list_accounts(filter)`, `update_account(account_id, UpdateAccountRequest)`, `delete_account(account_id)`, `get_trade_account_by_id(account_id)`
   - ACH methods: `create_ach_relationship_for_account(account_id, CreateACHRelationshipRequest)`, `get_ach_relationships_for_account(account_id)`, `delete_ach_relationship_for_account(account_id, ach_id)`
   - Transfer methods: `create_transfer_for_account(account_id, CreateACHTransferRequest)`, `get_transfers_for_account(account_id, filter)`, `cancel_transfer_for_account(account_id, transfer_id)`
   - Journal methods: `create_journal(CreateJournalRequest)`, `get_journals(filter)`, `cancel_journal_by_id(journal_id)`
   - Trading methods (on behalf of an account): `submit_order_for_account(account_id, OrderRequest)`, `get_orders_for_account(account_id, filter)`, `get_all_positions_for_account(account_id)`, etc.
   - Documents: `get_account_documents(account_id, filter)`, `download_account_document(...)`
   - Activities: `get_account_activities(filter)`

2. **Account creation request models**
   - `CreateAccountRequest(contact, identity, disclosures, agreements, documents?, trusted_contact?, account_type?)`
   - `Contact(email_address, phone_number, street_address, city, state, postal_code, country)`
   - `Identity(given_name, family_name, date_of_birth, tax_id, tax_id_type, country_of_citizenship, country_of_birth, country_of_tax_residence, funding_source)`
   - `Disclosures(is_control_person, is_affiliated_exchange_or_finra, is_politically_exposed, immediate_family_exposed)`
   - `Agreement(agreement, signed_at, ip_address)`
   - `TrustedContact(...)`

3. **Funding request models**
   - `CreateACHRelationshipRequest(account_owner_name, bank_account_type, bank_account_number, bank_routing_number, nickname?)`
   - `CreatePlaidRelationshipApiRequest(processor_token)` (Plaid integration)
   - `CreateACHTransferRequest(transfer_type, relationship_id, amount, direction)`
   - `CreateBankRequest(...)`, `CreateBankTransferRequest(...)`

4. **Journal request model**
   - `CreateJournalRequest(from_account, to_account, entry_type, amount?, symbol?, qty?, description?)`
   - `JournalEntryType`: JNLC (cash), JNLS (security)

5. **Enums**
   - `AccountStatus`: SUBMITTED, APPROVED, ACTIVE, REJECTED, etc.
   - `TaxIdType`: USA_SSN, USA_ITIN, etc.
   - `FundingSource`: EMPLOYMENT_INCOME, INVESTMENTS, INHERITANCE, BUSINESS_INCOME, SAVINGS, FAMILY
   - `AgreementType`: MARGIN_AGREEMENT, ACCOUNT_AGREEMENT, CUSTOMER_AGREEMENT, CRYPTO_AGREEMENT
   - `BankAccountType`: CHECKING, SAVINGS
   - `TransferType`: ACH, WIRE
   - `TransferDirection`: INCOMING, OUTGOING
   - `JournalEntryType`: JNLC, JNLS
   - `JournalStatus`: PENDING, EXECUTED, REJECTED, CANCELED

Format with code-block imports + usage. Cap at ~500 lines.

- [ ] **Step 3: Verify**

```bash
wc -l .claude/skills/alpaca-broker/references/sdk-reference.md
```

Expected: 250–600 lines.

---

### Task 18: Write `alpaca-broker/references/recipes.md`

**Files:**
- Create: `.claude/skills/alpaca-broker/references/recipes.md`

- [ ] **Step 1: Write the file**

````markdown
# Broker API — Recipes

```python
import os
from alpaca.broker.client import BrokerClient

client = BrokerClient(
    api_key=os.environ["BROKER_API_KEY_ID"],
    secret_key=os.environ["BROKER_API_SECRET_KEY"],
    sandbox=True,
)
```

## 1. Create an account (KYC)

```python
from alpaca.broker.requests import CreateAccountRequest
from alpaca.broker.models import (
    Contact, Identity, Disclosures, Agreement,
)
from alpaca.broker.enums import (
    TaxIdType, FundingSource, AgreementType,
)

req = CreateAccountRequest(
    contact=Contact(
        email_address="alice@example.com",
        phone_number="+15551234567",
        street_address=["123 Main St"],
        city="San Francisco", state="CA",
        postal_code="94105", country="USA",
    ),
    identity=Identity(
        given_name="Alice", family_name="Doe",
        date_of_birth="1990-01-01",
        tax_id="123-45-6789", tax_id_type=TaxIdType.USA_SSN,
        country_of_citizenship="USA",
        country_of_birth="USA",
        country_of_tax_residence="USA",
        funding_source=[FundingSource.EMPLOYMENT_INCOME],
    ),
    disclosures=Disclosures(
        is_control_person=False,
        is_affiliated_exchange_or_finra=False,
        is_politically_exposed=False,
        immediate_family_exposed=False,
    ),
    agreements=[
        Agreement(agreement=AgreementType.CUSTOMER,
                  signed_at="2025-04-25T12:00:00Z",
                  ip_address="192.0.2.1"),
        Agreement(agreement=AgreementType.MARGIN,
                  signed_at="2025-04-25T12:00:00Z",
                  ip_address="192.0.2.1"),
    ],
)
account = client.create_account(req)
print(account.id, account.status)
```

## 2. Fund an account: ACH relationship + transfer

```python
from alpaca.broker.requests import (
    CreateACHRelationshipRequest, CreateACHTransferRequest,
)
from alpaca.broker.enums import (
    BankAccountType, TransferType, TransferDirection,
)

ach = client.create_ach_relationship_for_account(
    account_id=account.id,
    ach_data=CreateACHRelationshipRequest(
        account_owner_name="Alice Doe",
        bank_account_type=BankAccountType.CHECKING,
        bank_account_number="32131231abc",
        bank_routing_number="121000358",
    ),
)

transfer = client.create_transfer_for_account(
    account_id=account.id,
    transfer_data=CreateACHTransferRequest(
        transfer_type=TransferType.ACH,
        relationship_id=ach.id,
        amount="100",
        direction=TransferDirection.INCOMING,
    ),
)
print(transfer.id, transfer.status)
```

## 3. List, get, update accounts

```python
from alpaca.broker.requests import ListAccountsRequest, UpdateAccountRequest

accts = client.list_accounts(ListAccountsRequest(query=None))
print(len(accts))

acct = client.get_account_by_id(account.id)

client.update_account(account.id, UpdateAccountRequest(
    contact=Contact(email_address="alice2@example.com",
                    phone_number="+15551234567",
                    street_address=["123 Main St"],
                    city="SF", state="CA",
                    postal_code="94105", country="USA"),
))
```

## 4. Place an order on behalf of an end-user

```python
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

order = client.submit_order_for_account(
    account_id=account.id,
    order_data=MarketOrderRequest(
        symbol="AAPL", qty=1,
        side=OrderSide.BUY, time_in_force=TimeInForce.DAY,
    ),
)
print(order.id, order.status)
```

## 5. Journal cash between accounts (round-ups, allowances)

```python
from alpaca.broker.requests import CreateJournalRequest
from alpaca.broker.enums import JournalEntryType

journal = client.create_journal(CreateJournalRequest(
    from_account=parent_account_id,
    to_account=child_account_id,
    entry_type=JournalEntryType.CASH,
    amount="5.00",
    description="Weekly allowance",
))
print(journal.id, journal.status)
```

## 6. Webhooks for account events

The Broker API can POST events to your URL. Wire it up in the dashboard, then handle:

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/alpaca/webhook")
async def webhook(req: Request):
    event = await req.json()
    # event["event_type"] examples: "account.updated", "transfer.completed", "trade"
    # Validate the signature header per Alpaca docs before trusting payload
    print(event["event_type"], event.get("account_id"))
    return {"ok": True}
```

(Signature validation requires the webhook secret from the Broker dashboard — see Alpaca docs `https://docs.alpaca.markets/docs/webhook-events`.)
````

- [ ] **Step 2: Verify**

```bash
wc -l .claude/skills/alpaca-broker/references/recipes.md
```

Expected: 100–250 lines.

---

### Task 19: Write `alpaca-broker/scripts/check_setup.py`

**Files:**
- Create: `.claude/skills/alpaca-broker/scripts/check_setup.py`

- [ ] **Step 1: Write the script**

```python
"""Verify Alpaca Broker API credentials and connectivity."""

from __future__ import annotations

import os
import sys


def main() -> int:
    key = os.environ.get("BROKER_API_KEY_ID")
    secret = os.environ.get("BROKER_API_SECRET_KEY")
    if not key or not secret:
        print("ERROR: BROKER_API_KEY_ID and BROKER_API_SECRET_KEY must be set.")
        return 1

    try:
        from alpaca.broker.client import BrokerClient
        from alpaca.broker.requests import ListAccountsRequest
    except ImportError:
        print("ERROR: alpaca-py not installed. Run: uv add alpaca-py")
        return 1

    try:
        client = BrokerClient(api_key=key, secret_key=secret, sandbox=True)
        accts = client.list_accounts(ListAccountsRequest())
    except Exception as exc:
        print(f"ERROR: list_accounts failed: {exc}")
        return 1

    print(f"OK  sandbox accounts visible: {len(accts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run it**

```bash
uv run --env-file .env python .claude/skills/alpaca-broker/scripts/check_setup.py
```

Expected: line starting with `OK sandbox accounts visible:`

---

### Task 20: Smoke-test alpaca-broker

**Files:** none

- [ ] **Step 1: Fresh chat, prompt:**

> Create a sandbox Alpaca brokerage account for a hypothetical user named Bob Smith and fund it with $200 via ACH.

Expected: Claude activates `alpaca-broker`, reads recipes 1 and 2, generates code that creates the account then sets up ACH transfer.

- [ ] **Step 2: Off-recipe prompt:**

> List all transfers on a given account, filtered by direction.

Expected: Claude consults `sdk-reference.md` for `get_transfers_for_account` and shows the filter request type.

- [ ] **Step 3: Fix any gaps**

---

# Phase 5: alpaca-connect skill

### Task 21: Write `alpaca-connect/SKILL.md`

**Files:**
- Create: `.claude/skills/alpaca-connect/SKILL.md`

- [ ] **Step 1: Write the file**

```markdown
---
name: alpaca-connect
description: Use when building a third-party integration that lets users log in with their existing Alpaca account via OAuth2. Triggers include "Alpaca OAuth", "Connect API", "third-party Alpaca app", "log in with Alpaca", "Alpaca authorization flow", "Alpaca access token".
---

# Alpaca Connect API

Implement OAuth2 against Alpaca's Connect API in Python.

## When invoked

1. Confirm `alpaca-py` is installed (also requires `httpx` or `requests` — install if missing)
2. Confirm `ALPACA_OAUTH_CLIENT_ID` and `ALPACA_OAUTH_CLIENT_SECRET` are set, plus a registered `redirect_uri`
3. If the task matches a known pattern, read `references/recipes.md`
4. If the task needs protocol details, read `references/sdk-reference.md`
5. Live fallback: WebFetch `https://docs.alpaca.markets/docs/oauth-apps`

## Quick reference

- Authorize URL: `https://app.alpaca.markets/oauth/authorize`
- Token URL: `https://api.alpaca.markets/oauth/token`
- Scopes: `account:write`, `trading`, `data`
- Token exchange uses standard OAuth2 authorization-code grant
- Access tokens can be passed to `TradingClient(oauth_token=...)` instead of `api_key`/`secret_key`

## Files

- `references/auth-setup.md`
- `references/sdk-reference.md`
- `references/recipes.md`
- `scripts/check_setup.py`
```

- [ ] **Step 2: Verify**

```bash
ls -la .claude/skills/alpaca-connect/SKILL.md
```

---

### Task 22: Write `alpaca-connect/references/auth-setup.md`

**Files:**
- Create: `.claude/skills/alpaca-connect/references/auth-setup.md`

- [ ] **Step 1: Write the file**

```markdown
# Connect API — Auth & Setup

## OAuth app registration

Register an OAuth app at `https://app.alpaca.markets/oauth/apps`. You'll get:

- `client_id`
- `client_secret`
- A registered `redirect_uri` (e.g. `http://localhost:3000/callback` for dev)

## Environment variables

```
ALPACA_OAUTH_CLIENT_ID=your_client_id
ALPACA_OAUTH_CLIENT_SECRET=your_client_secret
ALPACA_OAUTH_REDIRECT_URI=http://localhost:3000/callback
```

## Endpoints

- Authorize: `https://app.alpaca.markets/oauth/authorize`
- Token exchange: `https://api.alpaca.markets/oauth/token`
- Revoke: `https://api.alpaca.markets/oauth/revoke`

## Scopes

- `account:write` — read + modify account
- `trading` — place/cancel orders, manage positions
- `data` — market data access (rarely needed; use direct keys for data)

## Default flow

Authorization-code grant. The app shows the user a consent page on Alpaca, then Alpaca redirects back to `redirect_uri` with a `code` query param, which the app trades for an access token + refresh token.
```

- [ ] **Step 2: Verify**

```bash
ls -la .claude/skills/alpaca-connect/references/auth-setup.md
```

---

### Task 23: Write `alpaca-connect/references/sdk-reference.md`

**Files:**
- Create: `.claude/skills/alpaca-connect/references/sdk-reference.md`

- [ ] **Step 1: Pull current OAuth details**

WebFetch `https://docs.alpaca.markets/docs/oauth-apps` and the linked authorize/token endpoint docs.

- [ ] **Step 2: Write the file**

The file MUST cover:

1. **Authorization URL parameters**
   - `response_type=code` (required)
   - `client_id` (required)
   - `redirect_uri` (required, must exactly match registration)
   - `scope` (space-separated, required)
   - `state` (recommended, opaque CSRF token)

2. **Token exchange POST** to `https://api.alpaca.markets/oauth/token`
   - Body (form-encoded): `grant_type=authorization_code`, `code`, `client_id`, `client_secret`, `redirect_uri`
   - Response JSON fields: `access_token`, `token_type=Bearer`, `scope`
   - Refresh tokens: Alpaca's standard OAuth flow does NOT typically issue refresh tokens; access tokens are long-lived but can be revoked. (Verify against current docs at execution time.)

3. **Revocation POST** to `https://api.alpaca.markets/oauth/revoke`
   - Body: `token=<access_token>`, `client_id`, `client_secret`

4. **Using an access token with `alpaca-py`**

```python
from alpaca.trading.client import TradingClient
client = TradingClient(oauth_token=access_token, paper=False)
account = client.get_account()
```

(`oauth_token` mode bypasses `api_key`/`secret_key`.)

5. **Errors**
   - `invalid_grant` — code expired or already used
   - `invalid_client` — client_id/secret wrong
   - `unauthorized_client` — scopes not granted

Cap at ~200 lines.

- [ ] **Step 3: Verify**

```bash
wc -l .claude/skills/alpaca-connect/references/sdk-reference.md
```

Expected: 80–250 lines.

---

### Task 24: Write `alpaca-connect/references/recipes.md`

**Files:**
- Create: `.claude/skills/alpaca-connect/references/recipes.md`

- [ ] **Step 1: Write the file**

````markdown
# Connect API — Recipes

## 1. Build the authorize URL

```python
import os, secrets
from urllib.parse import urlencode

CLIENT_ID = os.environ["ALPACA_OAUTH_CLIENT_ID"]
REDIRECT_URI = os.environ["ALPACA_OAUTH_REDIRECT_URI"]

def build_authorize_url(scopes: list[str]) -> tuple[str, str]:
    state = secrets.token_urlsafe(24)
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(scopes),
        "state": state,
    }
    url = "https://app.alpaca.markets/oauth/authorize?" + urlencode(params)
    return url, state
```

Store `state` in a session cookie / cache and verify it on callback.

## 2. Exchange code for access token

```python
import os, httpx

CLIENT_ID = os.environ["ALPACA_OAUTH_CLIENT_ID"]
CLIENT_SECRET = os.environ["ALPACA_OAUTH_CLIENT_SECRET"]
REDIRECT_URI = os.environ["ALPACA_OAUTH_REDIRECT_URI"]

def exchange_code(code: str) -> dict:
    r = httpx.post(
        "https://api.alpaca.markets/oauth/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()  # {"access_token": "...", "token_type": "Bearer", "scope": "..."}
```

## 3. Use the access token with alpaca-py

```python
from alpaca.trading.client import TradingClient

def client_for_user(access_token: str) -> TradingClient:
    return TradingClient(oauth_token=access_token, paper=False)

# example
client = client_for_user(token)
print(client.get_account().id)
```

## 4. FastAPI endpoint glue

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse

app = FastAPI()
SESSIONS: dict[str, str] = {}  # state -> session_id, replace with real store

@app.get("/login")
def login():
    url, state = build_authorize_url(["account:write", "trading"])
    SESSIONS[state] = "user-session-id"
    return RedirectResponse(url)

@app.get("/callback")
def callback(code: str, state: str):
    if state not in SESSIONS:
        raise HTTPException(400, "bad state")
    SESSIONS.pop(state)
    token_data = exchange_code(code)
    # store token_data["access_token"] for the user
    return {"ok": True}
```
````

- [ ] **Step 2: Verify**

```bash
wc -l .claude/skills/alpaca-connect/references/recipes.md
```

Expected: 80–200 lines.

---

### Task 25: Write `alpaca-connect/scripts/check_setup.py`

**Files:**
- Create: `.claude/skills/alpaca-connect/scripts/check_setup.py`

- [ ] **Step 1: Write the script**

```python
"""Verify Alpaca Connect (OAuth) app credentials are present.

This does NOT make a live API call (that would require a real user token).
It only validates that the client credentials are configured and the authorize
URL builds correctly.
"""

from __future__ import annotations

import os
import sys
from urllib.parse import urlencode


def main() -> int:
    client_id = os.environ.get("ALPACA_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("ALPACA_OAUTH_CLIENT_SECRET")
    redirect_uri = os.environ.get("ALPACA_OAUTH_REDIRECT_URI")
    missing = [n for n, v in [
        ("ALPACA_OAUTH_CLIENT_ID", client_id),
        ("ALPACA_OAUTH_CLIENT_SECRET", client_secret),
        ("ALPACA_OAUTH_REDIRECT_URI", redirect_uri),
    ] if not v]
    if missing:
        print(f"ERROR: missing env vars: {', '.join(missing)}")
        return 1

    url = "https://app.alpaca.markets/oauth/authorize?" + urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "account:write trading",
        "state": "dummy",
    })
    print(f"OK  authorize url builds: {url[:80]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run it**

```bash
uv run --env-file .env python .claude/skills/alpaca-connect/scripts/check_setup.py
```

Expected: line starting with `OK authorize url builds:`. If env vars aren't set, that's fine — Connect is optional and you can configure later.

---

### Task 26: Smoke-test alpaca-connect

**Files:** none

- [ ] **Step 1: Fresh chat, prompt:**

> Build a FastAPI app that lets a user log in with their Alpaca account and prints their account ID.

Expected: Claude activates `alpaca-connect`, combines recipes 1, 2, 4, produces a runnable FastAPI app.

- [ ] **Step 2: Off-recipe prompt:**

> How do I revoke an issued access token?

Expected: Claude reads `sdk-reference.md`, finds the revoke endpoint, generates the POST.

---

# Phase 6: Multi-skill validation

### Task 27: Cross-skill smoke test

**Files:** none

- [ ] **Step 1: Fresh chat, prompt that spans broker + trading + market-data:**

> Build a robo-advisor backend: create a new sandbox Alpaca account, fund it with $500 via ACH, then for the next 5 trading days fetch the previous-day bars for SPY, QQQ, VTI and place a $100 market buy on whichever has the lowest 5-day return.

Expected: Claude pulls in `alpaca-broker` (recipes 1, 2), `alpaca-market-data` (recipe 2), `alpaca-trading` (recipe 2 for the buy). Code is roughly correct end-to-end — minor fixes acceptable.

- [ ] **Step 2: If a skill failed to activate, tighten its `description` triggers**

- [ ] **Step 3: Document any limitations** in a top-level `.claude/skills/README.md` (one-line summary per skill + link to spec)

---

## Self-Review

After all tasks complete:

1. **Spec coverage:** Every API in the spec (Trading, Market Data, Broker, Connect) has its own skill ✓. Every recipe listed in spec section "Content Sourcing → recipes.md" is implemented ✓.
2. **Placeholder scan:** None — all code blocks are concrete.
3. **Type consistency:** Class names match `alpaca-py` current API. If versions drift, sdk-reference tasks tell the implementer to re-pull from source.
4. **Open question:** None blocking.
