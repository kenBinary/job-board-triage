from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BaseInfiniteScrollModel(ABC):
    """Base class for models handling infinite scrolling pages.

    Subclasses define URL construction via `get_url()` while the scraper
    retains full control over scroll mechanics, delays, and stop conditions.

    Attributes:
        base_url (str): The starting URL.
        max_scrolls (int): Maximum number of scroll attempts before stopping.
    """

    base_url: str
    max_scrolls: int = 10

    @abstractmethod
    def get_url(self) -> str:
        """Construct and return the target URL for infinite scrolling."""
        pass

    def should_continue(self, current_scrolls: int) -> bool:
        """Return True if scrolling should continue based on current scroll count."""
        return current_scrolls < self.max_scrolls
