# Standard library
from datetime import date

# Third-party
from pydantic import BaseModel, Field

# Local modules
from .common import (
    AvailIpd,
    CertainAgreement,
    Contact,
    DateStruct,
    ExpandedAccessInfo,
    LargeDoc,
    LimitationsAndCaveats,
    Location,
    Official,
    Organization,
    OrgStudyIdInfo,
    PartialDate,
    PartialDateStruct,
    PointOfContact,
    Reference,
    SecondaryIdInfo,
    SeeAlsoLink,
    Sponsor,
    SubmissionTracking,
    UnpostedAnnotation,
    ViolationAnnotation,
)
from .enums import (
    AnalysisDispersionType,
    ArmGroupType,
    BioSpecRetention,
    BrowseLeafRelevance,
    ConfidenceIntervalNumSides,
    DesignAllocation,
    DesignMasking,
    DesignTimePerspective,
    EnrollmentType,
    EventAssessment,
    InterventionalAssignment,
    InterventionType,
    IpdSharing,
    IpdSharingInfoType,
    MeasureDispersionType,
    MeasureParam,
    NonInferiorityType,
    ObservationalModel,
    OutcomeMeasureType,
    Phase,
    PrimaryPurpose,
    ReportingStatus,
    ResponsiblePartyType,
    SamplingMethod,
    Sex,
    StandardAge,
    Status,
    StudyType,
    WhoMasked,
)

# --- Base Measurement/Stats Structures ---
# These are complex and reused in Baseline, Outcome, Adverse Events, Flow

class DenomCount(BaseModel):
    groupId: str | None = None
    value: str | None = None

class Denom(BaseModel):
    units: str | None = None
    counts: list["DenomCount"] = []

class Measurement(BaseModel):
    groupId: str | None = None
    value: str | None = None
    spread: str | None = None
    lowerLimit: str | None = None
    upperLimit: str | None = None
    comment: str | None = None

class MeasureCategory(BaseModel):
    title: str | None = None
    measurements: list[Measurement] = []

class MeasureClass(BaseModel):
    title: str | None = None
    denoms: list[Denom] = []
    categories: list[MeasureCategory] = []

class MeasureAnalysis(BaseModel):
    paramType: str | None = None # Different from MeasureParam enum? Spec shows string.
    paramValue: str | None = None
    dispersionType: AnalysisDispersionType | None = None
    dispersionValue: str | None = None
    statisticalMethod: str | None = None
    statisticalComment: str | None = None
    pValue: str | None = None
    pValueComment: str | None = None
    ciNumSides: ConfidenceIntervalNumSides | None = None
    ciPctValue: str | None = None # Should this be float? Spec says string.
    ciLowerLimit: str | None = None
    ciUpperLimit: str | None = None
    ciLowerLimitComment: str | None = None
    ciUpperLimitComment: str | None = None
    estimateComment: str | None = None
    testedNonInferiority: bool | None = None
    nonInferiorityType: NonInferiorityType | None = None
    nonInferiorityComment: str | None = None
    otherAnalysisDescription: str | None = None
    groupDescription: str | None = None # Added based on context in spec
    groupIds: list[str] = []

class MeasureGroup(BaseModel):
    id: str | None = Field(default=None, alias="groupId") # Sometimes 'id', sometimes 'groupId'
    title: str | None = None
    description: str | None = None

# --- Protocol Section ---

class IdentificationModule(BaseModel):
    nctId: str | None = None
    nctIdAliases: list[str] = []
    orgStudyIdInfo: OrgStudyIdInfo | None = None
    secondaryIdInfos: list[SecondaryIdInfo] = []
    briefTitle: str | None = None
    officialTitle: str | None = None
    acronym: str | None = None
    organization: Organization | None = None

