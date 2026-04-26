"""Treasury AI multi-agent system.

LangGraph orchestration of 7 specialised agents:
  - cfo_router: classifies user intent
  - portfolio_reader: status / read queries
  - forecaster: cashflow analysis via bank MCP
  - strategist: builds T-bill ladder using live Alpaca quotes
  - risk_officer: validates against policy.yaml (veto power)
  - cfo_synthesis: composes natural-language reply for the user
  - executor: places approved trades via Alpaca paper Trading API
"""

from agents.graph import build_graph, run_graph

__all__ = ["build_graph", "run_graph"]
