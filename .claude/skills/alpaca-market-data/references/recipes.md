# Market Data API — Recipes

All snippets share auth setup:

```python
import os
KEY = os.environ["APCA_API_KEY_ID"]
SECRET = os.environ["APCA_API_SECRET_KEY"]
```

## 1. Latest quote / trade / bar

```python
from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, CryptoLatestQuoteRequest

stock = StockHistoricalDataClient(KEY, SECRET)
crypto = CryptoHistoricalDataClient(KEY, SECRET)

stock_q = stock.get_stock_latest_quote(StockLatestQuoteRequest(symbol_or_symbols=["AAPL", "MSFT"]))
print(stock_q["AAPL"].ask_price, stock_q["MSFT"].bid_price)

crypto_q = crypto.get_crypto_latest_quote(CryptoLatestQuoteRequest(symbol_or_symbols="BTC/USD"))
print(crypto_q["BTC/USD"].ask_price)
```

## 2. Historical bars

```python
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.enums import Adjustment

client = StockHistoricalDataClient(KEY, SECRET)

req = StockBarsRequest(
    symbol_or_symbols="AAPL",
    timeframe=TimeFrame(5, TimeFrameUnit.Minute),
    start=datetime.utcnow() - timedelta(days=5),
    end=datetime.utcnow(),
    adjustment=Adjustment.ALL,
)
bars = client.get_stock_bars(req).df  # DataFrame
print(bars.tail())
```

## 3. Real-time stream (stocks + crypto + news)

```python
import asyncio
from alpaca.data.live import StockDataStream, CryptoDataStream, NewsDataStream

stocks = StockDataStream(KEY, SECRET)
crypto = CryptoDataStream(KEY, SECRET)
news = NewsDataStream(KEY, SECRET)

async def on_bar(bar):
    print("BAR", bar.symbol, bar.close)

async def on_news(item):
    print("NEWS", item.headline, item.symbols)

stocks.subscribe_bars(on_bar, "AAPL", "MSFT")
crypto.subscribe_quotes(on_bar, "BTC/USD")
news.subscribe_news(on_news, "AAPL")

async def main():
    await asyncio.gather(stocks._run_forever(), crypto._run_forever(), news._run_forever())

asyncio.run(main())
```

For simpler single-stream use, just call `stocks.run()` (blocking).

## 4. Multi-symbol snapshot for a dashboard

```python
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockSnapshotRequest

client = StockHistoricalDataClient(KEY, SECRET)
snap = client.get_stock_snapshot(StockSnapshotRequest(
    symbol_or_symbols=["AAPL", "MSFT", "NVDA", "TSLA", "META"],
))
for sym, s in snap.items():
    print(sym, s.latest_trade.price, s.daily_bar.open, s.daily_bar.close)
```

## 5. News feed → sentiment hook

```python
from alpaca.data.historical import NewsClient
from alpaca.data.requests import NewsRequest
from datetime import datetime, timedelta

news = NewsClient(KEY, SECRET)
items = news.get_news(NewsRequest(
    symbols=["AAPL"],
    start=datetime.utcnow() - timedelta(days=1),
    include_content=True,
    limit=20,
)).news

# Hand off to your sentiment model
for item in items:
    score = your_sentiment_fn(item.summary or item.headline)
    print(item.headline, score)
```

(If `NewsClient` is unavailable in your version, use `StockHistoricalDataClient.get_news(...)` per the SDK reference.)

## 6. Options chain + greeks

```python
from alpaca.data.historical import OptionHistoricalDataClient
from alpaca.data.requests import OptionChainRequest

opt = OptionHistoricalDataClient(KEY, SECRET)
chain = opt.get_option_chain(OptionChainRequest(underlying_symbol="AAPL"))
for symbol, snapshot in chain.items():
    print(symbol, snapshot.latest_quote.ask_price, snapshot.greeks)
```
