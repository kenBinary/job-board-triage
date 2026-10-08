from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Type, TypeVar

T = TypeVar("T", bound="BaseLinkModel")


@dataclass
class BaseLinkModel(ABC):
    """Base class for link models used in job scraping.

    Attributes:
        max_page (int): The maximum number of pages to scrape for a given link.
        base_url (str): The base URL for the job search.
    """

    max_page: int
    base_url: str

    @abstractmethod
    def get_next_page(self, page: int) -> str:
        pass

    @abstractmethod
    def to_json(self, indent: Optional[int] = None) -> str:
        """Serializes the model instance to a JSON string."""
        pass

    @classmethod
    @abstractmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """Deserializes a JSON string into an instance of the model."""
        pass
