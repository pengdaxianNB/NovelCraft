from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.ai.prompts.writing import WRITING_SYSTEM, get_writing_user_prompt
from app.utils.logging import get_logger

logger = get_logger(__name__)


class WritingAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.9,
            max_tokens=2000,
        )

    async def generate(
        self,
        genre: str,
        tone: str,
        pov: str,
        words_per_chapter: int,
        style_instructions: str,
        outline_summary: str,
        previous_context: str,
        character_context: str,
        rag_context: str,
        on_segment: callable = None,
    ) -> tuple[str, int]:
        system_msg = SystemMessage(content=WRITING_SYSTEM.format(
            genre=genre,
            tone=tone,
            pov=pov,
            words_per_chapter=words_per_chapter,
            style_instructions=style_instructions,
            outline_summary=outline_summary,
            previous_context=previous_context,
            character_context=character_context,
            rag_context=rag_context,
        ))

        stages = ["opening", "development", "climax", "ending"]
        full_text = ""
        total_tokens = 0

        for i, stage in enumerate(stages):
            user_msg = HumanMessage(content=get_writing_user_prompt(stage, full_text))
            response = await self.llm.ainvoke([system_msg, user_msg])
            segment_text = str(response.content)
            full_text += segment_text + "\n\n"
            usage = response.response_metadata.get("token_usage", {})
            total_tokens += usage.get("total_tokens", 0)

            if on_segment:
                await on_segment(stage, segment_text, (i + 1) / len(stages) * 100)

        word_count = len(full_text)
        return full_text.strip(), word_count, total_tokens
