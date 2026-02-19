import operator
from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, ConfigDict, field_validator
from typing_extensions import TypedDict


class SpecialistFinding(BaseModel):
    agent_type: str
    subtask_id: str
    findings: str
    commands_run: list[str]
    evidence: list[str]
    confidence: float
    timestamp: datetime

    model_config = ConfigDict(frozen=True)

    @field_validator("agent_type", "subtask_id")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v


class Subtask(BaseModel):
    """A single investigation task produced by the Parent Agent."""
    subtask_id: str
    service_name: str       # which service to investigate
    container: str          # docker container name (from YAML config)
    description: str        # what to look for
    hypothesis: str         # the parent's working theory
    assigned_agent: str     # must match a registered specialist agent_type

    model_config = ConfigDict(frozen=True)


class GraphState(TypedDict):
    # Incident
    incident_id: str
    incident_summary: str

    # Loaded from YAML — passed through so agents have full context
    product_config: dict

    # Parent agent output
    subtasks: list[Subtask]

    # Specialist findings — reducer appends results from parallel runs
    current_cycle_findings: Annotated[list[SpecialistFinding], operator.add]
