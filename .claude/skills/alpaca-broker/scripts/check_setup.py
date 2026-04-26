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
