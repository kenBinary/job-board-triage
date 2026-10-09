import logging
from pathlib import Path
from typing import Optional

LOG_DIR = Path(".data/logs")
LOG_FILE = LOG_DIR / "scraper.log"


def setup_logging(verbose: bool = False) -> None:
    """
    Configure application-wide logging.

    - Console output: INFO by default, DEBUG if verbose=True.
    - File output: Always DEBUG to .data/logs/scraper.log.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    if root_logger.handlers:
        root_logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_level = logging.DEBUG if verbose else logging.INFO
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("camoufox").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured under the root logger."""
    return logging.getLogger(name)


def format_job_log(
    board: str,
    title: str,
    company: Optional[str] = None,
    salary: Optional[str] = None,
    location: Optional[str] = None,
    page_info: Optional[str] = None,
    item_info: Optional[str] = None,
) -> str:
    """
    Standardizes job formatting into a compact single-line format:
    [{board}] [page {p}/{max_p}] [{idx}/{total}] {title} | {company} | {salary} | {location}
    """
    parts = [f"[{board}]"]
    if page_info:
        parts.append(f"[{page_info}]")
    if item_info:
        parts.append(f"[{item_info}]")

    title_str = title.strip() if title else "Untitled"
    company_str = company.strip() if company else "N/A"
    salary_str = salary.strip() if salary else "N/A"
    location_str = location.strip() if location else "N/A"

    details = f"{title_str} | {company_str} | {salary_str} | {location_str}"
    parts.append(details)

    return " ".join(parts)