class StatusModule(BaseModel):
    statusVerifiedDate: PartialDate = None
    overallStatus: Status | None = None
    lastKnownStatus: Status | None = None # Added based on common CTG usage
    delayedPosting: bool | None = None
    whyStopped: str | None = None
    expandedAccessInfo: ExpandedAccessInfo | None = None
    startDateStruct: PartialDateStruct | None = None
    primaryCompletionDateStruct: PartialDateStruct | None = None
    completionDateStruct: PartialDateStruct | None = None
    studyFirstSubmitDate: date | None = None
    studyFirstSubmitQcDate: date | None = None
    studyFirstPostDateStruct: DateStruct | None = None
    resultsWaived: bool | None = None # Added based on common CTG usage
    resultsFirstSubmitDate: date | None = None
    resultsFirstSubmitQcDate: date | None = None
    resultsFirstPostDateStruct: DateStruct | None = None
    dispFirstSubmitDate: date | None = None
    dispFirstSubmitQcDate: date | None = None
    dispFirstPostDateStruct: DateStruct | None = None
    lastUpdateSubmitDate: date | None = None
    lastUpdatePostDateStruct: DateStruct | None = None

class ResponsibleParty(BaseModel):
    type: ResponsiblePartyType | None = None
    investigatorFullName: str | None = None
    investigatorTitle: str | None = None
    investigatorAffiliation: str | None = None
    oldNameTitle: str | None = None # Added based on common CTG usage
    oldOrganization: str | None = None # Added based on common CTG usage

class SponsorCollaboratorsModule(BaseModel):
    responsibleParty: ResponsibleParty | None = None
    leadSponsor: Sponsor | None = None
    collaborators: list[Sponsor] = []

class OversightModule(BaseModel):
    oversightHasDmc: bool | None = None
    isFdaRegulatedDrug: bool | None = None
    isFdaRegulatedDevice: bool | None = None
    isUnapprovedDevice: bool | None = None # Added based on common CTG usage
    isPpsd: bool | None = None # Added based on common CTG usage
    isUsExport: bool | None = None # Added based on common CTG usage
    fdaaa801Violation: bool | None = None # Added based on common CTG usage

class DescriptionModule(BaseModel):
    briefSummary: str | None = None
    detailedDescription: str | None = None

class ConditionsModule(BaseModel):
    conditions: list[str] = Field(default=[], alias="condition") # Field name is 'conditions' but often 'condition' in API
    keywords: list[str] = Field(default=[], alias="keyword") # Field name is 'keywords' but often 'keyword' in API

class ExpandedAccessTypes(BaseModel):
    individual: bool | None = None
    intermediate: bool | None = None
    treatment: bool | None = None

class MaskingBlock(BaseModel):
    masking: DesignMasking | None = None
    maskingDescription: str | None = None
    whoMasked: list[WhoMasked] = []

class DesignInfo(BaseModel):
    allocation: DesignAllocation | None = None
    interventionModel: InterventionalAssignment | None = None
    interventionModelDescription: str | None = None
    primaryPurpose: PrimaryPurpose | None = None
    observationalModel: ObservationalModel | None = None
    timePerspective: DesignTimePerspective | None = None
    maskingInfo: MaskingBlock | None = None

class BioSpec(BaseModel):
    retention: BioSpecRetention | None = None
    description: str | None = None

class EnrollmentInfo(BaseModel):
    count: int | None = None
    type: EnrollmentType | None = None

class DesignModule(BaseModel):
    studyType: StudyType | None = None
    nPtrsToThisExpAccNctId: float | None = None # Spec says number, assume float
    expandedAccessTypes: ExpandedAccessTypes | None = None # Added based on common CTG usage
    patientRegistry: bool | None = None # Added based on common CTG usage
    targetDuration: str | None = None # Pattern: ^\d+ (Year|Years|Month|Months|Week|Weeks|Day|Days|Hour|Hours|Minute|Minutes)$    
    phases: list[Phase] = Field(default=[], alias="phase") # Field name is 'phases' but often 'phase' in API
    designInfo: DesignInfo | None = None
    bioSpec: BioSpec | None = None
    enrollmentInfo: EnrollmentInfo | None = None

