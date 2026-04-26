"""Treasury AI — Orca-facing entry point.

Wires the LangGraph multi-agent system (agents/graph.py) into Orca's
process_message contract. Per-conversation state is held by LangGraph's
in-memory checkpointer keyed by Orca's chat/session id.
"""

import logging
import os

# Load .env early so Alpaca/Anthropic clients in submodules see the keys
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional; Orca-supplied vars also work
    pass

from orca import ChatMessage, OrcaHandler, Variables, create_agent_app

from agents.graph import run_graph

logger = logging.getLogger(__name__)


def _resolve_credential(variables: Variables, *names: str) -> str | None:
    """Look up a credential by any of the candidate names.

    Checks Orca admin-panel variables first (in the order given), then env vars.
    """
    for n in names:
        v = variables.get(n) or os.environ.get(n)
        if v:
            return v
    return None


def _hydrate_env(variables: Variables) -> None:
    """Push Orca-supplied variables into os.environ so module-level
    Alpaca/Anthropic clients can find them."""
    mapping = [
        # Market Data API (uses Trading/paper credentials — read-only)
        ("APCA_API_KEY_ID", ["APCA_API_KEY_ID", "ALPACA_API_KEY", "MADHACK-ALPACA-KEY"]),
        (
            "APCA_API_SECRET_KEY",
            ["APCA_API_SECRET_KEY", "ALPACA_API_SECRET", "ALPACA_SECRET_KEY", "MADHACK-ALPACA-SECRET"],
        ),
        # Broker API (separate credentials — used to open + trade on customer accounts)
        ("BROKER_API_KEY_ID", ["BROKER_API_KEY_ID", "MADHACK-BROKER-KEY"]),
        ("BROKER_API_SECRET_KEY", ["BROKER_API_SECRET_KEY", "MADHACK-BROKER-SECRET"]),
        # Anthropic
        ("ANTHROPIC_API_KEY", ["ANTHROPIC_API_KEY", "MADHACK-ANTHROPIC-KEY"]),
    ]
    for env_name, candidates in mapping:
        v = _resolve_credential(variables, *candidates)
        if v:
            os.environ[env_name] = v


def _thread_id_for(data: ChatMessage) -> str:
    """Use a stable per-conversation thread id so LangGraph state persists
    across user turns (e.g. propose → approve)."""
    for attr in ("chat_id", "session_id", "conversation_id"):
        v = getattr(data, attr, None)
        if v:
            return str(v)
    return "demo"


async def process_message(data: ChatMessage):
    handler = OrcaHandler()
    session = handler.begin(data)

    try:
        _hydrate_env(Variables(data.variables))

        # Sanity-check required keys
        if not os.environ.get("BROKER_API_KEY_ID") or not os.environ.get("BROKER_API_SECRET_KEY"):
            session.stream(
                "⚠ Missing Alpaca Broker API keys. Set BROKER_API_KEY_ID + BROKER_API_SECRET_KEY."
            )
            session.close()
            return
        if not os.environ.get("APCA_API_KEY_ID") or not os.environ.get("APCA_API_SECRET_KEY"):
            session.stream(
                "⚠ Missing Alpaca Market Data keys. Set APCA_API_KEY_ID + APCA_API_SECRET_KEY."
            )
            session.close()
            return
        if not os.environ.get("ANTHROPIC_API_KEY"):
            session.stream("⚠ Missing ANTHROPIC_API_KEY.")
            session.close()
            return

        thread_id = _thread_id_for(data)
        user_message = data.message or ""

        session.loading.start("thinking")
        try:
            reply = await run_graph(user_message=user_message, thread_id=thread_id)
        finally:
            session.loading.end("thinking")

        session.stream(reply)
        session.close()

    except Exception as e:
        logger.exception("Error processing message")
        session.error("Something went wrong.", exception=e)


app, orca = create_agent_app(
    process_message_func=process_message,
    title="Treasury AI",
    description="AI treasurer for European startups — multi-agent on Orca + Alpaca",
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
