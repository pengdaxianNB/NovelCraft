from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.ai.prompts.writing import WRITING_SYSTEM, get_writing_user_prompt
from app.ai.utils import ainvoke_with_retry, create_llm, trim_context
from app.utils.logging import get_logger

logger = get_logger(__name__)

STAGE_RATIOS = {"opening": 0.20, "development": 0.35, "climax": 0.25, "ending": 0.20}


class WritingAgent:
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
        description: str = "",
        on_segment: callable = None,
        resume_from: dict | None = None,
    ) -> tuple[str, int, int]:
        per_stage_max_tokens = max(1000, int(words_per_chapter * 0.42))

        combined_context = trim_context(character_context, rag_context, previous_context)

        system_msg = SystemMessage(content=WRITING_SYSTEM.format(
            genre=genre,
            tone=tone,
            pov=pov,
            words_per_chapter=words_per_chapter,
            style_instructions=style_instructions,
            outline_summary=outline_summary,
            previous_context=previous_context,
            character_context=character_context,
            rag_context=combined_context if combined_context else rag_context,
            user_description=description,
        ))

        stages = ["opening", "development", "climax", "ending"]
        full_text = ""
        total_tokens = 0
        start_stage_idx = 0

        if resume_from and resume_from.get("completed_stages"):
            done = resume_from["completed_stages"]
            full_text = resume_from.get("full_text", "")
            total_tokens = resume_from.get("total_tokens", 0)
            start_stage_idx = len(done)
            logger.info("Resuming from checkpoint",
                completed_stages=done,
                current_chars=len(full_text),
                start_stage_idx=start_stage_idx,
            )
            for s in done:
                if on_segment:
                    si = stages.index(s)
                    await on_segment(s, "", (si + 1) / len(stages) * 100)

        for i in range(start_stage_idx, len(stages)):
            stage = stages[i]
            chars_written = len(full_text)
            remaining_stages = stages[i + 1:]
            remaining_ratio = sum(STAGE_RATIOS[s] for s in remaining_stages)
            remaining_budget = int(words_per_chapter * remaining_ratio) if remaining_stages else 0
            stage_target = max(100, words_per_chapter - chars_written - remaining_budget)

            llm = self._make_llm(per_stage_max_tokens)
            user_msg = HumanMessage(content=get_writing_user_prompt(
                stage=stage,
                previous_text=full_text,
                total_target=words_per_chapter,
                chars_written=chars_written,
                remaining_budget=remaining_budget,
                stage_target=stage_target,
            ))
            response = await ainvoke_with_retry(llm, [system_msg, user_msg])
            segment_text = str(response.content)
            full_text += segment_text + "\n\n"
            usage = response.response_metadata.get("token_usage", {})
            total_tokens += usage.get("total_tokens", 0)

            logger.info("Stage completed",
                stage=stage,
                stage_chars=len(segment_text),
                total_chars=len(full_text),
                target=words_per_chapter,
            )

            if on_segment:
                await on_segment(stage, segment_text, (i + 1) / len(stages) * 100)

        word_count = len(full_text)

        deviation = abs(word_count - words_per_chapter) / max(words_per_chapter, 1)
        if deviation > 0.15:
            full_text, word_count, extra_tokens = await self._adjust_length(
                full_text, word_count, words_per_chapter, per_stage_max_tokens
            )
            total_tokens += extra_tokens

        logger.info("Chapter generation complete",
            final_chars=word_count,
            target=words_per_chapter,
            deviation_pct=f"{deviation * 100:.1f}%",
            total_tokens=total_tokens,
        )

        return full_text.strip(), word_count, total_tokens

    async def _adjust_length(
        self, text: str, current_count: int, target: int, max_tokens: int
    ) -> tuple[str, int, int]:
        llm = self._make_llm(max_tokens)
        if current_count > target:
            to_cut = current_count - target
            prompt = (
                f"以下章节正文共{current_count}字，超出目标{target}字约{to_cut}字。"
                f"请精简冗余描写和对话，压缩至{target}字左右，保持情节完整。\n\n"
                f"正文：\n{text[-3000:]}"
            )
        else:
            to_add = target - current_count
            prompt = (
                f"以下章节正文共{current_count}字，距目标{target}字还差{to_add}字。"
                f"请适当扩充描写、对话或心理活动，扩展至{target}字左右，保持文风一致。\n\n"
                f"正文：\n{text[-3000:]}"
            )

        response = await ainvoke_with_retry(llm, [HumanMessage(content=prompt)])
        adjusted = str(response.content)
        adjusted_count = len(adjusted)
        extra_tokens = response.response_metadata.get("token_usage", {}).get("total_tokens", 0)

        if abs(adjusted_count - target) > abs(current_count - target):
            return text, current_count, extra_tokens

        return adjusted, adjusted_count, extra_tokens

    def _make_llm(self, max_tokens: int) -> ChatOpenAI:
        return create_llm(temperature=0.9, max_tokens=max_tokens)
