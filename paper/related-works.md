# Related Works — LLM-Assisted RCA Framework

> Cross-reference of all papers read in SP2026 against the proposed **Hierarchical Multi-Agent RCA Framework** (`Plan.pdf`).  
> Papers are grouped by the week they were read, then marked by relevance tier.

---

## Relevance Legend

| Tier | Meaning |
|------|---------|
| ⭐⭐⭐ | **Core** — directly cited to justify a specific architectural decision |
| ⭐⭐ | **Supporting** — validates a design pattern or component |
| ⭐ | **Background** — provides broader AIOps context |

---

## Week 1 — Jan 12th

### 1. Triangle: Empowering Incident Triage with Multi-LLM-Agents ⭐⭐
**Citation:** Yu ZH, Ma M, Feng X, Ding R, Zhang C, Li Z, Chintalapati M, Zhang X, Wang R, Bansal C, Rajmohan S. Triangle: Empowering Incident Triage with Multi-LLM-Agents. *Proceedings of the 33rd ACM International Conference on the Foundations of Software Engineering*. ACM 2025.

**Core Idea:** A multi-agent system for cloud incident triage that mimics human team collaboration. Specialized agents distill incident semantics, generate candidate on-call teams from historical data, and negotiate final routing via a voting process. Achieved 97% triage accuracy and 91% reduction in time-to-engage in a real production system serving tens of millions of users.

**Relevance to Plan:** Validates the **Orchestrator → Specialist routing** design. The voting/negotiation mechanism is analogous to the Synthesis LLM aggregating specialist findings before the Parent Agent makes a final routing or convergence decision.

---

### 2. A Survey of AIOps in the Era of Large Language Models ⭐
**Citation:** Zhang L, Jia T, Jia M, Wu Y, Liu A, Yang Y, Wu Z, Hu X, Yu P, Li Y. A Survey of AIOps in the Era of Large Language Models. *ACM Computing Surveys*. 2025.

**Core Idea:** Comprehensive analysis of how LLMs are reshaping AIOps. The central recommendation is integration — not replacement — of LLMs with existing toolchains, using smaller specialized models for high-frequency structured data and LLMs for high-level contextual reasoning.

**Relevance to Plan:** Provides the broad academic framing for the entire project. The "hybrid" philosophy (smaller fast models for Workers, large-context model for Synthesis LLM) directly mirrors the survey's key recommendation.

---

### 3. FLASH: A Workflow Automation Agent for Diagnosing Recurring Incidents ⭐⭐⭐
**Citation:** Zhang X, Mittal T, Bansal C, Wang R, Ma M, Ren Z, Huang H, Rajmohan S. FLASH: A Workflow Automation Agent for Diagnosing Recurring Incidents. 2024.  
**Org:** Microsoft Research

**Core Idea:** Introduces "Status Supervision" — decomposing the diagnostic lifecycle into four distinct states (Planning, Initialization, Execution, Completion) — and "Hindsight Integration," which uses a ToolStub to simulate past incidents for learning. Achieved 73.9% accuracy and reduced TTM from 90 min to 5.3 min across 250 real-world scenarios.

**Relevance to Plan:** Directly maps to the **Investigation Lifecycle** (Phase 1–3). The four-state model mirrors the framework's own phases. The "Hindsight Integration" concept aligns with the `known_failures` field in the YAML service configuration.

---

### 4. AIOps for Reliability: Evaluating LLMs for Automated Root Cause Analysis in Chaos Engineering ⭐⭐
**Citation:** Szandała T. AIOps for Reliability: Evaluating Large Language Models for Automated Root Cause Analysis in Chaos Engineering. *International Conference on Computational Science*. Springer 2025 (pp. 323–336).

**Core Idea:** Tests GPT-4o, Gemini 1.5, and Mistral Small against human SREs across 8 infrastructure failure scenarios. Few-shot prompting improves AI accuracy from 44–58% (zero-shot) to 60–74%, but humans still reach 82%. LLMs show a negative bias — misclassifying benign traffic surges as failures.

