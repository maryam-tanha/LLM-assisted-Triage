# Methodology Draft
## An Open-source LLM-Assisted System for IT/SRE Triage

---

## Overview

This section describes the design and implementation of our hierarchical multi-agent Root Cause Analysis (RCA) framework. The system automates incident investigation in cloud-native microservice environments by decomposing the diagnostic problem across a set of specialized LLM agents, each operating within a strictly scoped execution context. The framework is built on LangGraph and communicates with any OpenRouter-compatible LLM, making it deployable without custom model infrastructure.

---

## 3.1 System Architecture

The system follows a **hierarchical, iterative graph** pattern with three tiers:

1. **Parent Agent** — orchestrates the investigation; decides what to examine and when to conclude
2. **Specialist Agents** — execute narrow, domain-specific investigations in parallel
3. **Synthesis Agent** — correlates cross-domain findings between each investigation cycle

These tiers form a loop that repeats until the Parent Agent either produces a root cause conclusion or the cycle limit is reached.

```
START
  |
  v
[Parent Agent]  ──── "conclude" ──────────────> END
  |
  "investigate"
  |
  v  (fan-out via Send)
[Specialist Nodes]  (parallel)
  log_agent | runtime_status_agent | ...
  |
  v  (findings merged via list reducer)
[Synthesis Agent]
  |
  v  (loop back)
[Parent Agent]
```

The graph is constructed dynamically at startup from a registry of registered specialists. Adding a new specialist requires only creating a module that calls `register()` at import time; no changes to the orchestration layer are needed.

---

## 3.2 Service Configuration (YAML)

All system behavior is driven by a per-product YAML configuration file, which acts as the source of truth for both the Parent Agent's planning and the specialists' execution context. The schema is validated with Pydantic before the graph is invoked.

**Top-level fields (`ProductConfig`):**

| Field | Type | Description |
|---|---|---|
| `product` | string | Human-readable product name |
| `access_method` | string | `"docker_exec"` or `"ssh"` |
| `services` | list | Service definitions (see below) |
| `agents` | list | References to agent YAML config files |

**Per-service fields (`ServiceConfig`):**

| Field | Type | Description |
|---|---|---|
| `service_name` | string | Logical service identifier |
| `container` | string | Docker container name or SSH hostname |
| `expected_behavior` | string | Plain-language description of healthy behavior |
| `known_failures` | list | Pattern-to-cause mappings for common failure modes |
| `context_commands` | list | Shell commands run at the start of every investigation for this service |
| `log_hints` | list | Free-text hints about where relevant logs appear |
| `additional_info` | dict | Metadata: owner, dependencies, version, etc. |

**Known failure entry:**
```yaml
known_failures:
  - pattern: "ConnectionError: Error -2"
    likely_cause: "Redis is down or not reachable"
```

The `context_commands` field is particularly significant: these commands run before the ReAct loop begins, giving the specialist an initial evidence snapshot without consuming tool-call budget.

**Example (voting app):**
```yaml
product: VotingApp
access_method: docker_exec
services:
  - service_name: vote
    container: example-voting-app-vote-1
    expected_behavior: |
      Serves HTTP on port 80, connects to Redis for vote buffering.
    known_failures:
      - pattern: "ConnectionError: Error -2"
        likely_cause: "Redis is down"
    context_commands:
      - "cat /proc/1/environ | tr '\\0' '\\n' | grep REDIS"
      - "cat /usr/local/app/app.py"
    log_hints:
      - "Application stdout is provided via docker logs"
      - "Look for ConnectionError in the logs"
agents:
  - agents/log_agent.yaml
  - agents/runtime_status_agent.yaml
```

---

## 3.3 Parent Agent

The Parent Agent is the planning and decision-making component of the system. At each cycle it receives the full incident context, the list of available specialists, all prior cycle summaries, and the new synthesis output, then selects one of two actions via tool calls:

**Tool 1: `create_subtasks`**
Invoked when more evidence is needed. Produces a list of `Subtask` objects, each specifying the target service, container, natural-language description, investigation hypothesis, and the specialist to assign.

```python
class Subtask(BaseModel):
    subtask_id: str        # Format: "c{cycle}-task-{num:03d}"
    service_name: str
    container: str
    description: str
    hypothesis: str
    assigned_agent: str    # Must match a registered agent_type
```