class ArmGroup(BaseModel):
    label: str | None = None
    type: ArmGroupType | None = None
    description: str | None = None
    interventionNames: list[str] = []

class Intervention(BaseModel):
    type: InterventionType | None = None
    name: str | None = None
    description: str | None = None
    armGroupLabels: list[str] = []
    otherNames: list[str] = []

class ArmsInterventionsModule(BaseModel):
    armGroups: list[ArmGroup] = []
    interventions: list[Intervention] = []

class Outcome(BaseModel):
    measure: str | None = None
    description: str | None = None
    timeFrame: str | None = None

class OutcomesModule(BaseModel):
    primaryOutcomes: list[Outcome] = []
    secondaryOutcomes: list[Outcome] = []
    otherOutcomes: list[Outcome] = []

class EligibilityModule(BaseModel):
    eligibilityCriteria: str | None = None
    healthyVolunteers: bool | None = None
    sex: Sex | None = None
    genderBased: bool | None = None
    genderDescription: str | None = None
    minimumAge: str | None = None # Pattern: ^\d+ (Year|Years|Month|Months|Week|Weeks|Day|Days|Hour|Hours|Minute|Minutes)$    
    maximumAge: str | None = None # Pattern: ^\d+ (Year|Years|Month|Months|Week|Weeks|Day|Days|Hour|Hours|Minute|Minutes)$    
    stdAges: list[StandardAge] = Field(default=[], alias="stdAge") # Field name is 'stdAges' but often 'stdAge' in API
    studyPopulation: str | None = None
    samplingMethod: SamplingMethod | None = None

class ContactsLocationsModule(BaseModel):
    centralContacts: list[Contact] = []
    overallOfficials: list[Official] = []
    locations: list[Location] = Field(default=[], alias="location") # Field name is 'locations' but often 'location' in API

class ReferencesModule(BaseModel):
    references: list[Reference] = Field(default=[], alias="reference") # Field name is 'references' but often 'reference' in API
    seeAlsoLinks: list[SeeAlsoLink] = Field(default=[], alias="seeAlsoLink") # Field name is 'seeAlsoLinks' but often 'seeAlsoLink' in API
    availIpds: list[AvailIpd] = Field(default=[], alias="availIpd") # Field name is 'availIpds' but often 'availIpd' in API

class IpdSharingStatementModule(BaseModel):
    ipdSharing: IpdSharing | None = None
    description: str | None = Field(default=None, alias="ipdSharingDescription") # often 'ipdSharingDescription'
    infoTypes: list[IpdSharingInfoType] = Field(default=[], alias="ipdSharingInfoType")
    timeFrame: str | None = Field(default=None, alias="ipdSharingTimeFrame") # often 'ipdSharingTimeFrame'
    accessCriteria: str | None = Field(default=None, alias="ipdSharingAccessCriteria") # often 'ipdSharingAccessCriteria'
    url: str | None = Field(default=None, alias="ipdSharingURL") # often 'ipdSharingURL'

class ProtocolSection(BaseModel):
    identificationModule: IdentificationModule | None = None
    statusModule: StatusModule | None = None
    sponsorCollaboratorsModule: SponsorCollaboratorsModule | None = None
    oversightModule: OversightModule | None = None
    descriptionModule: DescriptionModule | None = None
    conditionsModule: ConditionsModule | None = None
    designModule: DesignModule | None = None
    armsInterventionsModule: ArmsInterventionsModule | None = None
    outcomesModule: OutcomesModule | None = None
    eligibilityModule: EligibilityModule | None = None
    contactsLocationsModule: ContactsLocationsModule | None = None
    referencesModule: ReferencesModule | None = None
    ipdSharingStatementModule: IpdSharingStatementModule | None = None

# --- Results Section ---