**Relevance to Plan:** Justifies the **Evaluator Agent (Quality Gate)**. The negative bias finding is direct evidence that an independent evaluator is required before delivering an RCA report — the Parent Agent alone cannot be trusted to self-verify.

---

### 5. Hy-LIFT: Hybrid LLM-Assisted Fault Diagnosis Framework ⭐
**Citation:** Salman AD, Zeyad AT, Jumaa SS, Raafat SM, Jasim FH, Humaidi AJ. Hybrid LLM-Assisted Fault Diagnosis Framework for 5G/6G Networks Using Real-World Logs. *Computers*. 2025 Dec 12;14(12):551.

**Core Idea:** Three-stage pipeline: expert rules generate seed labels → semi-supervised classifier trains on unlabeled logs → LLM translates results into operator-friendly narratives. Achieves 89.2% accuracy with high explainability scores.

**Relevance to Plan:** Supports the **Log Agent** and **Synthesis LLM** design. The pattern of "structured rules first, then LLM for narrative" mirrors how Worker Agents should pre-process log data before passing it upstream to the Synthesizer.

---

## Week 2 — Jan 19th

### 6. Automatic Root Cause Analysis via LLMs for Cloud Incidents (RCACopilot) ⭐⭐⭐
**Citation:** Chen Y, Xie H, Ma M, Kang Y, Gao X, Shi L, Cao Y, Gao X, Fan H, Wen M, Zeng J. Automatic root cause analysis via large language models for cloud incidents. *EuroSys 2024* (pp. 674–688).  
**Org:** Microsoft

**Core Idea:** Built and deployed an on-call RCA system at Microsoft scale using **Recursive Summarization** — the LLM first converts raw logs into narrative symptom summaries (e.g., "DB Connectivity Spike at 10:00 AM"), then uses those summaries to query a Solution Database of historical runbooks.

**Relevance to Plan:** Provides the key design rule for **Worker Agent output format**. Workers must not return raw log text — they must return structured summaries. This pre-processing step is shown to increase Planner accuracy by ~15% and is the justification for the `context_commands` field in the YAML config.

---

### 7. D-Bot: Database Diagnosis System Using Large Language Models ⭐⭐
**Citation:** Zhou X, Li G, Sun Z, Liu Z, Chen W, Wu J, Liu J, Feng R, Zeng G. D-Bot: Database Diagnosis System Using Large Language Models. *arXiv:2312.01454*. 2023.  
**Org:** Tsinghua University / VLDB

**Core Idea:** Specialized database diagnostic agent using **Tree of Thought (ToT)** reasoning. Instead of guessing immediately, it follows a decision tree: Check CPU → High → Check Slow Queries → Found. Builds its own knowledge base from offline documentation before diagnosing.

**Relevance to Plan:** Influences the **Database Agent** design and the Parent Agent's planning logic. The ToT branching model suggests the Planner should generate a decision tree of subtasks, not a flat list — branching based on Worker findings rather than waiting for a full new planning cycle.

---

### 8. OpenRCA: Can LLMs Locate the Root Cause of Software Failures? ⭐⭐⭐
**Citation:** Xu J, Zhang Q, Zhong Z, He S, Zhang C, Lin Q, Pei D, He P, Zhang D, Zhang Q. OpenRCA: Can Large Language Models Locate the Root Cause of Software Failures? *ICLR 2025*.  
**Link:** https://openreview.net/forum?id=M4qNIzQYpd

**Core Idea:** Benchmark study on real-world microservice failures (Kubernetes/Istio). LLMs are strong at generic reasoning but fail at **Topological Reasoning** — they cannot deduce service call chains without an explicit dependency graph.

**Relevance to Plan:** Primary justification for the **YAML Service Configuration as Source of Truth**. Without explicit topology (which service calls which), the Planner hallucinates dependencies. The `dependencies` field in the YAML directly mitigates the hallucination risk documented here.

---

### 9. Autonomous Agents in Software Engineering: A Multi-Agent LLM Approach ⭐⭐⭐
**Citation:** Ashraf B, Talavera G. Autonomous Agents in Software Engineering: A Multi-Agent LLM Approach. ResearchGate.

