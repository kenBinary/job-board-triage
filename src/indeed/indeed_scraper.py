import asyncio
import random
from typing import List
from playwright.async_api import BrowserContext

from src.common.infra.browser_context import CamoufoxSingleton
from src.common.logger import format_job_log, get_logger
from src.db.database import SessionLocal
from src.indeed.db import create_indeed_details_bulk, get_indeed_details_by_job_id
from src.indeed.get_jobs import fetch_job
from src.indeed.models.indeed_job_details import IndeedJobDetails
from src.indeed.models.indeed_link import IndeedLink, IndeedParams
from src.indeed.indeed_run_tracker import IndeedRunTracker

logger = get_logger("indeed_scraper")

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

    context = await CamoufoxSingleton.get_context()
    assert isinstance(context, BrowserContext)
    page = await CamoufoxSingleton.get_primary_page()
    try:
        with SessionLocal() as db:
            total_items = len(targets)
            logger.info(f"[Indeed] Scraping {total_items} target link(s)...")
            for index, link in enumerate(targets):
                tracker.set_current_index(index)
                logger.info(
                    f"[Indeed] Target {index + 1}/{total_items}: {link.params.q} ({link.params.l})"
                )
                try:
                    consecutive_skipped = 0
                    for current_page in range(1, link.max_page + 1):
                        if consecutive_skipped >= SKIPPED_JOBS_THRESHOLD:
                            logger.info(
                                f"[Indeed] Skipped jobs threshold of {SKIPPED_JOBS_THRESHOLD} reached. Stopping scraping for this link."
                            )
                            break

                        current_link = link.get_next_page(current_page)
                        logger.debug(f"[Indeed] Scraping link: {current_link}")
                        await page.goto(current_link, wait_until="domcontentloaded")

                        page_title = await page.title()
                        if "security check" in page_title.lower():
                            logger.warning(
                                f"[Indeed] Security check detected: {page_title}"
                            )
                            input(
                                "Solve any CAPTCHA or log in if required, then press Enter here..."
                            )

                        indeed_response = await fetch_job(page)

                        indeed_job_details: List[IndeedJobDetails] = []
                        saved_count = 0
                        skipped_count = 0
                        if indeed_response:
                            total_cards = len(indeed_response.job_cards)
                            for card_idx, job in enumerate(
                                indeed_response.job_cards, 1
                            ):
                                existing_job_details = get_indeed_details_by_job_id(
                                    db, job.jobkey if job.jobkey else ""
                                )
                                if existing_job_details:
                                    skipped_count += 1
                                    consecutive_skipped += 1
                                    logger.debug(
                                        f"[Indeed] [SKIP] Job {job.jobkey} ({job.title}) already in DB"
                                    )
                                    continue

                                indeed_job_detail = IndeedJobDetails.from_api_data(job)
                                if any(
                                    j.job_id == job.jobkey for j in indeed_job_details
                                ):
                                    skipped_count += 1
                                    continue

                                consecutive_skipped = 0
                                indeed_job_details.append(indeed_job_detail)
                                saved_count += 1

                                formatted_job = format_job_log(
                                    board="Indeed",
                                    title=job.title or "Untitled",
                                    company=job.company,
                                    salary=indeed_job_detail.formatted_salary,
                                    location=indeed_job_detail.location,
                                    page_info=f"page {current_page}/{link.max_page}",
                                    item_info=f"{card_idx}/{total_cards}",
                                )
                                logger.debug(formatted_job)

                            if len(indeed_job_details) > 0:
                                create_indeed_details_bulk(db, indeed_job_details)

                            logger.info(
                                f"[Indeed] Target {index + 1}/{total_items} [page {current_page}/{link.max_page}]: "
                                f"Scraped {total_cards} jobs ({saved_count} saved, {skipped_count} skipped)"
                            )
                        else:
                            logger.info(
                                f"[Indeed] Target {index + 1}/{total_items} [page {current_page}/{link.max_page}]: No jobs found"
                            )
                    await asyncio.sleep(random.uniform(10.0, 20.0))
                    tracker.record_success()
                except Exception as e:
                    logger.error(
                        f"[Indeed] Failed target {index + 1}/{total_items} ({link.get_next_page(1)}): {e}"
                    )
                    if tracker.record_link_error(link=link, error=e):
                        break
                    await asyncio.sleep(random.uniform(10.0, 20.0))

            tracker.finalize()
    except Exception as e:
        logger.error(f"[Indeed] Error occurred during scrape run: {e}")
    finally:
        await page.close()


if __name__ == "__main__":
    asyncio.run(scrape_indeed())
