import asyncio
import math
from src.db.database import SessionLocal
from src.jobstreet.db import (
    create_jobstreet_details_bulk,
    get_jobstreet_details_by_job_id,
    update_jobstreet_details,
)
from src.jobstreet.get_jobs import JobSearchParams, fetch_jobs, WorkArrangementEnum
from src.jobstreet.models.jobstreet_job_details import JobStreetJobDetails


async def scrape_jobstreet_jobs(
    search_params: JobSearchParams, max_page: int = 1
) -> None:
    try:
        result = await fetch_jobs(search_params)

        pagination = result.data.jobSearchV7.results.pagination
        total_results = int(pagination.resultCount)
        page_size = int(pagination.pageSize)
        total_pages = math.ceil(total_results / page_size) if page_size > 0 else 1

        print(f"Total matching jobs: {pagination.resultCount}")
        print(f"Current page: {pagination.page} / Page size: {pagination.pageSize}\n")

        with SessionLocal() as db:
            job_details_list: list[JobStreetJobDetails] = []

            for _ in range(1, min(total_pages, max_page) + 1):
                print(f"Scraping page {search_params.page} of {total_pages}...")
                for job in result.data.jobSearchV7.results.jobs:
                    print(f"[{job.id}] {job.title}")
                    print(
                        f"URL: https://ph.jobstreet.com/job/{job.id}"
                        if job.id
                        else "N/A"
                    )
                    existing_job_details = get_jobstreet_details_by_job_id(db, job.id)
                    if existing_job_details:
                        existing_job_details.is_new = False
                        update_jobstreet_details(db, existing_job_details)
                        print(
                            f"Job with ID {job.id} already exists in the database. Skipping."
                        )
                        print("-" * 50)
                        continue

                    job_details = JobStreetJobDetails.from_api_data(job)
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
                search_params.page += 1
                await asyncio.sleep(3)

            create_jobstreet_details_bulk(db, job_details_list)
    except Exception as e:
        print(f"Error occurred while scraping JobStreet: {e}")


MAX_PAGE_TO_SCRAPE = 2
SEARCH_LIST_PARAMS: list[JobSearchParams] = [
    JobSearchParams(
        text="developer",
        where=["Philippines"],
        work_arrangement_ids=[WorkArrangementEnum.REMOTE],
        listed_at="7d",
        sort="listedAt",
        page=1,
        page_size=10,
    ),
    JobSearchParams(
        text="software",
        where=["Philippines"],
        work_arrangement_ids=[WorkArrangementEnum.REMOTE],
        listed_at="7d",
        sort="listedAt",
        page=1,
        page_size=10,
    ),
    JobSearchParams(
        text="engineer",
        where=["Philippines"],
        work_arrangement_ids=[WorkArrangementEnum.REMOTE],
        listed_at="7d",
        sort="listedAt",
        page=1,
        page_size=10,
    ),
    JobSearchParams(
        text="",
        where=["Cagayan de Oro Misamis Oriental"],
        listed_at="7d",
        sort="listedAt",
        page=1,
        page_size=10,
    ),
    JobSearchParams(
        text="developer",
        where=["Cebu City Cebu"],
        listed_at="7d",
        sort="listedAt",
        page=1,
        page_size=10,
    ),
    JobSearchParams(
        text="engineer",
        where=["Cebu City Cebu"],
        listed_at="7d",
        sort="listedAt",
        page=1,
        page_size=10,
    ),
    JobSearchParams(
        text="software",
        where=["Cebu City Cebu"],
        listed_at="7d",
        sort="listedAt",
        page=1,
        page_size=10,
    ),
]


async def scrape_jobstreet() -> None:
    try:
        total_items = len(SEARCH_LIST_PARAMS)
        for index, search_params in enumerate(SEARCH_LIST_PARAMS):
            print(f"Scraping JobStreet with parameters: {search_params}")
            await scrape_jobstreet_jobs(search_params, max_page=MAX_PAGE_TO_SCRAPE)

            if index < total_items - 1:
                await asyncio.sleep(10)

            print("" + "=" * 50 + "\n")
            print("" + "=" * 50 + "\n")

    except Exception as e:
        print(f"Error occurred while scraping JobStreet: {e}")


if __name__ == "__main__":
    asyncio.run(scrape_jobstreet())
