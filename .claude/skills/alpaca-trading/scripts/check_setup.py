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
