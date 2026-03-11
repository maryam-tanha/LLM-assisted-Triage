# RCA Framework Observability UI

This document walks through the Streamlit-based UI for the multi-agent Root Cause
Analysis framework. Each section corresponds to a visible panel or feature in the
interface.

To start the UI, run the following from the `rca-framework/` directory:

    streamlit run ui.py

## Layout

The page uses a wide three-region layout: a persistent sidebar on the left for all
run inputs, a center column showing the agent graph and node status, and a right
column with the combined activity and inspection panel.

| Sidebar            | Center (55%)          | Right (45%)                 |
|--------------------|-----------------------|-----------------------------|
| Inputs + metrics   | Graph topology        | Timeline / State / Report   |
|                    | Node status badges    |                             |

## Sidebar

All inputs needed to configure and start a run are collected here, centralizing configuration and keeping the main workspace uncluttered.

### Service Config

A dropdown listing every `.yaml` file found in the `configs/` directory. Selecting
a config loads the service definitions for that target environment, compiles the
LangGraph agent graph, and renders the topology diagram. Switching configs rebuilds
the graph without clearing the other inputs.

### Incident ID

A short text field for labelling the run, such as `INC-2024-001`. Leaving it blank
causes the system to generate a random ID at run time (for example, `inc-a3f9b1`).
The ID used is shown below the metrics once the run is active.

### Incident Description

A text area pre-filled with a representative voting-app incident. This is the
natural-language description passed to the parent orchestrator as its starting
context. Write symptoms and affected services here, not suspected causes.

### Max Investigation Cycles

A slider from 1 to 5 (default 3). One cycle covers a full round of planning,
parallel specialist execution, and synthesis. The parent agent will write a
conclusion after this many cycles regardless of its internal confidence. Setting
this higher allows the agent to investigate more thoroughly before concluding.

### Advanced Settings

Collapsed by default under an expander. Contains one tunable parameter:

**Max Concurrency** sets how many specialist agent nodes may run at the same time.
The default is read from the `MAX_CONCURRENCY` environment variable, falling back
to 10. The expander also displays the active LLM model name and the registered
specialist types as a quick reference.

### Run and Reset

The **Run** button starts the investigation. It is disabled while a run is in
progress and relabels itself to signal that the system is working. The **Reset**
button clears all output from the previous run while keeping the loaded graph and
config intact. Both buttons are disabled during an active run so they cannot be
triggered accidentally.

### Live Metrics

Once a run starts, four metric tiles appear below the buttons and update throughout:

- **Findings** -- total `SpecialistFinding` objects collected across all cycles
- **Cycles** -- number of completed investigation loops
- **Nodes Done** -- completed nodes as a fraction of the total (e.g., `3/4`)
- **Elapsed** -- wall-clock seconds since the run began

## Graph Topology

A diagram of the agent graph rendered from the active service config.

The diagram is a dynamically generated Mermaid `flowchart TD` constructed at load time from
the specialist registry. It shows the full execution path:

```
__start__ --> parent_agent
parent_agent --> log_specialist              (investigate branch, Send fan-out)
parent_agent --> runtime_status_specialist   (investigate branch, Send fan-out)
log_specialist --> synthesis
runtime_status_specialist --> synthesis
synthesis --> parent_agent                   (loop back)
parent_agent --> __end__                     (conclude branch)
```

LangGraph's built-in `draw_mermaid_png()` does not show these specialist edges
because the `Send` fan-out from `parent_agent` is resolved at runtime, not at
compile time. The static export only sees the conditional edge declaration, not
where it routes. Constructing the diagram dynamically from the registry solves this.

The Mermaid source is sent to the `mermaid.ink` API to produce a PNG. If that
request fails (no internet connection), the raw Mermaid source is shown as a code
block so the topology remains readable.

## Node Status Badges

A row of color-coded pill badges below the graph, one per agent node. The
`__start__` and `__end__` sentinels are excluded.

| State   | Color | Symbol | Meaning                          |
|---------|-------|--------|----------------------------------|
| idle    | gray  | o      | Not yet invoked this run         |
| running | amber | filled | Currently executing               |
| done    | green | filled | Completed                        |
| error   | red   | x      | Raised an exception              |

Badges update after each node completes. Only the specialist nodes actually
dispatched in a given cycle are marked running. Nodes not chosen for that cycle
reset to idle, preventing outdated statuses from persisting and causing confusion.

## Activity and Inspector Panel

The right column combines the activity log and node inspector into a single
tabbed panel. During a run, it updates after every node event. After the run
finishes, it transitions to a readable static view.

### Timeline Tab

The main view. Events are grouped by investigation cycle, each in an outer
expander. The latest cycle starts expanded; earlier ones are collapsed.

The outer expander header for each cycle shows the cycle number, the number of
findings produced, whether synthesis has completed, and a spinning indicator if
the cycle is still active.

Inside each cycle, three layers of nested expanders appear in sequence:

**parent_agent decision**
The orchestrator's planning output. When the decision is `investigate`, it shows
each subtask dispatched: the subtask ID, target service, assigned specialist type,
the specific task description, and the hypothesis behind why that service was
chosen. When the decision is `conclude`, it shows the RCA finding the agent wrote.

**Specialist findings**
One expander per `SpecialistFinding`, labelled with agent type, confidence
percentage, and subtask ID. Inside each:

- A confidence bar, color-coded green (70% or above), amber (40 to 69%), or gray
  (below 40%)
- The agent's written analysis
- An expandable list of supporting evidence (log lines, observations)
- An expandable code block of the shell commands that were run inside the container

**Synthesis output**
The synthesis agent's cross-service correlation for the cycle. Shows a narrative
summary, a bulleted list of key findings, and recommended next steps. If synthesis
is still running, a status indicator is displayed instead.

### State Tab

A snapshot of the investigation configuration and progress.

Shown fields: incident ID, product name, access method, service list, LLM model,
the same four metric tiles from the sidebar, a cumulative investigation history
built up by the synthesis agent across cycles, and a service configuration table
listing each service with its container name and description. The service table is
hidden while a run is active to keep the view focused on live data.

### RCA Report Tab

The final report generated by the parent agent after it completes its investigation. Rendered
as Markdown. This tab only appears once a final report exists. It contains the
agent's full explanation of the root cause, the evidence that led to it, and
recommended remediation steps.

## Live Streaming

The system calls `graph.stream(..., stream_mode="updates")` which yields one event
per completed node. Each event contains only that node's state delta, not the full
accumulated graph state. Consequently, accessing the full history
requires the session-state accumulators rather than the raw event payloads.

During a run, after each event:

1. Node badges update to reflect the latest status
2. The right panel re-renders with the updated cycle timeline and state metrics
3. The latest cycle expander stays open so new activity is always visible

All findings, cycle summaries, and parent outputs are appended to separate lists in
session state. Nothing is overwritten between cycles. This ensures the complete
history across all cycles remains visible in the Timeline tab once the run finishes.

After completion, a final page rerun switches the right panel from live mode to
static mode, which adds the tabbed interface and, if a report was produced, the
RCA Report tab.