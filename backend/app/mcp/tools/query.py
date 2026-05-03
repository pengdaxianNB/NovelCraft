from mcp.server import Server


def register_query_tools(server: Server):
    @server.tool()
    async def query_characters(novel_id: str, query_text: str, top_k: int = 5) -> str:
        """语义检索相关角色及其关系，返回角色档案"""
        return f"Character query: {query_text} (top_k={top_k})"

    @server.tool()
    async def query_plot_context(novel_id: str, query_text: str, top_k: int = 3) -> str:
        """检索相关已写章节片段，保持剧情一致"""
        return f"Plot context query: {query_text} (top_k={top_k})"

    @server.tool()
    async def get_writing_context(novel_id: str, chapter_number: int) -> str:
        """聚合当前写作所需的所有上下文（大纲、角色、前几章摘要、风格配置）"""
        return f"Writing context for novel {novel_id}, chapter {chapter_number}"
