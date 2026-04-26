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
