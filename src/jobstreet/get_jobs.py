import uuid
from typing import Any, Dict, List, Literal, Optional
from src.jobstreet.models.schemas import JobSearchResponse
from src.http_client import get_client

URL = "https://ph.jobstreet.com/graphql"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:156.0) Gecko/20100101 Firefox/156.0",
    "Accept": "application/graphql-response+json,application/json;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "x-custom-features": "application/features.seek.all+json",
    "seek-request-brand": "jobstreet",
    "seek-request-country": "PH",
}

GRAPHQL_QUERY = """
query JobSearchV7($params: JobSearchV7QueryInput!, $locale: Locale!, $zone: Zone!, $country: JobSearchV7Country!, $timezone: Timezone!, $tagsSubType: [JobSearchV7TagsSubType!]) {
  jobSearchV7(params: $params) {
    results {
      jobs {
        id
        title
        abstract
        adDisplay
        advertiser {
          id
          name
          __typename
        }
        organisation {
          id
          name
          companyProfileId
          companyProfileUrl
          companyProfileRelativeUrlToBeUsedWithZone
          __typename
        }
        categories {
          id
          label(locale: $locale)
          __typename
        }
        location {
          id
          displayName {
            text
            __typename
          }
          seoHierarchy {
            contextualName {
              text
              __typename
            }
            __typename
          }
          __typename
        }
        cjs {
          workTypes {
            sourceId
            name(locale: $locale)
            __typename
          }
          source {
            isAutoIncluded
            __typename
          }
          salary {
            hideSalary
            minimum
            maximum
            currency
            period
            displayValue
            __typename
          }
          roleTitles {
            shortId
            isDistinct
            __typename
          }
          product {
            branding {
              companyLogoURL
              __typename
            }
            bullets
            adType {
              sourceId
              __typename
            }
            __typename
          }
          externalReferences {
            id
            sourceSystem
            type
            metadata {
              name
              assets {
                profilePhotoUrl
                __typename
              }
              __typename
            }
            __typename
          }
          __typename
        }
        listedAt {
          dateTimeUtc
          label(context: JOB_POSTED, length: SHORT, timezone: $timezone, locale: $locale)
          __typename
        }
        salary {
          period
          min
          max
          currency
          __typename
        }
        sol
        tags(subType: $tagsSubType) {
          type
          label(locale: $locale)
          __typename
        }
        url
        workArrangements {
          id
          label {
            lang
            text
            __typename
          }
          __typename
        }
        activity {
          visitedApplicationSite {
            count
            mostRecent {
              dateTimeUtc
              __typename
            }
            __typename
          }
          applicationEnds {
            count
            mostRecent {
              dateTimeUtc
              __typename
            }
            __typename
          }
          applicationStarts {
            count
            mostRecent {
              dateTimeUtc
              __typename
            }
            __typename
          }
          impressions {
            count
            mostRecent {
              dateTimeUtc
              __typename
            }
            __typename
          }
          jobDetails {
            count
            mostRecent {
              dateTimeUtc
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
      pagination {
        page
        pageSize
        resultCount
        __typename
      }
      __typename
    }
    enrichment {
      facets {
        categoryV1 {
          id
          label {
            lang
            text
            __typename
          }
          count
          __typename
        }
        distinctTitleV1 {
          id
          label
          count
          __typename
        }
        __typename
      }
      suggestions {
        queryParamLabelsV1 {
          text
          where {
            id
            kind
            label {
              lang
              text
              __typename
            }
            contextualName {
              lang
              text
              __typename
            }
            contextualNameLocalisations(siteKey: $country) {
              lang
              text
              __typename
            }
            isGranular
            defaultDistanceKms
            __typename
          }
          locationsHierarchy {
            id
            kind
            label {
              lang
              text
              __typename
            }
            contextualName {
              lang
              text
              __typename
            }
            isGranular
            defaultDistanceKms
            __typename
          }
          __typename
        }
        relatedSearchesV1 {
          totalJobs
          text
          __typename
        }
        organisationV1 {
          organisationId
          organisationName
          totalJobs
          __typename
        }
        locationV1 {
          local {
            sequence
            completions {
              id
              label(locale: $locale, zone: $zone, context: CONTEXTUAL_NAME, labelType: SHORT)
              __typename
            }
            __typename
          }
          international {
            sequence
            completions {
              id
              label(locale: $locale, zone: $zone, context: CONTEXTUAL_NAME, labelType: SHORT)
              __typename
            }
            __typename
          }
          __typename
        }
        sabFilterV1 {
          showSABFilter
          __typename
        }
        canonicalV1 {
          text
          where {
            id
            name
            __typename
          }
          __typename
        }
        spellingCorrectionV1 {
          type
          count
          searchToken
          label {
            lang
            defaultText
            __typename
          }
          intent {
            country
            locale
            text
            where
            whereId
            sort
            distanceKms
            filter {
              advertiserId
              categoryId
              listedAt
              organisationId
              organisationName
              salaryMin
              salaryMax
              tags
              workTypeId
              workArrangementId
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
      __typename
    }
    context {
      searchToken
      filterNewSince
      representations {
        uiV1 {
          country
          locale
          text
          where
          whereId
          sort
          distanceKms
          filter {
            advertiserId
            categoryId
            listedAt
            organisationId
            organisationName
            salaryMin
            salaryMax
            tags
            workTypeId
            workArrangementId
            __typename
          }
          __typename
        }
        __typename
      }
      __typename
    }
    metadata {
      flight
      request {
        correlationId
        __typename
      }
      sol
      __typename
    }
    __typename
  }
}
"""


