import asyncio
import json
import base64
import random
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

import litellm

from src.common.logger import get_logger
from .models.extraction_schemas import (
    PostJobExtractionResult,
)

logger = get_logger("linkedin_llm_extractor")

GEMINI_MODEL = "gemini/gemini-3.5-flash-lite"

SYSTEM_PROMPT = """\
You are an expert at extracting structured job posting information from LinkedIn posts.
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


def _fetch_image_as_data_url(url: str) -> Optional[str]:
    """Download an image and return it as a base64 data URL."""
    try:
        import urllib.request

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            content_type = response.headers.get("Content-Type", "image/jpeg").split(
                ";"
            )[0]
            raw = response.read()
            encoded = base64.b64encode(raw).decode("utf-8")
            return f"data:{content_type};base64,{encoded}"
    except Exception as e:
        logger.warning(f"  [image] Failed to fetch {url[:80]}...: {e}")
        return None


async def extract_jobs_from_post(
    text: str,
    image_urls: list[str],
) -> PostJobExtractionResult:
    """
    Call LiteLLM (Gemini) to extract structured job data from a LinkedIn post.

    :param text:       Raw text content scraped from the post element.
    :param image_urls: List of resolved image URLs (srcset-selected or src fallback).
    :returns:          A PostJobExtractionResult with is_job_post flag and jobs list.
    """
    content: list[dict] = [{"type": "text", "text": text}]

    for url in image_urls:
        data_url = _fetch_image_as_data_url(url)
        await asyncio.sleep(random.uniform(1.0, 3.5))
        if data_url:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": data_url},
                }
            )

    response = litellm.completion(
        model=GEMINI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
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

    raw_json = response.choices[0].message.content  # type: ignore[union-attr]
    if not raw_json:
        raise ValueError("Model returned an empty response or no content.")

    data = json.loads(raw_json)
    return PostJobExtractionResult.model_validate(data)
