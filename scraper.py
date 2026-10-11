import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional
import typer

from src.common.enums.job_board import JobBoardEnum
from src.common.logger import get_logger, setup_logging
from src.db.database import BaseEntity, engine

logger = get_logger("scraper_app")


from src.indeed.indeed_run_tracker import IndeedRunTracker
from src.indeed.indeed_scraper import scrape_indeed
from src.common.infra.browser_context import CamoufoxSingleton
from src.jobstreet.jobstreet_run_tracker import JobstreetRunTracker
from src.jobstreet.jobstreet_scraper import scrape_jobstreet
from src.kalibrr.kalibrr_run_tracker import KalibrrRunTracker
from src.kalibrr.kalibrr_scraper import scrape_kalibrr
from src.mynimo.mynimo_run_tracker import MynimoRunTracker
from src.mynimo.mynimo_scraper import scrape_mynimo
from src.olj.olj_run_tracker import OljRunTracker
from src.olj.olj_scraper import scrape_olj
from src.linkedin_posts.linkedin_posts_run_tracker import LinkedinPostsRunTracker
from src.linkedin_posts.linkedin_posts_scraper import scrape_linkedin_posts
from src.facebook_posts.facebook_posts_run_tracker import FacebookPostsRunTracker
from src.facebook_posts.facebook_posts_scraper import scrape_facebook_posts

app = typer.Typer()

SCRAPERS = {
    JobBoardEnum.JobStreet: scrape_jobstreet,
    JobBoardEnum.Indeed: scrape_indeed,
    JobBoardEnum.Olj: scrape_olj,
    JobBoardEnum.Mynimo: scrape_mynimo,
    JobBoardEnum.Kalibrr: scrape_kalibrr,
    JobBoardEnum.LinkedinPosts: scrape_linkedin_posts,
    JobBoardEnum.FacebookPosts: scrape_facebook_posts,
}


@dataclass
class BoardConfig:
    links: list[Any] | None
    is_retry: bool


async def run_scrapers(board_configs: Dict[JobBoardEnum, BoardConfig]) -> None:
    BaseEntity.metadata.create_all(bind=engine)

    try:
        async with asyncio.TaskGroup() as tg:
            for name, config in board_configs.items():
                tg.create_task(
                    SCRAPERS[name](links=config.links, is_retry=config.is_retry)
                )
    finally:
        await CamoufoxSingleton.close()


def initialize_retry_state(board_name: str) -> tuple[bool, int]:
    match board_name:
        case JobBoardEnum.JobStreet.value:
            has_retry_links = JobstreetRunTracker.has_retry_links()
            count = JobstreetRunTracker.get_retry_count()
        case JobBoardEnum.Olj.value:
            has_retry_links = OljRunTracker.has_retry_links()
            count = OljRunTracker.get_retry_count()
        case JobBoardEnum.Indeed.value:
            has_retry_links = IndeedRunTracker.has_retry_links()
            count = IndeedRunTracker.get_retry_count()
        case JobBoardEnum.Mynimo.value:
            has_retry_links = MynimoRunTracker.has_retry_links()
            count = MynimoRunTracker.get_retry_count()
        case JobBoardEnum.Kalibrr.value:
            has_retry_links = KalibrrRunTracker.has_retry_links()
            count = KalibrrRunTracker.get_retry_count()
        case JobBoardEnum.LinkedinPosts.value:
            has_retry_links = LinkedinPostsRunTracker.has_retry_links()
            count = LinkedinPostsRunTracker.get_retry_count()
        case JobBoardEnum.FacebookPosts.value:
            has_retry_links = FacebookPostsRunTracker.has_retry_links()
            count = FacebookPostsRunTracker.get_retry_count()
        case _:
            has_retry_links = False
            count = 0
    return has_retry_links, count


def clear_retry_state(board_name: str) -> None:
    match board_name:
        case JobBoardEnum.JobStreet.value:
            JobstreetRunTracker.clear_retry_state()
        case JobBoardEnum.Olj.value:
            OljRunTracker.clear_retry_state()
        case JobBoardEnum.Indeed.value:
            IndeedRunTracker.clear_retry_state()
        case JobBoardEnum.Mynimo.value:
            MynimoRunTracker.clear_retry_state()
        case JobBoardEnum.Kalibrr.value:
            KalibrrRunTracker.clear_retry_state()
        case JobBoardEnum.LinkedinPosts.value:
            LinkedinPostsRunTracker.clear_retry_state()
        case JobBoardEnum.FacebookPosts.value:
            FacebookPostsRunTracker.clear_retry_state()
        case _:
            pass


