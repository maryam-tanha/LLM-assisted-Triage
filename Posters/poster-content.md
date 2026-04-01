# Poster Content — LLM-Assisted Triage

> Matches the Northeastern / Khoury College poster template exactly.
> Left column: Introduction → Objective → Methodology
> Centre: Figures / Charts / Diagrams
> Right column: Results → Analysis → Conclusion
> Bottom: Key Sources & Acknowledgements

---

## Poster Structure (ASCII Diagram)

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  [NEU Logo]   LLM-ASSISTED TRIAGE: A MULTI-AGENT FRAMEWORK FOR        [University Seal] │
│  Khoury       AUTOMATED INCIDENT ROOT CAUSE ANALYSIS                                    │
│  College      Automated fault diagnosis for microservice systems using                   │
│               LLM-powered specialist agents                                              │
├──────────────┬────────────────────────┬──────────────────────────────────────────────────┤
│   Authors    │       Advisor          │     Consultant              Affiliations         │
│ Kalhar Pandya│  Prof. Maryam Tanha    │  Dr. Dawood Sajjadi,     Northeastern University │
│              │                        │  Director of SRE,        Khoury College of       │
│              │                        │  Fortinet                Computer Sciences       │
├──────────────┴──┬─────────────────────┴────────────┬────────────────────────────────────┤
│                 │                                  │                                    │
│  Introduction   │    [FIGURE 1: Architecture       │  Results                           │
│                 │     Diagram — LangGraph           │                                    │
│  (6 bullets,    │     multi-agent flow]            │  (EXP-06 metrics table,            │
│   ~150 words)   │                                  │   Locust findings,                 │
│                 │    [FIGURE 2: Experiment          │   experiment suite table)          │
│                 │     Results — Pie/Bar Charts]    │                                    │
├─────────────────┤                                  ├────────────────────────────────────┤
│                 │                                  │                                    │
│  Objective      │    [FIGURE 3: Fault Injection    │  Analysis                          │
│                 │     Pipeline Diagram]            │                                    │
│  (1 paragraph,  │                                  │  (8 bullets,                       │
│   ~100 words)   │    [FIGURE 4: Demo Target        │   ~150 words)                      │
│                 │     Topology Diagrams]           │                                    │
├─────────────────┤                                  ├────────────────────────────────────┤
│                 │                                  │                                    │
│  Methodology    │    [FIGURE 5: EXP-06 Evidence    │  Conclusion                        │
│                 │     Log Panel / Code Block]      │                                    │
│  (5 structured  │                                  │  (contributions + future work,     │
│   bullets,      │    [FIGURE 6: Metric Callout     │   ~150 words)                      │
│   ~200 words)   │     Cards: 136.5s, $0.49,       │                                    │
│                 │     4 cycles]                    │  [Optional: concluding figure]     │
│                 │                                  │                                    │
├─────────────────┴──────────────────────────────────┴────────────────────────────────────┤
│                                                                                         │
│                        Key Sources & Acknowledgements                                   │
│                                                                                         │
│  Sources: (left-aligned)                     Acknowledgements: (right-aligned)           │
│  5 key references                            Advisor, Consultant, Infrastructure         │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## TITLE BANNER

**Title:**
LLM-Assisted Triage: A Multi-Agent Framework for Automated Incident Root Cause Analysis

**Subheading:**
Automated fault diagnosis for microservice systems using LLM-powered specialist agents

**Authors:** Kalhar Pandya
**Advisor:** Prof. Maryam Tanha
**Consultant:** Dr. Dawood Sajjadi, Director of SRE, Fortinet
**Affiliations:** Northeastern University, Khoury College of Computer Sciences

---

## LEFT COLUMN

### Introduction

This research addresses the challenge of automated Root Cause Analysis (RCA) in cloud-native microservice environments. Modern distributed systems comprise dozens of interdependent services where a single fault can cascade across the entire stack. Incident investigation requires SREs to correlate logs, process states, and configurations across containers — a slow, expert-dependent process that drives high Mean Time to Resolution (MTTR). Large Language Models (LLMs) demonstrate strong reasoning over unstructured operational data, yet existing approaches are limited to single-agent architectures lacking parallel investigation and iterative refinement. This study presents a multi-agent framework that addresses these gaps by combining parallel specialist dispatch, multi-cycle reasoning, and security-constrained live container introspection.

### Objective

This research aims to design, implement, and validate a multi-agent RCA framework that autonomously investigates microservice incidents. The specific objectives are to: (1) enable parallel investigation of multiple services using self-registering specialist agents, (2) support iterative multi-cycle reasoning where insufficient evidence triggers additional investigation rounds, (3) produce structured, evidence-backed RCA reports with calibrated confidence scores, (4) enforce security via deny-first command allowlisting and credential redaction, and (5) validate against real fault-injected deployments with known ground truth.

