import asyncio

from src.indeed.get_jobs import fetch_jobs
from src.jobstreet.jobstreet_scraper import scrape_jobstreet


async def scrape_indeed() -> None:
    try:
        await fetch_jobs()
    except Exception as e:
        print(f"Error occurred while scraping Indeed: {e}")


if __name__ == "__main__":
    asyncio.run(scrape_jobstreet())
