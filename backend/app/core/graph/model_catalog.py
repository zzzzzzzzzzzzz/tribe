"""Model IDs that Tribe permits for each integrated LLM provider.

Model names identify API endpoints; inclusion does not guarantee the upstream
provider exposes every ID to the configured account.
"""

from app.core.graph.gigachat_config import GIGACHAT_MODEL

OPENAI_MODELS: tuple[str, ...] = (
    "gpt-5.2",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-5-nano",
    "gpt-5.1",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "gpt-6-luna",
    "gpt-5.6-luna",
    "gpt-5.6-terra",
    "gpt-5.5",
    "gpt-5.4-mini",
    "gpt-5.4-nano",
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-3.5-turbo",
)


def validate_model_selection(provider: str, model: str) -> None:
    """Reject unsupported models for providers with explicit allowlists."""
    if provider == "openai" and model not in OPENAI_MODELS:
        raise ValueError(
            f"Unsupported OpenAI model {model!r}. Choose one of: {', '.join(OPENAI_MODELS)}"
        )
    if provider == "gigachat" and model != GIGACHAT_MODEL:
        raise ValueError(
            f"GigaChat currently supports only {GIGACHAT_MODEL}; got {model!r}"
        )
