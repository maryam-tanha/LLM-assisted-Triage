# Literature Review Summary: Multi-Agent RCA Frameworks

This document compiles the findings, key metrics, and relevance of 20 academic papers related to the development of a Multi-agent RCA (Root Cause Analysis) framework for automated incident investigation in cloud/microservice environments.

## 1. 01_MetaGPT
**Title:** METAGPT: META PROGRAMMING FOR A MULTI-AGENT COLLABORATIVE FRAMEWORK
**Core Findings & Method:** Introduces MetaGPT, an LLM-based multi-agent framework that incorporates Standardized Operating Procedures (SOPs) from human workflows. It uses an assembly-line paradigm to assign specialized roles (Product Manager, Project Manager, Architect, Engineer, QA Engineer) to agents, breaking down complex tasks. Agents communicate using structured documents via a shared message pool with a publish-subscribe mechanism to reduce hallucinations. It also includes an executable feedback mechanism for self-correction during code generation.
**Key Metrics and Numbers:** 
- Achieved state-of-the-art results on coding benchmarks: 85.9% Pass@1 on HumanEval and 87.7% Pass@1 on MBPP.
- 100% task completion rate on the SoftwareDev benchmark.
- Highly efficient token usage, averaging 24,613 tokens and 503 seconds per software task (without feedback).
**Relevance to a Multi-agent RCA framework:** Highly relevant. Establishing specialized roles (e.g., Log Analyst, Metric Expert) and utilizing structured SOPs can greatly streamline root cause analysis. A shared, publish-subscribe message pool ensures agents stay focused on relevant alerts without getting distracted, mitigating hallucination risks during critical cloud incident investigations.

## 2. 02_DBot_Database_Diagnosis
**Title:** D-Bot: Database Diagnosis System using Large Language Models
**Core Findings & Method:** Presents an LLM-based database diagnosis system that automates root cause analysis. D-Bot extracts knowledge offline from diagnosis documents and dynamically generates prompts matching the context and tools. It employs a tree search algorithm for multi-step reasoning and a collaborative multi-agent mechanism to address complex anomalies with multiple root causes asynchronously.
**Key Metrics and Numbers:** 
- Validated on 539 anomalies across 6 typical applications.
- Generates precise diagnosis reports in under 10 minutes (compared to hours for human DBAs).
- Fine-tuned local models (Baichuan2, CodeLlama) achieve diagnostic accuracy comparable to GPT-4. (Note: Llama 2-13B was also tested but failed entirely, achieving near-zero accuracy.)
**Relevance to a Multi-agent RCA framework:** Extremely relevant. Its architecture is directly applicable to cloud RCA. The use of offline document extraction (for playbooks), automatic tool retrieval, and asynchronous collaboration among multiple LLM experts provides a strong blueprint for investigating complex, multi-root-cause incidents in cloud environments.

