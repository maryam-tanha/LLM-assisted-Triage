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


class ProductConfig(BaseModel):
    product: str
    access_method: str                  # "docker_exec" | "ssh"
    services: list[ServiceConfig]

    def get_service(self, name: str) -> ServiceConfig | None:
        for s in self.services:
            if s.service_name == name:
                return s
        return None


def load_config(yaml_path: str | Path) -> ProductConfig:
    """Load and validate a product service configuration YAML."""
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ProductConfig(**raw)
