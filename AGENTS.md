# LLM-Assisted Triage — Agent & Task Progress

This file tracks all major work streams, tasks, and their current status across the project.

**Updated:** 2026-04-07

---

## Legend
- ✅ Done
- 🔄 In Progress
- ⬜ Not Started
- ❌ Blocked

---

## 1. RCA Framework — Core

| Task | Status | Notes |
|------|--------|-------|
| LangGraph graph builder (`core/graph/builder.py`) | ✅ | Fan-out via `Send`, parallel specialist execution |
| Parent agent — LLM-based orchestrator (`agents/parent_agent.py`) | ✅ | Tool-calling: `create_subtasks` / `write_rca_conclusion` |
| Synthesis agent (`agents/synthesis_agent.py`) | ✅ | Aggregates findings per cycle into `CycleSummary` |
| Graph state model (`core/graph/state.py`) | ✅ | `Annotated[list, operator.add]` reducers for parallel merge |
| Specialist registry (`core/graph/registry.py`) | ✅ | `register()` + `get_all()`, auto-import on startup |
| `log_agent` specialist | ✅ | Reads container logs, grep-based evidence extraction |
| `runtime_status_agent` specialist | ✅ | Checks process/resource state inside containers |
| `yaml_specialist` (profile-driven agents) | ✅ | Loads agent config from YAML, no code required |
| Security allowlist (`security/allowlist.py`) | ✅ | Blocks writes, redirects, network tools |
| Output redactor (`security/redactor.py`) | ✅ | Strips AWS keys, private keys, emails, IPs |
| Docker tool (`tools/docker_tool.py`) | ✅ | `docker exec` runner with timeout + output caps |
| SSH tool (`tools/ssh_tool.py`) | ✅ | SSH-based command execution for remote VMs |
| Usage tracker (`framework/usage_tracker.py`) | ✅ | Tracks token usage and cost per run |
| Multi-cycle investigation loop | ✅ | `max_cycles` env var, parent re-enters after synthesis |
| OpenRouter credit reporting | ✅ | Before/after credit delta printed in demo output |

---

## 2. RCA Framework — Profiles

| Task | Status | Notes |
|------|--------|-------|
| `voting_app` profile | ✅ | 5 services: vote, worker, redis, db, result |
| `voting_app` agent configs (log, runtime, network, docker_specs) | ✅ | All 4 YAML agents configured |
| `mail_app` profile (`profiles/mail_app/profile.yaml`) | ✅ | 4 services: mailserver, roundcube, db, redis — SSH access |
| `mail_app` agent configs (log, runtime, network, docker_specs) | ✅ | All 4 YAML agents configured |
| `mail_app` — SSH access method wired in | ✅ | Uses `tools/ssh_tool.py` via ubuntu@16.174.20.34 |

---

## 3. Demo Target — Mail App

| Task | Status | Notes |
|------|--------|-------|
| Docker Compose stack (`demo-targets/mail-app/docker-compose.yml`) | ✅ | mailserver, roundcube, db, redis |
| `restart: always` on all containers | ✅ | Survives reboots |
| Healthchecks on all 4 services | ✅ | Roundcube healthcheck fixed (grep -qi) |
| `mailserver.env` configuration | ✅ | STARTTLS on 587, IMAPS on 993 |
| Redis session config for Roundcube (`config/setup-redis.sh`) | ✅ | Post-setup script wired into Roundcube entrypoint |
| Test accounts (alice, bob, admin) | ✅ | Created via `setup.sh` on the server |
| AWS EC2 deployment | ✅ | Running at `16.174.20.34`, repo at `~/LLM-assisted-Triage` |
| `.gitignore` for runtime-generated config files | ⬜ | `dovecot-quotas.cf`, `postfix-accounts.cf`, `config/ssl/` untracked |

---

## 4. Locust Load & Functionality Testing

| Task | Status | Notes |
|------|--------|-------|
| `WebMailUser` — Roundcube HTTP session (login, inbox, compose, send) | ✅ | |
| `SMTPUser` — Direct SMTP submission (port 587, STARTTLS) | ✅ | |
| `IMAPUser` — Direct IMAP retrieval (port 143, STARTTLS) | ✅ | |
| SMTP round-trip test (send via SMTP, verify via IMAP) | ✅ | Polls up to 15s |
| Fix `r.url` NoneType bug in `WebMailUser._login()` | ✅ | Use body checks instead of `r.url` |
| Fix IMAP `search_unseen` state bug (SEARCH in AUTH state) | ✅ | `_reconnect()` now calls `select_inbox()` |
| Fix round-trip 3s hardcoded delay | ✅ | Replaced with 15-iteration polling loop |
| Session-drop detection on all webmail tasks | ✅ | All tasks check body for login form |

