# Poster Content - LLM-Assisted Triage

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
│                 │     Diagram - LangGraph           │                                    │
│  (prose,        │     multi-agent flow]            │  (all 6 experiments summary,       │
│   ~48 words)    │                                  │   accuracy + cost metrics,         │
│                 │    [FIGURE 2: Experiment          │   ~62 words)                       │
│                 │     Results Table]               │                                    │
├─────────────────┤                                  ├────────────────────────────────────┤
│                 │                                  │                                    │
│  Objective      │    [FIGURE 3: Fault Injection    │  Analysis                          │
│                 │     Pipeline Diagram]            │                                    │
│  (1 paragraph,  │                                  │  (prose,                           │
│   ~41 words)    │    [FIGURE 4: Demo Target        │   ~57 words)                       │
│                 │     Topology Diagrams]           │                                    │
├─────────────────┤                                  ├────────────────────────────────────┤
│                 │                                  │                                    │
│  Methodology    │    [FIGURE 5: EXP-01 Evidence    │  Conclusion                        │
│                 │     Log Panel / Code Block]      │                                    │
│  (5 bullets,    │                                  │  (contributions + future work,     │
│   ~78 words)    │    [FIGURE 6: Metric Callout     │   ~106 words)                      │
│                 │     Cards: 6/6, 89s, $0.27,     │                                    │
│                 │     2.2 cycles]                  │  [Optional: concluding figure]     │
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

Modern distributed systems make incident diagnosis slow and expert-dependent. This study presents a multi-agent RCA framework using LLMs to autonomously investigate microservice faults by correlating container logs, process states, and configurations in parallel across services, reducing manual SRE triage and cutting Mean Time to Resolution.

### Objective

To design, implement, and validate a multi-agent RCA framework that autonomously investigates microservice incidents via parallel specialist dispatch, iterative multi-cycle reasoning, and security-constrained container introspection, producing structured, evidence-backed RCA reports validated against real fault-injected deployments.

### Methodology

- This study employed a **systems design and empirical validation** approach to investigate LLM-driven automated incident RCA in microservice environments.
- The framework was implemented using **LangGraph**: Parent Agent (LLM orchestrator) → parallel specialist fan-out via Send API → Synthesis Agent → iterative loop or conclusion.
- Four **specialist agent types** were developed (Log, Runtime Status, Docker Specs, and Network), each self-registering at runtime with no code changes per deployment.
- **Controlled fault injection** experiments (6 designed, 6 completed) were run on a 4-service Mail App deployed on AWS EC2, covering database, web server, mail transport, DNS, and OS-level memory faults.
- **Ground-truth validation** compared the agent's identified root cause against each injected configuration change per experiment.

---

## RIGHT COLUMN

### Results

All six fault injection experiments were run end-to-end on the Mail App (AWS EC2). The agent correctly identified the root cause in every case: **6/6 accuracy, averaging 2.2 cycles, 89 seconds, and $0.27 per run** (GPT-4.1). The fastest diagnosis was EXP-04 (Postfix rate limit, 1 cycle, 45s, $0.04); the hardest was EXP-05 (DNS corruption, 3 cycles, 155s, $0.58) where symptoms appeared one layer removed from the actual fault. Single-cycle solves occurred when logs contained unambiguous error codes (EXP-02, EXP-04).

### Analysis

The experiments span five fault domains and two failure modes: total outage (EXP-02, EXP-03) and partial degradation (EXP-01, EXP-04, EXP-05, EXP-06). Partial degradation faults were harder and required more cycles on average. The iterative loop proved critical for EXP-05 (DNS): cycle 1 found symptoms in Postfix logs, but two more rounds were needed to trace them to a corrupted `/etc/resolv.conf`. At $0.04-$0.58 per run, the cost supports production use where reduced MTTR outweighs API spend.

### Conclusion

