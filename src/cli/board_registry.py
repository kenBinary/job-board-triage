from dataclasses import dataclass
from typing import Any, Callable

from src.common.enums.job_board import JobBoardEnum
from src.facebook_posts.facebook_posts_run_tracker import FacebookPostsRunTracker
from src.facebook_posts.facebook_posts_scraper import scrape_facebook_posts
from src.indeed.indeed_run_tracker import IndeedRunTracker
from src.indeed.indeed_scraper import scrape_indeed
from src.jobstreet.jobstreet_run_tracker import JobstreetRunTracker
from src.jobstreet.jobstreet_scraper import scrape_jobstreet
from src.kalibrr.kalibrr_run_tracker import KalibrrRunTracker
from src.kalibrr.kalibrr_scraper import scrape_kalibrr
from src.linkedin.linkedin_run_tracker import LinkedinRunTracker
from src.linkedin.linkedin_scraper import scrape_linkedin
from src.linkedin_posts.linkedin_posts_run_tracker import LinkedinPostsRunTracker
from src.linkedin_posts.linkedin_posts_scraper import scrape_linkedin_posts
from src.mynimo.mynimo_run_tracker import MynimoRunTracker
from src.mynimo.mynimo_scraper import scrape_mynimo
from src.olj.olj_run_tracker import OljRunTracker
from src.olj.olj_scraper import scrape_olj


@dataclass(frozen=True)
class BoardRegistration:
    scraper: Callable[..., Any]
    tracker: Any
    is_slow: bool = False


BOARD_REGISTRY: dict[JobBoardEnum, BoardRegistration] = {
    JobBoardEnum.JobStreet: BoardRegistration(
        scraper=scrape_jobstreet, tracker=JobstreetRunTracker, is_slow=False
    ),
    JobBoardEnum.Indeed: BoardRegistration(
        scraper=scrape_indeed, tracker=IndeedRunTracker, is_slow=True
    ),
    JobBoardEnum.Olj: BoardRegistration(
        scraper=scrape_olj, tracker=OljRunTracker, is_slow=False
    ),
    JobBoardEnum.Mynimo: BoardRegistration(
        scraper=scrape_mynimo, tracker=MynimoRunTracker, is_slow=False
    ),
    JobBoardEnum.Kalibrr: BoardRegistration(
        scraper=scrape_kalibrr, tracker=KalibrrRunTracker, is_slow=False
    ),
    JobBoardEnum.Linkedin: BoardRegistration(
        scraper=scrape_linkedin, tracker=LinkedinRunTracker, is_slow=True
    ),
    JobBoardEnum.LinkedinPosts: BoardRegistration(
        scraper=scrape_linkedin_posts, tracker=LinkedinPostsRunTracker, is_slow=True
    ),
    JobBoardEnum.FacebookPosts: BoardRegistration(
        scraper=scrape_facebook_posts, tracker=FacebookPostsRunTracker, is_slow=True
    ),
}


def get_boards_by_speed(is_slow: bool) -> list[JobBoardEnum]:
    return [board for board, reg in BOARD_REGISTRY.items() if reg.is_slow == is_slow]
