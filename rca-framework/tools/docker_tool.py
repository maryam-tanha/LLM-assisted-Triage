import os
import subprocess

from security.allowlist import CommandAllowlist
from security.redactor import Redactor


class DockerExecutionError(Exception):
    def __init__(self, message: str, command: str, container: str) -> None:
        super().__init__(message)
        self.command = command
        self.container = container


class DockerExecutor:
    """Runs commands inside a local Docker container via `docker exec`.

    Used instead of SSHExecutor when access_method is docker_exec.
    The allowlist and redactor are applied the same way as in the SSH path.
    """

    def execute(self, container: str, command: str) -> str:
        """Run `docker exec <container> sh -c <command>` and return stdout.

        Raises DockerExecutionError if the container is unreachable or the
        command exits with a non-zero status and produced no stdout.
        """
        max_output_bytes = int(os.environ.get("MAX_OUTPUT_BYTES", "65536"))
        stderr_max_bytes = int(os.environ.get("STDERR_MAX_BYTES", "4096"))
        timeout = int(os.environ.get("DOCKER_EXEC_TIMEOUT", "30"))
        try:
            result = subprocess.run(
                ["docker", "exec", container, "sh", "-c", command],
                capture_output=True,
                timeout=timeout,
            )
            stdout = result.stdout[:max_output_bytes].decode("utf-8", errors="replace")
            stderr = result.stderr[:stderr_max_bytes].decode("utf-8", errors="replace")

            if result.returncode != 0 and not stdout.strip():
                return f"STDERR: {stderr.strip()}"
            return stdout
        except subprocess.TimeoutExpired:
            raise DockerExecutionError(
                f"Command timed out after {timeout}s", command, container
            )
        except FileNotFoundError:
            raise DockerExecutionError(
                "docker binary not found on PATH", command, container
            )

    def get_container_logs(self, container: str) -> str:
        """Fetch container stdout/stderr via `docker logs` on the host.

        This is the only reliable way to read application stdout from a Docker
        container — /proc/1/fd/1 blocks forever when read from inside the container.
        Returns the last DOCKER_LOGS_TAIL lines, redacted and byte-capped.
        """
        tail = int(os.environ.get("DOCKER_LOGS_TAIL", "200"))
        max_output_bytes = int(os.environ.get("MAX_OUTPUT_BYTES", "65536"))
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(tail), container],
                capture_output=True,
                timeout=10,
            )
            # docker logs writes to stderr by default; combine both streams
            raw = (result.stdout + result.stderr)[:max_output_bytes]
            output = raw.decode("utf-8", errors="replace")
            return Redactor().redact(output) if output.strip() else "(no log output)"
        except subprocess.TimeoutExpired:
            return "DOCKER_LOGS_TIMEOUT: docker logs timed out"
        except FileNotFoundError:
            return "DOCKER_LOGS_ERROR: docker binary not found on PATH"
        except Exception as exc:
            return f"DOCKER_LOGS_ERROR: {exc}"

    def run_checked(self, container: str, command: str) -> str:
        """Validate via allowlist, execute, and redact output.

        Returns the redacted output, or a BLOCKED/error string.
        This is the method the log agent calls directly.
        """
        allowed, reason = CommandAllowlist.is_allowed(command)
        if not allowed:
            return f"BLOCKED: {reason}"
        try:
            raw = self.execute(container, command)
            return Redactor().redact(raw)
        except DockerExecutionError as exc:
            return f"DOCKER_ERROR: {exc}"
