# Trading API — Recipes

All snippets assume:

```python
import os
from alpaca.trading.client import TradingClient

client = TradingClient(
    api_key=os.environ["APCA_API_KEY_ID"],
    secret_key=os.environ["APCA_API_SECRET_KEY"],
    paper=True,
)
```

## 1. Connect & verify

```python
account = client.get_account()
print(account.status, account.cash, account.equity, account.buying_power)
```

## 2. Market / limit / bracket order

```python
from alpaca.trading.requests import (
    MarketOrderRequest, LimitOrderRequest,
    TakeProfitRequest, StopLossRequest,
)
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass

# Market buy 1 share of AAPL
client.submit_order(MarketOrderRequest(
    symbol="AAPL", qty=1,
    side=OrderSide.BUY, time_in_force=TimeInForce.DAY,
))

# Limit sell at $200
client.submit_order(LimitOrderRequest(
    symbol="AAPL", qty=1, limit_price=200,
    side=OrderSide.SELL, time_in_force=TimeInForce.GTC,
))

# Bracket: buy with take-profit and stop-loss
client.submit_order(MarketOrderRequest(
    symbol="AAPL", qty=1,
    side=OrderSide.BUY, time_in_force=TimeInForce.GTC,
    order_class=OrderClass.BRACKET,
    take_profit=TakeProfitRequest(limit_price=210),
    stop_loss=StopLossRequest(stop_price=180, limit_price=179),
))
```

## 3. Stream order updates

```python
import asyncio
from alpaca.trading.stream import TradingStream

stream = TradingStream(
    os.environ["APCA_API_KEY_ID"],
    os.environ["APCA_API_SECRET_KEY"],
    paper=True,
)

async def on_update(data):
    print(data.event, data.order.symbol, data.order.status)

stream.subscribe_trade_updates(on_update)
stream.run()  # blocking; use stream.stop() to end
```

## 4. Get / close positions

```python
# All open positions
positions = client.get_all_positions()
for p in positions:
    print(p.symbol, p.qty, p.unrealized_pl)

# Single position
aapl = client.get_open_position("AAPL")

# Close everything
client.close_all_positions(cancel_orders=True)

# Close part of a position
from alpaca.trading.requests import ClosePositionRequest
client.close_position("AAPL", ClosePositionRequest(percentage="50"))
```

## 5. DCA scheduler skeleton

```python
import time
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

SYMBOL = "VOO"
NOTIONAL = 10  # dollars per cycle
INTERVAL_SECONDS = 7 * 24 * 3600  # weekly

while True:
    client.submit_order(MarketOrderRequest(
        symbol=SYMBOL, notional=NOTIONAL,
        side=OrderSide.BUY, time_in_force=TimeInForce.DAY,
    ))
    time.sleep(INTERVAL_SECONDS)
```

For production: replace the `while/sleep` with `cron` or `apscheduler`, and only fire when `client.get_clock().is_open`.

## 6. Natural-language → order parser pattern

When wiring an LLM tool call to Alpaca:

```python
from pydantic import BaseModel, Field
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

class PlaceOrderArgs(BaseModel):
    symbol: str = Field(..., description="Ticker, e.g. AAPL")
    side: str = Field(..., description="'buy' or 'sell'")
    qty: float | None = None
    notional: float | None = None
    limit_price: float | None = None

def place_order(args: PlaceOrderArgs):
    side = OrderSide.BUY if args.side.lower() == "buy" else OrderSide.SELL
    common = dict(symbol=args.symbol, side=side, time_in_force=TimeInForce.DAY)
    if args.qty is not None:
        common["qty"] = args.qty
    elif args.notional is not None:
        common["notional"] = args.notional
    else:
        raise ValueError("must supply qty or notional")
    if args.limit_price is None:
        return client.submit_order(MarketOrderRequest(**common))
    return client.submit_order(LimitOrderRequest(limit_price=args.limit_price, **common))
```

Expose `place_order` to the LLM via your agent framework's tool/function-calling API.
