"""
auth.py
────────
Handles password hashing and verification.
Used by server.py when users sign up or log in.

We use bcrypt — the industry standard for storing passwords safely.
NEVER store plain text passwords. bcrypt turns "mypassword123"
into something like "$2b$12$abc123..." which can't be reversed.
"""

import bcrypt
import uuid


def hash_password(plain_password: str) -> str:
    """
    Turn a plain password into a safe hash to store in the database.
    bcrypt automatically adds a random 'salt' so two identical
    passwords produce different hashes — extra secure.
    """
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt(rounds=10))
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain password matches the stored hash.
    Returns True if correct, False if wrong.
    Used during login.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def generate_api_key() -> str:
    """Generate a unique API key like: at_sk_a1b2c3d4e5f6g7h8"""
    return f"at_sk_{uuid.uuid4().hex[:16]}"