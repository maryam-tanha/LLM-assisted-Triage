import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from config.llm import get_llm
from config.loader import ProductConfig
from graph.state import Subtask

load_dotenv(Path(__file__).parent.parent / ".env")

# Tool schema — the parent calls this once to produce subtasks for all specialists.
# The assigned_agent field is populated from the live registry description list that
# is injected into the prompt, so the LLM picks an agent type by name, not by guessing.
_CREATE_SUBTASKS_TOOL = {
    "name": "create_subtasks",
    "description": (
        "Create a list of investigation subtasks. "
        "Call this once with all subtasks you want the specialist agents to investigate."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "subtasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "The service_name from the config",
                        },
                        "container": {
                            "type": "string",
                            "description": "The exact container name from the config",
                        },
                        "description": {
                            "type": "string",
                            "description": "What the specialist should specifically look for",
                        },
                        "hypothesis": {
                            "type": "string",
                            "description": "Working theory about what went wrong here",
                        },
                        "assigned_agent": {
                            "type": "string",
                            "description": (
                                "The agent type to assign this subtask to. "
                                "Must be one of the available specialist types listed in the prompt."
                            ),
                        },
                    },
                    "required": [
                        "service_name",
                        "container",
                        "description",
                        "hypothesis",
                        "assigned_agent",
                    ],
                },
            }
        },
        "required": ["subtasks"],
    },
}


def _load_system_prompt() -> str:
    path = Path(__file__).parent.parent / "config" / "prompts" / "parent_system.txt"
    return path.read_text(encoding="utf-8")


def _build_user_message(
    incident_summary: str,
    config: ProductConfig,
    available_specialists: dict[str, str],
) -> str:
    """Format the incident + service config + available specialists into an LLM prompt."""
    specialists_block = "\n".join(
        f"  - {agent_type}: {description}"
        for agent_type, description in available_specialists.items()
    )

    services_block = []
    for svc in config.services:
        failures = "\n".join(
            f"      - pattern: {kf.pattern}\n        likely_cause: {kf.likely_cause}"
            for kf in svc.known_failures
        )
        services_block.append(
            f"  service_name: {svc.service_name}\n"
            f"  container: {svc.container}\n"
            f"  description: {svc.description.strip()}\n"
            f"  expected_behavior: {svc.expected_behavior.strip()}\n"
            f"  known_failures:\n{failures}"
        )

    services_text = "\n\n".join(services_block)
    return (
        f"## Available Specialist Agents\n\n{specialists_block}\n\n"
        f"## Incident\n\n{incident_summary}\n\n"
        f"## Service Configuration ({config.product})\n\n{services_text}"
    )


def run_parent_agent(
    incident_summary: str,
    config: ProductConfig,
    available_specialists: dict[str, str],
) -> list[Subtask]:
    """
    Call the LLM parent agent with the incident, service config, and available specialists.
    Returns a list of Subtask objects for the graph to dispatch to specialist nodes.
    """
    llm = get_llm()
    llm_with_tool = llm.bind_tools([_CREATE_SUBTASKS_TOOL], tool_choice="required")

    messages = [
        SystemMessage(content=_load_system_prompt()),
        HumanMessage(content=_build_user_message(incident_summary, config, available_specialists)),
    ]

    response = llm_with_tool.invoke(messages)

    if not response.tool_calls:
        raise RuntimeError(
            "Parent agent did not call create_subtasks. "
            f"Response: {response.content}"
        )

    tool_call = response.tool_calls[0]
    raw_subtasks = tool_call["args"].get("subtasks", [])

    subtasks: list[Subtask] = []
    for i, raw in enumerate(raw_subtasks):
        # Fall back to the first available specialist if the LLM returned an unknown type
        assigned = raw.get("assigned_agent", "")
        if assigned not in available_specialists:
            assigned = next(iter(available_specialists), "log")

        subtasks.append(
            Subtask(
                subtask_id=f"task-{i+1:03d}",
                service_name=raw["service_name"],
                container=raw["container"],
                description=raw["description"],
                hypothesis=raw["hypothesis"],
                assigned_agent=assigned,
            )
        )

    return subtasks
