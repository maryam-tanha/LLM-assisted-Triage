# Conference Poster Plan — LLM-Assisted Triage

## Context

Kalhar is preparing a **conference poster** (40" x 27", landscape) for his capstone/research project: a multi-agent RCA (Root Cause Analysis) framework that uses LLMs and LangGraph to automatically investigate microservice incidents. The poster needs to present the system architecture, methodology, experimental validation (EXP-06 confirmed result), and future work in a professional, visually striking format.

**Poster size:** 40" x 27" (landscape — wider than tall)
**Colour scheme:** Dark tech (navy/teal/white)
**Graphics:** AI-generated hero visuals + hand-made architecture/result diagrams
**Audience:** Conference attendees — mix of academics and industry practitioners

---

## 1. Poster Layout (40" x 27" Landscape — 3-Column)

The landscape format suits a **3-column layout** with a full-width title banner and full-width results strip.

```
← ──────────────────── 40" wide ──────────────────── →
┌────────────────────────────────────────────────────┐ ↑
│                   TITLE BANNER                     │ 3.5"
│  LLM-Assisted Triage: A Multi-Agent Framework for  │
│  Automated Incident Root Cause Analysis            │
│  Kalhar Pandya  |  email  |  university logo       │
├──────────────┬───────────────────┬─────────────────┤
│              │                   │                 │
│  1. BACK-    │  3. SYSTEM        │  5. DEMO        │
│  GROUND      │     ARCHITECTURE  │     TARGETS     │
│              │                   │                 │ 10"
│  2. MOTIV-   │  [HERO ARCH.      │  6. EXPERIMENT  │
│  ATIONS &    │   DIAGRAM]        │     VALIDATION  │
│  OBJECTIVES  │                   │                 │
│              │  component legend  │                 │
├──────────────┴───────────────────┴─────────────────┤
│            FULL-WIDTH RESULTS STRIP                │
│  ┌────────────┐ ┌─────────────────┐ ┌────────────┐│ 7"
│  │ EXP-06     │ │ Fault Injection │ │ Evidence   ││
│  │ Results +  │ │ Pipeline Diagram│ │ Log Panel  ││
│  │ Metrics    │ │ (Graphic C)     │ │(Graphic B) ││
│  └────────────┘ └─────────────────┘ └────────────┘│
├──────────────┬────────────────────┬────────────────┤
│ 7. KEY       │ 8. CONCLUSION &   │  REFERENCES    │ 4"
│    RESULTS   │    FUTURE WORK    │  + QR CODE     │
│  [metric     │                   │                │
│   cards]     │                   │                │
└──────────────┴────────────────────┴────────────────┘ ↓ 27"

Column widths: LEFT ~11"  |  CENTRE ~17"  |  RIGHT ~12"
(Centre column is widest for the architecture diagram)
```

