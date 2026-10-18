import json
from typing import List, Optional
from pathlib import Path

from src.common.settings import settings
from src.common.enums.job_board import JobBoardEnum
from src.common.error_tracker import ConsecutiveErrorTracker
from src.common.logger import get_logger
from src.kalibrr.models.kalibrr_link import KalibrrLink

logger = get_logger("kalibrr_tracker")


class KalibrrRunTracker(ConsecutiveErrorTracker):
    _RETRY_STATE_DIR = Path(".data/retry_state")
    _FILE_PATH = _RETRY_STATE_DIR / f"{JobBoardEnum.Kalibrr}-failed-links.json"

    def __init__(self, links: List[KalibrrLink], is_retry_run: bool = False):
        super().__init__(
            board_name=JobBoardEnum.Kalibrr,
            max_errors=settings.max_consecutive_link_errors,
        )
        self.links = links
        self.halted = False
        self.current_index = 0
        self.is_retry_run = is_retry_run
        self.failed_links: List[KalibrrLink] = []

    def set_current_index(self, index: int) -> None:
        self.current_index = index

    def record_success(self) -> None:
        super().record_success()
        if self.is_retry_run and self._FILE_PATH.exists():
            remaining_links = self.links[self.current_index + 1 :]
            self._save_retry_links(remaining_links)

    def record_link_error(
        self,
        link: KalibrrLink,
        error: Optional[Exception] = None,
    ) -> bool:
        self.failed_links.append(link)

        should_halt = super().record_error(error=error)
        if should_halt:
            self.halted = True
            self._save_halt_state()
        return should_halt

    def _save_halt_state(self) -> None:
        remaining_unvisited = (
            self.links[self.current_index + 1 :]
            if self.current_index + 1 < len(self.links)
            else []
        )
        combined = self.failed_links + remaining_unvisited
        self._save_retry_links(combined)
        logger.info(
            f"[{self.board_name}] Saved {len(combined)} link(s) to retry state: {self._FILE_PATH}"
        )

    def _save_retry_links(self, links: List[KalibrrLink]) -> None:
        if not self._RETRY_STATE_DIR.exists():
            self._RETRY_STATE_DIR.mkdir(parents=True, exist_ok=True)

        if not links:
            self.clear_retry_state()
            return
        data = [link.to_json() for link in links]
        self._FILE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load_retry_links(cls) -> Optional[List[KalibrrLink]]:
        if not cls._FILE_PATH.exists():
            return None
        try:
            data = json.loads(cls._FILE_PATH.read_text(encoding="utf-8"))
            if not isinstance(data, list) or not data:
                return None
            return [KalibrrLink.from_json(item) for item in data]
        except Exception as e:
            logger.error(
                f"[KALIBRR] Failed to load retry links from {cls._FILE_PATH}: {e}"
            )
            return None

    @classmethod
    def clear_retry_state(cls) -> None:
        if cls._FILE_PATH.exists():
            try:
                cls._FILE_PATH.unlink()
            except OSError as e:
                logger.warning(
                    f"[KALIBRR] Warning: failed to delete {cls._FILE_PATH}: {e}"
                )

    def finalize(self) -> None:
        if self.halted:
            return

        if self.failed_links:
            self._save_retry_links(self.failed_links)
            logger.warning(
                f"[{self.board_name}] Saved {len(self.failed_links)} failed link(s) to retry state: {self._FILE_PATH}"
            )
        elif self.is_retry_run:
            self.clear_retry_state()
            logger.info(
                f"[{self.board_name}] All retry links completed successfully. Cleared retry state."
            )

    @classmethod
    def has_retry_links(cls) -> bool:
        """Return True if a non-empty retry state file exists for the board."""
        if not cls._FILE_PATH.exists():
            return False
        try:
            content = json.loads(cls._FILE_PATH.read_text(encoding="utf-8"))
            return isinstance(content, list) and len(content) > 0
        except Exception:
            return False

    @classmethod
    def get_retry_count(cls) -> int:
        """Return number of saved links in the retry file for the board."""
        if not cls._FILE_PATH.exists():
            return 0
        try:
            content = json.loads(cls._FILE_PATH.read_text(encoding="utf-8"))
            return len(content) if isinstance(content, list) else 0
        except Exception:
            return 0
