# 🔍 Agent Debugging Replay Tool

A full stack observability tool for AI agents. Record every LLM call, tool call, and error your agent makes — then replay, inspect, and debug it visually on a live dashboard.

> Built with FastAPI · Streamlit · Groq · SQLite · bcrypt

🌐 **Live Demo:** ["https://agent-debugging-replay-tool.streamlit.app/"]

---

## 🎯 The Problem This Solves

When an AI agent breaks, your terminal shows one line:

```
Error: Tool not found
```

That tells you **nothing**. You don't know:
- Which step caused it
- What prompt the LLM received at that point
- How much money was wasted before it failed
- Whether this is the same bug from last week

**Agent Debugging Replay Tool fixes this.** It records every single step your agent takes and lets you inspect it like a flight recorder.

---

## ✨ Features

- 🔐 **Auth system** — signup, login, unique API key per user
- 🕵️ **Step recorder** — captures every LLM call, tool call, and error
- 📋 **Step timeline** — expand any step to see full input/output
- 🗺️ **Flow graph** — visual diagram of your agent's path
- 📊 **Cost analysis** — token usage chart + efficiency tips
- 👥 **Multi-user** — every user sees only their own agent runs
- ☁️ **Fully hosted** — server on Railway, dashboard on Streamlit Cloud

---



## 🚀 Quick Start (Local)

### 1. Clone the repo
```bash
git clone https://github.com/cookieshop02/Agent-Debugging-Replay-Tool.git
cd Agent-Debugging-Replay-Tool
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create your `.env` file
```bash
# create a .env file in the project root
GROQ_API_KEY=your_groq_key_here
TRACKER_API_KEY=your api key provided to you after you create account on platform (you can directly add into your code or write it here)
```
Get a free Groq API key at [console.groq.com](https://console.groq.com)

### 4. Start the server (Terminal 1)
```bash
uvicorn server:app --reload --port 8000
```

### 5. Start the dashboard (Terminal 2)
```bash
streamlit run app.py
```

### 6. Open browser
Go to `http://localhost:8501` → Create an account → You're in.

---

## 🧩 Add the Tracer to Your Own Agent

### Install
```bash
pip install requests python-dotenv
```

### Use it
```python
from tracer.recorder import AgentTracer

# 1. create tracer with your API key (from dashboard after signup)
tracer = AgentTracer(api_key="at_sk_your_key_here", name="My Agent Run")
tracer.start()

# 2. record every LLM call
tracer.record_llm(
    prompt="What should I do first?",
    response="I should search the web.",
    tokens=85
)

# 3. record every tool call
tracer.record_tool(
    tool_name="web_search",
    input_data="latest AI news",
    output_data="Results: ...",
    duration_ms=320
)

# 4. record errors
try:
    result = some_tool()
except Exception as e:
    tracer.record_error("Calling some_tool", e)

# 5. finish
tracer.finish(status="success")  # or "error"
```

Then open the dashboard — your run appears instantly in the sidebar.

---

## 📁 Project Structure

```
Agent-Debugging-Replay-Tool/
│
├── server.py               ← FastAPI backend (deployed on Railway)
├── server_db.py            ← Server database logic (SQLite)
├── auth.py                 ← Password hashing (bcrypt)
│
├── app.py                  ← Streamlit dashboard
├── pages/
│   └── 1_login.py          ← Login / signup page
│
├── groq_agent.py           ← Example real agent using Groq
│
├── tracer/
│   ├── __init__.py
│   ├── recorder.py         ← AgentTracer class (the spy)
│   └── queries.py          ← Fetches data from server
│
├── .env.example            ← Environment variable template
├── .gitignore              ← Keeps secrets out of GitHub
└── requirements.txt
```

---

## 🔌 API Endpoints

See at:

Full interactive docs at: `https://your-railway-url.up.railway.app/docs`

---

## ☁️ Deployment

| Service | Platform | URL |
|---------|----------|-----|
| FastAPI Server | Railway | `https://agent-debugging-replay-tool-production.up.railway.app/` |
| Streamlit Dashboard | Streamlit Cloud | `https://agent-debugging-replay-tool.streamlit.app/` |

### Deploy your own

**Server (Railway):**
1. Push to GitHub
2. Connect repo on [railway.app](https://railway.app)
3. Add `GROQ_API_KEY` environment variable
4. Set start command: `uvicorn server:app --host 0.0.0.0 --port $PORT`

**Dashboard (Streamlit Cloud):**
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect GitHub repo
3. Set main file: `app.py`
4. Deploy

---

## 💡 Why This Is Better Than Just Reading Terminal Logs

| | Terminal Logs | This Tool |
|--|---------------|-----------|
| See full prompt history | ❌ | ✅ |
| Compare runs | ❌ | ✅ |
| Cost per step | ❌ | ✅ |
| Visual flow diagram | ❌ | ✅ |
| Shareable with teammates | ❌ | ✅ |
| Persistent history | ❌ | ✅ |
| Works across multiple agents | ❌ | ✅ |



---

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, SQLite
- **Frontend:** Streamlit, Graphviz
- **Auth:** bcrypt password hashing
- **LLM:** Groq (llama3-8b-8192)
- **Hosting:** Railway (API) + Streamlit Cloud (UI)

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

Made with 🔍 to make AI agent debugging less painful.