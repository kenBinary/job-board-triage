import asyncio
from typing import Optional
import typer

from src.db.database import BaseEntity, engine
from src.indeed.indeed_scraper import scrape_indeed
from src.jobstreet.jobstreet_scraper import scrape_jobstreet
from src.mynimo.mynimo_scraper import scrape_mynimo
from src.olj.olj_scraper import scrape_olj

app = typer.Typer()

SCRAPERS = {
    "jobstreet": scrape_jobstreet,
    "indeed": scrape_indeed,
    "olj": scrape_olj,
    "mynimo": scrape_mynimo,
}


async def run_scrapers(boards: list[str]):
    BaseEntity.metadata.create_all(bind=engine)

    async with asyncio.TaskGroup() as tg:
        for name in boards:
            tg.create_task(SCRAPERS[name]())


@app.command()
def main(
    board: Optional[str] = typer.Option(
        None,
        "--board",
        "-b",
        help="Comma-separated list of job boards to scrape (e.g. --board=indeed,olj). Default runs all.",
    ),
):
    if board:
        requested_boards = [b.strip().lower() for b in board.split(",") if b.strip()]

        invalid = set(requested_boards) - set(SCRAPERS.keys())
        if invalid:
            valid_list = ", ".join(SCRAPERS.keys())
            raise typer.BadParameter(
                f"Unknown board(s): {', '.join(invalid)}. Valid options: {valid_list}"
            )
    else:
        requested_boards = list(SCRAPERS.keys())

    asyncio.run(run_scrapers(requested_boards))


if __name__ == "__main__":
    app()
