from typing import Any
from dotenv import load_dotenv
import litellm

from src.common.logger import get_logger

load_dotenv()

logger = get_logger("litellm_provider")

DEFAULT_GEMINI_MODELS: list[str] = [
    "gemini/gemini-3.1-flash-lite",
    "gemini/gemini-3.5-flash-lite",
    "gemini/gemini-3-flash-preview",
]
DEFAULT_GEMINI_MODEL = DEFAULT_GEMINI_MODELS[0]


class LiteLLMProvider:
    """
    Dedicated provider for asynchronous LiteLLM completions with model rotation and retry resilience.
    """

    def __init__(self, models: list[str] | None = None):
        self.models: list[str] = list(models) if models else list(DEFAULT_GEMINI_MODELS)
        self.rate_limited_models: set[str] = set()
        self._current_model_idx: int = 0
        self.consecutive_failures: int = 0

    @property
    def available_models(self) -> list[str]:
        """Return the list of models that have not been rate limited."""
        return [m for m in self.models if m not in self.rate_limited_models]

    def _get_next_model(self) -> str:
        """Select the next available non-rate-limited model and advance the rotation index."""
        available = self.available_models
        if not available:
            raise RuntimeError("All configured models are currently rate limited.")
        selected_model = available[self._current_model_idx % len(available)]
        self._current_model_idx = (self._current_model_idx + 1) % len(available)
        return selected_model

    def _is_rate_limit_error(self, exc: Exception) -> bool:
        """Determine whether the encountered exception indicates a 429 / Rate Limit error."""
        if isinstance(exc, litellm.exceptions.RateLimitError):
            return True
        if getattr(exc, "status_code", None) == 429:
            return True
        if "429" in str(exc):
            return True
        return False

    async def acompletion(
        self,
        messages: list[dict],
        response_format: dict | None = None,
        max_retries: int = 3,
        **kwargs: Any,
    ):
        """
        Execute litellm.acompletion with model rotation and retry resilience.

        Retries with alternating models up to `max_retries` times upon failure.
        Maintains consecutive failure count in `self.consecutive_failures`,
        resetting it to 0 on any successful completion.
        If a model returns a 429 / RateLimitError, it is permanently excluded
        from future attempts for the lifetime of this provider instance.
        """
        last_exception: Exception | None = None

        for attempt in range(1, max_retries + 1):
            if not self.available_models:
                logger.error("[LLM completion] All models are rate limited.")
                if last_exception:
                    raise last_exception
                raise RuntimeError("All configured models are currently rate limited.")

            chosen_model = self._get_next_model()
            logger.debug(
                f"[LLM completion] Attempt {attempt}/{max_retries} using model '{chosen_model}'."
            )
            try:
                response = await litellm.acompletion(
                    model=chosen_model,
                    messages=messages,
                    response_format=response_format,
                    **kwargs,
                )
                self.consecutive_failures = 0
                return response
            except Exception as e:
                self.consecutive_failures += 1
                last_exception = e
                logger.warning(
                    f"[LLM completion] Attempt {attempt}/{max_retries} failed with model '{chosen_model}': {e}. "
                    f"Total consecutive failures: {self.consecutive_failures}."
                )

                if self._is_rate_limit_error(e):
                    self.rate_limited_models.add(chosen_model)
                    logger.warning(
                        f"[LLM completion] Model '{chosen_model}' hit 429 rate limit. "
                        f"Excluded from future rotations. Remaining available models: {self.available_models}"
                    )
                    if not self.available_models:
                        logger.error(
                            "[LLM completion] All models exhausted due to rate limits."
                        )
                        raise e

        logger.error(
            f"[LLM completion] All {max_retries} attempts failed. Consecutive failures: {self.consecutive_failures}."
        )
        if last_exception:
            raise last_exception
        raise RuntimeError("LLM completion failed with unknown error.")
