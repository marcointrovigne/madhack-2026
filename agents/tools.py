"""Tools for Treasury AI agents.

Three flavors:
1. **Broker API tools** (`agents.broker`) — account read, positions, order submission
   on the customer's brokerage account opened via Alpaca Broker API.
2. **Market Data tools** — quotes and bars, using the Trading/paper keys (works
   on the same data plane regardless of which account is trading).
3. **Bank MCP tools** — lazy-loaded from the local bank-mcp/ stdio server.

Account creation, funding, and per-account orders all flow through Broker API.
Market data is read-only and shared across the agent.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import yaml
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from langchain_core.tools import tool

PROJECT_ROOT = Path(__file__).parent.parent


# ----------------------------------------------------------------------
# Market data client (lazy singleton)
#
# Uses the Trading/paper credentials. Same data plane regardless of which
# brokerage account is doing the trading — quotes & bars don't depend on
# the broker-vs-trading API distinction.
# ----------------------------------------------------------------------

_data_client: Optional[StockHistoricalDataClient] = None


def _market_data_creds() -> tuple[str, str]:
    api_key = (
        os.environ.get("APCA_API_KEY_ID")
        or os.environ.get("ALPACA_API_KEY")
        or os.environ.get("MADHACK-ALPACA-KEY")
    )
    api_secret = (
        os.environ.get("APCA_API_SECRET_KEY")
        or os.environ.get("ALPACA_SECRET_KEY")
        or os.environ.get("ALPACA_API_SECRET")
        or os.environ.get("MADHACK-ALPACA-SECRET")
    )
    if not api_key or not api_secret:
        raise RuntimeError("Alpaca market-data keys not set in env")
    return api_key, api_secret


def get_data_client() -> StockHistoricalDataClient:
    global _data_client
    if _data_client is None:
        key, secret = _market_data_creds()
        _data_client = StockHistoricalDataClient(key, secret)
    return _data_client


# ----------------------------------------------------------------------
# Alpaca tools (LangChain)
# ----------------------------------------------------------------------

@tool
def alpaca_get_latest_quote(symbol: str) -> dict:
    """Get the latest bid/ask quote for a stock or ETF (e.g. 'BIL', 'SGOV', 'SHV', 'SHY').

    Returns: {symbol, bid, ask, mid_price, timestamp}.
    """
    sym = symbol.upper().strip()
    request = StockLatestQuoteRequest(symbol_or_symbols=sym)
    res = get_data_client().get_stock_latest_quote(request)
    q = res[sym]
    bid = float(q.bid_price or 0)
    ask = float(q.ask_price or 0)
    mid = (bid + ask) / 2 if (bid and ask) else (ask or bid)
    return {
        "symbol": sym,
        "bid": bid,
        "ask": ask,
        "mid_price": mid,
        "timestamp": str(q.timestamp),
    }


@tool
def alpaca_get_bars(symbol: str, days: int = 30) -> list:
    """Get recent daily bars for a ticker. Useful for estimating yield from distributions.

    Args:
        symbol: Ticker (e.g. 'BIL').
        days: How many calendar days of history (default 30).

    Returns: list of {date, open, close, high, low, volume}.
    """
    from datetime import datetime, timedelta, timezone

    sym = symbol.upper().strip()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    request = StockBarsRequest(
        symbol_or_symbols=sym,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
    )
    res = get_data_client().get_stock_bars(request)
    bars = res.data.get(sym, [])
    return [
        {
            "date": str(b.timestamp.date()),
            "open": float(b.open),
            "close": float(b.close),
            "high": float(b.high),
            "low": float(b.low),
            "volume": int(b.volume),
        }
        for b in bars
    ]


# Re-export Broker API tools alongside Market Data tools so callers
# only need one import surface.
from agents.broker import (  # noqa: E402  (imported here intentionally)
    BROKER_TOOLS_READ,
    BROKER_TOOLS_WRITE,
    broker_get_account,
    broker_get_recent_orders,
    broker_list_positions,
    broker_submit_order,
    fund_account,
    get_or_create_account,
    transfer_bank_to_brokerage,
)

# Convenience groupings used by the agent nodes
MARKET_DATA_TOOLS = [alpaca_get_latest_quote, alpaca_get_bars]
# Portfolio Reader can also initiate bank→brokerage wires (composite write).
PORTFOLIO_READ_TOOLS = MARKET_DATA_TOOLS + BROKER_TOOLS_READ + [transfer_bank_to_brokerage]
EXECUTOR_TOOLS = [alpaca_get_latest_quote, broker_get_account, broker_submit_order]


# ----------------------------------------------------------------------
# Bank MCP tools (lazy-loaded from stdio subprocess)
# ----------------------------------------------------------------------

_mcp_client = None
_bank_tools_cache = None


async def get_bank_tools() -> list:
    """Lazy-init the bank MCP client (stdio subprocess) and return its LangChain tools."""
    global _mcp_client, _bank_tools_cache
    if _bank_tools_cache is not None:
        return _bank_tools_cache

    from langchain_mcp_adapters.client import MultiServerMCPClient

    bank_dir = PROJECT_ROOT / "bank-mcp"
    mcp_script = bank_dir / "mcp_server.py"

    _mcp_client = MultiServerMCPClient(
        {
            "bank": {
                "command": sys.executable,
                "args": [str(mcp_script)],
                "transport": "stdio",
                "cwd": str(bank_dir),
                "env": {
                    **os.environ,
                    "BANK_MOCK_DB_PATH": str(bank_dir / "data" / "bank_mock.sqlite3"),
                },
            }
        }
    )
    _bank_tools_cache = await _mcp_client.get_tools()
    return _bank_tools_cache


# ----------------------------------------------------------------------
# Config loaders
# ----------------------------------------------------------------------

def load_policy() -> dict:
    """Load IPS policy from config/policy.yaml."""
    return yaml.safe_load((PROJECT_ROOT / "config" / "policy.yaml").read_text())


def load_company_profile() -> dict:
    """Load company profile from config/company_profile.yaml."""
    return yaml.safe_load((PROJECT_ROOT / "config" / "company_profile.yaml").read_text())
