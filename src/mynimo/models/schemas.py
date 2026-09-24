from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class JobParams(BaseModel):
    path: str
    page: str
    invalid: bool
    is_overseas: bool
    region_name: str
    main: int
    redirectURL: str
    category_parent: int
    category_id: Optional[int] = None
    job_level: Optional[str] = None
    subcategory_alias: Optional[str] = None
    category_operation: str
    typeQuery: str
    city_name: str
    tab: str


class SidebarRequest(BaseModel):
    path: str
    page: str
    invalid: bool
    is_overseas: bool
    region_name: str
    main: int
    redirectURL: str
    category_parent: int
    location_id: List[int]
    category_id: Optional[int] = None
    job_level: Optional[str] = None
    subcategory_alias: Optional[str] = None
    category_operation: str
    typeQuery: str


class NavigationItem(BaseModel):
    name: str
    display_name: str
    count: int
    job_vacancy_count: Optional[int] = None
    conditions: Optional[str] = None


class ParentCategoryItem(BaseModel):
    job_id: int
    id: int
    name: str
    job_count: int
    job_vacancy_count: int
    weight: int
    alias: str


class CategoryCountItem(BaseModel):
    job_count: int
    alias: str
    region_name: str
    name: str
    id: int
    weight: int
    job_vacancy_count: Optional[int] = None


class SidebarCategoryCount(BaseModel):
    parent_category: List[ParentCategoryItem]
    sub_category: List[Any]
    all: CategoryCountItem
    management: CategoryCountItem
    urgent: CategoryCountItem
    part_time: CategoryCountItem
    high_school: CategoryCountItem
    overseas: CategoryCountItem


class SidebarProvinceCount(BaseModel):
    job_id: int
    weight: int
    name: str
    location_id: int
    region_parent_id: int
    job_vacancy_count: int
    job_count: int


class SidebarLevelCount(BaseModel):
    job_id: int
    job_level: str
    pretty: str
    job_count: int
    job_vacancy_count: int


class EligibilityItem(BaseModel):
    eligibility: str
    pretty: str
    job_count: int
    job_vacancy_count: int


class SidebarEligibilityCount(BaseModel):
    pwd: EligibilityItem
    senior: EligibilityItem


class Sidebar(BaseModel):
    sidebarCategoryCount: SidebarCategoryCount
    sidebarProvinceCount: List[SidebarProvinceCount]
    sidebarLevelCount: List[SidebarLevelCount]
    sidebarEligibilityCount: SidebarEligibilityCount
    key: str
    request: SidebarRequest


class JobItem(BaseModel):
    job_location_id: int
    location_name: str
    location_parent_name: str
    barangay_name: Optional[str] = None
    lack_documents: int

    # --- CHANGE THESE TWO LINES ---
    size: Optional[str] = None
    year_established: Optional[int] = None
    # ------------------------------

    jobs_id: int
    starts: str
    scheduled: int
    id: int
    title: str
    package: str
    urgent: int
    max_salary: int
    min_salary: int
    part_time: int
    high_school: int
    work_from_home: int
    job_level: str
    company: str
    overseas_location: str
    tagging: str
    content: str

    # Fields present in regular job items but optional/absent in priorities
    starts_iso: Optional[str] = None
    hide_salary: Optional[int] = None
    direct_employer: Optional[str] = None
    logo: Optional[str] = None
    last_updated_date: Optional[str] = None
    num_vacancies: Optional[Union[int, str]] = None
    is_pwd: Optional[int] = None
    is_senior_citizen: Optional[int] = None
    tagging_object: Optional[Dict[str, str]] = None


class JobPaginationResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    current_page: int
    data: List[JobItem]
    first_page_url: HttpUrl
    from_: Optional[int] = Field(default=None, alias="from")
    last_page: int
    last_page_url: HttpUrl
    next_page_url: Optional[HttpUrl] = None
    path: HttpUrl
    per_page: int
    prev_page_url: Optional[HttpUrl] = None
    to: Optional[int] = None
    total: int


class JobsContainer(BaseModel):
    result: JobPaginationResult


class SeoMessage(BaseModel):
    id: int
    type: str
    location_id: int
    category_id: int
    position: str
    status: str
    message: str
    updated: str
    created: str
    user_id: int
    urgent: int
    tag: str


class JobSearchData(BaseModel):
    params: JobParams
    navigation: List[NavigationItem]
    sidebar: Sidebar
    jobs: JobsContainer
    priorities: Optional[JobItem] = None
    seomessage: List[SeoMessage]


class MynimoResponse(BaseModel):
    message: str
    error: bool
    data: JobSearchData
    result: Any
