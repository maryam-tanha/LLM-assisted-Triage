"""
langgraph_app.py — LangGraph Studio / CLI entry point
======================================================
Exposes `graph` as a module-level variable so LangGraph Studio (web) can
discover and visualise it.

Usage (LangGraph Studio via CLI):
    pip install "langgraph-cli[inmem]"
    cd rca-framework
    langgraph dev
    # then open: https://smith.langchain.com/studio/?baseUrl=http://localhost:2024

The initial state can be sent from the Studio UI as JSON.
"""

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Auto-discover and register all specialist modules
_spec_dir = Path(__file__).parent / "core" / "agents" / "specialists"
for _f in sorted(_spec_dir.glob("*_agent.py")):
    if _f.stem != "base_specialist":
        importlib.import_module(f"core.agents.specialists.{_f.stem}")

from framework.loader import load_profile
from core.graph.builder import build_graph

_PROFILE_DIR = Path(__file__).parent / "profiles" / "voting_app"
_config = load_profile(_PROFILE_DIR)

# LangGraph Studio discovers this variable via langgraph.json
graph = build_graph(_config)
