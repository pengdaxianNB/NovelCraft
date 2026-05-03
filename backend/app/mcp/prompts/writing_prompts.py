from mcp.server import Server


def register_prompts(server: Server):
    @server.prompt()
    async def continue_writing(novel_id: str, chapter_number: int) -> str:
        """根据当前进度生成续写提示词，聚合上下文"""
        return f"Continue writing prompt for novel {novel_id}, chapter {chapter_number}"

    @server.prompt()
    async def character_dialogue(novel_id: str, character_id: str, scene: str) -> str:
        """为特定角色生成对话提示词"""
        return f"Character dialogue prompt for character {character_id} in scene: {scene}"
