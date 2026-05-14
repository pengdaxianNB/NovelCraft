import json
from mcp.server.fastmcp import FastMCP
from app.mcp import get_mcp_db


def register_consistency_tools(server: FastMCP):
    @server.tool()
    async def check_consistency(
        novel_id: str,
        chapter_content: str = "",
        chapter_id: str = "",
    ) -> str:
        """检查新章节与已有设定的矛盾。传入 chapter_id 从数据库加载，或传入 chapter_content 直接检查"""
        from app.services.novel_service import NovelService
        from app.services.character_service import CharacterService
        from app.services.chapter_service import ChapterService
        from app.services.world_setting_service import WorldSettingService
        from app.ai.agents.review_agent import ReviewAgent

        try:
            # Resolve chapter content and title
            chapter_title = "待审校章节"
            content_to_review = chapter_content

            async with get_mcp_db() as db:
                if chapter_id:
                    ch = await ChapterService(db).get_chapter(chapter_id)
                    if not ch:
                        return json.dumps({"error": f"章节 {chapter_id} 不存在"})
                    content_to_review = ch.content or ""
                    chapter_title = f"第{ch.chapter_number}章 {ch.title}"
                    if not chapter_content:
                        chapter_content_override = ""
                    novel_id_actual = str(ch.novel_id)
                else:
                    novel_id_actual = novel_id

                if not content_to_review:
                    return json.dumps({"error": "请提供 chapter_id 或 chapter_content"})

                novel = await NovelService(db).get_novel(novel_id_actual)
                if not novel:
                    return json.dumps({"error": f"小说 {novel_id_actual} 不存在"})

                characters = await CharacterService(db).list_characters(novel_id_actual)
                character_context = "\n".join(
                    f"- {c.name}({c.role}): "
                    + "; ".join(f"{k}: {v}" for k, v in (c.profile or {}).items() if v)
                    for c in characters
                )

                world_settings = await WorldSettingService(db).list_world_settings(novel_id_actual)
                world_context = "\n".join(
                    f"[{ws.category}] {ws.title}: {ws.content}" for ws in world_settings
                )

                chapters = await ChapterService(db).list_chapters(novel_id_actual)
                previous_context = "\n\n".join(
                    f"第{ch.chapter_number}章 {ch.title}\n{(ch.content or '')[-500:]}"
                    for ch in sorted(chapters, key=lambda x: x.chapter_number, reverse=True)[:3]
                )

                style = novel.style_config or {}

            agent = ReviewAgent()
            result = await agent.review(
                chapter_title=chapter_title,
                chapter_content=content_to_review,
                words_per_chapter=style.get("words_per_chapter", 3000),
                style_config=json.dumps(style, ensure_ascii=False),
                character_context=character_context,
                world_context=world_context,
                previous_context=previous_context,
            )

            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": f"一致性检查失败: {str(e)}"})
