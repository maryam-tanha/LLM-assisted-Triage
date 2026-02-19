"""
Graph Builder
=============
Builds the RCA LangGraph dynamically from the specialist registry.

Graph topology:

    START
      │
      ▼
  parent_agent      ← decides "investigate" or "conclude"
      │
      │ "investigate" (Send fan-out — one Send per subtask)
      ▼
  [specialist nodes] ← run in parallel; each returns {current_cycle_findings: [...]}
      │                 results merged via Annotated[list, operator.add] reducer
      ▼
  synthesis         ← cross-domain correlation; produces CycleSummary
      │
      └──────────────► parent_agent  (loop back)
                            │
                            │ "conclude"
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
from agents.synthesis_agent import run_synthesis_agent
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

    product_config is captured as a closure so the parent and dispatch logic
    can look up service details without serialising the full config into graph state.
    """
    registry = get_all()

    # ── Parent agent node ────────────────────────────────────────────────────
    def parent_agent_node(state: GraphState) -> dict:
        """
        Orchestrates the investigation.

        On cycle 0 with pre-populated subtasks (manual mode): skip LLM and
        immediately mark as "investigate" so specialists run.

        Otherwise: call the parent LLM which decides to investigate more
        (create_subtasks) or conclude (write_rca_conclusion).
        """
        current_cycle: int = state.get("current_cycle", 0)

        # Manual override: subtasks pre-set before cycle 0 starts
        if state.get("subtasks") and current_cycle == 0:
            subtasks = state["subtasks"]
            print(f"\n  Parent agent (manual mode): using pre-set subtasks, starting cycle 1.")
            for st in subtasks:
                print(f"    [{st.subtask_id}] {st.service_name} ({st.container}) → agent: {st.assigned_agent}")
                print(f"      Task : {st.description}")
                print(f"      Why  : {st.hypothesis}")
            return {"parent_decision": "investigate", "current_cycle": 1}

        print(f"\n  Parent agent running (cycle {current_cycle + 1})...")
        agent_cfg_map = {a.agent_type: a for a in product_config.agents}
        available = {
            agent_type: (
                agent_cfg_map[agent_type].parent_llm_description()
                if agent_type in agent_cfg_map
                else entry.description
            )
            for agent_type, entry in registry.items()
        }
        update = run_parent_agent(
            incident_summary=state["incident_summary"],
            config=product_config,
            available_specialists=available,
            cycle_summaries=state.get("cycle_summaries", []),
            cumulative_history=state.get("cumulative_history", ""),
            current_cycle=current_cycle,
            max_cycles=state.get("max_cycles", 3),
        )
        decision = update.get("parent_decision", "")
        if decision == "investigate":
            subtasks = update.get("subtasks", [])
            print(f"  Parent decided: investigate with {len(subtasks)} subtask(s).")
            for st in subtasks:
                print(f"    [{st.subtask_id}] {st.service_name} ({st.container}) → agent: {st.assigned_agent}")
                print(f"      Task : {st.description}")
                print(f"      Why  : {st.hypothesis}")
        elif decision == "conclude":
            print("  Parent decided: conclude.")
        return update

    # ── Routing: parent → specialists (fan-out) or END ───────────────────────
    def route_parent(state: GraphState) -> list[Send] | str:
        """
        Route based on parent_decision:
          - "conclude" → END
          - "investigate" → Send fan-out to assigned specialist nodes
        """
        if state.get("parent_decision") == "conclude":
            return END

        sends: list[Send] = []
        for subtask in state.get("subtasks", []):
            entry = registry.get(subtask.assigned_agent)
            if entry is None:
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

    builder.add_node("parent_agent", parent_agent_node)
    builder.add_node("synthesis", run_synthesis_agent)

    for entry in registry.values():
        builder.add_node(entry.node_name, entry.node_fn)
        # Each specialist feeds into synthesis (not END)
        builder.add_edge(entry.node_name, "synthesis")

    builder.add_edge(START, "parent_agent")
    builder.add_conditional_edges("parent_agent", route_parent)
    builder.add_edge("synthesis", "parent_agent")

    return builder.compile()
