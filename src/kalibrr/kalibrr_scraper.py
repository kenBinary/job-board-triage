import asyncio
import math
import random

from src.common.enums.job_board import JobBoardEnum
from src.common.logger import format_job_log, get_logger
from src.common.settings import settings
from src.db.database import SessionLocal
from src.kalibrr.db import create_kalibrr_details_bulk, get_kalibrr_details_by_job_id
from src.kalibrr.get_jobs import fetch_jobs
from src.kalibrr.models.kalibrr_job_details import KalibrrJobDetails
from src.kalibrr.models.kalibrr_link import KalibrrLink
from src.kalibrr.kalibrr_run_tracker import KalibrrRunTracker

logger = get_logger("kalibrr_scraper")

async def scrape_kalibrr_link(
    link_target: KalibrrLink, target_idx: int, total_targets: int
) -> None:
    """Scrape a single Kalibrr search target across up to max_page pages."""
    for current_page in range(1, link_target.max_page + 1):
        page_url = link_target.get_next_page(current_page)
        current_offset = link_target.params.offset + (
            (current_page - 1) * link_target.params.limit
        )
        logger.debug(
            f"[Kalibrr] Fetching page {current_page} (offset={current_offset}): {page_url}"
        )

        try:
            response = await fetch_jobs(page_url)

            total = response.count
            max_reachable_pages = (
                math.ceil(total / link_target.params.limit) if total > 0 else 0
            )

            if not response.jobs:
                logger.debug("[Kalibrr] No jobs returned. Stopping pagination.")
                break

            new_jobs: list[KalibrrJobDetails] = []
            jobs_in_page = response.jobs
            total_jobs_in_page = len(jobs_in_page)
            saved_count = 0
            skipped_count = 0

            for job_idx, job in enumerate(jobs_in_page, 1):
                job_id_str = str(job.id)
                with SessionLocal() as db:
                    existing = get_kalibrr_details_by_job_id(db, job_id_str)
                if existing:
                    skipped_count += 1
                    logger.debug(
                        f"[Kalibrr] [SKIP] [{job_id_str}] {job.name} already in DB"
                    )
                    continue

                if any(j.job_id == job_id_str for j in new_jobs):
                    skipped_count += 1
                    continue

                job_details = KalibrrJobDetails.from_api_data(job)
                new_jobs.append(job_details)
                saved_count += 1

                salary_display = None
                if job.salary_shown and (job.base_salary or job.maximum_salary):
                    currency = job.salary_currency or ""
                    lo = f"{job.base_salary:,.0f}" if job.base_salary else "?"
                    hi = f"{job.maximum_salary:,.0f}" if job.maximum_salary else "?"
                    interval = job.salary_interval or ""
                    salary_display = f"{currency} {lo} - {hi} / {interval}".strip()

                location_display = job_details.location or None

                formatted_job = format_job_log(
                    board="Kalibrr",
                    title=job.name or "Untitled",
                    company=job.company_name,
                    salary=salary_display,
                    location=location_display,
                    page_info=f"page {current_page}/{link_target.max_page}",
                    item_info=f"{job_idx}/{total_jobs_in_page}",
                )
                logger.debug(formatted_job)

            if new_jobs:
                with SessionLocal() as db:
                    create_kalibrr_details_bulk(db, new_jobs)

            logger.info(
                f"[Kalibrr] Target {target_idx}/{total_targets} [page {current_page}/{link_target.max_page}]: "
                f"Scraped {total_jobs_in_page} jobs ({saved_count} saved, {skipped_count} skipped)"
            )

            if current_page >= max_reachable_pages:
                logger.debug(
                    f"[Kalibrr] Reached last available page ({max_reachable_pages}). Stopping."
                )
                break

            if current_page < link_target.max_page:
                delay = random.uniform(5.0, 10.0)
                await asyncio.sleep(delay)

        except Exception as e:
            logger.error(
                f"[Kalibrr] Error on page {current_page} for '{link_target.params.text}': {e}"
            )
            raise


async def scrape_kalibrr(
    links: list[KalibrrLink] | None = None, is_retry: bool = False
) -> None:
    """Scrape all configured Kalibrr search targets."""
    targets = (
        links if links is not None else settings.get_scraper_links(JobBoardEnum.Kalibrr)
    )
    tracker = KalibrrRunTracker(links=targets, is_retry_run=is_retry)

    try:
        total = len(targets)
        logger.info(f"[Kalibrr] Scraping {total} target link(s)...")
        for index, link_target in enumerate(targets):
            tracker.set_current_index(index)
            logger.info(
                f"[Kalibrr] Target {index + 1}/{total}: '{link_target.params.text or 'All'}'"
            )
            try:
                await scrape_kalibrr_link(
                    link_target, target_idx=index + 1, total_targets=total
                )
                tracker.record_success()
            except Exception as e:
                logger.error(
                    f"[Kalibrr] Failed target {index + 1}/{total} ({link_target.get_next_page(1)}): {e}"
                )
                if tracker.record_link_error(link=link_target, error=e):
                    break

            if index < total - 1:
                delay = random.uniform(4.0, 8.0)
                await asyncio.sleep(delay)

        tracker.finalize()

    except Exception as e:
        logger.error(f"[Kalibrr] Error occurred during scrape run: {e}")


if __name__ == "__main__":
    asyncio.run(scrape_kalibrr())
