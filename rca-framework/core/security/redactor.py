import re

# Order matters: more specific patterns run before the broad base64 catch-all.
_REDACTION_PATTERNS: list[tuple[re.Pattern, str]] = [
    # AWS access key IDs
    (re.compile(r"(?i)(AKIA|ASIA|AROA)[A-Z0-9]{16}"), "[REDACTED_AWS_KEY]"),
    # PEM private key blocks (multiline)
    (
        re.compile(
            r"-----BEGIN [A-Z ]+PRIVATE KEY-----.*?-----END [A-Z ]+PRIVATE KEY-----",
            re.DOTALL,
        ),
        "[REDACTED_PRIVATE_KEY]",
    ),
    # Bearer tokens
    (
        re.compile(r"(?i)(bearer\s+)[A-Za-z0-9\-_.]{20,}"),
        r"\1[REDACTED_TOKEN]",
    ),
    # api_key= / api-key=
    (
        re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)[^\s,'\"]+"),
        r"\1[REDACTED_KEY]",
    ),
    # token=
    (
        re.compile(r"(?i)(token\s*[=:]\s*)[^\s,'\"]+"),
        r"\1[REDACTED_TOKEN]",
    ),
    # password=
    (
        re.compile(r"(?i)(password\s*[=:]\s*)[^\s,'\"]+"),
        r"\1[REDACTED_PASSWORD]",
    ),
    # secret=
    (
        re.compile(r"(?i)(secret\s*[=:]\s*)[^\s,'\"]+"),
        r"\1[REDACTED_SECRET]",
    ),
    # Email addresses
    (
        re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
        "[REDACTED_EMAIL]",
    ),
    # IPv4 addresses — partial redaction keeps first octet for network context
    (
        re.compile(r"\b(\d{1,3})\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
        r"\1.x.x.x",
    ),
    # Long base64-like strings — broad catch-all, placed last
    (
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        "[REDACTED_BASE64]",
    ),
]


class Redactor:
    def __init__(
        self,
        extra_patterns: list[tuple[re.Pattern, str]] | None = None,
    ) -> None:
        self._patterns = _REDACTION_PATTERNS.copy()
        if extra_patterns:
            self._patterns.extend(extra_patterns)

    def redact(self, text: str) -> str:
        """Apply all redaction patterns in order and return the redacted string."""
        for pattern, replacement in self._patterns:
            text = pattern.sub(replacement, text)
        return text
