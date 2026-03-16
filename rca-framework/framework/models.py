from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SSHConfig(BaseModel):
    host: str
    port: int = 22
    username: str
    key_path: str | None = None
    # repr=False prevents password from appearing in logs or stack traces
    password: str | None = Field(default=None, repr=False)
    timeout: int = 30

    model_config = ConfigDict(frozen=True)

    @field_validator("host", "username")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v

    @field_validator("port")
    @classmethod
    def valid_port(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError("port must be between 1 and 65535")
        return v

    @field_validator("timeout")
    @classmethod
    def positive_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("timeout must be positive")
        return v

    @model_validator(mode="after")
    def require_auth(self) -> "SSHConfig":
        if self.key_path is None and self.password is None:
            raise ValueError("Either key_path or password must be provided")
        return self


class KnownFailure(BaseModel):
    pattern: str
    likely_cause: str


class ServiceConfig(BaseModel):
    service_name: str
    description: str
    container: str                      # docker exec target
    expected_behavior: str
    known_failures: list[KnownFailure]
    context_commands: list[str]
    log_hints: list[str] = []           # investigation hints injected into the LLM prompt
    additional_info: dict = {}


class AgentConfig(BaseModel):
    agent_type: str
    description: str
    when_to_use: str = ""
    do_not_use: str = ""
    system_prompt: str = ""             # loaded from YAML; replaces .txt file lookup

    def parent_llm_description(self) -> str:
        """Full text shown to the parent LLM for this agent."""
        parts = [self.description.strip()]
        if self.when_to_use.strip():
            parts.append(f"When to use:\n{self.when_to_use.strip()}")
        if self.do_not_use.strip():
            parts.append(f"Do not use when:\n{self.do_not_use.strip()}")
        return "\n\n".join(parts)

    def get_system_prompt(self) -> str:
        if not self.system_prompt.strip():
            raise ValueError(
                f"Agent '{self.agent_type}' has no system_prompt defined in its YAML."
            )
        return self.system_prompt.strip()


class ParentConfig(BaseModel):
    """Loaded from profiles/<name>/parent.yaml."""
    role: str = "parent"
    system_prompt: str

    def get_system_prompt(self) -> str:
        return self.system_prompt.strip()


class SynthesisConfig(BaseModel):
    """Loaded from profiles/<name>/synthesis.yaml."""
    role: str = "synthesis"
    system_prompt: str

    def get_system_prompt(self) -> str:
        return self.system_prompt.strip()


class ProductConfig(BaseModel):
    profile_name: str = ""              # from profile.yaml profile_name key
    product: str
    access_method: str                  # "docker_exec" | "ssh"
    services: list[ServiceConfig]
    agents: list[AgentConfig] = []      # auto-discovered from agents/ subdirectory
    parent_prompt: str = ""             # loaded from parent.yaml
    synthesis_prompt: str = ""          # loaded from synthesis.yaml
    profile_path: Path | None = Field(default=None, exclude=True)  # runtime path

    def get_service(self, name: str) -> ServiceConfig | None:
        for s in self.services:
            if s.service_name == name:
                return s
        return None

    def get_agent(self, agent_type: str) -> AgentConfig | None:
        for a in self.agents:
            if a.agent_type == agent_type:
                return a
        return None
