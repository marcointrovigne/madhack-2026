"""Shared LLM and prompt loading utilities for Treasury AI agents."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from langchain_anthropic import ChatAnthropic

PROMPTS_DIR = Path(__file__).parent / "prompts"

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 2048


def load_prompt(name: str) -> str:
    """Load a markdown prompt from agents/prompts/<name>.md."""
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def get_anthropic_key() -> str:
    """Resolve the Anthropic API key from common env-var spellings."""
    for name in ("ANTHROPIC_API_KEY", "MADHACK-ANTHROPIC-KEY"):
        v = os.environ.get(name)
        if v:
            return v
    raise RuntimeError(
        "Anthropic API key not found. Set ANTHROPIC_API_KEY in your environment."
    )


def make_llm(
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.0,
) -> ChatAnthropic:
    """Build a ChatAnthropic instance with our defaults."""
    return ChatAnthropic(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        api_key=get_anthropic_key(),
    )


# Module-level shared LLM (most agents are deterministic)
_shared_llm: Optional[ChatAnthropic] = None


def shared_llm() -> ChatAnthropic:
    """Lazy-init shared LLM instance for reuse across agents."""
    global _shared_llm
    if _shared_llm is None:
        _shared_llm = make_llm()
    return _shared_llm