### Methodology

- This study employed a **systems design and empirical validation** approach to investigate LLM-driven automated incident root cause analysis in microservice environments.
- The framework was implemented using **LangGraph** with a cyclic multi-agent graph: Parent Agent (LLM orchestrator) → parallel specialist fan-out via Send API → Synthesis Agent → iterative loop or conclusion.
- Four **specialist agent types** were developed: Log Agent (log analysis), Runtime Status Agent (resource metrics), Docker Specs Agent (container config), and Network Agent (connectivity) — each self-registering at runtime.
- Validation data was collected through **controlled fault injection experiments** (6 designed, 1 confirmed) on two live environments: a 5-service Voting App (Docker Compose) and a 4-service Mail App (AWS EC2).
- **Load generation** used Locust with WebMailUser, SMTPUser, and IMAPUser task classes to simulate realistic traffic during fault conditions.
- Methodological rigor was ensured through **ground-truth comparison** — each experiment injects a known fault, and the agent's identified root cause is compared against the injected configuration change.

---

## RIGHT COLUMN

### Results

The framework was validated on EXP-06: Dovecot IMAP connection limit exhaustion (`mail_max_userip_connections=1`). The agent correctly identified the root cause in **4 cycles, 136.5 seconds, at ~$0.49 cost** (GPT-4.1 via OpenRouter), deploying 4 of 6 available specialists. Evidence cited included exact Dovecot log entries showing repeated IMAP login rejections. Locust confirmed 29 IMAP failures with `[UNAVAILABLE] Maximum connections exceeded`, 3 session aborts, and correlated `ConnectionResetError` events. The agent recommended increasing the limit to 3-5 and implementing connection utilization alerts. Five additional experiments (full crash, DB outage, Redis OOM, message size limit, web UI crash) are designed and pending execution.

### Analysis

The EXP-06 result demonstrates the framework can diagnose **partial degradation** faults — where IMAP fails while SMTP and webmail remain functional — a class of incident where overall health metrics appear normal, making it particularly challenging for human operators. The 4-cycle iterative approach was critical: Cycle 1 identified connection errors, while subsequent cycles narrowed to the exact Dovecot configuration parameter through synthesis-guided refinement. Parallel fan-out replaced the sequential context-switching required by single-agent or manual approaches. The deny-first security layer blocked zero legitimate commands while preventing all write and network operations. At $0.49 per run, the cost profile supports production deployment where reduced MTTR value far exceeds API cost. These findings align with and extend prior work (RCACopilot, FLASH, OpenRCA) by adding parallel execution and iterative reasoning.

### Conclusion

This research presents a multi-agent RCA framework that autonomously investigates microservice incidents through parallel specialist dispatch, iterative multi-cycle reasoning, and security-constrained live container introspection. The framework successfully identified an injected Dovecot connection limit fault in 136.5 seconds at $0.49, validating that LLM-assisted triage is viable for real-world incident response. Key contributions include: a LangGraph-based dynamic fan-out architecture, cycle-based investigation with synthesis-driven refinement, a deny-first security layer for safe LLM container access, and YAML-driven profiles for code-free deployment to new environments. Future work includes running all six experiments to benchmark accuracy, comparing MTTR against manual baselines, extending to Kubernetes, and adding human-in-the-loop approval for high-risk commands.

---

## BOTTOM BANNER

### Key Sources & Acknowledgements

**Sources:**
1. Chen et al., "RCACopilot: LLM-Aided Root Cause Analysis," ICSE 2024
2. Yang et al., "FLASH: Fast Log Anomaly Detection," ASE 2023
3. Wang et al., "OpenRCA: RCA via Knowledge Graphs + LLMs," ISSRE 2024
4. Hong et al., "MetaGPT: Multi-Agent Collaboration," ICLR 2024
5. LangGraph Documentation, LangChain Inc., 2024-2025

**Acknowledgements:**
Prof. Maryam Tanha (Advisor), Northeastern University, Khoury College of Computer Sciences. Dr. Dawood Sajjadi (Consultant), Director of SRE, Fortinet. Infrastructure supported by OpenRouter API and AWS EC2.

---

## CENTRE FIGURES (6 visuals to place in the middle area)

### Figure 1: Architecture Diagram (top centre)

