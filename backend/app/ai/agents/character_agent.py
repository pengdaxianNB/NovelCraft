import json
from langchain_core.messages import SystemMessage, HumanMessage
from app.ai.prompts.character import CHARACTER_SYSTEM, CHARACTER_USER
from app.ai.utils import ainvoke_with_retry, create_llm
from app.utils.logging import get_logger

logger = get_logger(__name__)


class CharacterAgent:
    def __init__(self):
        self.llm = create_llm(temperature=0.3, max_tokens=2000)

    async def extract(
        self,
        chapter_content: str,
        existing_characters: list[str],
        rag_context: str = "",
    ) -> list[dict]:
        truncated = chapter_content[:8000] if len(chapter_content) > 8000 else chapter_content
        existing_list = "\n".join(f"- {name}" for name in existing_characters) if existing_characters else "（暂无已有角色）"

        system_msg = SystemMessage(content=CHARACTER_SYSTEM)
        user_msg = HumanMessage(content=CHARACTER_USER.format(
            existing_characters=existing_list,
            rag_context=rag_context,
            chapter_content=truncated,
        ))
        response = await ainvoke_with_retry(self.llm, [system_msg, user_msg])
        result = self._parse_extraction_response(str(response.content))
        usage = response.response_metadata.get("token_usage", {})
        tokens = usage.get("total_tokens", 0)
        logger.info("Character extraction completed", tokens=tokens, extracted=len(result))
        return result

    def _parse_extraction_response(self, content: str) -> list[dict]:
        try:
            text = content.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
            result = json.loads(text)
            if isinstance(result, list):
                return result
            return []
        except (json.JSONDecodeError, TypeError):
            logger.warning("Failed to parse character extraction response", raw=content[:200])
            return []
