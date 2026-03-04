"""
app.py  —  Agent Tracer Dashboard
Run with:  streamlit run app.py
"""

import streamlit as st
import sqlite3
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tracer"))
from tracer.queries import get_all_sessions, get_session, get_steps, delete_session


# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Agent Tracer",
    page_icon="🔍",
    layout="wide"
)

# ── CHECK LOGIN ───────────────────────────────
st.sidebar.title("🔍 Agent Tracer")

# if not logged in, send them to login page
if "api_key" not in st.session_state or not st.session_state.api_key:
    st.title("👋 Welcome to Agent Tracer")
    st.info("Please login or create an account first.")
    st.page_link("pages/1_login.py", label="Go to Login →", icon="🔐")
    st.stop()

# logged in — get their info
api_key   = st.session_state.api_key
user_name = st.session_state.get("user_name", "")

# show user info + logout in sidebar
st.sidebar.markdown(f"👤 **{user_name}**")
st.sidebar.caption(st.session_state.get("email", ""))
if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.rerun()
st.sidebar.markdown("---")

# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────

st.markdown("""
<style>
    .step-card {
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 5px solid #ccc;
    }
    .step-llm    { border-left-color: #4f8ef7; background: #f0f5ff; }
    .step-tool   { border-left-color: #22c55e; background: #f0fdf4; }
    .step-error  { border-left-color: #ef4444; background: #fff1f1; }

    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-llm   { background:#dbeafe; color:#1d4ed8; }
    .badge-tool  { background:#dcfce7; color:#15803d; }
    .badge-error { background:#fee2e2; color:#b91c1c; }
    .badge-success { background:#dcfce7; color:#15803d; }
    .badge-running { background:#fef9c3; color:#854d0e; }

    .metric-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .metric-value { font-size: 28px; font-weight: 700; color: #1e293b; }
    .metric-label { font-size: 13px; color: #64748b; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def status_badge(status):
    if status == "success":
        return '<span class="badge badge-success">✅ success</span>'
    elif status == "error":
        return '<span class="badge badge-error">❌ error</span>'
    else:
        return '<span class="badge badge-running">🔄 running</span>'

def type_badge(step_type):
    if step_type == "llm_call":
        return '<span class="badge badge-llm">🤖 LLM</span>'
    elif step_type == "tool_call":
        return '<span class="badge badge-tool">🔧 Tool</span>'
    else:
        return '<span class="badge badge-error">💥 Error</span>'

def step_css_class(step_type):
    mapping = {"llm_call": "step-llm", "tool_call": "step-tool", "error": "step-error"}
    return mapping.get(step_type, "step-card")

def format_cost(cost):
    if cost == 0:
        return "$0.0000"
    return f"${cost:.4f}"

def build_graphviz(steps):
    """Build a Graphviz DOT string from steps list."""
    lines = ["digraph agent {", '  rankdir=LR;', '  node [shape=box, style=filled, fontsize=12];']

    for i, step in enumerate(steps):
        node_id = f"step{i}"
        label = f"Step {step['step_number']}\\n"

        if step["step_type"] == "llm_call":
            label += "🤖 LLM Call"
            color = "#93c5fd"
        elif step["step_type"] == "tool_call":
            # extract tool name from "toolname(args)"
            raw = step["input_text"]
            tool_name = raw.split("(")[0] if "(" in raw else raw[:20]
            label += f"🔧 {tool_name}"
            color = "#86efac"
        else:
            label += "💥 Error"
            color = "#fca5a5"

        if step["status"] == "error":
            color = "#fca5a5"

        lines.append(f'  {node_id} [label="{label}", fillcolor="{color}"];')

    # draw arrows between steps
    for i in range(len(steps) - 1):
        lines.append(f"  step{i} -> step{i+1};")

    lines.append("}")
    return "\n".join(lines)


# ─────────────────────────────────────────────
# SIDEBAR — session list
# ─────────────────────────────────────────────

st.sidebar.markdown("---")

sessions = get_all_sessions(api_key)

if not sessions:
    st.sidebar.warning("No sessions yet. Run your agent first.")
    st.title("👋 Welcome to Agent Tracer")
    st.info("No agent runs found for this API key.\n\nRun your agent with the tracer to start recording.")
    st.stop()

# Session selector
st.sidebar.subheader(f"📋 Sessions ({len(sessions)})")

session_labels = []
for s in sessions:
    icon = "✅" if s["status"] == "success" else ("❌" if s["status"] == "error" else "🔄")
    session_labels.append(f"{icon} {s['name']} [{s['id']}]")

selected_idx = st.sidebar.radio(
    "Select a run to inspect:",
    range(len(sessions)),
    format_func=lambda i: session_labels[i]
)

selected_session = sessions[selected_idx]

# Delete button
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Delete this session"):
    delete_session(api_key, selected_session["id"])
    st.rerun()

if st.sidebar.button("🔄 Refresh"):
    st.rerun()


# ─────────────────────────────────────────────
# MAIN AREA
# ─────────────────────────────────────────────

session = get_session(api_key, selected_session["id"])
steps   = get_steps(api_key, selected_session["id"])

# ── Header ────────────────────────────────────
col_title, col_badge = st.columns([4, 1])
with col_title:
    st.title(f"🔍 {session['name']}")
    st.caption(f"Session ID: `{session['id']}` · Started: {session['started_at'][:19].replace('T',' ')}")
with col_badge:
    st.markdown(f"<br>{status_badge(session['status'])}", unsafe_allow_html=True)

st.markdown("---")

# ── Summary Metrics ───────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)

llm_steps   = [s for s in steps if s["step_type"] == "llm_call"]
tool_steps  = [s for s in steps if s["step_type"] == "tool_call"]
error_steps = [s for s in steps if s["step_type"] == "error" or s["status"] == "error"]
total_tokens = sum(s["tokens_used"] for s in steps)
total_cost   = sum(s["cost_usd"] for s in steps)

with m1:
    st.markdown(f'<div class="metric-box"><div class="metric-value">{len(steps)}</div><div class="metric-label">Total Steps</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-box"><div class="metric-value">{len(llm_steps)}</div><div class="metric-label">LLM Calls</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-box"><div class="metric-value">{len(tool_steps)}</div><div class="metric-label">Tool Calls</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-box"><div class="metric-value" style="color:{"#ef4444" if error_steps else "#22c55e"}">{len(error_steps)}</div><div class="metric-label">Errors</div></div>', unsafe_allow_html=True)
with m5:
    st.markdown(f'<div class="metric-box"><div class="metric-value">{format_cost(total_cost)}</div><div class="metric-label">Total Cost</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 Step Timeline", "🗺️ Flow Graph", "📊 Analysis"])


# ── TAB 1: Step Timeline ──────────────────────
with tab1:
    if not steps:
        st.info("No steps recorded for this session.")
    else:
        st.subheader(f"All Steps ({len(steps)})")

        for step in steps:
            css = step_css_class(step["step_type"] if step["status"] != "error" else "error")
            badge = type_badge(step["step_type"])

            with st.expander(
                f"Step {step['step_number']} — {step['step_type'].replace('_',' ').title()}  |  "
                f"Tokens: {step['tokens_used']}  |  "
                f"Cost: {format_cost(step['cost_usd'])}",
                expanded=(step["status"] == "error")
            ):
                col_l, col_r = st.columns([1, 1])

                with col_l:
                    st.markdown(f"**Type:** {badge}", unsafe_allow_html=True)
                    st.markdown(f"**Status:** {status_badge(step['status'])}", unsafe_allow_html=True)
                    st.markdown(f"**Time:** {step['timestamp'][11:19]}")
                    if step["duration_ms"]:
                        st.markdown(f"**Duration:** {step['duration_ms']:.0f}ms")

                with col_r:
                    st.markdown(f"**Tokens:** {step['tokens_used']}")
                    st.markdown(f"**Cost:** {format_cost(step['cost_usd'])}")

                st.markdown("---")

                in_col, out_col = st.columns(2)
                with in_col:
                    st.markdown("**📥 Input**")
                    st.code(step["input_text"] or "—", language=None)
                with out_col:
                    st.markdown("**📤 Output**")
                    st.code(step["output_text"] or "—", language=None)

                if step["error_msg"]:
                    st.error(f"💥 Error: {step['error_msg']}")


# ── TAB 2: Flow Graph ─────────────────────────
with tab2:
    if not steps:
        st.info("No steps to visualize.")
    else:
        st.subheader("Agent Flow Diagram")
        st.caption("Each box = one step. Blue = LLM call, Green = Tool call, Red = Error")

        dot_code = build_graphviz(steps)
        st.graphviz_chart(dot_code, width="stretch")

        st.markdown("---")
        st.markdown("**Legend:**")
        cols = st.columns(3)
        cols[0].markdown("🟦 **Blue** = LLM Call")
        cols[1].markdown("🟩 **Green** = Tool Call")
        cols[2].markdown("🟥 **Red** = Error")


# ── TAB 3: Analysis ───────────────────────────
with tab3:
    st.subheader("Run Analysis")

    # Cost breakdown
    if llm_steps:
        st.markdown("#### 💰 Cost Breakdown")
        llm_cost  = sum(s["cost_usd"] for s in llm_steps)
        tool_cost = sum(s["cost_usd"] for s in tool_steps)
        col1, col2 = st.columns(2)
        col1.metric("LLM Cost", format_cost(llm_cost))
        col2.metric("Tool Cost", format_cost(tool_cost))

    # Token usage per step
    st.markdown("#### 🔢 Tokens Per LLM Call")
    if llm_steps:
        import pandas as pd
        token_data = pd.DataFrame([
            {"Step": f"Step {s['step_number']}", "Tokens": s["tokens_used"]}
            for s in llm_steps
        ])
        st.bar_chart(token_data.set_index("Step"))
    else:
        st.info("No LLM calls recorded.")

    # Error summary
    st.markdown("#### ⚠️ Issues Found")
    if error_steps:
        for s in error_steps:
            st.error(f"**Step {s['step_number']}**: {s['error_msg'] or 'Unknown error'}")
    else:
        st.success("No errors in this run! 🎉")

    # Efficiency tip
    st.markdown("#### 💡 Efficiency Tips")
    if len(llm_steps) > 4:
        st.warning(f"⚠️ This agent made **{len(llm_steps)} LLM calls**. Consider whether some can be replaced with deterministic logic to reduce cost.")
    if total_cost > 0.01:
        st.warning(f"⚠️ This run cost **{format_cost(total_cost)}**. Review if all LLM calls were necessary.")
    if not error_steps and len(llm_steps) <= 4:
        st.success("✅ This run looks efficient — no wasted calls detected.")