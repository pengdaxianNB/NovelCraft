import pytest

from app.services.rag_context_service import (
    RagContextBundle,
    RagContextHit,
    format_rag_context,
)


def test_format_rag_context_groups_hits_by_source():
    bundle = RagContextBundle(
        query="dragon sect",
        hits=[
            RagContextHit(source="knowledge", title="notes.txt", content="The sect uses jade tokens."),
            RagContextHit(source="world", title="Cultivation ranks", content="Foundation comes before Core."),
        ],
        timings_ms={"knowledge_search": 12.5},
    )

    formatted = format_rag_context(bundle)

    assert "## knowledge" in formatted
    assert "[notes.txt]" in formatted
    assert "The sect uses jade tokens." in formatted
    assert "## world" in formatted
    assert "[Cultivation ranks]" in formatted


def test_format_rag_context_returns_empty_string_without_hits():
    bundle = RagContextBundle(query="anything")

    assert format_rag_context(bundle) == ""


@pytest.mark.asyncio
async def test_async_rag_context_degrades_when_knowledge_search_fails(monkeypatch):
    from app.services.rag_context_service import AsyncRagContextService

    class FakeDb:
        async def execute(self, *_args, **_kwargs):
            raise AssertionError("project material queries should be skipped after setup")

    async def fail_search(*_args, **_kwargs):
        raise RuntimeError("embedding unavailable")

    monkeypatch.setattr("app.services.rag_context_service.hybrid_search", fail_search)

    service = AsyncRagContextService(FakeDb())
    bundle = await service.build_review_context(
        novel_id="550e8400-e29b-41d4-a716-446655440000",
        chapter_content="A quiet chapter about jade tokens.",
        chapter_number=1,
        include_project_materials=False,
    )

    assert bundle.hits == []
    assert bundle.warnings
    assert "embedding unavailable" in bundle.warnings[0]
