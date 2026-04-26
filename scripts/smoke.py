"""Quick smoke test of the Treasury AI graph.

Run with:
    uv run python scripts/smoke.py "What's my current cash situation?"

Loads .env, invokes the graph once with the given message, prints the reply.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Make project root importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from agents.graph import run_graph  # noqa: E402  (import after load_dotenv)


async def main() -> None:
    message = sys.argv[1] if len(sys.argv) > 1 else "What's my current cash situation?"
    print(f"\n→ User: {message}\n")
    reply = await run_graph(message, thread_id="smoke")
    print("← Agent reply:\n")
    print(reply)
    print()


if __name__ == "__main__":
    asyncio.run(main())
