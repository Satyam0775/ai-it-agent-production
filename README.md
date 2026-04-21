# AI IT Support Agent

An AI-powered IT automation agent that accepts natural language commands and executes them on a web-based admin panel through real browser automation. Built in two phases — first as a working prototype, then hardened into a production-style agent with guardrails, approval workflows, smart retry logic, and multi-step execution support.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Evolution of the System](#evolution-of-the-system)
- [Setup](#setup)
- [Usage](#usage)
- [Demo Commands](#demo-commands)
- [Design Decisions](#design-decisions)
- [Future Improvements](#future-improvements)

---

## Overview

The agent takes a plain English request from the command line, parses the intent using an LLM (Google Gemini 2.5 Flash with a rule-based fallback), validates the request through a guardrails layer, requests human approval where required, and executes the action either through Playwright browser automation or a direct data-layer operation — depending on the intent.

All actions are logged to `logs.json` with timestamp, parsed intent, execution status, and error detail.

---

## Architecture

```
User Input (CLI)
      |
      v
LLM Intent Parser  (Gemini 2.5 Flash + rule-based fallback)
      |
      v
Guardrails Layer   (input validation: email format, domain, intent support)
      |
      v
Approval Layer     (human confirmation for sensitive actions)
      |
      v
Execution Layer
      |-- Browser Automation  (create_user, reset_password via Playwright)
      |-- Data Layer          (check_user via direct JSON read)
      |-- Multi-Step Engine   (conditional create + reset workflow)
      |
      v
Logging            (logs.json: timestamp, intent, status, error)
```

---

## Project Structure

```
ai-it-agent/
├── agent/
│   ├── agent.py          # Main orchestrator — runs the full pipeline
│   ├── llm.py            # Intent parsing (Gemini API + rule-based fallback)
│   ├── browser.py        # Playwright browser automation (create/reset)
│   ├── guardrails.py     # Input validation and approval prompts
│   ├── utils.py          # Logging, safe execution, user existence check
│   └── config.py         # Central configuration (URLs, domains, intents, retries)
├── backend/
│   ├── main.py           # FastAPI mock admin panel
│   └── templates/        # Jinja2 HTML templates (login, users, create user)
└── data/
    ├── users.json        # Persistent user store
    └── logs.json         # Action audit log
```

---

## Tech Stack

| Component          | Technology                    |
|--------------------|-------------------------------|
| Language           | Python 3.10                   |
| Backend / Admin UI | FastAPI + Jinja2              |
| Browser Automation | Playwright (Chromium)         |
| LLM                | Google Gemini 2.5 Flash       |
| LLM Fallback       | Rule-based regex parser       |
| Data Storage       | JSON files                    |
| Config Management  | python-dotenv                 |

---

## Features

**Natural Language Understanding**
Requests are parsed by Gemini 2.5 Flash. If no API key is present, a deterministic rule-based regex parser handles intent extraction. Both paths return the same structured output: `intent`, `email`, and `name`.

**Real Browser Automation**
All UI actions are performed through Playwright using semantic selectors only (`get_by_role`, `get_by_label`, `get_by_text`). No CSS selectors or XPaths. The browser operates visibly by default for observability.

**Guardrails**
Every request is validated before execution:
- Email must be present and well-formed
- Email domain must match the configured allowed domain (`@company.com`)
- Intent must be a recognised, supported operation

**Approval System**
Sensitive actions (`reset_password`) require explicit CLI confirmation before the browser is launched. The approval check is intent-driven and configured centrally via `APPROVAL_REQUIRED` in `config.py`.

**Smart Retry Logic**
`safe_execute` retries browser actions on transient failures with exponential back-off (2s, 4s). It detects deterministic errors — such as "user already exists" or "user not found" — and aborts immediately without retrying, since retrying would never produce a different outcome.

**check_user (Data-Layer Operation)**
User existence is verified by reading `users.json` directly, with no browser involved. This is intentionally a lightweight, non-destructive operation that bypasses the browser automation path entirely.

**Multi-Step Workflow**
A single natural language instruction can trigger a conditional two-step operation:
1. Check whether the user exists.
2. If absent, create the user first.
3. Reset the password regardless of whether the user was just created or already existed.

**Logging and Observability**
Every agent run appends a structured entry to `logs.json`:

```json
{
  "timestamp": "2026-04-15T09:41:00Z",
  "input": "reset password for alice@company.com",
  "parsed": { "intent": "reset_password", "email": "alice@company.com", "name": "Alice" },
  "status": "success",
  "error": ""
}
```

Possible status values: `success`, `failure`, `rejected`, `denied`.

---

## Evolution of the System

The project was built in two distinct phases. The table below documents what changed and why.

| Dimension            | Phase 1 (Initial Build)                          | Phase 2 (Production Hardening)                                  |
|----------------------|--------------------------------------------------|-----------------------------------------------------------------|
| Execution model      | Single-step, direct execution                    | Structured pipeline with discrete, testable stages             |
| Safety               | None                                             | Guardrails layer validates every request before execution       |
| Sensitive actions    | Executed immediately                             | Approval gate prompts for human confirmation                    |
| Error handling       | Uniform retry on all failures                    | Deterministic errors short-circuit; transient errors retry      |
| Supported intents    | `create_user`, `reset_password`                  | Added `check_user` (data layer) and `multi_step` (conditional)  |
| Execution layer      | Browser only                                     | Hybrid: browser for UI actions, direct data access for reads    |
| Observability        | Print statements                                 | Structured JSON audit log with timestamp, status, and error     |
| Workflow complexity  | One intent maps to one action                    | Multi-step workflows with conditional branching                 |

---

## Setup

### Prerequisites

- Python 3.10+
- A Google Gemini API key (optional — system falls back to rule-based parsing without one)

### Install dependencies

```bash
pip install fastapi uvicorn jinja2 playwright python-dotenv google-generativeai
playwright install chromium
```

### Configure environment

Create a `.env` file in the `agent/` directory:

```env
GEMINI_API_KEY=your_key_here
```

If `GEMINI_API_KEY` is not set or left as the placeholder value, the agent will automatically use the rule-based parser.

### Start the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The admin panel will be available at `http://localhost:8000`.

### Seed initial data (optional)

Create `data/users.json` with an empty array to initialise the user store:

```bash
mkdir -p data
echo "[]" > data/users.json
```

---

## Usage

Run the agent from the `agent/` directory:

```bash
python agent.py "<natural language request>"
```

The agent will print each pipeline stage — parse, validate, approve, execute, log — with status indicators at every step.

---

## Demo Commands

**Create a user**
```bash
python agent.py "create user john@company.com"
```

**Reset a password**
```bash
python agent.py "reset password for alice@company.com"
```
Requires CLI approval before execution.

**Check if a user exists**
```bash
python agent.py "check user john@company.com"
```
Reads `users.json` directly. No browser launched.

**Multi-step workflow**
```bash
python agent.py "if user john@company.com does not exist create it and then reset password"
```
Conditionally creates the user if absent, then resets the password.

**Rejected request — wrong domain**
```bash
python agent.py "create user john@gmail.com"
```
Rejected at the guardrails layer. No browser launched. Logged with status `rejected`.

**Rejected request — unrecognised intent**
```bash
python agent.py "delete user john@company.com"
```
Fails at intent parsing. Logged with status `failure`.

---

## Design Decisions

**Semantic selectors only in Playwright**
`get_by_role`, `get_by_label`, and `get_by_text` were used exclusively. This makes automation resilient to layout changes and mirrors how a human navigates the UI, which is more representative of a real agent behaviour.

**LLM with deterministic fallback**
Relying solely on an external API introduces a single point of failure. The rule-based parser ensures the agent continues to function correctly during API outages, rate limiting, or in environments where no API key is available — such as CI or local demos.

**Centralised configuration**
`config.py` is the single source of truth for allowed domains, supported intents, approval requirements, retry counts, and browser settings. No magic strings are scattered across modules.

**Deterministic error detection in retry logic**
Errors like "user already exists" are not transient — retrying them wastes time and adds browser overhead with a guaranteed identical outcome. The `_NO_RETRY_PHRASES` tuple in `utils.py` makes this policy explicit, extensible, and easy to audit.

**check_user as a data-layer operation**
Reading `users.json` directly for existence checks avoids unnecessary browser sessions for a read-only operation. This separation between read operations (data layer) and write operations (browser layer) is an intentional architectural boundary.

**Approval as a configurable, intent-driven gate**
The `APPROVAL_REQUIRED` list in `config.py` controls which intents require human confirmation. Adding a new sensitive intent requires a one-line config change, not a code change.

---

## Future Improvements

- **Persistent storage** — Replace `users.json` with a proper database (PostgreSQL or SQLite) for concurrent access safety and query support.
- **Additional intents** — `delete_user`, `update_email`, `list_users`, `disable_account`.
- **Non-interactive approval** — Support approval via Slack message, email confirmation, or a signed webhook for headless / automated environments.
- **LLM provider abstraction** — Introduce a provider interface so Gemini, OpenAI, or a local model can be swapped without touching parsing logic.
- **Structured test suite** — Unit tests for guardrails and the rule-based parser; integration tests with a headless browser against the FastAPI backend.
- **Log viewer** — A lightweight FastAPI endpoint or CLI command to query and filter `logs.json` by status, intent, or date range.
- **Rate limiting and deduplication** — Prevent the same action from being submitted twice within a short window, guarding against accidental double-execution.