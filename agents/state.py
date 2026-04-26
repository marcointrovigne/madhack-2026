"""Shared state for the Treasury AI LangGraph.

Every node reads/writes a slice of TreasuryState.  Inter-agent communication
happens through this object — there are no direct calls between agents.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, TypedDict

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field, field_validator


def _coerce_number(v):
    """Strip commas / currency symbols / whitespace from LLM-emitted numbers."""
    if isinstance(v, str):
        cleaned = v.replace(",", "").replace("$", "").replace("€", "").replace("USD", "").replace("EUR", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            pass
    return v


# ---------- Structured outputs from each agent ----------

class KeyOutflow(BaseModel):
    date: str
    amount_usd: float
    label: str

    _coerce_amount = field_validator("amount_usd", mode="before")(_coerce_number)


class ForecastOutput(BaseModel):
    """Forecaster's structured output — read by Strategist + CFO Synthesis."""
    current_balance_usd: float
    monthly_burn_usd: float
    monthly_recurring_inflow_usd: float
    liquid_required_30d: float
    liquid_required_90d: float
    liquid_required_180d: float
    lockable_long_term: float
    key_outflows_next_180d: list[KeyOutflow] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] = "medium"
    reasoning: str = ""

    _coerce_currency = field_validator(
        "current_balance_usd",
        "monthly_burn_usd",
        "monthly_recurring_inflow_usd",
        "liquid_required_30d",
        "liquid_required_90d",
        "liquid_required_180d",
        "lockable_long_term",
        mode="before",
    )(_coerce_number)


class AllocationLine(BaseModel):
    ticker: str
    amount_usd: float
    duration_bucket: str
    est_yield_pct: float

    _coerce_currency = field_validator("amount_usd", "est_yield_pct", mode="before")(_coerce_number)


class Allocation(BaseModel):
    """Strategist's proposal — validated by Risk Officer, executed by Executor."""
    lines: list[AllocationLine]
    total_deployed_usd: float
    cash_buffer_usd: float
    blended_yield_pct: float
    annual_yield_usd: float
    rationale: str

    _coerce_currency = field_validator(
        "total_deployed_usd",
        "cash_buffer_usd",
        "blended_yield_pct",
        "annual_yield_usd",
        mode="before",
    )(_coerce_number)


class RiskViolation(BaseModel):
    rule: str
    actual: Any
    field: str
    severity: Literal["block", "warn"] = "block"


class RiskVerdict(BaseModel):
    """Risk Officer's verdict — gates execution. Drives the revision loop."""
    passed: bool
    violations: list[RiskViolation] = Field(default_factory=list)
    suggestions: Optional[str] = None


class ExecutionFill(BaseModel):
    ticker: str
    shares: float
    avg_price: float
    filled_usd: float
    order_id: str = ""


class ExecutionResult(BaseModel):
    """Executor's confirmation — final action of a deploy flow."""
    fills: list[ExecutionFill] = Field(default_factory=list)
    total_deployed_usd: float = 0.0
    remaining_cash_usd: float = 0.0
    errors: list[str] = Field(default_factory=list)


# ---------- Intent classification ----------

Intent = Literal[
    "deploy",       # invest new cash
    "withdraw",     # pull cash out
    "status",       # show current state
    "what_if",      # simulation
    "education",    # explain a concept
    "approve",      # user is responding "approve" to a pending proposal
    "unknown",
]


# ---------- The shared state object ----------

class TreasuryState(TypedDict, total=False):
    # User & conversation
    user_message: str
    conversation_history: Annotated[list, add_messages]

    # Static context (loaded once)
    company_profile: dict
    policy: dict

    # Routing
    intent: Intent

    # Agent outputs
    forecast: Optional[ForecastOutput]
    proposal: Optional[Allocation]
    proposal_revision: int
    risk_verdict: Optional[RiskVerdict]
    execution_result: Optional[ExecutionResult]

    # Final response to user
    cfo_response: str
    awaiting_approval: bool
    user_approved: Optional[bool]
