import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.ai.prompts.outline import OUTLINE_SYSTEM, OUTLINE_USER
from app.utils.logging import get_logger

logger = get_logger(__name__)


class OutlineAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.8,
            max_tokens=4000,
        )

    async def generate(
        self,
        genre: str,
        level: str,
        parent_title: str,
        count: int,
        world_context: str,
        character_context: str,
        existing_outlines: str,
        instruction: str = "",
    ) -> list[dict]:
        system_msg = SystemMessage(content=OUTLINE_SYSTEM.format(
            genre=genre,
            world_context=world_context,
            character_context=character_context,
            existing_outlines=existing_outlines,
            count=count,
            level=level,
        ))
        user_msg = HumanMessage(content=OUTLINE_USER.format(
            level=level,
            parent_title=parent_title,
            count=count,
            instruction=instruction,
        ))
        response = await self.llm.ainvoke([system_msg, user_msg])
        return self._parse_outline_response(str(response.content))

    def _parse_outline_response(self, content: str) -> list[dict]:
        outlines = []
        lines = content.strip().split("\n")
        current = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith(("#", "##", "###")) or (line[0].isdigit() and ("." in line or "、" in line)):
                if current:
                    outlines.append(current)
                current = {"title": line.lstrip("#0123456789. 、"), "summary": ""}
            elif current:
                current["summary"] += line + "\n"
        if current:
            outlines.append(current)
        return outlines
