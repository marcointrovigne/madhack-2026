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
