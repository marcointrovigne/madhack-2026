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
