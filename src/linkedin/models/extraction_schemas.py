from typing import Optional
from pydantic import BaseModel, Field

from src.common.constants.job_category import JobCategory


class ExtractedJobListing(BaseModel):
    """A single job opening extracted from a LinkedIn job card."""

    job_id: str = Field(description="Unique LinkedIn job ID (numeric string).")
    title: str = Field(description="Job title or role name.")
    company_name: Optional[str] = Field(
        default=None, description="Hiring company name, if present."
    )
    location: Optional[str] = Field(
        default=None,
        description="Location of the job (e.g. City, Country, or Region).",
    )
    work_type: Optional[str] = Field(
        default=None,
        description="Work arrangement: 'Remote', 'Hybrid', 'On-site', or null if unspecified.",
    )
    short_description: str = Field(
        default="",
        description="A brief 1-2 sentence summary of the role based on card text.",
    )
    salary_min: Optional[float] = Field(
        default=None,
        description="Minimum salary value (numeric only). Null if not mentioned.",
    )
    salary_max: Optional[float] = Field(
        default=None,
        description="Maximum salary value (numeric only). Null if not mentioned.",
    )
    salary_currency: Optional[str] = Field(
        default=None,
        description="Currency code (e.g. 'PHP', 'USD'). Null if not mentioned.",
    )
    salary_period: Optional[str] = Field(
        default=None,
        description="Pay frequency: 'hourly', 'monthly', or 'yearly'. Null if not mentioned.",
    )
    posted_date_utc: Optional[str] = Field(
        default=None,
        description=(
            "The date and time the job was posted, in"
            "ISO-8601 UTC string. Use the card screenshot for relative dates such "
            "as '2h' or 'Yesterday'. Null only when the date is unreadable."
        ),
    )
    is_early_applicant: Optional[bool] = Field(
        default=None,
        description="True if card indicates 'Be an early applicant' or early applicant status.",
    )
    category: JobCategory = Field(
        description=(
            "Job category. Choose one of: 'Engineering & IT' (Software, Hardware, "
            "Data, Systems), 'Sales & Marketing' (Growth, Account Execs, Advertising), "
            "'Operations & Administration' (HR, Office Support, Logistics), "
            "'Finance & Legal' (Accounting, Corporate, Compliance), "
            "'Product & Design' (UI/UX, Product Management, Creative), "
            "'Customer Service' (Support, Success), 'Healthcare & Life Sciences', "
            "'Trades, Labor & Field Services', or 'Others'."
        ),
    )


class BatchJobExtractionResult(BaseModel):
    """Structured output from LLM for a batch of LinkedIn job cards."""

    jobs: list[ExtractedJobListing] = Field(
        default_factory=list,
        description="List of extracted jobs corresponding to the input job cards.",
    )
