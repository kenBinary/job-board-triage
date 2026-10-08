import asyncio

from src.db.database import SessionLocal
from src.olj.db import create_olj_details_bulk, get_olj_details_by_job_id
from src.olj.get_jobs import fetch_jobs
from src.olj.models.olj_job_details import OljJobDetails
from src.olj.models.olj_link import OljLink, OljParams
from src.olj.olj_run_tracker import OljRunTracker

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


async def scrape_olj(
    links: list[OljLink] | None = None, is_retry: bool = False
) -> None:
    """Scrape all configured OnlineJobs search targets."""
    targets = links if links is not None else LINKS
    tracker = OljRunTracker(links=targets, is_retry_run=is_retry)

    try:
        with SessionLocal() as db:
            olj_job_details_list: list[OljJobDetails] = []
            total_items = len(targets)
            for index, link in enumerate(targets):
                tracker.set_current_index(index)
                print(f"Scraping OnlineJobs target {index + 1} of {total_items}")
                try:
                    for current_page in range(1, link.max_page + 1):
                        current_link = link.get_next_page(current_page)
                        print(f"Scraping OnlineJobs with link: {current_link}")

                        olj_jobs = await fetch_jobs(current_link)
                        print(f"Scraped {len(olj_jobs)} jobs from OnlineJobs.")
                        for job in olj_jobs:
                            existing_job_details = get_olj_details_by_job_id(db, job.id)
                            if existing_job_details:
                                print(
                                    f"Job with ID {job.id} already exists in the database. Skipping."
                                )
                                print("-" * 50)
                                continue

                            job_details = OljJobDetails.from_api_data(job)
                            if any(j.job_id == job.id for j in olj_job_details_list):
                                continue
                            olj_job_details_list.append(job_details)

                            print(f"[{job.id}] {job.title}")
                            print(
                                f"https://www.onlinejobs.ph{job.link}"
                                if job.link
                                else "N/A"
                            )
                            print(f"  Job Type: {job.job_type}")
                            print(
                                f"  Salary: {job.salary}"
                                if job.salary
                                else "  Salary: N/A"
                            )
                            print(
                                f" Tags: {', '.join(job.tags) if job.tags else 'N/A'}"
                            )
                            print("-" * 50)

                        create_olj_details_bulk(db, olj_job_details_list)
                        olj_job_details_list.clear()
                        print("*" * 50)

                        if current_page < link.max_page:
                            await asyncio.sleep(10)

                    tracker.record_success()
                except Exception as e:
                    if tracker.record_link_error(link=link, error=e):
                        break

                print("" + "=" * 50 + "\n")

        tracker.finalize()

    except Exception as e:
        print(f"Error occurred while scraping OnlineJobs: {e}")


if __name__ == "__main__":
    asyncio.run(scrape_olj())
