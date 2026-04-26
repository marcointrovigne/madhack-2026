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
