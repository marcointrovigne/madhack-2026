"""LangGraph nodes for Treasury AI.

Each node is an async function: TreasuryState -> dict (partial state update).

Patterns used:
  - cfo_router: LLM with structured output (intent classification only)
  - portfolio_reader: ReAct-style tool loop (variable read queries)
  - forecaster: Python pre-fetches MCP data, LLM analyses + structured output
  - strategist: Python pre-fetches Alpaca quotes, LLM constructs ladder
  - risk_officer: pure Python validation, LLM phrases the verdict
  - executor: pure Python — iterate proposal, submit orders
  - cfo_synthesis: LLM composes natural-language reply from full state
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from pydantic import BaseModel, Field

from agents.llm import load_prompt, shared_llm
from agents.state import (
    Allocation,
    AllocationLine,
    ExecutionFill,
    ExecutionResult,
    ForecastOutput,
    KeyOutflow,
    RiskVerdict,
    RiskViolation,
    TreasuryState,
)
from agents.tools import (
    EXECUTOR_TOOLS,
    PORTFOLIO_READ_TOOLS,
    alpaca_get_bars,
    alpaca_get_latest_quote,
    broker_get_account,
    broker_list_positions,
    broker_submit_order,
    get_bank_tools,
    load_company_profile,
    load_policy,
)

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

DEMO_CLIENT_ID = "main-company"
TARGET_TICKERS = ["SGOV", "BIL", "SHV", "SHY"]


def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _days_ago_iso(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()


async def _run_tool_loop(llm_with_tools, tools, messages: list, max_iter: int = 6):
    """Run a tool-calling loop until the LLM stops asking for tool calls."""
    tool_map = {t.name: t for t in tools}
    for _ in range(max_iter):
        response = await llm_with_tools.ainvoke(messages)
        messages.append(response)
        tool_calls = getattr(response, "tool_calls", None) or []
        if not tool_calls:
            return response, messages
        for tc in tool_calls:
            name = tc["name"]
            args = tc.get("args", {})
            tool = tool_map.get(name)
            if tool is None:
                content = f"Error: tool {name} not found"
            else:
                try:
                    if hasattr(tool, "ainvoke"):
                        content = await tool.ainvoke(args)
                    else:
                        content = tool.invoke(args)
                except Exception as e:
                    content = f"Error invoking {name}: {e}"
            messages.append(
                ToolMessage(content=json.dumps(content, default=str), tool_call_id=tc["id"])
            )
    return messages[-1], messages


async def _bank_tool(name: str, **kwargs) -> Any:
    """Call a single bank MCP tool by name with kwargs."""
    tools = await get_bank_tools()
    tool = next((t for t in tools if t.name == name), None)
    if tool is None:
        raise RuntimeError(f"Bank MCP tool not found: {name}")
    return await tool.ainvoke(kwargs)


# ----------------------------------------------------------------------
# CFO Router — classify user intent
# ----------------------------------------------------------------------

class _IntentSchema(BaseModel):
    intent: str = Field(description="One of: deploy, withdraw, status, what_if, education, approve, unknown")


async def cfo_router_node(state: TreasuryState) -> dict:
    user_message = state.get("user_message", "")
    awaiting = state.get("awaiting_approval", False)
    history = state.get("conversation_history", [])

    # Hot-path heuristic: if awaiting approval and user types short approval, skip the LLM call
    short = user_message.strip().lower()
    if awaiting and short in {"approve", "approved", "yes", "ok", "go", "do it", "execute", "proceed"}:
        return {"intent": "approve"}

    llm = shared_llm().with_structured_output(_IntentSchema)
    prompt = load_prompt("cfo_router")
    msg = (
        f"Conversation history (last 4 turns): {json.dumps(history[-4:], default=str)}\n\n"
        f"Awaiting approval flag: {awaiting}\n\n"
        f"User message: {user_message}"
    )
    try:
        result: _IntentSchema = await llm.ainvoke([SystemMessage(content=prompt), HumanMessage(content=msg)])
        intent = result.intent if result.intent in {"deploy", "withdraw", "status", "what_if", "education", "approve", "unknown"} else "unknown"
    except Exception:
        intent = "unknown"

    # Guard: if we set "approve" but nothing's awaiting, downgrade to unknown
    if intent == "approve" and not awaiting:
        intent = "unknown"

    update: dict = {"intent": intent}

    # Fresh deploy flow — wipe transient slots so we don't reuse old outputs
    if intent == "deploy":
        update.update(
            {
                "proposal_revision": 0,
                "forecast": None,
                "proposal": None,
                "risk_verdict": None,
                "execution_result": None,
                "awaiting_approval": False,
            }
        )

    # Approve uses the previously stored proposal — clear only execution_result
    if intent == "approve":
        update["execution_result"] = None

    return update


# ----------------------------------------------------------------------
# Portfolio Reader — answer status / read queries
# ----------------------------------------------------------------------

async def portfolio_reader_node(state: TreasuryState) -> dict:
    user_message = state.get("user_message", "")
    company = state.get("company_profile") or load_company_profile()

    bank_tools = await get_bank_tools()
    tools = PORTFOLIO_READ_TOOLS + bank_tools

    llm = shared_llm().bind_tools(tools)
    system = (
        load_prompt("portfolio_reader")
        + f"\n\nCompany context: {json.dumps(company['company'], default=str)}\n"
        f"Today: {_today_iso()}\n"
        f"Bank client_id to use: '{DEMO_CLIENT_ID}'"
    )
    messages = [SystemMessage(content=system), HumanMessage(content=user_message)]
    final, _ = await _run_tool_loop(llm, tools, messages, max_iter=6)
    text = final.content if isinstance(final.content, str) else str(final.content)
    return {"cfo_response": text, "company_profile": company}


# ----------------------------------------------------------------------
# Forecaster — analyze cashflow, project liquidity, output structured forecast
# ----------------------------------------------------------------------

async def forecaster_node(state: TreasuryState) -> dict:
    company = state.get("company_profile") or load_company_profile()

    # Pre-fetch raw data from MCP tools (deterministic, then LLM analyses)
    try:
        client_info = await _bank_tool("get_client", client_id=DEMO_CLIENT_ID)
    except Exception as e:
        client_info = {"error": str(e), "balance": 0}

    try:
        statement_90d = await _bank_tool(
            "get_statement",
            client_id=DEMO_CLIENT_ID,
            from_date=_days_ago_iso(90),
            to_date=_today_iso(),
            limit=2000,
        )
    except Exception as e:
        statement_90d = {"error": str(e), "movements": []}

    try:
        statement_360d = await _bank_tool(
            "get_statement",
            client_id=DEMO_CLIENT_ID,
            from_date=_days_ago_iso(360),
            to_date=_days_ago_iso(91),
            limit=2000,
        )
    except Exception as e:
        statement_360d = {"error": str(e), "movements": []}

    try:
        bank_policy = await _bank_tool("get_company_policy", client_id=DEMO_CLIENT_ID)
    except Exception:
        bank_policy = {}

    llm = shared_llm().with_structured_output(ForecastOutput)
    system = load_prompt("forecaster")
    user_blob = (
        f"Today: {_today_iso()}\n\n"
        f"Company profile: {json.dumps(company, default=str)}\n\n"
        f"Bank-side policy (from MCP): {json.dumps(bank_policy, default=str)}\n\n"
        f"Current account info: {json.dumps(client_info, default=str)}\n\n"
        f"Statement (last 90 days): {json.dumps(statement_90d, default=str)[:8000]}\n\n"
        f"Statement (90-360 days back): {json.dumps(statement_360d, default=str)[:6000]}\n\n"
        "Produce the structured ForecastOutput now."
    )
    try:
        forecast: ForecastOutput = await llm.ainvoke(
            [SystemMessage(content=system), HumanMessage(content=user_blob)]
        )
    except Exception as e:
        # Defensive fallback so the graph doesn't deadlock
        balance = 0.0
        if isinstance(client_info, dict):
            try:
                balance = float(client_info.get("balance", 0) or 0)
            except (TypeError, ValueError):
                balance = 0.0
        forecast = ForecastOutput(
            current_balance_usd=balance,
            monthly_burn_usd=65000,
            monthly_recurring_inflow_usd=45000,
            liquid_required_30d=max(balance * 0.2, 30000),
            liquid_required_90d=max(balance * 0.4, 90000),
            liquid_required_180d=max(balance * 0.6, 150000),
            lockable_long_term=max(0, balance - max(balance * 0.6, 150000)),
            key_outflows_next_180d=[],
            confidence="low",
            reasoning=f"Forecaster fell back to defaults due to: {e}",
        )

    return {"forecast": forecast, "company_profile": company}


# ----------------------------------------------------------------------
# Strategist — build T-bill ladder respecting Forecaster + Policy constraints
# ----------------------------------------------------------------------

async def strategist_node(state: TreasuryState) -> dict:
    forecast = state.get("forecast")
    policy = state.get("policy") or load_policy()
    risk_verdict = state.get("risk_verdict")
    revision = state.get("proposal_revision", 0)

    # Pre-fetch live quotes for all candidate tickers
    quotes = {}
    for sym in TARGET_TICKERS:
        try:
            q = alpaca_get_latest_quote.invoke({"symbol": sym})
            quotes[sym] = q
        except Exception as e:
            quotes[sym] = {"error": str(e)}

    # Pre-fetch the brokerage account's actual buying power — this is the
    # hard cap on what we can actually deploy. The Forecaster computes a
    # theoretical lockable amount from bank flow; the Strategist must respect
    # what's actually in the brokerage. (Customer wires more from bank if needed.)
    try:
        brokerage = broker_get_account.invoke({})
        brokerage_buying_power = float(brokerage.get("buying_power", 0))
        brokerage_cash = float(brokerage.get("cash", 0))
    except Exception:
        brokerage_buying_power = 0.0
        brokerage_cash = 0.0

    llm = shared_llm().with_structured_output(Allocation)
    system = load_prompt("strategist")
    revision_note = ""
    if risk_verdict and not risk_verdict.passed and revision > 0:
        revision_note = (
            f"\n\n## REVISION #{revision} REQUIRED\n"
            f"Your previous proposal was REJECTED. Violations:\n"
            f"{json.dumps([v.model_dump() for v in risk_verdict.violations], default=str)}\n"
            f"Risk Officer's suggestions: {risk_verdict.suggestions}\n"
            f"Fix these specific issues. Don't change unrelated parts of the allocation."
        )

    user_blob = (
        f"Today: {_today_iso()}\n\n"
        f"Forecast (from Forecaster):\n{forecast.model_dump_json() if forecast else '{}'}\n\n"
        f"Investment Policy (constraints):\n{json.dumps(policy, default=str)}\n\n"
        f"Live market quotes (Alpaca):\n{json.dumps(quotes, default=str)}\n\n"
        f"## ACTUAL BROKERAGE FUNDS (hard cap)\n"
        f"The customer's brokerage account currently has buying_power = ${brokerage_buying_power:,.2f}.\n"
        f"Cap `total_deployed_usd` at MIN(forecast.lockable_long_term, brokerage_buying_power * 0.98).\n"
        f"If brokerage funds are smaller than the lockable amount, propose deploying what's available\n"
        f"and mention in `rationale` that more capacity is available if the customer wires more from\n"
        f"their bank account.\n"
        f"{revision_note}\n"
        "Produce the structured Allocation now."
    )
    try:
        proposal: Allocation = await llm.ainvoke(
            [SystemMessage(content=system), HumanMessage(content=user_blob)]
        )
    except Exception as e:
        # Defensive fallback: trivial all-SGOV allocation
        lockable = forecast.lockable_long_term if forecast else 50000
        proposal = Allocation(
            lines=[
                AllocationLine(
                    ticker="SGOV",
                    amount_usd=round(lockable * 0.6, 2),
                    duration_bucket="0-3mo",
                    est_yield_pct=4.30,
                ),
                AllocationLine(
                    ticker="BIL",
                    amount_usd=round(lockable * 0.3, 2),
                    duration_bucket="1-3mo",
                    est_yield_pct=4.28,
                ),
            ],
            total_deployed_usd=round(lockable * 0.9, 2),
            cash_buffer_usd=round(lockable * 0.1, 2),
            blended_yield_pct=4.29,
            annual_yield_usd=round(lockable * 0.9 * 0.0429, 2),
            rationale=f"Fallback proposal due to: {e}",
        )

    return {"proposal": proposal, "proposal_revision": revision + 1, "policy": policy}


# ----------------------------------------------------------------------
# Risk Officer — Pure Python validation against policy.yaml
# ----------------------------------------------------------------------

def _validate_proposal(proposal: Allocation, policy: dict) -> RiskVerdict:
    violations: list[RiskViolation] = []

    allowed_tickers = policy.get("allowed_tickers", {})
    risk_limits = policy.get("risk_limits", {})
    liq_req = policy.get("liquidity_requirements", {})

    max_single_pct = float(risk_limits.get("max_pct_single_etf", 60))
    max_duration_months = float(risk_limits.get("max_duration_months", 18))
    max_lockup_pct = float(risk_limits.get("max_total_lockup_pct", 70))
    min_liquid_pct = float(liq_req.get("min_daily_liquidity_pct", 30))

    total = proposal.total_deployed_usd or 1.0
    weighted_dur = 0.0
    locked_long_pct = 0.0
    liquid_pct = 0.0

    for line in proposal.lines:
        # Check ticker is in whitelist
        meta = allowed_tickers.get(line.ticker)
        if meta is None:
            violations.append(
                RiskViolation(
                    rule="allowed_tickers whitelist",
                    actual=line.ticker,
                    field=f"lines[{line.ticker}]",
                )
            )
            continue
        # Single-ETF cap
        pct = (line.amount_usd / total) * 100
        if pct > max_single_pct:
            violations.append(
                RiskViolation(
                    rule=f"max_pct_single_etf={max_single_pct}",
                    actual=round(pct, 2),
                    field=f"lines[{line.ticker}]",
                )
            )
        # Duration bookkeeping
        dur_months = float(meta.get("duration_months", 0))
        weighted_dur += dur_months * (line.amount_usd / total)
        if dur_months > 3:
            locked_long_pct += pct
        else:
            liquid_pct += pct

    if weighted_dur > max_duration_months:
        violations.append(
            RiskViolation(
                rule=f"max_duration_months={max_duration_months}",
                actual=round(weighted_dur, 2),
                field="weighted_avg_duration",
            )
        )
    if locked_long_pct > max_lockup_pct:
        violations.append(
            RiskViolation(
                rule=f"max_total_lockup_pct={max_lockup_pct}",
                actual=round(locked_long_pct, 2),
                field="total_locked_>3mo",
            )
        )
    if liquid_pct < min_liquid_pct:
        violations.append(
            RiskViolation(
                rule=f"min_daily_liquidity_pct={min_liquid_pct}",
                actual=round(liquid_pct, 2),
                field="liquid_0_3mo_pct",
            )
        )

    passed = len(violations) == 0
    suggestions = None
    if not passed:
        # Generate a one-sentence machine-readable suggestion
        first = violations[0]
        suggestions = (
            f"Fix '{first.rule}' on '{first.field}' "
            f"(actual={first.actual}). Reduce that line's allocation and redistribute."
        )
    return RiskVerdict(passed=passed, violations=violations, suggestions=suggestions)


async def risk_officer_node(state: TreasuryState) -> dict:
    proposal = state.get("proposal")
    policy = state.get("policy") or load_policy()
    if proposal is None:
        return {"risk_verdict": RiskVerdict(passed=False, suggestions="No proposal to validate.")}
    verdict = _validate_proposal(proposal, policy)
    return {"risk_verdict": verdict, "policy": policy}


# ----------------------------------------------------------------------
# Executor — Pure Python: iterate proposal lines, submit market orders
# ----------------------------------------------------------------------

async def executor_node(state: TreasuryState) -> dict:
    proposal = state.get("proposal")
    if proposal is None:
        return {
            "execution_result": ExecutionResult(errors=["No proposal to execute"])
        }

    fills: list[ExecutionFill] = []
    errors: list[str] = []
    deployed = 0.0

    try:
        account = broker_get_account.invoke({})
        buying_power = float(account.get("buying_power", 0))
    except Exception as e:
        return {
            "execution_result": ExecutionResult(
                errors=[f"Could not read brokerage account: {e}"]
            )
        }

    if buying_power < proposal.total_deployed_usd * 0.95:
        # Allow a small slop, but if deeply insufficient, abort
        # (Paper accounts default to $100k buying power so this should pass)
        errors.append(
            f"Buying power ${buying_power:.0f} below proposal total "
            f"${proposal.total_deployed_usd:.0f}. Sizing down proportionally."
        )
        scale = buying_power / proposal.total_deployed_usd if proposal.total_deployed_usd > 0 else 0
    else:
        scale = 1.0

    for line in proposal.lines:
        target_usd = line.amount_usd * scale
        try:
            quote = alpaca_get_latest_quote.invoke({"symbol": line.ticker})
            ask = float(quote.get("ask") or quote.get("mid_price") or 0)
            if ask <= 0:
                raise ValueError(f"No live price for {line.ticker}")
            shares = math.floor(target_usd / ask * 100) / 100  # 2 decimals fractional
            if shares <= 0:
                errors.append(f"Skipped {line.ticker}: target ${target_usd:.2f} too small at ${ask:.2f}/share")
                continue
            order = broker_submit_order.invoke({"symbol": line.ticker, "qty": shares, "side": "buy"})
            avg_price = float(order.get("filled_avg_price") or ask)
            filled_usd = shares * avg_price
            fills.append(
                ExecutionFill(
                    ticker=line.ticker,
                    shares=shares,
                    avg_price=avg_price,
                    filled_usd=round(filled_usd, 2),
                    order_id=order.get("order_id", ""),
                )
            )
            deployed += filled_usd
        except Exception as e:
            errors.append(f"Failed to execute {line.ticker}: {e}")

    return {
        "execution_result": ExecutionResult(
            fills=fills,
            total_deployed_usd=round(deployed, 2),
            remaining_cash_usd=round(buying_power - deployed, 2),
            errors=errors,
        )
    }


# ----------------------------------------------------------------------
# CFO Synthesis — compose the natural-language reply for the user
# ----------------------------------------------------------------------

async def cfo_synthesis_node(state: TreasuryState) -> dict:
    llm = shared_llm()
    system = load_prompt("cfo_synthesis")

    intent = state.get("intent")
    forecast = state.get("forecast")
    proposal = state.get("proposal")
    verdict = state.get("risk_verdict")
    execution = state.get("execution_result")

    awaiting = (
        intent == "deploy"
        and proposal is not None
        and verdict is not None
        and verdict.passed
        and execution is None
    )

    blob = {
        "intent": intent,
        "user_message": state.get("user_message", ""),
        "forecast": forecast.model_dump() if forecast else None,
        "proposal": proposal.model_dump() if proposal else None,
        "risk_verdict": verdict.model_dump() if verdict else None,
        "execution_result": execution.model_dump() if execution else None,
        "awaiting_approval": awaiting,
        "company": (state.get("company_profile") or {}).get("company", {}),
    }
    user_blob = (
        f"Compose the founder-facing reply.\n\n"
        f"State summary:\n{json.dumps(blob, default=str, indent=2)}"
    )
    response = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=user_blob)])
    text = response.content if isinstance(response.content, str) else str(response.content)
    return {"cfo_response": text, "awaiting_approval": awaiting}


# ----------------------------------------------------------------------
# Education / catch-all — short LLM reply, no tools
# ----------------------------------------------------------------------

async def education_node(state: TreasuryState) -> dict:
    llm = shared_llm()
    system = (
        "You are Treasury AI's CFO Synthesis agent in education mode. "
        "Explain the financial concept the user is asking about, in 3-5 short sentences, "
        "using examples relevant to a startup with ~$325k cash. "
        "Be friendly, not condescending. End with a brief offer to help apply the concept."
    )
    response = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=state.get("user_message", ""))])
    text = response.content if isinstance(response.content, str) else str(response.content)
    return {"cfo_response": text}


async def what_if_node(state: TreasuryState) -> dict:
    """What-if simulation: run Forecaster with the user's hypothetical scenario described in the prompt."""
    # Reuse forecaster but feed the user's stress scenario as additional context
    company = state.get("company_profile") or load_company_profile()
    user_msg = state.get("user_message", "")

    try:
        client_info = await _bank_tool("get_client", client_id=DEMO_CLIENT_ID)
    except Exception:
        client_info = {}
    try:
        statement_90d = await _bank_tool(
            "get_statement",
            client_id=DEMO_CLIENT_ID,
            from_date=_days_ago_iso(180),
            to_date=_today_iso(),
            limit=2000,
        )
    except Exception:
        statement_90d = {"movements": []}

    llm = shared_llm().with_structured_output(ForecastOutput)
    system = load_prompt("forecaster") + (
        "\n\nYou are in WHAT-IF mode. Apply the user's hypothetical scenario "
        "as an adjustment to your forecast assumptions, and state the adjustment "
        "clearly in your reasoning."
    )
    user_blob = (
        f"Today: {_today_iso()}\n\n"
        f"User scenario: {user_msg}\n\n"
        f"Company profile: {json.dumps(company, default=str)}\n\n"
        f"Account: {json.dumps(client_info, default=str)}\n\n"
        f"Statement (last 180 days): {json.dumps(statement_90d, default=str)[:8000]}\n"
    )
    try:
        forecast: ForecastOutput = await llm.ainvoke(
            [SystemMessage(content=system), HumanMessage(content=user_blob)]
        )
    except Exception as e:
        forecast = ForecastOutput(
            current_balance_usd=float(client_info.get("balance", 0) or 0),
            monthly_burn_usd=65000,
            monthly_recurring_inflow_usd=45000,
            liquid_required_30d=30000,
            liquid_required_90d=90000,
            liquid_required_180d=150000,
            lockable_long_term=0,
            confidence="low",
            reasoning=f"What-if fallback: {e}",
        )
    return {"forecast": forecast}
