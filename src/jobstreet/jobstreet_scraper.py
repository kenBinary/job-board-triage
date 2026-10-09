import asyncio
import math
import random
from typing import List

from src.common.logger import format_job_log, get_logger
from src.db.database import SessionLocal
from src.jobstreet.db import (
    create_jobstreet_details_bulk,
    get_jobstreet_details_by_job_id,
)
from src.jobstreet.get_jobs import fetch_jobs, WorkArrangementEnum
from src.jobstreet.jobstreet_run_tracker import JobstreetRunTracker
from src.jobstreet.models.jobstreet_job_details import JobStreetJobDetails
from src.jobstreet.models.jobstreet_link import JobStreetLink, JobStreetParams

logger = get_logger("jobstreet_scraper")

BASE_URL = "https://ph.jobstreet.com/graphql"

LINKS: List[JobStreetLink] = [
    JobStreetLink(
        max_page=2,
        base_url=BASE_URL,
        params=JobStreetParams(
            text="developer",
            where=["Philippines"],
            work_arrangement_ids=[WorkArrangementEnum.REMOTE],
            listed_at="7d",
            sort="listedAt",
            page_size=10,
        ),
    ),
    JobStreetLink(
        max_page=2,
        base_url=BASE_URL,
        params=JobStreetParams(
            text="software",
            where=["Philippines"],
            work_arrangement_ids=[WorkArrangementEnum.REMOTE],
            listed_at="7d",
            sort="listedAt",
            page_size=10,
        ),
    ),
    JobStreetLink(
        max_page=2,
        base_url=BASE_URL,
        params=JobStreetParams(
            text="engineer",
            where=["Philippines"],
            work_arrangement_ids=[WorkArrangementEnum.REMOTE],
            listed_at="7d",
            sort="listedAt",
            page_size=10,
        ),
    ),
    JobStreetLink(
        max_page=2,
        base_url=BASE_URL,
        params=JobStreetParams(
            text="",
            where=["Cagayan de Oro Misamis Oriental"],
            listed_at="7d",
            sort="listedAt",
            page_size=10,
        ),
    ),
    JobStreetLink(
        max_page=2,
        base_url=BASE_URL,
        params=JobStreetParams(
            text="developer",
            where=["Cebu City Cebu"],
            listed_at="7d",
            sort="listedAt",
            page_size=10,
        ),
    ),
    JobStreetLink(
        max_page=2,
        base_url=BASE_URL,
        params=JobStreetParams(
            text="engineer",
            where=["Cebu City Cebu"],
            listed_at="7d",
            sort="listedAt",
            page_size=10,
        ),
    ),
    JobStreetLink(
        max_page=2,
        base_url=BASE_URL,
        params=JobStreetParams(
            text="software",
            where=["Cebu City Cebu"],
            listed_at="7d",
            sort="listedAt",
            page_size=10,
        ),
    ),
]


async def scrape_jobstreet_link(
    link: JobStreetLink, target_idx: int, total_targets: int
) -> None:
    """Scrapes job listings for a JobStreetLink across its configured max_page."""
    with SessionLocal() as db:
        for current_page in range(1, link.max_page + 1):
            page_url = link.get_next_page(current_page)
            search_params = link.get_search_params(current_page)
            logger.debug(f"[JobStreet] Scraping link: {page_url}")

            result = await fetch_jobs(search_params)

            pagination = result.data.jobSearchV7.results.pagination
            total_results = int(pagination.resultCount)
            page_size = int(pagination.pageSize)
            total_pages = math.ceil(total_results / page_size) if page_size > 0 else 1

            job_details_list: list[JobStreetJobDetails] = []
            jobs_in_page = result.data.jobSearchV7.results.jobs
            total_jobs_in_page = len(jobs_in_page)
            saved_count = 0
            skipped_count = 0

            for job_idx, job in enumerate(jobs_in_page, 1):
                existing_job_details = get_jobstreet_details_by_job_id(db, job.id)
                if existing_job_details:
                    skipped_count += 1
                    logger.debug(
                        f"[JobStreet] [SKIP] Job {job.id} ({job.title}) already in DB"
                    )
                    continue

                job_details = JobStreetJobDetails.from_api_data(job)
                if any(j.job_id == job.id for j in job_details_list):
                    skipped_count += 1
                    continue

                job_details_list.append(job_details)
                saved_count += 1

                salary_str = None
                if job.salary and job.salary.min and job.salary.max:
                    salary_str = f"{job.salary.currency} {job.salary.min:,} - {job.salary.max:,} ({job.salary.period})"

                location_str = (
                    job.location.displayName.text
                    if job.location and job.location.displayName
                    else None
                )
                company_str = job.advertiser.name if job.advertiser else None

                formatted_job = format_job_log(
                    board="JobStreet",
                    title=job.title or "Untitled",
                    company=company_str,
                    salary=salary_str,
                    location=location_str,
                    page_info=f"page {current_page}/{link.max_page}",
                    item_info=f"{job_idx}/{total_jobs_in_page}",
                )
                logger.debug(formatted_job)

            if job_details_list:
                create_jobstreet_details_bulk(db, job_details_list)

            logger.info(
                f"[JobStreet] Target {target_idx}/{total_targets} [page {current_page}/{link.max_page}]: "
                f"Scraped {total_jobs_in_page} jobs ({saved_count} saved, {skipped_count} skipped)"
            )

            if current_page >= total_pages:
                logger.debug(
                    f"[JobStreet] Reached last available page ({total_pages}). Stopping pagination."
                )
                break

            if current_page < link.max_page:
                await asyncio.sleep(5)


async def scrape_jobstreet(
    links: list[JobStreetLink] | None = None, is_retry: bool = False
) -> None:
    """Scrape all configured JobStreet search targets."""
    targets = links if links is not None else LINKS
    tracker = JobstreetRunTracker(links=targets, is_retry_run=is_retry)

    try:
        total_items = len(targets)
        logger.info(f"[JobStreet] Scraping {total_items} target link(s)...")
        for index, link in enumerate(targets):
            tracker.set_current_index(index)
            query_desc = link.params.text or "All"
            locations_desc = (
                ", ".join(link.params.where) if link.params.where else "Any"
            )
            logger.info(
                f"[JobStreet] Target {index + 1}/{total_items}: {query_desc} ({locations_desc})"
            )
            try:
                await scrape_jobstreet_link(
                    link, target_idx=index + 1, total_targets=total_items
                )
                tracker.record_success()
            except Exception as e:
                logger.error(
                    f"[JobStreet] Failed target {index + 1}/{total_items} ({link.get_next_page(1)}): {e}"
                )
                if tracker.record_link_error(link=link, error=e):
                    break

            if index < total_items - 1:
                await asyncio.sleep(random.uniform(4.0, 10.0))

        tracker.finalize()

    except Exception as e:
        logger.error(f"[JobStreet] Error occurred during scrape run: {e}")


if __name__ == "__main__":
    asyncio.run(scrape_jobstreet())