```
                         ┌─────────────────────┐
                         │ Incident Description │
                         └──────────┬──────────┘
                                    ▼
                         ┌─────────────────────┐
                         │    PARENT AGENT      │◄──────────────┐
                         │    (LLM Planner)     │               │
                         │                      │               │
                         │  - create_subtasks   │               │
                         │  - write_conclusion  │               │
                         └──────────┬───────────┘               │
                                    │ Send fan-out              │
                         ┌──────────┼──────────┐                │
                         ▼          ▼          ▼                │
                       ┌────────┐ ┌─────────┐ ┌──────────┐     │
                       │  LOG   │ │RUNTIME  │ │ DOCKER   │     │
                       │ AGENT  │ │ STATUS  │ │  SPECS   │     │
                       │        │ │ AGENT   │ │  AGENT   │     │
                       │ logs,  │ │ memory, │ │ cgroups, │     │
                       │ errors │ │ disk,   │ │ restarts │     │
                       └───┬────┘ └───┬─────┘ └────┬─────┘     │
                           └──────────┼────────────┘            │
                                      ▼                         │
                         ┌─────────────────────┐                │
                         │  SYNTHESIS AGENT     │────────────────┘
                         │  → CycleSummary      │  Cycle N+1
                         └──────────┬───────────┘
                                    ▼
                         ┌─────────────────────┐
                         │   FINAL RCA REPORT  │
                         └─────────────────────┘
```

### Figure 2: Experiment Results Table (centre, as chart/table)

| ID     | Injected Fault              | Impact                   | Status        |
|--------|-----------------------------|--------------------------|---------------|
| EXP-01 | Full mailserver crash       | SMTP/IMAP/Web down       | Designed      |
| EXP-02 | PostgreSQL outage           | Roundcube total failure   | Designed      |
| EXP-03 | Redis OOM (1MB limit)       | Silent session eviction   | Designed      |
| EXP-04 | Postfix msg size (1KB)      | All sends fail            | Designed      |
| EXP-05 | Roundcube crash             | Web UI only              | Designed      |
| EXP-06 | Dovecot conn limit=1        | IMAP partial degradation | **Confirmed** |

### Figure 3: Fault Injection Pipeline (centre, horizontal flow)

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  1. INJECT   │────►│  2. LOCUST LOAD  │────►│  3. RCA AGENT    │────►│ 4. COMPARE TO   │
│     FAULT    │     │     TEST         │     │     RUN          │     │   GROUND TRUTH  │
│              │     │                  │     │                  │     │                 │
│  Modify      │     │  WebMailUser     │     │  Parent Agent    │     │  Root cause     │
│  config      │     │  SMTPUser        │     │  → Specialists   │     │  match?         │
│  parameter   │     │  IMAPUser        │     │  → Synthesis     │     │  Confidence?    │
└──────────────┘     └──────────────────┘     └──────────────────┘     └─────────────────┘
```

### Figure 4: Demo Target Topologies (centre)

**Voting App (Docker Compose, 5 services):**
```
[Browser] ──► [vote :8080] ──► [redis :6379] ──► [worker] ──► [db :5432]
                 (Flask)                           (.NET)      (PostgreSQL)
                                                                    │
[Browser] ◄── [result :8081] ◄─────────────────────────────────────┘
                 (Node.js)
```

**Mail App (AWS EC2, 4 services):**
```
[Browser] ──► [roundcube :8080] ──► [mailserver]
                 (PHP)               (Postfix + Dovecot)
                   │                  :25 / :587 / :993
                   ▼
             [db :5432]             [redis :6379]
             (PostgreSQL)           (session cache)
```

### Figure 5: EXP-06 Evidence Log Panel (centre, styled code block)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  LOCUST FAULT OBSERVATION — EXP-06                                      │
│                                                                         │
│  29  IMAP  error('[UNAVAILABLE] Maximum number of connections           │
│       from user+IP exceeded (mail_max_userip_connections=1)')           │
│   3  IMAP  abort('command: LOGIN => socket error: EOF')                 │
│   1  IMAP  ConnectionResetError(10054, ...)                             │
│                                                                         │
│  AGENT OUTPUT:                                                          │
│  "Dovecot's mail_max_userip_connections=1 caused mass IMAP login        │
│   rejections when users attempted concurrent connections."              │
└──────────────────────────────────────────────────────────────────────────┘
```

### Figure 6: Metric Callout Cards (centre bottom)

```
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │                  │   │                  │
│     136.5s       │   │      $0.49       │   │    4 cycles      │
│                  │   │                  │   │                  │
│   end-to-end     │   │    per run       │   │   to diagnose    │
│   investigation  │   │   (GPT-4.1)     │   │   root cause     │
│                  │   │                  │   │                  │
└──────────────────┘   └──────────────────┘   └──────────────────┘
```
