# Market Data API — SDK Reference

Source: `alpaca-py` SDK (`alpacahq/alpaca-py`). Re-pull live details via Context7 or WebFetch if method signatures differ from what's here.

---

## 1. StockHistoricalDataClient

Historical OHLCV bars, quotes, trades, and snapshots for US equities.

```python
from alpaca.data.historical import StockHistoricalDataClient
# or explicitly:
from alpaca.data.historical.stock import StockHistoricalDataClient

client = StockHistoricalDataClient(
    api_key="YOUR_APCA_API_KEY_ID",
    secret_key="YOUR_APCA_API_SECRET_KEY",
    # raw_data=False,      # return raw dicts instead of model objects
    # url_override=None,   # override base URL
)
```

### Methods

| Method | Request type | Returns |
|--------|-------------|---------|
| `get_stock_bars(request_params)` | `StockBarsRequest` | `BarSet` (dict-like, `.df` for DataFrame) |
| `get_stock_quotes(request_params)` | `StockQuotesRequest` | `QuoteSet` |
| `get_stock_trades(request_params)` | `StockTradesRequest` | `TradeSet` |
| `get_stock_latest_quote(request_params)` | `StockLatestQuoteRequest` | `dict[symbol, Quote]` |
| `get_stock_latest_trade(request_params)` | `StockLatestTradeRequest` | `dict[symbol, Trade]` |
| `get_stock_latest_bar(request_params)` | `StockLatestBarRequest` | `dict[symbol, Bar]` |
| `get_stock_snapshot(request_params)` | `StockSnapshotRequest` | `dict[symbol, Snapshot]` |

```python
from alpaca.data.requests import (
    StockBarsRequest, StockQuotesRequest, StockTradesRequest,
    StockLatestQuoteRequest, StockLatestTradeRequest,
    StockLatestBarRequest, StockSnapshotRequest,
)
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.enums import Adjustment, DataFeed
from datetime import datetime, timedelta

# Bars
bars = client.get_stock_bars(StockBarsRequest(
    symbol_or_symbols=["AAPL", "MSFT"],
    timeframe=TimeFrame.Day,
    start=datetime(2024, 1, 1),
    end=datetime(2024, 1, 31),
    adjustment=Adjustment.ALL,
    feed=DataFeed.SIP,
))
df = bars.df  # MultiIndex DataFrame (symbol, timestamp)

# Latest quote
quotes = client.get_stock_latest_quote(
    StockLatestQuoteRequest(symbol_or_symbols="AAPL")
)
print(quotes["AAPL"].ask_price, quotes["AAPL"].bid_price)

# Snapshot (aggregates latest quote, trade, bar)
snap = client.get_stock_snapshot(
    StockSnapshotRequest(symbol_or_symbols=["AAPL", "TSLA"])
)
for sym, s in snap.items():
    print(sym, s.latest_trade.price, s.daily_bar.close)
```

---

## 2. CryptoHistoricalDataClient

Historical data for cryptocurrency pairs (e.g. `BTC/USD`, `ETH/USD`).

```python
from alpaca.data.historical import CryptoHistoricalDataClient
# or:
from alpaca.data.historical.crypto import CryptoHistoricalDataClient

client = CryptoHistoricalDataClient(
    api_key="YOUR_APCA_API_KEY_ID",
    secret_key="YOUR_APCA_API_SECRET_KEY",
)
```

### Methods

| Method | Request type | Notes |
|--------|-------------|-------|
| `get_crypto_bars(request_params)` | `CryptoBarsRequest` | OHLCV bars |
| `get_crypto_quotes(request_params)` | `CryptoQuotesRequest` | Bid/ask history |
| `get_crypto_trades(request_params)` | `CryptoTradesRequest` | Tick trades |
| `get_crypto_latest_quote(request_params)` | `CryptoLatestQuoteRequest` | Current bid/ask |
| `get_crypto_latest_trade(request_params)` | `CryptoLatestTradeRequest` | Last trade |
| `get_crypto_latest_bar(request_params)` | `CryptoLatestBarRequest` | Latest bar |
| `get_crypto_snapshot(request_params)` | `CryptoSnapshotRequest` | Aggregated snapshot |
| `get_crypto_orderbook(request_params)` | `CryptoOrderbookRequest` | L2 order book |

```python
from alpaca.data.requests import (
    CryptoBarsRequest, CryptoLatestQuoteRequest,
    CryptoOrderbookRequest,
)
from alpaca.data.timeframe import TimeFrame

# 1-hour bars for BTC/USD
bars = client.get_crypto_bars(CryptoBarsRequest(
    symbol_or_symbols="BTC/USD",
    timeframe=TimeFrame.Hour,
    start=datetime(2024, 1, 1),
))
print(bars.df.tail())

# Latest quote
q = client.get_crypto_latest_quote(
    CryptoLatestQuoteRequest(symbol_or_symbols=["BTC/USD", "ETH/USD"])
)
print(q["BTC/USD"].ask_price)

# Order book
ob = client.get_crypto_orderbook(
    CryptoOrderbookRequest(symbol_or_symbols="BTC/USD")
)
print(ob["BTC/USD"].bids[:5], ob["BTC/USD"].asks[:5])
```

