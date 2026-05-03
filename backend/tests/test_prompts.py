"""Tests for AI prompt templates."""

from app.ai.prompts.outline import OUTLINE_SYSTEM, OUTLINE_USER
from app.ai.prompts.writing import WRITING_SYSTEM, get_writing_user_prompt
from app.ai.prompts.review import REVIEW_SYSTEM, REVIEW_USER


class TestOutlinePrompts:
    def test_system_prompt_contains_genre(self):
        assert "{genre}" in OUTLINE_SYSTEM
        assert "{level}" in OUTLINE_SYSTEM

    def test_user_prompt_contains_placeholders(self):
        assert "{count}" in OUTLINE_USER
        assert "{level}" in OUTLINE_USER
        assert "{genre}" in OUTLINE_USER

    def test_user_prompt_format_fills_placeholders(self):
        formatted = OUTLINE_USER.format(
            genre="玄幻",
            level="chapter",
            parent_title="第一卷",
            count=5,
            world_context="",
            character_context="",
            existing_outlines="",
        )
        assert "玄幻" in formatted
        assert "chapter" in formatted
        assert "5" in formatted
        assert "第一卷" in formatted


class TestWritingPrompts:
    def test_system_prompt_contains_slots(self):
        assert "{genre}" in WRITING_SYSTEM
        assert "{tone}" in WRITING_SYSTEM
        assert "{pov}" in WRITING_SYSTEM
        assert "{words_per_chapter}" in WRITING_SYSTEM

    def test_stage_prompts_exist(self):
        for stage in ("opening", "development", "climax", "ending"):
            prompt = get_writing_user_prompt(stage)
            assert prompt, f"Stage {stage} should return a non-empty prompt"
            assert isinstance(prompt, str)

    def test_unknown_stage_returns_string(self):
        result = get_writing_user_prompt("unknown")
        assert isinstance(result, str)


class TestReviewPrompts:
    def test_system_prompt_has_dimensions(self):
        assert "情节连贯性" in REVIEW_SYSTEM or "plot" in REVIEW_SYSTEM.lower()
        assert "角色一致性" in REVIEW_SYSTEM or "character" in REVIEW_SYSTEM.lower()

    def test_user_prompt_has_placeholders(self):
        assert "{chapter_content}" in REVIEW_USER
        assert "{outline_context}" in REVIEW_USER
        assert "{character_context}" in REVIEW_USER
