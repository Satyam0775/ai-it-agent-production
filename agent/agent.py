"""
agent.py — Orchestrator for the AI IT Support Agent.

Pipeline:
  1. Input (CLI)
  2. Parse intent (LLM)
  3. Validate (guardrails)
  4. Approval check (guardrails)
  5. Execute (browser automation)
  6. Log result (utils)

Usage:
  python agent.py "create user john@company.com"
  python agent.py "reset password for alice@company.com"
  python agent.py "check user alice@company.com"
  python agent.py "if user john@company.com does not exist create it and then reset password"
"""

import sys
import os
from pathlib import Path

# Ensure all sibling modules are importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv

from llm        import parse_intent
from guardrails import validate_intent, requires_approval, prompt_approval
from browser    import create_user, reset_password
from utils      import safe_execute, log_action, check_user_exists

load_dotenv()

DIVIDER = "=" * 58


def run_agent(user_input: str) -> None:
    print(DIVIDER)
    print(f"[Agent] Request: {user_input}")
    print(DIVIDER)

    parsed = {}   # keep in scope for logging even if we exit early

    # ── Step 1: Parse ──────────────────────────────────────────────────────
    print("\n[Step 1/5] Parsing intent...")
    try:
        parsed = parse_intent(user_input)
    except Exception as exc:
        msg = f"LLM parse failed: {exc}"
        print(f"[Agent] ERROR — {msg}")
        log_action(user_input, parsed, "failure", error=msg)
        return

    intent = parsed.get("intent", "unknown")
    email  = parsed.get("email") or ""
    name   = parsed.get("name")  or (email.split("@")[0].title() if email else "Unknown")

    print(f"  Intent : {intent}")
    print(f"  Email  : {email}")
    print(f"  Name   : {name}")

    # ── Unknown intent guard ───────────────────────────────────────────────
    if intent == "unknown":
        msg = "Could not determine a supported intent from the request."
        print(f"[Agent] ERROR — {msg}")
        log_action(user_input, parsed, "failure", error=msg)
        return

    # ── Step 2: Validate ───────────────────────────────────────────────────
    print("\n[Step 2/5] Validating input...")
    valid, reason = validate_intent(parsed)
    if not valid:
        print(f"[Guardrails] ✘  Rejected — {reason}")
        log_action(user_input, parsed, "rejected", error=reason)
        return
    print("[Guardrails] ✔  Validation passed.")

    # ── Step 3: Approval ───────────────────────────────────────────────────
    print("\n[Step 3/5] Checking approval requirements...")
    if requires_approval(intent):
        approved = prompt_approval(intent, email)
        if not approved:
            log_action(user_input, parsed, "denied")
            return
    else:
        print(f"[Guardrails] No approval required for '{intent}'.")

    # ── Step 4: Execute ────────────────────────────────────────────────────
    print("\n[Step 4/5] Executing via browser automation...")

    if intent == "create_user":
        success = safe_execute(create_user, email, name)
    elif intent == "reset_password":
        success = safe_execute(reset_password, email)
    elif intent == "check_user":
        exists = check_user_exists(email)
        if exists:
            print(f"[Agent] ✔  User '{email}' EXISTS in the system.")
        else:
            print(f"[Agent] ✘  User '{email}' does NOT exist in the system.")
        success = True
    elif intent == "multi_step":
        print("[Multi-Step] Checking user...")
        if not check_user_exists(email):
            print("[Multi-Step] User not found → creating...")
            success = safe_execute(create_user, email, name)
            if not success:
                log_action(user_input, parsed, "failure", error="create_user failed")
                return
        else:
            print("[Multi-Step] User already exists.")
        print("[Multi-Step] Resetting password...")
        success = safe_execute(reset_password, email)
    else:
        print(f"[Agent] No executor mapped for intent '{intent}'.")
        log_action(user_input, parsed, "failure", error=f"No executor for intent '{intent}'")
        return

    # ── Step 5: Log ────────────────────────────────────────────────────────
    print("\n[Step 5/5] Logging result...")
    status = "success" if success else "failure"
    log_action(user_input, parsed, status)

    print(f"\n{DIVIDER}")
    print(f"[Agent] Done — Status: {status.upper()}")
    print(DIVIDER)


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent.py \"<natural language request>\"")
        print()
        print("Examples:")
        print('  python agent.py "create user <email>"')
        print('  python agent.py "reset password for <email>"')
        print('  python agent.py "check user <email>"')
        print('  python agent.py "if user <email> does not exist create it and then reset password"')
        sys.exit(1)
        
    run_agent(" ".join(sys.argv[1:]))