---

## 3. OptionHistoricalDataClient

Historical data and snapshots for US equity options.

```python
from alpaca.data.historical import OptionHistoricalDataClient
# or:
from alpaca.data.historical.option import OptionHistoricalDataClient

client = OptionHistoricalDataClient(
    api_key="YOUR_APCA_API_KEY_ID",
    secret_key="YOUR_APCA_API_SECRET_KEY",
)
```

### Methods

| Method | Request type | Notes |
|--------|-------------|-------|
| `get_option_bars(request_params)` | `OptionBarsRequest` | OHLCV bars for an option contract |
| `get_option_trades(request_params)` | `OptionTradesRequest` | Trade ticks |
| `get_option_latest_quote(request_params)` | `OptionLatestQuoteRequest` | Current bid/ask |
| `get_option_latest_trade(request_params)` | `OptionLatestTradeRequest` | Last trade |
| `get_option_snapshot(request_params)` | `OptionSnapshotRequest` | Snapshot for one/many contracts |
| `get_option_chain(request_params)` | `OptionChainRequest` | Full chain by underlying symbol |

```python
from alpaca.data.requests import (
    OptionBarsRequest, OptionChainRequest, OptionSnapshotRequest,
)
from alpaca.data.timeframe import TimeFrame

# Option bars for a specific contract
bars = client.get_option_bars(OptionBarsRequest(
    symbol_or_symbols="AAPL240621C00200000",
    timeframe=TimeFrame.Day,
    start=datetime(2024, 5, 1),
    end=datetime(2024, 6, 21),
))

# Option chain for an underlying (all strikes/expiries)
chain = client.get_option_chain(OptionChainRequest(
    underlying_symbol="AAPL",
))
for contract_symbol, snapshot in chain.items():
    q = snapshot.latest_quote
    print(contract_symbol, q.ask_price, q.bid_price, snapshot.greeks)
```

---

## 4. News (NewsClient)

Fetch financial news articles by symbol or general market.

```python
from alpaca.data.historical.news import NewsClient
from alpaca.data.requests import NewsRequest

# API keys optional for public news; use keys for higher rate limits
news_client = NewsClient(
    api_key="YOUR_APCA_API_KEY_ID",
    secret_key="YOUR_APCA_API_SECRET_KEY",
)
```

### Methods

| Method | Request type | Returns |
|--------|-------------|---------|
| `get_news(request_params)` | `NewsRequest` | `NewsSet` (`.news` list, `.df` DataFrame) |

```python
from datetime import datetime, timedelta
from alpaca.data.requests import NewsRequest

result = news_client.get_news(NewsRequest(
    symbols=["AAPL", "MSFT"],
    start=datetime.utcnow() - timedelta(days=7),
    end=datetime.utcnow(),
    sort="desc",         # or Sort.DESC enum
    limit=50,
    include_content=True,
    exclude_contentless=False,
))

# Access articles
for article in result.news:
    print(article.headline, article.source, article.created_at)
    print("  Symbols:", article.symbols)
    print("  URL:", article.url)

# As DataFrame
df = result.df
```

**Fallback:** Some `alpaca-py` versions expose news through `StockHistoricalDataClient`. If `NewsClient` is unavailable:

```python
# Fallback (version-dependent)
from alpaca.data.historical import StockHistoricalDataClient
client = StockHistoricalDataClient(api_key=..., secret_key=...)
result = client.get_news(NewsRequest(symbols=["AAPL"], limit=10))
```

---

## 5. Request Types

All request classes live in `alpaca.data.requests`.

### Stock requests

```python
from alpaca.data.requests import (
    StockBarsRequest,
    StockQuotesRequest,
    StockTradesRequest,
    StockLatestQuoteRequest,
    StockLatestTradeRequest,
    StockLatestBarRequest,
    StockSnapshotRequest,
)
```

**`StockBarsRequest`**
```python
StockBarsRequest(
    symbol_or_symbols: str | list[str],  # "AAPL" or ["AAPL", "MSFT"]
    timeframe: TimeFrame,                 # TimeFrame.Minute, TimeFrame.Day, TimeFrame(5, TimeFrameUnit.Minute)
    start: datetime | str | None = None,
    end: datetime | str | None = None,
    limit: int | None = None,            # max bars returned
    adjustment: Adjustment | None = None, # Adjustment.RAW, SPLIT, DIVIDEND, ALL
    feed: DataFeed | None = None,         # DataFeed.IEX, DataFeed.SIP
    sort: Sort | None = None,             # Sort.ASC (default), Sort.DESC
)
```

