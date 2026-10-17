from src.common.infra.camofoux_provider import CamofouxProvider
from src.common.infra.litellm_provider import LiteLLMProvider


class InfraContainer:
    """Container holding infrastructure dependencies and singletons."""

    def __init__(
        self,
        litellm_provider: LiteLLMProvider | None = None,
        camoufox_provider: CamofouxProvider | None = None,
    ):
        self.litellm_provider: LiteLLMProvider = litellm_provider or LiteLLMProvider()
        self.camoufox_provider: CamofouxProvider = (
            camoufox_provider or CamofouxProvider()
        )


infra_container = InfraContainer()
