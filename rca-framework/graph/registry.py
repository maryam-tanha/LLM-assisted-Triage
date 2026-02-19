"""
Specialist Agent Registry
=========================
Each specialist agent calls register() at module-import time.
The parent agent reads get_all() to discover what specialists exist
and includes their descriptions in its LLM prompt, so it can assign
the right agent type per subtask without anything being hardcoded.
"""

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class SpecialistRegistration:
    """Describes a specialist agent to both the graph builder and the parent LLM."""

    agent_type: str     # identifier used in Subtask.assigned_agent, e.g. "log"
    description: str    # shown to the parent LLM so it can choose the right specialist
    node_name: str      # LangGraph node name, e.g. "log_specialist"
    node_fn: Callable   # LangGraph node function


_REGISTRY: dict[str, SpecialistRegistration] = {}


def register(reg: SpecialistRegistration) -> None:
    """Register a specialist. Typically called at the bottom of each specialist module."""
    _REGISTRY[reg.agent_type] = reg


def get_all() -> dict[str, SpecialistRegistration]:
    """Return a snapshot of all currently registered specialists."""
    return dict(_REGISTRY)
