# Market Data API — Auth & Setup

## Install

```bash
uv add alpaca-py
```

## Environment variables

Same keys as Trading API (paper or live both work for market data; data quality may differ):

```
APCA_API_KEY_ID=your_key_id
APCA_API_SECRET_KEY=your_secret
```

## First call (verifies keys work)

```python
import os
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest

client = StockHistoricalDataClient(
    api_key=os.environ["APCA_API_KEY_ID"],
    secret_key=os.environ["APCA_API_SECRET_KEY"],
)
quote = client.get_stock_latest_quote(StockLatestQuoteRequest(symbol_or_symbols="AAPL"))
print(quote["AAPL"].ask_price, quote["AAPL"].bid_price)
```

## Data feeds

- Free SIP feed: limited symbols
- IEX feed: free, full coverage but lower depth
- SIP full: paid

Pass `feed=DataFeed.IEX` (default) or `feed=DataFeed.SIP` on requests where it matters.
