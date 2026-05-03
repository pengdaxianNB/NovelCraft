from mcp.server import Server
from mcp.server.sse import SseServerTransport
from app.mcp.tools.generation import register_generation_tools
from app.mcp.tools.query import register_query_tools
from app.mcp.tools.knowledge import register_knowledge_tools
from app.mcp.tools.consistency import register_consistency_tools
from app.mcp.resources.novel_resources import register_resources
from app.mcp.prompts.writing_prompts import register_prompts

server = Server("novel-writing-agent")

register_generation_tools(server)
register_query_tools(server)
register_knowledge_tools(server)
register_consistency_tools(server)
register_resources(server)
register_prompts(server)


def create_sse_app():
    return SseServerTransport("/mcp/messages")
