"""Standalone diagnostic: submit a single $1 SGOV market order via Alpaca Broker API.

Loads .env, reads the Acme account_id from config/acme_account.json,
hits broker-api.sandbox.alpaca.markets directly with HTTP Basic Auth (no SDK).
Prints the raw request and response so we can show it to Alpaca support.

Usage:
    uv run python scripts/test_broker_order.py
"""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

BROKER_BASE_URL = "https://broker-api.sandbox.alpaca.markets"


def _account_id() -> str:
    record_path = Path(__file__).parent.parent / "config" / "acme_account.json"
    if not record_path.exists():
        raise RuntimeError(
            "config/acme_account.json not found — run scripts/setup_account.py first."
        )
    return json.loads(record_path.read_text())["account_id"]


def _basic_auth_header() -> str:
    key = os.environ["BROKER_API_KEY_ID"]
    secret = os.environ["BROKER_API_SECRET_KEY"]
    token = base64.b64encode(f"{key}:{secret}".encode()).decode()
    return f"Basic {token}"


def post(url: str, body: dict) -> tuple[int, str]:
    payload = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": _basic_auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main() -> None:
    account_id = _account_id()
    url = f"{BROKER_BASE_URL}/v1/trading/accounts/{account_id}/orders"
    body = {
        "symbol": "SGOV",
        "qty": "1",
        "side": "buy",
        "type": "market",
        "time_in_force": "day",
    }

    print("=" * 70)
    print(f"POST {url}")
    print(f"Authorization: Basic {os.environ['BROKER_API_KEY_ID'][:6]}...***")
    print(f"Content-Type: application/json")
    print()
    print("Request body:")
    print(json.dumps(body, indent=2))
    print()

    status, response = post(url, body)
    print(f"HTTP {status}")
    print(f"Response body:")
    try:
        print(json.dumps(json.loads(response), indent=2))
    except json.JSONDecodeError:
        print(response)
    print("=" * 70)


if __name__ == "__main__":
    main()
