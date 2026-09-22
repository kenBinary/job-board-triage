from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------------------------------
# Generic Base Model Setup
# --------------------------------------------------------------------------
class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


# --------------------------------------------------------------------------
# Browser / Device / Proctor Models
# --------------------------------------------------------------------------
class VersionDetail(BaseSchema):
    matchPrecision: Optional[str] = None
    originalVersionString: Optional[str] = None
    version: Optional[int | str] = None


class OSVersionDetail(BaseSchema):
    family: Optional[str] = None
    majorVersion: Optional[int] = None
    minorVersion: Optional[int] = None
    osFamily: Optional[str] = None
    osVersion: Optional[VersionDetail] = None
    patchVersion: Optional[int] = None
    releaseVersion: Optional[VersionDetail] = None
    version: Optional[str] = None


class UserAgentField(BaseSchema):
    confidence: Optional[int] = None
    defaultValue: Optional[str] = None
    isDefaultValue: Optional[bool] = None
    value: Optional[str] = None


class ProctorContext(BaseSchema):
    accountId: Optional[int] = None
    adFormat: Optional[str] = None
    app: Optional[bool] = None
    country: Optional[str] = None
    ctkAge: Optional[int] = None
    ctkDate: Optional[str] = None
    hasRez: Optional[bool] = None
    lang: Optional[str] = None
    loggedIn: Optional[bool] = None
    mtkAge: Optional[int] = None
    platform: Optional[str] = None
    privileged: Optional[bool] = None
    smartphone: Optional[bool] = None
    stealthGroups: List[Any] = Field(default_factory=list)
    tablet: Optional[bool] = None
    uaData: Optional[str] = None  # Stringified JSON in original payload


class ProctorIdentifiers(BaseSchema):
    ACCOUNT: Optional[str] = None
    USER: Optional[str] = None


class ProctorGroupPayload(BaseSchema):
    map: Optional[Dict[str, Any]] = None
    stringValue: Optional[str] = None
    stringArray: Optional[List[str]] = None
    longValue: Optional[int] = None
    longArray: Optional[List[int]] = None
    doubleValue: Optional[float] = None
    doubleArray: Optional[List[float]] = None
    json_: Optional[Any] = Field(None, alias="json")


class ProctorGroup(BaseSchema):
    group: Optional[str] = None
    value: Optional[int] = None
    allocationId: Optional[str] = None
    identifier: Optional[str] = None
    isLogged: Optional[bool] = None
    rolledOutAllocation: Optional[bool] = None
    silent: Optional[bool] = None
    testType: Optional[str] = None
    forceLogging: Optional[bool] = None
    payload: Optional[ProctorGroupPayload] = None


# --------------------------------------------------------------------------
# Query Modifiers
# --------------------------------------------------------------------------
class QueryModifier(BaseSchema):
    clickUrl: Optional[str] = None
    newQuery: Optional[str] = None


class QueryModifierResult(BaseSchema):
    originalQuery: Optional[str] = None
    queryModifiers: List[QueryModifier] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Job Card Models
# --------------------------------------------------------------------------
class TaxoEntityMatch(BaseSchema):
    displayText: Optional[str] = None
    id: Optional[str] = None
    rawName: Optional[str] = None
    source: Optional[str] = None
    strictness: Optional[str] = None
    suid: Optional[str] = None


class JobSeekerMatchSummaryModel(BaseSchema):
    sortedEntityDisplayText: List[str] = Field(default_factory=list)
    sortedMatchingEntityDisplayText: List[str] = Field(default_factory=list)
    sortedMisMatchingEntityDisplayText: List[str] = Field(default_factory=list)
    taxoEntityMatchesNegative: List[TaxoEntityMatch] = Field(default_factory=list)
    taxoEntityMatchesPositive: List[TaxoEntityMatch] = Field(default_factory=list)
    trafficLight: Optional[str] = None


class JobCardRequirementsModel(BaseSchema):
    additionalRequirementsCount: Optional[int] = 0
    jobOnlyRequirements: List[Any] = Field(default_factory=list)
    jobTagRequirements: List[Any] = Field(default_factory=list)
    requirementsHeaderShown: Optional[bool] = False
    screenerQuestionRequirements: List[Any] = Field(default_factory=list)


