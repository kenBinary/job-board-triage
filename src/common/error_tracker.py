from typing import Optional
from src.common.settings import settings
from src.common.logger import get_logger

logger = get_logger("error_tracker")


class ConsecutiveErrorTracker:
    def __init__(
        self,
        board_name: str,
        max_errors: int = settings.max_consecutive_link_errors,
    ):
        self.board_name = board_name
        self.max_errors = max_errors
        self.consecutive_errors = 0

    def record_success(self) -> None:
        self.consecutive_errors = 0

    def record_error(self, error: Optional[Exception] = None) -> bool:
        """
        Record a failure for the current link target.

        Returns True if the consecutive error threshold has been reached
        (caller should stop scraping this board).
        """
        self.consecutive_errors += 1
        logger.warning(
            f"[{self.board_name}] Consecutive link error "
            f"{self.consecutive_errors}/{self.max_errors}."
        )
        if error:
            logger.warning(f"[{self.board_name}] Error details: {error}")
        if self.consecutive_errors >= self.max_errors:
            logger.error(
                f"[STOP] {self.max_errors} consecutive links failed for "
                f"{self.board_name}. Stopping {self.board_name} scraping."
            )
            return True
        return False
