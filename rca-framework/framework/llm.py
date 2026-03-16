import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter

load_dotenv(Path(__file__).parent.parent / ".env")

_SENTINEL_KEY = "your-openrouter-api-key-here"


def get_llm() -> ChatOpenRouter:
    """Construct a ChatOpenRouter instance from environment variables.

    Required .env keys:
        OPENROUTER_API_KEY  — your OpenRouter API key
        LLM_MODEL           — provider/model string, e.g. openai/gpt-4.1
    """
    model = os.environ.get("LLM_MODEL")
    if not model:
        raise RuntimeError(
            "LLM_MODEL is not set. Add it to your .env file (e.g. LLM_MODEL=openai/gpt-4.1)."
        )

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key or api_key == _SENTINEL_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. "
            "Copy .env.example to .env and fill in your key."
        )

    return ChatOpenRouter(model=model)
