# DevFlow: MCP Dev-Workflow Automation Server

An MCP (Model Context Protocol) server built with **FastMCP** that turns a plain-English
feature request into engineering artifacts: structured requirements, Jira-style tickets,
a backend plan and a release checklist. Any MCP client (Claude Desktop, MCP Inspector)
can call the tools.

## Features
| Tool | What it does |
|---|---|
| `create_requirements` | User stories, functional / non-functional requirements, acceptance criteria, assumptions, open questions |
| `generate_tickets` | Jira-style tickets (key, type, priority, story points). Saved to `data/*.json` (mock Jira, no real API) |
| `generate_backend_plan` | REST endpoints, data models, implementation tasks, risks |
| `create_release_checklist` | Release checklist + rollback plan; `risk_level` low/medium/high |
| `run_full_workflow` | Runs all four steps in order with **per-step error recovery** |
| `list_saved_tickets` / `read_saved_tickets` | Browse saved ticket files (path-traversal safe) |

**Design notes**
- Typed tool schemas with Pydantic, so clients get structured, validated output.
- Deterministic rule-based engine (`devflow/capabilities.py`). No LLM key needed; the LLM
  client is the "brain", this server provides the tools. Same input gives the same output, so it is testable.
- Input validation with clear error messages (`devflow/validation.py`).
- Guardrails: unexpected errors are logged server-side and returned as clean `ToolError`s; one failing
  workflow step never hides the others.

## Project structure
```
mcp-dev-workflow-agent/
├── devflow/
│   ├── server.py        # FastMCP server + tool definitions + error handling
│   ├── planners.py      # logic that builds each artifact
│   ├── capabilities.py  # keyword -> requirements/endpoints/tasks knowledge base
│   ├── schemas.py       # Pydantic models (tool schemas)
│   └── validation.py    # input validation
├── tests/               # 17 tests (unit + end-to-end through an MCP client)
├── demo.py              # run everything without Claude Desktop
├── claude_desktop_config.example.json
├── INTERVIEW_GUIDE.md
└── requirements.txt
```

## Setup
Requires Python 3.10+.
```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate        Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
python demo.py                      # quick demo, prints tickets + endpoints
python demo.py "Add search with filters for products"
python -m pytest -q                 # run tests (should show 17 passed)
python -m devflow.server            # start MCP server over stdio
npx @modelcontextprotocol/inspector python -m devflow.server   # visual tool tester
```

## Use with Claude Desktop
1. Copy `claude_desktop_config.example.json` content into your Claude Desktop config
   (Settings > Developer > Edit Config).
2. Replace the paths with the absolute path to your Python (inside `.venv`) and this project.
3. Restart Claude Desktop, then try:
   *"Use DevFlow to run the full workflow for: add user login with password reset via email."*

## Roadmap (not built yet)
- Real Jira API integration (currently mock JSON files)
- GitHub repository inspection and PR review tools
- LLM-assisted requirement generation on top of the rule engine