class MouseDownHandlerOption(BaseSchema):
    adId: Optional[str | int] = None
    advn: Optional[str] = None
    extractTrackingUrls: List[Any] = Field(default_factory=list)
    from_: Optional[str] = Field(None, alias="from")
    jobKey: Optional[str] = None
    link: Optional[str] = None
    tk: Optional[str] = None


class RankingScoresModel(BaseSchema):
    bid: Optional[float] = None
    bidPosition: Optional[int] = None
    eApply: Optional[float] = None
    eAttainability: Optional[float] = None
    eQualified: Optional[float] = None


class SalarySnippet(BaseSchema):
    currency: Optional[str] = None
    salaryTextFormatted: Optional[bool] = False
    source: Optional[str] = None
    text: Optional[str] = None


class TaxonomyAttributeItem(BaseSchema):
    label: Optional[str] = None
    suid: Optional[str] = None


class TaxonomyAttribute(BaseSchema):
    attributes: List[TaxonomyAttributeItem] = Field(default_factory=list)
    label: Optional[str] = None


class ExtractedSalary(BaseSchema):
    min: Optional[float] = None
    max: Optional[float] = None
    type: Optional[str] = None


class JobCard(BaseSchema):
    appliedOrGreater: Optional[bool] = False
    applyCount: Optional[int] = 0
    assistedApply: Optional[bool] = False
    autoSourcerJob: Optional[bool] = False
    bidPosition: Optional[int] = -1
    blobKey: Optional[str] = None
    company: Optional[str] = None
    companyIdEncrypted: Optional[str] = None
    companyRating: Optional[float] = 0.0
    companyReviewCount: Optional[int] = 0
    country: Optional[str] = None
    createDate: Optional[int] = None
    d2iEnabled: Optional[bool] = False
    displayTitle: Optional[str] = None
    dradisJob: Optional[bool] = False
    employerAssistEnabled: Optional[bool] = False
    employerResponsive: Optional[bool] = False
    encryptedFccompanyId: Optional[str] = None
    encryptedResultData: Optional[str] = None
    enhancedAttributesModel: Optional[Dict[str, Any]] = Field(default_factory=dict)
    enticers: List[Any] = Field(default_factory=list)
    expired: Optional[bool] = False
    extractTrackingUrls: Optional[str] = None
    extractedSalary: Optional[ExtractedSalary] = None
    fccompanyId: Optional[int] = None
    featuredCompanyAttributes: Optional[Dict[str, Any]] = Field(default_factory=dict)
    featuredEmployer: Optional[bool] = False
    featuredEmployerCandidate: Optional[bool] = False
    feedId: Optional[int] = None
    formattedLocation: Optional[str] = None
    formattedRelativeTime: Optional[str] = None
    gatedVjp: Optional[bool] = False
    hideMetaData: Optional[bool] = False
    highVolumeHiringModel: Optional[Dict[str, Any]] = Field(default_factory=dict)
    hiringEventJob: Optional[bool] = False
    homepageJobFeedSectionId: Optional[str] = None
    indeedApplyEnabled: Optional[bool] = False
    indeedApplyFinishAppUrlEnabled: Optional[bool] = False
    indeedApplyResumeType: Optional[str] = None
    indeedApplyable: Optional[bool] = False
    isJobVisited: Optional[bool] = False
    isMobileThirdPartyApplyable: Optional[bool] = False
    isNoResumeJob: Optional[bool] = False
    isSubsidiaryJob: Optional[bool] = False
    isTopRatedEmployer: Optional[bool] = False
    jobCardRequirementsModel: Optional[JobCardRequirementsModel] = None
    jobFlairPackageEnabled: Optional[bool] = False
    jobLocationCity: Optional[str] = None
    jobLocationState: Optional[str] = None
    jobSeekerMatchSummaryModel: Optional[JobSeekerMatchSummaryModel] = None
    jobTypes: List[str] = Field(default_factory=list)
    jobkey: Optional[str] = None
    jsiEnabled: Optional[bool] = False
    link: Optional[str] = None
    locationCount: Optional[int] = 1
    minimumCount: Optional[int] = 1
    mobtk: Optional[str] = None
    moreLocUrl: Optional[str] = None
    mouseDownHandlerOption: Optional[MouseDownHandlerOption] = None
    newJob: Optional[bool] = False
    normTitle: Optional[str] = None
    numHires: Optional[int] = -1
    openInterviewsInterviewsOnTheSpot: Optional[bool] = False
    openInterviewsJob: Optional[bool] = False
    openInterviewsOffersOnTheSpot: Optional[bool] = False
    openInterviewsPhoneJob: Optional[bool] = False
    organicApplyStartCount: Optional[int] = 0
    organicBlob: Optional[str] = None
    overrideIndeedApplyText: Optional[bool] = False
    packageTier: Optional[str] = None
    preciseLocationModel: Optional[Dict[str, Any]] = Field(default_factory=dict)
    pubDate: Optional[int] = None
    rankedBenefits: Optional[Dict[str, Any]] = Field(default_factory=dict)
    rankingScoresModel: Optional[RankingScoresModel] = None
    recommendationReasonModel: Optional[Dict[str, Any]] = Field(default_factory=dict)
    redirectToThirdPartySite: Optional[bool] = False
    remoteLocation: Optional[bool] = False
    resultBeforeExpansion: Optional[bool] = False
    resumeMatch: Optional[bool] = False
    salarySnippet: Optional[SalarySnippet] = None
    saved: Optional[bool] = False
    savedApplication: Optional[bool] = False
    screenerQuestionsURL: Optional[str] = None
    searchUID: Optional[str] = None
    showCommutePromo: Optional[bool] = False
    showEarlyApply: Optional[bool] = False
    showJobType: Optional[bool] = False
    showRelativeDate: Optional[bool] = False
    showStrongerAppliedLabel: Optional[bool] = False
    smartFillEnabled: Optional[bool] = False
    smbD2iEnabled: Optional[bool] = False
    snippet: Optional[str] = ""
    sourceId: Optional[int] = None
    sponsored: Optional[bool] = False
    taxoAttributes: List[Any] = Field(default_factory=list)
    taxoAttributesDisplayLimit: Optional[int] = 0
    taxoLogAttributes: List[Any] = Field(default_factory=list)
    taxonomyAttributes: List[TaxonomyAttribute] = Field(default_factory=list)
    thirdPartyApplyUrl: Optional[str] = None
    tier: Optional[Dict[str, Any]] = Field(default_factory=dict)
    title: Optional[str] = None
    translatedAttributes: List[Any] = Field(default_factory=list)
    translatedCmiJobTags: List[Any] = Field(default_factory=list)
    truncatedCompany: Optional[str] = None
    urgentlyHiring: Optional[bool] = False
    viewJobLink: Optional[str] = None
    vjFeaturedEmployerCandidate: Optional[bool] = False