**Tool 2: `write_rca_conclusion`**
Invoked when the parent has sufficient evidence to declare a root cause. Produces a structured report with `root_cause`, `contributing_factors`, `evidence_summary`, and `recommended_actions`.

**Decision logic:**

The parent is forced to invoke `write_rca_conclusion` if `current_cycle >= max_cycles` (default: 3), ensuring the loop always terminates. The system also supports a **manual mode** in which subtasks are pre-populated in the initial state, causing the parent to bypass LLM planning entirely and route directly to the nominated specialist. This mode is useful for targeted single-service investigation.

**Prompt construction:**

At each cycle, the parent receives a user message containing:
- The incident summary
- The full YAML service topology
- The list of registered specialists with their descriptions and `when_to_use` / `do_not_use` guidance
- All prior `CycleSummary` objects
- The current cycle number and limit

The system prompt instructs the parent to reason about which services are implicated, which specialists are best suited, and whether the accumulated evidence is sufficient to conclude.

---

## 3.4 Specialist Agents

Specialist agents are domain-focused LLM agents that execute shell commands against a target container or host and produce a structured `SpecialistFinding`. All specialists share a common abstract base class (`BaseSpecialist`) that enforces a consistent interface.

**Abstract interface:**
```python
class BaseSpecialist(ABC):
    @property
    @abstractmethod
    def agent_type(self) -> str: ...      # Registry key

    @property
    @abstractmethod
    def prompt_file(self) -> str: ...     # System prompt filename

    @property
    @abstractmethod
    def context_commands(self) -> list[str]: ...  # Default pre-run commands
```

**Execution modes:**

Two execution backends are supported:

- **Docker exec** (`run_docker()`): uses `docker exec <container> sh -c <command>` on the local host. Container logs are fetched separately via `docker logs --tail N` since they are only available from the host side.
- **SSH** (`run()`): uses paramiko to establish an SSH session. A connection pool keyed by `(host, port, username)` reuses open sessions across commands.

Both paths apply the command allowlist and output redactor before any data reaches the LLM (Section 3.6).

**ReAct investigation loop:**

Each specialist runs a LangChain ReAct agent with a single tool: `run_command`. The agent is given:
- The specialist system prompt (domain knowledge, expected output format)
- Context command output (pre-fetched before the loop starts)
- Container logs (Docker mode only)
- The subtask description and hypothesis from the parent
- Service-level `known_failures`, `expected_behavior`, and `log_hints` from the YAML config

The loop continues until the LLM produces a `FINAL ANSWER` in the required format or the recursion limit is hit (`(MAX_ITERATIONS + buffer) * 2 + 1`, default MAX_ITERATIONS=10).

**Output format (`SpecialistFinding`):**

```python
class SpecialistFinding(BaseModel):
    agent_type: str
    subtask_id: str
    findings: str           # Full markdown narrative
    commands_run: list[str]
    evidence: list[str]     # Bullet-point evidence items
    confidence: float       # 0.0–1.0
    timestamp: datetime
```

The specialist is instructed to embed `CONFIDENCE: <float>` and `EVIDENCE:` and `SUMMARY:` sections in its final answer. The base class parses these with regex and falls back to safe defaults if the format is not followed.

**Registered specialists (current):**

| Agent Type | Focus | Default Context Commands |
|---|---|---|
| `log` | Application logs, error patterns, service-specific CLI tools | `journalctl`, `dmesg`, `tail /var/log/syslog` |
| `runtime_status` | Memory, CPU, disk, process state, resource limits | `df -h`, `free -m`, `top -bn1`, `ps aux`, `/proc/meminfo` |

New specialists register at import time and are automatically visible to the parent and graph builder:

```python
register(SpecialistRegistration(
    agent_type="log",
    description="Investigates container logs...",
    node_name="log_specialist",
    node_fn=log_specialist_node,
))
```

---

## 3.5 Synthesis Agent

After each investigation cycle, before the parent agent is called again, a Synthesis Agent correlates all new specialist findings. Its role is to surface cross-domain connections that individual specialists cannot see because they operate in isolated contexts.

**Input:** All `SpecialistFinding` objects produced since the previous synthesis, plus the full cumulative history of prior cycle summaries.