class FlowStats(BaseModel):
    groupId: str | None = None
    comment: str | None = None
    numSubjects: str | None = None # Spec shows string, might be int sometimes?
    numUnits: str | None = None # Spec shows string, might be int sometimes?

class FlowMilestone(BaseModel):
    type: str | None = None
    comment: str | None = None
    achievements: list[FlowStats] = []

class DropWithdraw(BaseModel):
    type: str | None = None
    comment: str | None = None
    reasons: list[FlowStats] = []

class FlowPeriod(BaseModel):
    title: str | None = None
    milestones: list[FlowMilestone] = []
    dropWithdraws: list[DropWithdraw] = []

class FlowGroup(BaseModel):
    id: str | None = None
    title: str | None = None
    description: str | None = None

class ParticipantFlowModule(BaseModel):
    preAssignmentDetails: str | None = None
    recruitmentDetails: str | None = None
    typeUnitsAnalyzed: str | None = None
    groups: list[FlowGroup] = Field(default=[], alias="groupList") # Often 'groupList'
    periods: list[FlowPeriod] = Field(default=[], alias="periodList") # Often 'periodList'

class BaselineMeasure(BaseModel):
    title: str | None = None
    description: str | None = None
    populationDescription: str | None = None
    paramType: MeasureParam | None = None
    dispersionType: MeasureDispersionType | None = None
    unitOfMeasure: str | None = None
    calculatePct: bool | None = None
    denomUnitsSelected: str | None = None
    denoms: list[Denom] = []
    classes: list[MeasureClass] = Field(default=[], alias="classList") # Often 'classList'

class BaselineCharacteristicsModule(BaseModel):
    populationDescription: str | None = None
    typeUnitsAnalyzed: str | None = None
    groups: list[MeasureGroup] = Field(default=[], alias="groupList") # Often 'groupList'
    denoms: list[Denom] = Field(default=[], alias="denomList") # Often 'denomList'
    measures: list[BaselineMeasure] = Field(default=[], alias="measureList") # Often 'measureList'

class OutcomeMeasure(BaseModel):
    type: OutcomeMeasureType | None = None
    title: str | None = None
    description: str | None = None
    populationDescription: str | None = None
    reportingStatus: ReportingStatus | None = None
    anticipatedPostingDate: PartialDate = None
    paramType: MeasureParam | None = None
    dispersionType: str | None = None # Spec shows string, not MeasureDispersionType enum?
    unitOfMeasure: str | None = None
    calculatePct: bool | None = None
    timeFrame: str | None = None
    typeUnitsAnalyzed: str | None = None
    denomUnitsSelected: str | None = None
    groups: list[MeasureGroup] = Field(default=[], alias="groupList") # Often 'groupList'
    denoms: list[Denom] = Field(default=[], alias="denomList") # Often 'denomList'
    classes: list[MeasureClass] = Field(default=[], alias="classList") # Often 'classList'
    analyses: list[MeasureAnalysis] = Field(default=[], alias="analysisList") # Often 'analysisList'

class OutcomeMeasuresModule(BaseModel):
    outcomeMeasures: list[OutcomeMeasure] = Field(default=[], alias="outcomeMeasureList") # Often 'outcomeMeasureList'

class EventStats(BaseModel):
    groupId: str | None = None
    numEvents: int | None = None
    numAffected: int | None = None
    numAtRisk: int | None = None

class AdverseEvent(BaseModel):
    term: str | None = None
    organSystem: str | None = None
    sourceVocabulary: str | None = None
    assessmentType: EventAssessment | None = None
    notes: str | None = None
    stats: list[EventStats] = []

class EventGroup(BaseModel):
    id: str | None = None
    title: str | None = None
    description: str | None = None
    deathsNumAffected: int | None = None
    deathsNumAtRisk: int | None = None
    seriousNumAffected: int | None = None
    seriousNumAtRisk: int | None = None
    otherNumAffected: int | None = None
    otherNumAtRisk: int | None = None

