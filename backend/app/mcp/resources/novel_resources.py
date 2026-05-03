from mcp.server import Server


def register_resources(server: Server):
    @server.resource("novel://{id}/outline")
    async def get_outline(id: str) -> str:
        """获取小说的完整大纲树"""
        return f"Outline tree for novel {id}"

    @server.resource("novel://{id}/characters")
    async def get_characters(id: str) -> str:
        """获取小说所有角色档案"""
        return f"Characters for novel {id}"

    @server.resource("novel://{id}/style")
    async def get_style(id: str) -> str:
        """获取小说的写作风格配置"""
        return f"Style config for novel {id}"
