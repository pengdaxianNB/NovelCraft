from app.schemas.chapter import ChapterReviewRequest, ChapterReviewResponse


def test_chapter_review_request_content_is_optional():
    req = ChapterReviewRequest()

    assert req.content is None


def test_chapter_review_response_contains_rag_metadata():
    res = ChapterReviewResponse(
        passed=False,
        issues=[{"dimension": "continuity", "severity": "high"}],
        summary="Needs fixes",
        rag_hits=[{"source": "world", "title": "Ranks"}],
        timings_ms={"rag_retrieval": 10.2},
    )

    assert res.rag_hits[0]["source"] == "world"
    assert res.timings_ms["rag_retrieval"] == 10.2
