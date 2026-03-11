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

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Register specialists before building the graph
import agents.specialists.log_agent           # noqa: F401
import agents.specialists.runtime_status_agent  # noqa: F401

from config.loader import load_config
from graph.builder import build_graph

_CONFIG_PATH = Path(__file__).parent / "configs" / "voting_app.yaml"
_config = load_config(_CONFIG_PATH)

# LangGraph Studio discovers this variable via langgraph.json
graph = build_graph(_config)
