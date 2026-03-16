"""
1_🛠_Profile_Manager.py — Full-page structured profile manager for RCA Framework.
===================================================================================
Provides form-based editing for all profile entities (services, agents, prompts)
and end-to-end new specialist creation without touching any Python files manually.

Accessible from the Streamlit sidebar when running:
    streamlit run ui.py
"""

import importlib
import io
import re
import sys
import uuid
import zipfile
from pathlib import Path

import streamlit as st
import yaml
from dotenv import load_dotenv

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))
load_dotenv(_ROOT / ".env")

# Dynamically discover and register all specialists
_spec_dir = _ROOT / "core" / "agents" / "specialists"
for _f in sorted(_spec_dir.glob("*_agent.py")):
    if _f.stem != "base_specialist":
        importlib.import_module(f"core.agents.specialists.{_f.stem}")

from framework.loader import load_profile, list_profiles  # noqa: E402

PROFILES_DIR = _ROOT / "profiles"
SPECIALISTS_DIR = _ROOT / "core" / "agents" / "specialists"

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Profile Manager", page_icon="🛠", layout="wide")
st.markdown("""
<style>
  /* Field group labels */
  .ce-label {
    font-size: 10px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1.2px; color: #9ca3af; margin-bottom: 4px;
  }

  /* Compact profile selector bar */
  .profile-bar {
    display: flex;
    align-items: flex-end;
    gap: 0.75rem;
    padding: 1rem 1.25rem;
    background: #1e2130;
    border: 1px solid #2d3348;
    border-radius: 10px;
    margin-bottom: 1.25rem;
  }

  /* Hide Streamlit's default page top padding so our custom header sits flush */
  .block-container { padding-top: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# ── New specialist system prompt template ──────────────────────────────────────
_PROMPT_TEMPLATE = """\
You are a {title} Specialist agent in an automated Root Cause Analysis (RCA) framework.

Your role is to investigate [describe your investigation domain here].

## Your Capabilities

You have access to a single tool: `run_command`. Use it to execute read-only shell
commands inside the target container. Commands are validated against a security allowlist.
If a command is blocked, you will receive "BLOCKED: <reason>" as the result.

Allowed command families: [list the commands your specialist will use]

Do not attempt write operations, privilege escalation, or network access.

## Initial Context

You will receive pre-collected output from context commands run at the start of the
investigation. Review all context before calling any tools.

## Investigation Process

1. Review all initial context output before calling any tools.
2. Focus your analysis on: [key signals, metrics, or patterns]
3. Use run_command to drill deeper into specific areas as needed.
4. Stop calling tools once you have enough evidence to form a conclusion.

## Output Format

Your final response MUST end with this exact structure (do not omit any section):

CONFIDENCE: <float between 0.0 and 1.0>
EVIDENCE:
- <exact output line or observation that supports your finding 1>
- <exact output line or observation that supports your finding 2>
SUMMARY:
<Markdown-formatted summary including: what you found (or ruled out), probable
root cause if evidence supports one, gaps in evidence, recommendations.>

## Confidence Calibration

- 0.9-1.0: Clear definitive evidence confirming root cause
- 0.7-0.9: Strong signals with consistent pattern
- 0.5-0.7: Partial evidence, moderate confidence
- 0.3-0.5: Weak signals, mostly inconclusive
- 0.0-0.3: No relevant evidence found

## Important

- Never invent data. Only quote values you actually observed in command output.
- Keep evidence excerpts short and precise — one line each.
- Focus on the specific service named in the subtask, not unrelated system metrics.
"""


# ── YAML I/O helpers ───────────────────────────────────────────────────────────

def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _save_yaml(path: Path, data: dict) -> None:
    path.write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


def _zip_profile(profile_path: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in profile_path.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(profile_path.parent))
    return buf.getvalue()


def _update_profile_services(profile_path: Path, services: list[dict]) -> None:
    raw = _load_yaml(profile_path / "profile.yaml")
    raw["services"] = services
    _save_yaml(profile_path / "profile.yaml", raw)


def _clear_editor_state() -> None:
    """Delete all config editor session state keys (called on profile switch)."""
    stale = [k for k in st.session_state if k.startswith("_ce_")]
    for k in stale:
        del st.session_state[k]


def _clear_keys_with(substring: str) -> None:
    stale = [k for k in st.session_state if substring in k]
    for k in stale:
        del st.session_state[k]


# ── List editor widget ─────────────────────────────────────────────────────────

def _list_editor(key: str, default: list[str], label: str, placeholder: str = "") -> list[str]:
    """
    Editable list of strings. Uses UUID-keyed items to avoid index-shift bugs on delete.
    Reads from / writes to st.session_state. Returns the current list value.
    """
    sk = f"_ce_le_{key}"
    if sk not in st.session_state:
        st.session_state[sk] = [{"id": str(uuid.uuid4()), "val": v} for v in default]

    items: list[dict] = st.session_state[sk]
    to_delete = None

    for item in items:
        c1, c2 = st.columns([9, 1])
        with c1:
            wk = f"_ce_le_{key}_{item['id']}"
            new_val = st.text_input(
                "", value=item["val"], placeholder=placeholder,
                label_visibility="collapsed", key=wk,
            )
            item["val"] = new_val
        with c2:
            if st.button("✕", key=f"_ce_led_{key}_{item['id']}", help="Remove"):
                to_delete = item["id"]

    if to_delete:
        st.session_state[sk] = [x for x in items if x["id"] != to_delete]
        st.rerun()

    if st.button(f"＋ Add {label}", key=f"_ce_leadd_{key}"):
        st.session_state[sk].append({"id": str(uuid.uuid4()), "val": ""})
        st.rerun()

    return [x["val"] for x in st.session_state[sk]]


# ── Known failures editor ──────────────────────────────────────────────────────

def _known_failures_editor(key: str, default: list[dict]) -> list[dict]:
    """Two-column editable list for known_failures (pattern + likely_cause)."""
    sk = f"_ce_kf_{key}"
    if sk not in st.session_state:
        st.session_state[sk] = [
            {
                "id": str(uuid.uuid4()),
                "pattern": f.get("pattern", ""),
                "likely_cause": f.get("likely_cause", ""),
            }
            for f in default
        ]

    items: list[dict] = st.session_state[sk]
    to_delete = None

    if items:
        h1, h2, _ = st.columns([4, 5, 1])
        h1.markdown('<div class="ce-label">Error Pattern</div>', unsafe_allow_html=True)
        h2.markdown('<div class="ce-label">Likely Cause</div>', unsafe_allow_html=True)

    for item in items:
        c1, c2, c3 = st.columns([4, 5, 1])
        with c1:
            pk = f"_ce_kf_{key}_{item['id']}_p"
            item["pattern"] = st.text_input(
                "", value=item["pattern"], placeholder="e.g. Out of memory",
                label_visibility="collapsed", key=pk,
            )
        with c2:
            ck = f"_ce_kf_{key}_{item['id']}_c"
            item["likely_cause"] = st.text_input(
                "", value=item["likely_cause"], placeholder="e.g. Memory leak in worker",
                label_visibility="collapsed", key=ck,
            )
        with c3:
            if st.button("✕", key=f"_ce_kfd_{key}_{item['id']}", help="Remove"):
                to_delete = item["id"]

    if to_delete:
        st.session_state[sk] = [x for x in items if x["id"] != to_delete]
        st.rerun()

    if st.button("＋ Add Known Failure", key=f"_ce_kfadd_{key}"):
        st.session_state[sk].append(
            {"id": str(uuid.uuid4()), "pattern": "", "likely_cause": ""}
        )
        st.rerun()

    return [
        {"pattern": x["pattern"], "likely_cause": x["likely_cause"]}
        for x in st.session_state[sk]
    ]


# ── Specialist Python generator ────────────────────────────────────────────────

def _generate_specialist_py(agent_type: str, context_commands: list[str], description: str) -> str:
    class_name = "".join(w.capitalize() for w in agent_type.split("_")) + "Agent"
    node_name = f"{agent_type}_specialist"
    ctx_repr = repr(context_commands)
    desc_clean = description.replace('"', '\\"').replace("\n", " ")

    return f"""\
from core.agents.specialists.base_specialist import BaseSpecialist
from core.graph.registry import SpecialistRegistration, register


class {class_name}(BaseSpecialist):
    \"\"\"Specialist agent: {description[:80].strip()}.\"\"\"

    @property
    def agent_type(self) -> str:
        return "{agent_type}"

    @property
    def prompt_file(self) -> str:
        # Kept for backward compatibility; prompt comes from profile YAML.
        return "{agent_type}_system.txt"

    @property
    def context_commands(self) -> list[str]:
        # Fallback used when a service has no context_commands in the YAML.
        return {ctx_repr}


def {node_name}_node(state: dict) -> dict:
    \"\"\"LangGraph node for the {class_name}.\"\"\"
    finding = {class_name}().run_docker(
        subtask_id=state["subtask_id"],
        subtask_description=state["subtask_description"],
        container=state["container"],
        service_context=state.get("service_context", {{}}),
        system_prompt=state.get("system_prompt", ""),
    )
    return {{"current_cycle_findings": [finding]}}


register(
    SpecialistRegistration(
        agent_type="{agent_type}",
        description=(
            "{desc_clean}"
        ),
        node_name="{node_name}",
        node_fn={node_name}_node,
    )
)
"""


# ── Profile creation helper ────────────────────────────────────────────────────

def _create_new_profile(profile_path: Path, name: str) -> None:
    profile_path.mkdir(parents=True, exist_ok=True)
    (profile_path / "agents").mkdir(exist_ok=True)
    _save_yaml(profile_path / "profile.yaml", {
        "profile_name": name,
        "product": name,
        "access_method": "docker_exec",
        "services": [],
    })
    _save_yaml(profile_path / "parent.yaml", {
        "role": "parent",
        "system_prompt": (
            "You are the Parent Agent responsible for orchestrating the RCA investigation."
        ),
    })
    _save_yaml(profile_path / "synthesis.yaml", {
        "role": "synthesis",
        "system_prompt": (
            "You are the Synthesis Agent responsible for correlating specialist findings."
        ),
    })


# ── Tab: Profile ───────────────────────────────────────────────────────────────

def _tab_profile(profile_path: Path, config) -> None:
    st.markdown("Edit the top-level product settings for this profile.")
    st.divider()

    pn   = st.text_input("Profile Name",   value=config.profile_name, key="_ce_t_pname")
    prod = st.text_input("Product",        value=config.product,       key="_ce_t_prod")
    access = st.selectbox(
        "Access Method", ["docker_exec", "ssh"],
        index=["docker_exec", "ssh"].index(config.access_method),
        key="_ce_t_access",
        help="docker_exec: run commands via `docker exec`. ssh: connect to remote VMs.",
    )

    st.divider()
    if st.button("💾 Save Profile Settings", type="primary", key="_ce_t_save_profile"):
        raw = _load_yaml(profile_path / "profile.yaml")
        raw.update(profile_name=pn, product=prod, access_method=access)
        _save_yaml(profile_path / "profile.yaml", raw)
        st.success("Profile settings saved.")


# ── Tab: Services ──────────────────────────────────────────────────────────────

def _tab_services(profile_path: Path) -> None:
    raw = _load_yaml(profile_path / "profile.yaml")
    services: list[dict] = raw.get("services", [])

    if st.button("＋ Add Service", key="_ce_t_add_svc", type="secondary"):
        new_idx = len(services) + 1
        services.append({
            "service_name": f"new_service_{new_idx}",
            "description": "",
            "container": "",
            "expected_behavior": "",
            "context_commands": [],
            "log_hints": [],
            "known_failures": [],
        })
        _update_profile_services(profile_path, services)
        st.rerun()

    if not services:
        st.caption("No services defined. Click **＋ Add Service** to get started.")
        return

    st.divider()

    for svc in services:
        svc_name = svc.get("service_name", "")
        k = re.sub(r"[^a-z0-9_]", "_", svc_name.lower())

        with st.expander(f"**{svc_name}**", expanded=False):
            svc_name_new = st.text_input(
                "Service Name", value=svc_name, key=f"_ce_s_{k}_name",
                help="Unique identifier used in subtask assignments.",
            )
            desc = st.text_area(
                "Description", value=svc.get("description", ""),
                height=80, key=f"_ce_s_{k}_desc",
                help="What this service does — shown to the parent LLM.",
            )
            container = st.text_input(
                "Container", value=svc.get("container", ""),
                key=f"_ce_s_{k}_container",
                help="Docker container name used for `docker exec` commands.",
            )
            expected = st.text_area(
                "Expected Behavior", value=svc.get("expected_behavior", ""),
                height=100, key=f"_ce_s_{k}_expected",
                help="Detailed description of normal operation — helps the LLM detect anomalies.",
            )

            st.markdown("**Context Commands** — pre-run diagnostic commands for this service")
            ctx_cmds = _list_editor(
                f"s_{k}_ctx", svc.get("context_commands", []),
                "Command", placeholder="e.g. redis-cli INFO",
            )

            st.markdown("**Log Hints** — investigation guidance passed to the specialist LLM")
            log_hints = _list_editor(
                f"s_{k}_hints", svc.get("log_hints", []),
                "Hint", placeholder="e.g. Look for WRONGTYPE errors in logs",
            )

            st.markdown("**Known Failures** — patterns the LLM should recognize immediately")
            known_failures = _known_failures_editor(f"s_{k}", svc.get("known_failures", []))

            st.divider()
            bc1, bc2 = st.columns([3, 1])
            with bc1:
                if st.button("💾 Save Service", key=f"_ce_s_{k}_save", type="primary"):
                    updated = {
                        "service_name": svc_name_new.strip(),
                        "description": desc.strip(),
                        "container": container.strip(),
                        "expected_behavior": expected.strip(),
                        "context_commands": [c for c in ctx_cmds if c.strip()],
                        "log_hints": [h for h in log_hints if h.strip()],
                        "known_failures": [
                            f for f in known_failures
                            if f["pattern"].strip() or f["likely_cause"].strip()
                        ],
                    }
                    updated_svcs = [
                        updated if s.get("service_name") == svc_name else s
                        for s in services
                    ]
                    _update_profile_services(profile_path, updated_svcs)
                    # Clear list-editor state so it re-inits from freshly saved data
                    _clear_keys_with(f"_ce_le_s_{k}_")
                    _clear_keys_with(f"_ce_kf_s_{k}")
                    st.success(f"Service '{svc_name_new.strip()}' saved.")
                    st.rerun()

            with bc2:
                if st.button("🗑 Delete", key=f"_ce_s_{k}_del"):
                    st.session_state[f"_ce_s_{k}_confirm"] = True

            if st.session_state.get(f"_ce_s_{k}_confirm"):
                st.warning(f"Delete **{svc_name}**? This cannot be undone.")
                cd1, cd2 = st.columns(2)
                with cd1:
                    if st.button("Yes, delete", key=f"_ce_s_{k}_confirm_yes", type="primary"):
                        _update_profile_services(
                            profile_path,
                            [s for s in services if s.get("service_name") != svc_name],
                        )
                        del st.session_state[f"_ce_s_{k}_confirm"]
                        st.rerun()
                with cd2:
                    if st.button("Cancel", key=f"_ce_s_{k}_confirm_no"):
                        del st.session_state[f"_ce_s_{k}_confirm"]
                        st.rerun()


# ── Tab: Agents ────────────────────────────────────────────────────────────────

def _tab_agents(profile_path: Path) -> None:
    agents_dir = profile_path / "agents"
    agents_dir.mkdir(exist_ok=True)
    agent_files = sorted(agents_dir.glob("*.yaml"))
    existing_types = {_load_yaml(f).get("agent_type", f.stem) for f in agent_files}

    # ── Section 1: Existing agents ────────────────────────────────────────────
    st.markdown("### Existing Agents")

    if not agent_files:
        st.caption("No agents defined yet. Create one in the section below.")
    else:
        for agent_file in agent_files:
            raw = _load_yaml(agent_file)
            at = raw.get("agent_type", agent_file.stem)
            k = re.sub(r"[^a-z0-9_]", "_", at.lower())
            preview = raw.get("description", "")[:60]

            with st.expander(f"**{at}** — {preview}…", expanded=False):
                st.text_input(
                    "Agent Type (read-only)", value=at, disabled=True,
                    key=f"_ce_a_{k}_type",
                )
                desc = st.text_area(
                    "Description", value=raw.get("description", ""),
                    height=80, key=f"_ce_a_{k}_desc",
                    help="Shown to the parent LLM to decide when to assign tasks to this specialist.",
                )
                when = st.text_area(
                    "When to Use", value=raw.get("when_to_use", ""),
                    height=110, key=f"_ce_a_{k}_when",
                )
                dont = st.text_area(
                    "Do Not Use", value=raw.get("do_not_use", ""),
                    height=90, key=f"_ce_a_{k}_dont",
                )
                prompt = st.text_area(
                    "System Prompt", value=raw.get("system_prompt", ""),
                    height=380, key=f"_ce_a_{k}_prompt",
                )

                st.divider()
                ac1, ac2 = st.columns([3, 1])
                with ac1:
                    if st.button("💾 Save Agent", key=f"_ce_a_{k}_save", type="primary"):
                        _save_yaml(agent_file, {
                            "agent_type": at,
                            "description": desc.strip(),
                            "when_to_use": when,
                            "do_not_use": dont,
                            "system_prompt": prompt,
                        })
                        st.success(f"Agent '{at}' saved.")

                with ac2:
                    if st.button("🗑 Delete", key=f"_ce_a_{k}_del"):
                        st.session_state[f"_ce_a_{k}_confirm"] = True

                if st.session_state.get(f"_ce_a_{k}_confirm"):
                    st.warning(f"Delete agent **{at}**? This removes the YAML file.")
                    cd1, cd2 = st.columns(2)
                    with cd1:
                        if st.button("Yes, delete", key=f"_ce_a_{k}_confirm_yes", type="primary"):
                            agent_file.unlink()
                            del st.session_state[f"_ce_a_{k}_confirm"]
                            st.rerun()
                    with cd2:
                        if st.button("Cancel", key=f"_ce_a_{k}_confirm_no"):
                            del st.session_state[f"_ce_a_{k}_confirm"]
                            st.rerun()

    st.divider()

    # ── Section 2: Create new specialist ──────────────────────────────────────
    st.markdown("### ✚ Create New Specialist")
    st.caption(
        "Fills in the YAML config and generates the Python module automatically. "
        "Reload the page after creation for the specialist to be active."
    )

    with st.expander("New Specialist Form", expanded=False):
        new_at = st.text_input(
            "Agent Type", key="_ce_new_at",
            placeholder="e.g. network_check",
            help="Lowercase letters, numbers, and underscores only. Must be unique.",
        )

        # Live validation feedback
        at_valid = bool(re.match(r"^[a-z][a-z0-9_]+$", new_at or ""))
        at_unique = new_at not in existing_types
        if new_at:
            if not at_valid:
                st.error("Must match `^[a-z][a-z0-9_]+$` (lowercase, no spaces or hyphens)")
            elif not at_unique:
                st.error(f"Agent type '{new_at}' already exists in this profile")
            else:
                st.success(f"✓ '{new_at}' is available")

        new_desc = st.text_area(
            "Description", height=80, key="_ce_new_desc",
            placeholder=(
                "2-3 sentences describing what this specialist investigates "
                "and what symptoms should trigger it."
            ),
        )
        new_when = st.text_area(
            "When to Use", height=100, key="_ce_new_when",
            placeholder="- When investigating X\n- When service shows Y behavior",
        )
        new_dont = st.text_area(
            "Do Not Use (optional)", height=80, key="_ce_new_dont",
            placeholder="- When investigating Z (use log specialist instead)",
        )

        st.markdown("**Fallback Context Commands**")
        st.caption("Used when a service YAML has no `context_commands` defined.")
        new_ctx = _list_editor(
            "new_spec_ctx", [], "Command",
            placeholder="e.g. netstat -an | head -50",
        )

        title = new_at.replace("_", " ").title() if new_at else ""
        default_prompt = _PROMPT_TEMPLATE.format(title=title)
        new_prompt = st.text_area(
            "System Prompt", value=default_prompt, height=380, key="_ce_new_prompt",
        )

        # Python file preview
        can_preview = new_at and at_valid and at_unique
        if can_preview:
            with st.expander("Preview: Generated Python File", expanded=False):
                py_src = _generate_specialist_py(
                    agent_type=new_at,
                    context_commands=[c for c in new_ctx if c.strip()],
                    description=new_desc.strip(),
                )
                st.code(py_src, language="python")

        st.divider()
        can_create = can_preview and new_desc.strip() and new_prompt.strip()
        if st.button(
            "✚ Create Specialist",
            type="primary",
            disabled=not can_create,
            key="_ce_create_btn",
        ):
            ctx_clean = [c for c in new_ctx if c.strip()]

            # 1. Write YAML to profile agents/
            _save_yaml(
                profile_path / "agents" / f"{new_at}.yaml",
                {
                    "agent_type": new_at,
                    "description": new_desc.strip(),
                    "when_to_use": new_when.strip(),
                    "do_not_use": new_dont.strip(),
                    "system_prompt": new_prompt,
                },
            )

            # 2. Write Python module to core/agents/specialists/
            py_path = SPECIALISTS_DIR / f"{new_at}_agent.py"
            py_src = _generate_specialist_py(new_at, ctx_clean, new_desc.strip())
            py_path.write_text(py_src, encoding="utf-8")

            yaml_path = profile_path / "agents" / f"{new_at}.yaml"
            st.success(f"✓ Specialist '{new_at}' created successfully!")
            st.info(
                "Reload the page (press **F5** or use the browser refresh button) "
                "for the new specialist to become active in the investigation graph."
            )
            with st.expander("Files Created"):
                st.code(
                    f"YAML:   {yaml_path}\nPython: {py_path}",
                    language="text",
                )


# ── Tab: Prompts ───────────────────────────────────────────────────────────────

def _tab_prompts(profile_path: Path) -> None:
    st.markdown(
        "Edit the system prompts for the **Parent Agent** (orchestrator) and "
        "**Synthesis Agent** (cross-domain correlator)."
    )
    st.divider()

    for fname, label, role in [
        ("parent.yaml", "Parent Agent Prompt", "parent"),
        ("synthesis.yaml", "Synthesis Agent Prompt", "synthesis"),
    ]:
        fpath = profile_path / fname
        if not fpath.exists():
            _save_yaml(fpath, {"role": role, "system_prompt": ""})

        current = _load_yaml(fpath)

        with st.expander(f"**{label}**", expanded=False):
            prompt_val = st.text_area(
                label,
                value=current.get("system_prompt", ""),
                height=500,
                key=f"_ce_prompt_{fname}",
                label_visibility="collapsed",
            )
            if st.button(f"💾 Save {label}", key=f"_ce_prompt_save_{fname}", type="primary"):
                _save_yaml(fpath, {"role": role, "system_prompt": prompt_val})
                st.success(f"{label} saved.")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    st.markdown(
        "<h2 style='margin-bottom:0.1rem'>🛠️ Profile Manager</h2>"
        "<p style='color:#6b7280;margin-top:0;margin-bottom:1.25rem;font-size:0.9rem'>"
        "Configure services, specialist agents, and system prompts for each investigation profile."
        "</p>",
        unsafe_allow_html=True,
    )

    profiles = list_profiles(PROFILES_DIR)

    # ── Handle empty profiles dir ─────────────────────────────────────────────
    if not profiles:
        st.warning("No profiles found in `profiles/`.")
        with st.container(border=True):
            st.markdown("**Create your first profile:**")
            np_name = st.text_input("Profile Name", key="_ce_first_profile")
            if st.button("Create Profile", type="primary") and np_name.strip():
                _create_new_profile(PROFILES_DIR / np_name.strip(), np_name.strip())
                st.rerun()
        return

    profile_names = list(profiles.keys())

    # ── Profile selector row ──────────────────────────────────────────────────
    if "_ce_active_profile" not in st.session_state:
        st.session_state["_ce_active_profile"] = profile_names[0]

    prev = st.session_state["_ce_active_profile"]
    if prev not in profile_names:
        prev = profile_names[0]
        st.session_state["_ce_active_profile"] = prev

    # ── Profile selector + action bar ─────────────────────────────────────────
    sel_col, act_col = st.columns([5, 4])

    with sel_col:
        selected = st.selectbox(
            "Active Profile",
            profile_names,
            index=profile_names.index(prev),
            key="_ce_profile_select",
        )
        if selected != prev:
            _clear_editor_state()
            st.session_state["_ce_active_profile"] = selected
            st.rerun()

    profile_path = profiles[selected]

    with act_col:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)  # align with selectbox
        b1, b2, b3 = st.columns(3)

        with b1:
            st.download_button(
                "⬇ Export ZIP",
                data=_zip_profile(profile_path),
                file_name=f"{selected}.zip",
                mime="application/zip",
                use_container_width=True,
                help="Download entire profile as a ZIP archive",
            )

        with b2:
            with st.popover("⬆ Import ZIP", use_container_width=True):
                st.caption("Upload a profile ZIP to add or replace a profile.")
                uploaded = st.file_uploader("Select ZIP", type=["zip"], key="_ce_zip_upload")
                if uploaded:
                    if st.button("Apply", key="_ce_apply_zip", type="primary"):
                        with zipfile.ZipFile(io.BytesIO(uploaded.read())) as zf:
                            zf.extractall(PROFILES_DIR)
                        st.success("Profile imported.")
                        st.rerun()

        with b3:
            if st.button("＋ New Profile", key="_ce_new_profile_btn", use_container_width=True):
                st.session_state["_ce_creating_profile"] = True

    # ── New profile form ───────────────────────────────────────────────────────
    if st.session_state.get("_ce_creating_profile"):
        with st.container(border=True):
            st.markdown("**Create New Profile**")
            np_name = st.text_input(
                "Profile Name", key="_ce_np_name",
                placeholder="e.g. my_product",
                help="Used as the directory name under profiles/",
            )
            nc1, nc2, _ = st.columns([2, 1, 4])
            with nc1:
                if st.button("Create Profile", type="primary", key="_ce_np_create") and np_name.strip():
                    _create_new_profile(PROFILES_DIR / np_name.strip(), np_name.strip())
                    st.session_state["_ce_creating_profile"] = False
                    st.session_state["_ce_active_profile"] = np_name.strip()
                    _clear_editor_state()
                    st.rerun()
            with nc2:
                if st.button("Cancel", key="_ce_np_cancel"):
                    st.session_state["_ce_creating_profile"] = False
                    st.rerun()

    st.divider()

    # ── Load config ───────────────────────────────────────────────────────────
    try:
        config = load_profile(profile_path)
    except Exception as e:
        st.error(f"Failed to load profile: {e}")
        return

    # ── Tabs ──────────────────────────────────────────────────────────────────
    t_profile, t_services, t_agents, t_prompts = st.tabs(
        ["⚙️ Profile", "🔧 Services", "🤖 Agents", "💬 Prompts"]
    )

    with t_profile:
        _tab_profile(profile_path, config)

    with t_services:
        _tab_services(profile_path)

    with t_agents:
        _tab_agents(profile_path)

    with t_prompts:
        _tab_prompts(profile_path)


if __name__ == "__main__":
    main()
