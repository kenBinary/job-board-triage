import asyncio
import math
import random
from typing import List

from src.db.database import SessionLocal
from src.jobstreet.db import (
    create_jobstreet_details_bulk,
    get_jobstreet_details_by_job_id,
)
from src.jobstreet.get_jobs import fetch_jobs, WorkArrangementEnum
from src.jobstreet.models.jobstreet_job_details import JobStreetJobDetails
from src.jobstreet.models.jobstreet_link import JobStreetLink, JobStreetParams

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


async def scrape_jobstreet_link(link: JobStreetLink) -> None:
    """Scrapes job listings for a JobStreetLink across its configured max_page."""
    try:
        with SessionLocal() as db:
            for current_page in range(1, link.max_page + 1):
                page_url = link.get_next_page(current_page)
                search_params = link.get_search_params(current_page)
                print(f"Scraping JobStreet link: {page_url}")

                result = await fetch_jobs(search_params)

                pagination = result.data.jobSearchV7.results.pagination
                total_results = int(pagination.resultCount)
                page_size = int(pagination.pageSize)
                total_pages = (
                    math.ceil(total_results / page_size) if page_size > 0 else 1
                )

                print(f"  Total matching jobs: {pagination.resultCount}")
                print(
                    f"  Current page: {pagination.page} / Total pages: {total_pages} (Page size: {pagination.pageSize})\n"
                )

                job_details_list: list[JobStreetJobDetails] = []

                for job in result.data.jobSearchV7.results.jobs:
                    print(f"[{job.id}] {job.title}")
                    print(
                        f"URL: https://ph.jobstreet.com/job/{job.id}"
                        if job.id
                        else "N/A"
                    )
                    existing_job_details = get_jobstreet_details_by_job_id(db, job.id)
                    if existing_job_details:
                        print(
                            f"Job with ID {job.id} already exists in the database. Skipping."
                        )
                        print("-" * 50)
                        continue

                    job_details = JobStreetJobDetails.from_api_data(job)
                    if any(j.job_id == job.id for j in job_details_list):
                        continue

                    job_details_list.append(job_details)

                    print(
                        f"  Company: {job.advertiser.name if job.advertiser else 'N/A'}"
                    )
                    print(
                        f"  Location: {job.location.displayName.text if job.location and job.location.displayName else 'N/A'}"
                    )
                    if job.salary and job.salary.min and job.salary.max:
                        print(
                            f"  Salary: {job.salary.currency} {job.salary.min:,} - {job.salary.max:,} ({job.salary.period})"
                        )
                    print("-" * 50)

                if job_details_list:
                    create_jobstreet_details_bulk(db, job_details_list)
                    print(
                        f"  Saved {len(job_details_list)} new job(s) from page {current_page}."
                    )

                if current_page >= total_pages:
                    print(
                        f"  Reached last available page ({total_pages}). Stopping pagination."
                    )
                    break

                if current_page < link.max_page:
                    await asyncio.sleep(5)

    except Exception as e:
        print(f"Error occurred while scraping JobStreet: {e}")


async def scrape_jobstreet(links: list[JobStreetLink] | None = None) -> None:
    """Scrape all configured JobStreet search targets."""
    targets = links if links is not None else LINKS

    try:
        total_items = len(targets)
        for index, link in enumerate(targets):
            print(f"Scraping JobStreet target {index + 1} of {total_items}")
            await scrape_jobstreet_link(link)

            if index < total_items - 1:
                await asyncio.sleep(random.uniform(4.0, 10.0))

            print("" + "=" * 50 + "\n")

    except Exception as e:
        print(f"Error occurred while scraping JobStreet: {e}")


if __name__ == "__main__":
    asyncio.run(scrape_jobstreet())
