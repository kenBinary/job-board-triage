import math
from typing import Generic, Optional, TypeVar
import uuid
from attr import dataclass
from sqlalchemy import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.db.database import BaseEntity


@dataclass(slots=True)
class PaginatedList[T]:
    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        return math.ceil(self.total / self.page_size) if self.page_size > 0 else 0

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1


class JobDetails(BaseEntity):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str]
    company_name: Mapped[Optional[str]] = mapped_column(default=None)
    location: Mapped[Optional[str]] = mapped_column(default=None)
    url: Mapped[Optional[str]] = mapped_column(default=None)
    short_description: Mapped[str] = mapped_column(default="")
    description: Mapped[str] = mapped_column(default="")

    salary_min: Mapped[Optional[float]] = mapped_column(default=None)
    salary_max: Mapped[Optional[float]] = mapped_column(default=None)
    salary_currency: Mapped[Optional[str]] = mapped_column(default=None)
    salary_period: Mapped[Optional[str]] = mapped_column(default=None)

    work_type: Mapped[Optional[str]] = mapped_column(default=None)

    posted_at_utc: Mapped[Optional[str]] = mapped_column(default=None)
    is_new: Mapped[Optional[bool]] = mapped_column(default=True)
