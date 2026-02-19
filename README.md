# LLM-Assisted Triage

Multi-agent RCA framework for automated incident investigation in cloud/microservice environments.

## Project Structure

```
v1/
├── rca-framework/          # Core RCA agent framework
│   ├── agents/            # Parent + specialist agents
│   ├── config/            # Prompts, models, service configs
│   ├── graph/             # LangGraph orchestration + registry
│   ├── security/          # Command allowlist + redaction
│   ├── tools/             # Docker/SSH executors
│   ├── tests/             # Unit tests
│   ├── demo.py            # Entry point
│   └── requirements.txt   # Python dependencies
├── paper/                 # Research paper (LaTeX)
└── Summary-SP2026-Kalhar.docx  # Project summary

```

## Quick Start

### Prerequisites
- Python 3.11+
- Docker (for demo)
- OpenRouter API key

### Installation

```bash
cd rca-framework
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### Run Demo

```bash
python demo.py
```

The demo investigates the example voting app (5 microservices: vote, worker, redis, db, result).

### Configuration

All behavior is controlled via `.env`:

```bash
LLM_MODEL=openai/gpt-4.1           # Model to use
MAX_ITERATIONS=10                   # Max tool calls per agent
MAX_CONCURRENCY=10                  # Parallel specialist nodes
DOCKER_EXEC_TIMEOUT=10              # Command timeout (seconds)
DOCKER_LOGS_TAIL=200                # Lines of docker logs to fetch
```

## Architecture

### Graph Flow

```
START → planning (parent LLM) → [Send fan-out] → specialist nodes → END
```

- **Parent Agent**: Reads incident + service config, produces subtasks
- **Specialist Agents**: Self-register via `graph/registry.py`, execute in parallel
- **LangGraph**: Dynamic dispatch based on `Subtask.assigned_agent`

### Adding a New Specialist

1. Create `agents/specialists/my_agent.py`:
```python
from agents.specialists.base_specialist import BaseSpecialist
from graph.registry import register, SpecialistRegistration

class MyAgent(BaseSpecialist):
    @property
    def agent_type(self) -> str:
        return "my_agent"
    
    @property
    def prompt_file(self) -> str:
        return "my_system.txt"
    
    @property
    def context_commands(self) -> list[str]:
        return ["ls /app", "ps aux"]

def my_agent_node(state: dict) -> dict:
    finding = MyAgent().run_docker(...)
    return {"current_cycle_findings": [finding]}

register(SpecialistRegistration(
    agent_type="my_agent",
    description="Investigates X by doing Y",
    node_name="my_agent_node",
    node_fn=my_agent_node,
))
```

2. Import in `demo.py`:
```python
import agents.specialists.my_agent  # noqa: F401
```

Done. The parent LLM now sees "my_agent" as an option and can assign subtasks to it.

## Service Configuration

Services are defined in `configs/voting_app.yaml`:

```yaml
services:
  - service_name: vote
    container: example-voting-app-vote-1
    expected_behavior: |
      Serves HTTP on port 80, connects to Redis
    known_failures:
      - pattern: "ConnectionError: Error -2"
        likely_cause: "Redis is down"
    context_commands:
      - "cat /proc/1/environ | tr '\\0' '\\n' | grep REDIS"
      - "cat /usr/local/app/app.py"
    log_hints:
      - "Application stdout is provided as docker logs"
      - "Look for ConnectionError in the logs"
```

The parent LLM reads this to decide which services to investigate. Specialists receive `context_commands` and `log_hints` to guide their investigation.

## Security

- **Command Allowlist**: `security/allowlist.py` blocks write operations, redirects, network tools
- **Output Redaction**: `security/redactor.py` strips AWS keys, private keys, emails, IPs
- **Timeouts**: All commands timeout after `DOCKER_EXEC_TIMEOUT` seconds
- **Output Caps**: stdout/stderr truncated at `MAX_OUTPUT_BYTES`

## Research

See `paper/` for the full research paper on LLM-assisted incident triage.

## License

MIT
