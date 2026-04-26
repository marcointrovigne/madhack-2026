# Trading API — SDK Reference

Source: `alpaca-py` v0.43+ Trading module (`alpaca.trading.*`).
For live lookup: Context7 library `/alpacahq/alpaca-py`, or WebFetch `https://github.com/alpacahq/alpaca-py/blob/master/alpaca/trading/`.

---

## 1. TradingClient

```python
from alpaca.trading.client import TradingClient

client = TradingClient(
    api_key="...",          # APCA_API_KEY_ID
    secret_key="...",       # APCA_API_SECRET_KEY
    paper=True,             # True = paper, False = live (default True)
    raw_data=False,         # if True, returns raw dicts instead of models
    url_override=None,      # override base URL if needed
    oauth_token=None,       # alternative to api_key/secret_key (Connect API)
)
```

### Account

```python
# Read account info (status, cash, equity, buying_power, portfolio_value, etc.)
account = client.get_account()

# Read/update account-level settings (fractional shares, shorting, etc.)
config = client.get_account_configurations()
client.set_account_configurations(config)

# Portfolio history (equity curve, P&L by period)
# from alpaca.trading.requests import GetPortfolioHistoryRequest
history = client.get_portfolio_history(filter=GetPortfolioHistoryRequest(
    period="1M", timeframe="1D",
))
```

### Orders

```python
# Submit any order (pass the appropriate *OrderRequest object)
order = client.submit_order(order_data=request_obj)

# List orders with optional filter
from alpaca.trading.requests import GetOrdersRequest
orders = client.get_orders(filter=GetOrdersRequest(status=QueryOrderStatus.OPEN))

# Single order by UUID
order = client.get_order_by_id(order_id="uuid-string")

# Cancel all open orders; returns list of CancelOrderResponse
client.cancel_orders()

# Cancel one order
client.cancel_order_by_id(order_id="uuid-string")

# Replace an order (change qty, price, TIF, etc.)
from alpaca.trading.requests import ReplaceOrderRequest
client.replace_order_by_id(
    order_id="uuid-string",
    order_data=ReplaceOrderRequest(limit_price=195.0),
)
```

### Positions

```python
# All open positions
positions = client.get_all_positions()

# Single position by ticker or asset UUID
pos = client.get_open_position(symbol_or_asset_id="AAPL")

# Close all positions (optionally cancel open orders first)
client.close_all_positions(cancel_orders=True)

# Close part or all of one position
from alpaca.trading.requests import ClosePositionRequest
client.close_position(
    symbol_or_asset_id="AAPL",
    close_options=ClosePositionRequest(percentage="50"),   # or qty="5"
)
```

### Assets

```python
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass, AssetStatus

assets = client.get_all_assets(filter=GetAssetsRequest(
    asset_class=AssetClass.US_EQUITY,
    status=AssetStatus.ACTIVE,
))
asset = client.get_asset(symbol_or_asset_id="AAPL")
```

### Watchlists

```python
from alpaca.trading.requests import (
    CreateWatchlistRequest, UpdateWatchlistRequest, AddAssetsToWatchlistRequest,
)

wl = client.create_watchlist(CreateWatchlistRequest(name="MyList", symbols=["AAPL", "MSFT"]))
all_wl = client.get_watchlists()
wl = client.get_watchlist_by_id(watchlist_id=wl.id)
client.update_watchlist_by_id(watchlist_id=wl.id, watchlist_data=UpdateWatchlistRequest(name="NewName", symbols=["NVDA"]))
client.add_asset_to_watchlist_by_id(watchlist_id=wl.id, symbol="TSLA")
client.remove_asset_from_watchlist_by_id(watchlist_id=wl.id, symbol="TSLA")
client.delete_watchlist_by_id(watchlist_id=wl.id)
```

### Calendar & Clock

```python
from alpaca.trading.requests import GetCalendarRequest
from datetime import date

# Market calendar (trading days, open/close times)
calendar = client.get_calendar(filters=GetCalendarRequest(
    start=date(2024, 1, 1), end=date(2024, 12, 31)
))

# Current market clock (is_open, next_open, next_close, timestamp)
clock = client.get_clock()
print(clock.is_open, clock.next_open, clock.next_close)
```

