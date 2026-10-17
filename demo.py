"""Demo without Claude Desktop: calls the MCP server in-process and prints results.

Usage: python demo.py "Add password reset via email with rate limiting"
"""
import asyncio
import sys

from fastmcp import Client

from devflow.server import mcp

DEFAULT = "Add user login with password reset via email and let users upload a profile photo"


async def main(request: str):
    async with Client(mcp) as client:
        tools = await client.list_tools()
        print("TOOLS:", ", ".join(t.name for t in tools), "\n")
        res = await client.call_tool("run_full_workflow", {"feature_request": request,
                                                           "project_key": "DEMO"})
        data = res.data
        print("Workflow ok:", data.all_steps_ok)
        print("Detected capabilities:", data.requirements.detected_capabilities)
        print(f"\nTickets ({data.tickets.total_story_points} pts) saved to {data.tickets.saved_to}")
        for t in data.tickets.tickets:
            print(f"  {t.key:8} [{t.type:5}] {t.priority:6} {t.story_points:>2}pt  {t.title}")
        print("\nEndpoints:")
        for e in data.backend_plan.endpoints:
            print(f"  {e.method:6} {e.path:25} {e.purpose}")
        print(f"\nChecklist items: {len(data.release_checklist.items)}")

        print("\nBad input test:")
        try:
            await client.call_tool("generate_tickets", {"feature_request": "hi"})
        except Exception as e:
            print("  Clean error ->", e)


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or DEFAULT))
