"""
ui.py — Streamlit Observability UI for the RCA Framework
=========================================================
Visual layer for the LangGraph multi-agent RCA framework.

Layout:
  Sidebar  : all run inputs (profile, incident ID, incident text, cycles, concurrency)
             + live metrics once a run starts
  Center   : graph topology PNG → node status badges
  Right    : tabbed panel — Timeline (cycle accordion) | State | RCA Report | Config

Run from rca-framework/:
    streamlit run ui.py
"""

import base64
import importlib
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv(Path(__file__).parent / ".env")

# ── Auto-discover and register all specialist modules ──────────────────────────
_spec_dir = Path(__file__).parent / "core" / "agents" / "specialists"
for _f in sorted(_spec_dir.glob("*_agent.py")):
    if _f.stem != "base_specialist":
        importlib.import_module(f"core.agents.specialists.{_f.stem}")

from framework.loader import load_profile, list_profiles
from core.graph.builder import build_graph
from core.graph.registry import get_all
from core.graph.state import CycleSummary, GraphState, SpecialistFinding, Subtask

# ── Constants ──────────────────────────────────────────────────────────────────
PROFILES_DIR = Path(__file__).parent / "profiles"
PROFILES = list_profiles(PROFILES_DIR)

DEFAULT_INCIDENT = (
    "Users are reporting that the voting page loads but votes don't seem to be "
    "registering. The result page shows 0 votes for all options even after multiple "
    "clicks. The containers appear to be running but something in the pipeline "
    "between vote → redis → worker → db → result may be broken."
)

_STATUS = {
    "idle":    {"color": "#4b5563", "emoji": "○"},
    "running": {"color": "#d97706", "emoji": "◉"},
    "done":    {"color": "#059669", "emoji": "●"},
    "error":   {"color": "#dc2626", "emoji": "✕"},
}

