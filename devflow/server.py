"""FastMCP server exposing the DevFlow tools.

Run:  python -m devflow.server          (stdio, for Claude Desktop / MCP Inspector)
"""
import functools
import logging
import sys

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from . import planners
from .schemas import (BackendPlan, ReleaseChecklist, Requirements, StepResult, TicketBundle,
                      WorkflowResult)
from .validation import (ValidationError, validate_feature_request, validate_project_key,
                         validate_risk_level)

# stdout is reserved for the MCP protocol on stdio, so log to stderr.
logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("devflow")

mcp = FastMCP(
    name="DevFlow",
    instructions=("Turns a feature request into requirements, Jira-style tickets, a backend plan "
                  "and a release checklist. Prefer run_full_workflow for a complete result."),
)


def safe_tool(fn):
    """Turn validation/expected errors into clean ToolErrors and log unexpected ones."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            log.info("tool=%s called", fn.__name__)
            return fn(*args, **kwargs)
        except ValidationError as e:
            log.warning("tool=%s validation error: %s", fn.__name__, e)
            raise ToolError(str(e)) from e
        except FileNotFoundError as e:
            raise ToolError(str(e)) from e
        except Exception as e:  # unexpected: log full trace, hide internals from client
            log.exception("tool=%s crashed", fn.__name__)
            raise ToolError(f"Internal error in {fn.__name__}. Check server logs.") from e
    return wrapper


@mcp.tool
@safe_tool
def create_requirements(feature_request: str, target_users: str = "end user") -> Requirements:
    """Convert a plain-English feature request into structured requirements:
    user stories, functional/non-functional requirements, acceptance criteria,
    assumptions and open questions."""
    request = validate_feature_request(feature_request)
    return planners.build_requirements(request, (target_users or "end user").strip())


@mcp.tool
@safe_tool
def generate_tickets(feature_request: str, project_key: str = "PROJ") -> TicketBundle:
    """Generate Jira-style tickets (key, type, priority, story points, acceptance
    criteria) for a feature and save them as JSON in the data/ folder.
    Mock Jira: nothing is sent to a real Jira instance."""
    request = validate_feature_request(feature_request)
    return planners.build_tickets(request, validate_project_key(project_key))


@mcp.tool
@safe_tool
def generate_backend_plan(feature_request: str) -> BackendPlan:
    """Produce a backend plan: REST endpoints, data models, implementation tasks and risks."""
    return planners.build_backend_plan(validate_feature_request(feature_request))


@mcp.tool
@safe_tool
def create_release_checklist(feature_request: str, risk_level: str = "medium") -> ReleaseChecklist:
    """Create a release/validation checklist and rollback plan.
    risk_level: low | medium | high (high adds rollout and security checks)."""
    request = validate_feature_request(feature_request)
    return planners.build_checklist(request, validate_risk_level(risk_level))


@mcp.tool
@safe_tool
def run_full_workflow(feature_request: str, project_key: str = "PROJ",
                      risk_level: str = "medium") -> WorkflowResult:
    """Run all four steps in order. A failing step is recorded and the workflow
    continues, so one failure never hides the other results (error recovery)."""
    request = validate_feature_request(feature_request)
    key, risk = validate_project_key(project_key), validate_risk_level(risk_level)
    steps, out = [], {}
    pipeline = [
        ("requirements", lambda: planners.build_requirements(request)),
        ("tickets", lambda: planners.build_tickets(request, key)),
        ("backend_plan", lambda: planners.build_backend_plan(request)),
        ("release_checklist", lambda: planners.build_checklist(request, risk)),
    ]
    for name, step in pipeline:
        try:
            out[name] = step()
            steps.append(StepResult(step=name, status="ok"))
        except Exception as e:
            log.exception("workflow step %s failed", name)
            steps.append(StepResult(step=name, status="failed", error=f"{type(e).__name__}: {e}"))
    return WorkflowResult(feature_request=request, steps=steps,
                          all_steps_ok=all(s.status == "ok" for s in steps),
                          requirements=out.get("requirements"), tickets=out.get("tickets"),
                          backend_plan=out.get("backend_plan"),
                          release_checklist=out.get("release_checklist"))


@mcp.tool
@safe_tool
def list_saved_tickets() -> list[str]:
    """List ticket files previously saved by generate_tickets."""
    return planners.list_saved()


@mcp.tool
@safe_tool
def read_saved_tickets(file_name: str) -> dict:
    """Read one saved ticket file by name (use list_saved_tickets to see names)."""
    return planners.read_saved(file_name)


def main():
    mcp.run()  # stdio transport by default


if __name__ == "__main__":
    main()
