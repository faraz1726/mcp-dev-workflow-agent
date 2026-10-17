"""End-to-end tests: call the tools through a real MCP client, in-process."""
import asyncio

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from devflow import planners
from devflow.server import mcp

REQ = "Add user login with password reset via email"


@pytest.fixture(autouse=True)
def isolated_data(tmp_path, monkeypatch):
    monkeypatch.setattr(planners, "DATA_DIR", tmp_path)


def call(tool, args):
    async def run():
        async with Client(mcp) as c:
            return await c.call_tool(tool, args)
    return asyncio.run(run())


def test_all_tools_registered():
    async def run():
        async with Client(mcp) as c:
            return {t.name for t in await c.list_tools()}
    names = asyncio.run(run())
    assert {"create_requirements", "generate_tickets", "generate_backend_plan",
            "create_release_checklist", "run_full_workflow"} <= names


def test_full_workflow_succeeds():
    data = call("run_full_workflow", {"feature_request": REQ, "project_key": "APP"}).data
    assert data.all_steps_ok
    assert [s.step for s in data.steps] == ["requirements", "tickets", "backend_plan",
                                            "release_checklist"]
    assert data.tickets.tickets[0].key == "APP-1"


def test_bad_input_returns_clean_tool_error():
    with pytest.raises(ToolError, match="too short"):
        call("generate_tickets", {"feature_request": "hi"})


def test_bad_project_key_rejected():
    with pytest.raises(ToolError, match="project_key"):
        call("generate_tickets", {"feature_request": REQ, "project_key": "bad key!"})


def test_workflow_recovers_from_failing_step(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("disk full")
    monkeypatch.setattr(planners, "build_tickets", boom)
    data = call("run_full_workflow", {"feature_request": REQ}).data
    assert not data.all_steps_ok
    failed = [s for s in data.steps if s.status == "failed"]
    assert failed[0].step == "tickets" and "disk full" in failed[0].error
    assert data.requirements is not None and data.release_checklist is not None
