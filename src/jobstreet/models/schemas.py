from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LocalizedText(BaseModel):
    lang: Optional[str] = None
    text: str
    typename: Optional[str] = Field(None, alias="__typename")


class LocationNode(BaseModel):
    id: Optional[str] = None
    kind: Optional[str] = None
    label: Optional[LocalizedText] = None
    contextualName: Optional[LocalizedText] = None
    contextualNameLocalisations: Optional[List[LocalizedText]] = None
    isGranular: Optional[bool] = None
    defaultDistanceKms: Optional[int] = None
    typename: Optional[str] = Field(None, alias="__typename")


class Advertiser(BaseModel):
    id: str
    name: str
    typename: Optional[str] = Field(None, alias="__typename")


class Organisation(BaseModel):
    id: str
    name: str
    companyProfileId: Optional[str] = None
    companyProfileUrl: Optional[str] = None
    companyProfileRelativeUrlToBeUsedWithZone: Optional[str] = None
    typename: Optional[str] = Field(None, alias="__typename")


class Category(BaseModel):
    id: str
    label: Optional[str] = None
    typename: Optional[str] = Field(None, alias="__typename")


class JobLocation(BaseModel):
    id: Optional[str] = None
    displayName: Optional[LocalizedText] = None
    seoHierarchy: Optional[List[LocationNode]] = None
    typename: Optional[str] = Field(None, alias="__typename")


class CjsWorkType(BaseModel):
    sourceId: Optional[str] = None
    name: Optional[str] = None
    typename: Optional[str] = Field(None, alias="__typename")


class CjsSalary(BaseModel):
    hideSalary: Optional[bool] = None
    minimum: Optional[int] = None
    maximum: Optional[int] = None
    currency: Optional[str] = None
    period: Optional[str] = None
    displayValue: Optional[str] = None
    typename: Optional[str] = Field(None, alias="__typename")


class CjsProductBranding(BaseModel):
    companyLogoURL: Optional[str] = None
    typename: Optional[str] = Field(None, alias="__typename")


class CjsProduct(BaseModel):
    branding: Optional[CjsProductBranding] = None
    bullets: Optional[List[str]] = None
    adType: Optional[str] = None
    typename: Optional[str] = Field(None, alias="__typename")


class CjsRoleTitle(BaseModel):
    shortId: Optional[str] = None
    isDistinct: Optional[bool] = None
    typename: Optional[str] = Field(None, alias="__typename")


class JobCjs(BaseModel):
    workTypes: Optional[List[CjsWorkType]] = None
    source: Optional[Dict[str, Any]] = None
    salary: Optional[CjsSalary] = None
    roleTitles: Optional[List[CjsRoleTitle]] = None
    product: Optional[CjsProduct] = None
    externalReferences: Optional[Any] = None
    typename: Optional[str] = Field(None, alias="__typename")


class SeekDateTime(BaseModel):
    dateTimeUtc: Optional[str] = None
    label: Optional[str] = None
    typename: Optional[str] = Field(None, alias="__typename")


class JobSalary(BaseModel):
    period: Optional[str] = None
    min: Optional[int] = None
    max: Optional[int] = None
    currency: Optional[str] = None
    typename: Optional[str] = Field(None, alias="__typename")


class JobTag(BaseModel):
    type: str
    label: Optional[str] = None
    typename: Optional[str] = Field(None, alias="__typename")


class WorkArrangement(BaseModel):
    id: str
    label: Optional[LocalizedText] = None
    typename: Optional[str] = Field(None, alias="__typename")


class ActivityCount(BaseModel):
    count: Optional[int] = None
    mostRecent: Optional[SeekDateTime] = None
    typename: Optional[str] = Field(None, alias="__typename")


class JobActivity(BaseModel):
    visitedApplicationSite: Optional[ActivityCount] = None
    applicationEnds: Optional[ActivityCount] = None
    applicationStarts: Optional[ActivityCount] = None
    impressions: Optional[ActivityCount] = None
    jobDetails: Optional[ActivityCount] = None
    typename: Optional[str] = Field(None, alias="__typename")


class Job(BaseModel):
    id: str
    title: str
    abstract: Optional[str] = None
    adDisplay: Optional[str] = None
    advertiser: Optional[Advertiser] = None
    organisation: Optional[Organisation] = None
    categories: Optional[List[Category]] = None
    location: Optional[JobLocation] = None
    cjs: Optional[JobCjs] = None
    listedAt: Optional[SeekDateTime] = None
    salary: Optional[JobSalary] = None
    sol: Optional[Dict[str, Any]] = None
    tags: Optional[List[JobTag]] = None
    url: Optional[str] = None
    workArrangements: Optional[List[WorkArrangement]] = None
    activity: Optional[JobActivity] = None
    typename: Optional[str] = Field(None, alias="__typename")


class Pagination(BaseModel):
    page: int
    pageSize: int
    resultCount: int
    typename: Optional[str] = Field(None, alias="__typename")


class SearchResults(BaseModel):
    jobs: List[Job]
    pagination: Pagination
    typename: Optional[str] = Field(None, alias="__typename")


class RelatedSearch(BaseModel):
    totalJobs: int
    text: str
    typename: Optional[str] = Field(None, alias="__typename")


class QueryParamLabels(BaseModel):
    text: Optional[str] = None
    where: Optional[List[LocationNode]] = None
    locationsHierarchy: Optional[List[List[LocationNode]]] = None
    typename: Optional[str] = Field(None, alias="__typename")


class EnrichmentSuggestions(BaseModel):
    queryParamLabelsV1: Optional[QueryParamLabels] = None
    relatedSearchesV1: Optional[List[RelatedSearch]] = None
    organisationV1: Optional[Any] = None
    locationV1: Optional[Any] = None
    sabFilterV1: Optional[Dict[str, Any]] = None
    canonicalV1: Optional[Any] = None
    spellingCorrectionV1: Optional[Any] = None
    typename: Optional[str] = Field(None, alias="__typename")


class Enrichment(BaseModel):
    facets: Optional[Any] = None
    suggestions: Optional[EnrichmentSuggestions] = None
    typename: Optional[str] = Field(None, alias="__typename")


class JobSearchV7(BaseModel):
    results: SearchResults
    enrichment: Optional[Enrichment] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    typename: Optional[str] = Field(None, alias="__typename")


class GraphQLResponseData(BaseModel):
    jobSearchV7: JobSearchV7


class JobSearchResponse(BaseModel):
    data: GraphQLResponseData
