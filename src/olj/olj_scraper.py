import asyncio

from src.db.database import SessionLocal
from src.olj.db import create_olj_details_bulk, get_olj_details_by_job_id
from src.olj.get_jobs import fetch_jobs
from src.olj.models.olj_job_details import OljJobDetails

links = [
    "https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword=engineer",
    "https://www.onlinejobs.ph/jobseekers/jobsearch/30?jobkeyword=engineer",
    "https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword=developer",
    "https://www.onlinejobs.ph/jobseekers/jobsearch/30?jobkeyword=developer",
    "https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword=fastapi",
    "https://www.onlinejobs.ph/jobseekers/jobsearch/30?jobkeyword=fastapi",
    "https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword=asp.net",
    "https://www.onlinejobs.ph/jobseekers/jobsearch/30?jobkeyword=asp.net",
    "https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword=.net",
    "https://www.onlinejobs.ph/jobseekers/jobsearch/30?jobkeyword=.net",
    "https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword=c%23",
    "https://www.onlinejobs.ph/jobseekers/jobsearch/30?jobkeyword=c%23",
    "https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword=python",
    "https://www.onlinejobs.ph/jobseekers/jobsearch/30?jobkeyword=python",
    "https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword=angular",
    "https://www.onlinejobs.ph/jobseekers/jobsearch/30?jobkeyword=angular",
    "https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword=react",
    "https://www.onlinejobs.ph/jobseekers/jobsearch/30?jobkeyword=react",
    "https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword=typescript",
    "https://www.onlinejobs.ph/jobseekers/jobsearch/30?jobkeyword=typescript",
    "https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword=javascript",
    "https://www.onlinejobs.ph/jobseekers/jobsearch/30?jobkeyword=javascript",
    "https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword=css",
    "https://www.onlinejobs.ph/jobseekers/jobsearch/30?jobkeyword=css",
    "https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword=html",
    "https://www.onlinejobs.ph/jobseekers/jobsearch/30?jobkeyword=html",
    "https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword=programmer",
    "https://www.onlinejobs.ph/jobseekers/jobsearch/30?jobkeyword=programmer",
]


async def scrape_olj() -> None:
    try:
        total_items = len(links)
        with SessionLocal() as db:
            olj_job_details_list: list[OljJobDetails] = []
            for index, link in enumerate(links):
                print(f"Scraping OnlineJobs with link: {link}")

                olj_jobs = await fetch_jobs(link)
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
                    print(f"https://www.onlinejobs.ph{job.link}" if job.link else "N/A")
                    print(f"  Job Type: {job.job_type}")
                    print(f"  Salary: {job.salary}" if job.salary else "  Salary: N/A")
                    print(f" Tags: {', '.join(job.tags) if job.tags else 'N/A'}")
                    print("-" * 50)

                create_olj_details_bulk(db, olj_job_details_list)
                olj_job_details_list.clear()
                print("*" * 50)

                if index < total_items - 1:
                    await asyncio.sleep(10)

    except Exception as e:
        print(f"Error occurred while scraping OnlineJobs: {e}")


if __name__ == "__main__":
    asyncio.run(scrape_olj())
