# LLM-Assisted Triage: A Multi-Agent Framework for Automated Incident Root Cause Analysis

> Khoury College of Computer Sciences, Northeastern University — Spring 2026 Apprenticeship Research Project

**Author:** Kalhar Pandya | **Advisor:** Dr. Maryam Tanha | **Consultant:** Dr. Dawood Sajjadi, Director of SRE, Fortinet

Multi-agent RCA framework that uses LLM-powered specialist agents to autonomously diagnose microservice faults by correlating container logs, process states, and configurations in parallel — reducing manual SRE triage and cutting Mean Time to Resolution.

## Project Structure

```
v1/
├── rca-framework/              # Core RCA agent framework
│   ├── core/
│   │   ├── agents/             # Parent, synthesis, and specialist agents
│   │   │   └── specialists/    # Base class, yaml_specialist bridge
│   │   ├── graph/              # LangGraph builder, state, registry
│   │   ├── tools/              # docker_tool.py, ssh_tool.py
│   │   └── security/           # allowlist.py, redactor.py
│   ├── framework/              # Models, profile loader, LLM client, usage tracker
│   ├── profiles/               # Per-product config directories
│   │   ├── voting_app/         # 5 services, Docker access
│   │   └── mail_app/           # 4 services, SSH access (AWS EC2)
│   ├── pages/                  # Streamlit multi-page UI (Profile Manager)
│   ├── demo.py                 # CLI entry point
│   ├── ui.py                   # Streamlit web UI entry point
│   └── langgraph_app.py        # LangGraph Studio entry point
├── LLM_assisted_Triage/        # Research paper (LaTeX, IEEEtran)
├── Posters/                    # Conference poster (PDF)
├── demo-targets/
│   └── mail-app/               # Docker Compose mail server (AWS EC2)
├── docs/
│   ├── research-notes/         # Literature review + architecture notes
│   ├── papers/                 # Reference papers (20 PDFs)
│   └── papers_text/            # Plain-text extractions of reference papers
└── AGENTS.md                   # Task tracker
```

## Quick Start

### Prerequisites

