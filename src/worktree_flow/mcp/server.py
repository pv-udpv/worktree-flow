"""MCP server with auto-exposure from FastAPI."""

import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("worktree-flow")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools (auto-generated from FastAPI)."""
    # TODO: Auto-generate from FastAPI routes
    return [
        Tool(
            name="create-worktree-from-issue",
            description="Create worktree from issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string", "description": "Issue ID"},
                    "provider": {"type": "string", "description": "Provider name"},
                },
                "required": ["issue_id"],
            },
        ),
        Tool(
            name="list-worktrees",
            description="List all worktrees",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Execute MCP tool (calls FastAPI endpoint)."""
    # TODO: Implement FastAPI endpoint calls
    return [
        TextContent(
            type="text",
            text=f"Tool '{name}' called with args: {arguments}\n\n⚠️  Not implemented yet - coming soon!",
        )
    ]


async def main():
    """Run MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