**Core Idea:** Empirical comparison of Multi-Agent (specialist) vs. Single "Super Agent" (generalist) setups. The specialist model consistently outperforms because context switching between domains degrades LLM performance.

**Relevance to Plan:** Core justification for the **Specialist Agent design** (Network, Memory, Log, Application, Database, Cache, OS agents). A single worker that tries to know Redis *and* Postgres *and* Nginx will confuse parameters. Each Worker is intentionally "dumb and narrow."

---

## Week 3 — Jan 29th

### 10. AgentOrchestra: Orchestrating Hierarchical Multi-Agent Intelligence ⭐⭐⭐
**Citation:** Zhang W, Zeng L, Xiao Y, Li Y, Zhao Y, Cui C, Liu Y, An B. AgentOrchestra: Orchestrating Hierarchical Multi-Agent Intelligence with the Tool-Environment-Agent (TEA) Protocol. *arXiv*, Cornell University.  
**Link:** https://ui.adsabs.harvard.edu/abs/2025arXiv250612508Z/abstract

**Core Idea:** Introduces the TEA (Tool-Environment-Agent) protocol — a central planner decomposes complex objectives into sub-tasks delegated to specialized sub-agents. Separating Planning from Execution significantly reduces error rates in long-horizon tasks.

**Relevance to Plan:** Direct validation of the **Parent Agent (Orchestrator) + Specialist Workers** topology. Justifies why the Parent Agent never executes tools directly and only delegates — this separation is shown to reduce error rates in complex, long-horizon workflows.

---

### 11. MA-RCA: Leveraging Multi-Agent Framework for Root Cause Analysis ⭐⭐⭐
**Citation:** Fu F, Ding H, Qin Y, Yu J, Xu D. Leveraging Multi-Agent Framework for Root Cause Analysis. *Complex & Intelligent Systems*. 2026 Jan;12(1):4.  
**Link:** https://link.springer.com/article/10.1007/s40747-025-02096-0

**Core Idea:** Explicitly separates RCA into "Retrieval" and "Validation" roles. Single-agent RCA fails due to context-switching. The multi-agent approach with isolated retrieval and validation achieves 95.8% accuracy.

**Relevance to Plan:** Empirical foundation for separating **Worker Agents (Retrieval)** from the **Synthesis LLM + Parent Agent (Validation)**. Provides quantitative evidence against feeding all logs into a single large context window.

---

### 12. MasRouter: Learning to Route LLMs for Multi-Agent Systems ⭐⭐
**Citation:** Yue Y, Zhang G, Liu B, Wan G, Wang K, Cheng D, Qi Y. MasRouter: Learning to Route LLMs for Multi-Agent Systems. *arXiv:2502.11133*. 2025.  
**Link (Repo):** https://github.com/yanweiyue/masrouter

**Core Idea:** A controller network dynamically decides which agent and which LLM backbone should handle a query based on complexity — routing simple issues to cheaper/smaller models, complex ones to larger models.

**Relevance to Plan:** Theoretical foundation for the **Intelligent Router** node. Rather than hard-coded rules ("if 'redis' in text → Redis Agent"), the router can learn to dispatch based on incident complexity, balancing cost and accuracy.

---

### 13. AOI: Multi-Agent Collaborative Framework for Intelligent IT Operations ⭐⭐⭐
**Citation:** Bai Z, Ge E, Hao J. Multi-Agent Collaborative Framework for Intelligent IT Operations: An AOI System with Context-Aware Compression and Dynamic Task Scheduling. *arXiv:2512.13956*. 2025.

**Core Idea:** Uses a "Probe Agent" (data collection) and "Observer Agent" (high-level decisions), with a **Context Compressor** that prevents the Observer from being overwhelmed by raw outputs. Sub-tasks return compressed summaries, not raw data.

**Relevance to Plan:** Validates the connection between **Worker Agents → Synthesis LLM**. Workers must compress findings ("Redis latency is high" vs. 1000 log lines) before passing upstream, ensuring the Synthesis LLM can reason without information overload.

---

