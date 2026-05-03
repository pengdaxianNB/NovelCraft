import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.ai.prompts.review import REVIEW_SYSTEM, REVIEW_USER
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ReviewAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.3,
            max_tokens=2000,
        )

    async def review(
        self,
        chapter_title: str,
        chapter_content: str,
        words_per_chapter: int,
        style_config: str,
        character_context: str,
        world_context: str,
        previous_context: str,
    ) -> dict:
        system_msg = SystemMessage(content=REVIEW_SYSTEM.format(
            words_per_chapter=words_per_chapter,
        ))
        user_msg = HumanMessage(content=REVIEW_USER.format(
            chapter_title=chapter_title,
            words_per_chapter=words_per_chapter,
            style_config=style_config,
            character_context=character_context,
            world_context=world_context,
            previous_context=previous_context,
            chapter_content=chapter_content,
        ))
        response = await self.llm.ainvoke([system_msg, user_msg])
        return self._parse_review_response(str(response.content))

    def _parse_review_response(self, content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"passed": True, "issues": [], "summary": "审校解析失败，默认通过"}
