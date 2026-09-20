import asyncio

from src.db.database import BaseEntity, engine
from src.jobstreet.jobstreet_scraper import scrape_jobstreet


def main():
    BaseEntity.metadata.create_all(bind=engine)

    asyncio.run(scrape_jobstreet())


if __name__ == "__main__":
    main()
