from mcp.server import Server


def register_knowledge_tools(server: Server):
    @server.tool()
    async def search_knowledge_base(novel_id: str, query_text: str, top_k: int = 5) -> str:
        """从RAG知识库中检索用户上传的参考资料"""
        return f"Knowledge base search: {query_text} (top_k={top_k})"
