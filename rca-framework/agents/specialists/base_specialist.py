import os
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from config.llm import get_llm
from config.models import SSHConfig
from graph.state import SpecialistFinding
from security.allowlist import CommandAllowlist
from security.redactor import Redactor
from tools.ssh_tool import SSHExecutionError, SSHExecutor
from tools.docker_tool import DockerExecutor

# Load .env from the project root (rca-framework/)
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# OpenAI-compatible tool schema (OpenRouter uses `parameters`, not `input_schema`)
_RUN_COMMAND_TOOL = {
    "name": "run_command",
    "description": "Execute a read-only shell command on the target host and return output",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to run on the remote host",
            }
        },
        "required": ["command"],
    },
}



class BaseSpecialist(ABC):
    """Abstract base for all specialist agents.

    Subclasses must define agent_type, prompt_file, and context_commands.
    The run() method orchestrates the full investigation flow.
    """

    @property
    @abstractmethod
    def agent_type(self) -> str: ...

    @property
    @abstractmethod
    def prompt_file(self) -> str: ...

    @property
    @abstractmethod
    def context_commands(self) -> list[str]: ...

    def run(
        self,
        subtask_id: str,
        subtask_description: str,
        ssh_config: SSHConfig,
        service_context: dict,
    ) -> SpecialistFinding:
        executor = SSHExecutor()
        try:
            system_prompt = self._load_prompt()
            context_output = self._run_context_commands(ssh_config, executor)
            final_text, commands_run = self._tool_loop(
                system_prompt,
                context_output,
                subtask_description,
                ssh_config,
                executor,
            )
            return self._parse_finding(final_text, subtask_id, commands_run)
        finally:
            executor.close_all()

    def run_docker(
        self,
        subtask_id: str,
        subtask_description: str,
        container: str,
        service_context: dict,
    ) -> SpecialistFinding:
        """Run the specialist against a local Docker container instead of SSH."""
        executor = DockerExecutor()
        system_prompt = self._load_prompt()
        # Prefer service-level context_commands from the YAML over the agent's
        # generic defaults (which are designed for bare-metal/VM hosts).
        commands = service_context.get("context_commands") or self.context_commands
        context_output = self._run_context_commands_docker(container, executor, commands)
        final_text, commands_run = self._tool_loop_docker(
            system_prompt,
            context_output,
            subtask_description,
            container,
            executor,
            service_context,
        )
        return self._parse_finding(final_text, subtask_id, commands_run)

    def _load_prompt(self) -> str:
        prompt_path = (
            Path(__file__).parent.parent.parent
            / "config"
            / "prompts"
            / self.prompt_file
        )
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_path}. "
                f"Expected at config/prompts/{self.prompt_file}"
            )
        return prompt_path.read_text(encoding="utf-8")

    def _run_context_commands(
        self, ssh_config: SSHConfig, executor: SSHExecutor
    ) -> str:
        redactor = Redactor()
        outputs: list[str] = []
        for command in self.context_commands:
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

    def _tool_loop(
        self,
        system_prompt: str,
        context_output: str,
        subtask_description: str,
        ssh_config: SSHConfig,
        executor: SSHExecutor,
    ) -> tuple[str, list[str]]:
        llm = get_llm()
        llm_with_tools = llm.bind_tools([_RUN_COMMAND_TOOL])
        redactor = Redactor()

        messages: list = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=(
                    f"## Context Output (from initial log gathering)\n\n"
                    f"{context_output}\n\n"
                    f"## Investigation Task\n\n"
                    f"{subtask_description}\n\n"
                    f"Use the run_command tool to gather additional log evidence if needed. "
                    f"When you have enough information, provide your final analysis."
                )
            ),
        ]

        commands_run: list[str] = []
        max_iterations = int(os.environ.get("MAX_ITERATIONS", "10"))

        for _ in range(max_iterations):
            response: AIMessage = llm_with_tools.invoke(messages)
            messages.append(response)

            if not response.tool_calls:
                return _extract_text(response), commands_run

            tool_results: list[ToolMessage] = []
            for tool_call in response.tool_calls:
                command = tool_call["args"].get("command", "")
                commands_run.append(command)

                allowed, reason = CommandAllowlist.is_allowed(command)
                if not allowed:
                    result_content = f"BLOCKED: {reason}"
                else:
                    try:
                        raw = executor.execute(ssh_config, command)
                        result_content = redactor.redact(raw)
                    except SSHExecutionError as exc:
                        result_content = f"SSH_ERROR: {exc}"

                tool_results.append(
                    ToolMessage(content=result_content, tool_call_id=tool_call["id"])
                )
            messages.extend(tool_results)

        # max_iterations reached — force final answer
        messages.append(
            HumanMessage(
                content=(
                    "You have reached the maximum number of tool calls. "
                    "Please provide your final analysis now based on what you have gathered."
                )
            )
        )
        response = llm_with_tools.invoke(messages)
        return _extract_text(response), commands_run

    def _run_context_commands_docker(
        self, container: str, executor: DockerExecutor, commands: list[str] | None = None
    ) -> str:
        outputs: list[str] = []

        # Prepend docker logs (host-side) so the LLM has the actual stdout/stderr
        # of the application before it tries any exec commands.
        # This avoids the LLM ever needing to read /proc/1/fd/1 or /dev/stdout,
        # which block forever when tailed from inside the container.
        container_logs = executor.get_container_logs(container)
        outputs.append(f"=== docker logs {container} (last {os.environ.get('DOCKER_LOGS_TAIL', '200')} lines) ===\n{container_logs}\n")

        for command in (commands or self.context_commands):
            result = executor.run_checked(container, command)
            outputs.append(f"=== {command} ===\n{result}\n")
        return "\n".join(outputs)

    def _tool_loop_docker(
        self,
        system_prompt: str,
        context_output: str,
        subtask_description: str,
        container: str,
        executor: DockerExecutor,
        service_context: dict | None = None,
    ) -> tuple[str, list[str]]:
        llm = get_llm()
        llm_with_tools = llm.bind_tools([_RUN_COMMAND_TOOL])

        sc = service_context or {}
        known_failures = sc.get("known_failures", [])
        log_hints = sc.get("log_hints", [])

        service_guidance = ""
        if known_failures:
            kf_lines = "\n".join(
                f"  - Pattern: \"{kf['pattern']}\" → {kf['likely_cause']}"
                for kf in known_failures
            )
            service_guidance += f"\n## Known Failure Patterns for This Service\n\n{kf_lines}\n"
        if log_hints:
            hint_lines = "\n".join(f"  - {h}" for h in log_hints)
            service_guidance += f"\n## Investigation Hints\n\n{hint_lines}\n"

        messages: list = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=(
                    f"## Target Container\n\n"
                    f"  {container}\n\n"
                    f"## Context Output (from initial log gathering)\n\n"
                    f"{context_output}\n"
                    f"{service_guidance}\n"
                    f"## Investigation Task\n\n"
                    f"{subtask_description}\n\n"
                    f"Use the run_command tool to gather additional log evidence if needed. "
                    f"When you have enough information, provide your final analysis."
                )
            ),
        ]

        commands_run: list[str] = []
        max_iterations = int(os.environ.get("MAX_ITERATIONS", "10"))

        for _ in range(max_iterations):
            response: AIMessage = llm_with_tools.invoke(messages)
            messages.append(response)

            if not response.tool_calls:
                return _extract_text(response), commands_run

            tool_results: list[ToolMessage] = []
            for tool_call in response.tool_calls:
                command = tool_call["args"].get("command", "")
                commands_run.append(command)
                result_content = executor.run_checked(container, command)
                tool_results.append(
                    ToolMessage(content=result_content, tool_call_id=tool_call["id"])
                )
            messages.extend(tool_results)

        messages.append(
            HumanMessage(
                content=(
                    "You have reached the maximum number of tool calls. "
                    "Please provide your final analysis now based on what you have gathered."
                )
            )
        )
        response = llm_with_tools.invoke(messages)
        return _extract_text(response), commands_run

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


def _extract_text(response: AIMessage) -> str:
    """Extract plain text from an AIMessage, handling both str and block-list formats."""
    if isinstance(response.content, str):
        return response.content
    return "".join(
        block.get("text", "")
        for block in response.content
        if isinstance(block, dict) and block.get("type") == "text"
    )
