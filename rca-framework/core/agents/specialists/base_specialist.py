import os
import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
import logging

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.errors import GraphRecursionError

from framework.llm import get_llm
from framework import usage_tracker
from framework.models import SSHConfig
from core.graph.state import SpecialistFinding
from core.security.allowlist import CommandAllowlist
from core.security.redactor import Redactor
from core.tools.docker_tool import DockerExecutor
from core.tools.ssh_tool import SSHExecutionError, SSHExecutor

# Ensure this logger writes to a separate file and doesn't pollute the main log
cmd_logger = logging.getLogger("CommandOutput")
if not cmd_logger.handlers:
    cmd_handler = logging.FileHandler("rca_commands.log")
    cmd_handler.setLevel(logging.INFO)
    cmd_handler.setFormatter(logging.Formatter('\n%(asctime)s - COMMAND OUTPUT:\n%(message)s\n' + '-'*60))
    cmd_logger.addHandler(cmd_handler)
cmd_logger.propagate = False

# Load .env from the project root (rca-framework/)
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

_INVESTIGATION_SUFFIX = (
    "Use the run_command tool to gather additional log evidence if needed. "
    "When you have enough information, provide your final analysis."
)


class BaseSpecialist(ABC):
    """Abstract base for all specialist agents.

    Subclasses must define agent_type and context_commands.
    The system_prompt is injected at call time from the profile YAML.
    The prompt_file property is kept for backward compatibility with tests.
    """

    @property
    @abstractmethod
    def agent_type(self) -> str: ...

    @property
    def prompt_file(self) -> str:
        """Deprecated: kept for backward compatibility. Prompt now comes from YAML."""
        return ""

    @property
    @abstractmethod
    def context_commands(self) -> list[str]: ...

    def run(
        self,
        subtask_id: str,
        subtask_description: str,
        ssh_config: SSHConfig,
        service_context: dict,
        system_prompt: str = "",
    ) -> SpecialistFinding:
        executor = SSHExecutor()
        redactor = Redactor()
        try:
            resolved_prompt = system_prompt or self._load_prompt_fallback()
            commands = service_context.get("context_commands") or self.context_commands
            context_output = self._run_context_commands(ssh_config, executor, commands)

            def execute_command(command: str) -> str:
                allowed, reason = CommandAllowlist.is_allowed(command)
                if not allowed:
                    return f"BLOCKED: {reason}"
                try:
                    raw = executor.execute(ssh_config, command)
                    return redactor.redact(raw)
                except SSHExecutionError as exc:
                    return f"SSH_ERROR: {exc}"

            service_guidance = _build_service_guidance(service_context)
            user_content = (
                f"## Context Output (from initial log gathering)\n\n"
                f"{context_output}\n"
                f"{service_guidance}\n"
                f"## Investigation Task\n\n"
                f"{subtask_description}\n\n"
                f"{_INVESTIGATION_SUFFIX}"
            )

            messages = [
                SystemMessage(content=resolved_prompt),
                HumanMessage(content=user_content),
            ]

            final_text, commands_run = self._run_tool_loop(messages, execute_command)
            return self._parse_finding(final_text, subtask_id, commands_run)
        finally:
            executor.close_all()

    def run_docker(
        self,
        subtask_id: str,
        subtask_description: str,
        container: str,
        service_context: dict,
        system_prompt: str = "",
    ) -> SpecialistFinding:
        """Run the specialist against a local Docker container instead of SSH."""
        executor = DockerExecutor()
        resolved_prompt = system_prompt or self._load_prompt_fallback()
        # Prefer service-level context_commands from the YAML over the agent's
        # generic defaults (which are designed for bare-metal/VM hosts).
        commands = service_context.get("context_commands") or self.context_commands
        context_output = self._run_context_commands_docker(container, executor, commands)

        def execute_command(command: str) -> str:
            return executor.run_checked(container, command)

        service_guidance = _build_service_guidance(service_context)
        user_content = (
            f"## Target Container\n\n"
            f"  {container}\n\n"
            f"## Context Output (from initial log gathering)\n\n"
            f"{context_output}\n"
            f"{service_guidance}\n"
            f"## Investigation Task\n\n"
            f"{subtask_description}\n\n"
            f"{_INVESTIGATION_SUFFIX}"
        )

        messages = [
            SystemMessage(content=resolved_prompt),
            HumanMessage(content=user_content),
        ]

        final_text, commands_run = self._run_tool_loop(messages, execute_command)
        return self._parse_finding(final_text, subtask_id, commands_run)

    def _load_prompt_fallback(self) -> str:
        """Fallback prompt loader for backward compatibility when system_prompt is not injected.

        Attempts to load from the old config/prompts/ path. If not found, returns empty string.
        """
        if not self.prompt_file:
            return ""
        prompt_path = (
            Path(__file__).parent.parent.parent.parent
            / "config"
            / "prompts"
            / self.prompt_file
        )
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return ""

    def _run_context_commands(
        self, ssh_config: SSHConfig, executor: SSHExecutor, commands: list[str] | None = None
    ) -> str:
        redactor = Redactor()
        outputs: list[str] = []
        for command in (commands or self.context_commands):
            allowed, reason = CommandAllowlist.is_allowed(command)
            if not allowed:
                outputs.append(f"=== {command} ===\nSKIPPED (blocked): {reason}\n")
                continue
            try:
                raw = executor.execute(ssh_config, command)
                redacted = redactor.redact(raw)
                outputs.append(f"=== {command} ===\n{redacted}\n")
            except SSHExecutionError as exc:
                outputs.append(f"=== {command} ===\nSSH_ERROR: {exc}\n")
        return "\n".join(outputs)

    def _run_context_commands_docker(
        self, container: str, executor: DockerExecutor, commands: list[str] | None = None
    ) -> str:
        outputs: list[str] = []

        # Prepend docker logs (host-side) so the LLM has the actual stdout/stderr
        # of the application before it tries any exec commands.
        container_logs = executor.get_container_logs(container)
        tail_count = os.environ.get("DOCKER_LOGS_TAIL", "200")
        outputs.append(
            f"=== docker logs {container} (last {tail_count} lines) ===\n"
            f"{container_logs}\n"
        )

        for command in (commands or self.context_commands):
            result = executor.run_checked(container, command)
            outputs.append(f"=== {command} ===\n{result}\n")
        return "\n".join(outputs)

    def _run_tool_loop(
        self,
        messages: list,
        execute_command: Callable[[str], str],
    ) -> tuple[str, list[str]]:
        """Run the specialist as a ReAct agent via create_agent (model + run_command tool)."""
        system_prompt = messages[0].content if messages else ""
        user_message = messages[1] if len(messages) > 1 else HumanMessage(content="")

        import logging
        import time
        logger = logging.getLogger("SpecialistAgent")

        @tool
        def run_command(command: str) -> str:
            """Execute a read-only shell command on the target host and return output."""
            logger.info(f"Agent executing tool: {command}")
            t0 = time.time()
            result = execute_command(command)
            duration = time.time() - t0
            logger.info(f"Command returned {len(result)} chars in {duration:.2f}s")
            
            if os.environ.get("LOG_COMMAND_OUTPUTS", "false").lower() == "true":
                cmd_logger.info(f"{command}\nOUTPUT:\n{result}")
                
            return result

        agent = create_agent(
            get_llm(),
            tools=[run_command],
            system_prompt=system_prompt,
        )
        max_iter = int(os.environ.get("MAX_ITERATIONS", "10"))
        buffer = max(2, max_iter // 5)
        recursion_limit = (max_iter + buffer) * 2 + 1
        try:
            t0 = time.time()
            result = agent.invoke(
                {"messages": [user_message]},
                config={"recursion_limit": recursion_limit},
            )
            duration = time.time() - t0
            logger.info(f"Specialist LLM agent run completed in {duration:.2f}s")
        except GraphRecursionError:
            return (
                "CONFIDENCE: 0.1\n"
                "EVIDENCE:\n"
                "- Investigation aborted: agent exceeded maximum tool-call iterations\n"
                "SUMMARY:\n"
                "The specialist reached the iteration limit without producing a final answer. "
                "This usually means the LLM entered a tool-call loop. "
                "Consider reducing the scope of the subtask or increasing MAX_ITERATIONS.\n",
                [],
            )

        for msg in result.get("messages", []):
            um = getattr(msg, "usage_metadata", None)
            if um:
                usage_tracker.record_usage(
                    um.get("input_tokens", 0), um.get("output_tokens", 0)
                )

        commands_run = [
            tc.get("args", {}).get("command", "")
            for msg in result["messages"]
            for tc in (getattr(msg, "tool_calls", None) or [])
        ]
        final_message = result["messages"][-1]
        final_text = _extract_text(final_message) if isinstance(final_message, AIMessage) else str(getattr(final_message, "content", ""))
        return final_text, commands_run

    def _parse_finding(
        self,
        llm_final_text: str,
        subtask_id: str,
        commands_run: list[str],
    ) -> SpecialistFinding:
        confidence = 0.5
        evidence: list[str] = []
        findings = llm_final_text

        conf_match = re.search(r"CONFIDENCE:\s*([\d.]+)", llm_final_text)
        if conf_match:
            try:
                confidence = max(0.0, min(1.0, float(conf_match.group(1))))
            except ValueError:
                pass

        evidence_match = re.search(
            r"EVIDENCE:\s*\n((?:\s*-[^\n]*\n?)+)", llm_final_text
        )
        if evidence_match:
            evidence = [
                line.strip().lstrip("- ")
                for line in evidence_match.group(1).splitlines()
                if line.strip().startswith("-")
            ]

        summary_match = re.search(
            r"SUMMARY:\s*\n([\s\S]+?)(?:\nCONFIDENCE:|\Z)", llm_final_text
        )
        if summary_match:
            findings = summary_match.group(1).strip()

        return SpecialistFinding(
            agent_type=self.agent_type,
            subtask_id=subtask_id,
            findings=findings,
            commands_run=commands_run,
            evidence=evidence,
            confidence=confidence,
            timestamp=datetime.now(timezone.utc),
        )


def _build_service_guidance(service_context: dict | None) -> str:
    """Format known failures and log hints into LLM prompt sections."""
    sc = service_context or {}
    known_failures = sc.get("known_failures", [])
    log_hints = sc.get("log_hints", [])

    sections: list[str] = []
    if known_failures:
        kf_lines = "\n".join(
            f"  - Pattern: \"{kf['pattern']}\" -> {kf['likely_cause']}"
            for kf in known_failures
        )
        sections.append(f"\n## Known Failure Patterns for This Service\n\n{kf_lines}\n")
    if log_hints:
        hint_lines = "\n".join(f"  - {h}" for h in log_hints)
        sections.append(f"\n## Investigation Hints\n\n{hint_lines}\n")
    return "".join(sections)


def _extract_text(response: AIMessage) -> str:
    """Extract plain text from an AIMessage, handling both str and block-list formats."""
    if isinstance(response.content, str):
        return response.content
    return "".join(
        block.get("text", "")
        for block in response.content
        if isinstance(block, dict) and block.get("type") == "text"
    )
