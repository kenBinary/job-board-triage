import asyncio
import json
import random
import re

from src.indeed.models.schemas import IndeedSearchResultPayload


async def fetch_job(page) -> IndeedSearchResultPayload | None:
    print("Scraping Page with title: ", await page.title())

    script_text = await page.locator("script#mosaic-data").inner_text()
    pattern = (
        r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]\s*=\s*({.+?});'
    )
    match = re.search(pattern, script_text)

    if match:
        data = json.loads(match.group(1))
        indeed_response = IndeedSearchResultPayload.model_validate(data)

        for job in indeed_response.job_cards:
            print("-", job.title, "|", job.company)
        return indeed_response
    else:
        print("Could not find mosaic-provider-jobcards assignment in #mosaic-data")
        return None