### 14. MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework ⭐⭐⭐
**Citation:** Hong S, Zhuge M, Chen J, et al. MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework. *ICLR 2024*.  
**Link (Repo):** https://github.com/geekan/MetaGPT

**Core Idea:** Treats agents as employees with job descriptions — assigns each a **Standard Operating Procedure (SOP)**. Transforms abstract goals into concrete structured outputs through an assembly-line model.

**Relevance to Plan:** Central to the **Specialist Agent implementation**. Each Worker Agent is not a generic LLM — it is an LLM equipped with a specific SOP checklist (e.g., the Redis Agent runs a defined sequence: check memory → check eviction → check replication). Ensures consistency and reduces hallucinations.

---

### 15. SageCopilot: An LLM-Empowered Autonomous Agent for Data Science as a Service ⭐⭐
**Citation:** Liao Y, Bian J, Yun Y, et al. SageCopilot: an LLM-empowered Autonomous Agent for Data Science as a Service. *IEEE Transactions on Services Computing*. 2025.

**Core Idea:** Two-phase architecture (Offline preparation + Online execution) with a mandatory "checking" phase where all results are verified before delivery. Results are synthesized into a coherent narrative rather than raw concatenation.

**Relevance to Plan:** Validates the **Evaluator Agent** and the final **Synthesis → Report** loop. The Parent Agent must act as a reviewer, synthesizing and cross-verifying sub-task results into a coherent narrative — not simply concatenating Worker outputs.

---

## Week 4 — Feb 5th

### 16. LLM Agent Communication Protocol (LACP): A Telecom-Inspired Protocol ⭐⭐
**Citation:** Li X, Liu M, Yuen C. LLM Agent Communication Protocol (LACP) Requires Urgent Standardization: A Telecom-Inspired Protocol is Necessary. *arXiv:2510.13821*. 2025.  
**Link:** https://arxiv.org/abs/2510.13821

**Core Idea:** Argues unstructured text/JSON is insufficient for robust agent collaboration. Proposes a telecom-inspired "Plan-Act-Observe" handshake with Semantic, Transactional, and Transport layers — agents explicitly acknowledge tasks and validate outputs before proceeding, preventing "silent failures."

**Relevance to Plan:** Influences **inter-agent message passing** between the Planner and Worker Agents. A Worker that fails to execute an SSH command should return a structured error code, not a hallucinated success message. This "handshake" logic maps to LangGraph's message passing between nodes.

---

### 17. On the Resilience of LLM-Based Multi-Agent Collaboration with Faulty Agents ⭐⭐⭐
**Citation:** Huang JT, Zhou J, Jin T, Zhou X, Chen Z, Wang W, Yuan Y, Lyu MR, Sap M. On the Resilience of LLM-Based Multi-Agent Collaboration with Faulty Agents. *arXiv:2408.00989*. 2024.  
**Link:** https://arxiv.org/abs/2408.00989

**Core Idea:** Stress-tested multi-agent topologies by injecting faulty (hallucinating/non-responsive) agents. **Hierarchical (Hub-and-Spoke)** topologies maintained system integrity 95% of the time; flat (Peer-to-Peer) structures often collapsed as errors propagated between workers.

**Relevance to Plan:** Direct justification for prohibiting **Worker-to-Worker communication**. The Parent Agent is the strict hub — a confused DB Agent cannot mislead the Network Agent without central oversight. This is the key security and reliability argument for the Hub-and-Spoke topology.

---

### 18. Building Multi-Agent SRE Assistants with AgentCore & MCP (AWS) ⭐⭐
**Citation:** AWS Architecture Blog. Building Scalable SRE Assistants using the Model Context Protocol. 2025.  
**Org:** AWS / Anthropic

**Core Idea:** Details the shift toward **Model Context Protocol (MCP)** for standardizing agent-infrastructure interfaces. Specialist Agents expose capabilities (log reading, metric fetching) as MCP servers, allowing any LLM to use them without custom API wrappers.

**Relevance to Plan:** Blueprint for **Phase 2 Resident Doctor / Worker Agent extensibility**. Instead of writing custom API wrappers for every tool, Worker Agents are structured as MCP servers — the Planner can dynamically discover available tools on a VM, making the system future-proof and extensible.

