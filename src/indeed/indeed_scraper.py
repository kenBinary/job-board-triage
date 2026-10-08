import asyncio
import random
from typing import List
from playwright.async_api import BrowserContext

from src.common.infra.browser_context import CamoufoxSingleton
from src.db.database import SessionLocal
from src.indeed.db import create_indeed_details_bulk, get_indeed_details_by_job_id
from src.indeed.get_jobs import fetch_job
from src.indeed.models.indeed_job_details import IndeedJobDetails
from src.indeed.models.indeed_link import IndeedLink, IndeedParams
from src.indeed.indeed_run_tracker import IndeedRunTracker

BASE_URL = "https://ph.indeed.com/jobs"


LINKS: List[IndeedLink] = [
    IndeedLink(
        max_page=2,
        base_url=BASE_URL,
        params=IndeedParams(
            q="developer",
            l="Philippines",
            sort="date",
            fromage=7,
            sc="0kf:attr(DSQF7);",
            radius=None,
        ),
    ),
    IndeedLink(
        max_page=2,
        base_url=BASE_URL,
        params=IndeedParams(
            q="software",
            l="Philippines",
            sort="date",
            fromage=7,
            sc="0kf:attr(DSQF7);",
            radius=None,
        ),
    ),
    IndeedLink(
        max_page=2,
        base_url=BASE_URL,
        params=IndeedParams(
            q="c#", l="Cebu City, Cebu", sort="date", fromage=7, radius=25, sc=None
        ),
    ),
    IndeedLink(
        max_page=2,
        base_url=BASE_URL,
        params=IndeedParams(
            q="asp.net", l="Cebu City, Cebu", sort="date", fromage=7, radius=25, sc=None
        ),
    ),
    IndeedLink(
        max_page=2,
        base_url=BASE_URL,
        params=IndeedParams(
            q="engineer",
            l="Philippines",
            sort="date",
            fromage=7,
            sc="0kf:attr(DSQF7);",
            radius=None,
        ),
    ),
    IndeedLink(
        max_page=2,
        base_url=BASE_URL,
        params=IndeedParams(
            q="angular", l="Cebu", sort="date", fromage=7, radius=25, sc=None
        ),
    ),
    IndeedLink(
        max_page=2,
        base_url=BASE_URL,
        params=IndeedParams(
            q="react", l="Cebu", sort="date", fromage=7, radius=25, sc=None
        ),
    ),
    IndeedLink(
        max_page=2,
        base_url=BASE_URL,
        params=IndeedParams(
            q="engineer", l="Cebu", sort="date", fromage=7, radius=25, sc=None
        ),
    ),
    IndeedLink(
        max_page=2,
        base_url=BASE_URL,
        params=IndeedParams(
            q="developer", l="Cebu", sort="date", fromage=7, radius=25, sc=None
        ),
    ),
    IndeedLink(
        max_page=2,
        base_url=BASE_URL,
        params=IndeedParams(
            q="software", l="Cebu", sort="date", fromage=7, radius=25, sc=None
        ),
    ),
    IndeedLink(
        max_page=2,
        base_url=BASE_URL,
        params=IndeedParams(
            q=None,
            l="Cagayan de Oro City, Misamis Oriental",
            sort="date",
            fromage=7,
            radius=25,
            sc=None,
        ),
    ),
]

PROFILE_DIR = "./camoufox_profile"
SKIPPED_JOBS_THRESHOLD = 10


async def scrape_indeed(
    links: list[IndeedLink] | None = None, is_retry: bool = False
) -> None:
    targets = links if links is not None else LINKS
    tracker = IndeedRunTracker(links=targets, is_retry_run=is_retry)

    try:
        context = await CamoufoxSingleton.get_context()
        assert isinstance(context, BrowserContext)
        page = await CamoufoxSingleton.get_primary_page()

        with SessionLocal() as db:
            total_items = len(targets)
            for index, link in enumerate(targets):
                tracker.set_current_index(index)
                print(f"Scraping Indeed target {index + 1} of {total_items}")
                try:
                    consecutive_skipped = 0
                    for current_page in range(1, link.max_page + 1):
                        if consecutive_skipped >= SKIPPED_JOBS_THRESHOLD:
                            print(
                                f"Skipped jobs threshold of {SKIPPED_JOBS_THRESHOLD} reached. Stopping scraping for this link."
                            )
                            break

                        current_link = link.get_next_page(current_page)
                        print(f"Scraping Indeed link: {current_link}")
                        await page.goto(current_link, wait_until="domcontentloaded")

                        page_title = await page.title()
                        if "security check" in page_title.lower():
                            print(f"Page title: {page_title}")
                            input(
                                "Solve any CAPTCHA or log in if required, then press Enter here..."
                            )

                        print("-" * 50)
                        indeed_response = await fetch_job(page)
                        print("-" * 50)

                        indeed_job_details: List[IndeedJobDetails] = []
                        if indeed_response:
                            for job in indeed_response.job_cards:
                                existing_job_details = get_indeed_details_by_job_id(
                                    db, job.jobkey if job.jobkey else ""
                                )
                                if existing_job_details:
                                    print(
                                        f"Job with ID {job.jobkey} already exists in the database. Skipping."
                                    )
                                    print("-" * 50)
                                    consecutive_skipped += 1
                                    continue

                                indeed_job_detail = IndeedJobDetails.from_api_data(job)
                                if any(
                                    j.job_id == job.jobkey for j in indeed_job_details
                                ):
                                    continue

                                consecutive_skipped = 0
                                indeed_job_details.append(indeed_job_detail)

                                print("-", job.title, "|", job.company)
                                print("-" * 50)

                            if len(indeed_job_details) > 0:
                                create_indeed_details_bulk(db, indeed_job_details)

                            print(
                                f"Saved {len(indeed_job_details)} job cards from {current_link}"
                            )
                        else:
                            print(f"No job cards found for {current_link}")
                    await asyncio.sleep(random.uniform(10.0, 20.0))
                    tracker.record_success()
                except Exception as e:
                    if tracker.record_link_error(link=link, error=e):
                        break
                    await asyncio.sleep(random.uniform(10.0, 20.0))

            tracker.finalize()
    except Exception as e:
        print(f"Error occurred while scraping Indeed: {e}")


if __name__ == "__main__":
    asyncio.run(scrape_indeed())
