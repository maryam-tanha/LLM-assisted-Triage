from core.agents.specialists.base_specialist import BaseSpecialist
from core.graph.registry import SpecialistRegistration, register


class RuntimeStatusAgent(BaseSpecialist):
    """Specialist that assesses container runtime health: memory, disk, CPU, processes."""

    @property
    def agent_type(self) -> str:
        return "runtime_status"

    @property
    def prompt_file(self) -> str:
        # Kept for backward compatibility with existing tests.
        return "runtime_status_system.txt"

    @property
    def context_commands(self) -> list[str]:
        # Fallback used only when a service has no context_commands in the YAML.
        return [
            "df -h",
            "free -m",
            "top -bn1",
            "ps aux",
            "uptime",
            "cat /proc/meminfo",
            "cat /proc/1/status",
            "cat /proc/1/limits",
        ]


def runtime_status_specialist_node(state: dict) -> dict:
    """
    LangGraph node for the Runtime Status Specialist.

    Receives a payload dict dispatched via Send() from the graph's dispatch step.
    Expected keys: subtask_id, subtask_description, container, service_context,
    system_prompt (injected by builder from profile YAML).
    """
    finding = RuntimeStatusAgent().run_docker(
        subtask_id=state["subtask_id"],
        subtask_description=state["subtask_description"],
        container=state["container"],
        service_context=state.get("service_context", {}),
        system_prompt=state.get("system_prompt", ""),
    )
    return {"current_cycle_findings": [finding]}


register(
    SpecialistRegistration(
        agent_type="runtime_status",
        description=(
            "Checks container runtime health and resource usage: memory consumption, "
            "disk space, CPU load, process state, OOM risk, and resource limits. "
            "Use when the incident may involve resource exhaustion, OOM kills, disk full, "
            "high CPU, zombie processes, or misconfigured container limits."
        ),
        node_name="runtime_status_specialist",
        node_fn=runtime_status_specialist_node,
    )
)
