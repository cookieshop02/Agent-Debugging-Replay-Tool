"""
tracer/queries.py  — PHASE 2 VERSION
──────────────────────────────────────
Now fetches data from your FastAPI server over HTTP
instead of reading from a local SQLite file.

What changed from Phase 1:
- Every function now calls requests.get() to the server
- Pass api_key so the server returns only YOUR sessions
- Everything else is identical (same function names, same return shapes)
"""

import requests

SERVER_URL = "http://localhost:8000"   # same as recorder.py


def _headers(api_key: str) -> dict:
    return {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }


def get_all_sessions(api_key: str) -> list:
    """Return all sessions for this api_key, newest first."""
    try:
        resp = requests.get(f"{SERVER_URL}/sessions", headers=_headers(api_key))
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[Queries] Could not fetch sessions: {e}")
        return []


def get_session(api_key: str, session_id: str) -> dict:
    """Return one session by id."""
    try:
        resp = requests.get(f"{SERVER_URL}/sessions/{session_id}", headers=_headers(api_key))
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[Queries] Could not fetch session: {e}")
        return {}


def get_steps(api_key: str, session_id: str) -> list:
    """Return all steps for a session, in order."""
    try:
        resp = requests.get(f"{SERVER_URL}/sessions/{session_id}/steps", headers=_headers(api_key))
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[Queries] Could not fetch steps: {e}")
        return []


def delete_session(api_key: str, session_id: str) -> bool:
    """Delete a session and all its steps."""
    try:
        resp = requests.delete(f"{SERVER_URL}/sessions/{session_id}", headers=_headers(api_key))
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[Queries] Could not delete session: {e}")
        return False
