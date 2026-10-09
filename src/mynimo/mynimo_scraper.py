import asyncio
import random
from sqlalchemy.orm import Session

from src.common.logger import format_job_log, get_logger
from src.db.database import SessionLocal
from src.mynimo.db import create_mynimo_details_bulk, get_mynimo_details_by_job_id
from src.mynimo.get_jobs import fetch_jobs
from src.mynimo.models.mynimo_job_details import MynimoJobDetails
from src.mynimo.models.mynimo_link import MynimoLink, MynimoParams
from src.mynimo.mynimo_run_tracker import MynimoRunTracker

logger = get_logger("mynimo_scraper")

BASE_URL = "https://www.mynimo.com/api/jobs/local/browse"

LINKS: list[MynimoLink] = [
    MynimoLink(
        max_page=2,
        base_url=BASE_URL,
        params=MynimoParams(path="/cebu-jobs"),
    ),
    MynimoLink(
        max_page=2,
        base_url=BASE_URL,
        params=MynimoParams(path="/cdo-jobs"),
    ),
    MynimoLink(
        max_page=2,
        base_url=BASE_URL,
        params=MynimoParams(path="/davao-jobs"),
    ),
    MynimoLink(
        max_page=2,
        base_url=BASE_URL,
        params=MynimoParams(path="/home-based-jobs"),
    ),
]


async def scrape_mynimo_link(
    db: Session, link_target: MynimoLink, target_idx: int, total_targets: int
) -> None:
    """Scrape a single Mynimo search target across up to max_page pages."""
    for current_page in range(1, link_target.max_page + 1):
        page_url = link_target.get_next_page(current_page)
        logger.debug(f"[Mynimo] Fetching page {current_page}: {page_url}")

        try:
            response = await fetch_jobs(page_url)
            pagination = response.data.jobs.result

            last_page = pagination.last_page
            total = pagination.total

            new_jobs: list[MynimoJobDetails] = []
            jobs_in_page = pagination.data
            total_jobs_in_page = len(jobs_in_page)
            saved_count = 0
            skipped_count = 0

            for job_idx, job in enumerate(jobs_in_page, 1):
                job_id_str = str(job.id)

                existing = get_mynimo_details_by_job_id(db, job_id_str)
                if existing:
                    skipped_count += 1
                    logger.debug(
                        f"[Mynimo] [SKIP] [{job_id_str}] {job.title} already in DB"
                    )
                    continue

                if any(j.job_id == job_id_str for j in new_jobs):
                    skipped_count += 1
                    continue

                job_details = MynimoJobDetails.from_api_data(job)
                new_jobs.append(job_details)
                saved_count += 1

                location_parts = [
                    p
                    for p in (
                        job.barangay_name,
                        job.location_name,
                        job.location_parent_name,
                    )
                    if p and p.strip()
                ]
                location_display = (
                    ", ".join(location_parts) or job.overseas_location or None
                )

                salary_display = None
                if not job.hide_salary and (job.min_salary or job.max_salary):
                    salary_display = (
                        f"PHP {job.min_salary:,} - {job.max_salary:,} / Monthly"
                    )

                formatted_job = format_job_log(
                    board="Mynimo",
                    title=job.title or "Untitled",
                    company=job.company,
                    salary=salary_display,
                    location=location_display,
                    page_info=f"page {current_page}/{link_target.max_page}",
                    item_info=f"{job_idx}/{total_jobs_in_page}",
                )
                logger.debug(formatted_job)

            if new_jobs:
                create_mynimo_details_bulk(db, new_jobs)

            logger.info(
                f"[Mynimo] Target {target_idx}/{total_targets} [page {current_page}/{link_target.max_page}]: "
                f"Scraped {total_jobs_in_page} jobs ({saved_count} saved, {skipped_count} skipped)"
            )

            if current_page >= last_page:
                logger.debug(
                    f"[Mynimo] Reached last page ({last_page}). Stopping pagination."
                )
                break

            if current_page < link_target.max_page:
                delay = random.uniform(4.0, 10.0)
                await asyncio.sleep(delay)

        except Exception as e:
            logger.error(f"[Mynimo] Error on page {current_page} of {page_url}: {e}")
            raise


async def scrape_mynimo(
    links: list[MynimoLink] | None = None, is_retry: bool = False
) -> None:
    """Scrape all configured Mynimo search targets."""
    targets = links if links is not None else LINKS
    tracker = MynimoRunTracker(links=targets, is_retry_run=is_retry)

    try:
        with SessionLocal() as db:
            total = len(targets)
            logger.info(f"[Mynimo] Scraping {total} target link(s)...")
            for index, link_target in enumerate(targets):
                tracker.set_current_index(index)
                logger.info(
                    f"[Mynimo] Target {index + 1}/{total}: path='{link_target.params.path}'"
                )
                try:
                    await scrape_mynimo_link(
                        db, link_target, target_idx=index + 1, total_targets=total
                    )
                    tracker.record_success()
                except Exception as e:
                    logger.error(
                        f"[Mynimo] Failed target {index + 1}/{total} ({link_target.get_next_page(1)}): {e}"
                    )
                    if tracker.record_link_error(link=link_target, error=e):
                        break

                if index < total - 1:
                    delay = random.uniform(3.0, 6.0)
                    await asyncio.sleep(delay)

        tracker.finalize()

    except Exception as e:
        logger.error(f"[Mynimo] Error occurred during scrape run: {e}")


if __name__ == "__main__":
    asyncio.run(scrape_mynimo())
