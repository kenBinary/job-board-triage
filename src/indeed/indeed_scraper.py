import asyncio
from typing import List

from camoufox import AsyncCamoufox

from src.db.database import SessionLocal
from src.indeed.db import create_indeed_details_bulk, get_indeed_details_by_job_id
from src.indeed.get_jobs import fetch_job
from src.indeed.models.indeed_job_details import IndeedJobDetails

links = [
    "https://ph.indeed.com/jobs?q=developer&l=Philippines&sort=date&fromage=7",
    "https://ph.indeed.com/jobs?q=developer&l=Philippines&sort=date&fromage=7&start=10",
    "https://ph.indeed.com/jobs?q=c%23&l=Cebu+City%2C+Cebu&sort=date&fromage=7",
    "https://ph.indeed.com/jobs?q=c%23&l=Cebu+City%2C+Cebu&sort=date&fromage=7&start=10",
    "https://ph.indeed.com/jobs?q=asp.net&l=Cebu+City%2C+Cebu&fromage=7&sort=date",
    "https://ph.indeed.com/jobs?q=asp.net&l=Cebu+City%2C+Cebu&fromage=7&sort=date&start=10",
    "https://ph.indeed.com/jobs?q=engineer&l=Philippines&sort=date&fromage=7",
    "https://ph.indeed.com/jobs?q=engineer&l=Philippines&sort=date&fromage=7&start=10",
    "https://ph.indeed.com/jobs?q=angular&l=Cebu&sort=date&fromage=7",
    "https://ph.indeed.com/jobs?q=angular&l=Cebu&sort=date&fromage=7&start=10",
    "https://ph.indeed.com/jobs?q=react&l=Cebu&fromage=7&sort=date",
    "https://ph.indeed.com/jobs?q=react&l=Cebu&fromage=7&sort=date&start=10",
    "https://ph.indeed.com/jobs?q=engineer&l=Cebu&fromage=7&sort=date",
    "https://ph.indeed.com/jobs?q=engineer&l=Cebu&fromage=7&sort=date&start=10",
    "https://ph.indeed.com/jobs?q=developer&l=Cebu&sort=date&fromage=7",
    "https://ph.indeed.com/jobs?q=developer&l=Cebu&sort=date&fromage=7&start=10",
    "https://ph.indeed.com/jobs?q=&l=Cagayan+de+Oro+City%2C+Misamis+Oriental&sort=date&fromage=7",
    "https://ph.indeed.com/jobs?q=&l=Cagayan+de+Oro+City%2C+Misamis+Oriental&sort=date&fromage=7&start=10",
]


PROFILE_DIR = "./camoufox_profile"


async def scrape_indeed() -> None:
    try:
        async with AsyncCamoufox(
            headless=False,
            persistent_context=True,
            user_data_dir=PROFILE_DIR,
            humanize=True,
        ) as browser:
            page = await browser.new_page()
            with SessionLocal() as db:
                for link in links:
                    await page.goto(link, wait_until="domcontentloaded")

                    page_title = await page.title()
                    if "security check" in page_title.lower():
                        print(f"Page title: {page_title}")
                        input(
                            "Solve any CAPTCHA or log in if required, then press Enter here..."
                        )

                    print("-" * 50)
                    print(f"Scraping Indeed link: {link}")
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
                                continue

                            indeed_job_detail = IndeedJobDetails.from_api_data(job)
                            if any(j.job_id == job.jobkey for j in indeed_job_details):
                                continue

                            indeed_job_details.append(indeed_job_detail)

                            print("-", job.title, "|", job.company)
                            print("-" * 50)
                        create_indeed_details_bulk(db, indeed_job_details)
                        print(
                            f"Scraped {len(indeed_response.job_cards)} job cards from {link}"
                        )
                    else:
                        print(f"No job cards found for {link}")
    except Exception as e:
        print(f"Error occurred while scraping Indeed: {e}")


if __name__ == "__main__":
    asyncio.run(scrape_indeed())
