from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.ai.rag.embedder import embed_query, embed_query_sync


async def hybrid_search(
    db: AsyncSession, novel_id: str, query: str, top_k: int = 5,
) -> list[dict]:
    query_embedding = None
    try:
        query_embedding = await embed_query(query)
    except Exception:
        query_embedding = None

    vector_results = []
    if query_embedding is not None:
        vector_sql = text("""
            SELECT rc.id, rc.content, rc.metadata,
                   1 - (rc.embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM rag_chunks rc
            JOIN rag_documents rd ON rc.document_id = rd.id
            WHERE rd.novel_id = CAST(:novel_id AS uuid) AND rc.embedding IS NOT NULL
            ORDER BY rc.embedding <=> CAST(:embedding AS vector)
            LIMIT 10
        """)
        try:
            result = await db.execute(vector_sql, {
                "embedding": str(query_embedding),
                "novel_id": novel_id,
            })
            for r in result:
                m = dict(r._mapping)
                m["id"] = str(m["id"])
                vector_results.append(m)
        except Exception:
            await db.rollback()

    keyword_sql = text("""
        SELECT rc.id, rc.content, rc.metadata, 0.0 AS similarity
        FROM rag_chunks rc
        JOIN rag_documents rd ON rc.document_id = rd.id
        WHERE rd.novel_id = CAST(:novel_id AS uuid) AND rc.content ILIKE :pattern
        LIMIT 5
    """)
    keyword_results = []
    try:
        result = await db.execute(keyword_sql, {
            "novel_id": novel_id,
            "pattern": f"%{query[:160]}%",
        })
        for r in result:
            m = dict(r._mapping)
            m["id"] = str(m["id"])
            keyword_results.append(m)
    except Exception:
        await db.rollback()

    fused = _rrf_fusion(vector_results, keyword_results)
    return fused[:top_k]


def _rrf_fusion(vector_results: list[dict], keyword_results: list[dict], k: int = 60) -> list[dict]:
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}
    for rank, r in enumerate(vector_results):
        doc_id = r["id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
        docs[doc_id] = r
    for rank, r in enumerate(keyword_results):
        doc_id = r["id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
        docs[doc_id] = r
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [docs[doc_id] for doc_id, _ in ranked]


def hybrid_search_sync(
    db: Session, novel_id: str, query: str, top_k: int = 5,
) -> list[dict]:
    query_embedding = None
    try:
        query_embedding = embed_query_sync(query)
    except Exception:
        query_embedding = None

    vector_results = []
    if query_embedding is not None:
        vector_sql = text("""
            SELECT rc.id, rc.content, rc.metadata,
                   1 - (rc.embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM rag_chunks rc
            JOIN rag_documents rd ON rc.document_id = rd.id
            WHERE rd.novel_id = CAST(:novel_id AS uuid) AND rc.embedding IS NOT NULL
            ORDER BY rc.embedding <=> CAST(:embedding AS vector)
            LIMIT 10
        """)
        try:
            result = db.execute(vector_sql, {
                "embedding": str(query_embedding),
                "novel_id": novel_id,
            })
            for r in result:
                m = dict(r._mapping)
                m["id"] = str(m["id"])
                vector_results.append(m)
        except Exception:
            db.rollback()

    keyword_sql = text("""
        SELECT rc.id, rc.content, rc.metadata, 0.0 AS similarity
        FROM rag_chunks rc
        JOIN rag_documents rd ON rc.document_id = rd.id
        WHERE rd.novel_id = CAST(:novel_id AS uuid) AND rc.content ILIKE :pattern
        LIMIT 5
    """)
    keyword_results = []
    try:
        result = db.execute(keyword_sql, {
            "novel_id": novel_id,
            "pattern": f"%{query[:160]}%",
        })
        for r in result:
            m = dict(r._mapping)
            m["id"] = str(m["id"])
            keyword_results.append(m)
    except Exception:
        db.rollback()

    fused = _rrf_fusion(vector_results, keyword_results)
    return fused[:top_k]