## 3. 03_LLM_Resilience_Faulty_Agents
**Title:** On the Resilience of LLM-Based Multi-Agent Collaboration with Faulty Agents
**Core Findings & Method:** Investigates the impact of clumsy or malicious (faulty) agents on multi-agent systems. The authors propose AUTOTRANSFORM and AUTOINJECT to simulate stealthy agent errors. They evaluate Linear, Flat, and Hierarchical communication structures. To increase resilience, they introduce a "Challenger" (enabling agents to challenge others' outputs) and an "Inspector" (an extra agent dedicated to reviewing and correcting messages).
**Key Metrics and Numbers:** 
- Hierarchical structures (A→(B↔C)) are the most resilient, with only a 5.5% performance drop, compared to 10.5% (Flat) and 23.7% (Linear).
- Code generation tasks were the most vulnerable, suffering a 22.6% performance drop.
- The Inspector and Challenger mechanisms can recover up to 96.4% of the performance lost due to faulty agents.
**Relevance to a Multi-agent RCA framework:** Highly relevant. In an automated RCA system, agents might hallucinate, misinterpret logs, or fail to pull the right metrics. Designing the system with a hierarchical structure and incorporating "Inspector/Challenger" guardrails ensures that incorrect analyses don't derail the entire investigation, ensuring high reliability in critical operational tasks.

## 4. 04_LACP_Telecom_Protocol
**Title:** LLM Agent Communication Protocol (LACP) Requires Urgent Standardization: A Telecom-Inspired Protocol is Necessary
**Core Findings & Method:** Proposes the LLM-Agent Communication Protocol (LACP) to resolve the fragmented and insecure landscape of multi-agent communication. Inspired by the OSI model in telecommunications, LACP utilizes a three-layer architecture: a Semantic Layer for intent (PLAN, ACT, OBSERVE), a Transactional Layer for integrity (atomic transactions, digital signatures), and a Transport Layer for delivery.
**Key Metrics and Numbers:** 
- Extremely low latency overhead (+2.9% to +3.5%, around 0.03ms increase).
- Payload size overhead is +30% for realistic large payloads (2,560 bytes vs 1,964 bytes) due to verifiable cryptographic signing, a justifiable cost for end-to-end security.
**Relevance to a Multi-agent RCA framework:** Extremely relevant. Cloud RCA involves handling sensitive infrastructure logs and executing mitigation actions. Standardizing communication with LACP ensures that agent interactions are secure, authenticated, and transactionally reliable, preventing unauthorized actions or miscommunication during an incident.

## 5. 05_SafeOps_AI_Agent_Code_of_Conduct
**Title:** Policy-as-Prompt: Turning AI Governance Rules into Guardrails for AI Agents
**Core Findings & Method:** Introduces a regulatory machine learning framework to bridge the gap between static policy documents (e.g., PRDs, TDDs) and runtime enforcement. The method generates a source-linked policy tree from design documents, which is then compiled into prompt-based classifiers (an Input Classifier and Output Auditor) to enforce least privilege and data minimization via real-time monitoring.
**Key Metrics and Numbers:** 
- The generated lightweight runtime judges (using GPT-4o) achieved 68-73% accuracy for detecting out-of-domain inputs and outputs (narrative text states 70-73%; Table 3 shows 68% as the floor for output auditing).
- The system acts as an effective "default-deny" guardrail, significantly reducing prompt-injection risks and preventing toxic or out-of-scope actions.
**Relevance to a Multi-agent RCA framework:** Highly relevant. Automated RCA agents must adhere strictly to compliance and security policies (e.g., not leaking PII from logs, not altering production states without permission). "Policy-as-Prompt" provides an actionable way to deploy real-time guardrails that restrict RCA agents strictly to their permitted read/write boundaries.

## 6. AOI: Multi-Agent IT Ops
**Title:** AOI: Context-Aware Multi-Agent Operations via Dynamic Scheduling and Hierarchical Memory Compression
**Core Findings & Method:** The paper proposes AOI (AI-Oriented Operations), a multi-agent collaborative framework that integrates three specialized agents (Observer, Probe, Executor) coordinated by an LLM-based Context Compressor. It utilizes a dynamic task scheduling strategy to adaptively prioritize operations based on real-time states and employs a three-layer memory architecture (Working, Episodic, Semantic) for context retention.
**Key Metrics and Numbers:** Achieves 72.4% context compression while preserving 92.8% of critical information. Improves task success rate to 94.2% and reduces Mean Time To Recovery (MTTR) by 34.4% compared to the best baseline.
**Relevance to a Multi-agent RCA framework:** Highly relevant. The architectural separation of duties (Observer for coordination, Probe for read-only telemetry gathering, Executor for safe remediation) provides a robust design template for an automated RCA framework. Additionally, its memory compression techniques address the exact issue of context overflow when dealing with large volumes of cloud logs and metrics.

## 7. AgentOrchestra
**Title:** AgentOrchestra: Orchestrating Multi-Agent Intelligence with the Tool-Environment-Agent(TEA) Protocol
**Core Findings & Method:** Introduces the TEA (Tool-Environment-Agent) protocol to provide standardized lifecycle, context management, and versioning for multi-agent systems. Based on this, it presents AgentOrchestra, a hierarchical framework where a central planner orchestrates domain-specific sub-agents, supporting dynamic tool instantiation and continuous self-evolution from execution feedback.
**Key Metrics and Numbers:** Achieves state-of-the-art performance of 89.04% on the GAIA benchmark, consistently outperforming strong monolithic baselines. 
**Relevance to a Multi-agent RCA framework:** Highly relevant. In a cloud RCA framework, treating environments (e.g., Kubernetes, database clusters) as first-class components with explicit constraints (as proposed by TEA) ensures safe and isolated execution. The hierarchical orchestration model is ideal for delegating specific incident investigation tasks to specialized sub-agents.

## 8. MasRouter
**Title:** MasRouter: Learning to Route LLMs for Multi-Agent System
**Core Findings & Method:** Defines the Multi-Agent System Routing (MASR) problem and proposes MasRouter, a framework that dynamically determines collaboration topologies, allocates agent roles, and routes appropriate LLM backbones for specific queries. It uses a cascaded controller network to balance performance and cost without relying solely on large, expensive models.
**Key Metrics and Numbers:** Improves performance by 1.8% to 8.2% on MBPP over SOTA. Highly economical, reducing inference overhead by up to 52.07% on HumanEval (cost reduction from $0.363 to $0.185 per query) and reducing costs by 17.21%–28.17% when integrated into mainstream MAS frameworks.
**Relevance to a Multi-agent RCA framework:** Very relevant. Automated RCA systems generate frequent queries to process alerts and metrics. MasRouter offers a blueprint for dynamically invoking lighter LLMs for simple log parsing tasks and routing complex root-cause reasoning to larger models, heavily optimizing operational costs.

## 9. OpenRCA
**Title:** OpenRCA: Can Large Language Models Locate the Root Cause of Software Failures?
**Core Findings & Method:** Introduces OpenRCA, a comprehensive benchmark comprising real-world software failures and associated telemetry (logs, metrics, traces) to evaluate LLMs on post-development RCA tasks. The authors also propose RCA-agent, which synthesizes and executes Python code to query and analyze massive telemetry data, preventing context window exhaustion.
**Key Metrics and Numbers:** The benchmark contains 335 failure cases and 68+ GB of telemetry data. Standard LLMs struggled significantly (Claude 3.5 solved only 5.37% of tasks with oracle telemetry). Using the code-executing RCA-agent, accuracy improved to 11.34%, highlighting the severe difficulty of raw log reasoning.
**Relevance to a Multi-agent RCA framework:** Extremely relevant. It empirically proves that LLMs cannot simply ingest raw cloud telemetry to find root causes. An effective cloud RCA framework must adopt the RCA-agent's methodology: using LLMs to write and execute programmatic scripts that query metrics/logs databases rather than reading raw text directly.

## 10. HyLIFT_5G_Fault_Diagnosis
**Title:** Hybrid LLM-Assisted Fault Diagnosis Framework for 5G/6G Networks Using Real-World Logs
**Core Findings & Method:** Proposes Hy-LIFT, a multi-stage diagnosis toolkit that combines an Interpretable Rule-Based Engine (IRBE) for known faults, a Semi-Supervised Classifier (SSC) using pseudo-labeling for unlabeled logs, and an LLM Augmentation Engine (LAE) to generate natural language explanations and hypothesize causes for novel faults.
**Key Metrics and Numbers:** Achieves high overall accuracy with a macro-F1 of ~89-90%, and robust per-class precision/recall of ~0.85–0.93, significantly outperforming purely rule-based or purely ML-based baseline methods.
**Relevance to a Multi-agent RCA framework:** Highly relevant. This hybrid approach directly mitigates LLM hallucinations and high latency. For an automated cloud RCA framework, using deterministic rules/ML for common infrastructure incidents and reserving LLM multi-agent analysis for complex, novel, or ambiguous incidents provides a highly reliable, scalable, and explainable architecture.

## 11. MA_RCA_MultiAgent_Framework
**Title:** Leveraging multi-agent framework for root cause analysis
**Core Findings & Method:** The paper proposes MA-RCA, a collaborative multi-agent framework that deploys specialized agents (RCA Agent, Retrieval Agent, Validation Agent, Report Agent) for distinct subtasks. It aims to counteract LLM hallucinations and error propagation by utilizing a Retrieval Agent to ground hypotheses in external domain knowledge (using RAG) and a Validation Agent to dynamically test hypotheses against runtime data.
**Key Metrics and Numbers:** The framework achieved 95.8% accuracy (F1 = 0.952) on the Nezha cloud-native platform dataset and 84.3% accuracy (F1 = 0.828) on a distributed power metering infrastructures dataset.
**Relevance to a Multi-agent RCA framework:** Highly relevant. This paper directly models a multi-agent architecture for RCA. The inclusion of specialized retrieval (RAG) and dynamic validation agents provides a strong blueprint for reducing hallucinations and improving diagnostic accuracy in automated cloud incident investigations.

## 12. Triangle_Incident_Triage_MultiLLM
**Title:** Triangle: Empowering Incident Triage with Multi-LLM-Agents
**Core Findings & Method:** The authors present Triangle, an end-to-end incident triage system built on a Multi-LLM-Agent framework. It utilizes semantic distillation to address the semantic heterogeneity of incident data. The system features multi-role agents (Analyser, Triage Decider, Team Manager) that use a negotiation mechanism to emulate human engineers' workflows, effectively handling decentralized domain knowledge. It also includes an automated Team Information Enrichment mechanism.
**Key Metrics and Numbers:** The system improves average incident triage accuracy by more than 20% and reduces the time to engage by about 3 time units per incident compared to state-of-the-art methods. It was successfully deployed in a production system serving tens of millions of users.
**Relevance to a Multi-agent RCA framework:** Very relevant. While focused primarily on incident triage and routing rather than deep RCA, the multi-role agent architecture, negotiation mechanisms, and semantic distillation techniques are highly applicable to the initial stages of an automated incident investigation framework.

## 13. AIOps_LLM_Survey
**Title:** A Survey of AIOps in the Era of Large Language Models
**Core Findings & Method:** This paper provides a comprehensive systematic review of 183 research papers published between 2020 and 2024 regarding the application of LLMs in AIOps. It analyzes transformations in data sources (logs, metrics, traces), the evolution of AIOps tasks, various LLM-based methods (Prompt-based, Embedding-based, Fine-Tuning, Foundation Models), and current evaluation methodologies, while identifying gaps and future research directions.
**Key Metrics and Numbers:** Analyzed 183 research papers spanning January 2020 to December 2024.
**Relevance to a Multi-agent RCA framework:** Relevant as foundational literature. It provides a comprehensive overview of the current state-of-the-art in LLM-based AIOps, which is crucial for positioning a new multi-agent RCA framework within the broader research landscape and identifying appropriate baselines and evaluation metrics.

## 14. FLASH_Workflow_Automation_Incidents
**Title:** FLASH: A Workflow Automation Agent for Diagnosing Recurring Incidents
**Core Findings & Method:** The paper introduces FLASH, a workflow automation agent tailored for diagnosing recurring incidents. It improves diagnostic reliability through "status supervision," which breaks down complex instructions to align with the current diagnosis status (Diagnosis Planning, Step Initialization, Step Execution, Step Completion). It also uses "hindsight integration" to reflect on and correct mistakes using knowledge generated from past failure experiences.
**Key Metrics and Numbers:** Evaluated on 250 production incidents and 52 troubleshooting guides from a major cloud provider (CompanyX). The approach outperformed state-of-the-art agent models by an average of 13.2% in accuracy. A qualitative study found that ~70% of TSG scenarios can be automated with minor revisions or human involvement (not all 70% are fully autonomous).
**Relevance to a Multi-agent RCA framework:** Highly relevant. It tackles the practical execution of diagnostic steps (workflows/troubleshooting guides) by an LLM agent. The concepts of status supervision and hindsight integration (learning from past failures) are directly applicable to the execution and validation agents within a larger multi-agent RCA framework.

## 15. AIOps_Reliability_RCA_Chaos_Engineering
**Title:** AIOps for Reliability: Evaluating Large Language Models for Automated Root Cause Analysis in Chaos Engineering
**Core Findings & Method:** This study evaluates LLMs (GPT-4o, Gemini-1.5, Mistral-small) for diagnosing system failures purely from observability metrics using a chaos engineering framework. It demonstrates that while LLMs can identify common failure patterns, their accuracy is heavily dependent on prompt engineering. The models often suffer from misclassification biases (e.g., misattributing harmless load spikes as security threats) and hallucinations, necessitating structured guidance.
**Key Metrics and Numbers:** In zero-shot settings, models achieved moderate accuracy (44–58%). Few-shot prompting improved performance to 60–74% accuracy. Human SREs achieved 82% accuracy under few-shot conditions (62% zero-shot); the 82% figure is not a general baseline — it is the SRE few-shot result.
**Relevance to a Multi-agent RCA framework:** Relevant for understanding the baseline capabilities and limitations of standalone LLMs in RCA. It emphasizes the necessity of a structured, multi-agent approach (incorporating RAG, validation tools, and strict guidelines) because raw LLMs still fall short of human performance due to hallucinations and biases.

## 16. RCACopilot_Automatic_RCA_Cloud
**Title:** Automatic Root Cause Analysis via Large Language Models for Cloud Incidents
**Core Findings & Method:** Introduces RCACopilot, an automated system that streamlines root cause analysis (RCA) for cloud incidents. It utilizes predefined "incident handlers" to systematically collect multi-source diagnostic data (logs, metrics, traces, etc.) and leverages Large Language Models (LLMs) to predict root cause categories and generate explanatory narratives.
**Key Metrics and Numbers:** Evaluated on a real-world dataset comprising a year's worth of incidents from Microsoft. RCACopilot achieved an RCA accuracy of up to 0.766. The diagnostic information collection component has been deployed at Microsoft for over four years; the novel LLM-based root cause prediction component was only several months old at time of publication.
**Relevance to a Multi-agent RCA framework:** Highly relevant. It provides a blueprint for how LLMs can process multi-source diagnostic data to infer root causes, and its use of incident-specific automated workflows ("handlers") strongly mirrors the concept of specialized agents executing targeted investigation tasks.

## 17. Autonomous_Agents_SE_MultiAgent
**Title:** Autonomous Agents in Software Engineering: A Multi-Agent LLM Approach
**Core Findings & Method:** Explores the integration of multi-agent LLM systems in software engineering workflows. The approach assigns specialized roles to different agents (e.g., requirement analysis, code generation, testing, debugging). The study emphasizes that while these agents automate tasks and improve efficiency, they face challenges in coordination, leading to conflicting decisions without proper resolution mechanisms.
**Key Metrics and Numbers:** The study provides qualitative results, noting reductions in coding and debugging time, and increased developer productivity in simulated environments. It highlights the importance of hybrid AI-human collaboration.
**Relevance to a Multi-agent RCA framework:** Relevant for architectural design. It highlights the necessity of robust communication protocols and decision-resolution mechanisms between agents—crucial elements for ensuring that multiple specialized RCA agents (e.g., a log analyzer, a metric analyzer, and a network investigator) coordinate effectively without conflicting.

## 18. Autonomous_Agents_InfoRetrieval_SE_LLM
**Title:** Autonomous agents in software development for information retrieval using LLM models
**Core Findings & Method:** Proposes a multi-agent framework designed for rapid and reliable information retrieval using LLMs. The architecture consists of six specialized agents across four modules: User Assistant (query refinement), Context Translator, Researcher (retrieval and recursive searching), Content Verifier, Report Author, and Source Manager (synthesis and citation verification).
**Key Metrics and Numbers:** Presents a conceptual architecture evaluated with models like Llama2, Llama3, and Gemma2, focusing on qualitative improvements in fact-finding reliability and strict quality control through recursive validation.
**Relevance to a Multi-agent RCA framework:** Directly applicable to the information gathering phase of an RCA framework. The recursive research process and the specialized verification agents demonstrate how a framework can ensure the accuracy and relevance of extracted diagnostic information from complex cloud environments.

## 19. SageCopilot_DataScience_Agent
**Title:** SageCopilot: An LLM-Empowered Autonomous Agent for Data Science as a Service
**Core Findings & Method:** Introduces SageCopilot, an industry-grade system automating the data science pipeline. It uses a two-phase architecture: an offline phase for schema semantic governance and seed data construction (data augmentation), and an online phase leveraging In-Context Learning (ICL) to convert natural language to executable SQL (NL2SQL), analyze data, and generate visualizations (Text2Viz).
**Key Metrics and Numbers:** Implemented SQL-to-Natural Language (SQL2NL) enhancement improved Execution Accuracy (EX) from 56.2% to 81.3% in a specific domain. The schema linking retrieval strategy achieved up to 92% recall.
**Relevance to a Multi-agent RCA framework:** Highly relevant. RCA frequently involves executing complex queries against telemetry databases to extract insights. The techniques presented for reliable NL2SQL generation, ICL prompt tuning, and SQL reflection are essential for enabling RCA agents to autonomously query and visualize cloud metrics and logs.

## 20. DivLog_Log_Parsing
**Title:** DivLog: Log Parsing with Prompt Enhanced In-Context Learning
**Core Findings & Method:** Proposes DivLog, a training-free log parsing framework that leverages the In-Context Learning (ICL) capabilities of LLMs to convert semi-structured logs into structured templates. It works by offline sampling of diverse log candidates and online retrieval of the top 5 most similar labeled examples to construct a specialized prompt, allowing the LLM to generate the target log's template.
**Key Metrics and Numbers:** Evaluated on 16 public LogPAI datasets, DivLog achieved state-of-the-art performance: 98.1% Parsing Accuracy (PA), 92.1% Precision Template Accuracy (PTA), and 92.9% Recall Template Accuracy (RTA).
**Relevance to a Multi-agent RCA framework:** Extremely relevant. Log parsing is the foundational first step for any log-based anomaly detection or RCA. By providing a highly accurate, training-free log parser that handles diverse formats, DivLog enables downstream RCA agents to process and analyze structured log data much more effectively.
