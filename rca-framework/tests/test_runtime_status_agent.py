"""
Tests for:
  - AgentConfig model and parent_llm_description()
  - load_profile loading agent YAML files
  - RuntimeStatusAgent basic properties
  - runtime_status_specialist_node LangGraph interface
"""
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.agents.specialists.runtime_status_agent import (
    RuntimeStatusAgent,
    runtime_status_specialist_node,
)
from framework.loader import load_profile
from framework.models import AgentConfig
from core.graph.state import SpecialistFinding
from core.security.allowlist import CommandAllowlist


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PROFILE_DIR = Path(__file__).parent.parent / "profiles" / "voting_app"


def _make_finding(**kwargs) -> SpecialistFinding:
    defaults = dict(
        agent_type="runtime_status",
        subtask_id="task-001",
        findings="## Runtime\nAll healthy.",
        commands_run=["df -h"],
        evidence=["Disk usage 45%"],
        confidence=0.9,
        timestamp=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return SpecialistFinding(**defaults)


# ---------------------------------------------------------------------------
# TestAgentConfig
# ---------------------------------------------------------------------------


class TestAgentConfig:
    def test_description_only(self):
        cfg = AgentConfig(agent_type="log", description="Checks logs.")
        assert cfg.parent_llm_description() == "Checks logs."

    def test_when_to_use_appended(self):
        cfg = AgentConfig(
            agent_type="log",
            description="Checks logs.",
            when_to_use="- Application errors\n- Connectivity issues",
        )
        result = cfg.parent_llm_description()
        assert "When to use:" in result
        assert "Application errors" in result

    def test_do_not_use_appended(self):
        cfg = AgentConfig(
            agent_type="log",
            description="Checks logs.",
            do_not_use="- Resource metrics",
        )
        result = cfg.parent_llm_description()
        assert "Do not use when:" in result
        assert "Resource metrics" in result

    def test_all_sections_combined(self):
        cfg = AgentConfig(
            agent_type="log",
            description="Checks logs.",
            when_to_use="- Errors",
            do_not_use="- CPU metrics",
        )
        result = cfg.parent_llm_description()
        assert result.index("Checks logs.") < result.index("When to use:")
        assert result.index("When to use:") < result.index("Do not use when:")

    def test_empty_when_to_use_not_shown(self):
        cfg = AgentConfig(agent_type="log", description="Desc.", when_to_use="   ")
        assert "When to use" not in cfg.parent_llm_description()

    def test_empty_do_not_use_not_shown(self):
        cfg = AgentConfig(agent_type="log", description="Desc.", do_not_use="\n")
        assert "Do not use" not in cfg.parent_llm_description()


# ---------------------------------------------------------------------------
# TestLoadProfileAgents
# ---------------------------------------------------------------------------


class TestLoadProfileAgents:
    def test_agents_loaded_from_yaml(self):
        config = load_profile(PROFILE_DIR)
        assert len(config.agents) == 2
        agent_types = {a.agent_type for a in config.agents}
        assert "log" in agent_types
        assert "runtime_status" in agent_types

    def test_log_agent_has_description(self):
        config = load_profile(PROFILE_DIR)
        log_agent = config.get_agent("log")
        assert log_agent is not None
        assert len(log_agent.description.strip()) > 0

    def test_runtime_agent_has_description(self):
        config = load_profile(PROFILE_DIR)
        rt_agent = config.get_agent("runtime_status")
        assert rt_agent is not None
        assert len(rt_agent.description.strip()) > 0

    def test_runtime_agent_has_when_to_use(self):
        config = load_profile(PROFILE_DIR)
        rt_agent = config.get_agent("runtime_status")
        assert rt_agent is not None
        assert rt_agent.when_to_use.strip() != ""

    def test_get_agent_unknown_returns_none(self):
        config = load_profile(PROFILE_DIR)
        assert config.get_agent("nonexistent") is None

    def test_parent_llm_description_includes_when_to_use(self):
        config = load_profile(PROFILE_DIR)
        rt_agent = config.get_agent("runtime_status")
        assert rt_agent is not None
        desc = rt_agent.parent_llm_description()
        assert "When to use" in desc

    def test_runtime_agent_has_system_prompt(self):
        config = load_profile(PROFILE_DIR)
        rt_agent = config.get_agent("runtime_status")
        assert rt_agent is not None
        assert rt_agent.system_prompt.strip() != ""

    def test_missing_profile_yaml_raises(self, tmp_path):
        empty_dir = tmp_path / "no_profile"
        empty_dir.mkdir()
        with pytest.raises(FileNotFoundError):
            load_profile(empty_dir)

    def test_no_agents_dir_defaults_to_empty(self, tmp_path):
        profile_dir = tmp_path / "test_profile"
        profile_dir.mkdir()
        (profile_dir / "profile.yaml").write_text(
            "profile_name: test\nproduct: Test\naccess_method: docker_exec\nservices: []\n"
        )
        (profile_dir / "parent.yaml").write_text("role: parent\nsystem_prompt: 'test'\n")
        (profile_dir / "synthesis.yaml").write_text("role: synthesis\nsystem_prompt: 'test'\n")
        config = load_profile(profile_dir)
        assert config.agents == []


# ---------------------------------------------------------------------------
# TestRuntimeStatusAgent
# ---------------------------------------------------------------------------


class TestRuntimeStatusAgent:
    def setup_method(self):
        self.agent = RuntimeStatusAgent()

    def test_agent_type(self):
        assert self.agent.agent_type == "runtime_status"

    def test_prompt_file(self):
        assert self.agent.prompt_file == "runtime_status_system.txt"

    def test_context_commands_not_empty(self):
        assert len(self.agent.context_commands) > 0

    def test_fallback_context_commands_all_allowed(self):
        for cmd in self.agent.context_commands:
            allowed, reason = CommandAllowlist.is_allowed(cmd)
            assert allowed, f"Fallback command blocked: {cmd!r} — {reason}"


# ---------------------------------------------------------------------------
# TestRuntimeStatusSpecialistNode
# ---------------------------------------------------------------------------


class TestRuntimeStatusSpecialistNode:
    @patch("core.agents.specialists.runtime_status_agent.RuntimeStatusAgent.run_docker")
    def test_node_returns_reducer_compatible_dict(self, mock_run_docker):
        mock_run_docker.return_value = _make_finding()

        state = {
            "subtask_id": "task-001",
            "subtask_description": "Check memory and disk",
            "container": "example-voting-app-redis-1",
            "service_context": {},
        }

        result = runtime_status_specialist_node(state)

        assert "current_cycle_findings" in result
        assert isinstance(result["current_cycle_findings"], list)
        assert len(result["current_cycle_findings"]) == 1
        assert result["current_cycle_findings"][0].agent_type == "runtime_status"

    @patch("core.agents.specialists.runtime_status_agent.RuntimeStatusAgent.run_docker")
    def test_node_passes_correct_arguments(self, mock_run_docker):
        mock_run_docker.return_value = _make_finding(subtask_id="t2")

        state = {
            "subtask_id": "t2",
            "subtask_description": "Check for OOM risk",
            "container": "example-voting-app-worker-1",
            "service_context": {"expected_behavior": "runs continuously"},
        }

        runtime_status_specialist_node(state)

        mock_run_docker.assert_called_once_with(
            subtask_id="t2",
            subtask_description="Check for OOM risk",
            container="example-voting-app-worker-1",
            service_context={"expected_behavior": "runs continuously"},
            system_prompt="",
        )

    @patch("core.agents.specialists.runtime_status_agent.RuntimeStatusAgent.run_docker")
    def test_node_uses_empty_service_context_when_missing(self, mock_run_docker):
        mock_run_docker.return_value = _make_finding()

        state = {
            "subtask_id": "t3",
            "subtask_description": "Disk check",
            "container": "example-voting-app-db-1",
            # no service_context key
        }

        runtime_status_specialist_node(state)

        _, kwargs = mock_run_docker.call_args
        assert kwargs["service_context"] == {}
