import asyncio
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Dict
import typer

from src.cli.board_registry import BOARD_REGISTRY
from src.common.enums.job_board import JobBoardEnum

# from src.common.infra.browser_context import CamoufoxSingleton
from src.common.infra.dependencies import infra_container
from src.common.logger import get_logger
from src.db.database import BaseEntity, engine

logger = get_logger("scraper_app")


class RetryMode(StrEnum):
    PROMPT = "prompt"
    FORCE_RETRY = "retry"
    FORCE_FRESH = "fresh"


@dataclass
class BoardConfig:
    links: list[Any] | None
    is_retry: bool


class ScraperOrchestrator:
    def resolve_board_config(self, board: JobBoardEnum, mode: RetryMode) -> BoardConfig:
        tracker = BOARD_REGISTRY[board].tracker
        has_retry = tracker.has_retry_links()
        count = tracker.get_retry_count() if has_retry else 0

        if mode == RetryMode.FORCE_FRESH:
            if has_retry:
                tracker.clear_retry_state()
                logger.info(f"[{board.value}] Cleared previous retry state.")
            return BoardConfig(links=None, is_retry=False)

        if mode == RetryMode.FORCE_RETRY:
            if has_retry:
                logger.info(f"[{board.value}] Resuming {count} link(s).")
                return BoardConfig(links=tracker.load_retry_links(), is_retry=True)
            logger.info(f"[{board.value}] No retry state found; running configured links.")
            return BoardConfig(links=None, is_retry=False)

        if has_retry:
            should_resume = typer.confirm(
                f"Found saved state for '{board.value}' ({count} remaining). Resume?",
                default=True,
            )
            if should_resume:
                logger.info(f"[{board.value}] Resuming {count} link(s).")
                return BoardConfig(links=tracker.load_retry_links(), is_retry=True)
            logger.info(f"[{board.value}] Starting fresh with default links.")

        return BoardConfig(links=None, is_retry=False)

    async def run(self, boards: list[JobBoardEnum], mode: RetryMode) -> None:
        BaseEntity.metadata.create_all(bind=engine)
        board_configs: Dict[JobBoardEnum, BoardConfig] = {
            b: self.resolve_board_config(b, mode) for b in boards
        }

        try:
            async with asyncio.TaskGroup() as tg:
                for board, config in board_configs.items():
                    scraper_fn = BOARD_REGISTRY[board].scraper
                    tg.create_task(
                        scraper_fn(links=config.links, is_retry=config.is_retry)
                    )
        finally:
            await infra_container.camoufox_provider.close_context()