---

## Week 5 — Feb 12th

### 19. SafeOps: Bounding the Action Space of Autonomous LLM Agents ⭐⭐⭐
**Citation:** Kholkar G, Ahuja R. The AI Agent Code of Conduct: Automated Guardrail Policy-as-Prompt Synthesis. *arXiv:2509.23994*. 2025.  
**Link:** https://ui.adsabs.harvard.edu/abs/2025arXiv250923994K/abstract

**Core Idea:** Applies the **Principle of Least Privilege** to LLM agents. Strict security policies are compiled into runtime guardrails, dynamically restricting an agent's action space based on environment context and authorization level.

**Relevance to Plan:** Academic foundation for **Worker Agent security design**. Justifies initializing agents in a "Read-Only Default" state. LangGraph's `interrupt` functionality is the implementation mechanism — agents can autonomously observe, but state-mutating commands require explicit human authorization. Directly supports the `Least Privilege` and `Command Allowlisting` security requirements.

---

### 20. DivLog: Log Parsing with Prompt-Enhanced In-Context Learning ⭐⭐⭐
**Citation:** Xu J, Yang R, Huo Y, Zhang C, He P. DivLog: Log Parsing with Prompt Enhanced In-Context Learning. *ICSE 2024* (pp. 1–12).  
**Link:** https://dl.acm.org/doi/abs/10.1145/3597503.3639155

**Core Idea:** Addresses the challenge of massive, repetitive logs exceeding LLM context limits. DivLog filters and parses raw logs into structured templates — selecting diverse, representative sequences rather than dumping raw files — reducing token usage while improving anomaly detection.

**Relevance to Plan:** Validates the **"Thin Sidecar" Worker Agent** concept. Workers must perform **local log parsing** before transmission — extracting only unique error templates and anomalies to send to the Aggregator. Prevents gigabytes of raw SSH output from overwhelming the Synthesis LLM's context window.

---

## Summary Table

| # | Paper | Tier | Architectural Component |
|---|-------|------|------------------------|
| 1 | Triangle | ⭐⭐ | Orchestrator → Specialist routing |
| 2 | AIOps Survey | ⭐ | General framing (hybrid model) |
| 3 | FLASH | ⭐⭐⭐ | Investigation Lifecycle, YAML `known_failures` |
| 4 | AIOps for Reliability | ⭐⭐ | Evaluator Agent (negative bias finding) |
| 5 | Hy-LIFT | ⭐ | Log Agent, Synthesis LLM |
| 6 | RCACopilot (EuroSys) | ⭐⭐⭐ | Worker output format, `context_commands` |
| 7 | D-Bot | ⭐⭐ | Database Agent, Tree-of-Thought Planner |
| 8 | OpenRCA | ⭐⭐⭐ | YAML topology / Source of Truth |
| 9 | Autonomous Agents in SE | ⭐⭐⭐ | Specialist Agent design (narrow & focused) |
| 10 | AgentOrchestra | ⭐⭐⭐ | Parent Agent never executes tools directly |
| 11 | MA-RCA | ⭐⭐⭐ | Workers = Retrieval, Synthesizer = Validation |
| 12 | MasRouter | ⭐⭐ | Intelligent Router node |
| 13 | AOI | ⭐⭐⭐ | Worker output compression before Synthesis LLM |
| 14 | MetaGPT | ⭐⭐⭐ | SOP-based Specialist Agent implementation |
| 15 | SageCopilot | ⭐⭐ | Evaluator + Report synthesis |
| 16 | LACP | ⭐⭐ | Structured inter-agent message passing |
| 17 | Resilience of MAS | ⭐⭐⭐ | Hub-and-Spoke topology, no Worker-to-Worker comms |
| 18 | AWS MCP SRE | ⭐⭐ | Phase 2 extensibility via MCP |
| 19 | SafeOps | ⭐⭐⭐ | Read-Only Default, Least Privilege, `interrupt` |
| 20 | DivLog | ⭐⭐⭐ | Local log parsing by Worker Agents (Thin Sidecar) |