class AdverseEventsModule(BaseModel):
    frequencyThreshold: str | None = None # Might be float? Spec says string.
    timeFrame: str | None = None
    description: str | None = None
    allCauseMortalityComment: str | None = None # Added based on common CTG usage
    eventGroups: list[EventGroup] = Field(default=[], alias="eventGroupList") # Often 'eventGroupList'
    seriousEvents: list[AdverseEvent] = Field(default=[], alias="seriousEventList") # Often 'seriousEventList'
    otherEvents: list[AdverseEvent] = Field(default=[], alias="otherEventList") # Often 'otherEventList'


class MoreInfoModule(BaseModel):
    limitationsAndCaveats: LimitationsAndCaveats | None = None
    certainAgreement: CertainAgreement | None = None
    pointOfContact: PointOfContact | None = None

class ResultsSection(BaseModel):
    participantFlowModule: ParticipantFlowModule | None = None
    baselineCharacteristicsModule: BaselineCharacteristicsModule | None = None
    outcomeMeasuresModule: OutcomeMeasuresModule | None = None
    adverseEventsModule: AdverseEventsModule | None = None
    moreInfoModule: MoreInfoModule | None = None

# --- Annotation Section ---

class AnnotationModule(BaseModel):
    unpostedAnnotation: UnpostedAnnotation | None = None
    violationAnnotation: ViolationAnnotation | None = None

class AnnotationSection(BaseModel):
    annotationModule: AnnotationModule | None = None

# --- Document Section ---

class LargeDocumentModule(BaseModel):
    noSap: bool | None = None # Added based on common CTG usage
    largeDocs: list[LargeDoc] = Field(default=[], alias="largeDocList") # Often 'largeDocList'


class DocumentSection(BaseModel):
    largeDocumentModule: LargeDocumentModule | None = None

# --- Derived Section ---

class MiscInfoModule(BaseModel):
    versionHolder: date | None = None # Spec says string format date, use date
    removedCountries: list[str] = Field(default=[], alias="removedCountry") # Often 'removedCountry'
    submissionTracking: SubmissionTracking | None = None # Added based on common CTG usage

class Mesh(BaseModel):
    id: str | None = None
    term: str | None = None

class BrowseLeaf(BaseModel):
    id: str | None = None
    name: str | None = None
    asFound: str | None = None
    relevance: BrowseLeafRelevance | None = None

class BrowseBranch(BaseModel):
    abbrev: str | None = None
    name: str | None = None

class BrowseModule(BaseModel):
    meshes: list[Mesh] = Field(default=[], alias="mesh") # Often 'mesh'
    ancestors: list[Mesh] = Field(default=[], alias="ancestor") # Often 'ancestor'
    browseLeaves: list[BrowseLeaf] = Field(default=[], alias="browseLeaf") # Often 'browseLeaf'
    browseBranches: list[BrowseBranch] = Field(default=[], alias="browseBranch") # Often 'browseBranch'


class DerivedSection(BaseModel):
    miscInfoModule: MiscInfoModule | None = None
    conditionBrowseModule: BrowseModule | None = None
    interventionBrowseModule: BrowseModule | None = None

# --- Top-Level Study Schema ---

class Study(BaseModel):
    protocolSection: ProtocolSection | None = None
    resultsSection: ResultsSection | None = None
    annotationSection: AnnotationSection | None = None
    documentSection: DocumentSection | None = None
    derivedSection: DerivedSection | None = None
    hasResults: bool | None = None

# --- Paged Studies Response ---

class PagedStudies(BaseModel):
    studies: list[Study]
    nextPageToken: str | None = None
    totalCount: int | None = None


# Update forward refs for models that reference themselves or others defined later
Denom.model_rebuild()
MeasureClass.model_rebuild()
BaselineMeasure.model_rebuild()
OutcomeMeasure.model_rebuild()