**Output (`CycleSummary`):**
```python
class CycleSummary(BaseModel):
    cycle_num: int
    summary: str              # Narrative paragraph
    key_findings: list[str]   # Bullet points
    recommendations: list[str]
    specialist_types: list[str]
    timestamp: datetime
```

The synthesis agent does not have tool access — it is a single LLM call over the aggregated findings. The system prompt instructs it to look for causal chains across services (e.g., a memory pressure event on one host correlating with elevated latency in a downstream service). Its `SUMMARY` and `KEY_FINDINGS` sections are appended to the `cumulative_history` string, which the parent agent reads in subsequent cycles.

A `findings_offset` pointer ensures the synthesis agent only processes findings that are new since the last cycle; it never re-reads already-processed findings.

---

## 3.6 Security Layer

Two security components apply to every command execution path before any data is returned to the LLM.

### 3.6.1 Command Allowlist

The allowlist enforces a **deny-first** policy. A command is blocked if it matches any blocked pattern; if not blocked, it must match an allowed prefix to proceed.

**Blocked patterns (regex, any position in string):**
- Destructive operations: `rm`, `chmod`, `chown`, `sudo`, `mkfs`, `dd`
- Shell redirection: `>`, `>>`, `>/dev/`
- Code injection: `| bash`, `| sh`, `eval`, `exec`
- Network exfiltration: `curl`, `wget`, `nc`, `netcat`

**Allowed prefixes (must appear at start of command):**
- Log reading: `journalctl`, `tail`, `dmesg`, `cat /var/log/`, `cat /proc/`
- System status: `df`, `free`, `ps`, `top -bn1`, `uptime`, `hostname`, `date`, `uname`
- Service tools: `redis-cli`, `psql`, `node`, `python`
- Filtering: `grep`, `wc`, `ls`

Blocked commands return the string `"BLOCKED: <reason>"` to the specialist, which the LLM must handle by choosing a different command or concluding with available evidence.

### 3.6.2 Output Redactor

All command output is redacted before being passed to the LLM. Patterns are applied in priority order (most specific first):

| Pattern | Replacement |
|---|---|
| AWS access key prefixes (`AKIA`, `ASIA`, `AROA` + 16 chars) | `[REDACTED_AWS_KEY]` |
| PEM private key blocks | `[REDACTED_PRIVATE_KEY]` |
| Bearer tokens | `bearer [REDACTED_TOKEN]` |
| `api_key=...` | `api_key=[REDACTED_KEY]` |
| `password=...` | `password=[REDACTED_PASSWORD]` |
| `secret=...` | `secret=[REDACTED_SECRET]` |
| Email addresses | `[REDACTED_EMAIL]` |
| IPv4 addresses | `1.x.x.x` (partial, preserves subnet context) |
| Base64 strings (40+ chars) | `[REDACTED_BASE64]` |

The redactor is applied in both the Docker exec and SSH execution paths. It can be extended with `extra_patterns` at instantiation time for deployment-specific secrets.

---

## 3.7 Graph Construction and State Management

The graph is built dynamically at startup by `build_graph()` in `graph/builder.py`.

### Graph State

The shared state is a LangGraph `TypedDict` (`GraphState`) that flows through all nodes:

| Field | Type | Notes |
|---|---|---|
| `incident_id` | str | Unique incident identifier |
| `incident_summary` | str | Plain-language description of the incident |
| `product_config` | dict | Serialized YAML config |
| `subtasks` | list[Subtask] | Current cycle's investigation tasks |
| `parent_decision` | str | `"investigate"` or `"conclude"` |
| `current_cycle` | int | Cycle counter |
| `max_cycles` | int | Configurable limit (default: 3) |
| `current_cycle_findings` | Annotated[list, add] | Parallel findings merged by reducer |
| `findings_offset` | int | Pointer for synthesis to read only new findings |
| `cycle_summaries` | Annotated[list, add] | Accumulated cycle summaries |
| `cumulative_history` | str | Running text context for the parent |
| `rca_finding` | str | Final root cause string |
| `final_report` | str | Full markdown RCA report |

The `Annotated[list, operator.add]` type on `current_cycle_findings` and `cycle_summaries` is the LangGraph reducer that enables parallel specialist nodes to write their results independently; LangGraph merges them via list concatenation without conflict.

### Routing

A conditional edge function `route_parent()` inspects `parent_decision` after each parent agent invocation:

