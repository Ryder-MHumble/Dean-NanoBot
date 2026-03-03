"""API usage tracker — appends one JSONL record per LLM call."""

import json
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path

_usage_file: Path | None = None

# ── Per-request context (set by the agent loop before each LLM call) ──────────
_ctx_sender:  ContextVar[str] = ContextVar("nanobot_sender",  default="unknown")
_ctx_channel: ContextVar[str] = ContextVar("nanobot_channel", default="unknown")


def set_context(sender_id: str, channel: str) -> None:
    """Called by the agent loop to bind the current user to subsequent records."""
    _ctx_sender.set(sender_id or "unknown")
    _ctx_channel.set(channel or "unknown")


def _file() -> Path:
    global _usage_file
    if _usage_file is None:
        d = Path.home() / ".nanobot"
        d.mkdir(parents=True, exist_ok=True)
        _usage_file = d / "usage.jsonl"
    return _usage_file


def record(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    cost_usd: float,
) -> None:
    """Append one usage record to ~/.nanobot/usage.jsonl (fire-and-forget)."""
    entry = {
        "ts":      datetime.now(timezone.utc).isoformat(),
        "sender":  _ctx_sender.get(),
        "channel": _ctx_channel.get(),
        "model":   model,
        "in":      prompt_tokens,
        "out":     completion_tokens,
        "total":   prompt_tokens + completion_tokens,
        "cost":    round(cost_usd, 8),
    }
    try:
        with open(_file(), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # never crash the main flow
