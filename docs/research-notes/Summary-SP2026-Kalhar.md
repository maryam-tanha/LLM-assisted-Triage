# Summary

**Summary**

**Week of Jan 12th**

Paper: 1  
Triangle: Empowering Incident Triage with Multi-LLM-Agents

Yu ZH, Ma M, Feng X, Ding R, Zhang C, Li Z, Chintalapati M, Zhang X, Wang R, Bansal C, Rajmohan S. Triangle: Empowering Incident Triage with Multi-LLM-Agents. InProceedings of the 33rd ACM International Conference on the Foundations of Software Engineering. ACM 2025\. 

Summery:

This is a multi-agent system designed to automate and optimize incident triage in large-scale cloud environments by mimicking human collaboration to address challenges like semantic ambiguity and decentralized domain knowledge. The framework employs specialized agents to distill incident semantics, generate candidate teams based on historical data and documentation, and negotiate final assignments through a voting process that incorporates automated retrieval of monitoring logs. Deployed in a real-world global cloud production system serving tens of millions of users, Triangle significantly outperformed existing methods by achieving up to 97% triage accuracy and reducing the time required to engage responsible teams by as much as 91%, demonstrating its capability to handle complex, dynamic service interruptions efficiently.

Paper: 2  
A Survey of AIOps in the Era of Large Language Models

Zhang L, Jia T, Jia M, Wu Y, Liu A, Yang Y, Wu Z, Hu X, Yu P, Li Y. A Survey of AIOps in the Era of Large Language Models. ACM Computing Surveys. 2025\.

This survey comprehensively analyzes the transformative impact of Large Language Models (LLMs) on Artificial Intelligence for IT Operations (AIOps), detailing how their generative capabilities are reshaping failure management methodologies. The authors systematically review the field through four key research questions, covering the utilization of diverse data sources, the evolution of AIOps tasks, the development of specific LLM-based methods, and the adaptation of evaluation frameworks. A central theme of the research is the strategic necessity of integrating LLMs with existing AIOps toolchains rather than replacing them entirely, advocating for a collaborative model where specialized smaller models handle high-frequency structured data while LLMs provide high-level contextual reasoning and explanation. The paper concludes that while LLMs offer promising advancements for software reliability and automated remediation, future research must address critical challenges regarding cost-effectiveness, inference latency, and the seamless interoperability of hybrid systems to achieve scalable real-world implementation.

Paper 3:  
FLASH: A Workflow Automation Agent for Diagnosing Recurring Incidents

Zhang X, Mittal T, Bansal C, Wang R, Ma M, Ren Z, Huang H, Rajmohan S. FLASH: A Workflow Automation Agent for Diagnosing Recurring Incidents \[Internet\]. 2024

Summery:  
FLASH is a workflow automation agent developed by Microsoft Research designed to mitigate the low reliability and cumulative error accumulation often seen when LLMs attempt to diagnose recurring cloud incidents. The system distinguishes itself through two core mechanisms: "Status Supervision," which decomposes the diagnostic lifecycle into four distinct states (Planning, Initialization, Execution, and Completion) to minimize complexity, and "Hindsight Integration," which uses a specialized "ToolStub" to simulate past incidents, allowing the agent to learn from validated historical failures. In comparative testing against state-of-the-art frameworks like TaskWeaver and ReAct across 250 real-world scenarios, FLASH achieved a superior accuracy of 73.9% and reduced the Time to Mitigate (TTM) from a 90-minute baseline to just 5.3 minutes. However, the research notes that the quality of existing Troubleshooting Guides (TSGs) remains a significant bottleneck, with only 8.5% of documents being immediately ready for automation without revision.

Paper 4:  
AIOps for Reliability: Evaluating Large Language Models for Automated Root Cause Analysis in Chaos Engineering

SzandaÅ‚a T. Aiops for reliability: Evaluating large language models for automated root cause analysis in chaos engineering. InInternational Conference on Computational Science 2025 Jul 6 (pp. 323-336). Cham: Springer Nature Switzerland.

Summery  
This research evaluates the potential of Large Language Models to automate Root Cause Analysis within a controlled chaos engineering environment aimed at reducing Site Reliability Engineer burnout. By testing GPT-4o, Gemini 1.5, and Mistral Small against human experts across eight distinct infrastructure scenarios, the study finds that while few-shot prompting significantly improves AI performance from a zero-shot baseline of 44-58% to 60-74%, human engineers still maintain a superior accuracy of 82%. A critical finding is the prevalence of a negative bias in LLMs, which causes them to misclassify benign traffic surges as system failures, whereas humans correctly identify them as non-incidents. Ultimately, the paper concludes that current LLMs function best as assistive co-pilots rather than standalone replacements, necessitating human oversight and sophisticated prompt engineering to mitigate false alarms and ensure accurate diagnostics in production environments.

