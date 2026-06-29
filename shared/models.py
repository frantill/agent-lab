"""Costruzione del modello LLM via OpenRouter (model-agnostic).

Tutti gli agenti del lab costruiscono il modello da qui. Per cambiare provider o
modello basta impostare AGENT_MODEL nel `.env`: il codice degli agenti non cambia.
È questo il layer che ci stacca da un singolo provider (Anthropic/OpenAI).
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

load_dotenv()

DEFAULT_MODEL = "z-ai/glm-4.6"


def build_model(model_name: str | None = None) -> OpenAIChatModel:
    """Ritorna un modello Pydantic AI puntato su OpenRouter.

    Args:
        model_name: slug OpenRouter (es. "deepseek/deepseek-chat"). Se None usa
            la env var AGENT_MODEL, altrimenti DEFAULT_MODEL.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY mancante. Crea il file .env (vedi README) "
            "e inserisci la tua chiave OpenRouter."
        )
    name = model_name or os.environ.get("AGENT_MODEL", DEFAULT_MODEL)
    provider = OpenRouterProvider(api_key=api_key)
    return OpenAIChatModel(name, provider=provider)
