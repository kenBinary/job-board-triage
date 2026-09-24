from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, HttpUrl


class Company(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None
    id: int
    industry: Optional[str] = None
    logo_small: Optional[HttpUrl | str] = None
    name: str
    verified_business: bool
    visible: bool


class CompanyInfo(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None
    hidden: bool = False
    industry: Optional[str] = None
    is_demo: bool
    logo: Optional[HttpUrl | str] = None
    logo_1200x630: Optional[HttpUrl | str] = None
    logo_160x90: Optional[HttpUrl | str] = None
    logo_small: Optional[HttpUrl | str] = None
    name: str
    url: Optional[HttpUrl | str] = None


class AddressComponents(BaseModel):
    address_line_1: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None


class GoogleLocation(BaseModel):
    address_components: Optional[AddressComponents] = None


class Perks(BaseModel):
    other: Optional[str] = None
    types: List[str] = []


class SdsSkill(BaseModel):
    created_at: Optional[datetime] = None
    custom: bool
    id: int
    name: str
    updated_at: Optional[datetime] = None


class JobSdsSkill(BaseModel):
    created_at: Optional[datetime] = None
    job_id: int
    sds_skill: SdsSkill
    sds_skill_id: int


class Job(BaseModel):
    id: int
    name: str
    slug: str
    activation_date: Optional[datetime] = None
    application_end_date: Optional[datetime] = None
    apply_redirect_url: Optional[HttpUrl | str] = None
    created_at: Optional[datetime] = None

    base_salary: Optional[float] = None
    maximum_salary: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_interval: Optional[str] = None
    salary_shown: bool

    company: Company
    company_info: CompanyInfo
    company_name: str

    description: Optional[str] = None
    qualifications: Optional[str] = None
    function: Optional[str] = None
    tenure: Optional[str] = None
    number_of_openings: Optional[int] = 1
    education_level: Optional[int] = None
    work_experience: Optional[int] = None

    google_location: Optional[GoogleLocation] = None
    distance_from_user: Optional[float] = None
    is_work_from_home: bool
    is_hybrid: bool
    is_open_to_fresh_grads: bool

    bookmarked: bool
    is_featured: bool
    visibility: str
    priority_score: Optional[float] = None
    response_rate: Optional[float] = None
    es_is_top_brand: bool
    es_recruiter_last_seen: Optional[datetime] = None

    perks: Optional[Perks] = None
    photo_urls: List[HttpUrl | str] = []
    job_sds_skills: List[JobSdsSkill] = []
    exam_versions: List[Any] = []


class KalibrrJobSearchResponse(BaseModel):
    count: int
    jobs: List[Job]
    search_text: Optional[str] = None
    correction_text_search: Optional[str] = None
    from_alternative: bool
    from_correction: bool