Paper 5:  
Hy-LIFT: Hybrid LLM-Assisted Fault Diagnosis Framework

Salman AD, Zeyad AT, Jumaa SS, Raafat SM, Jasim FH, Humaidi AJ. Hybrid LLM-Assisted Fault Diagnosis Framework for 5G/6G Networks Using Real-World Logs. Computers. 2025 Dec 12;14(12):551.

Summery  
Hy-LIFT is a novel hybrid framework designed to automate fault diagnosis in 5G/6G networks by integrating interpretable rule-based logic with semi-supervised learning and Large Language Models (LLMs). Addressing the limitations of brittle rule systems and data-hungry machine learning models, the framework utilizes a three-stage pipeline where expert rules first generate high-precision seed labels that are subsequently used to train a semi-supervised classifier on vast amounts of unlabeled logs. The final stage employs an LLM to translate complex technical data into operator-friendly diagnostic narratives and identify novel fault patterns, allowing the system to achieve an overall accuracy of 89.2% on real-world operator logs while significantly outperforming traditional methods in both data efficiency and engineer-rated explainability.

**Week of Jan 19th**

Paper 1:  
Automatic root cause analysis via large language models for cloud incidents

Chen Y, Xie H, Ma M, Kang Y, Gao X, Shi L, Cao Y, Gao X, Fan H, Wen M, Zeng J. Automatic root cause analysis via large language models for cloud incidents. InProceedings of the Nineteenth European Conference on Computer Systems 2024 Apr 22 (pp. 674-688).

**Authors/Org: Microsoft (EuroSys 2024\)**  
The Core Idea: They built a system similar to the proposal to handle on-call incidents at Microsoft. Instead of just "asking the LLM," they use a Recursive Summarization technique.They feed the LLM raw logs, ask it to summarize the "symptoms," and then use those symptoms to query a "Solution Database" (historical runbooks).

Key Insight	  
Don't dump raw logs into the RCA Node. RCACopilot proves that "pre-processing" logs into narrative summaries (e.g., converting 100 lines of Connection Refused into a single sentence "DB Connectivity Spike at 10:00 AM") increases the Planner's accuracy by \~15%. Your Worker Agents should output these summaries, not raw text.

Is the above paper the most relevant to our project? 

Paper 2:

D-Bot: Database Diagnosis System using Large Language Models

Zhou X, Li G, Sun Z, Liu Z, Chen W, Wu J, Liu J, Feng R, Zeng G. D-bot: Database diagnosis system using large language models. arXiv preprint arXiv:2312.01454. 2023 Dec 3\.

Authors/Org: Tsinghua University (VLDB Endowment)  
The Core Idea: A specialized agent for databases. It uses a Tree of Thought (ToT) reasoning process. Instead of guessing the error immediately, it follows a tree: Check CPU \-\> High \-\> Check Slow Queries \-\> Found. It also extracts knowledge from documentation (offline) to build its own "knowledge base" before diagnosing.

Key Insight for the Project:  
Use Tree-of-Thought for the Planner. Your Planner shouldn't just generate a flat list of tasks. It should generate a decision tree. If Task A (Check CPU) returns "Normal", the Planner should have a branch ready to switch to Task B (Check Network), rather than waiting for a whole new planning cycle.

Paper 3:  
OpenRCA: Can large language models locate the root cause of software failures?

Xu J, Zhang Q, Zhong Z, He S, Zhang C, Lin Q, Pei D, He P, Zhang D, Zhang Q. OpenRCA: Can large language models locate the root cause of software failures?. InThe Thirteenth International Conference on Learning Representations 2025\.

Authors/Org: Middleware Lab (OpenReview Benchmark)

The Core Idea: A benchmark study testing LLMs on real-world microservices failures (Kubernetes/Istio). They found that LLMs are great at Generic Reasoning (understanding why a DB might fail) but terrible at Topology Reasoning (understanding that Service A calls Service B).

Key Insight for the Project:

Ground the Topology. The paper suggests that providing the LLM with a strict Service Dependency Graph  is non-negotiable. Without the YAML explicitly stating "Checkout Service depends on Redis," the Agent will often hallucinate that the Checkout Service talks directly to the Database.

Paper 4:   
Autonomous Agents in Software Engineering: A Multi-Agent LLM Approach

Ashraf B, Talavera G. Autonomous Agents in Software Engineering: A Multi-Agent LLM Approach.

