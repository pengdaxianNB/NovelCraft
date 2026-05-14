from mcp.server.fastmcp import FastMCP

from app.mcp.tools.generation import register_generation_tools
from app.mcp.tools.query import register_query_tools
from app.mcp.tools.knowledge import register_knowledge_tools
from app.mcp.tools.consistency import register_consistency_tools
from app.mcp.tools.management import register_management_tools
from app.mcp.resources.novel_resources import register_resources
from app.mcp.prompts.writing_prompts import register_prompts

mcp = FastMCP("novel-writing-agent")

register_generation_tools(mcp)
register_query_tools(mcp)
register_knowledge_tools(mcp)
register_consistency_tools(mcp)
register_management_tools(mcp)
register_resources(mcp)
register_prompts(mcp)


def create_sse_app():
    """Return the ASGI app that serves the MCP server over SSE."""
    return mcp.sse_app()
