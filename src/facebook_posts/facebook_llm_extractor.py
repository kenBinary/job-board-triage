import json
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from src.common.infra.dependencies import infra_container
from src.common.infra.litellm_provider import (
    DEFAULT_GEMINI_MODELS,
    LiteLLMProvider,
)
from src.common.llm_extractor import BaseLLMExtractor
from src.common.logger import get_logger
from .models.extraction_schemas import PostJobExtractionResult

logger = get_logger("facebook_llm_extractor")

DEFAULT_GEMINI_MODEL = DEFAULT_GEMINI_MODELS[0]

DEFAULT_FACEBOOK_SYSTEM_PROMPT = """\
You are an expert at extracting structured job posting information from Facebook posts.
Given post text and optionally one or more images, determine whether the post is a job advertisement.

Rules:
- If the post is NOT advertising a job opening, return is_job_post=false and an empty jobs list.
- If the post IS a job posting, extract all job openings described in it.
  A single post may advertise multiple roles — return one entry per distinct role.
- Extract salary information as numeric values with currency and period when available.
- work_type must be exactly one of: "Remote", "Hybrid", "On-site", or null.
- For short_description, write a concise 1-2 sentence summary of the role.
- For description, include all responsibilities, qualifications, and requirements.
- Extract any contact email or application link if explicitly mentioned.
- Extract the post date shown on the Facebook card screenshot as posted_date_utc.
  Convert absolute and relative dates (for example, "2h" or "Yesterday") to an
  ISO-8601 UTC string. Return null only when the date is unreadable.
- Assign exactly one category to each job:
  - "Engineering & IT": Software, Hardware, Data, Systems
  - "Sales & Marketing": Growth, Account Execs, Advertising
  - "Operations & Administration": HR, Office Support, Logistics
  - "Finance & Legal": Accounting, Corporate, Compliance
  - "Product & Design": UI/UX, Product Management, Creative
  - "Customer Service": Support, Success
  - "Healthcare & Life Sciences"
  - "Trades, Labor & Field Services"
  - "Others" when none of the categories fit.
- Respond ONLY with valid JSON matching the provided schema.
"""


class FacebookLLMExtractor(BaseLLMExtractor[PostJobExtractionResult]):
    def __init__(
        self,
        prompt_template: str,
        models: list[str] | None = None,
        provider: LiteLLMProvider | None = None,
    ):
        super().__init__(prompt_template=prompt_template)
        if provider:
            self.provider = provider
        elif models:
            self.provider = LiteLLMProvider(models=models)
        else:
            self.provider = infra_container.litellm_provider

    @property
    def consecutive_failures(self) -> int:
        return self.provider.consecutive_failures

    async def extract_jobs_from_post(
        self,
        text: str,
        image_data_urls: list[str],
    ) -> PostJobExtractionResult:
        """
        Call LiteLLM (Gemini) to extract structured job data from a Facebook post.

        :param text:            Raw text content scraped from the post card (via innerText).
        :param image_data_urls: List of pre-converted base64 data URLs for any post images / screenshots.
        :returns:               A PostJobExtractionResult with is_job_post flag and jobs list.
        """
        reference_time = datetime.now(timezone.utc).isoformat()
        content: list[dict] = [
            {
                "type": "text",
                "text": (
                    f"{text}\n\n"
                    f"Current UTC time for resolving relative post dates: {reference_time}"
                ),
            }
        ]

        for data_url in image_data_urls:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": data_url},
                }
            )

        try:
            response = await self.provider.acompletion(
                messages=[
                    {"role": "system", "content": self.prompt_template},
                    {"role": "user", "content": content},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "PostJobExtractionResult",
                        "schema": PostJobExtractionResult.model_json_schema(),
                        "strict": True,
                    },
                },
            )
        except Exception as e:
            logger.error(f"[LLM extraction] Failed to extract jobs from post: {e}")
            raise e

        raw_json = response.choices[0].message.content  # type: ignore[union-attr]
        if not raw_json:
            raise ValueError("Model returned an empty response or no content.")

        data = json.loads(raw_json)
        return PostJobExtractionResult.model_validate(data)
