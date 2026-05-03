from __future__ import annotations

from functools import lru_cache

from config import get_settings
from langchain_openai import ChatOpenAI


@lru_cache(maxsize=1)
def get_chat_model() -> ChatOpenAI:
    settings = get_settings()
    api_key = settings.openai_api_key or None

    return ChatOpenAI(
        model=settings.openai_llm_model,
        temperature=0.2,
        api_key=api_key,
        streaming=True,
    )
