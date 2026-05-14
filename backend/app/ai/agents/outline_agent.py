from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.prompts.outline import OUTLINE_SYSTEM, OUTLINE_USER
from app.ai.utils import ainvoke_with_retry, create_llm
from app.utils.logging import get_logger

logger = get_logger(__name__)


class OutlineAgent:
    def __init__(self):
        self.llm = create_llm(temperature=0.8, max_tokens=4000)

    async def generate(
        self,
        genre: str,
        level: str,
        parent_title: str,
        count: int,
        world_context: str,
        character_context: str,
        existing_outlines: str,
        rag_context: str = "",
        instruction: str = "",
    ) -> list[dict]:
        system_msg = SystemMessage(content=OUTLINE_SYSTEM.format(
            genre=genre,
            world_context=world_context,
            character_context=character_context,
            existing_outlines=existing_outlines,
            rag_context=rag_context,
            count=count,
            level=level,
        ))
        user_msg = HumanMessage(content=OUTLINE_USER.format(
            level=level,
            parent_title=parent_title,
            count=count,
            instruction=instruction,
        ))
        response = await ainvoke_with_retry(self.llm, [system_msg, user_msg])
        result = self._parse_outline_response(str(response.content))
        usage = response.response_metadata.get("token_usage", {})
        logger.info("Outline generation completed", tokens=usage.get("total_tokens", 0), outlines=len(result))
        return result

    def _parse_outline_response(self, content: str) -> list[dict]:
        outlines: list[dict] = []
        current: dict[str, str] = {}
        for raw_line in content.strip().splitlines():
            line = raw_line.strip()
            if not line:
                continue
            is_heading = line.startswith(("#", "-", "*")) or (
                line[0].isdigit() and ("." in line or "、" in line)
            )
            if is_heading:
                if current:
                    outlines.append(current)
                title = line.lstrip("#-* 0123456789.、").strip()
                current = {"title": title, "summary": ""}
            elif current:
                current["summary"] += line + "\n"
        if current:
            outlines.append(current)
        return outlines