### Corporate Actions

```python
from alpaca.trading.requests import GetCorporateAnnouncementsRequest
from alpaca.trading.enums import CorporateActionType

announcements = client.get_corporate_announcements(
    filter=GetCorporateAnnouncementsRequest(
        ca_types=[CorporateActionType.DIVIDEND],
        since=date(2024, 1, 1),
        until=date(2024, 12, 31),
        symbol="AAPL",
    )
)
```

---

## 2. Order Request Models

All request models live in `alpaca.trading.requests`.

```python
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    StopOrderRequest,
    StopLimitOrderRequest,
    TrailingStopOrderRequest,
    GetOrdersRequest,
    ReplaceOrderRequest,
    ClosePositionRequest,
    TakeProfitRequest,
    StopLossRequest,
)
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
```

### MarketOrderRequest

```python
MarketOrderRequest(
    symbol="AAPL",              # required: ticker string
    qty=1,                      # shares (mutually exclusive with notional)
    notional=100.0,             # dollar amount (fractional shares)
    side=OrderSide.BUY,         # required
    time_in_force=TimeInForce.DAY,  # required
    extended_hours=False,       # optional: True for pre/post market
    client_order_id="my-id",   # optional: idempotency key
    order_class=OrderClass.BRACKET,  # optional: SIMPLE/BRACKET/OCO/OTO
    take_profit=TakeProfitRequest(limit_price=210),   # if BRACKET/OCO/OTO
    stop_loss=StopLossRequest(stop_price=180),        # if BRACKET/OTO
)
```

### LimitOrderRequest

Same fields as `MarketOrderRequest`, plus:

```python
LimitOrderRequest(
    ...,
    limit_price=195.0,   # required
)
```

### StopOrderRequest

```python
StopOrderRequest(
    symbol="AAPL", qty=1, side=OrderSide.SELL,
    time_in_force=TimeInForce.GTC,
    stop_price=175.0,    # required
)
```

### StopLimitOrderRequest

```python
StopLimitOrderRequest(
    symbol="AAPL", qty=1, side=OrderSide.SELL,
    time_in_force=TimeInForce.GTC,
    stop_price=175.0,    # required: triggers the order
    limit_price=174.0,   # required: worst acceptable fill price
)
```

### TrailingStopOrderRequest

```python
TrailingStopOrderRequest(
    symbol="AAPL", qty=1, side=OrderSide.SELL,
    time_in_force=TimeInForce.GTC,
    trail_price=5.0,      # fixed $ trail (mutually exclusive with trail_percent)
    # trail_percent=2.5,  # % trail — use one or the other
)
```

### GetOrdersRequest

```python
GetOrdersRequest(
    status=QueryOrderStatus.OPEN,   # OPEN | CLOSED | ALL
    limit=50,                       # max orders to return (default 50, max 500)
    after=datetime(...),            # orders after this timestamp
    until=datetime(...),            # orders before this timestamp
    direction="asc",                # "asc" or "desc"
    nested=True,                    # include legs of multi-leg orders
    side=OrderSide.BUY,             # filter by side
    symbols=["AAPL", "MSFT"],       # filter by symbols
)
```

### ReplaceOrderRequest

```python
ReplaceOrderRequest(
    qty=2,
    time_in_force=TimeInForce.GTC,
    limit_price=196.0,
    stop_price=None,
    trail=None,                     # new trail value for trailing stops
    client_order_id="new-id",
)
```

### ClosePositionRequest

```python
ClosePositionRequest(
    qty="5",             # number of shares (string)
    # percentage="50",   # percentage 0–100 (mutually exclusive with qty)
)
```

### TakeProfitRequest / StopLossRequest (for bracket orders)

```python
TakeProfitRequest(
    limit_price=210.0,   # required: exit limit price
)

StopLossRequest(
    stop_price=180.0,    # required: stop trigger price
    limit_price=179.0,   # optional: converts stop to stop-limit leg
)
```

---

## 3. Enums

All enums live in `alpaca.trading.enums`.