from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional
import uuid
from enum import Enum


class WorkArrangementEnum(str, Enum):
    ONSITE = "1"
    HYBRID = "2"
    REMOTE = "3"


@dataclass
class JobSearchParams:
    """Parameters for querying job listings from JobStreet / SEEK via GraphQL.

    Attributes:
        text: Search query or job title (e.g., "frontend developer",
            "data analyst", or "" to match all jobs).
        where: Target location array. Defaults to `["Philippines"]` if None.
            Examples: `["Taguig"]`, `["Cebu City"]`, `["Metro Manila"]`.
        distance_kms: Search radius in kilometers around `where`.
            Examples: 10, 25, 50.
        sort: Result ordering criteria.
            - "listedAt": Newest jobs first (Date posted).
            - "score": Relevance to the search query.
        listed_at: Age filter for job postings.
            - None: No filter (all jobs).
            - "1d": Jobs posted in the last 24 hours.
            - "3d": Jobs posted in the last 3 days.
            - "7d": Jobs posted in the last 7 days.
            - "14d": Jobs posted in the last 14 days.
            - "30d": Jobs posted in the last 30 days.
        work_arrangement_ids: Working arrangement identifiers:
            - ["1"]: On-site
            - ["2"]: Hybrid
            - ["3"]: Remote / Work from home
            Can be combined, e.g., `["2", "3"]`.
        salary_min: Minimum compensation filter (e.g., 50000).
        salary_max: Maximum compensation filter (e.g., 100000).
        work_type_ids: Employment type IDs (e.g., Full-time, Part-time, Contract).
        category_ids: Job industry/classification IDs (e.g., IT/Software).
        organisation_id: Unique identifier for a specific employer/company.
        organisation_name: Name of a specific employer/company.
        page: Page number for pagination (1-indexed: 1, 2, 3, ...).
        page_size: Number of jobs returned per page (default: 30).
            Higher values (e.g., 50 or 100) are subject to backend limits.
        country: Country code (e.g., "PH", "MY", "SG", "ID").
            Also sets the `seek-request-country` HTTP header.
        locale: Regional locale string (e.g., "en-PH", "en-MY").
        zone: SEEK/JobStreet infrastructure deployment zone (e.g., "asia-6").
        timezone: Regional timezone (e.g., "Asia/Manila", "Asia/Kuala_Lumpur").
        auth_token: Bearer JWT token override without the "Bearer " prefix.
            If omitted, uses the built-in default token.
    """

    text: str = ""
    where: Optional[List[str]] = None
    distance_kms: int = 50
    sort: Literal["listedAt", "score"] = "listedAt"
    listed_at: Literal[None, "1d", "3d", "7d", "14d", "30d"] = "7d"
    work_arrangement_ids: Optional[List[WorkArrangementEnum]] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    work_type_ids: Optional[List[str]] = None
    category_ids: Optional[List[str]] = None
    organisation_id: Optional[str] = None
    organisation_name: Optional[str] = None
    page: int = 1
    page_size: int = 30
    country: str = "PH"
    locale: str = "en-PH"
    zone: str = "asia-6"
    timezone: str = "Asia/Manila"
    auth_token: Optional[str] = None


