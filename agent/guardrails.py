"""
guardrails.py — Input validation and approval rules for the AI IT Agent.
"""

from config import ALLOWED_EMAIL_DOMAIN, SUPPORTED_INTENTS, APPROVAL_REQUIRED


def validate_intent(parsed: dict) -> tuple[bool, str]:
    """
    Validate a parsed intent dict before execution.

    Returns:
        (True, "")           — valid, proceed
        (False, reason_str)  — invalid, reason explains why
    """
    intent    = parsed.get("intent", "")
    email     = parsed.get("email", "") or ""

    # ── Rule 1: email must be present ─────────────────────────────────────
    if not email or not email.strip():
        return False, "No email address found in the request."

    # ── Rule 2: email must match allowed domain ────────────────────────────
    if not email.lower().endswith(ALLOWED_EMAIL_DOMAIN):
        return False, (
            f"Email '{email}' is not allowed. "
            f"Only {ALLOWED_EMAIL_DOMAIN} addresses are supported."
        )

    # ── Rule 3: basic email format check ──────────────────────────────────
    local = email.split("@")[0]
    if not local or " " in email:
        return False, f"Email '{email}' appears to be malformed."

    # ── Rule 4: intent must be supported ──────────────────────────────────
    if intent not in SUPPORTED_INTENTS:
        return False, (
            f"Unknown intent '{intent}'. "
            f"Supported intents: {', '.join(SUPPORTED_INTENTS)}."
        )

    return True, ""


def requires_approval(intent: str) -> bool:
    """
    Return True if this intent requires explicit human approval before execution.
    Currently: reset_password requires approval.
    """
    return intent in APPROVAL_REQUIRED


def prompt_approval(intent: str, email: str) -> bool:
    """
    Prompt the user for CLI approval.
    Returns True if approved, False if denied.
    """
    print(f"\n[Guardrails] ⚠  Action '{intent}' on '{email}' requires approval.")
    answer = input("[Guardrails] Proceed? (yes/no): ").strip().lower()
    approved = answer in ("yes", "y")
    if approved:
        print("[Guardrails] ✔  Approved.")
    else:
        print("[Guardrails] ✘  Denied by user.")
    return approved