```python
from alpaca.trading.enums import (
    OrderSide, TimeInForce, OrderClass, OrderStatus,
    AssetClass, AssetStatus, PositionSide, QueryOrderStatus,
)
```

### OrderSide

```python
OrderSide.BUY
OrderSide.SELL
```

### TimeInForce

```python
TimeInForce.DAY    # Good for day — expires at market close
TimeInForce.GTC    # Good till cancelled
TimeInForce.OPG    # Market-on-open (MOO/LOO)
TimeInForce.CLS    # Market-on-close (MOC/LOC)
TimeInForce.IOC    # Immediate or cancel (partial fills OK)
TimeInForce.FOK    # Fill or kill (all or nothing, immediately)
```

### OrderClass

```python
OrderClass.SIMPLE   # Standard single-leg order (default)
OrderClass.BRACKET  # Entry + take-profit + stop-loss
OrderClass.OCO      # One-cancels-other (take-profit + stop-loss on existing position)
OrderClass.OTO      # One-triggers-other (entry + one exit leg)
```

### OrderStatus

```python
OrderStatus.NEW
OrderStatus.PARTIALLY_FILLED
OrderStatus.FILLED
OrderStatus.DONE_FOR_DAY
OrderStatus.CANCELED
OrderStatus.EXPIRED
OrderStatus.REPLACED
OrderStatus.PENDING_CANCEL
OrderStatus.PENDING_REPLACE
OrderStatus.HELD
OrderStatus.ACCEPTED
OrderStatus.PENDING_NEW
OrderStatus.ACCEPTED_FOR_BIDDING
OrderStatus.STOPPED
OrderStatus.REJECTED
OrderStatus.SUSPENDED
OrderStatus.CALCULATED
```

### QueryOrderStatus (for GetOrdersRequest.status)

```python
QueryOrderStatus.OPEN    # all open orders (NEW, PARTIALLY_FILLED, etc.)
QueryOrderStatus.CLOSED  # filled/canceled/expired
QueryOrderStatus.ALL     # no filter
```

### AssetClass

```python
AssetClass.US_EQUITY   # US stocks and ETFs
AssetClass.CRYPTO      # Cryptocurrencies
AssetClass.US_OPTION   # US equity options
```

### AssetStatus

```python
AssetStatus.ACTIVE
AssetStatus.INACTIVE
```

### PositionSide

```python
PositionSide.LONG   # net long position
PositionSide.SHORT  # net short position
```

---

## 4. Streaming — TradingStream

Receives real-time order lifecycle events over WebSocket.

```python
from alpaca.trading.stream import TradingStream

stream = TradingStream(
    api_key="...",
    secret_key="...",
    paper=True,          # matches the environment of your TradingClient
    url_override=None,   # optional WSS URL override
)
```

### Subscribe and run

```python
async def on_update(data):
    # data is a TradeUpdate object
    print(data.event, data.order.symbol, data.order.status)

stream.subscribe_trade_updates(on_update)
stream.run()   # blocking — runs the asyncio event loop
# stream.stop()  # call from another thread or signal handler to stop
```

### TradeUpdate fields

| Field | Type | Description |
|-------|------|-------------|
| `event` | `TradeEvent` | e.g. `fill`, `partial_fill`, `canceled`, `replaced`, `new` |
| `order` | `Order` | Full order snapshot at event time |
| `timestamp` | `datetime` | When the event occurred |
| `position_qty` | `str` or `None` | Net position qty after the event |
| `price` | `str` or `None` | Fill price (if fill event) |
| `qty` | `str` or `None` | Filled qty for this event |

### TradeEvent values (common)

```python
from alpaca.trading.enums import TradeEvent

TradeEvent.NEW
TradeEvent.FILL
TradeEvent.PARTIAL_FILL
TradeEvent.CANCELED
TradeEvent.REPLACED
TradeEvent.PENDING_NEW
TradeEvent.REJECTED
TradeEvent.EXPIRED
```

### Async usage pattern

```python
import asyncio

async def main():
    stream = TradingStream("key", "secret", paper=True)

    async def handler(data):
        print(data)

    stream.subscribe_trade_updates(handler)
    await stream._run_forever()   # non-blocking coroutine version

asyncio.run(main())
```
