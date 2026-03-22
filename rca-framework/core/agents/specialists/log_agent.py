from core.agents.specialists.base_specialist import BaseSpecialist
from core.graph.registry import SpecialistRegistration, register


class LogAgent(BaseSpecialist):
    """Specialist agent that investigates container logs and system state."""

    @property
    def agent_type(self) -> str:
        return "log"

    @property
    def prompt_file(self) -> str:
        # Kept for backward compatibility with existing tests.
        return "log_system.txt"

    @property
    def context_commands(self) -> list[str]:
        # Fallback used only when no service-level context_commands are in the YAML.
        # These are VM/host style commands and will fail inside slim Docker containers;
        # prefer defining context_commands per service in the YAML instead.
        return [
            "journalctl -n 100 --no-pager",
            "dmesg | tail -50",
            "tail -n 200 /var/log/syslog",
        ]


def log_specialist_node(state: dict) -> dict:
    """
    LangGraph node for the Log Specialist.

    Receives a payload dict dispatched via Send() from the graph's dispatch step.
    Expected keys: subtask_id, subtask_description, container, service_context,
    system_prompt (injected by builder from profile YAML).
    """
    if "ssh_config" in state:
        finding = LogAgent().run(
            subtask_id=state["subtask_id"],
            subtask_description=state["subtask_description"],
            ssh_config=state["ssh_config"],
            service_context=state.get("service_context", {}),
            system_prompt=state.get("system_prompt", ""),
        )
    else:
        finding = LogAgent().run_docker(
            subtask_id=state["subtask_id"],
            subtask_description=state["subtask_description"],
            container=state["container"],
            service_context=state.get("service_context", {}),
            system_prompt=state.get("system_prompt", ""),
        )
    return {"current_cycle_findings": [finding]}


# Self-register so the parent agent and graph builder discover this specialist
# automatically without any hardcoding in demo.py or builder.py.
register(
    SpecialistRegistration(
        agent_type="log",
        description=(
            "Investigates container logs and runtime state via docker exec. "
            "Use for any service where you want to check application output, "
            "process state, filesystem, or service-specific CLI tools (redis-cli, psql, etc.)."
        ),
        node_name="log_specialist",
        node_fn=log_specialist_node,
    )
)
