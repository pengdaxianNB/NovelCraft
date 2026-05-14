import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.prompts.review import REVIEW_SYSTEM, REVIEW_USER
from app.ai.utils import ainvoke_with_retry, create_llm
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ReviewAgent:
    def __init__(self):
        self.llm = create_llm(temperature=0.3, max_tokens=2000)

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
        response = await ainvoke_with_retry(self.llm, [system_msg, user_msg])
        result = self._parse_review_response(str(response.content))
        usage = response.response_metadata.get("token_usage", {})
        result["tokens_used"] = usage.get("total_tokens", 0)
        logger.info("Review completed", tokens=result["tokens_used"], passed=result.get("passed"))
        return result

    def _parse_review_response(self, content: str) -> dict:
        try:
            text = content.strip()
            if text.startswith("```"):
                lines = text.splitlines()
                text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
            result = json.loads(text)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
        logger.warning("ReviewAgent JSON parse failed, defaulting to not passed")
        return {"passed": False, "issues": [{"type": "parse_error", "detail": "LLM output could not be parsed as valid JSON"}], "summary": "Review response parsing failed; defaulted to not passed."}
