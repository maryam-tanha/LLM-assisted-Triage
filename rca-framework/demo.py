"""
demo.py — RCA Framework Demo
=============================
Graph flow:
  START → planning (parent LLM) → [Send fan-out] → specialist nodes → END

Adding a new specialist:
  1. Create a BaseSpecialist subclass with its own prompt + context_commands
  2. Call register() at the bottom of its module
  3. Import that module below the "register specialists" block

Run from rca-framework/:
    python demo.py
    python demo.py --incident "Result page showing 0 votes for all candidates"
    python demo.py --service vote
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# ── Register specialists ──────────────────────────────────────────────────────
# Each import triggers the module-level register() call in that specialist file.
# The parent LLM and graph builder discover available agents from the registry.
import agents.specialists.log_agent  # noqa: F401

# ── Core imports ──────────────────────────────────────────────────────────────
from config.loader import load_config
from graph.builder import build_graph
from graph.registry import get_all
from graph.state import GraphState, Subtask, SpecialistFinding

CONFIG_PATH = Path(__file__).parent / "configs" / "voting_app.yaml"

DEFAULT_INCIDENT = (
    "Users are reporting that the voting page loads but votes don't seem to be "
    "registering. The result page shows 0 votes for all options even after multiple "
    "clicks. The containers appear to be running but something in the pipeline "
    "between vote → redis → worker → db → result may be broken."
)


# ── Formatters ────────────────────────────────────────────────────────────────

def print_separator(title: str = "") -> None:
    width = 70
    if title:
        pad = (width - len(title) - 2) // 2
        print(f"\n{'=' * pad} {title} {'=' * pad}")
    else:
        print("\n" + "=" * width)


def print_subtasks(subtasks: list[Subtask]) -> None:
    print_separator("PARENT AGENT — SUBTASKS GENERATED")
    for st in subtasks:
        print(f"\n  [{st.subtask_id}] {st.service_name} ({st.container})")
        print(f"  Agent       : {st.assigned_agent}")
        print(f"  Description : {st.description}")
        print(f"  Hypothesis  : {st.hypothesis}")


def print_finding(finding: SpecialistFinding) -> None:
    print_separator(f"FINDING — {finding.subtask_id} ({finding.agent_type})")
    print(f"  Confidence : {finding.confidence:.0%}")
    if finding.evidence:
        print(f"  Evidence   :")
        for e in finding.evidence:
            print(f"    - {e}")
    print(f"\n  Summary:\n")
    for line in finding.findings.splitlines():
        print(f"    {line}")
    if finding.commands_run:
        print(f"\n  Commands run ({len(finding.commands_run)}):")
        for cmd in finding.commands_run:
            print(f"    $ {cmd}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="RCA Framework Demo")
    parser.add_argument(
        "--incident",
        default=DEFAULT_INCIDENT,
        help="Incident description to investigate",
    )
    parser.add_argument(
        "--service",
        default=None,
        help="Target one service directly (skips parent LLM planning)",
    )
    args = parser.parse_args()

    # ── 1. Load config ────────────────────────────────────────────────────────
    print_separator("LOADING CONFIG")
    config = load_config(CONFIG_PATH)
    print(f"  Product     : {config.product}")
    print(f"  Services    : {[s.service_name for s in config.services]}")
    print(f"  Specialists : {list(get_all().keys())}")

    # ── 2. Build graph ────────────────────────────────────────────────────────
    graph = build_graph(config)

    # ── 3. Initial state ──────────────────────────────────────────────────────
    initial_state: GraphState = {
        "incident_id": "inc-001",
        "incident_summary": args.incident,
        "product_config": config.model_dump(),
        "subtasks": [],
        "current_cycle_findings": [],
    }

    # Manual mode: pre-populate subtasks so planning_node skips LLM
    if args.service:
        svc = config.get_service(args.service)
        if not svc:
            print(f"  ERROR: service '{args.service}' not found in config.")
            sys.exit(1)
        initial_state["subtasks"] = [
            Subtask(
                subtask_id="task-001",
                service_name=svc.service_name,
                container=svc.container,
                description=f"Investigate for incident: {args.incident}",
                hypothesis="Manual target — investigating directly.",
                assigned_agent="log",
            )
        ]
        print(f"\n  (Manual mode: targeting '{args.service}' only)")

    # ── 4. Run the graph ──────────────────────────────────────────────────────
    print_separator("PARENT AGENT — PLANNING")
    print(f"  Incident : {args.incident[:120]}...")
    if not args.service:
        print("\n  Calling LLM to plan investigation...")

    max_concurrency = int(os.environ.get("MAX_CONCURRENCY", "10"))
    result = graph.invoke(initial_state, config={"max_concurrency": max_concurrency})

    # ── 5. Print plan ─────────────────────────────────────────────────────────
    print_subtasks(result["subtasks"])

    findings: list[SpecialistFinding] = result["current_cycle_findings"]
    if not findings:
        print("\n  No findings produced.")
        return

    # ── 6. Print findings ─────────────────────────────────────────────────────
    print_separator("ALL FINDINGS")
    for finding in findings:
        print_finding(finding)

    print_separator()
    print(f"\n  Investigation complete. {len(findings)} finding(s) produced.\n")


if __name__ == "__main__":
    main()
