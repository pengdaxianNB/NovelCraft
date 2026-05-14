from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db
from app.schemas.rag import RagDocumentResponse, RagSearchRequest, RagSearchResult
from app.models.rag import RagDocument, RagChunk
from app.services.rag_service import RagService

router = APIRouter(tags=["rag"])


@router.post("/novels/{novel_id}/rag/documents", response_model=RagDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(novel_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    content = await file.read()
    return await RagService(db).upload_document(
        novel_id=novel_id,
        filename=file.filename or "unknown.txt",
        content=content.decode("utf-8", errors="ignore"),
    )


@router.get("/novels/{novel_id}/rag/documents", response_model=list[RagDocumentResponse])
async def list_documents(novel_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(RagDocument).where(RagDocument.novel_id == novel_id).order_by(RagDocument.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.delete("/rag/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(RagDocument).where(RagDocument.id == document_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)
    await db.commit()


@router.post("/rag/search", response_model=list[RagSearchResult])
async def search_rag(data: RagSearchRequest, db: AsyncSession = Depends(get_db)):
    if data.novel_id:
        results = await RagService(db).search(data.novel_id, data.query, data.top_k)
        return [
            RagSearchResult(
                id=str(item["id"]),
                content=str(item.get("content") or "")[:500],
                metadata=item.get("metadata") or {},
                similarity=float(item.get("similarity") or 0.0),
            )
            for item in results
        ]

    stmt = (
        select(RagChunk)
        .where(RagChunk.content.ilike(f"%{data.query}%"))
        .limit(data.top_k)
    )
    result = await db.execute(stmt)
    chunks = result.scalars().all()
    return [
        RagSearchResult(
            id=str(chunk.id),
            content=chunk.content[:500],
            metadata=chunk.metadata_json,
            similarity=0.0,
        )
        for chunk in chunks
    ]
