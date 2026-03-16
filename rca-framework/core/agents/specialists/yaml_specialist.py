"""
YAML Specialist
===============
A generic BaseSpecialist subclass that is driven entirely by an AgentConfig
loaded from a YAML file. This allows new specialist agents to be created by
adding a YAML file to ``profiles/<name>/agents/`` with no Python code required.

Behaviour controlled by AgentConfig fields:
- ``context_commands``         — shell commands run inside the container before
                                 the LLM loop (same as the ``context_commands``
                                 property on Python-based specialists).
- ``gather_docker_host_context`` — when True, prepends ``docker inspect``,
                                 ``docker stats --no-stream``, and
                                 ``docker events`` output from the host before
                                 the in-container context. Used by the Docker
                                 Specs specialist.

Registration is handled by ``core.graph.builder.build_graph()``, which creates
a YAMLSpecialist instance and registers it for every AgentConfig that does not
already have a Python-based specialist registered under the same ``agent_type``.
"""

from __future__ import annotations

from framework.models import AgentConfig
from core.agents.specialists.base_specialist import BaseSpecialist


class YAMLSpecialist(BaseSpecialist):
    """Specialist backed purely by an AgentConfig YAML — no Python subclass needed."""

    def __init__(self, agent_cfg: AgentConfig) -> None:
        self._agent_type = agent_cfg.agent_type
        self._context_commands = agent_cfg.context_commands
        self._gather_host = agent_cfg.gather_docker_host_context

    @property
    def agent_type(self) -> str:
        return self._agent_type

    @property
    def context_commands(self) -> list[str]:
        return self._context_commands

    def _run_context_commands_docker(
        self,
        container: str,
        executor,  # DockerExecutor — avoid circular import by not type-hinting
        commands: list[str] | None = None,
    ) -> str:
        """Gather in-container context, then optionally prepend host-side Docker data."""
        in_container = super()._run_context_commands_docker(container, executor, commands)

        if not self._gather_host:
            return in_container

        host_section = (
            f"\n\n=== docker inspect ===\n{executor.get_inspect(container)}"
            f"\n\n=== docker stats (snapshot) ===\n{executor.get_stats_snapshot(container)}"
            f"\n\n=== docker events (last 24h) ===\n{executor.get_events(container)}"
        )
        return host_section + in_container
