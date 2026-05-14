import json
from mcp.server.fastmcp import FastMCP
from app.mcp import get_mcp_db


def register_knowledge_tools(server: FastMCP):
    @server.tool()
    async def search_knowledge_base(novel_id: str, query_text: str, top_k: int = 5) -> str:
        """从RAG知识库中检索用户上传的参考资料"""
        from app.services.rag_service import RagService

        try:
            async with get_mcp_db() as db:
                results = await RagService(db).search(novel_id, query_text, top_k)

            return json.dumps(
                [
                    {
                        "id": str(r.get("id", "")),
                        "content": r.get("content", ""),
                        "similarity": r.get("similarity"),
                        "metadata": r.get("metadata", {}),
                    }
                    for r in results
                ],
                ensure_ascii=False,
                indent=2,
            )
        except Exception as e:
            return json.dumps({"error": f"知识库搜索失败: {str(e)}"})

    @server.tool()
    async def upload_knowledge_document(novel_id: str, filename: str, content: str) -> str:
        """上传参考文档到 RAG 知识库，自动分段并嵌入向量"""
        from app.services.rag_service import RagService

        try:
            async with get_mcp_db() as db:
                doc = await RagService(db).upload_document(novel_id, filename, content)

            return json.dumps({
                "id": str(doc.id),
                "filename": doc.filename,
                "chunk_count": doc.chunk_count,
                "status": doc.status,
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": f"上传文档失败: {str(e)}"})
