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
