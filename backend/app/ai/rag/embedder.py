from langchain_openai import OpenAIEmbeddings
from app.config import settings

_embedder: OpenAIEmbeddings | None = None


def get_embedder() -> OpenAIEmbeddings:
    global _embedder
    if _embedder is None:
        kwargs = dict(
            model=settings.openai_embedding_model,
            openai_api_key=settings.openai_api_key,
        )
        if settings.openai_base_url:
            kwargs["openai_api_base"] = settings.openai_base_url
        _embedder = OpenAIEmbeddings(**kwargs)
    return _embedder


async def embed_texts(texts: list[str]) -> list[list[float]]:
    return await get_embedder().aembed_documents(texts)


async def embed_query(text: str) -> list[float]:
    return await get_embedder().aembed_query(text)


def embed_query_sync(text: str) -> list[float]:
    return get_embedder().embed_query(text)
