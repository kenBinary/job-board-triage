import asyncio

from src.db.database import BaseEntity, engine
from src.indeed.indeed_scraper import scrape_indeed
from src.jobstreet.jobstreet_scraper import scrape_jobstreet


async def main():
    BaseEntity.metadata.create_all(bind=engine)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(scrape_jobstreet())
        tg.create_task(scrape_indeed())


if __name__ == "__main__":
    asyncio.run(main())