# ── Page config & CSS ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Incident Investigator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  /* Pill-shaped agent status badges */
  .node-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 12px 3px 10px;
    border-radius: 20px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    font-weight: 600;
    color: #fff;
    margin: 2px 4px 2px 0;
    letter-spacing: 0.2px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
  }

  /* Confidence bar */
  .conf-track { background: #374151; height: 3px; border-radius: 2px; margin-top: 5px; margin-bottom: 8px; }
  .conf-fill  { height: 3px; border-radius: 2px; }

  /* Section divider labels */
  .section-label {
    font-size: 10px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1.5px; color: #6b7280; margin-bottom: 6px;
  }

  .pending-badge {
    display: inline-block;
    font-size: 10px; font-weight: 600; letter-spacing: 0.5px;
    color: #f59e0b; margin-left: 6px;
  }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
_DEFAULTS: dict = {
    "running":            False,
    "finished":           False,
    "events":             [],
    "node_status":        {},
    # per-node lists — one dict per cycle, never overwrite
    "node_outputs":       {},   # {node_name: [state_update, ...]}
    # structured accumulators (append-only during a run)
    "parent_outputs":     [],   # list[dict] — one entry per parent_agent invocation
    "findings":           [],   # list[SpecialistFinding] — all findings across all cycles
    "cycle_summaries":    [],   # list[CycleSummary] — all synthesis outputs
    "cumulative_history": "",   # latest cumulative_history from synthesis
    "final_report":       "",
    # graph/config — preserved across resets
    "graph":              None,
    "graph_png":          None,
    "graph_mermaid_source": "",
    "config":             None,
    "loaded_cfg":         None,
    # run metadata
    "elapsed":            None,
    "incident_id_used":   "",
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


def _reset_run() -> None:
    """Clear run state; preserve loaded graph/config."""
    preserve = {"graph", "graph_png", "graph_mermaid_source", "config", "loaded_cfg"}
    for k, v in _DEFAULTS.items():
        if k in preserve:
            continue
        st.session_state[k] = (
            [] if isinstance(v, list) else
            ({} if isinstance(v, dict) else v)
        )
    if st.session_state.graph:
        st.session_state.node_status = {
            n: "idle"
            for n in st.session_state.graph.get_graph().nodes
            if not n.startswith("__")
        }


# ── Hand-crafted Mermaid diagram (shows Send fan-out; LangGraph static PNG does not) ─
def _build_mermaid_source() -> str:
    """Build flowchart TD from specialist registry with all edges visible."""
    registry = get_all()
    lines = [
        "flowchart TD",
        "  startNode([__start__]) --> parent_agent",
    ]
    for entry in registry.values():
        lines.append(f'  parent_agent -->|"investigate (Send)"| {entry.node_name}')
    lines.append('  parent_agent -->|conclude| endNode([__end__])')
    for entry in registry.values():
        lines.append(f"  {entry.node_name} --> synthesis")
    lines.append("  synthesis --> parent_agent")
    return "\n".join(lines)


def _mermaid_source_to_png(mermaid_source: str) -> bytes | None:
    """Render Mermaid source to PNG via mermaid.ink API. Returns None on failure."""
    try:
        encoded = base64.urlsafe_b64encode(mermaid_source.encode("utf-8")).decode("ascii")
        url = f"https://mermaid.ink/img/{encoded}?type=png"
        req = Request(url, headers={"User-Agent": "RCA-Framework-UI/1.0"})
        with urlopen(req, timeout=10) as resp:
            return resp.read()
    except (URLError, OSError):
        return None


# ── Graph loader (cached in session state) ─────────────────────────────────────
def _load_graph(profile_name: str) -> None:
    if st.session_state.loaded_cfg == profile_name:
        return
    config = load_profile(PROFILES[profile_name])
    graph = build_graph(config)
    mermaid_source = _build_mermaid_source()
    png = _mermaid_source_to_png(mermaid_source)
    st.session_state.config = config
    st.session_state.graph = graph
    st.session_state.graph_png = png
    st.session_state.graph_mermaid_source = mermaid_source
    st.session_state.loaded_cfg = profile_name
    st.session_state.node_status = {
        n: "idle"
        for n in graph.get_graph().nodes
        if not n.startswith("__")
    }


# ── Sidebar — ALL inputs live here ────────────────────────────────────────────
def _sidebar() -> tuple[str, str, str, int, int, bool]:
    """Returns (profile_name, incident_id, incident, max_cycles, max_concurrency, run_clicked)."""
    with st.sidebar:
        st.title("🔍 Incident Investigator")
        st.caption("Multi-agent RCA · Powered by LangGraph")
        st.divider()

        cfg = st.selectbox(
            "Profile",
            list(PROFILES.keys()),
            help="Profile directory from profiles/ describing the target product",
        )

        incident_id = st.text_input(
            "Incident ID",
            value="",
            placeholder="Auto-generated if blank",
            help="Optional label for this run, e.g. INC-2024-001",
        )

        incident = st.text_area(
            "Incident Description",
            value=DEFAULT_INCIDENT,
            height=165,
            help="Describe the symptoms and affected services",
        )

        max_cycles = st.slider(
            "Max Investigation Cycles", min_value=1, max_value=5, value=3,
            help="How many plan → investigate → synthesise loops before forcing a conclusion",
        )

        with st.expander("⚙️ Advanced Settings"):
            max_conc = st.number_input(
                "Max Concurrency",
                min_value=1, max_value=20,
                value=int(os.environ.get("MAX_CONCURRENCY", "10")),
                help="Maximum specialist nodes running in parallel",
            )
            st.caption(f"Model: `{os.environ.get('LLM_MODEL', 'openai/gpt-4.1')}`")
            st.caption(f"Specialists: `{', '.join(get_all().keys())}`")

        st.divider()
        c1, c2 = st.columns(2)
        run = c1.button(
            "▶ Run" if not st.session_state.running else "⏳ Running…",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.running,
        )
        if c2.button("↺ Reset", use_container_width=True, disabled=st.session_state.running):
            _reset_run()
            st.rerun()

        if st.session_state.running or st.session_state.finished:
            st.divider()
            ca, cb = st.columns(2)
            ca.metric("Findings",   len(st.session_state.findings))
            cb.metric("Cycles",     len(st.session_state.cycle_summaries))
            done  = sum(1 for s in st.session_state.node_status.values() if s == "done")
            total = len(st.session_state.node_status)
            ca.metric("Nodes Done", f"{done}/{total}")
            if st.session_state.elapsed:
                cb.metric("Elapsed", f"{st.session_state.elapsed:.1f}s")
            if st.session_state.incident_id_used:
                st.caption(f"ID: `{st.session_state.incident_id_used}`")

    return cfg, incident_id.strip(), incident, max_cycles, int(max_conc), run


# ── Node status badge HTML ─────────────────────────────────────────────────────
def _badges_html() -> str:
    parts = []
    for node, status in st.session_state.node_status.items():
        s = _STATUS.get(status, _STATUS["idle"])
        parts.append(
            f'<span class="node-badge" style="background:{s["color"]}">'
            f'{s["emoji"]} {node}</span>'
        )
    return "".join(parts) or "<span style='color:#6b7280'>No nodes loaded.</span>"


# ── Cycle-grouped accordion ────────────────────────────────────────────────────
def _cycle_of_finding(f: SpecialistFinding) -> int:
    """Extract cycle number from subtask_id like 'c1-task-007'."""
    try:
        return int(f.subtask_id.split("-")[0][1:])
    except (ValueError, IndexError):
        return 1


def _render_finding_inline(f: SpecialistFinding) -> None:
    """Render a single SpecialistFinding: confidence bar + text + evidence + commands."""
    pct = int(f.confidence * 100)
    conf_color = "#059669" if pct >= 70 else "#d97706" if pct >= 40 else "#6b7280"
    st.markdown(
        f"<span style='color:{conf_color};font-weight:700'>{pct}% confidence</span>"
        f'<div class="conf-track"><div class="conf-fill" style="width:{pct}%;background:{conf_color}"></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f.findings)
    if f.evidence:
        with st.expander(f"Evidence ({len(f.evidence)})"):
            for e in f.evidence:
                st.markdown(f"- {e}")
    if f.commands_run:
        with st.expander(f"Commands run ({len(f.commands_run)})"):
            st.code("\n".join(f"$ {c}" for c in f.commands_run), language="bash")


def _render_cycle_timeline() -> None:
    """
    Cycle-grouped accordion.

    Outer expander per cycle → inner expanders:
      🔀 parent_agent — N subtasks dispatched   (collapsed)
      [agent_type] · [conf]% · [subtask_id]     (collapsed, one per SpecialistFinding)
      🔗 synthesis — N key findings              (collapsed)

    Latest cycle starts expanded; all others collapsed.
    Pending (in-flight) events are labelled with a live indicator.
    """
    events = st.session_state.events
    if not events:
        st.caption("Waiting for events…")
        return

    all_cycles = sorted(set(
        ev.get("_cycle", 1) for ev in events if ev.get("_cycle") is not None
    ))
    latest_cycle = all_cycles[-1] if all_cycles else 1

    # Set of node names currently marked running (for live indicator)
    running_nodes = {n for n, s in st.session_state.node_status.items() if s == "running"}

    for cycle_num in all_cycles:
        cycle_findings = [
            f for f in st.session_state.findings
            if _cycle_of_finding(f) == cycle_num
        ]
        cycle_summary = next(
            (cs for cs in st.session_state.cycle_summaries if cs.cycle_num == cycle_num),
            None,
        )
        # parent outputs for this cycle (investigate or conclude)
        cycle_parent_outs = [
            out for out in st.session_state.parent_outputs
            if out.get("current_cycle") == cycle_num
        ]

        n_findings = len(cycle_findings)
        is_latest = cycle_num == latest_cycle
        synth_label = " · synthesised" if cycle_summary else ""
        running_label = " ⏳" if is_latest and st.session_state.running else ""
        outer_label = (
            f"Cycle {cycle_num} — {n_findings} finding{'s' if n_findings != 1 else ''}"
            f"{synth_label}{running_label}"
        )

        with st.expander(outer_label, expanded=is_latest):
            for out in cycle_parent_outs:
                dec = out.get("parent_decision", "")
                subtasks: list = out.get("subtasks", [])

                if dec == "investigate":
                    pa_running = "parent_agent" in running_nodes
                    pa_label = f"🔀 parent_agent — {len(subtasks)} subtask(s) dispatched"
                    if pa_running:
                        pa_label += " ⏳"
                    with st.expander(pa_label, expanded=False):
                        for t in subtasks:
                            if isinstance(t, Subtask):
                                st.markdown(
                                    f"- **`{t.subtask_id}`** · `{t.service_name}` "
                                    f"→ `{t.assigned_agent}`  \n"
                                    f"  *Task:* {t.description}  \n"
                                    f"  *Hypothesis:* {t.hypothesis}"
                                )
                            elif isinstance(t, dict):
                                st.json(t)

                elif dec == "conclude":
                    with st.expander("✅ parent_agent — Writing conclusion", expanded=False):
                        if out.get("rca_finding"):
                            st.info(out["rca_finding"])

            # One inner expander per SpecialistFinding
            for f in cycle_findings:
                pct = int(f.confidence * 100)
                conf_color = "#059669" if pct >= 70 else "#d97706" if pct >= 40 else "#6b7280"
                f_label_plain = f"{f.agent_type} · {pct}% · {f.subtask_id}"
                with st.expander(f_label_plain, expanded=False):
                    _render_finding_inline(f)

            # Synthesis summary
            if cycle_summary:
                synth_running = "synthesis" in running_nodes
                s_label = f"🔗 synthesis — {len(cycle_summary.key_findings)} key finding(s)"
                if synth_running:
                    s_label += " ⏳"
                with st.expander(s_label, expanded=False):
                    st.markdown(cycle_summary.summary)
                    if cycle_summary.key_findings:
                        st.markdown("**Key Findings**")
                        for kf in cycle_summary.key_findings:
                            st.markdown(f"- {kf}")
                    if cycle_summary.recommendations:
                        st.markdown("**Recommendations**")
                        for r in cycle_summary.recommendations:
                            st.markdown(f"- {r}")
            elif is_latest and "synthesis" in running_nodes:
                st.caption("🔗 synthesis running…")


def _render_state_tab() -> None:
    """Global investigation state snapshot."""
    cfg = st.session_state.config
    if st.session_state.incident_id_used:
        st.markdown(f"**Incident ID:** `{st.session_state.incident_id_used}`")
    if cfg:
        st.markdown(f"**Product:** `{cfg.product}`  |  **Access:** `{cfg.access_method}`")
        st.markdown(
            "**Services:** " + " · ".join(f"`{s.service_name}`" for s in cfg.services)
        )
    st.markdown(f"**Model:** `{os.environ.get('LLM_MODEL', 'openai/gpt-4.1')}`")

    ca, cb = st.columns(2)
    ca.metric("Findings",   len(st.session_state.findings))
    cb.metric("Cycles",     len(st.session_state.cycle_summaries))
    done  = sum(1 for s in st.session_state.node_status.values() if s == "done")
    total = len(st.session_state.node_status)
    ca.metric("Nodes Done", f"{done}/{total}")
    if st.session_state.elapsed:
        cb.metric("Elapsed", f"{st.session_state.elapsed:.1f}s")

    if st.session_state.cumulative_history:
        with st.expander("Cumulative Investigation History"):
            st.text(st.session_state.cumulative_history)

    if cfg and not st.session_state.running:
        with st.expander("Service Configuration"):
            for svc in cfg.services:
                st.markdown(
                    f"**`{svc.service_name}`** · container: `{svc.container}`  \n"
                    f"{svc.description.strip()}"
                )


# ── Right panel: static (tabs Timeline | State | RCA Report) ──────────────────
def render_right_panel_static() -> None:
    """Unified right panel: cycle-grouped Timeline accordion + State + RCA Report."""
    has_report = bool(st.session_state.final_report)

    tab_labels = ["📋 Timeline", "📊 Status"]
    if has_report:
        tab_labels.append("📝 RCA Report")
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        _render_cycle_timeline()

    with tabs[1]:
        _render_state_tab()

    if has_report:
        with tabs[2]:
            st.markdown(st.session_state.final_report)


# ── Right panel: live (during streaming — cycle timeline + compact state) ───────
def render_right_panel_live(_latest_node: str) -> None:
    """Live view: cycle accordion (auto-expands latest cycle) + state metrics."""
    _render_cycle_timeline()
    st.divider()
    _render_state_tab()


# ── Event one-liners for the activity log ─────────────────────────────────────
def _summarize(node: str, upd: dict) -> str:
    if node == "parent_agent":
        dec = upd.get("parent_decision", "")
        if dec == "investigate":
            return (
                f"Dispatching {len(upd.get('subtasks', []))} subtask(s) "
                f"— cycle {upd.get('current_cycle', '?')}"
            )
        if dec == "conclude":
            return "Writing final RCA report"
        return f"Decision: {dec or 'planning…'}"
    if node == "synthesis":
        sums = upd.get("cycle_summaries", [])
        nkf  = len(getattr(sums[-1], "key_findings", [])) if sums else 0
        return f"Synthesised {nkf} key finding(s)"
    findings = [
        f for f in upd.get("current_cycle_findings", [])
        if isinstance(f, SpecialistFinding)
    ]
    if findings:
        snippet = findings[0].findings[:100].replace("\n", " ")
        return f"{int(findings[0].confidence * 100)}% confidence — {snippet}…"
    return "Completed"


# ── Mark only actually-dispatched nodes as running ────────────────────────────
def _mark_dispatched_running(subtasks: list) -> None:
    """Mark dispatched specialists as running; reset non-dispatched ones to idle."""
    registry = get_all()
    dispatched_nodes: set[str] = set()
    for t in subtasks:
        assigned = (
            t.assigned_agent if isinstance(t, Subtask)
            else t.get("assigned_agent") if isinstance(t, dict)
            else None
        )
        if assigned:
            entry = registry.get(assigned)
            if entry and entry.node_name in st.session_state.node_status:
                st.session_state.node_status[entry.node_name] = "running"
                dispatched_nodes.add(entry.node_name)
    # Reset specialists not dispatched this cycle so stale "done" badges don't linger
    for node_name in {e.node_name for e in registry.values()}:
        if node_name not in dispatched_nodes and node_name in st.session_state.node_status:
            st.session_state.node_status[node_name] = "idle"


# ── Streaming runner ───────────────────────────────────────────────────────────
def _run_stream(
    incident: str,
    incident_id: str,
    max_cycles: int,
    max_concurrency: int,
    status_ph,
    right_ph,
) -> None:
    graph  = st.session_state.graph
    config = st.session_state.config

    inc_id = incident_id or f"inc-{uuid.uuid4().hex[:6]}"
    st.session_state.incident_id_used = inc_id

    initial: GraphState = {
        "incident_id":            inc_id,
        "incident_summary":       incident,
        "product_config":         config.model_dump(),
        "subtasks":               [],
        "parent_decision":        "",
        "current_cycle":          0,
        "max_cycles":             max_cycles,
        "current_cycle_findings": [],
        "findings_offset":        0,
        "cycle_summaries":        [],
        "cumulative_history":     "",
        "rca_finding":            "",
        "final_report":           "",
    }

    t0 = datetime.now()
    current_cycle = 1

    def _repaint(latest: str | None = None) -> None:
        status_ph.markdown(_badges_html(), unsafe_allow_html=True)
        with right_ph.container():
            if latest:
                render_right_panel_live(latest)
            else:
                render_right_panel_static()

    # Seed: parent_agent is the first node to run
    st.session_state.node_status["parent_agent"] = "running"
    st.session_state.events.append({
        "_node": "parent_agent", "_ts": datetime.now().strftime("%H:%M:%S"),
        "_msg": "Planning investigation…", "_running": True, "_cycle": 1,
    })
    _repaint("parent_agent")

    for event in graph.stream(
        initial,
        config={"max_concurrency": max_concurrency},
        stream_mode="updates",
    ):
        for node_name, state_update in event.items():
            if node_name.startswith("__"):
                continue

            ts = datetime.now().strftime("%H:%M:%S")

            # Mark only the arriving node as done (no sweep — parallel specialists
            # must stay "running" until their own event arrives)
            st.session_state.node_status[node_name] = "done"

            # Append to per-node list (never overwrite — preserves all cycles)
            st.session_state.node_outputs.setdefault(node_name, []).append(state_update)

            # Accumulate into structured lists
            if node_name == "parent_agent":
                st.session_state.parent_outputs.append(state_update)
                current_cycle = state_update.get("current_cycle", current_cycle)

            for f in state_update.get("current_cycle_findings", []):
                if isinstance(f, SpecialistFinding):
                    st.session_state.findings.append(f)

            for cs in state_update.get("cycle_summaries", []):
                if isinstance(cs, CycleSummary):
                    st.session_state.cycle_summaries.append(cs)

            if state_update.get("cumulative_history"):
                st.session_state.cumulative_history = state_update["cumulative_history"]

            if state_update.get("final_report"):
                st.session_state.final_report = state_update["final_report"]

            # Precisely mark what runs next
            dec = state_update.get("parent_decision", "")
            if dec == "investigate":
                _mark_dispatched_running(state_update.get("subtasks", []))
            elif node_name == "synthesis":
                st.session_state.node_status["parent_agent"] = "running"
            elif node_name != "parent_agent" and "synthesis" in st.session_state.node_status:
                st.session_state.node_status["synthesis"] = "running"

            st.session_state.events.append({
                "_node": node_name, "_ts": ts,
                "_msg":  _summarize(node_name, state_update),
                "_cycle": current_cycle,
            })

            _repaint(latest=node_name)

    # Clean up any lingering "running" markers
    for n in st.session_state.node_status:
        if st.session_state.node_status[n] == "running":
            st.session_state.node_status[n] = "done"

    st.session_state.elapsed  = (datetime.now() - t0).total_seconds()
    st.session_state.running  = False
    st.session_state.finished = True
    _repaint()


# ── Main layout ────────────────────────────────────────────────────────────────
def main() -> None:
    cfg_name, incident_id, incident, max_cycles, max_concurrency, run_clicked = _sidebar()

    if PROFILES:
        _load_graph(cfg_name)

    center, right = st.columns([11, 9])

    # ── Center: graph + node status only ──────────────────────────────────────
    with center:
        with st.container(border=True):
            st.markdown(
                '<div class="section-label">Agent Graph</div>',
                unsafe_allow_html=True,
            )
            if st.session_state.graph_png:
                st.image(st.session_state.graph_png, use_container_width=True)
            elif st.session_state.get("graph_mermaid_source"):
                st.code(
                    st.session_state.graph_mermaid_source,
                    language="text",
                )
            else:
                st.caption("Select a profile to load the graph.")

        st.markdown('<div class="section-label">Live Agent Status</div>', unsafe_allow_html=True)
        status_placeholder = st.empty()
        status_placeholder.markdown(_badges_html(), unsafe_allow_html=True)

    # ── Right: unified Activity + Inspector (one placeholder) ───────────────────
    with right:
        st.markdown('<div class="section-label">Investigation Feed</div>', unsafe_allow_html=True)
        right_panel_placeholder = st.empty()

    # ── Trigger run or render static right panel ────────────────────────────────
    if run_clicked and not st.session_state.running:
        _reset_run()
        st.session_state.running = True
        _run_stream(
            incident, incident_id, max_cycles, max_concurrency,
            status_placeholder, right_panel_placeholder,
        )
        st.rerun()
    else:
        with right_panel_placeholder.container():
            render_right_panel_static()


if __name__ == "__main__":
    main()
