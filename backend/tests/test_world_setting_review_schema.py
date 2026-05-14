from app.schemas.world_setting import WorldSettingConsistencyResponse


def test_world_setting_consistency_response_has_rag_metadata():
    response = WorldSettingConsistencyResponse(
        passed=False,
        issues=[{"severity": "high", "description": "Conflicts with chapter 2."}],
        summary="Needs review",
        rag_hits=[{"source": "chapter", "title": "Chapter 2"}],
        timings_ms={"rag_retrieval": 11.4},
    )

    assert response.issues[0]["severity"] == "high"
    assert response.rag_hits[0]["source"] == "chapter"