Across six fault injection experiments spanning five infrastructure domains, the framework achieved 100% root cause accuracy at $0.27 and 89 seconds per incident on average. Key contributions: LangGraph dynamic fan-out for parallel specialist dispatch, synthesis-driven iterative reasoning, a deny-first security layer, and YAML-driven profiles for code-free onboarding.

Cost stayed below $0.60 even in the worst case (3-cycle DNS fault), making the approach practical for production SRE workflows. Future work targets Kubernetes-native execution, human-in-the-loop command approval, and evaluation on incidents without pre-defined ground truth.

---

## BOTTOM BANNER

### Key Sources & Acknowledgements

**Sources (20 references — sorted by citation length, 7 columns × 3 rows):**

| Col 1 (longest) | Col 2 | Col 3 | Col 4 | Col 5 | Col 6 | Col 7 (shortest) |
|---|---|---|---|---|---|---|
| Szandala — "AIOps for Reliability," ICCS 2025 | Kholkar & Ahuja — "Guardrail Policy-as-Prompt," arXiv 2025 | Huang et al. — "Resilience of Multi-Agent," arXiv 2024 | Zhang et al. — "AgentOrchestra," arXiv 2025 | Yu et al. — "Triangle," FSE 2025 | Xu et al. — "OpenRCA," ICLR 2025 | Hong et al. — "MetaGPT," ICLR 2023 |
| Salman et al. — "HyLift 5G/6G," Computers 2025 | Ashraf & Talavera — "Autonomous Agents in SE," 2025 | Zhang et al. — "AIOps Survey," ACM Comp. Surveys 2025 | Liao et al. — "SageCopilot," IEEE TSC 2025 | Zhou et al. — "D-Bot," arXiv 2023 | Xu et al. — "DivLog," ICSE 2024 | Li et al. — "LACP," arXiv 2025 |
| Fu et al. — "MARCA," Complex & Intell. Sys. 2026 | AWS Blog — "SRE Assistants + MCP," 2025 | Bai et al. — "AOI Framework," arXiv 2025 | Chen et al. — "RCACopilot," EuroSys 2024 | Yue et al. — "MasRouter," arXiv 2025 | Zhang et al. — "FLASH," MS Research 2024 | |

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

| ID     | Injected Fault              | Domain       | Cycles | Time   | Cost   | Result    |
|--------|-----------------------------|--------------|--------|--------|--------|-----------|
| EXP-01 | Dovecot conn limit=1        | Mail (IMAP)  | 4      | 136.5s | $0.49  | Correct   |
| EXP-02 | PostgreSQL max_connections=4 | Database     | 1      | ~30s   | $0.03  | Correct   |
| EXP-03 | PHP memory_limit=10M        | Web server   | 2      | 74.8s  | $0.14  | Correct   |
| EXP-04 | Postfix rate limit=1        | Mail (SMTP)  | 1      | 44.9s  | $0.04  | Correct   |
| EXP-05 | Corrupt /etc/resolv.conf    | DNS          | 3      | 155.2s | $0.58  | Correct   |
| EXP-06 | Container memory=48MB (OOM) | OS / Memory  | 2      | 95.3s  | $0.32  | Correct   |
|        |                             | **Average**  | **2.2**| **89s**|**$0.27**| **6/6** |

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

### Figure 5: EXP-01 Evidence Log Panel (centre, styled code block)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  LOCUST FAULT OBSERVATION - EXP-01                                      │
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
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │                  │   │                  │   │                  │
│      6 / 6       │   │      89s avg     │   │     $0.27 avg    │   │   2.2 cycles     │
│                  │   │                  │   │                  │   │                  │
│   root causes    │   │   end-to-end     │   │    per run       │   │   avg to         │
│   identified     │   │   diagnosis      │   │   (GPT-4.1)     │   │   diagnose       │
│                  │   │                  │   │                  │   │                  │
└──────────────────┘   └──────────────────┘   └──────────────────┘   └──────────────────┘
```
