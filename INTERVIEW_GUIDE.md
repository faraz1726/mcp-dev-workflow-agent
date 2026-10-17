# Interview Guide

## 30-second pitch
"I built DevFlow, an MCP server in Python with FastMCP. You give it a feature request and it
produces structured requirements, Jira-style tickets, a backend plan and a release checklist.
Tools have typed Pydantic schemas, inputs are validated, and the full-workflow tool recovers
from a failing step instead of crashing. It has 17 tests. Real Jira/GitHub integration is my next step."

## 2-minute demo
1. `python -m pytest -q` shows 17 passed.
2. `python demo.py` shows the workflow output.
3. In Claude Desktop (or MCP Inspector): "Use DevFlow to run the full workflow for: add user login with password reset."
4. Show a bad input (`"hi"`) giving a clean error.
5. Open `data/tickets_*.json`.

## Be honest about
- The engine is **rule-based** (keyword matching), not an LLM. A client LLM calls the tools.
- Jira is **mocked** (JSON files). GitHub integration is on the roadmap, not built.

## Likely questions and answers
**What is MCP?** An open protocol that lets LLM apps discover and call tools/resources on a server in a standard way (like USB-C for AI tools).
**Why FastMCP?** Decorator-based; it generates the tool schema from Python type hints and docstrings.
**Why Pydantic schemas?** The client gets a predictable, validated structure, and bad output fails loudly.
**How do you handle failure?** Validation errors become `ToolError`s with clear messages; unexpected errors are logged and hidden from clients; `run_full_workflow` records each step's status and continues.
**Why not call an LLM inside?** Determinism, no cost or API key, easy testing. The calling model already provides the intelligence.
**How would you add real Jira?** A `jira_client.py` using the Jira REST API with an API token from env vars, behind the same ticket schema, with retries and timeouts.
**How would you test it?** Unit tests on planners, end-to-end tests with an in-process MCP `Client`, and a monkeypatched failing step to prove error recovery.
**What would you improve?** LLM-assisted requirements, a richer capability catalog, auth for remote (HTTP) deployment, and CI.

## Resume bullets that match what is built
- Built a FastMCP server with 7 typed tools (Pydantic schemas) that convert a feature request into requirements, Jira-style tickets, backend plans and release checklists.
- Implemented input validation, structured error handling and per-step error recovery in a multi-step workflow tool.
- Wrote 17 pytest tests, including end-to-end tests through an MCP client and failure-injection tests.
