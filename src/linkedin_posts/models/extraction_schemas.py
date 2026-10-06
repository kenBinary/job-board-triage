from typing import Literal, Optional
from pydantic import BaseModel, Field

JobCategory = Literal[
    "Engineering & IT",
    "Sales & Marketing",
    "Operations & Administration",
    "Finance & Legal",
    "Product & Design",
    "Customer Service",
    "Healthcare & Life Sciences",
    "Trades, Labor & Field Services",
    "Others",
]


class ExtractedJobListing(BaseModel):
    """A single job opening extracted from a LinkedIn post."""

    title: str = Field(description="Job title or role name.")
    company_name: Optional[str] = Field(
        default=None, description="Hiring company name, if mentioned."
    )
    location: Optional[str] = Field(
        default=None,
        description="Location of the job (city, country, or 'Philippines' if general).",
    )
    work_type: Optional[str] = Field(
        default=None,
        description="Work arrangement: 'Remote', 'Hybrid', 'On-site', or None if unspecified.",
    )
    short_description: str = Field(
        default="",
        description="A brief one-to-two sentence summary of the job role.",
    )
    description: str = Field(
        default="",
        description=(
            "Full extracted job description, including responsibilities, "
            "qualifications, and any other relevant details from the post."
        ),
    )
    salary_min: Optional[float] = Field(
        default=None,
        description="Minimum salary value (numeric, no currency symbol). Null if not mentioned.",
    )
    salary_max: Optional[float] = Field(
        default=None,
        description="Maximum salary value (numeric, no currency symbol). Null if not mentioned.",
    )
    salary_currency: Optional[str] = Field(
        default=None,
        description="Currency code (e.g. 'PHP', 'USD'). Null if not mentioned.",
    )
    salary_period: Optional[str] = Field(
        default=None,
        description="Pay frequency: 'hourly', 'monthly', or 'yearly'. Null if not mentioned.",
    )
    contact_email: Optional[str] = Field(
        default=None,
        description="Contact email address for applying, if present in the post.",
    )
    contact_link: Optional[str] = Field(
        default=None,
        description="Application or contact URL/link mentioned in the post, if any.",
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


class PostJobExtractionResult(BaseModel):
    """Top-level structured output from the LLM for a single LinkedIn post."""

    is_job_post: bool = Field(
        description=(
            "True if this LinkedIn post is advertising one or more job openings. "
            "False if it is not a job post (e.g. news, opinion, event)."
        )
    )
    jobs: list[ExtractedJobListing] = Field(
        default_factory=list,
        description=(
            "List of job openings extracted from the post. "
            "Should be empty if is_job_post is False. "
            "Can have multiple entries if the post advertises multiple roles."
        ),
    )
