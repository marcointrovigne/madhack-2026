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
