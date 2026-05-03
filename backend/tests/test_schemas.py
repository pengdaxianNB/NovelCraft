"""Tests for Pydantic schemas — validation, defaults, and edge cases."""

import pytest
from pydantic import ValidationError
from app.schemas.novel import NovelCreate, NovelUpdate, NovelStyleUpdate, StyleConfig, ScheduleConfig
from app.schemas.outline import OutlineCreate, OutlineResponse, OutlineUpdate
from app.schemas.character import CharacterCreate
from app.schemas.world_setting import WorldSettingCreate
from app.schemas.generation import GenerateOutlineRequest, GenerateChapterRequest
from app.schemas.rag import RagSearchRequest


class TestStyleConfig:
    def test_defaults(self):
        cfg = StyleConfig()
        assert cfg.tone == "热血"
        assert cfg.pov == "第三人称"
        assert cfg.words_per_chapter == 3000
        assert cfg.custom_instructions == ""

    def test_custom_values(self):
        cfg = StyleConfig(tone="轻松", pov="第一人称", words_per_chapter=2000)
        assert cfg.tone == "轻松"
        assert cfg.pov == "第一人称"
        assert cfg.words_per_chapter == 2000


class TestNovelCreate:
    def test_minimal_fields(self):
        data = NovelCreate(title="测试小说")
        assert data.title == "测试小说"
        assert data.genre == "玄幻"
        assert data.synopsis is None
        assert data.style_config.tone == "热血"
        assert data.schedule_config.enabled is False

    def test_full_fields(self):
        data = NovelCreate(
            title="星辰变",
            genre="仙侠",
            synopsis="一个少年崛起的故事",
            style_config=StyleConfig(tone="热血", pov="第三人称", words_per_chapter=4000),
            schedule_config=ScheduleConfig(enabled=True, cron="0 */6 * * *"),
        )
        assert data.title == "星辰变"
        assert data.genre == "仙侠"
        assert data.style_config.words_per_chapter == 4000
        assert data.schedule_config.enabled is True
        assert data.schedule_config.cron == "0 */6 * * *"

    def test_title_too_long(self):
        with pytest.raises(ValidationError):
            NovelCreate(title="x" * 201)

    def test_empty_title(self):
        with pytest.raises(ValidationError):
            NovelCreate(title="")


class TestNovelUpdate:
    def test_partial_update(self):
        data = NovelUpdate(title="新书名")
        assert data.title == "新书名"
        assert data.genre is None
        assert data.synopsis is None

    def test_empty_update(self):
        data = NovelUpdate()
        assert data.title is None
        assert data.genre is None

    def test_status_update(self):
        data = NovelUpdate(status="writing")
        assert data.status == "writing"


class TestNovelStyleUpdate:
    def test_partial_style_update(self):
        data = NovelStyleUpdate(tone="轻松")
        assert data.tone == "轻松"
        assert data.pov is None
        assert data.words_per_chapter is None

    def test_full_style_update(self):
        data = NovelStyleUpdate(
            tone="黑暗",
            pov="第一人称",
            words_per_chapter=5000,
            custom_instructions="每章结尾留有悬念",
        )
        assert data.tone == "黑暗"
        assert data.words_per_chapter == 5000
        assert data.custom_instructions == "每章结尾留有悬念"


class TestOutlineCreate:
    def test_create_with_required_fields(self):
        data = OutlineCreate(title="大结局", level="chapter", sequence=10)
        assert data.title == "大结局"
        assert data.level == "chapter"
        assert data.sequence == 10
        assert data.parent_id is None
        assert data.summary is None

    def test_create_with_parent(self):
        data = OutlineCreate(
            title="第三章",
            level="chapter",
            sequence=3,
            parent_id="550e8400-e29b-41d4-a716-446655440000",
        )
        assert data.parent_id == "550e8400-e29b-41d4-a716-446655440000"


class TestOutlineResponse:
    def test_with_children(self):
        child = OutlineResponse(
            id="2",
            novel_id="1",
            level="chapter",
            parent_id="1",
            sequence=1,
            title="第一章",
            summary="开始",
            status="draft",
            children=[],
        )
        parent = OutlineResponse(
            id="1",
            novel_id="1",
            level="volume",
            parent_id=None,
            sequence=0,
            title="第一卷",
            summary="起源",
            status="draft",
            children=[child],
        )
        assert len(parent.children) == 1
        assert parent.children[0].title == "第一章"


class TestCharacterCreate:
    def test_minimal(self):
        data = CharacterCreate(name="萧炎")
        assert data.name == "萧炎"
        assert data.role == "配角"
        assert data.description is None

    def test_full(self):
        data = CharacterCreate(
            name="林动",
            role="主角",
            description="青阳镇少年",
            profile={"age": 18, "level": "练气期"},
        )
        assert data.role == "主角"
        assert data.profile == {"age": 18, "level": "练气期"}


class TestWorldSettingCreate:
    def test_create(self):
        data = WorldSettingCreate(
            name="斗气大陆",
            category="地域",
            description="以斗气为尊的世界",
        )
        assert data.name == "斗气大陆"
        assert data.category == "地域"
        assert data.description == "以斗气为尊的世界"


class TestGenerateRequests:
    def test_generate_outline(self):
        req = GenerateOutlineRequest(novel_id="abc", level="chapter", count=5)
        assert req.level == "chapter"
        assert req.count == 5
        assert req.parent_id is None

    def test_generate_chapter(self):
        req = GenerateChapterRequest(
            novel_id="abc",
            outline_id="def",
            chapter_number=3,
            words_override=4000,
        )
        assert req.chapter_number == 3
        assert req.words_override == 4000

    def test_generate_chapter_defaults(self):
        req = GenerateChapterRequest(novel_id="abc")
        assert req.words_override is None


class TestRagSearchRequest:
    def test_search(self):
        req = RagSearchRequest(novel_id="abc", query="斗气", top_k=10)
        assert req.query == "斗气"
        assert req.top_k == 10

    def test_default_top_k(self):
        req = RagSearchRequest(novel_id="abc", query="修炼")
        assert req.top_k == 5
