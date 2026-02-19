from pathlib import Path

import yaml
from pydantic import BaseModel


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

    def parent_llm_description(self) -> str:
        """Full text shown to the parent LLM for this agent."""
        parts = [self.description.strip()]
        if self.when_to_use.strip():
            parts.append(f"When to use:\n{self.when_to_use.strip()}")
        if self.do_not_use.strip():
            parts.append(f"Do not use when:\n{self.do_not_use.strip()}")
        return "\n\n".join(parts)


class ProductConfig(BaseModel):
    product: str
    access_method: str                  # "docker_exec" | "ssh"
    services: list[ServiceConfig]
    agents: list[AgentConfig] = []      # loaded from per-agent YAML files

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


def load_config(yaml_path: str | Path) -> ProductConfig:
    """Load and validate a product service configuration YAML."""
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    # Load agent YAML files referenced in the main config
    agent_configs: list[AgentConfig] = []
    for rel_path in raw.pop("agents", []):
        agent_path = path.parent / rel_path
        if not agent_path.exists():
            raise FileNotFoundError(f"Agent config not found: {agent_path}")
        agent_raw = yaml.safe_load(agent_path.read_text(encoding="utf-8"))
        agent_configs.append(AgentConfig(**agent_raw))
    raw["agents"] = agent_configs

    return ProductConfig(**raw)
