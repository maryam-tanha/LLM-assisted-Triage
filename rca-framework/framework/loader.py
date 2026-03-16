from pathlib import Path

import yaml

from framework.models import (
    AgentConfig,
    ParentConfig,
    ProductConfig,
    SynthesisConfig,
)


def load_profile(profile_dir: str | Path) -> ProductConfig:
    """Load a complete profile from a directory.

    Expects the directory to contain:
      profile.yaml      — product + services
      parent.yaml       — parent agent system prompt
      synthesis.yaml    — synthesis agent system prompt
      agents/           — one YAML per specialist agent (config + system_prompt)
    """
    root = Path(profile_dir)
    profile_yaml = root / "profile.yaml"
    if not profile_yaml.exists():
        raise FileNotFoundError(f"Profile not found: {profile_yaml}")

    raw = yaml.safe_load(profile_yaml.read_text(encoding="utf-8"))

    # Auto-discover specialist agent YAMLs from agents/ subdirectory
    agent_configs: list[AgentConfig] = []
    agents_dir = root / "agents"
    if agents_dir.exists():
        for agent_file in sorted(agents_dir.glob("*.yaml")):
            agent_raw = yaml.safe_load(agent_file.read_text(encoding="utf-8"))
            agent_configs.append(AgentConfig(**agent_raw))

    # Load framework agent prompts
    parent_prompt = ""
    parent_yaml = root / "parent.yaml"
    if parent_yaml.exists():
        parent_raw = yaml.safe_load(parent_yaml.read_text(encoding="utf-8"))
        parent_prompt = ParentConfig(**parent_raw).get_system_prompt()

    synthesis_prompt = ""
    synthesis_yaml = root / "synthesis.yaml"
    if synthesis_yaml.exists():
        synthesis_raw = yaml.safe_load(synthesis_yaml.read_text(encoding="utf-8"))
        synthesis_prompt = SynthesisConfig(**synthesis_raw).get_system_prompt()

    raw["agents"] = agent_configs
    raw["parent_prompt"] = parent_prompt
    raw["synthesis_prompt"] = synthesis_prompt

    config = ProductConfig(**raw)
    config = config.model_copy(update={"profile_path": root})
    return config


def list_profiles(profiles_dir: str | Path) -> dict[str, Path]:
    """Return {profile_name: profile_dir} for all valid profiles found."""
    root = Path(profiles_dir)
    if not root.exists():
        return {}
    return {
        p.name: p
        for p in sorted(root.iterdir())
        if p.is_dir() and (p / "profile.yaml").exists()
    }
