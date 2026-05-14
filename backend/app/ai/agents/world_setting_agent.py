import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.prompts.world_setting import WORLD_SETTING_SYSTEM, WORLD_SETTING_USER
from app.ai.utils import ainvoke_with_retry, create_llm
from app.utils.logging import get_logger

logger = get_logger(__name__)


class WorldSettingAgent:
    def __init__(self):
        self.llm = create_llm(temperature=0.2, max_tokens=1600)

    async def check_consistency(
        self,
        category: str,
        title: str,
        content: str,
        rag_context: str,
    ) -> dict:
        response = await ainvoke_with_retry(self.llm, [
            SystemMessage(content=WORLD_SETTING_SYSTEM),
            HumanMessage(content=WORLD_SETTING_USER.format(
                category=category,
                title=title,
                content=content,
                rag_context=rag_context,
            )),
        ])
        result = self._parse_response(str(response.content))
        usage = response.response_metadata.get("token_usage", {})
        result["tokens_used"] = usage.get("total_tokens", 0)
        logger.info("World setting check completed", tokens=result["tokens_used"])
        return result

    def _parse_response(self, content: str) -> dict:
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
        logger.warning("WorldSettingAgent JSON parse failed, defaulting to not passed")
        return {"passed": False, "issues": [{"type": "parse_error", "detail": "LLM output could not be parsed as valid JSON"}], "summary": "Consistency response parsing failed; defaulted to not passed."}
