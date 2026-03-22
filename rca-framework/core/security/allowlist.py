import re

# Blocked patterns are checked against the full command string (deny-first).
# Even an allowed prefix like "journalctl" must be rejected if it contains "| bash".
BLOCKED_PATTERNS: list[re.Pattern] = [
    re.compile(r"rm\s"),
    re.compile(r">\s"),           # output redirection
    re.compile(r">>"),            # append redirection
    re.compile(r"\|\s*bash"),
    re.compile(r"\|\s*sh\b"),
    # re.compile(r"sudo\s"),  # Relaxed for SSH docker commands
    re.compile(r"chmod\s"),
    re.compile(r"chown\s"),
    re.compile(r"\bcurl\b"),
    re.compile(r"\bwget\b"),
    re.compile(r"\bnc\b"),
    re.compile(r"\bnetcat\b"),
    re.compile(r"eval\s"),
    # re.compile(r"exec\s"),  # Relaxed for docker exec
    re.compile(r"\bdd\b"),
    re.compile(r"mkfs\b"),
    re.compile(r">/dev/"),
]

# Allowed patterns are matched at the start of the command (after block check passes).
ALLOWED_PATTERNS: list[re.Pattern] = [
    re.compile(r"^docker\b"),
    re.compile(r"^sudo\s+docker\b"),
    re.compile(r"^sudo\s+-n\s+docker\b"),
    re.compile(r"^find\b"),
    re.compile(r"^journalctl\b"),
    re.compile(r"^tail\b"),
    re.compile(r"^dmesg\b"),
    re.compile(r"^cat /var/log/"),
    re.compile(r"^cat /proc/"),
    re.compile(r"^cat /usr/local/app/"),
    re.compile(r"^cat /app/"),
    re.compile(r"^grep\b"),
    re.compile(r"^wc\b"),
    re.compile(r"^ls\b"),
    re.compile(r"^df\b"),
    re.compile(r"^free\b"),
    re.compile(r"^ps\b"),
    re.compile(r"^top -bn1\b"),
    re.compile(r"^uptime\b"),
    re.compile(r"^hostname\b"),
    re.compile(r"^date\b"),
    re.compile(r"^uname\b"),
    re.compile(r"^redis-cli\b"),
    re.compile(r"^psql\b"),
    re.compile(r"^node\b"),
    re.compile(r"^python\b"),
    # Network inspection (read-only)
    re.compile(r"^ss\b"),
    re.compile(r"^ip\s"),
    re.compile(r"^cat /etc/"),
    # cgroup / sysfs (read-only)
    re.compile(r"^cat /sys/"),
]


class CommandAllowlist:
    @staticmethod
    def is_allowed(command: str) -> tuple[bool, str]:
        """
        Returns (True, "") if the command is allowed.
        Returns (False, reason) if the command is blocked or not in the allowlist.

        Evaluation order:
        1. Empty command check
        2. Blocked patterns (search full string) — deny-first
        3. Allowed patterns (match at start)
        4. Fallback: not in allowlist
        """
        command = command.strip()

        if not command:
            return False, "Empty command"

        for pattern in BLOCKED_PATTERNS:
            if pattern.search(command):
                return False, f"Blocked pattern: {pattern.pattern}"

        for pattern in ALLOWED_PATTERNS:
            if pattern.match(command):
                return True, ""

        return False, "Command not in allowlist"
