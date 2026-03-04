"""
pages/1_login.py
─────────────────
Streamlit login and signup page.
This is the first thing any user sees when they open the app
and are not logged in yet.

Streamlit automatically picks up files in the pages/ folder
and shows them as separate pages.
"""

import streamlit as st
import requests

SERVER_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Agent Tracer — Login",
    page_icon="🔍",
    layout="centered"
)

# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────

st.markdown("""
<style>
    .main { max-width: 420px; margin: auto; }
    div[data-testid="stForm"] {
        background: #f8fafc;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }
    .api-key-box {
        background: #f0fdf4;
        border: 1px solid #22c55e;
        border-radius: 8px;
        padding: 14px;
        font-family: monospace;
        font-size: 13px;
        word-break: break-all;
        margin-top: 12px;
    }
    .hint {
        background: #fffbeb;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 13px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# IF ALREADY LOGGED IN
# ─────────────────────────────────────────────

if "api_key" in st.session_state and st.session_state.api_key:
    st.success(f"✅ You're logged in as **{st.session_state.get('user_name', '')}**")
    st.info("Go to the **Dashboard** page from the sidebar to see your agent runs.")

    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()
    st.stop()


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
st.title("🔍 Agent Tracer")
st.caption("Debug and inspect your AI agents in real time")
st.markdown("---")

# ─────────────────────────────────────────────
# TABS: LOGIN / SIGNUP
# ─────────────────────────────────────────────

tab_login, tab_signup = st.tabs(["🔐 Login", "✨ Create Account"])


# ── LOGIN TAB ────────────────────────────────
with tab_login:
    st.subheader("Welcome back")

    with st.form("login_form"):
        email    = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Login →", use_container_width=True)

    if submitted:
        if not email or not password:
            st.error("Please fill in both fields.")
        else:
            with st.spinner("Logging in..."):
                try:
                    resp = requests.post(f"{SERVER_URL}/login", json={
                        "email":    email,
                        "password": password
                    })

                    if resp.status_code == 200:
                        data = resp.json()

                        # save to session state — persists across pages
                        st.session_state.api_key   = data["api_key"]
                        st.session_state.user_name = data["name"]
                        st.session_state.email     = data["email"]

                        st.success(f"✅ Welcome back, {data['name']}!")
                        st.info("Go to the **Dashboard** page in the sidebar.")
                        st.rerun()

                    elif resp.status_code == 401:
                        st.error(f"❌ {resp.json()['detail']}")
                    else:
                        st.error("Something went wrong. Try again.")

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to server. Make sure it's running:\n```\nuvicorn server:app --reload --port 8000\n```")


# ── SIGNUP TAB ───────────────────────────────
with tab_signup:
    st.subheader("Create your free account")

    with st.form("signup_form"):
        name      = st.text_input("Your Name",  placeholder="John Doe")
        email_s   = st.text_input("Email",       placeholder="you@example.com")
        password_s = st.text_input("Password",   type="password", placeholder="min 6 characters")
        password_c = st.text_input("Confirm Password", type="password", placeholder="same as above")
        submitted_s = st.form_submit_button("Create Account →", use_container_width=True)

    if submitted_s:
        # front-end validation
        if not name or not email_s or not password_s or not password_c:
            st.error("Please fill in all fields.")
        elif len(password_s) < 6:
            st.error("Password must be at least 6 characters.")
        elif password_s != password_c:
            st.error("Passwords don't match.")
        else:
            with st.spinner("Creating your account..."):
                try:
                    resp = requests.post(f"{SERVER_URL}/signup", json={
                        "name":     name,
                        "email":    email_s,
                        "password": password_s
                    })

                    if resp.status_code == 200:
                        data = resp.json()

                        # save to session state
                        st.session_state.api_key   = data["api_key"]
                        st.session_state.user_name = data["name"]
                        st.session_state.email     = data["email"]

                        st.success(f"✅ Account created! Welcome, {data['name']}!")

                        # show the api key prominently
                        st.markdown("**Your API Key** — copy this into your agent:")
                        st.markdown(f'<div class="api-key-box">🔑 {data["api_key"]}</div>', unsafe_allow_html=True)
                        st.markdown('<div class="hint">⚠️ Save this key! You\'ll need it in your <code>groq_agent.py</code> file as <code>TRACER_API_KEY</code></div>', unsafe_allow_html=True)

                        st.info("Now go to the **Dashboard** page in the sidebar.")

                    elif resp.status_code == 400:
                        st.error(f"❌ {resp.json()['detail']}")
                    else:
                        st.error("Something went wrong. Try again.")

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to server. Make sure it's running:\n```\nuvicorn server:app --reload --port 8000\n```")