import json
from typing import Any, List
from dotenv import load_dotenv
from datetime import datetime, timezone

from src.linkedin.models.extraction_schemas import BatchJobExtractionResult
from src.linkedin.models.job_card import JobCardRawData

load_dotenv()

from src.common.infra.dependencies import infra_container
from src.common.infra.litellm_provider import (
    DEFAULT_GEMINI_MODELS,
    LiteLLMProvider,
)
from src.common.logger import get_logger

logger = get_logger("linkedin_llm_extractor")

DEFAULT_GEMINI_MODEL = DEFAULT_GEMINI_MODELS[0]

DEFAULT_LINKEDIN_JOB_SYSTEM_PROMPT = """\
You are an expert at extracting structured job listing data from raw text scraped from LinkedIn job board cards.
You will be provided with a JSON array of job card items, where each item has "job_id" and "card_text".

For each item:
2. Extract the job title or role name into "title".
3. Extract the hiring company name into "company_name" (or null if not found).
4. Extract the job location into "location" (e.g. City, Country, or Region, or null).
5. Determine "work_type": exactly one of "Remote", "Hybrid", "On-site", or null if not explicitly indicated.
6. Provide a concise 1-2 sentence role summary in "short_description".
7. Extract salary information if present:
   - "salary_min": numeric value (no currency symbols) or null
   - "salary_max": numeric value (no currency symbols) or null
   - "salary_currency": standard code (e.g. "PHP", "USD") or null
   - "salary_period": "hourly", "monthly", "yearly", or null
8. Extract relative posted time (e.g. "1 hour ago", "3 days ago", "Reposted 2 weeks ago") into "posted_relative_time".
9. Set "is_early_applicant" to true if the card mentions "Be an early applicant" or similar early applicant callout, otherwise false or null.
10. Assign exactly one category to each job:
   - "Engineering & IT": Software, Hardware, Data, Systems, QA, DevOps
   - "Sales & Marketing": Growth, Account Execs, Advertising, Content
   - "Operations & Administration": HR, Office Support, Logistics, Admin
   - "Finance & Legal": Accounting, Corporate, Compliance, Legal
   - "Product & Design": UI/UX, Product Management, Graphic Design
   - "Customer Service": Support, Success, Call Center
   - "Healthcare & Life Sciences"
   - "Trades, Labor & Field Services"
   - "Others" when none of the categories fit.
11. Determine the posted date in UTC ISO-8601 format (e.g. "2023-08-15T14:30:00Z") based on the relative posted time and current date, or null if the date cannot be determined.

Respond ONLY with valid JSON matching the BatchJobExtractionResult schema.
"""


class LinkedInJobLLMExtractor:
    def __init__(
        self,
        prompt_template: str = DEFAULT_LINKEDIN_JOB_SYSTEM_PROMPT,
        models: list[str] | None = None,
        provider: LiteLLMProvider | None = None,
    ):
        self.prompt_template = prompt_template
        self.provider: LiteLLMProvider

        if provider:
            self.provider = provider
        elif models:
            self.provider = LiteLLMProvider(models=models)
        else:
            self.provider = infra_container.litellm_provider

    @property
    def consecutive_failures(self) -> int:
        return self.provider.consecutive_failures

    async def extract_batch(
        self,
        cards: List[JobCardRawData],
    ) -> BatchJobExtractionResult:
        """Call LiteLLM (Gemini) to extract structured job data from a batch of cards.

        :param cards: List of JobCardRawData objects.
        :returns:     BatchJobExtractionResult containing list of ExtractedJobListing.
        """
        if not cards:
            return BatchJobExtractionResult(jobs=[])

        payload_text = json.dumps([card.model_dump() for card in cards], indent=2)

        content: list[dict[str, Any]] = [{"type": "text", "text": payload_text}]

        now_utc = datetime.now(timezone.utc).isoformat()
        content.append({"type": "text", "text": f"Current UTC time: {now_utc}"})

        try:
            response = await self.provider.acompletion(
                messages=[
                    {"role": "system", "content": self.prompt_template},
                    {
                        "role": "user",
                        "content": content,
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "BatchJobExtractionResult",
                        "schema": BatchJobExtractionResult.model_json_schema(),
                        "strict": True,
                    },
                },
            )
        except Exception as e:
            logger.error(f"[LinkedIn LLM] Failed to extract jobs batch: {e}")
            raise e

        raw_json = response.choices[0].message.content  # type: ignore[union-attr]
        if not raw_json:
            raise ValueError("Model returned an empty response or no content.")

        data = json.loads(raw_json)
        return BatchJobExtractionResult.model_validate(data)