- Python 3.11+
- An [OpenRouter](https://openrouter.ai/keys) API key
- Docker on the local machine (for `docker_exec` access method), **or** SSH access to a remote host running Docker (for `ssh` access method)

### Installation

```bash
cd rca-framework
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### Run an Investigation (CLI)

```bash
# Default profile (voting_app, local Docker):
python demo.py --incident "Redis is not responding, votes are not being recorded"

# Specify a profile:
python demo.py --profile profiles/mail_app --incident "Users cannot send email"

# Target a single service (skips LLM planning, goes straight to specialists):
python demo.py --profile profiles/mail_app --incident "IMAP login failures" --service mailserver
```

The CLI prints the full RCA report to stdout, including each cycle's findings, synthesis, and the final conclusion. Token usage and cost are shown at the end.

### Run the Web UI

```bash
streamlit run ui.py
```

The UI has three panels:

| Sidebar | Center | Right |
|---------|--------|-------|
| Profile selector, incident description, max cycles slider, run/reset buttons, live metrics | Agent graph topology diagram with color-coded node status badges | Tabbed panel: Timeline (per-cycle findings), State (config snapshot), RCA Report (final output) |

The **Profile Manager** page (accessible from the sidebar) lets you create and edit profiles, services, and agent configs through a form — no YAML editing required.

### Environment Variables

All settings live in `rca-framework/.env` (copy from `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | — | Required. Get one at [openrouter.ai/keys](https://openrouter.ai/keys) |
| `LLM_MODEL` | `openai/gpt-4.1` | Model to use via OpenRouter |
| `MAX_ITERATIONS` | `10` | Max tool calls per specialist per subtask |
| `MAX_CONCURRENCY` | `10` | Parallel specialist thread pool size |
| `MAX_OUTPUT_BYTES` | `65536` | Max stdout captured per command |
| `DOCKER_EXEC_TIMEOUT` | `10` | Command timeout in seconds |
| `DOCKER_LOGS_TAIL` | `200` | Lines of container logs fetched as initial context |
| `LOG_COMMAND_OUTPUTS` | `false` | Write all command I/O to `rca_commands.log` |

---

## Architecture

### Investigation Flow

```
START → Parent Agent → [Send() fan-out] → Specialist Agents (parallel)
                                                    ↓
                                              Synthesis Agent
                                                    ↓
                       Parent Agent ←──────────────┘  (loop up to N cycles)
                            ↓
                     Final RCA Report
```

1. **Parent Agent** receives the incident and product config. It calls `create_subtasks` to assign specific investigation tasks to specialists, specifying which service and agent type to use.
2. **Specialist Agents** run in parallel via LangGraph `Send()`. Each gets SSH or Docker access to its target container. They execute read-only commands (`run_command` tool) and produce a structured finding with confidence score and evidence.
3. **Synthesis Agent** correlates findings from all specialists in that cycle, identifies gaps, and recommends next steps.
4. **Parent Agent** reviews the synthesis. It either starts another cycle with new subtasks or calls `write_rca_conclusion` to produce the final report.

The loop runs up to `MAX_CYCLES` (default 3). If the parent hasn't concluded by then, it's forced to write a conclusion with whatever evidence it has.

### Key Files

| File | Role |
|------|------|
| `core/agents/parent_agent.py` | LLM orchestrator, two tools: `create_subtasks`, `write_rca_conclusion` |
| `core/agents/specialists/base_specialist.py` | Abstract base for all specialists (ReAct loop with `run_command`) |
| `core/agents/specialists/yaml_specialist.py` | Bridge class that turns YAML agent configs into specialist instances |
| `core/agents/synthesis_agent.py` | Tool-free agent that correlates per-cycle findings |
| `core/graph/builder.py` | Builds the LangGraph graph dynamically from the specialist registry |
| `core/graph/state.py` | `GraphState` TypedDict with parallel merge reducers |
| `core/tools/ssh_tool.py` | Pooled SSH command execution (paramiko) |
| `core/tools/docker_tool.py` | Local `docker exec` command execution |
| `core/security/allowlist.py` | Deny-first command filter |
| `core/security/redactor.py` | Strips secrets from all command output before it reaches the LLM |

---

## Creating a Profile

A profile defines a deployment target — the services to investigate, how to reach them, and which specialist agents to use. Each profile is a directory under `profiles/`.

### Step 1: Create the Profile Directory

```
profiles/my_app/
  profile.yaml
  parent.yaml
  synthesis.yaml
  agents/
    log_agent.yaml
    runtime_status_agent.yaml
```

### Step 2: Write `profile.yaml`

This defines the product, access method, and every service the agents can investigate.

**For local Docker access:**

```yaml
profile_name: my_app
product: MyApp
access_method: docker_exec

services:
  - service_name: api
    description: "Node.js API server handling all REST endpoints"
    container: myapp-api-1          # exact container name from docker ps
    host_port: 3000
    internal_port: 3000
    expected_behavior: |
      Listens on port 3000. Returns 200 on GET /health.
      Connects to PostgreSQL on db:5432.
    known_failures:
      - pattern: "ECONNREFUSED"
        likely_cause: "Database is down or unreachable"
      - pattern: "ENOMEM"
        likely_cause: "Container hit memory limit"
    context_commands:
      - "node --version"
      - "cat /app/package.json | grep version"
      - "ps aux"
      - "df -h"
      - "free -m"
    log_hints:
      - "App logs go to stdout — use docker logs myapp-api-1"
      - "Check for unhandled promise rejections in recent output"
```

**For SSH access (remote Docker host):**

```yaml
profile_name: my_app
product: MyApp
access_method: ssh
ssh_host: 10.0.1.50
ssh_user: ubuntu
ssh_key_path: /path/to/your/key.pem   # absolute path to SSH private key

services:
  - service_name: api
    container: myapp-api-1
    # ... same service fields as above
    # context_commands should prefix with: sudo docker exec <container>
    context_commands:
      - "sudo docker exec myapp-api-1 node --version"
      - "sudo docker exec myapp-api-1 ps aux"
      - "sudo docker exec myapp-api-1 df -h"
```

**Key fields per service:**

| Field | Required | Purpose |
|-------|----------|---------|
| `service_name` | Yes | Identifier used by the parent agent when assigning subtasks |
| `description` | Yes | Tells the LLM what this service does |
| `container` | Yes | Exact Docker container name for command execution |
| `expected_behavior` | Recommended | What "healthy" looks like — the LLM compares against this |
| `known_failures` | Recommended | Pattern/cause pairs the LLM checks first (speeds up diagnosis) |
| `context_commands` | Recommended | Commands run automatically at the start of each specialist invocation |
| `log_hints` | Recommended | Tells the specialist where and how to find logs for this service |

### Step 3: Write `parent.yaml` and `synthesis.yaml`

You can copy these from an existing profile (`voting_app` or `mail_app`) — they contain the system prompts for the parent and synthesis agents. Customize if your domain needs specific investigation strategies.

```yaml
# parent.yaml
role: parent
system_prompt: |
  You are the Parent Agent in an automated RCA framework.
  ... (see profiles/voting_app/parent.yaml for full example)
```

```yaml
# synthesis.yaml
role: synthesis
system_prompt: |
  You are the Synthesis Agent in an automated RCA framework.
  ... (see profiles/voting_app/synthesis.yaml for full example)
```

### Step 4: Create Agent YAML Files

Each file in `agents/` defines a specialist. The `YAMLSpecialist` bridge class auto-discovers these at startup — no Python code needed.

```yaml
# agents/log_agent.yaml
agent_type: log
description: "Investigates container logs for errors, warnings, and anomalies"
when_to_use: |
  - You need to see application stdout/stderr or error messages
  - The incident involves connectivity errors or timeouts
do_not_use: |
  - You only need resource metrics (use runtime_status instead)

system_prompt: |
  You are a Log Specialist agent. You have one tool: run_command.
  ... (see profiles/mail_app/agents/log_agent.yaml for full example)
```

**Agent YAML fields:**

| Field | Required | Purpose |
|-------|----------|---------|
| `agent_type` | Yes | Identifier used when the parent assigns subtasks (e.g., `log`, `runtime_status`) |
| `description` | Yes | Shown to the parent agent so it knows what this specialist can do |
| `system_prompt` | Yes | The specialist's full system prompt (investigation instructions, output format) |
| `when_to_use` | Recommended | Guides the parent on when to dispatch this agent |
| `do_not_use` | Recommended | Prevents the parent from assigning irrelevant work |

### Step 5: Run It

```bash
python demo.py --profile profiles/my_app --incident "API returning 500 errors"
```

---

## Understanding the Execution

### CLI Output

The CLI (`demo.py`) prints each phase as it happens:

1. **Cycle header** — `=== Cycle 1 ===`
2. **Parent decision** — which subtasks were created, targeting which services with which agents
3. **Specialist findings** — each specialist's confidence, evidence, and summary
4. **Synthesis** — cross-service correlation and recommended next steps
5. **Final RCA Report** — root cause, evidence chain, and recommended actions
6. **Usage summary** — total tokens, cost, and duration

### Log Files

| File | What It Contains | How to Enable |
|------|-----------------|---------------|
| `rca_execution.log` | Full debug trace: agent decisions, tool calls, state transitions | Always active (Python logging) |
| `rca_commands.log` | Every command sent to containers and its raw output | Set `LOG_COMMAND_OUTPUTS=true` in `.env` |
| `logs/usage_log.jsonl` | One JSON line per run: model, tokens, cost, duration | Always active |

### Web UI Details

See `rca-framework/UI_GUIDE.md` for the full walkthrough. Key features:

- **Live streaming** — findings appear in real-time as each specialist completes
- **Node status badges** — color-coded indicators (gray=idle, amber=running, green=done, red=error)
- **Timeline tab** — expandable per-cycle view showing parent decisions, specialist findings with confidence bars, and synthesis output
- **RCA Report tab** — the final Markdown report, only appears after conclusion

---

## Security

- **Command Allowlist** (`core/security/allowlist.py`): Deny-first. Blocks `rm`, `chmod`, `curl`, `wget`, `nc`, shell redirects, `| bash`. Only explicitly allowed read-only commands proceed.
- **Output Redactor** (`core/security/redactor.py`): Strips AWS keys, PEM blocks, bearer tokens, passwords, email addresses, IPv4 addresses, and long base64 strings from all command output before it reaches the LLM.

## Research Paper

See `LLM_assisted_Triage/` for the IEEE conference paper (IEEEtran format).

| Section | Status |
|---------|--------|
| Abstract, Introduction, Related Work, Methodology | Complete |
| Experiments & Results (Section IV) | Pending write-up (6/6 experiments run) |
| Conclusion | Pending |

Track all task status in `AGENTS.md`.

## License

MIT — see [LICENSE](LICENSE).
