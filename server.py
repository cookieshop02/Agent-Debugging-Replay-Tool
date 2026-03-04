"""
server.py  — PHASE 3 VERSION
──────────────────────────────
New endpoints added:
  POST /signup   — create account with name, email, password
  POST /login    — login with email, password → get api_key back

Everything else unchanged from Phase 2.

Run with:  uvicorn server:app --reload --port 8000
"""

from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from auth import hash_password, verify_password, generate_api_key
from server_db import (
    init_db, is_valid_key, email_exists,
    create_user, get_user_by_email, get_user_by_key,
    create_session, update_session, fetch_sessions,
    fetch_session, delete_session_db,
    create_step, fetch_steps
)

app = FastAPI(title="Agent Tracer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


# ─────────────────────────────────────────────
# AUTH GUARD — runs on every protected endpoint
# ─────────────────────────────────────────────

def get_api_key(x_api_key: str = Header(...)):
    if not is_valid_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# ─────────────────────────────────────────────
# REQUEST SCHEMAS
# ─────────────────────────────────────────────

class SignupBody(BaseModel):
    name: str
    email: str
    password: str

class LoginBody(BaseModel):
    email: str
    password: str

class SessionCreateBody(BaseModel):
    session_id: str
    name: str
    started_at: str

class SessionUpdateBody(BaseModel):
    status: str
    ended_at: str
    total_cost: float
    total_tokens: int

class StepBody(BaseModel):
    id: str
    session_id: str
    step_number: int
    step_type: str
    input_text: str
    output_text: str
    duration_ms: float
    tokens_used: int
    cost_usd: float
    status: str
    error_msg: Optional[str] = None
    timestamp: str


# ─────────────────────────────────────────────
# SIGNUP  —  POST /signup
# ─────────────────────────────────────────────

@app.post("/signup")
def signup(body: SignupBody):
    """
    Anyone can call this to create an account.
    Checks:
      - email not already taken
      - password at least 6 characters
    Returns their new api_key on success.
    """

    # validation
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    if email_exists(body.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    # create the account
    api_key       = generate_api_key()
    password_hash = hash_password(body.password)

    create_user(
        api_key=api_key,
        name=body.name,
        email=body.email,
        password_hash=password_hash
    )

    return {
        "message": f"Account created! Welcome, {body.name}",
        "api_key": api_key,    # they save this for their agent
        "name":    body.name,
        "email":   body.email
    }


# ─────────────────────────────────────────────
# LOGIN  —  POST /login
# ─────────────────────────────────────────────

@app.post("/login")
def login(body: LoginBody):
    """
    Login with email + password.
    Returns api_key and user info on success.
    """

    # find the user
    user = get_user_by_email(body.email)
    if not user:
        raise HTTPException(status_code=401, detail="Email not found")

    # check password
    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Wrong password")

    return {
        "message": f"Welcome back, {user['name']}!",
        "api_key": user["api_key"],
        "name":    user["name"],
        "email":   user["email"]
    }


# ─────────────────────────────────────────────
# PROFILE  —  GET /me
# ─────────────────────────────────────────────

@app.get("/me")
def get_profile(api_key: str = Depends(get_api_key)):
    """Returns logged in user's profile."""
    user = get_user_by_key(api_key)
    return {
        "name":       user["name"],
        "email":      user["email"],
        "api_key":    user["api_key"],
        "created_at": user["created_at"]
    }


# ─────────────────────────────────────────────
# SESSIONS — unchanged from Phase 2
# ─────────────────────────────────────────────

@app.post("/sessions")
def create_session_route(body: SessionCreateBody, api_key: str = Depends(get_api_key)):
    create_session(api_key, body.session_id, body.name, body.started_at)
    return {"ok": True, "session_id": body.session_id}


@app.patch("/sessions/{session_id}")
def update_session_route(session_id: str, body: SessionUpdateBody, api_key: str = Depends(get_api_key)):
    update_session(session_id, body.status, body.ended_at, body.total_cost, body.total_tokens)
    return {"ok": True}


@app.get("/sessions")
def get_sessions_route(api_key: str = Depends(get_api_key)):
    return fetch_sessions(api_key)


@app.get("/sessions/{session_id}")
def get_session_route(session_id: str, api_key: str = Depends(get_api_key)):
    session = fetch_session(api_key, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.delete("/sessions/{session_id}")
def delete_session_route(session_id: str, api_key: str = Depends(get_api_key)):
    delete_session_db(api_key, session_id)
    return {"ok": True}


# ─────────────────────────────────────────────
# STEPS — unchanged from Phase 2
# ─────────────────────────────────────────────

@app.post("/steps")
def create_step_route(body: StepBody, api_key: str = Depends(get_api_key)):
    create_step(body.dict())
    return {"ok": True}


@app.get("/sessions/{session_id}/steps")
def get_steps_route(session_id: str, api_key: str = Depends(get_api_key)):
    session = fetch_session(api_key, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return fetch_steps(session_id)


# ─────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────

@app.get("/")
def health():
    return {"status": "Agent Tracer API is running ✅"}