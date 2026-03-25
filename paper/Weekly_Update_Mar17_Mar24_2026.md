# Weekly Progress Update — Mar 17–24, 2026
**Project:** LLM-Assisted Triage (AI-Infra-Project v1)
**Author:** Kalhar Pandya

---

## Overview

This week's work focused on extending the RCA framework with a real-world mail server demo target deployed on AWS, wiring it into the LangGraph agent pipeline, and running the first end-to-end fault injection experiment. Key deliverables: a working 4-service mail stack on EC2, a Locust load/functionality test suite, a complete fault injection playbook (6 experiments), and a confirmed successful RCA agent run.

---

## 1. Mail Server Setup on AWS EC2

**Goal:** Provide a realistic, multi-service target environment for the RCA framework — replacing the local voting-app demo with a production-like mail stack.

### What was deployed

A 4-container Docker Compose stack on `ubuntu@16.174.20.34` (EC2):

| Container | Image | Role | Ports |
|-----------|-------|------|-------|
| `mail-app-mailserver-1` | `docker-mailserver/docker-mailserver` | Postfix (SMTP) + Dovecot (IMAP) | 25, 587, 143, 993 |
| `mail-app-roundcube-1` | `roundcube/roundcubemail:latest-apache` | PHP webmail UI | 8080 |
| `mail-app-db-1` | `postgres:15-alpine` | Roundcube session/contact store | 5432 (internal) |
| `mail-app-redis-1` | `redis:7-alpine` | PHP session cache | 6379 (internal) |

### Key setup steps
- Wrote `docker-compose.yml`, `mailserver.env`, `setup.sh` (auto-creates alice/bob/admin test accounts), and `aws-setup.sh` (EC2 bootstrap script)
- All containers configured with `restart: always` — survive reboots without manual intervention
- Stack deployed directly from GitHub repo (`/home/ubuntu/LLM-assisted-Triage/demo-targets/mail-app/`) — no manual file copies

**Commits:**
- `eb31635` — `Kalhar: Add mail-app demo target and RCA profile` (757 lines: docker-compose, mailserver.env, setup scripts)
- `40c985f` — `Kalhar: Fix Roundcube healthcheck case-sensitivity (grep -qi)` — healthcheck was using case-sensitive grep for "roundcube" but HTML had "Roundcube"

---

## 2. Redis Session Integration in Roundcube (PHP)

**Goal:** Wire Redis as the PHP session backend for Roundcube so session data is stored in-memory (not on disk), enabling EXP-03 (Redis eviction fault) to produce a meaningful signal.

### What was done
- Added `config/redis-session.php` — PHP session configuration pointing Roundcube at the Redis container
- Mounted the config via a Docker post-setup script (`config/setup-redis.sh`) injected into Roundcube's entrypoint tasks directory
- Updated `docker-compose.yml` to mount the post-setup script at `/entrypoint-tasks/post-setup/setup-redis.sh`

This ensures Roundcube's PHP session handler uses Redis (`tcp://redis:6379`) instead of the default file-based sessions, making Redis failures immediately visible as session drops in the webmail UI.

