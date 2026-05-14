import asyncio
from itertools import cycle
from typing import Any

from langchain_core.caches import InMemoryCache
from langchain_core.globals import set_llm_cache
from langchain_openai import ChatOpenAI

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

MAX_RETRIES = 3
BASE_DELAY = 1.0

_key_cycle = cycle(settings.openai_api_keys or [settings.openai_api_key])


def create_llm(
    temperature: float = 0.7,
    max_tokens: int = 2000,
    model: str | None = None,
) -> ChatOpenAI:
    kwargs: dict[str, Any] = dict(
        model=model or settings.openai_model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    keys = settings.openai_api_keys
    kwargs["openai_api_key"] = next(_key_cycle) if keys else settings.openai_api_key
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return ChatOpenAI(**kwargs)


async def ainvoke_with_retry(
    llm: Any,
    messages: list[Any],
    max_retries: int = MAX_RETRIES,
    base_delay: float = BASE_DELAY,
) -> Any:
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return await llm.ainvoke(messages)
        except Exception as exc:
            last_exc = exc
            if attempt == max_retries:
                break
            delay = base_delay * (2 ** attempt)
            logger.warning(
                "LLM call failed, retrying",
                attempt=attempt + 1,
                max_retries=max_retries,
                delay=delay,
                error=str(exc),
            )
            await asyncio.sleep(delay)

    fallback_model = settings.openai_fallback_model
    if fallback_model:
        logger.warning(
            "Primary model exhausted, trying fallback",
            fallback_model=fallback_model,
            error=str(last_exc),
        )
        fallback_llm = create_llm(
            temperature=getattr(llm, "temperature", 0.7),
            max_tokens=getattr(llm, "max_tokens", 2000),
            model=fallback_model,
        )
        return await fallback_llm.ainvoke(messages)

    raise last_exc  # type: ignore[misc]


MAX_PROMPT_CHARS = 12000


def trim_context(*contexts: str, max_chars: int = MAX_PROMPT_CHARS) -> str:
    parts = [c for c in contexts if c.strip()]
    combined = "\n\n".join(parts)
    if len(combined) <= max_chars:
        return combined
    ratio = max_chars / len(combined)
    trimmed = []
    for ctx in parts:
        budget = max(200, int(len(ctx) * ratio))
        if len(ctx) > budget:
            trimmed.append(ctx[:budget] + "\n...")
        else:
            trimmed.append(ctx)
    return "\n\n".join(trimmed)


def init_llm_cache() -> None:
    if settings.llm_cache_enabled:
        set_llm_cache(InMemoryCache())
        logger.info("LLM cache enabled (in-memory)")
    else:
        logger.info("LLM cache disabled")
