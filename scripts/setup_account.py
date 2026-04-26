"""One-shot setup: open Acme's brokerage account via Alpaca Broker API and fund it.

Run once before the demo:
    uv run python scripts/setup_account.py

Idempotent — if config/acme_account.json already exists, this script
prints the cached account_id and exits without re-creating.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make project root importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from agents.broker import (  # noqa: E402
    create_acme_account,
    fund_account,
    get_broker_client,
    load_account_record,
)


def main() -> None:
    existing = load_account_record()
    if existing:
        account_id = existing["account_id"]
        print(f"✓ Account already configured: {account_id}")
        print(f"  Created: {existing.get('created_at')}")
    else:
        print("Creating new brokerage account for Acme via Alpaca Broker API...")
        record = create_acme_account()
        account_id = record["account_id"]
        print(f"✓ Account created: {account_id}")
        print(f"  Status: {record['status']}")

    # Check current funding state
    bc = get_broker_client()
    try:
        trade_acct = bc.get_trade_account_by_id(account_id=account_id)
        cash = float(trade_acct.cash or 0)
        print(f"\nCurrent state:")
        print(f"  Status:       {trade_acct.status}")
        print(f"  Cash:         ${cash:,.2f}")
        print(f"  Buying power: ${float(trade_acct.buying_power or 0):,.2f}")
        print(f"  Equity:       ${float(trade_acct.equity or 0):,.2f}")
    except Exception as e:
        cash = 0
        print(f"\n(Could not fetch live trade account info: {e})")
        print("Account may still be in SUBMITTED state — sandbox typically activates within seconds.")

    # Sandbox caps at $50,000 per daily transfer — fund up to the cap
    target_funding = 50_000
    if cash < target_funding * 0.5:
        print(f"\nRequesting INCOMING ACH transfer of ${target_funding:,.2f} (sandbox daily cap)...")
        try:
            transfer = fund_account(account_id, target_funding)
            print(f"✓ Transfer initiated: {transfer['transfer_id']}")
            print(f"  Status: {transfer['status']}  (sandbox auto-completes)")
        except Exception as e:
            print(f"⚠ Funding request failed: {e}")
    else:
        print(f"\n✓ Account is sufficiently funded — skipping transfer request.")

    print(f"\nAccount ID persisted to config/acme_account.json")
    print("→ Run: uv run python scripts/smoke.py 'Show me my brokerage account.'")


if __name__ == "__main__":
    main()