**Column breakdown:**
- **Left column (~11"):** Background + Motivations & Objectives (stacked)
- **Centre column (~17"):** System Architecture — the hero diagram dominates
- **Right column (~12"):** Demo Targets + Experimental Validation (stacked)
- **Full-width results strip:** EXP-06 metrics, fault injection pipeline, evidence log panel
- **Bottom row (3-col):** Key Results | Conclusion & Future Work | References + QR

---

## 2. Colour Scheme — Dark Tech

### Primary Palette

| Role            | Hex       | Usage                                    |
|-----------------|-----------|------------------------------------------|
| **Background**  | `#0B1628` | Main poster background (deep navy)       |
| **Panel BG**    | `#112240` | Section card backgrounds                 |
| **Accent 1**    | `#64FFDA` | Teal — headings, highlights, key callouts|
| **Accent 2**    | `#00B4D8` | Cyan — diagram lines, graph edges        |
| **Text Primary**| `#CCD6F6` | Body text (light grey-blue)              |
| **Text Bright** | `#E6F1FF` | Section titles, emphasis                 |
| **White**       | `#FFFFFF` | Title, key numbers, chart labels         |
| **Alert/Warm**  | `#FF6B6B` | Error states, fault injection highlights |
| **Success**     | `#57CC99` | Confirmed/success states                 |
| **Muted**       | `#8892B0` | Captions, secondary text                 |

### Typography

| Element          | Font              | Size (approx at 27x40) | Weight |
|------------------|-------------------|-------------------------|--------|
| Title            | Montserrat or Poppins | 72–84pt              | Bold   |
| Section headers  | Montserrat        | 36–42pt                 | SemiBold|
| Body text        | Inter or Source Sans Pro | 18–22pt           | Regular|
| Code/evidence    | JetBrains Mono or Fira Code | 14–16pt       | Regular|
| Captions         | Inter              | 14–16pt                 | Light  |

### Design Rules

- Section panels: rounded corners (12px), subtle `#112240` fill with 1px `#1D3461` border
- Accent glow: teal (`#64FFDA`) used as thin top-border on section cards
- Diagram nodes: filled `#112240` with `#64FFDA` border, white text
- Diagram edges: `#00B4D8` with arrowheads
- Code blocks: `#0A0F1A` background, `#64FFDA` text, monospace
- Charts: teal/cyan bars on dark background; error bars in `#FF6B6B`

---

## 3. Section Content

### TITLE BANNER
> **LLM-Assisted Triage: A Multi-Agent Framework for Automated Incident Root Cause Analysis**
> Kalhar Pandya | [university/email] | [university logo if applicable]
> [Optional: 1-line tagline in teal: "Automated fault diagnosis for microservice systems using LLM-powered specialist agents"]

### 1. Background (left column, ~200 words)
- Modern cloud systems comprise dozens of interdependent microservices
- Incidents trigger cascading failures across services
- Manual Root Cause Analysis requires expert knowledge, cross-service log correlation, and is slow (high MTTR)
- Large Language Models (LLMs) demonstrate strong reasoning over unstructured operational data — logs, configs, process state
- **Gap:** No existing system combines parallel specialist dispatch, multi-cycle iterative reasoning, and live container introspection

### 2. Motivations & Objectives (right column, ~150 words)
**Problem:** Incident MTTR is a critical SRE metric; manual triage is the bottleneck.

**Objectives:**
- Design a multi-agent framework where specialist agents investigate different service domains **in parallel**
- Enable iterative refinement: if evidence is insufficient, loop for additional cycles
- Produce structured, evidence-backed RCA reports with confidence scores
- Enforce security constraints: read-only command allowlist + credential redaction
- Validate on real fault-injected deployments

### 3. System Architecture (full-width, centrepiece)
**Content:** Full LangGraph architecture diagram (see Section 4 — Graphics)

**Text annotations around the diagram:**
- **Parent Agent** — LLM orchestrator using tool-calling. Decides `create_subtasks` (fan-out) or `write_rca_conclusion` (terminate). Iterates up to `MAX_CYCLES`.
- **Specialist Agents** — Self-register via registry; execute in parallel via LangGraph `Send` API. Each runs a ReAct-style tool loop with `run_command` for live container introspection.
  - `log_agent`: Container log analysis, error pattern matching
  - `runtime_status_agent`: Process state, memory, disk, CPU
  - `docker_specs_agent`: cgroup limits, OOM history, restart count
  - `network_agent`: Inter-service connectivity, DNS, port state
- **Synthesis Agent** — Correlates cross-domain findings into `CycleSummary` with key findings + recommendations for next investigation cycle
- **Graph State** — `Annotated[list, operator.add]` reducers enable parallel result merging

### 4. Security Layer (left sub-column)
- **Command Allowlist:** Deny-first policy — blocks `rm`, `curl`, `wget`, `chmod`, `eval`, output redirections, pipe-to-shell. Only allows read-only diagnostic commands (`cat /proc/`, `ps`, `df`, `redis-cli`, `psql`, etc.)
- **Output Redaction:** Strips AWS keys, PEM private keys, bearer tokens, API keys, passwords, emails, IPv4 addresses, base64 blobs before passing to LLM
- **Execution Sandbox:** Command timeout (`DOCKER_EXEC_TIMEOUT`), output caps (`MAX_OUTPUT_BYTES`)

### 5. Demo Targets (right sub-column)
**Two validated environments:**

| Target | Services | Access | Infra |
|--------|----------|--------|-------|
| **Voting App** | vote (Flask), worker (.NET), redis, db (PostgreSQL), result (Node.js) | Docker exec | Local Docker Compose |
| **Mail App** | mailserver (Postfix+Dovecot), roundcube (PHP), db (PostgreSQL), redis | SSH | AWS EC2 (live) |

- YAML-driven profiles: service configs, known failure patterns, context commands, log hints
- Locust load testing suite: WebMailUser, SMTPUser, IMAPUser with round-trip verification

### 6. Experimental Validation (full-width)

**Fault Injection Experiments:**

| ID | Injected Fault | Target Service | Observable Impact | Agent Status |
|----|---------------|----------------|-------------------|--------------|
| EXP-01 | Full mailserver crash | mailserver | SMTP/IMAP/Web down | Designed |
| EXP-02 | PostgreSQL outage | db | Roundcube total failure | Designed |
| EXP-03 | Redis OOM (maxmemory=1mb) | redis | Silent session eviction | Designed |
| EXP-04 | Postfix message size (1KB) | mailserver | All sends fail | Designed |
| EXP-05 | Roundcube crash | roundcube | Web UI only | Designed |
| **EXP-06** | **Dovecot connection limit=1** | **mailserver** | **IMAP partial degradation** | **Confirmed** |

**EXP-06 Confirmed Result (highlight box):**
- Model: GPT-4.1 via OpenRouter | Cycles: 4 | Time: 136.5s | Cost: ~$0.49
- **Root cause correctly identified:** Dovecot `mail_max_userip_connections=1` causing mass IMAP login rejections
- Evidence: Dovecot logs showed repeated connection limit rejections matching Locust fault timeline
- Agent recommended: increase limit to 3–5, implement connection utilization alerts

### 7. Key Results (left sub-column)
- Agent correctly identified injected root cause with high confidence
- 4-cycle iterative investigation refined diagnosis
- Parallel specialist execution across log + runtime + docker domains
- Total cost per investigation: ~$0.49 (GPT-4.1)
- 136.5 seconds end-to-end for 4-cycle investigation
- Security layer blocked 0 legitimate commands, caught all test injection attempts

### 8. Conclusion & Future Work (right sub-column)
**Conclusions:**
- Multi-agent parallel dispatch enables faster, more thorough investigation than single-agent approaches
- LangGraph's `Send` API provides elegant dynamic fan-out based on LLM-planned subtasks
- Security-first design (allowlist + redaction) makes live container execution safe for LLM use
- YAML-driven profiles enable rapid deployment to new service environments

**Future Work:**
- Run EXP-01 through EXP-05; measure accuracy and MTTR across all fault types
- Add Kubernetes pod support (beyond Docker Compose)
- Implement human-in-the-loop approval for high-risk diagnostic commands
- Benchmark against manual triage and single-agent baselines
- Integrate with production alerting systems (PagerDuty, OpsGenie)

### FOOTER
- Key references (3–5): RCACopilot, FLASH, OpenRCA, MetaGPT/MA-RCA, LangGraph
- QR code linking to GitHub repo or paper

---

## 4. Graphics — What to Create

### Graphic A: Hero Architecture Diagram (hand-made, draw.io or Figma)
**Type:** Flowchart / system diagram
**Location:** Section 3 — centre column (the widest column)
**Size:** ~15" x 9" (fits the centre column)

**Content:**
```
                    ┌──────────────────┐
                    │   INCIDENT       │
                    │  DESCRIPTION     │
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │  PARENT AGENT    │◄──────────────────┐
                    │  (LLM Planner)   │                   │
                    │  Tools:          │                   │
                    │  • create_subtasks│                  │
                    │  • write_conclusion│                 │
                    └────────┬─────────┘                   │
                             │ fan-out                     │
                    ┌────────┴─────────┐                   │
                    ▼        ▼         ▼                   │
            ┌──────────┐ ┌──────────┐ ┌──────────┐        │
            │log_agent │ │ runtime  │ │ docker   │        │
            │          │ │ _status  │ │ _specs   │        │
            │ Reads:   │ │ Checks:  │ │ Audits:  │        │
            │ logs,    │ │ memory,  │ │ cgroups, │        │
            │ errors,  │ │ disk,    │ │ restarts,│        │
            │ patterns │ │ CPU, PIDs│ │ limits   │        │
            └────┬─────┘ └────┬─────┘ └────┬─────┘        │
                 └─────────────┼───────────┘               │
                               ▼                           │
                    ┌──────────────────┐                   │
                    │ SYNTHESIS AGENT  │                   │
                    │ Cross-domain     │───────────────────┘
                    │ correlation      │    (loop if needed)
                    │ → CycleSummary   │
                    └──────────────────┘
                               │ (on conclude)
                               ▼
                    ┌──────────────────┐
                    │  FINAL RCA       │
                    │  REPORT          │
                    └──────────────────┘
```

**Style:**
- Nodes: rounded rectangles, fill `#112240`, border `#64FFDA`, white text
- Edges: `#00B4D8` lines with arrow tips
- Parallel specialists: side-by-side with dashed grouping box labeled "Parallel Execution (Send fan-out)"
- Loop arrow: curved `#FF6B6B` dashed arrow from Synthesis back to Parent, labeled "Cycle N+1"
- Background: transparent (sits on `#0B1628` poster background)

**Tool:** draw.io (export as high-res PNG at 300 DPI) or Figma

---

### Graphic B: EXP-06 Evidence Panel (hand-made, PowerPoint/Figma)
**Type:** Annotated log excerpt + timeline
**Location:** Section 6 (experimental validation)
**Size:** ~24" x 3"

**Content:** Styled code block showing actual Locust output:
```
29  IMAP  imap.full_session  error('[UNAVAILABLE] Maximum number of
     connections from user+IP exceeded (mail_max_userip_connections=1)')
 3  IMAP  imap.full_session  abort('command: LOGIN => socket error: EOF')
 1  IMAP  imap.full_session  ConnectionResetError(10054, ...)
```

**Style:** Dark code block (`#0A0F1A`), teal monospace text, red highlights on error keywords

---

### Graphic C: Fault Injection Pipeline Diagram (hand-made)
**Type:** Horizontal pipeline / flow
**Location:** Section 6 (above results table)
**Size:** ~24" x 2.5"

**Content:**
```
[1. Inject Fault]  →  [2. Locust Load Test]  →  [3. RCA Agent Run]  →  [4. Compare to Ground Truth]
   dovecot              WebMail + SMTP +          Parent → Specialists     Root cause match?
   config change         IMAP users                → Synthesis → Report    Confidence score?
```

**Style:** Horizontal arrow flow, each step in a teal-bordered card, numbered

---

### Graphic D: AI-Generated Hero Visual (AI image generation)
**Type:** Atmospheric/conceptual illustration
**Location:** Title banner background or Section 3 background (subtle, low opacity)
**Size:** Full-width banner

**AI Image Generation Prompt (for DALL-E 3 / Midjourney):**

> **Prompt 1 (Title Banner Background):**
> "Abstract digital illustration of interconnected microservice nodes in a dark navy void, with glowing teal circuit-board traces connecting them. Some nodes pulse with red warning indicators. A central luminous AI brain node orchestrates diagnostic beams scanning each service. Minimal, clean, tech poster aesthetic. Dark background (#0B1628), teal (#64FFDA) and cyan (#00B4D8) glow effects. No text. Ultra-wide aspect ratio 27:6. High resolution, 300 DPI print quality."

> **Prompt 2 (Alternative — more abstract):**
> "Dark navy tech background with abstract flowing data streams in teal and cyan. Faint hexagonal grid pattern. Glowing nodes represent microservices connected by luminous pathways. One node pulses red indicating a fault, while diagnostic scan lines emanate from a central orchestrator. Minimalist, modern conference poster style. No text, no faces. Aspect ratio 40:4 (ultra-wide banner). Print quality."

> **Prompt 3 (Section 3 Background — subtle):**
> "Extremely subtle dark tech background texture: faint circuit-board trace pattern in dark navy (#112240) on deep navy (#0B1628). Barely visible hexagonal grid. Teal (#64FFDA) accent glow in corners. Abstract, minimal. No objects, no text. Seamless tileable pattern. High resolution print."

**Usage:** Generate at highest resolution, place behind title or architecture section at 10–20% opacity so it adds atmosphere without competing with content.

---

### Graphic E: Demo Target Architecture Mini-Diagrams (hand-made)
**Type:** Two small service topology diagrams
**Location:** Section 5 (Demo Targets)
**Size:** ~10" x 3" each

**Voting App:**
```
[User] → [vote :8080] → [redis] → [worker] → [db (PostgreSQL)]
                                                     ↓
                                              [result :8081] ← [User]
```

**Mail App:**
```
[User] → [roundcube :8080] → [mailserver (Postfix+Dovecot)]
              ↓                      ↓
          [db (PostgreSQL)]     [redis (sessions)]
```

**Style:** Small, clean, same node styling as main architecture diagram

---

### Graphic F: Key Metrics Callout Cards (hand-made, PowerPoint)
**Type:** Large-number callout boxes
**Location:** Section 7 (Key Results)
**Size:** 3 cards, each ~7" x 2.5"

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   136.5s    │  │    $0.49    │  │   4 cycles  │
│  end-to-end │  │  per run    │  │ to diagnose │
│ investigation│  │  (GPT-4.1)  │  │  root cause │
└─────────────┘  └─────────────┘  └─────────────┘
```

**Style:** Large teal numbers (60pt+), white caption text, `#112240` card backgrounds

---

## 5. File Deliverables

| # | File | Format | Tool |
|---|------|--------|------|
| 1 | Poster PPTX | 27"x40" PowerPoint | python-pptx (programmatic) |
| 2 | Architecture diagram | PNG 300 DPI | draw.io → export |
| 3 | EXP-06 evidence panel | PNG 300 DPI | Figma/PowerPoint |
| 4 | Fault injection pipeline | PNG 300 DPI | draw.io |
| 5 | Hero background | PNG 300 DPI | DALL-E 3 / Midjourney |
| 6 | Demo target mini-diagrams | PNG 300 DPI | draw.io |
| 7 | Metrics callout cards | Built into PPTX | python-pptx |

---

## 6. Implementation Steps

### Step 1: Create the PPTX poster skeleton
- Use `python-pptx` to create a 40"x27" landscape slide
- Set background to `#0B1628`
- Create all section panels as rounded rectangles with `#112240` fill, `#64FFDA` top border accent
- Place title banner, section boxes per layout above

### Step 2: Populate text content
- Fill each section with the content from Section 3 of this plan
- Apply typography: Montserrat/Poppins for headings, Inter for body, monospace for code
- Apply colour scheme: `#64FFDA` headings, `#CCD6F6` body, `#FFFFFF` title

### Step 3: Create placeholder image boxes
- Add placeholder rectangles for each graphic (A–F) with labels
- These will be replaced with actual graphics once generated

### Step 4: Provide AI image generation prompts
- Include the prompts from Section 4 Graphic D in a companion text file
- User generates images externally and drops them into the PPTX

### Step 5: Create hand-made diagram specs
- Provide draw.io XML or detailed specs for Graphics A, C, E
- Provide styled code block specs for Graphic B

---

## 7. Verification

- Open the generated PPTX in PowerPoint and verify:
  - Slide size is 40" x 27" landscape
  - Background is dark navy (`#0B1628`)
  - All 8 sections present with correct content
  - Colour scheme matches spec (teal headings, light body text)
  - Placeholder boxes visible for all graphics
  - Text is readable at conference viewing distance (~3–4 feet)
  - No text overflow or clipping
- Print a scaled test page to verify layout proportions
