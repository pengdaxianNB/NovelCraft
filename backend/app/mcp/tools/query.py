import json
from mcp.server.fastmcp import FastMCP
from app.mcp import get_mcp_db


def register_query_tools(server: FastMCP):
    @server.tool()
    async def query_characters(novel_id: str, query_text: str, top_k: int = 5) -> str:
        """语义检索相关角色及其关系，返回角色档案"""
        from app.services.character_service import CharacterService
        from app.ai.rag.retriever import hybrid_search

        try:
            async with get_mcp_db() as db:
                rag_results = await hybrid_search(db, novel_id, query_text, top_k)
                characters = await CharacterService(db).list_characters(novel_id)

            query_lower = query_text.lower()
            matched_chars = []
            for c in characters:
                profile_text = " ".join(
                    str(v) for v in (c.profile or {}).values() if v
                )
                if query_lower in c.name.lower() or query_lower in profile_text.lower():
                    matched_chars.append({
                        "id": str(c.id),
                        "name": c.name,
                        "role": c.role,
                        "profile": c.profile,
                    })
                    if len(matched_chars) >= top_k:
                        break

            return json.dumps({
                "characters": matched_chars,
                "knowledge_results": [
                    {
                        "content": r.get("content", ""),
                        "similarity": r.get("similarity"),
                        "metadata": r.get("metadata", {}),
                    }
                    for r in rag_results
                ],
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": f"查询角色失败: {str(e)}"})

    @server.tool()
    async def query_plot_context(novel_id: str, query_text: str, top_k: int = 3) -> str:
        """检索相关已写章节片段，保持剧情一致"""
        from app.services.chapter_service import ChapterService
        from app.ai.rag.retriever import hybrid_search

        try:
            async with get_mcp_db() as db:
                rag_results = await hybrid_search(db, novel_id, query_text, top_k)
                chapters = await ChapterService(db).list_chapters(novel_id)

            query_lower = query_text.lower()
            matched = []
            for ch in chapters:
                if not ch.content:
                    continue
                if query_lower in ch.title.lower() or query_lower in (ch.content or "").lower():
                    matched.append({
                        "id": str(ch.id),
                        "chapter_number": ch.chapter_number,
                        "title": ch.title,
                        "excerpt": ch.content[:500],
                        "word_count": ch.word_count,
                        "status": ch.status,
                    })
                    if len(matched) >= top_k:
                        break

            return json.dumps({
                "chapters": matched,
                "knowledge_results": [
                    {"content": r.get("content", ""), "similarity": r.get("similarity")}
                    for r in rag_results
                ],
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": f"查询剧情上下文失败: {str(e)}"})

    @server.tool()
    async def get_writing_context(novel_id: str, chapter_number: int) -> str:
        """聚合当前写作所需的所有上下文（大纲、角色、前几章摘要、风格配置）"""
        from app.services.novel_service import NovelService
        from app.services.outline_service import OutlineService
        from app.services.character_service import CharacterService
        from app.services.chapter_service import ChapterService

        try:
            async with get_mcp_db() as db:
                novel = await NovelService(db).get_novel(novel_id)
                if not novel:
                    return json.dumps({"error": f"小说 {novel_id} 不存在"})

                outlines = await OutlineService(db).list_outlines(novel_id)
                characters = await CharacterService(db).list_characters(novel_id)
                chapters = await ChapterService(db).list_chapters(novel_id)

            def flatten_outlines(nodes, depth=0):
                result = []
                for n in nodes:
                    prefix = "  " * depth
                    result.append({
                        "id": str(n.id),
                        "title": n.title,
                        "level": n.level,
                        "summary": n.summary,
                        "status": n.status,
                    })
                    if n.children:
                        result.extend(flatten_outlines(n.children, depth + 1))
                return result

            style = novel.style_config or {}
            return json.dumps({
                "novel": {
                    "id": str(novel.id),
                    "title": novel.title,
                    "genre": novel.genre,
                    "synopsis": novel.synopsis,
                    "style_config": style,
                },
                "chapter_number": chapter_number,
                "outlines": flatten_outlines(outlines),
                "characters": [
                    {
                        "id": str(c.id),
                        "name": c.name,
                        "role": c.role,
                        "profile": c.profile,
                    }
                    for c in characters
                ],
                "recent_chapters": [
                    {
                        "id": str(ch.id),
                        "chapter_number": ch.chapter_number,
                        "title": ch.title,
                        "excerpt": (ch.content or "")[-500:],
                        "word_count": ch.word_count,
                        "status": ch.status,
                    }
                    for ch in sorted(chapters, key=lambda x: x.chapter_number, reverse=True)[:5]
                ],
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": f"构建写作上下文失败: {str(e)}"})
