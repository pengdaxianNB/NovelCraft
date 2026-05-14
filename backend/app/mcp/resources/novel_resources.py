import json
from mcp.server.fastmcp import FastMCP
from app.mcp import get_mcp_db


def register_resources(server: FastMCP):
    @server.resource("novel://{id}/outline")
    async def get_outline(id: str) -> str:
        """获取小说的完整大纲树"""
        from app.services.outline_service import OutlineService

        try:
            async with get_mcp_db() as db:
                outlines = await OutlineService(db).list_outlines(id)

            def serialize_tree(nodes):
                return [
                    {
                        "id": str(n.id),
                        "title": n.title,
                        "level": n.level,
                        "summary": n.summary,
                        "status": n.status,
                        "sequence": n.sequence,
                        "children": serialize_tree(n.children),
                    }
                    for n in nodes
                ]

            return json.dumps(serialize_tree(outlines), ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": f"获取大纲失败: {str(e)}"})

    @server.resource("novel://{id}/characters")
    async def get_characters(id: str) -> str:
        """获取小说所有角色档案"""
        from app.services.character_service import CharacterService

        try:
            async with get_mcp_db() as db:
                characters = await CharacterService(db).list_characters(id)

            return json.dumps(
                [
                    {
                        "id": str(c.id),
                        "name": c.name,
                        "role": c.role,
                        "profile": c.profile,
                        "created_at": str(c.created_at) if c.created_at else None,
                    }
                    for c in characters
                ],
                ensure_ascii=False,
                indent=2,
            )
        except Exception as e:
            return json.dumps({"error": f"获取角色失败: {str(e)}"})

    @server.resource("novel://{id}/style")
    async def get_style(id: str) -> str:
        """获取小说的写作风格配置"""
        from app.services.novel_service import NovelService

        try:
            async with get_mcp_db() as db:
                novel = await NovelService(db).get_novel(id)
                if not novel:
                    return json.dumps({"error": f"小说 {id} 不存在"})

            return json.dumps(
                {
                    "novel_id": str(novel.id),
                    "title": novel.title,
                    "genre": novel.genre,
                    "synopsis": novel.synopsis,
                    "style_config": novel.style_config,
                    "schedule_config": novel.schedule_config,
                    "status": novel.status,
                },
                ensure_ascii=False,
                indent=2,
            )
        except Exception as e:
            return json.dumps({"error": f"获取风格配置失败: {str(e)}"})

    @server.resource("novel://{id}/chapters")
    async def get_chapters(id: str) -> str:
        """获取小说所有章节的元数据列表"""
        from app.services.chapter_service import ChapterService

        try:
            async with get_mcp_db() as db:
                chapters = await ChapterService(db).list_chapters(id)

            return json.dumps(
                [
                    {
                        "id": str(ch.id),
                        "chapter_number": ch.chapter_number,
                        "title": ch.title,
                        "word_count": ch.word_count,
                        "status": ch.status,
                        "updated_at": str(ch.updated_at) if ch.updated_at else None,
                    }
                    for ch in sorted(chapters, key=lambda x: x.chapter_number)
                ],
                ensure_ascii=False,
                indent=2,
            )
        except Exception as e:
            return json.dumps({"error": f"获取章节目录失败: {str(e)}"})

    @server.resource("novel://{id}/chapter/{number}")
    async def get_chapter_by_number(id: str, number: int) -> str:
        """按章节号获取指定章节的完整正文"""
        from app.services.chapter_service import ChapterService

        try:
            async with get_mcp_db() as db:
                chapters = await ChapterService(db).list_chapters(id)
                target = next((ch for ch in chapters if ch.chapter_number == number), None)
                if not target:
                    return json.dumps({"error": f"小说 {id} 中第 {number} 章不存在"})

            return json.dumps(
                {
                    "id": str(target.id),
                    "chapter_number": target.chapter_number,
                    "title": target.title,
                    "content": target.content,
                    "word_count": target.word_count,
                    "status": target.status,
                    "generation_meta": target.generation_meta,
                },
                ensure_ascii=False,
                indent=2,
            )
        except Exception as e:
            return json.dumps({"error": f"获取章节失败: {str(e)}"})

    @server.resource("novel://{id}/world-settings")
    async def get_world_settings(id: str) -> str:
        """获取小说的所有世界观设定"""
        from app.services.world_setting_service import WorldSettingService

        try:
            async with get_mcp_db() as db:
                settings = await WorldSettingService(db).list_world_settings(id)

            return json.dumps(
                [
                    {
                        "id": str(ws.id),
                        "category": ws.category,
                        "title": ws.title,
                        "content": ws.content,
                    }
                    for ws in settings
                ],
                ensure_ascii=False,
                indent=2,
            )
        except Exception as e:
            return json.dumps({"error": f"获取世界观设定失败: {str(e)}"})

    @server.resource("novel://{id}/summary")
    async def get_summary(id: str) -> str:
        """获取小说概览：基本信息 + 进度统计"""
        from app.services.novel_service import NovelService
        from app.services.chapter_service import ChapterService
        from app.services.character_service import CharacterService
        from app.services.outline_service import OutlineService

        try:
            async with get_mcp_db() as db:
                novel = await NovelService(db).get_novel(id)
                if not novel:
                    return json.dumps({"error": f"小说 {id} 不存在"})

                chapters = await ChapterService(db).list_chapters(id)
                characters = await CharacterService(db).list_characters(id)
                outlines = await OutlineService(db).list_outlines(id)

            def count_tree(nodes):
                total = 0
                for n in nodes:
                    total += 1 + count_tree(n.children)
                return total

            published = [ch for ch in chapters if ch.status == "published"]
            total_words = sum(ch.word_count or 0 for ch in chapters)

            return json.dumps(
                {
                    "novel_id": str(novel.id),
                    "title": novel.title,
                    "genre": novel.genre,
                    "synopsis": novel.synopsis,
                    "status": novel.status,
                    "progress": {
                        "total_chapters": len(chapters),
                        "published_chapters": len(published),
                        "total_words": total_words,
                        "total_characters": len(characters),
                        "total_outline_nodes": count_tree(outlines),
                    },
                    "latest_chapter": max(ch.chapter_number for ch in chapters) if chapters else 0,
                },
                ensure_ascii=False,
                indent=2,
            )
        except Exception as e:
            return json.dumps({"error": f"获取小说概览失败: {str(e)}"})