# --------------------------------------------------------------------------
# Mosaic Provider & Metadata Models
# --------------------------------------------------------------------------
class MosaicProviderJobCardsModel(BaseSchema):
    adSignature: Optional[str] = None
    appName: Optional[str] = None
    applyHolisticStyle: Optional[bool] = False
    baseUrl: Optional[str] = None
    bot: Optional[bool] = False
    brandedAds: List[Any] = Field(default_factory=list)
    csrfToken: Optional[str] = None
    encryptedQueryData: Optional[str] = None
    experienceLevelFilterRefineBy: Optional[str] = ""
    fccId: Optional[int] = -1
    hasResume: Optional[bool] = False
    indeedApplyOnlyFilterUsed: Optional[bool] = False
    indeedPro: Optional[bool] = False
    ipCountry: Optional[str] = None
    isDesktop: Optional[bool] = False
    isHighContrastIconShown: Optional[bool] = False
    isIpadApp: Optional[bool] = False
    isJobCardShelfApplied: Optional[bool] = False
    isTablet: Optional[bool] = False
    jobCardExpansionType: Optional[str] = None
    jobCardVariant: Optional[str] = None
    jobSeenLogParameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    jobTypeFilterRefineBy: Optional[str] = ""
    kebabMenuEnabled: Optional[bool] = False
    loggedIn: Optional[bool] = False
    mobtk: Optional[str] = None
    mosaicNonJobContent: List[Any] = Field(default_factory=list)
    mustShowSponsoredLabel: Optional[bool] = False
    myIndeedRegisterLink: Optional[str] = None
    noJsUrlOnly: Optional[bool] = False
    outOfCountry: Optional[bool] = False
    overrideShelf: Optional[bool] = False
    pageNumber: Optional[int] = 1
    passportLoginLink: Optional[str] = None
    prforceGroups: Optional[str] = ""
    proctorContext: Optional[ProctorContext] = None
    proctorIdentifiers: Optional[ProctorIdentifiers] = None
    queryModifierResult: Optional[QueryModifierResult] = None
    radius: Optional[int] = 25
    refineByTypes: List[Any] = Field(default_factory=list)
    results: List[JobCard] = Field(default_factory=list)
    searchTimestamp: Optional[int] = None
    searchUID: Optional[str] = None
    shiftScheduleFilterRefineBy: List[Any] = Field(default_factory=list)
    shouldAppendMCLKToViewjob: Optional[bool] = False
    shouldRunReactClientSide: Optional[bool] = True
    shouldServerSideRender: Optional[bool] = True
    shouldShowITAOverFE: Optional[bool] = False
    shouldShowResponsiveEmployer: Optional[bool] = True
    shouldUseJCSMouseDownHandler: Optional[bool] = True
    showDislikeJobButton: Optional[bool] = False
    showFeaturedCompany: Optional[bool] = False
    showMobJobSnippet: Optional[bool] = False
    showModalSaveMenu: Optional[bool] = False
    showSaveJobButton: Optional[bool] = False
    showSerpMetadata: Optional[bool] = False
    showStations: Optional[bool] = False
    stabilizeHTMLForSEO: Optional[bool] = False
    tierSummaries: List[Any] = Field(default_factory=list)
    twoLineJobTitle: Optional[bool] = False
    viewjobFrom: Optional[str] = None
    what: Optional[str] = None
    where: Optional[str] = None


