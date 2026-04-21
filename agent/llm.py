"""
llm.py — Natural-language intent parser.
Uses Gemini 2.5 Flash if GEMINI_API_KEY is set; falls back to rule-based parsing.
Always returns: { "intent": str, "email": str | None, "name": str | None }
"""

import os
import re
import json

from config import SUPPORTED_INTENTS


# ── Rule-based fallback ────────────────────────────────────────────────────

def _rule_based_parse(text: str) -> dict:
    """Regex-based parser. No API required."""
    lower = text.lower()

    if any(k in lower for k in ["create user", "add user", "new user", "register user"]):
        intent = "create_user"
    elif any(k in lower for k in ["reset password", "change password", "reset pass"]):
        intent = "reset_password"
    elif any(k in lower for k in ["check user", "does user exist", "find user"]):
        intent = "check_user"
    elif "if" in lower and "create" in lower and "reset" in lower:
        intent = "multi_step"
    else:
        intent = "unknown"

    email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
    email = email_match.group(0) if email_match else None

    name = None
    name_match = re.search(
        r"(?:named?|for|user)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", text
    )
    if name_match:
        name = name_match.group(1)
    elif email:
        local = email.split("@")[0]
        name = local.replace(".", " ").replace("_", " ").title()

    return {"intent": intent, "email": email, "name": name}


# ── Gemini parser ──────────────────────────────────────────────────────────

def _gemini_parse(text: str, api_key: str) -> dict:
    """Parse intent via Gemini 2.5 Flash."""
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""You are an IT support assistant. Parse the following request.

Request: "{text}"

Return ONLY a valid JSON object — no markdown, no explanation — with:
  "intent":  one of {SUPPORTED_INTENTS}
  "email":   the email address, or null
  "name":    the person's display name (derive from email local part if not stated), or null

Example:
{{"intent": "create_user", "email": "john@company.com", "name": "John"}}"""

        response = model.generate_content(prompt)
        raw = response.text.strip()
        raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        parsed = json.loads(raw)

        return {
            "intent": parsed.get("intent", "unknown"),
            "email":  parsed.get("email"),
            "name":   parsed.get("name"),
        }

    except Exception as exc:
        print(f"[LLM] Gemini failed ({exc}) — using rule-based fallback.")
        return _rule_based_parse(text)


# ── Public API ─────────────────────────────────────────────────────────────

def parse_intent(text: str) -> dict:
    """
    Parse a natural-language IT request into a structured dict.

    Returns:
        {
            "intent": "create_user" | "reset_password" | "check_user" | "unknown",
            "email":  str | None,
            "name":   str | None,
        }
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if api_key and api_key not in ("", "YOUR_GEMINI_API_KEY_HERE"):
        print("[LLM] Using Gemini 2.5 Flash...")
        result = _gemini_parse(text, api_key)
    else:
        print("[LLM] No API key — using rule-based parser.")
        result = _rule_based_parse(text)

    print(f"[LLM] Parsed: {result}")
    return result