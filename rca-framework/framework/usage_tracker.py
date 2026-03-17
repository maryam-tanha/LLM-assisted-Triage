"""Token usage tracking and cost estimation for RCA framework runs.

Usage pattern:
    usage_tracker.start_run(run_id, model="anthropic/claude-...", profile="voting_app")
    # ... run the graph ...
    entry = usage_tracker.finish_run(duration_s=elapsed)
"""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path

_LOGS_DIR = Path(__file__).parent.parent / "logs"
_USAGE_FILE = _LOGS_DIR / "usage_log.jsonl"

# ── In-memory accumulator (one active run at a time) ──────────────────────────
_lock = threading.Lock()
_active: dict | None = None  # populated by start_run, cleared by finish_run


def start_run(run_id: str, model: str, profile: str) -> None:
    """Initialise the in-memory accumulator for a new investigation run."""
    global _active
    with _lock:
        _active = {
            "run_id": run_id,
            "model": model,
            "profile": profile,
            "input_tokens": 0,
            "output_tokens": 0,
            "started_at": datetime.now().isoformat(timespec="seconds"),
        }


def record_usage(input_tokens: int, output_tokens: int) -> None:
    """Accumulate token counts for the active run.  No-op if no run is active."""
    with _lock:
        if _active is None:
            return
        _active["input_tokens"] += input_tokens
        _active["output_tokens"] += output_tokens


def finish_run(duration_s: float) -> dict:
    """Finalise the active run, persist to JSONL, and clear state.

    Returns the persisted entry dict, or {} if no run was active.
    """
    global _active
    with _lock:
        if _active is None:
            return {}
        entry = dict(_active)
        _active = None

    entry["duration_seconds"] = round(duration_s, 1)
    entry["finished_at"] = datetime.now().isoformat(timespec="seconds")

    _LOGS_DIR.mkdir(exist_ok=True)
    with _USAGE_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")

    return entry


# ── History helpers ────────────────────────────────────────────────────────────

def load_history(profile: str | None = None, limit: int = 20) -> list[dict]:
    """Return the most-recent *limit* run entries from the JSONL log.

    Pass *profile* to filter entries to a specific investigation profile.
    Returns an empty list when the log does not exist yet.
    """
    if not _USAGE_FILE.exists():
        return []

    entries: list[dict] = []
    for line in _USAGE_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if profile:
        entries = [e for e in entries if e.get("profile") == profile]

    return entries[-limit:]  # most-recent N


def estimate_cost(
    input_price: float,
    output_price: float,
    profile: str | None = None,
    limit: int = 20,
) -> dict | None:
    """Estimate cost for one investigation based on historical token averages.

    Args:
        input_price:  USD per token for input  (OpenRouter ``pricing.prompt``).
        output_price: USD per token for output (OpenRouter ``pricing.completion``).
        profile:      Filter history to this profile name (recommended).
        limit:        Number of most-recent runs to average.

    Returns:
        Dict with keys ``avg_input_tokens``, ``avg_output_tokens``,
        ``estimated_cost_usd``, ``based_on_runs``; or ``None`` when no history.
    """
    history = load_history(profile=profile, limit=limit)
    if not history:
        return None

    avg_in = sum(e.get("input_tokens", 0) for e in history) / len(history)
    avg_out = sum(e.get("output_tokens", 0) for e in history) / len(history)
    cost = avg_in * input_price + avg_out * output_price

    return {
        "avg_input_tokens": int(avg_in),
        "avg_output_tokens": int(avg_out),
        "estimated_cost_usd": round(cost, 4),
        "based_on_runs": len(history),
    }
