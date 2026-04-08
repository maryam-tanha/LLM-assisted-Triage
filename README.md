# LLM-Assisted Triage

Multi-agent Root Cause Analysis (RCA) framework for automated incident investigation in cloud/microservice environments. Also an active research project with an accompanying IEEE conference paper.

## Project Structure

```
v1/
├── rca-framework/              # Core RCA agent framework
│   ├── core/
│   │   ├── agents/             # Parent, synthesis, and specialist agents
│   │   │   └── specialists/    # log_agent, runtime_status_agent, yaml_specialist, base
│   │   ├── graph/              # LangGraph builder, state, registry
│   │   ├── tools/              # docker_tool.py, ssh_tool.py
│   │   └── security/           # allowlist.py, redactor.py
│   ├── framework/              # Shared models, loader, LLM client, usage tracker
│   ├── profiles/               # Per-product config directories
│   │   ├── voting_app/         # profile.yaml, parent.yaml, synthesis.yaml, agents/
│   │   └── mail_app/           # profile.yaml, parent.yaml, synthesis.yaml, agents/
│   ├── pages/                  # Streamlit multi-page UI components
│   ├── demo.py                 # CLI entry point
│   ├── ui.py                   # Streamlit web UI entry point
│   ├── langgraph_app.py        # LangGraph Studio entry point
│   └── requirements.txt
├── LLM_assisted_Triage/        # Research paper (LaTeX, IEEEtran)
│   ├── main.tex
│   ├── fig_architecture.tex
│   ├── references.bib
│   └── PAPER_UPDATE_PLAN.md
├── demo-targets/
│   └── mail-app/               # Docker Compose mail server (AWS EC2)
├── AGENTS.md                   # Task tracker — read this first
├── Literature_Review_Summary.md
└── Summary-SP2026-Kalhar.md    # Architecture design doc + paper summaries
```

## Quick Start

### Prerequisites
- Python 3.11+
- Docker (for voting_app demo)
- OpenRouter API key

### Installation

```bash
cd rca-framework
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### Run CLI Demo

```bash
python demo.py --profile voting_app --incident "Redis is down"
# Target a specific service manually:
python demo.py --profile voting_app --incident "Redis is down" --service redis
```

### Run Web UI

```bash
streamlit run ui.py
```

### Environment Variables

```bash
LLM_MODEL=openai/gpt-4.1       # Model to use (via OpenRouter)
MAX_ITERATIONS=10               # Max tool calls per specialist agent
MAX_CONCURRENCY=10              # Parallel specialist nodes
DOCKER_EXEC_TIMEOUT=30         # Command timeout (seconds)
DOCKER_LOGS_TAIL=200           # Lines of docker logs to fetch
LOG_COMMAND_OUTPUTS=false      # Log all command outputs to rca_commands.log
```

## Architecture

### Graph Flow

```
START → parent_agent → [Send() fan-out] → specialist nodes (parallel)
                                                    ↓
                                              synthesis
                                                    ↓
                       parent_agent ←─────────────┘   (loop, max N cycles)
                            ↓
                          END  →  Final RCA Report
```

- **Parent Agent** (`core/agents/parent_agent.py`): LLM orchestrator with two tools: `create_subtasks` (fans out to specialists) and `write_rca_conclusion` (ends the loop). Hard-wires conclusion at `MAX_CYCLES` (default 3).
- **Specialist Agents** (`core/agents/specialists/`): ReAct agents with a single `run_command` tool. Narrow domain scope. Registered via `core/graph/registry.py`.
- **Synthesis Agent** (`core/agents/synthesis_agent.py`): Tool-free, reads new `SpecialistFinding` objects via `findings_offset`, produces `CycleSummary` for the parent's next cycle.
- **LangGraph State** (`core/graph/state.py`): `GraphState` TypedDict with `Annotated[list, operator.add]` reducers for parallel fan-in merge.

## Profile System

Each deployment target lives in `profiles/<name>/`:

```
profiles/voting_app/
  profile.yaml        # product metadata, access_method, services list
  parent.yaml         # parent agent system prompt
  synthesis.yaml      # synthesis agent system prompt
  agents/
    log.yaml          # log specialist config
    runtime_status.yaml
    network.yaml
    docker_specs.yaml
```

`profile.yaml` service entries define `expected_behavior`, `known_failures`, `context_commands`, and `log_hints`. Agent YAML files define `agent_type`, `system_prompt`, `when_to_use`, `do_not_use`, `context_commands`, and `gather_docker_host_context`.

## Adding a New Specialist

**Option A — Python (full control):**
1. Create `core/agents/specialists/my_agent.py` extending `BaseSpecialist`
2. Call `register(SpecialistRegistration(...))` at the bottom of the file
3. Import it in `demo.py` — it auto-registers into the graph

**Option B — YAML only (no Python required):**
1. Create `profiles/<name>/agents/my_agent.yaml` with `agent_type`, `system_prompt`, `when_to_use`, `do_not_use`
2. The `YAMLSpecialist` bridge class picks it up at startup automatically

## Security

- **Command Allowlist** (`core/security/allowlist.py`): Deny-first. Blocks `rm`, `chmod`, `curl`, `wget`, `nc`, shell redirects, `| bash`. Only explicitly allowed prefixes (log readers, system status utilities, service CLIs) proceed.
- **Output Redactor** (`core/security/redactor.py`): Strips AWS keys, PEM blocks, bearer tokens, `api_key=`/`password=` assignments, email addresses, full IPv4 addresses, long base64 strings. Runs on every execution path before output reaches the LLM.

## Research Paper

See `LLM_assisted_Triage/` for the IEEE conference paper draft.
Current state: Introduction, Related Work, and full Methodology section complete. Abstract and keywords written. Experiments and Conclusion sections pending experiment runs.

Track all task status in `AGENTS.md`.

## License

MIT