- If `"conclude"` → routes to `END`
- If `"investigate"` → produces a `list[Send]`, one per subtask, fanning out to the assigned specialist node

```python
def route_parent(state: GraphState):
    if state["parent_decision"] == "conclude":
        return END
    return [
        Send(entry.node_name, {
            "subtask_id": subtask.subtask_id,
            "subtask_description": subtask.description,
            "container": subtask.container,
            "service_context": build_service_context(subtask, state),
        })
        for subtask, entry in zip(state["subtasks"], resolved_entries)
    ]
```

The `Send` API is LangGraph's mechanism for parallel dispatch: each `Send(node, payload)` creates an independent invocation of the target node. All such invocations run concurrently up to `MAX_CONCURRENCY` (default: 10), and their outputs are merged into the shared state by the list reducer.

### Edge Summary

| Edge | Type | Condition |
|---|---|---|
| START → parent_agent | Fixed | Always |
| parent_agent → END | Conditional | `parent_decision == "conclude"` |
| parent_agent → specialist(s) | Conditional (Send) | `parent_decision == "investigate"` |
| specialist → synthesis | Fixed | Always |
| synthesis → parent_agent | Fixed | Always |

---

## 3.8 LLM Integration

All agents share a single LLM accessor (`get_llm()`) backed by OpenRouter, which provides a unified API to any hosted model. The model is selected via the `LLM_MODEL` environment variable (e.g., `openai/gpt-4.1`), making the framework model-agnostic at the orchestration layer.

**Per-agent binding:**

| Agent | Binding |
|---|---|
| Parent Agent | `get_llm().bind_tools(tools, tool_choice="any")` — forces a tool call |
| Specialist Agents | `create_agent(get_llm(), tools=[run_command], system_prompt=...)` |
| Synthesis Agent | `get_llm().invoke(messages)` — no tools, pure generation |

The `tool_choice="any"` constraint on the parent prevents it from generating free text in lieu of a structured action, ensuring state transitions are always typed and parseable.

---

## 3.9 Environment Configuration

The system is configured entirely through environment variables, allowing deployment-specific tuning without code changes:

| Variable | Default | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | — | Required; OpenRouter authentication |
| `LLM_MODEL` | — | Model identifier (e.g., `openai/gpt-4.1`) |
| `MAX_CYCLES` | 3 | Maximum investigation cycles before forced conclusion |
| `MAX_ITERATIONS` | 10 | Maximum ReAct steps per specialist |
| `MAX_CONCURRENCY` | 10 | Parallel specialist execution limit |
| `DOCKER_EXEC_TIMEOUT` | 30 | Command timeout in seconds |
| `DOCKER_LOGS_TAIL` | 200 | Lines to retrieve from docker logs |
| `MAX_OUTPUT_BYTES` | 65536 | Command stdout cap |
| `STDERR_MAX_BYTES` | 4096 | Command stderr cap |

---

## 3.10 Extension Points

The framework is designed for incremental extension at two levels:

**Adding a specialist:**
1. Create `agents/specialists/my_agent.py` with a class extending `BaseSpecialist`
2. Define `agent_type`, `prompt_file`, and `context_commands`
3. Call `register(SpecialistRegistration(...))` at module level
4. Add `import agents.specialists.my_agent` in `demo.py`

The parent LLM immediately sees the new agent type in its prompt and can assign subtasks to it.

**Adding a service:**
Update the product YAML to add a new entry under `services`. No code changes are required; the parent agent reads the topology at invocation time.

---

## Notes for Paper Writing

- **Figures to add:** (1) Full graph topology diagram showing nodes, edges, and cycle loop; (2) Sequence diagram of a single investigation cycle from incident ingestion to RCA report; (3) YAML config schema diagram
- **Tables to add:** (1) Comparison of our design choices against prior work (D-Bot, RCACopilot, FLASH, MA-RCA); (2) Environment variable reference
- **Numbers to verify before submission:** MAX_CYCLES default, MAX_ITERATIONS default, MAX_CONCURRENCY default — confirm these match the actual `.env.example` values
- **Sections still needed:** Abstract, Experiments & Results, Conclusion
- **Terminology check:** "thin sidecar" (used in intro) should appear in Section 3.4 as well — currently called specialist/worker; consider aligning
