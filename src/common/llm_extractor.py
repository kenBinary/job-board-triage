from abc import ABC, abstractmethod


class BaseLLMExtractor[T](ABC):
    def __init__(self, prompt_template: str):
        self.prompt_template = prompt_template

    @abstractmethod
    async def extract_jobs_from_post(self, text: str, image_data_urls: list[str]) -> T:
        pass
