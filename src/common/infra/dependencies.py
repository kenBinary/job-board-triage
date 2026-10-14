from src.common.infra.litellm_provider import LiteLLMProvider


class InfraContainer:
    """Container holding infrastructure dependencies and singletons."""

    def __init__(self, litellm_provider: LiteLLMProvider | None = None):
        self.litellm_provider: LiteLLMProvider = litellm_provider or LiteLLMProvider()


infra_container = InfraContainer()