def load_retry_links(board_name: str) -> list[Any] | None:
    match board_name:
        case JobBoardEnum.JobStreet.value:
            return JobstreetRunTracker.load_retry_links()
        case JobBoardEnum.Olj.value:
            return OljRunTracker.load_retry_links()
        case JobBoardEnum.Indeed.value:
            return IndeedRunTracker.load_retry_links()
        case JobBoardEnum.Mynimo.value:
            return MynimoRunTracker.load_retry_links()
        case JobBoardEnum.Kalibrr.value:
            return KalibrrRunTracker.load_retry_links()
        case JobBoardEnum.LinkedinPosts.value:
            return LinkedinPostsRunTracker.load_retry_links()
        case JobBoardEnum.FacebookPosts.value:
            return FacebookPostsRunTracker.load_retry_links()
        case _:
            return None


def create_board_config(
    board_name: str, links: list[Any] | None, is_retry: bool
) -> BoardConfig:
    match board_name:
        case (
            JobBoardEnum.JobStreet.value
            | JobBoardEnum.Olj.value
            | JobBoardEnum.Indeed.value
            | JobBoardEnum.Mynimo.value
            | JobBoardEnum.Kalibrr.value
            | JobBoardEnum.LinkedinPosts.value
            | JobBoardEnum.FacebookPosts.value
        ):
            return BoardConfig(links=links, is_retry=is_retry)
        case _:
            raise ValueError(f"Unknown board name: {board_name}")


@app.command()
def main(
    board: Optional[str] = typer.Option(
        None,
        "--board",
        "-b",
        help="Comma-separated list of job boards to scrape (e.g. --board=indeed,olj). Default runs all.",
    ),
    retry: bool = typer.Option(
        False,
        "--retry",
        "-r",
        help="Force resume scraping from saved retry state without prompting.",
    ),
    fresh: bool = typer.Option(
        False,
        "--fresh",
        help="Force fresh start, ignoring and clearing any existing retry state without prompting.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable detailed item-level verbose logs. Defaults to summary INFO logs.",
    ),
):
    setup_logging(verbose=verbose)

    if retry and fresh:
        raise typer.BadParameter(
            "Cannot specify both --retry and --fresh at the same time."
        )

    if board:
        requested_boards = [b.strip().lower() for b in board.split(",") if b.strip()]
        if not requested_boards:
            raise typer.BadParameter("No valid board names provided.")

        valid_values = set(JobBoardEnum)
        invalid = set(requested_boards) - valid_values

        if invalid:
            valid_list = ", ".join(valid_values)
            raise typer.BadParameter(
                f"Unknown board(s): {', '.join(invalid)}. Valid options: {valid_list}"
            )

        requested_boards = [JobBoardEnum(b) for b in requested_boards]
    else:
        requested_boards = list(JobBoardEnum)

    board_configs: Dict[JobBoardEnum, BoardConfig] = {}
    for board in requested_boards:
        has_retry_links, count = initialize_retry_state(board)

        if fresh:
            if has_retry_links:
                clear_retry_state(board)
                logger.info(f"[{board}] Starting fresh (cleared previous retry state).")
            config = create_board_config(board, links=None, is_retry=False)
            board_configs[board] = config
        elif retry:
            if has_retry_links:
                loaded_retry_links = load_retry_links(board)
                config = create_board_config(
                    board, links=loaded_retry_links, is_retry=True
                )
                board_configs[board] = config
                logger.info(
                    f"[{board}] Resuming from saved retry state ({count} link(s))."
                )
            else:
                config = create_board_config(board, links=None, is_retry=False)
                logger.info(f"[{board}] No retry state found; running default links.")
                board_configs[board] = config
        else:
            if has_retry_links:
                should_resume = typer.confirm(
                    f"Found saved retry state for '{board}' ({count} link(s) remaining). Resume where it left off?",
                    default=True,
                )
                if should_resume:
                    loaded = load_retry_links(board)
                    config = create_board_config(board, links=loaded, is_retry=True)
                    board_configs[board] = config
                    logger.info(
                        f"[{board}] Resuming from saved retry state ({count} link(s))."
                    )
                else:
                    config = create_board_config(board, links=None, is_retry=False)
                    board_configs[board] = config
                    logger.info(f"[{board}] Starting fresh with default links.")
            else:
                config = create_board_config(board, links=None, is_retry=False)
                board_configs[board] = config

    asyncio.run(run_scrapers(board_configs))


if __name__ == "__main__":
    app()
