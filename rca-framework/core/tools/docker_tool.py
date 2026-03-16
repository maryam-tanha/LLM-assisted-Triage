import os
import subprocess

from core.security.allowlist import CommandAllowlist
from core.security.redactor import Redactor


class DockerExecutionError(Exception):
    def __init__(self, message: str, command: str, container: str) -> None:
        super().__init__(message)
        self.command = command
        self.container = container


def _env_int(name: str, default: int) -> int:
    """Read an integer from the environment with a fallback default."""
    return int(os.environ.get(name, str(default)))


class DockerExecutor:
    """Runs commands inside a local Docker container via `docker exec`.

    Used instead of SSHExecutor when access_method is docker_exec.
    The allowlist and redactor are applied the same way as in the SSH path.
    """

    def __init__(self) -> None:
        self._redactor = Redactor()

    def execute(self, container: str, command: str) -> str:
        """Run `docker exec <container> sh -c <command>` and return stdout.

        Raises DockerExecutionError if the container is unreachable or the
        command exits with a non-zero status and produced no stdout.
        """
        max_output_bytes = _env_int("MAX_OUTPUT_BYTES", 65536)
        stderr_max_bytes = _env_int("STDERR_MAX_BYTES", 4096)
        timeout = _env_int("DOCKER_EXEC_TIMEOUT", 30)
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
        container -- /proc/1/fd/1 blocks forever when read from inside the container.
        Returns the last DOCKER_LOGS_TAIL lines, redacted and byte-capped.
        """
        tail = _env_int("DOCKER_LOGS_TAIL", 200)
        max_output_bytes = _env_int("MAX_OUTPUT_BYTES", 65536)
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(tail), container],
                capture_output=True,
                timeout=10,
            )
            # docker logs writes to stderr by default; combine both streams
            raw = (result.stdout + result.stderr)[:max_output_bytes]
            output = raw.decode("utf-8", errors="replace")
            return self._redactor.redact(output) if output.strip() else "(no log output)"
        except subprocess.TimeoutExpired:
            return "DOCKER_LOGS_TIMEOUT: docker logs timed out"
        except FileNotFoundError:
            return "DOCKER_LOGS_ERROR: docker binary not found on PATH"
        except Exception as exc:
            return f"DOCKER_LOGS_ERROR: {exc}"

    def get_inspect(self, container: str) -> str:
        """Run `docker inspect <container>` on the host and return redacted JSON.

        Used by DockerSpecsAgent to retrieve full container configuration
        (resource limits, restart policy, mounts, port bindings, image, env).
        Not an interactive LLM tool — called once during context gathering.
        """
        max_output_bytes = _env_int("MAX_OUTPUT_BYTES", 65536)
        try:
            result = subprocess.run(
                ["docker", "inspect", container],
                capture_output=True,
                timeout=10,
            )
            raw = result.stdout[:max_output_bytes].decode("utf-8", errors="replace")
            return self._redactor.redact(raw) if raw.strip() else "(no inspect output)"
        except subprocess.TimeoutExpired:
            return "(unavailable: docker inspect timed out)"
        except FileNotFoundError:
            return "(unavailable: docker binary not found)"
        except Exception as exc:
            return f"(unavailable: {exc})"

    def get_stats_snapshot(self, container: str) -> str:
        """Run `docker stats --no-stream` on the host for a live resource snapshot.

        Returns a table row with CPU%, memory usage/limit, net I/O, block I/O, PIDs.
        """
        try:
            result = subprocess.run(
                [
                    "docker", "stats", container, "--no-stream",
                    "--format",
                    "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}\t{{.PIDs}}",
                ],
                capture_output=True,
                timeout=15,
            )
            raw = result.stdout.decode("utf-8", errors="replace")
            return self._redactor.redact(raw) if raw.strip() else "(no stats output)"
        except subprocess.TimeoutExpired:
            return "(unavailable: docker stats timed out)"
        except FileNotFoundError:
            return "(unavailable: docker binary not found)"
        except Exception as exc:
            return f"(unavailable: {exc})"

    def get_events(self, container: str, since: str = "24h") -> str:
        """Fetch recent Docker daemon events for the container from the host.

        Covers OOM kills, restarts, health check failures, and start/stop events.
        """
        try:
            result = subprocess.run(
                [
                    "docker", "events",
                    "--filter", f"container={container}",
                    "--since", since,
                    "--until", "now",
                    "--format", "{{.Time}} {{.Type}} {{.Action}}",
                ],
                capture_output=True,
                timeout=10,
            )
            raw = result.stdout.decode("utf-8", errors="replace")
            return raw.strip() if raw.strip() else "(no events in last 24h)"
        except subprocess.TimeoutExpired:
            return "(unavailable: docker events timed out)"
        except FileNotFoundError:
            return "(unavailable: docker binary not found)"
        except Exception as exc:
            return f"(unavailable: {exc})"

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
            return self._redactor.redact(raw)
        except DockerExecutionError as exc:
            return f"DOCKER_ERROR: {exc}"
