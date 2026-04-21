"""
utils.py — Logging and safe execution utilities for the AI IT Agent.
"""

import json
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from config import LOGS_FILE, DEFAULT_RETRIES, USERS_FILE


# ── Deterministic errors — never retry these ───────────────────────────────
_NO_RETRY_PHRASES = (
    "already exists",
    "not found",
)


# ── Logging ────────────────────────────────────────────────────────────────

def _load_logs() -> list:
    """Load existing logs from disk, or return empty list."""
    if LOGS_FILE.exists():
        try:
            with open(LOGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_logs(logs: list) -> None:
    """Persist logs list to disk."""
    LOGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOGS_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)


def log_action(user_input: str, parsed: dict, status: str, error: str = "") -> None:
    """
    Append one entry to logs.json.

    Entry shape:
    {
        "timestamp": "2026-04-15T09:41:00Z",
        "input":     "reset password for alice@company.com",
        "parsed":    { "intent": "reset_password", "email": "...", "name": "..." },
        "status":    "success" | "failure" | "rejected" | "denied",
        "error":     ""   // populated on failure
    }
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "input":     user_input,
        "parsed":    parsed,
        "status":    status,
        "error":     error,
    }

    logs = _load_logs()
    logs.append(entry)
    _save_logs(logs)

    # Console summary
    icon = "✔" if status == "success" else "✘"
    print(f"[Log] {icon}  Status={status}  |  {entry['timestamp']}")
    if error:
        print(f"[Log]    Error: {error}")


# ── Safe Execution ─────────────────────────────────────────────────────────

def safe_execute(fn, *args, retries: int = DEFAULT_RETRIES) -> bool:
    """
    Call fn(*args) with automatic retries on transient exceptions.

    Deterministic errors (e.g. "already exists", "not found") are NOT
    retried — they are permanent business-logic failures and retrying
    would never produce a different outcome.

    Returns:
        True   — fn completed without raising
        False  — permanent error detected (no retry) or all attempts failed
    """
    attempts = retries + 1

    for attempt in range(1, attempts + 1):
        try:
            print(f"[Execute] Attempt {attempt}/{attempts}...")
            fn(*args)
            print(f"[Execute] ✔  Completed on attempt {attempt}.")
            return True

        except Exception as exc:
            error_msg = str(exc)
            tb = traceback.format_exc()
            print(f"[Execute] ✘  Attempt {attempt} failed: {error_msg}")

            # ── Deterministic failure — abort immediately, no retry ────────
            if any(phrase in error_msg.lower() for phrase in _NO_RETRY_PHRASES):
                print(f"[Execute] Permanent error detected — skipping retries.")
                print(f"[Execute] Last traceback:\n{tb}")
                return False

            # ── Transient failure — retry with back-off ────────────────────
            if attempt < attempts:
                wait = attempt * 2  # 2s, 4s back-off
                print(f"[Execute]    Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"[Execute] All {attempts} attempts failed.")
                print(f"[Execute] Last traceback:\n{tb}")

    return False


# ── User Existence Check ───────────────────────────────────────────────────

def check_user_exists(email: str) -> bool:
    """
    Check whether a user with the given email exists in users.json.

    Returns:
        True  — user found
        False — user not found or data file missing
    """
    if not USERS_FILE.exists():
        print(f"[Utils] Users file not found at {USERS_FILE}.")
        return False

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[Utils] Failed to read users file: {exc}")
        return False

    for user in users:
        if user.get("email", "").lower() == email.lower():
            return True

    return False