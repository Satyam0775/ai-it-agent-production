"""
config.py — Central configuration for the AI IT Agent.
"""

from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent
LOGS_FILE  = BASE_DIR / "data" / "logs.json"
USERS_FILE = BASE_DIR / "data" / "users.json"

# ── Backend ────────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"

# ── Allowed domains ────────────────────────────────────────────────────────
ALLOWED_EMAIL_DOMAIN = "@company.com"

# ── Supported intents ──────────────────────────────────────────────────────
SUPPORTED_INTENTS = ["create_user", "reset_password", "check_user", "multi_step"]

# ── Intents that require human approval ───────────────────────────────────
APPROVAL_REQUIRED = ["reset_password"]

# ── Playwright ─────────────────────────────────────────────────────────────
BROWSER_SLOW_MO  = 600   # ms between actions
BROWSER_HEADLESS = False # always visible for demo

# ── Retry ──────────────────────────────────────────────────────────────────
DEFAULT_RETRIES = 2