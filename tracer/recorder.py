"""
tracer/recorder.py  — PHASE 2 VERSION
───────────────────────────────────────
Now sends data to your FastAPI server over HTTP
instead of writing to a local SQLite file.

What changed from Phase 1:
- Added api_key parameter
- _save_step() now calls requests.post() instead of sqlite3
- start() and finish() also call the server
- Everything else is identical
"""

import time
import uuid
import requests
from datetime import datetime

# ── point this at your server ──────────────────
# local dev:   http://localhost:8000
# production:  https://your-app.railway.app
SERVER_URL = "https://agent-debugging-replay-tool-production.up.railway.app/"


class AgentTracer:
    """
    Exactly the same interface as Phase 1.
    Only difference: pass your api_key.

    Usage:
        tracer = AgentTracer(api_key="at_sk_abc123", name="My Agent Run")
        tracer.start()
        tracer.record_llm(prompt="...", response="...", tokens=50)
        tracer.record_tool(tool_name="search", input_data="query", output_data="result")
        tracer.finish()
    """

    def __init__(self, api_key: str, name: str = "Agent Run"):
        self.api_key      = api_key
        self.session_id   = str(uuid.uuid4())[:8]
        self.name         = name
        self.step_counter = 0
        self.total_cost   = 0.0
        self.total_tokens = 0

    # ── headers sent with every request ───────────
    @property
    def _headers(self):
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key    # server uses this to identify who is sending data
        }

    # ── START ─────────────────────────────────────
    def start(self):
        """Call this before your agent starts."""
        try:
            resp = requests.post(f"{SERVER_URL}/sessions", headers=self._headers, json={
                "session_id": self.session_id,
                "name":       self.name,
                "started_at": datetime.now().isoformat()
            })
            resp.raise_for_status()
            print(f"[Tracer] Session started: {self.session_id}")
        except Exception as e:
            print(f"[Tracer] WARNING: Could not reach server — {e}")
        return self

    # ── FINISH ────────────────────────────────────
    def finish(self, status: str = "success"):
        """Call this after your agent finishes."""
        try:
            resp = requests.patch(
                f"{SERVER_URL}/sessions/{self.session_id}",
                headers=self._headers,
                json={
                    "status":       status,
                    "ended_at":     datetime.now().isoformat(),
                    "total_cost":   self.total_cost,
                    "total_tokens": self.total_tokens
                }
            )
            resp.raise_for_status()
            print(f"[Tracer] Session finished: {self.session_id} | Cost: ${self.total_cost:.4f} | Tokens: {self.total_tokens}")
        except Exception as e:
            print(f"[Tracer] WARNING: Could not reach server — {e}")

    # ── INTERNAL: send one step to server ─────────
    def _save_step(self, step_type, input_text, output_text, duration_ms,
                   tokens=0, cost=0.0, status="success", error_msg=None):
        self.step_counter += 1
        self.total_cost   += cost
        self.total_tokens += tokens

        try:
            resp = requests.post(f"{SERVER_URL}/steps", headers=self._headers, json={
                "id":          str(uuid.uuid4())[:8],
                "session_id":  self.session_id,
                "step_number": self.step_counter,
                "step_type":   step_type,
                "input_text":  str(input_text),
                "output_text": str(output_text),
                "duration_ms": duration_ms,
                "tokens_used": tokens,
                "cost_usd":    cost,
                "status":      status,
                "error_msg":   error_msg,
                "timestamp":   datetime.now().isoformat()
            })
            resp.raise_for_status()
        except Exception as e:
            print(f"[Tracer] WARNING: Step not saved — {e}")

    # ── LLM CALL ──────────────────────────────────
    def record_llm(self, prompt: str, response: str, tokens: int = 0, model: str = "groq"):
        cost = (tokens / 1_000_000) * 3.0    # rough cost estimate
        self._save_step("llm_call", prompt, response, 0, tokens=tokens, cost=cost)
        print(f"  [Step {self.step_counter}] LLM call recorded | tokens: {tokens}")
        return response

    # ── TOOL CALL ─────────────────────────────────
    def record_tool(self, tool_name: str, input_data, output_data, duration_ms: float = 0):
        self._save_step("tool_call", f"{tool_name}({input_data})", str(output_data), duration_ms)
        print(f"  [Step {self.step_counter}] Tool call recorded: {tool_name}")
        return output_data

    # ── ERROR ─────────────────────────────────────
    def record_error(self, context: str, error: Exception):
        self._save_step("error", context, "", 0, status="error", error_msg=str(error))
        print(f"  [Step {self.step_counter}] ERROR recorded: {error}")

    # ── AUTO-WRAP DECORATORS (unchanged) ──────────
    def wrap_llm_call(self, fn):
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = fn(*args, **kwargs)
                ms = (time.time() - start) * 1000
                prompt = args[0] if args else str(kwargs)
                self._save_step("llm_call", prompt, str(result), ms)
                return result
            except Exception as e:
                self._save_step("llm_call", str(args), "", 0, status="error", error_msg=str(e))
                raise
        return wrapper

    def wrap_tool_call(self, tool_name: str):
        def decorator(fn):
            def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = fn(*args, **kwargs)
                    ms = (time.time() - start) * 1000
                    self._save_step("tool_call", f"{tool_name}({args})", str(result), ms)
                    return result
                except Exception as e:
                    self._save_step("tool_call", f"{tool_name}({args})", "", 0, status="error", error_msg=str(e))
                    raise
            return wrapper
        return decorator
