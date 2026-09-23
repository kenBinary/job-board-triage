from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class OljJobSchema(BaseModel):
    id: str = Field(..., description="Unique job identifier")
    title: str = Field(..., description="Job title")
    job_type: str = Field(..., description="Type of employment (e.g., Full Time)")
    link: str = Field(..., description="Relative or absolute URL to the job listing")
    author: str = Field(..., description="Company or author name posting the job")
    posted_date: datetime = Field(
        ..., description="Date and time when the job was posted"
    )
    salary: Optional[str] = Field(None, description="Salary offered for the role")
    description: str = Field(..., description="Job description")
    tags: Optional[list[str]] = Field(None, description="List of relevant skill tags")