**Commits:**
- `c70e588` — `fix(mail-app): add redis session config for roundcube`
- `46a7262` — `fix(mail-app): use post-setup script for redis config` (fixed mount approach — PHP config alone wasn't sufficient; needed the entrypoint hook)

---

## 3. Locust Load & Functionality Testing

**Goal:** Create a multi-protocol test suite that exercises all paths of the mail stack simultaneously and provides clear failure signals per protocol.

### What was built (`demo-targets/mail-app/locustfile.py` — 635 lines)

Three Locust user classes covering all three protocols:

| Class | Protocol | Tasks |
|-------|----------|-------|
| `WebMailUser` (weight 3) | HTTP → Roundcube | login, list inbox, open message, compose+send, round-trip verify |
| `SMTPUser` (weight 1) | SMTP port 587 (STARTTLS) | direct send, round-trip (send → IMAP verify) |
| `IMAPUser` (weight 1) | IMAP port 143 (STARTTLS) | select+list, search unseen, full session |

Custom `SmtpClient` and `ImapClient` wrappers emit metrics to the Locust dashboard via `events.request.fire()`, so IMAP/SMTP operations appear alongside HTTP in the stats table.

### Bugs fixed during development
Three bugs were identified and fixed:

1. **`r.url` is `None` in `catch_response` context** — Locust's `catch_response=True` context doesn't guarantee `r.url`. Fixed by checking `r.text` body content instead (look for `name="_pass"` / `id="login-form"`) rather than inspecting the URL.

2. **IMAP state after reconnect (`SEARCH illegal in state AUTH`)** — After a failed IMAP command, `_reconnect()` logged back in but forgot to `SELECT INBOX`. Subsequent `SEARCH` commands were rejected by Dovecot because the session was in `AUTH` state, not `SELECTED`. Fixed by calling `select_inbox()` immediately after reconnect.

3. **Round-trip delivery timeout** — Original code used a fixed `gevent.sleep(3)` then checked once. Under load, mail delivery took longer than 3s. Fixed by polling in a loop: `for _ in range(15): gevent.sleep(1); check inbox; if found: break`.

**Commit:** `8ec6be9` — `feat: Introduce a mail application demo target with Locust load testing and Docker Compose configuration.`

---

## 4. RCA Framework — Mail App Profile & Agent Wiring

**Goal:** Connect the mail-app stack to the LangGraph RCA agent pipeline so investigations can run against it from both `demo.py` (CLI) and `ui.py` (Streamlit).

### What was built

**Profile** (`rca-framework/profiles/mail_app/`):
- `profile.yaml` — service definitions for all 4 containers with `access_method: ssh`, SSH key path, per-service `context_commands`, `log_hints`, `known_failures`, and `expected_behavior`
- `parent.yaml`, `synthesis.yaml` — orchestrator and synthesis agent prompts
- `agents/log_agent.yaml`, `agents/runtime_status_agent.yaml`, `agents/docker_specs_agent.yaml`, `agents/network_agent.yaml` — specialist agent system prompts tuned for mail-service failure patterns

**Agent graph updates** (`rca-framework/core/`):
- `graph/builder.py` — updated to support SSH-based profiles (not just local Docker)
- `agents/specialists/base_specialist.py` — added `run()` method that creates `SSHExecutor`, runs context commands, passes output to LLM tool loop, parses findings
- `framework/models.py` — added `SSHConfig` model with host/user/key/timeout fields

**Both `ui.py` and `demo.py` are functionally identical** — the UI is a Streamlit wrapper around the same LangGraph graph. Selecting `mail_app` profile causes agents to SSH into `16.174.20.34` and run `docker exec` commands remotely.

**Commits:**
- `fb5f3dd` — `feat: Introduce core RCA framework data models and a new mail_app profile configuration`
- `663a6c4` — `feat: Introduce initial Root Cause Analysis (RCA) framework with agent architecture, mail application profile, and Docker integration` (730 lines across 17 files)

---

## 5. SSH Tool Fix

**Problem:** `ssh_tool.py` used `paramiko.RSAKey.from_private_key_file()` — hardcoded to RSA key type. If the PEM file is Ed25519 or ECDSA, this raises `SSHException`, the agent gets `SSH_ERROR: not a valid RSA private key file` as command output, and can produce misleading findings.

**Fix:** Changed to `key_filename=ssh_config.key_path` in `client.connect()` — paramiko auto-detects the key type (RSA, Ed25519, ECDSA, etc.).

```python
# Before
connect_kwargs["pkey"] = paramiko.RSAKey.from_private_key_file(ssh_config.key_path)

# After
connect_kwargs["key_filename"] = ssh_config.key_path  # auto-detects key type
```

**Commit:** `606cf7d` — `Kalhar: Fix ssh_tool to auto-detect key type instead of hardcoding RSAKey`

---

## 6. Fault Injection Experiments

**Goal:** Define a repeatable experiment playbook — inject a fault, observe the Locust signal, run the RCA agent, restore, repeat.

### Experiment design (`demo-targets/mail-app/EXPERIMENTS.md`)

Six experiments covering different failure modes:

| ID | Fault | One-line inject | Affected |
|----|-------|-----------------|----------|
| EXP-01 | Mailserver crash | `docker stop mail-app-mailserver-1` | SMTP + IMAP + Webmail |
| EXP-02 | PostgreSQL outage | `docker stop mail-app-db-1` | Webmail only |
| EXP-03 | Redis memory exhaustion | `redis-cli CONFIG SET maxmemory 1mb` | Webmail sessions (silent 200s) |
| EXP-04 | Postfix size limit misconfiguration | `postconf -e message_size_limit=1024` | All sends |
| EXP-05 | Roundcube crash | `docker stop mail-app-roundcube-1` | Web UI only |
| EXP-06 | Dovecot IMAP connection limit | `echo mail_max_userip_connections=1 >> dovecot.cf` | IMAP only (partial) |

All experiments include: inject command, expected Locust signal table, RCA incident description string, and restore command.

### EXP-06 — First End-to-End Run ✅

**EXP-06** was the first experiment run end-to-end this week:

**Fault injected:** `mail_max_userip_connections=1` in Dovecot — limits each user to 1 simultaneous IMAP connection per IP address.

**Locust signal observed (confirmed):**
```
29  IMAP  imap.full_session  error('[UNAVAILABLE] Maximum number of connections from user+IP exceeded')
 3  IMAP  imap.full_session  abort('command: LOGIN => socket error: EOF')
 3  IMAP  imap.login         abort('command: LOGIN => socket error: EOF')
```
- RPS collapsed from ~1.8 to near-zero; p95 latency spiked to 100,000ms
- SMTP and Roundcube webmail unaffected (correct — only IMAP was throttled)

**RCA Agent result (inc-98b699):**
- **Model:** `openai/gpt-4.1`
- **Cycles:** 4 | **Elapsed:** 136.5s | **Nodes:** 4/6 | **Est. cost:** ~$0.49
- **Verdict:** ✅ Agent correctly identified `mail_max_userip_connections=1` as the exact root cause
- Agent ruled out OOM, disk exhaustion, Redis/DB issues through systematic specialist investigation
- Recommended: increase to 3–5 connections, add monitoring alerts, document in runbooks

**Commits:**
- `752e241` — `Kalhar: Add mail-app fault injection experiments guide`
- `9913c43` — `Kalhar: Simplify experiments + add AGENTS.md task tracker for mail-app`
- `e4658e1` — `Kalhar: Add EXP-06 Dovecot connection limit (confirmed working), update AGENTS.md progress`

---

## 7. Project Housekeeping

- **`demo-targets/mail-app/AGENTS.md`** — created as a living task tracker: infrastructure status, per-experiment progress table, and outstanding task list
- **Stale folder cleanup** — removed manually-copied `/home/ubuntu/mail-app/` from the EC2 instance; all operations now run from the GitHub repo clone
- **SSH connection pattern documented** in project memory: use `StrictHostKeyChecking=no` + `-i key.pem` + run commands non-interactively with quoted commands

---

## Commit Log (chronological)

| Date | Hash | Message |
|------|------|---------|
| Mar 21 | `eb31635` | Kalhar: Add mail-app demo target and RCA profile |
| Mar 21 | `8ec6be9` | feat: Introduce mail-app Locust load testing and Docker Compose |
| Mar 21 | `40c985f` | Kalhar: Fix Roundcube healthcheck case-sensitivity |
| Mar 21 | `fb5f3dd` | feat: Introduce core RCA framework data models and mail_app profile |
| Mar 21 | `663a6c4` | feat: Introduce initial RCA framework with agent architecture |
| Mar 21 | `c70e588` | fix(mail-app): add redis session config for roundcube |
| Mar 21 | `46a7262` | fix(mail-app): use post-setup script for redis config |
| Mar 24 | `752e241` | Kalhar: Add mail-app fault injection experiments guide |
| Mar 24 | `9913c43` | Kalhar: Simplify experiments + add AGENTS.md task tracker |
| Mar 24 | `e7b4938` | Kalhar: Add AGENTS.md project task tracker |
| Mar 24 | `e4658e1` | Kalhar: Add EXP-06 Dovecot connection limit (confirmed working) |
| Mar 24 | `606cf7d` | Kalhar: Fix ssh_tool to auto-detect key type instead of hardcoding RSAKey |

---

## Next Steps

- Run EXP-01 through EXP-05 end-to-end (inject → Locust → RCA agent → restore)
- Document agent findings per experiment in AGENTS.md
- Analyse agent performance across experiments (accuracy, cycles, cost, time)
- Feed results into the IEEE paper's evaluation section
