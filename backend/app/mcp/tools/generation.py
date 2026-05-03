from mcp.server import Server
from mcp.types import Tool, TextContent


def register_generation_tools(server: Server):
    @server.tool()
    async def generate_outline(novel_id: str, level: str, parent_id: str = "", count: int = 5) -> str:
        """为指定小说生成新的大纲节点。level: volume/arc/chapter"""
        return f"Outline generation triggered for novel {novel_id}, level={level}, count={count}"

    @server.tool()
    async def generate_chapter(novel_id: str, outline_id: str, chapter_number: int) -> str:
        """生成具体章节正文，流式返回写作过程"""
        return f"Chapter generation triggered: novel={novel_id}, chapter={chapter_number}"

    @server.tool()
    async def rewrite_section(chapter_id: str, target_text: str, instruction: str) -> str:
        """按指令重写章节的某一段落"""
        return f"Rewrite triggered for chapter {chapter_id}"
