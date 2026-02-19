"""
Synthesis Agent
===============
After all specialist nodes complete a cycle, this agent:
  1. Reads new findings (current_cycle_findings[findings_offset:])
  2. Calls the LLM to produce a cross-domain correlation narrative
  3. Appends a CycleSummary to cycle_summaries
  4. Updates cumulative_history
  5. Advances findings_offset so the next cycle processes only new findings
"""

import re
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from config.llm import get_llm
from graph.state import CycleSummary, SpecialistFinding

load_dotenv(Path(__file__).parent.parent / ".env")


def _load_system_prompt() -> str:
    path = Path(__file__).parent.parent / "config" / "prompts" / "synthesis_system.txt"
    return path.read_text(encoding="utf-8")


def _build_user_message(
    incident_summary: str,
    new_findings: list[SpecialistFinding],
    cumulative_history: str,
    cycle_num: int,
) -> str:
    findings_text = "\n\n".join(
        f"### Specialist Finding #{i + 1} — {f.agent_type} (task: {f.subtask_id})\n"
        f"Confidence: {f.confidence:.0%}\n"
        f"Evidence: {', '.join(f.evidence) if f.evidence else 'none listed'}\n\n"
        f"{f.findings}"
        for i, f in enumerate(new_findings)
    )

    history_block = (
        f"## Prior Investigation History\n\n{cumulative_history}\n\n"
        if cumulative_history
        else ""
    )

    return (
        f"## Incident\n\n{incident_summary}\n\n"
        f"{history_block}"
        f"## Cycle {cycle_num} Specialist Findings\n\n{findings_text}"
    )


def _parse_synthesis(text: str) -> tuple[list[str], list[str], str]:
    """Extract SUMMARY, KEY_FINDINGS, RECOMMENDATIONS from synthesis output."""
    key_findings: list[str] = []
    recommendations: list[str] = []
    summary = text  # fallback: use full text as summary

    kf_match = re.search(r"KEY_FINDINGS:\s*\n((?:\s*-[^\n]*\n?)+)", text)
    if kf_match:
        key_findings = [
            line.strip().lstrip("- ")
            for line in kf_match.group(1).splitlines()
            if line.strip().startswith("-")
        ]

    rec_match = re.search(r"RECOMMENDATIONS:\s*\n((?:\s*-[^\n]*\n?)+)", text)
    if rec_match:
        recommendations = [
            line.strip().lstrip("- ")
            for line in rec_match.group(1).splitlines()
            if line.strip().startswith("-")
        ]

    summary_match = re.search(
        r"SUMMARY:\s*\n([\s\S]+?)(?:\nKEY_FINDINGS:|\nRECOMMENDATIONS:|\Z)", text
    )
    if summary_match:
        summary = summary_match.group(1).strip()

    return key_findings, recommendations, summary


def _update_history(current: str, cycle_num: int, synthesis_text: str) -> str:
    entry = f"=== Cycle {cycle_num} Synthesis ===\n{synthesis_text}"
    return f"{current}\n\n{entry}" if current else entry


def run_synthesis_agent(state: dict) -> dict:
    """
    LangGraph node function for the synthesis agent.

    Reads pending specialist findings, synthesizes them, updates cycle state.
    """
    all_findings: list[SpecialistFinding] = state.get("current_cycle_findings", [])
    offset: int = state.get("findings_offset", 0)
    new_findings = all_findings[offset:]

    if not new_findings:
        return {}  # nothing to synthesize — no state change

    cycle_num: int = state.get("current_cycle", 1)
    incident_summary: str = state.get("incident_summary", "")
    cumulative_history: str = state.get("cumulative_history", "")

    llm = get_llm()
    messages = [
        SystemMessage(content=_load_system_prompt()),
        HumanMessage(
            content=_build_user_message(
                incident_summary, new_findings, cumulative_history, cycle_num
            )
        ),
    ]

    response = llm.invoke(messages)
    synthesis_text = (
        response.content
        if isinstance(response.content, str)
        else "".join(
            block.get("text", "")
            for block in response.content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    )

    key_findings, recommendations, summary = _parse_synthesis(synthesis_text)
    specialist_types = list({f.agent_type for f in new_findings})

    cycle_summary = CycleSummary(
        cycle_num=cycle_num,
        summary=summary,
        key_findings=key_findings,
        recommendations=recommendations,
        specialist_types=specialist_types,
        timestamp=datetime.now(timezone.utc),
    )

    print(f"  Synthesis complete (cycle {cycle_num}).")
    return {
        "cycle_summaries": [cycle_summary],
        "cumulative_history": _update_history(cumulative_history, cycle_num, synthesis_text),
        "findings_offset": offset + len(new_findings),
    }
