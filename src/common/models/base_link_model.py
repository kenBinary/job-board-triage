from abc import ABC, abstractmethod

from dataclasses import dataclass


@dataclass
class BaseLinkModel(ABC):
    """Base class for link models used in job scraping.

    Attributes:
        max_pages (int): The maximum number of pages to scrape for a given link.
        base_url (str): The base URL for the job search.
    """

    max_page: int
    base_url: str

    @abstractmethod
    def get_next_page(self, page) -> str:
        pass