async def fetch_jobs(
    params: Optional[JobSearchParams] = None,
) -> JobSearchResponse:
    """Fetches job listings from JobStreet / SEEK via GraphQL.

    Args:
        params: Job search options and query filters. Uses defaults if omitted.

    Returns:
        JobSearchResponse: Strongly-typed Pydantic model populated from the GraphQL response.

    Raises:
        httpx.HTTPStatusError: If the HTTP request returns an error status code (4xx or 5xx).
        pydantic.ValidationError: If the response payload fails Pydantic schema validation.
    """
    if params is None:
        params = JobSearchParams()

    where = params.where if params.where is not None else ["Philippines"]

    filter_data: Dict[str, Any] = {}
    if params.listed_at:
        filter_data["listedAt"] = params.listed_at
    if params.work_arrangement_ids:
        filter_data["workArrangementId"] = params.work_arrangement_ids
    if params.salary_min is not None:
        filter_data["salaryMin"] = params.salary_min
    if params.salary_max is not None:
        filter_data["salaryMax"] = params.salary_max
    if params.work_type_ids:
        filter_data["workTypeId"] = params.work_type_ids
    if params.category_ids:
        filter_data["categoryId"] = params.category_ids
    if params.organisation_id:
        filter_data["organisationId"] = params.organisation_id
    if params.organisation_name:
        filter_data["organisationName"] = params.organisation_name

    payload = {
        "operationName": "JobSearchV7",
        "variables": {
            "params": {
                "searchIntent": {
                    "country": params.country,
                    "locale": params.locale,
                    "text": params.text,
                    "where": where,
                    "distanceKms": params.distance_kms,
                    "filter": filter_data,
                    "sort": params.sort,
                },
                "searchContext": {
                    "brand": "jobstreet",
                    "channel": "web",
                    "solVisitorId": str(uuid.uuid4()),
                    "intent": "SEARCH",
                    "source": "FE_SERP",
                },
                "responseConfig": {
                    "results": ["jobs"],
                    "representations": ["uiV1"],
                    "page": params.page,
                    "pageSize": params.page_size,
                    "enrichment": {
                        "suggestions": [
                            "locationV1",
                            "queryParamLabelsV1",
                            "sabFilterV1",
                            "organisationV1",
                            "spellingCorrectionV1",
                            "relatedSearchesV1",
                        ],
                        "relatedSearchesCount": 12,
                    },
                },
                "sessionId": str(uuid.uuid4()),
            },
            "locale": params.locale,
            "zone": params.zone,
            "timezone": params.timezone,
            "country": params.country,
            "tagsSubType": ["VSAB"],
        },
        "extensions": {
            "clientLibrary": {
                "name": "@apollo/client",
                "version": "4.2.9",
            }
        },
        "query": GRAPHQL_QUERY,
    }

    headers = DEFAULT_HEADERS.copy()
    headers["seek-request-country"] = params.country
    if params.auth_token:
        headers["Authorization"] = f"Bearer {params.auth_token}"

    client = get_client()
    response = await client.post(URL, headers=headers, json=payload)
    response.raise_for_status()

    return JobSearchResponse.model_validate(response.json())
