"""
Graph Builder
=============
Builds the RCA LangGraph dynamically from the specialist registry.

Graph topology:

    START
      │
      ▼
  planning          ← parent LLM: reads incident + config + available specialists,
      │               produces Subtask list with assigned_agent per task
      │ (Send fan-out — one Send per subtask, routed to the subtask's node_name)
      ▼
  [specialist nodes] ← run in parallel; each returns {current_cycle_findings: [...]}
      │                 results are merged via the Annotated[list, operator.add] reducer
      ▼
     END

Adding a new specialist type requires only:
  1. Creating a BaseSpecialist subclass
  2. Calling register() at the bottom of its module
  3. Importing that module in demo.py (or any entry point) to trigger registration
"""

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from agents.parent_agent import run_parent_agent
from config.loader import ProductConfig, ServiceConfig
from graph.registry import get_all
from graph.state import GraphState, Subtask


def _service_context(svc: ServiceConfig | None) -> dict:
    if svc is None:
        return {}
    return {
        "expected_behavior": svc.expected_behavior,
        "known_failures": [
            {"pattern": kf.pattern, "likely_cause": kf.likely_cause}
            for kf in svc.known_failures
        ],
        "context_commands": svc.context_commands,
        "log_hints": svc.log_hints,
    }


def _subtask_description(subtask: Subtask, svc: ServiceConfig | None) -> str:
    base = f"{subtask.description}\n\nHypothesis: {subtask.hypothesis}"
    if svc is None:
        return base
    return (
        f"{base}\n\n"
        f"Expected behavior: {svc.expected_behavior}\n"
        f"Known failures: {[{'pattern': kf.pattern, 'likely_cause': kf.likely_cause} for kf in svc.known_failures]}"
    )


def build_graph(product_config: ProductConfig):
    """
    Compile and return the RCA LangGraph.

    product_config is captured as a closure so the planning and dispatch nodes
    can look up service details without serialising the full config into graph state.
    """
    registry = get_all()

    # ── Planning node ────────────────────────────────────────────────────────
    def planning_node(state: GraphState) -> dict:
        """
        Call the parent LLM to decide which services to investigate and with
        which specialist.  Skipped when subtasks are pre-populated (manual mode).
        """
        if state.get("subtasks"):
            return {}  # manual override: keep existing subtasks as-is

        available = {agent_type: entry.description for agent_type, entry in registry.items()}
        subtasks = run_parent_agent(
            state["incident_summary"],
            product_config,
            available_specialists=available,
        )
        return {"subtasks": subtasks}

    # ── Dispatch (conditional edge) ──────────────────────────────────────────
    def dispatch_subtasks(state: GraphState) -> list[Send] | str:
        """
        Fan out each subtask to its assigned specialist node via Send.
        If no subtasks exist (e.g. parent returned nothing), route to END.
        """
        sends: list[Send] = []
        for subtask in state.get("subtasks", []):
            entry = registry.get(subtask.assigned_agent)
            if entry is None:
                # Unknown agent type — skip rather than crash
                continue
            svc = product_config.get_service(subtask.service_name)
            sends.append(
                Send(
                    entry.node_name,
                    {
                        "subtask_id": subtask.subtask_id,
                        "subtask_description": _subtask_description(subtask, svc),
                        "container": subtask.container,
                        "service_context": _service_context(svc),
                    },
                )
            )
        return sends if sends else END

    # ── Assemble graph ────────────────────────────────────────────────────────
    builder = StateGraph(GraphState)

    builder.add_node("planning", planning_node)

    for entry in registry.values():
        builder.add_node(entry.node_name, entry.node_fn)
        builder.add_edge(entry.node_name, END)

    builder.add_edge(START, "planning")
    builder.add_conditional_edges("planning", dispatch_subtasks)

    return builder.compile()
