import asyncio
import random

from src.common.logger import format_job_log, get_logger
from src.db.database import SessionLocal
from src.olj.db import create_olj_details_bulk, get_olj_details_by_job_id
from src.olj.get_jobs import fetch_jobs
from src.olj.models.olj_job_details import OljJobDetails
from src.olj.models.olj_link import OljLink, OljParams
from src.olj.olj_run_tracker import OljRunTracker

logger = get_logger("olj_scraper")

BASE_URL = "https://www.onlinejobs.ph/jobseekers/jobsearch"

LINKS = [
    OljLink(
        max_page=2,
        base_url=BASE_URL,
        params=OljParams(jobkeyword=jobkeyword),
    )
    for jobkeyword in [
        "engineer",
        "developer",
        "fastapi",
        "asp.net",
        ".net",
        "c#",
        "python",
        "angular",
        "react",
        "typescript",
        "javascript",
        "css",
        "html",
        "programmer",
    ]
]


async def _scrape_link(link: OljLink, target_link: int, total_link: int) -> None:
    for current_page in range(1, link.max_page + 1):
        current_link = link.get_next_page(current_page)
        logger.debug(f"[OnlineJobs] Scraping link: {current_link}")

        result = await fetch_jobs(current_link)
        total_scraped = len(result.jobs)
        saved_count = 0
        skipped_count = 0

        if not result.has_next_page:
            logger.info(
                f"[OnlineJobs] Target {target_link + 1}/{total_link} [page {current_page}/{link.max_page}]: "
                f"Scraped {total_scraped} jobs (no next page)"
            )
            break

        olj_job_details_list: list[OljJobDetails] = []
        for job_idx, job in enumerate(result.jobs, 1):
            with SessionLocal() as db:
                existing_job_details = get_olj_details_by_job_id(db, job.id)

            if existing_job_details:
                skipped_count += 1
                logger.debug(
                    f"[OnlineJobs] [SKIP] Job {job.id} ({job.title}) already in DB"
                )
                continue

            job_details = OljJobDetails.from_api_data(job)
            if any(j.job_id == job.id for j in olj_job_details_list):
                skipped_count += 1
                continue

            olj_job_details_list.append(job_details)
            saved_count += 1

            formatted_job = format_job_log(
                board="OnlineJobs",
                title=job.title or "Untitled",
                company=None,
                salary=job.salary if job.salary else None,
                location=job.job_type if job.job_type else None,
                page_info=f"page {current_page}/{link.max_page}",
                item_info=f"{job_idx}/{total_scraped}",
            )
            logger.debug(formatted_job)

        if olj_job_details_list:
            with SessionLocal() as db:
                create_olj_details_bulk(db, olj_job_details_list)
                olj_job_details_list.clear()

        logger.info(
            f"[OnlineJobs] Target {target_link + 1}/{total_link} [page {current_page}/{link.max_page}]: "
            f"Scraped {total_scraped} jobs ({saved_count} saved, {skipped_count} skipped)"
        )

        if current_page < link.max_page:
            await asyncio.sleep(random.uniform(3.5, 5.0))


async def scrape_olj(
    links: list[OljLink] | None = None, is_retry: bool = False
) -> None:
    targets = links if links is not None else LINKS
    tracker = OljRunTracker(links=targets, is_retry_run=is_retry)

    try:
        total_items = len(targets)
        logger.info(f"[OnlineJobs] Scraping {total_items} target link(s)...")
        for index, link in enumerate(targets):
            tracker.set_current_index(index)
            logger.info(
                f"[OnlineJobs] Target {index + 1}/{total_items}: keyword='{link.params.jobkeyword}'"
            )
            try:
                await _scrape_link(link, target_link=index, total_link=total_items)
                tracker.record_success()
            except Exception as e:
                logger.error(
                    f"[OnlineJobs] Failed target {index + 1}/{total_items} ({link.get_next_page(1)}): {e}"
                )
                if tracker.record_link_error(link=link, error=e):
                    break

        tracker.finalize()

    except Exception as e:
        logger.error(f"[OnlineJobs] Error occurred during scrape run: {e}")


if __name__ == "__main__":
    asyncio.run(scrape_olj())