**`StockQuotesRequest`**
```python
StockQuotesRequest(
    symbol_or_symbols: str | list[str],
    start: datetime | str | None = None,
    end: datetime | str | None = None,
    limit: int | None = None,
    feed: DataFeed | None = None,
    sort: Sort | None = None,
)
```

**`StockTradesRequest`** — same fields as `StockQuotesRequest`.

**`StockLatestQuoteRequest`**
```python
StockLatestQuoteRequest(
    symbol_or_symbols: str | list[str],
    feed: DataFeed | None = None,
)
```

**`StockLatestTradeRequest`** — same as `StockLatestQuoteRequest`.

**`StockLatestBarRequest`** — same as `StockLatestQuoteRequest`.

**`StockSnapshotRequest`**
```python
StockSnapshotRequest(
    symbol_or_symbols: str | list[str],
    feed: DataFeed | None = None,
)
```

### Crypto requests

```python
from alpaca.data.requests import (
    CryptoBarsRequest,
    CryptoQuotesRequest,
    CryptoTradesRequest,
    CryptoLatestQuoteRequest,
    CryptoLatestTradeRequest,
    CryptoLatestBarRequest,
    CryptoSnapshotRequest,
    CryptoOrderbookRequest,
)
```

Mirror of stock requests with `Crypto*` prefix. `CryptoOrderbookRequest(symbol_or_symbols)` fetches the L2 order book.

### Option requests

```python
from alpaca.data.requests import (
    OptionBarsRequest,
    OptionTradesRequest,
    OptionLatestQuoteRequest,
    OptionLatestTradeRequest,
    OptionSnapshotRequest,
    OptionChainRequest,
)
```

**`OptionBarsRequest`** — same shape as `StockBarsRequest`.

**`OptionChainRequest`**
```python
OptionChainRequest(
    underlying_symbol: str,           # e.g. "AAPL"
    expiration_date: date | None = None,
    expiration_date_gte: date | None = None,
    expiration_date_lte: date | None = None,
    strike_price_gte: float | None = None,
    strike_price_lte: float | None = None,
    type: str | None = None,          # "call" or "put"
    limit: int | None = None,
)
```

### News request

```python
from alpaca.data.requests import NewsRequest

NewsRequest(
    symbols: list[str] | str | None = None,  # None = all market news
    start: datetime | str | None = None,
    end: datetime | str | None = None,
    sort: str | Sort | None = None,           # "asc" or "desc"
    include_content: bool = False,
    exclude_contentless: bool = False,
    limit: int | None = None,                 # max 50 per page; auto-paginated
)
```

---

## 6. Streams

All stream classes live in `alpaca.data.live`.

```python
from alpaca.data.live import (
    StockDataStream,
    CryptoDataStream,
    OptionDataStream,
    NewsDataStream,
)
```

### StockDataStream

```python
from alpaca.data.live import StockDataStream
from alpaca.data.enums import DataFeed

stream = StockDataStream(
    api_key="YOUR_APCA_API_KEY_ID",
    secret_key="YOUR_APCA_API_SECRET_KEY",
    feed=DataFeed.IEX,    # IEX (free) or SIP (paid)
    # raw_data=False,
    # websocket_params={},
)

# --- Subscriptions (all handlers must be async) ---

async def on_quote(quote):
    print(quote.symbol, quote.ask_price, quote.bid_price)

async def on_trade(trade):
    print(trade.symbol, trade.price, trade.size)

async def on_bar(bar):
    print(bar.symbol, bar.open, bar.high, bar.low, bar.close, bar.volume)

# Subscribe by passing handler then symbol(s)
stream.subscribe_quotes(on_quote, "AAPL", "MSFT")
stream.subscribe_trades(on_trade, "AAPL")
stream.subscribe_bars(on_bar, "AAPL", "SPY")
stream.subscribe_updated_bars(on_bar, "AAPL")   # real-time bar updates within the minute
stream.subscribe_daily_bars(on_bar, "SPY")

# Unsubscribe
stream.unsubscribe_quotes("MSFT")
stream.unsubscribe_trades("AAPL")
stream.unsubscribe_bars("SPY")

# Lifecycle
stream.run()   # blocking; starts the WebSocket event loop
stream.stop()  # call from another thread/task to stop
```

### CryptoDataStream

Same API shape as `StockDataStream`. Pairs use `"BTC/USD"` format.