---

## 5. Experiments

| Task | Status | Notes |
|------|--------|-------|
| EXP-01: Dovecot IMAP connection limit exhaustion | ✅ Done | Agent correct — 4 cycles, 136s, ~$0.49 |
| EXP-02: PostgreSQL max connections exhaustion | ✅ Done | Agent correct — 1 cycle, ~30s, ~$0.027 |
| EXP-03: PHP memory limit too low | ✅ Done | Agent correct — 2 cycles, 75s, ~$0.14 |
| EXP-04: Postfix per-client send rate limit | ✅ Done | Agent correct — 1 cycle, 45s, ~$0.04 |
| EXP-05: DNS resolver corruption in mailserver | ✅ Done | Agent correct — 3 cycles, 155s, ~$0.58 |
| EXP-06: Container hard memory limit (OOM) | ✅ Done | Agent correct — 2 cycles, 95s, ~$0.32 |
| Run EXP-01 end-to-end (inject → Locust → agent → restore) | ✅ | |
| Run EXP-02 end-to-end | ✅ | |
| Run EXP-03 end-to-end | ✅ | |
| Run EXP-04 end-to-end | ✅ | |
| Run EXP-05 end-to-end | ✅ | |
| Run EXP-06 end-to-end | ✅ | |
| Document agent outputs and RCA accuracy per experiment | ✅ | Results documented in EXPERIMENTS.md |

---

## 6. Observability UI

| Task | Status | Notes |
|------|--------|-------|
| Streamlit UI (`rca-framework/ui.py`) | ✅ | 3-panel: sidebar, graph+log, inspector |
| Real-time `graph.stream()` updates | ✅ | Per-node events streamed live |
| Topology mermaid diagram | ✅ | Falls back to text if no internet |
| LangGraph Studio integration (`langgraph.json`) | ✅ | `langgraph dev` from `rca-framework/` |

---

## 7. Research Paper

| Task | Status | Notes |
|------|--------|-------|
| Literature review (20 papers) | ✅ | Summarised in `Literature_Review_Summary.md` |
| Architecture design doc | ✅ | `Summary-SP2026-Kalhar.md` |
| LaTeX paper — Abstract + Keywords | ✅ | Written 2026-04-04 |
| LaTeX paper — Introduction | ✅ | No changes needed, already accurate |
| LaTeX paper — Related Work | ✅ | No changes needed, already accurate |
| LaTeX paper — Methodology §III.1 Architecture overview | ✅ | Evaluator Agent removed; profile system introduced |
| LaTeX paper — Methodology §III.2 Service Configuration | ✅ | Expanded to multi-file profile directory system; YAML-only specialists added |
| LaTeX paper — Methodology §III.3 Parent Agent | ✅ | Manual investigation mode added |
| LaTeX paper — Methodology §III.4 Specialist Agents | ✅ | Docker host context gathering added; YAML specialist path added |
| LaTeX paper — Methodology §III.5 Synthesis | ✅ | Renamed from "Synthesis and Evaluation"; Evaluator Agent removed; future work note added |
| LaTeX paper — Methodology §III.6 Security Model | ✅ | No changes needed, already accurate |
| Architecture figure (`LLM_assisted_Triage/fig_architecture.tex`) | ✅ | Evaluator node, PASS node, FAIL arrow removed; conclusion routes directly to Final RCA Report; profile directory label added |
| Humanization pass on paper | ✅ | AI markers removed, em dashes replaced, voice consistent with original sections |
| Experimental results section | ⬜ | Depends on completing experiments (Section IV left empty intentionally) |
| Conclusion section | ⬜ | Left empty intentionally — to be written after experiments |
| Evaluation metrics defined | ⬜ | Precision/recall of root cause identification |

### Paper Location
- `LLM_assisted_Triage/main.tex` — main paper (IEEEtran)
- `LLM_assisted_Triage/fig_architecture.tex` — TikZ architecture figure
- `LLM_assisted_Triage/references.bib` — bibliography (20 entries)
- `LLM_assisted_Triage/PAPER_UPDATE_PLAN.md` — detailed plan used for this update session

---

## 8. Infrastructure / DevOps

| Task | Status | Notes |
|------|--------|-------|
| AWS EC2 mail server provisioned | ✅ | `ubuntu@16.174.20.34` |
| GitHub repo connected on server | ✅ | `~/LLM-assisted-Triage`, deploy key configured |
| SSH access documented in memory | ✅ | `ubuntu@16.174.20.34`, key at `P:\LLM-RCA-Reasearch\Keys\mail-server-kalhar-laptop.pem` |
| `.gitignore` for runtime mail config files | ⬜ | `config/ssl/`, `postfix-accounts.cf`, `dovecot-quotas.cf` |
