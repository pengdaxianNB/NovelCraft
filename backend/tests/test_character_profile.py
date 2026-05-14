from app.tasks.generation_tasks import merge_character_profile


def test_merge_character_profile_preserves_existing_and_adds_history():
    profile = {"personality": "calm", "abilities": "sword"}
    extracted = {
        "profile": {"personality": "reckless", "relationships": "trusts Lin"},
        "evidence": "He protected Lin in the alley.",
    }

    result = merge_character_profile(profile, extracted, chapter_number=3)

    assert result["personality"] == "calm"
    assert result["relationships"] == "trusts Lin"
    assert result["appearances"][0]["chapter_number"] == 3
    assert "protected Lin" in result["appearances"][0]["evidence"]
