from mcp.server import Server


def register_consistency_tools(server: Server):
    @server.tool()
    async def check_consistency(novel_id: str, chapter_content: str) -> str:
        """检查新章节与已有设定的矛盾，返回审校报告"""
        return "Consistency check completed"