```python
from alpaca.data.live import CryptoDataStream

stream = CryptoDataStream("YOUR_KEY", "YOUR_SECRET")

async def on_bar(bar):
    print("CRYPTO BAR", bar.symbol, bar.close)

stream.subscribe_bars(on_bar, "BTC/USD", "ETH/USD")
stream.subscribe_quotes(on_bar, "BTC/USD")
stream.run()
```

### OptionDataStream

```python
from alpaca.data.live.option import OptionDataStream

stream = OptionDataStream("YOUR_KEY", "YOUR_SECRET")

async def on_trade(trade):
    print(trade.symbol, trade.price, trade.size)

stream.subscribe_trades(on_trade, "AAPL240621C00200000")
stream.run()
```

### NewsDataStream

```python
from alpaca.data.live import NewsDataStream

news_stream = NewsDataStream("YOUR_KEY", "YOUR_SECRET")

async def on_news(item):
    print(item.headline, item.symbols, item.created_at)

# Subscribe to news for specific symbols (or "*" for all)
news_stream.subscribe_news(on_news, "AAPL", "MSFT")
news_stream.run()
```

### Running multiple streams concurrently

```python
import asyncio

async def main():
    await asyncio.gather(
        stock_stream._run_forever(),
        crypto_stream._run_forever(),
        news_stream._run_forever(),
    )

asyncio.run(main())
```

---

## 7. Models

All model classes live in `alpaca.data.models`. They are returned by client methods.

### Bar

```python
# from alpaca.data.models import Bar
Bar(
    symbol: str,
    timestamp: datetime,
    open: float,
    high: float,
    low: float,
    close: float,
    volume: float,
    trade_count: int,
    vwap: float,
)
```

Access: `bar.symbol`, `bar.close`, `bar.vwap`. `BarSet.df` gives a MultiIndex pandas DataFrame with `(symbol, timestamp)`.

### Quote

```python
Quote(
    symbol: str,
    timestamp: datetime,
    ask_price: float,
    ask_size: float,
    ask_exchange: str,
    bid_price: float,
    bid_size: float,
    bid_exchange: str,
    conditions: list[str],
    tape: str,
)
```

### Trade

```python
Trade(
    symbol: str,
    timestamp: datetime,
    price: float,
    size: float,
    exchange: str,
    id: str,
    conditions: list[str],
    tape: str,
)
```

### Snapshot

```python
Snapshot(
    symbol: str,
    latest_quote: Quote,
    latest_trade: Trade,
    minute_bar: Bar,
    daily_bar: Bar,
    previous_daily_bar: Bar,
)
```

Access: `snap["AAPL"].daily_bar.close`, `snap["AAPL"].latest_quote.ask_price`.

### News

```python
News(
    id: int,
    headline: str,
    summary: str,
    content: str | None,   # populated only if include_content=True
    url: str,
    source: str,
    symbols: list[str],
    created_at: datetime,
    updated_at: datetime,
    author: str,
)
```

---

## 8. Enums

### TimeFrame and TimeFrameUnit

```python
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

# Shorthand constants
TimeFrame.Minute    # 1-minute bars
TimeFrame.Hour      # 1-hour bars
TimeFrame.Day       # 1-day bars
TimeFrame.Week      # 1-week bars
TimeFrame.Month     # 1-month bars

# Custom intervals
TimeFrame(5, TimeFrameUnit.Minute)   # 5-minute bars
TimeFrame(4, TimeFrameUnit.Hour)     # 4-hour bars
TimeFrame(15, TimeFrameUnit.Minute)  # 15-minute bars

# TimeFrameUnit values
TimeFrameUnit.Minute
TimeFrameUnit.Hour
TimeFrameUnit.Day
TimeFrameUnit.Week
TimeFrameUnit.Month
```

### Adjustment

Controls how corporate actions (splits, dividends) are applied to price history.

```python
from alpaca.data.enums import Adjustment

Adjustment.RAW        # no adjustment
Adjustment.SPLIT      # split-adjusted
Adjustment.DIVIDEND   # dividend-adjusted
Adjustment.ALL        # split + dividend adjusted (recommended for backtesting)
```

### DataFeed

Selects the market data feed for stock requests and streams.

```python
from alpaca.data.enums import DataFeed

DataFeed.IEX   # IEX exchange feed — free tier, good coverage
DataFeed.SIP   # Consolidated tape (full SIP) — paid subscription
DataFeed.OTC   # OTC markets feed
```

### Sort

Controls chronological ordering of returned records.

```python
from alpaca.data.enums import Sort

Sort.ASC   # oldest → newest (default for most endpoints)
Sort.DESC  # newest → oldest
```

### CryptoFeed

```python
from alpaca.data.enums import CryptoFeed

CryptoFeed.US   # US crypto feed (default)
```

### Exchange

```python
from alpaca.data.enums import Exchange

# Common values: Exchange.NYSE, Exchange.NASDAQ, Exchange.AMEX, Exchange.OTC
```
