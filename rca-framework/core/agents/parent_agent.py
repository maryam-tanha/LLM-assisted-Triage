from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from framework.llm import get_llm
from framework.models import ProductConfig
from framework import usage_tracker
from core.graph.state import CycleSummary, Subtask

load_dotenv(Path(__file__).parent.parent.parent / ".env")

# ── Tool: investigate — produce subtasks for specialist agents ────────────────
_CREATE_SUBTASKS_TOOL = {
    "name": "create_subtasks",
    "description": (
        "Create a list of investigation subtasks when you need more evidence. "
        "Call this when the current findings are insufficient to identify the root cause."
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

# ── Tool: conclude — write the final RCA when enough evidence exists ──────────
_WRITE_RCA_TOOL = {
    "name": "write_rca_conclusion",
    "description": (
        "Write the final Root Cause Analysis when you have enough evidence to conclude. "
        "Call this when the investigation findings are sufficient to identify the root cause."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "root_cause": {
                "type": "string",
                "description": "The identified root cause of the incident",
            },
            "contributing_factors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Secondary factors that contributed to the incident",
            },
            "evidence_summary": {
                "type": "string",
                "description": "Summary of the key evidence supporting this conclusion",
            },
            "recommended_actions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Immediate and long-term remediation steps",
            },
        },
        "required": [
            "root_cause",
            "contributing_factors",
            "evidence_summary",
            "recommended_actions",
        ],
    },
}


def _build_user_message(
    incident_summary: str,
    config: ProductConfig,
    available_specialists: dict[str, str],
    cycle_summaries: list[CycleSummary],
    cumulative_history: str,
    current_cycle: int,
    max_cycles: int,
) -> str:
    agent_blocks = []
    for agent_type, description in available_specialists.items():
        indented_desc = "\n".join(
            f"    {line}" if line.strip() else ""
            for line in description.splitlines()
        )
        agent_blocks.append(f"### {agent_type}\n{indented_desc}")
    specialists_block = "\n\n".join(agent_blocks)

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

    # Build cycle context section (empty on first cycle)
    cycle_context = ""
    if cycle_summaries:
        summaries_text = "\n\n".join(
            f"### Cycle {cs.cycle_num} Summary\n"
            f"{cs.summary}\n\n"
            f"Key Findings:\n"
            + "\n".join(f"  - {kf}" for kf in cs.key_findings)
            + (
                "\n\nRecommendations from synthesis:\n"
                + "\n".join(f"  - {r}" for r in cs.recommendations)
                if cs.recommendations
                else ""
            )
            for cs in cycle_summaries
        )
        cycles_remaining = max_cycles - current_cycle
        cycle_context = (
            f"## Investigation History ({len(cycle_summaries)} cycle(s) completed)\n\n"
            f"{summaries_text}\n\n"
            f"## Running Narrative\n\n{cumulative_history}\n\n"
            f"Cycles remaining before forced conclusion: {cycles_remaining}\n\n"
        )

    return (
        f"## Available Specialist Agents\n\n{specialists_block}\n\n"
        f"## Incident\n\n{incident_summary}\n\n"
        f"## Service Configuration ({config.product})\n\n{services_text}\n\n"
        f"{cycle_context}"
    )


def _format_final_report(rca_args: dict) -> str:
    root_cause = rca_args.get("root_cause", "")
    contributing = rca_args.get("contributing_factors", [])
    evidence = rca_args.get("evidence_summary", "")
    actions = rca_args.get("recommended_actions", [])

    contributing_text = "\n".join(f"  - {f}" for f in contributing)
    actions_text = "\n".join(f"  - {a}" for a in actions)

    return (
        f"# Root Cause Analysis Report\n\n"
        f"## Root Cause\n\n{root_cause}\n\n"
        f"## Contributing Factors\n\n{contributing_text}\n\n"
        f"## Evidence Summary\n\n{evidence}\n\n"
        f"## Recommended Actions\n\n{actions_text}\n"
    )


def run_parent_agent(
    incident_summary: str,
    config: ProductConfig,
    available_specialists: dict[str, str],
    cycle_summaries: list[CycleSummary] | None = None,
    cumulative_history: str = "",
    current_cycle: int = 0,
    max_cycles: int = 3,
    system_prompt: str = "",
) -> dict:
    """
    Call the LLM parent agent to decide the next action.

    Returns a state-update dict with either:
      - {"parent_decision": "investigate", "subtasks": [...], "current_cycle": n+1}
      - {"parent_decision": "conclude", "rca_finding": "...", "final_report": "..."}
    """
    cycle_summaries = cycle_summaries or []

    # Force conclusion if we've hit the cycle cap
    force_conclude = current_cycle >= max_cycles

    llm = get_llm()
    tools = [_CREATE_SUBTASKS_TOOL, _WRITE_RCA_TOOL]
    # When forced to conclude, only expose the conclude tool
    if force_conclude:
        tools = [_WRITE_RCA_TOOL]

    llm_with_tools = llm.bind_tools(tools, tool_choice="any")

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=_build_user_message(
                incident_summary,
                config,
                available_specialists,
                cycle_summaries,
                cumulative_history,
                current_cycle,
                max_cycles,
            )
        ),
    ]

    if force_conclude:
        messages.append(
            HumanMessage(
                content=(
                    "You have reached the maximum number of investigation cycles. "
                    "You MUST call write_rca_conclusion now with your best assessment "
                    "based on all findings collected so far."
                )
            )
        )

    response = llm_with_tools.invoke(messages)

    um = getattr(response, "usage_metadata", None)
    if um:
        usage_tracker.record_usage(um.get("input_tokens", 0), um.get("output_tokens", 0))

    if not response.tool_calls:
        # Fallback: treat as conclude with whatever text was returned
        return {
            "parent_decision": "conclude",
            "rca_finding": response.content or "No conclusion produced.",
            "final_report": f"# Root Cause Analysis\n\n{response.content or 'No conclusion.'}",
        }

    tool_call = response.tool_calls[0]
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]

    if tool_name == "write_rca_conclusion":
        rca_text = tool_args.get("root_cause", "")
        return {
            "parent_decision": "conclude",
            "rca_finding": rca_text,
            "final_report": _format_final_report(tool_args),
        }

    # create_subtasks — investigate another cycle
    raw_subtasks = tool_args.get("subtasks", [])
    subtasks: list[Subtask] = []
    for i, raw in enumerate(raw_subtasks):
        assigned = raw.get("assigned_agent", "")
        if assigned not in available_specialists:
            assigned = next(iter(available_specialists), "log")

        subtasks.append(
            Subtask(
                subtask_id=f"c{current_cycle + 1}-task-{i + 1:03d}",
                service_name=raw["service_name"],
                container=raw["container"],
                description=raw["description"],
                hypothesis=raw["hypothesis"],
                assigned_agent=assigned,
            )
        )

    return {
        "parent_decision": "investigate",
        "subtasks": subtasks,
        "current_cycle": current_cycle + 1,
    }
