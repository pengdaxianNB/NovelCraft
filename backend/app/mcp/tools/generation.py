import json

from mcp.server.fastmcp import FastMCP

from app.mcp import get_mcp_db


def register_generation_tools(server: FastMCP):
    @server.tool()
    async def generate_outline(novel_id: str, level: str, parent_id: str = "", count: int = 5) -> str:
        """为指定小说生成新的大纲节点。level: volume/arc/chapter"""
        from app.services.generation_dispatch_service import GenerationDispatchService

        try:
            async with get_mcp_db() as db:
                result = await GenerationDispatchService(db).dispatch_outline(
                    novel_id=novel_id, level=level, parent_id=parent_id, count=count,
                )
            result["message"] = f"大纲生成已入队 (level={level}, count={count})，通过 task_id 查询进度"
            return json.dumps(result, ensure_ascii=False, indent=2)
        except ValueError as e:
            return json.dumps({"error": str(e)})
        except Exception as e:
            return json.dumps({"error": f"大纲生成派发失败: {str(e)}"})

    @server.tool()
    async def generate_chapter(
        novel_id: str,
        chapter_number: int = 0,
        outline_id: str = "",
        description: str = "",
    ) -> str:
        """生成具体章节正文。chapter_number 为 0 时自动取最新章节号+1"""
        from app.services.generation_dispatch_service import GenerationDispatchService

        try:
            async with get_mcp_db() as db:
                result = await GenerationDispatchService(db).dispatch_chapter(
                    novel_id=novel_id,
                    outline_id=outline_id,
                    chapter_number=chapter_number,
                    description=description,
                )
            result["message"] = f"第 {result['chapter_number']} 章生成已入队，通过 task_id 查询进度"
            return json.dumps(result, ensure_ascii=False, indent=2)
        except ValueError as e:
            return json.dumps({"error": str(e)})
        except Exception as e:
            return json.dumps({"error": f"章节生成派发失败: {str(e)}"})

    @server.tool()
    async def rewrite_section(
        instruction: str,
        chapter_id: str = "",
        target_text: str = "",
    ) -> str:
        """按指令改写文本。传 chapter_id 从数据库加载全文，或传 target_text 直接改写指定段落"""
        from app.ai.utils import create_llm, ainvoke_with_retry
        from langchain_core.messages import HumanMessage
        from app.services.chapter_service import ChapterService

        try:
            text_to_rewrite = target_text
            chapter_context = ""

            if chapter_id:
                async with get_mcp_db() as db:
                    chapter = await ChapterService(db).get_chapter(chapter_id)
                    if not chapter:
                        return json.dumps({"error": f"章节 {chapter_id} 不存在"})
                    chapter_context = f"所属章节第{chapter.chapter_number}章《{chapter.title}》"
                    if not text_to_rewrite:
                        text_to_rewrite = chapter.content or ""

            if not text_to_rewrite:
                return json.dumps({"error": "请提供 target_text 或 chapter_id"})

            llm = create_llm(temperature=0.7, max_tokens=2000)
            prompt = f"""你是一位专业网文作者。请按照以下指令改写文本。

改写指令: {instruction}

{chapter_context}

原文本:
---
{text_to_rewrite[:2000]}
---

请直接输出改写后的结果，保持原意但优化表达。不要添加前缀说明。"""

            response = await ainvoke_with_retry(llm, [HumanMessage(content=prompt)])
            rewritten = str(response.content)

            return json.dumps({
                "rewritten_text": rewritten,
                "original_length": len(text_to_rewrite),
                "rewritten_length": len(rewritten),
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": f"改写失败: {str(e)}"})

    @server.tool()
    async def get_generation_task(task_id: str) -> str:
        """查询生成任务的进度和结果"""
        from sqlalchemy import select
        from app.models.generation_task import GenerationTask

        try:
            async with get_mcp_db() as db:
                stmt = select(GenerationTask).where(GenerationTask.id == task_id)
                result = await db.execute(stmt)
                task = result.scalar_one_or_none()
                if not task:
                    return json.dumps({"error": f"任务 {task_id} 不存在"})

            return json.dumps({
                "task_id": str(task.id),
                "task_type": task.task_type,
                "status": task.status,
                "progress": task.progress,
                "result": task.result,
                "error_message": task.error_message,
                "started_at": str(task.started_at) if task.started_at else None,
                "completed_at": str(task.completed_at) if task.completed_at else None,
                "created_at": str(task.created_at),
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": f"查询任务失败: {str(e)}"})