class MetaData(BaseSchema):
    isJpBundle: Optional[bool] = False
    mosaicProviderJobCardsModel: Optional[MosaicProviderJobCardsModel] = None
    savedJobCount: Optional[int] = 0
    uiVariant: Optional[str] = None


class Artifacts(BaseSchema):
    hiringEventInfoMap: Dict[str, Any] = Field(default_factory=dict)
    responsiveEmployerMap: Dict[str, bool] = Field(default_factory=dict)


# --------------------------------------------------------------------------
# Root Schema
# --------------------------------------------------------------------------
class IndeedSearchResultPayload(BaseSchema):
    metaData: Optional[MetaData] = None
    proctorGroups: Dict[str, ProctorGroup] = Field(default_factory=dict)
    deploymentGroup: Optional[str] = None
    artifacts: Optional[Artifacts] = None
    isApp: Optional[bool] = False
    isAndroid: Optional[bool] = False
    isDsanr: Optional[bool] = False
    isJpBundle: Optional[bool] = False
    shouldRunReactClientSide: Optional[bool] = True
    countryCode: Optional[str] = None
    language: Optional[str] = None
    isProduction: Optional[bool] = True
    oneGraphUrl: Optional[str] = None
    oneGraphApiKey: Optional[str] = None
    ctk: Optional[str] = None
    isHorizontalMode: Optional[bool] = False
    hostId: Optional[str] = None
    pageId: Optional[str] = None
    providerId: Optional[str] = None
    uiVariant: Optional[str] = None

    @property
    def job_cards(self) -> List[JobCard]:
        if self.metaData and self.metaData.mosaicProviderJobCardsModel:
            return self.metaData.mosaicProviderJobCardsModel.results
        return []
