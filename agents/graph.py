"""Treasury AI — LangGraph orchestration.

Topology:
                    ┌────────────────┐
                    │   CFO Router   │   (classifies intent)
                    └───┬────────────┘
                        │ intent
        ┌───────────────┼───────────────┬───────────────┬───────────────┐
        │               │               │               │               │
        ▼               ▼               ▼               ▼               ▼
   status        deploy           what_if        education        approve
   (Portfolio    (Forecaster →    (What-If →     (Education →     (Executor →
    Reader →     Strategist →     CFO Synth →    END)             CFO Synth →
    END)         Risk Officer ←   END)                            END)
                 (revision loop
                  back to
                  Strategist)
                 → CFO Synth →
                  awaits approval
                  → END)

Inter-agent communication is via the shared TreasuryState object.
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agents.nodes import (
    cfo_router_node,
    cfo_synthesis_node,
    education_node,
    executor_node,
    forecaster_node,
    portfolio_reader_node,
    risk_officer_node,
    strategist_node,
    what_if_node,
)
from agents.state import TreasuryState
from agents.tools import load_company_profile, load_policy

MAX_REVISIONS = 3


def _route_after_cfo_router(state: TreasuryState) -> str:
    intent = state.get("intent", "unknown")
    return {
        "deploy": "forecaster",
        "withdraw": "portfolio_reader",  # MVP: surface positions, manual sell flow if asked
        "status": "portfolio_reader",
        "what_if": "what_if",
        "education": "education",
        "approve": "executor",
        "unknown": "cfo_synthesis",
    }.get(intent, "cfo_synthesis")


def _route_after_risk_officer(state: TreasuryState) -> str:
    verdict = state.get("risk_verdict")
    revision = state.get("proposal_revision", 0)
    if verdict is not None and verdict.passed:
        return "cfo_synthesis"
    if revision >= MAX_REVISIONS:
        return "cfo_synthesis"
    return "strategist"


def build_graph():
    """Construct and compile the Treasury AI state graph."""
    builder = StateGraph(TreasuryState)

    # Register all nodes
    builder.add_node("cfo_router", cfo_router_node)
    builder.add_node("portfolio_reader", portfolio_reader_node)
    builder.add_node("forecaster", forecaster_node)
    builder.add_node("strategist", strategist_node)
    builder.add_node("risk_officer", risk_officer_node)
    builder.add_node("executor", executor_node)
    builder.add_node("cfo_synthesis", cfo_synthesis_node)
    builder.add_node("education", education_node)
    builder.add_node("what_if", what_if_node)

    # Entry
    builder.add_edge(START, "cfo_router")

    # Branch after intent classification
    builder.add_conditional_edges(
        "cfo_router",
        _route_after_cfo_router,
        {
            "forecaster": "forecaster",
            "portfolio_reader": "portfolio_reader",
            "what_if": "what_if",
            "education": "education",
            "executor": "executor",
            "cfo_synthesis": "cfo_synthesis",
        },
    )

    # Deploy pipeline
    builder.add_edge("forecaster", "strategist")
    builder.add_edge("strategist", "risk_officer")
    builder.add_conditional_edges(
        "risk_officer",
        _route_after_risk_officer,
        {
            "strategist": "strategist",
            "cfo_synthesis": "cfo_synthesis",
        },
    )

    # Terminal edges
    builder.add_edge("executor", "cfo_synthesis")
    builder.add_edge("what_if", "cfo_synthesis")
    builder.add_edge("portfolio_reader", END)  # composes its own response inline
    builder.add_edge("education", END)
    builder.add_edge("cfo_synthesis", END)

    # Compile with in-memory checkpointer so state persists across user turns
    return builder.compile(checkpointer=MemorySaver())


# Module-level compiled graph (singleton)
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


async def run_graph(user_message: str, thread_id: str = "demo") -> str:
    """Run the graph for one user message, return the natural-language reply.

    The graph uses a checkpointer keyed by `thread_id`, so subsequent calls
    with the same thread_id resume from prior state (preserves proposals
    awaiting approval across user turns).
    """
    graph = get_graph()
    config = {"configurable": {"thread_id": thread_id}}

    # Lazy-load static context once (tiny YAML files)
    company_profile = load_company_profile()
    policy = load_policy()

    initial_input = {
        "user_message": user_message,
        "company_profile": company_profile,
        "policy": policy,
    }

    final_state = await graph.ainvoke(initial_input, config=config)
    return final_state.get("cfo_response") or "Sorry, I couldn't process that — could you rephrase?"
