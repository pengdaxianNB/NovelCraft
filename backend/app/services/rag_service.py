from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.rag import RagDocument, RagChunk
from app.ai.rag.splitter import split_document
from app.ai.rag.embedder import embed_texts
from app.ai.rag.retriever import hybrid_search


class RagService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_document(self, novel_id: str, filename: str, content: str) -> RagDocument:
        doc = RagDocument(novel_id=novel_id, filename=filename, content=content)
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        chunks = split_document(content)
        if not chunks:
            doc.status = "ready"
            doc.chunk_count = 0
            await self.db.commit()
            return doc

        chunk_objs = []
        for i, chunk_text in enumerate(chunks):
            chunk_objs.append(RagChunk(
                document_id=doc.id,
                chunk_index=i,
                content=chunk_text,
                metadata_json={"filename": filename},
            ))

        try:
            embeddings = await embed_texts([c.content for c in chunk_objs])
            for chunk, emb in zip(chunk_objs, embeddings):
                chunk.embedding = emb
        except Exception:
            for chunk in chunk_objs:
                chunk.embedding = None

        self.db.add_all(chunk_objs)
        doc.chunk_count = len(chunks)
        doc.status = "ready"
        await self.db.commit()
        return doc

    async def list_documents(self, novel_id: str) -> list[RagDocument]:
        stmt = select(RagDocument).where(RagDocument.novel_id == novel_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def delete_document(self, document_id: str) -> bool:
        stmt = select(RagDocument).where(RagDocument.id == document_id)
        result = await self.db.execute(stmt)
        doc = result.scalar_one_or_none()
        if not doc:
            return False
        await self.db.delete(doc)
        await self.db.commit()
        return True

    async def search(self, novel_id: str, query: str, top_k: int = 5) -> list[dict]:
        return await hybrid_search(self.db, novel_id, query, top_k)
