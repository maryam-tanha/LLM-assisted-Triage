import os

import paramiko

from framework.models import SSHConfig


class SSHExecutionError(Exception):
    def __init__(self, message: str, command: str, host: str) -> None:
        super().__init__(message)
        self.command = command
        self.host = host


class SSHExecutor:
    def __init__(self) -> None:
        # Pool keyed by (host, port, username) to reuse connections across commands
        self._pool: dict[tuple[str, int, str], paramiko.SSHClient] = {}

    def execute(self, ssh_config: SSHConfig, command: str) -> str:
        """
        Execute a command on the remote host and return stdout as a string.
        Output is capped at MAX_OUTPUT_BYTES to prevent memory exhaustion.
        Raises SSHExecutionError on paramiko failures.
        """
        max_output_bytes = int(os.environ.get("MAX_OUTPUT_BYTES", "65536"))
        stderr_max_bytes = int(os.environ.get("STDERR_MAX_BYTES", "4096"))
        try:
            client = self._get_or_create_client(ssh_config)
            stdin, stdout, stderr = client.exec_command(
                command, timeout=ssh_config.timeout
            )
            out = stdout.read(max_output_bytes).decode("utf-8", errors="replace")
            err = stderr.read(stderr_max_bytes).decode("utf-8", errors="replace")
            exit_code = stdout.channel.recv_exit_status()
            if exit_code != 0 and not out.strip():
                return f"STDERR: {err.strip()}"
            return out
        except EOFError:
            # Stale pooled connection — evict and retry once with a fresh client
            key = (ssh_config.host, ssh_config.port, ssh_config.username)
            self._pool.pop(key, None)
            try:
                client = self._get_or_create_client(ssh_config)
                stdin, stdout, stderr = client.exec_command(
                    command, timeout=ssh_config.timeout
                )
                out = stdout.read(max_output_bytes).decode("utf-8", errors="replace")
                err = stderr.read(stderr_max_bytes).decode("utf-8", errors="replace")
                exit_code = stdout.channel.recv_exit_status()
                if exit_code != 0 and not out.strip():
                    return f"STDERR: {err.strip()}"
                return out
            except (paramiko.SSHException, OSError, EOFError) as exc:
                raise SSHExecutionError(str(exc), command, ssh_config.host) from exc
        except (paramiko.SSHException, OSError) as exc:
            raise SSHExecutionError(str(exc), command, ssh_config.host) from exc

    def close_all(self) -> None:
        """Close all pooled SSH connections."""
        for client in self._pool.values():
            try:
                client.close()
            except Exception:
                pass
        self._pool.clear()

    def _get_or_create_client(self, ssh_config: SSHConfig) -> paramiko.SSHClient:
        key = (ssh_config.host, ssh_config.port, ssh_config.username)

        existing = self._pool.get(key)
        if existing is not None:
            transport = existing.get_transport()
            if transport is not None and transport.is_active():
                return existing

        client = paramiko.SSHClient()
        # AutoAddPolicy is appropriate for trusted internal infrastructure.
        # For production hardening, switch to RejectPolicy with a known_hosts file.
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs: dict = {
            "hostname": ssh_config.host,
            "port": ssh_config.port,
            "username": ssh_config.username,
            "timeout": ssh_config.timeout,
        }
        if ssh_config.key_path is not None:
            # Use key_filename so paramiko auto-detects key type (RSA, Ed25519, ECDSA, etc.)
            connect_kwargs["key_filename"] = ssh_config.key_path
        else:
            connect_kwargs["password"] = ssh_config.password

        client.connect(**connect_kwargs)
        self._pool[key] = client
        return client