Authors/Org: ResearchGate (Multiple Authors)  
The Core Idea: This paper explores the "Specialist" model vs. the "Generalist" model. They found that a Multi-Agent setup (one agent for coding, one for testing, one for reviewing) outperformed a single "Super Agent" because context switching degrades LLM performance.

Key Insight for the Project:  
Keep Workers "Dumb" and Specialized. Do not make one "Super Worker" that knows how to check Nginx and Postgres and Redis. Create distinct tools or sub-prompts for each. If a Worker tries to know everything, it will confuse parameters (e.g., trying to run SQL commands on a Redis instance).

Does any of the papers (including the ones from last week)  have a public github repo? If yes, add the link below the paper.

You can read this short paper as well: [https://dl.acm.org/doi/10.1145/3696630.3731432](https://dl.acm.org/doi/10.1145/3696630.3731432)

Next week: Read another 6 papers  
Look for open-source code and data  
What kind of method do you think is better?

# 29th Jan

**29th Jan**

### **1\. AgentOrchestra: Orchestrating Hierarchical Multi-Agent Intelligence**

* **Citation:** Zhang W, Zeng L, Xiao Y, Li Y, Zhao Y, Cui C, Liu Y, An B. AgentOrchestra: Orchestrating hierarchical multi-agent intelligence with the Tool-Environment-Agent (TEA) protocol.   
* **Authors/Org:** arXiv / Cornell University (Zhang et al.)  
* **The Core Idea:** The authors introduce the "TEA" (Tool-Environment-Agent) protocol, which uses a central planner to decompose complex objectives into sub-tasks. Their research demonstrates that assigning specialized sub-agents (like a "Browser Agent" or "Data Analyzer") is significantly more effective for long-horizon tasks than relying on a single model.  
* **Relevance to My Proposed Architecture:** This paper validates my design decision to separate the **"Big Mind"** from the **"Sub-Tasks."** It provides evidence that separating the high-level "Planning" phase from the granular "Execution" phase reduces error rates in complex workflows. I will use this to justify why my "Big Mind" does not execute tools directly but instead delegates to specialists.  
* **Link:** [PDF via arXiv](https://arxiv.org/abs/2506.12508) *,* [https://ui.adsabs.harvard.edu/abs/2025arXiv250612508Z/abstract](https://ui.adsabs.harvard.edu/abs/2025arXiv250612508Z/abstract)

### **2\. MA-RCA: Leveraging Multi-Agent Framework for Root Cause Analysis**

* **Citation:** Fu F, Ding H, Qin Y, Yu J, Xu D. Leveraging multi-agent framework for root cause analysis. Complex & Intelligent Systems. 2026 Jan;12(1):4.  
* **Authors/Org:** ResearchGate (Various)  
* **The Core Idea:** This framework is designed specifically for IT operations, employing distinct agents for "Hypothesis Generation," "Information Retrieval," and "Validation." The study argues that single-agent Root Cause Analysis (RCA) often fails due to hallucinations when the model is forced to switch contexts between logs and metrics.  
* **Relevance to My Proposed Architecture:** I am adopting this "Retrieval vs. Validation" split for my **"Investigate..."** nodes. This research supports my decision to have "Retrieval Agents" (my Sub-Tasks) that strictly fetch data, while a separate "Validation Agent" (my Bigger Mind) analyzes that data. This ensures my system minimizes context-switching errors.  
* **Link:** [PDF via ResearchGate](https://www.researchgate.net/publication/397344105_Leveraging_multi-agent_framework_for_root_cause_analysis)

### **3\. MasRouter: Learning to Route LLMs for Multi-Agent System**

* **Citation:** Yue Y, Zhang G, Liu B, Wan G, Wang K, Cheng D, Qi Y. Masrouter: Learning to route llms for multi-agent systems. arXiv preprint arXiv:2502.11133. 2025 Feb 16\.  
* **Authors/Org:** ACL Anthology (Yanwei Yue et al.)  
* **The Core Idea:** This paper introduces "MASR" (Multi-Agent System Routing), a framework that dynamically decides which agent-and which LLM backbone-should handle a query. It utilizes a "controller network" to assign roles based on the complexity of the query.  
* **Relevance to My Proposed Architecture:** This serves as the theoretical foundation for my **"Router"** node. Instead of using hard-coded rules (e.g., "if 'redis' in text, go to Redis agent"), I plan to implement a router that *learns* to delegate based on incident complexity. This aligns with the paper's findings on balancing cost and accuracy by routing simple issues to smaller models.  
* **Link:** [PDF via ACL Anthology](https://aclanthology.org/2025.acl-long.757/)  
* **Repo:**[https://github.com/yanweiyue/masrouter](https://github.com/yanweiyue/masrouter)

### **4\. AOI: Multi-Agent Collaborative Framework for Intelligent IT Operations**

* **Citation:** Bai Z, Ge E, Hao J. Multi-Agent Collaborative Framework for Intelligent IT Operations: An AOI System with Context-Aware Compression and Dynamic Task Scheduling. arXiv preprint arXiv:2512.13956. 2025 Dec 15\.  
* **Authors/Org:** IEEE Access / arXiv (AOI Team)  
* **The Core Idea:** The AOI (AI-Oriented Operations) system uses a "Probe Agent" to gather data and an "Observer Agent" to make high-level decisions. Crucially, it introduces a "Context Compressor" to ensure the Observer isn't overwhelmed by raw logs.  
* **Relevance to My Proposed Architecture:** This validates the connection between my **"Run Sub Tasks"** and **"Bigger Mind"** nodes. Following this research, I will ensure my Sub-Tasks do not just return raw text but instead "compress" or summarize findings (e.g., "Redis latency is high," rather than 1000 lines of logs) so the "Bigger Mind" can reason effectively without information overload.  
* **Link:** [PDF via arXiv](https://arxiv.org/abs/2512.13956)  
* **Repo:** *Repository not publicly listed.*

### **5\. MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework**

* **Citation:** Hong S, Zhuge M, Chen J, Zheng X, Cheng Y, Wang J, Zhang C, Wang Z, Yau SK, Lin Z, Zhou L. MetaGPT: Meta programming for a multi-agent collaborative framework. InThe twelfth international conference on learning representations 2023 Aug 1\.  
* **Authors/Org:** DeepWisdom / KAUST / DeepSense AI  
* **The Core Idea:** MetaGPT treats agents like employees with specific job descriptions (e.g., Product Manager, Engineer) by assigning them "Standard Operating Procedures" (SOPs). This transforms abstract requirements into concrete outputs through a structured assembly line.  
* **Relevance to My Proposed Architecture:** This paper is central to how I will implement my **"Investigate..."** nodes. I will write specific SOPs for each worker. For example, my "Redis Investigator" won't just be a generic LLM; it will be an LLM equipped with a specific checklist of commands to run, ensuring consistency and reducing hallucinations.  
* **Link:** [PDF via arXiv](https://arxiv.org/abs/2308.00352)  
* **Repo:** [https://github.com/geekan/MetaGPT](https://github.com/geekan/MetaGPT)

### 

### **6\. SageCopilot: an LLM-empowered Autonomous Agent for Data Science as a Service**

* **Citation:** Liao Y, Bian J, Yun Y, Wang S, Zhang Y, Chu J, Wang T, Li Y, Li X, Ji S, Xiong H. SageCopilot: an LLM-empowered Autonomous Agent for Data Science as a Service. IEEE Transactions on Services Computing. 2025 Nov 21\.  
* **Authors/Org:** IEEE (Yuan Liao et al.)  
* **The Core Idea:** SageCopilot utilizes a two-phase architecture: an "Offline" phase to prepare tools and demonstrations, and an "Online" phase to refine user inputs and execute scripts. It emphasizes a strict "checking" phase where results are verified before being shown to the user.  
* **Relevance to My Proposed Architecture:** This validates the final stage of my pipeline, specifically the **"Bigger Mind" â†’ "Report Generated"** loop. I will design the "Bigger Mind" to act as a reviewer that synthesizes and verifies the sub-task results into a coherent narrative, rather than simply concatenating the outputs.  
* **Link:** [PDF via IEEE](https://ieeexplore.ieee.org/abstract/document/11264326)


### **Proposed Architecture: Hierarchical Multi-Agent System for Incident Diagnosis**

**System Overview**

We propose a Hierarchical Multi-Agent System (HMAS) designed to automate the triage and diagnosis of IT incidents. Unlike traditional flat architectures, this system utilizes an Orchestrator-Worker topology to separate high-level reasoning from low-level execution. The core innovation is the integration of a Baseline Comparison Engine, which grounds LLM analysis in factual "healthy state" data to minimize hallucinations.

**Core Components**

1. **Orchestrator** ("Big Mind"): The central planner that decomposes the incident trigger into a high-level investigation strategy. It maintains the global context of the incident but delegates specific actions.  
2. **Intelligent Router**: A dynamic dispatch layer that analyzes the Orchestrator's strategy and routes tasks to the most appropriate specialist, ensuring efficient resource utilization.  
3. **Specialist Worker Layer** ("Sub-Tasks"): A suite of "narrow" agents, each equipped with strict Standard Operating Procedures (SOPs) for specific technologies (e.g., Redis, Nginx, Postgres). These agents focus solely on data retrieval and state verification, preventing context-switching errors.  
4. **Synthesizer** ("Bigger Mind"): The validation and reasoning engine. It aggregates outputs from the Specialist Workers, compares live metrics against the historical Baseline Database, and synthesizes a coherent Root Cause Analysis (RCA) report with actionable escalation paths.  
   

**System Flowchart**

# 5th Feb

1. **MA-RCA: Leveraging Multi-Agent Framework for Root Cause Analysis**  
   * **Citation:** Fu F, Ding H, Qin Y, Yu J, Xu D. Leveraging multi-agent framework for root cause analysis. Complex & Intelligent Systems. 2026 Jan;12(1):4.  
   * **Authors/Org:** Springer Professional / ResearchGate (2025)  
   * **The Core Idea:** The authors propose a framework that explicitly divides the RCA process into distinct "Retrieval" and "Validation" roles. Their experiments show that single-agent systems suffer from high error rates due to "context-switching," whereas a specialized multi-agent approach achieves significantly higher accuracy (95.8%) by isolating the retrieval of runbooks from the generation of hypotheses.  
   * **Relevance to My Proposed Architecture:** This paper directly supports my decision to separate the "Planner" node from the "Worker" nodes in my LangGraph design. It provides the empirical evidence needed to justify why I am not simply feeding all logs into a single large context window, but rather using specialized workers to retrieve and validate specific data points before aggregation.  
   * **Link:** https://link.springer.com/article/10.1007/s40747-025-02096-0  
       
2. **LLM Agent Communication Protocol (LACP): A Telecom-Inspired Protocol**  
   * **Citation:** Li X, Liu M, Yuen C. LLM Agent Communication Protocol (LACP) Requires Urgent Standardization: A Telecom-Inspired Protocol is Necessary. arXiv preprint arXiv:2510.13821. 2025 Sep 26\.  
   * **Authors/Org:** arXiv (2025)  
   * **The Core Idea:** This paper argues that unstructured text or simple JSON is insufficient for robust agent collaboration. It introduces a telecom-inspired "Plan-Act-Observe" handshake protocol consisting of Semantic, Transactional, and Transport layers. This ensures that agents explicitly acknowledge tasks and validate outputs before moving to the next step, preventing "silent failures."  
   * **Relevance to My Proposed Architecture:** This influences the design of my internal message passing between the Planner and the Resident Doctor. I will adopt this "handshake" logic to ensure that if a Worker Agent on a VM fails to execute a command, the Planner receives a structured error code rather than a hallucinated success message.  
   * **Link:** [https://arxiv.org/abs/2510.13821](https://arxiv.org/abs/2510.13821)  
   *   
3. **On the Resilience of LLM-Based Multi-Agent Collaboration with Faulty Agents**  
   * **Citation:** Huang JT, Zhou J, Jin T, Zhou X, Chen Z, Wang W, Yuan Y, Lyu MR, Sap M. On the resilience of llm-based multi-agent collaboration with faulty agents. arXiv preprint arXiv:2408.00989. 2024 Aug 2..  
   * **Authors/Org:** OpenReview (2025)  
   * **The Core Idea:** The researchers conducted stress tests by injecting "faulty" (hallucinating or non-responsive) agents into various topological structures. They found that Hierarchical (Hub-and-Spoke) topologies maintained system integrity 95% of the time, whereas Flat (Peer-to-Peer) structures often collapsed as errors propagated unchecked between workers.  
   * **Relevance to My Proposed Architecture:** This validates my strict "Hub-and-Spoke" topology where the Planner acts as the central hub. I will use this research to defend my choice of prohibiting direct "Worker-to-Worker" communication, ensuring that a confused agent on the database server cannot mislead the agent on the web server without central oversight.  
   * **Link:** https://arxiv.org/abs/2408.00989  
4. **Building Multi-Agent SRE Assistants with AgentCore & MCP**  
   * **Citation:** AWS Architecture Blog. Building Scalable SRE Assistants using the Model Context Protocol.  
   * **Authors/Org:** AWS / Anthropic (2025)  
   * **The Core Idea:** This technical report details the shift toward the Model Context Protocol (MCP) for standardizing how agents interface with infrastructure. It demonstrates how "Specialist Agents" can expose capabilities (like log reading or metric fetching) via standardized MCP servers, allowing any LLM to utilize them without custom API wrappers.  
   * **Relevance to My Proposed Architecture:** This serves as the blueprint for my Phase 2 "Resident Doctor." Instead of writing custom API wrappers for every tool, I will structure my internal agents as MCP servers. This allows my central Planner to dynamically discover available tools on a VM, making the system extensible and future-proof.  
   * **Link:** [AWS Architecture Blog](https://aws.amazon.com/blogs/architecture/) / [Model Context Protocol](https://modelcontextprotocol.io)

# 12th Feb

**OpenRCA: Can Large Language Models Locate the Root Cause of Software Failures?**

* Xu J, Zhang Q, Zhong Z, He S, Zhang C, Lin Q, Pei D, He P, Zhang D, Zhang Q. OpenRCA: Can large language models locate the root cause of software failures?. InThe Thirteenth International Conference on Learning Representations 2025\.  
  * **The Core Idea:** This extensive benchmark study tested LLMs on real-world microservices failures (e.g., in Kubernetes and Istio environments). The researchers discovered that while LLMs excel at general reasoning (e.g., knowing *why* a database connection fails), they perform poorly at "Topological Reasoning"- understanding the specific call chains between microservices unless explicitly provided with a dependency graph.  
  * **Relevance to My Proposed Architecture:** This paper is the primary justification for my "Source of Truth" YAML configuration. It proves that I cannot simply rely on the LLM to deduce the infrastructure layout from logs alone. By feeding the Planner a structured YAML topology mapping out which services live on which VMs, I am directly mitigating the topological hallucination risks identified in this study.  
  * **Link:** https://openreview.net/forum?id=M4qNIzQYpd

**SafeOps: Bounding the Action Space of Autonomous LLM Agents in Production Environments**

* **Citation:** Kholkar G, Ahuja R. The AI Agent Code of Conduct: Automated Guardrail Policy-as-Prompt Synthesis. arXiv e-prints. 2025 Sep:arXiv-2509.  
  * **The Core Idea:** This paper addresses the critical need to bound the action space of autonomous agents. The authors propose applying the "Principle of Least Privilege" directly to LLM applications. They demonstrate a framework that compiles strict security policies into runtime guardrails, ensuring that an agent's available action space is dynamically restricted based on the context of the environment and the authorization level of the task.  
  * **Relevance to My Proposed Architecture:** This research provides the academic foundation for the security design of my Worker Agents. It justifies my approach of initializing agents in a strict "Read-Only Default" state. By implementing LangGraph's interrupt functionality, the system aligns with the principle of least privilege \- the agent can autonomously observe, but the action space for state-mutating commands requires explicit authorization.  
  * **Link:** https://ui.adsabs.harvard.edu/abs/2025arXiv250923994K/abstract

**DivLog: Log Parsing with Prompt Enhanced In-Context Learning**

* **Citation:** Xu J, Yang R, Huo Y, Zhang C, He P. Divlog: Log parsing with prompt enhanced in-context learning. InProceedings of the IEEE/ACM 46th International Conference on Software Engineering 2024 Apr 12 (pp. 1-12).  
* **The Core Idea:** This paper addresses the challenge of feeding massive, repetitive infrastructure logs into LLMs, which typically exceed context limits and degrade reasoning. DivLog introduces a mechanism to filter and parse raw logs into structured templates before inference. By selecting diverse, representative log sequences rather than dumping raw files, it reduces token usage while significantly improving anomaly detection accuracy.  
* **Relevance to My Proposed Architecture:** This perfectly validates the "Thin Sidecar" Worker Agent concept in Phase 2\. Instead of transferring gigabytes of raw logs over SSH to the central Planner (which would overwhelm the LLM's context window), the Worker Agents must perform local log parsing and filtering \- extracting only the unique error templates and anomalies \- to send back to the Aggregator.  
* **Link:** https://dl.acm.org/doi/abs/10.1145/3597503.3639155

# **LLM Agent-Assisted Root Cause Analysis Framework \- (Please suggest a good name, we need to rethink the name based on changes in project)**

AI Generated Diagrams (For reference) \- will make it again for paper  
This report is outcome of detailed conversation AI and  multiple iteration of my learnings and understandings from papers

## **1\. Overview**

This document outlines the plan for building an autonomous, multi-agent framework that performs Root Cause Analysis (RCA) across distributed microservice architectures. The system uses specialized LLM-powered agents coordinated through a central parent agent to investigate production incidents \- progressively narrowing the search space until the exact root cause is identified, validated, and reported.

## **2\. Problem Statement**

Modern cloud-native products are composed of numerous microservices deployed across independent virtual machines. When an incident occurs, SRE and DevOps teams must manually SSH into multiple machines, grep through logs, cross-reference network/memory/database metrics, and synthesize findings from disparate sources. This process is slow, error-prone, and heavily dependent on institutional knowledge.

This framework automates the entire investigative workflow through coordinated LLM agents with domain-specific expertise.

## **3\. High-Level Architecture**

## **4\. Core Components**

### **4.1 Service Configuration (YAML)**

A single YAML file per product that acts as the source of truth for the infrastructure. It describes every microservice the framework needs to access and investigate.

**Fields per microservice:**

| Field | Description |
| ----- | ----- |
| service\_name | Unique identifier for the microservice |
| ssh\_config | Connection details \- host, port, user, key path, jump host if applicable |
| expected\_behavior | Description of healthy behavior, SLOs, nominal metrics |
| known\_failures | Known failure modes, historical patterns, and their signatures |
| context\_commands | Array of shell commands (grep, awk, regex filters) developers define to extract initial diagnostic context |
| additional\_info | Service owner, dependencies, deployment version, architecture notes |

**Example:**

| product: PaymentGatewayservices:  \- service\_name: auth-service    ssh\_config:      host: 10.0.1.12      port: 22      user: sre-bot      key\_path: /keys/auth-service.pem    expected\_behavior: |      Handles \~2,000 req/s at P99 \< 120ms. Token refresh       cycle every 15 min. Redis session cache hit rate \> 95%.    known\_failures:      \- pattern: "TokenExpiredError spike"        likely\_cause: "Redis cache eviction or clock drift"      \- pattern: "Connection pool exhaustion"        likely\_cause: "Downstream DB latency or connection leak"    context\_commands:      \- "journalctl \-u auth-service \--since '1 hour ago' | grep \-iE 'error|fatal|timeout'"      \- "ss \-tunap | grep :8443 | wc \-l"      \- "cat /proc/meminfo | grep \-i 'memavailable\\\\|memfree'"    additional\_info:      owner: auth-team@company.com      dependencies: \[redis-cluster, user-db, token-vault\]      version: 3.12.1 |
| :---- |

### **4.2 Parent Agent (Orchestrator)**

The central coordinating agent. It never directly investigates infrastructure \- it reasons, plans, delegates, and decides when to stop.

**Responsibilities:**

* **Intake:** Parses the incoming incident ticket (title, description, severity, affected services) alongside the full service configuration to build situational awareness.  
* **Task Decomposition:** Breaks the investigation into discrete subtasks. Each subtask specifies what to investigate, on which service, and what to look for.  
* **Agent Assignment:** Maps each subtask to the appropriate specialist agent(s). This is a many-to-many relationship \- one subtask can go to multiple specialists, and one specialist can receive multiple subtasks.  
* **Iterative Refinement:** After each investigation cycle, reviews synthesized findings and decides whether to create more subtasks (broader or more focused) or to converge on a root cause.  
* **Convergence Signal:** The loop terminates when the Parent Agent produces a final RCA finding *without* invoking the subtask-creation tool. This implicit signal means it has enough evidence to conclude.

### **4.3 Specialist Agents**

Pre-configured, domain-specific LLM agents. Each has a tailored system prompt, tool access, and domain knowledge that focuses its analysis on its area of expertise.

| Agent | Domain | Focus Areas |
| ----- | ----- | ----- |
| **Network Agent** | Network | Connectivity, DNS, latency, packet loss, firewall rules, load balancers, TLS/SSL |
| **Memory Agent** | Memory | RAM utilization, swap, OOM kills, memory leaks, heap/stack analysis |
| **Log Agent** | Logs | Application/system logs, audit trails, pattern anomalies, error frequency |
| **Application Agent** | Application | Process health, thread pools, request queues, app-level errors, dependency failures |
| **Database Agent** | Database | Query performance, connection pools, replication lag, lock contention, deadlocks |
| **Cache Agent** | Cache | Hit/miss ratios, eviction rates, memory pressure, replication, key distribution |
| **OS Agent** | OS / Kernel | CPU, disk I/O, file descriptors, kernel logs (dmesg), zombie processes, cron jobs |

**Execution flow per specialist:**

1. Receive subtask from the Parent Agent (target service, scope, guiding hypothesis).  
2. SSH into the target VM using credentials from the service config.  
3. Execute relevant context\_commands plus additional domain-specific diagnostic commands.  
4. Analyze outputs against the expected\_behavior and known\_failures entries.  
5. Return structured findings: observations, anomalies, confidence level, and recommended follow-ups.

### **4.4 Synthesis LLM (Cross-Domain Consolidation)**

After all specialist agents in a cycle complete their subtasks, outputs are aggregated and passed to a large-context-window LLM for cross-domain correlation.

**Responsibilities:**

* Ingest all specialist findings from the current cycle plus full investigation history from prior cycles.  
* Identify cross-domain correlations (e.g., a memory spike on Service A coinciding with connection pool exhaustion on Service B).  
* Eliminate redundant or contradictory findings.  
* Produce a unified cycle summary that is fed back to the Parent Agent for the next iteration.

**Why separate from the Parent Agent?** The Parent Agent is optimized for planning and tool use. The Synthesis LLM is optimized for large-context reasoning over a large body of evidence. Separating these allows each to use the best model configuration \- e.g., the Synthesis LLM can use a 200K+ token context window model while specialists use faster, tool-optimized models.

### **4.5 Evaluator Agent (Quality Gate)**

Once the Parent Agent converges on a root cause, the output passes through an independent evaluator before delivery.

**Evaluation criteria:**

| Criterion | Description |
| ----- | ----- |
| **Accuracy** | Is the root cause logically consistent with collected evidence? Any gaps or unsupported leaps? |
| **Completeness** | Does it address the full scope \- contributing factors, blast radius, timeline? |
| **Professionalism** | Is the report clear, structured, and suitable for engineering leads and management? |
| **Actionability** | Does it include concrete remediation steps or recommendations? |

**Feedback loop:** If the evaluator finds deficiencies, it generates structured feedback and sends the finding back to the Parent Agent for revision. This continues until the report passes all criteria.

## **5\. Investigation Lifecycle**

### **Phase 1 \- Initialization**

1. Incident ticket is received (via integration or manual input).  
2. Service configuration for the affected product is loaded.  
3. Parent Agent ingests both and builds an initial investigation plan.

### **Phase 2 \- Investigation Loop**

4. Parent Agent decomposes the investigation into subtasks and assigns them to specialist agents.  
5. Specialist agents execute investigations via SSH, collecting evidence from target VMs.  
6. All outputs are collected and forwarded to the Synthesis LLM.  
7. Synthesis LLM produces a cycle summary and returns it to the Parent Agent with cumulative history.  
8. Parent Agent evaluates:  
   * **Insufficient evidence â†’** Create new subtasks (broader or more focused), return to step 4\.  
   * **Root cause identified â†’** Produce final finding, proceed to Phase 3\.

### **Phase 3 \- Validation and Delivery**

9. Evaluator Agent reviews the finding against all criteria.  
10. If it fails â†’ structured feedback sent back to Parent Agent for revision.  
11. If it passes â†’ final RCA report is generated and delivered.

## **6\. Component Summary**

| Component | Role | Type |
| ----- | ----- | ----- |
| **Service Configuration** | YAML file describing all microservices | Configuration |
| **Parent Agent** | Central coordinator \- plans, delegates, converges | LLM Agent (Tool-Using) |
| **Network Agent** | Network diagnostics | Specialist Agent |
| **Memory Agent** | Memory analysis | Specialist Agent |
| **Log Agent** | Log analysis | Specialist Agent |
| **Application Agent** | Application health | Specialist Agent |
| **Database Agent** | Database diagnostics | Specialist Agent |
| **Cache Agent** | Cache systems | Specialist Agent |
| **OS Agent** | OS/Kernel diagnostics | Specialist Agent |
| **Synthesis LLM** | Cross-domain finding consolidation | LLM (Large Context) |
| **Evaluator Agent** | Quality gate and validation | LLM Agent (Evaluator) |

## **7\. Design Rationale**

**Why specialized agents instead of one general agent?** A single agent trying to reason about network topology, memory patterns, and database locks simultaneously suffers from context dilution. Specialist agents maintain focused prompts and domain-specific tooling, producing higher-quality analysis per domain.

**Why a separate Synthesis LLM?** Specialists operate in isolated contexts to stay focused. Cross-domain correlation (e.g., connecting a memory issue to a database timeout) requires holistic reasoning over a large evidence set \- a fundamentally different capability best served by a large-context model.

**Why an iterative loop?** RCA is inherently exploratory. Initial hypotheses may be wrong. Symptoms on Service A may trace to a root cause on Service C that wasn't initially investigated. The loop allows adaptive expansion or narrowing based on emerging evidence \- mirroring how experienced SREs actually work.

**Why an independent evaluator?** Self-evaluation by the Parent Agent introduces confirmation bias. An independent evaluator ensures the final report is evidence-backed, logically sound, and stakeholder-ready.

## **8\. Security Considerations**

* **SSH Keys:** Credentials stored in an encrypted vault (e.g., HashiCorp Vault, AWS Secrets Manager), fetched at runtime, never persisted beyond the active session.  
* **Least Privilege:** Bot user on each VM has read-only access. No write or admin access.  
* **Command Allowlisting:** All commands executed by agents are validated against an allowlist. No arbitrary command execution.  
* **Audit Trail:** Every SSH session, command, and agent decision is logged for post-incident review.  
* **Data Redaction:** Sensitive data (credentials, PII) encountered in logs is redacted before being passed to any LLM.

