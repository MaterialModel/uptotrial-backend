# Standard library
from datetime import date as date_type
from datetime import datetime
from typing import Annotated, Any, Literal, Union

# Third-party
from pydantic import BaseModel, Field

# Local modules
from app.infrastructure.clinical_trials_gov.schemas.enums import (
    AgencyClass,
    AgreementRestrictionType,
    ContactRole,
    DateType,
    ExpandedAccessStatus,
    OfficialRole,
    OrgStudyIdType,
    RecruitmentStatus,
    ReferenceType,
    SecondaryIdType,
    UnpostedEventType,
    ViolationEventType,
)

# Type Aliases for specific formats mentioned in descriptions
PartialDate = Annotated[str | None, Field(description="Date in `yyyy`, `yyyy-MM`, or `yyyy-MM-dd` format", default=None)]
DateTimeMinutes = Annotated[datetime | None, Field(description="Date and time in `yyyy-MM-dd'T'HH:mm` format", default=None)]
# Basic Types (used directly or within other models)

class GeoPoint(BaseModel):
    lat: float
    lon: float

class Organization(BaseModel):
    fullName: str | None = None
    agency_class: AgencyClass | None = Field(default=None, alias="class") # 'class' is reserved

class DateStruct(BaseModel):
    date: date_type | None = None
    type: DateType | None = None

class PartialDateStruct(BaseModel):
    date: PartialDate = None
    type: DateType | None = None

class ExpandedAccessInfo(BaseModel):
    hasExpandedAccess: bool | None = None
    nctId: str | None = None
    statusForNctId: ExpandedAccessStatus | None = None

class OrgStudyIdInfo(BaseModel):
    id: str | None = None
    type: OrgStudyIdType | None = None
    link: str | None = None

class SecondaryIdInfo(BaseModel):
    id: str | None = None
    type: SecondaryIdType | None = None
    domain: str | None = None
    link: str | None = None

class Sponsor(BaseModel):
    name: str | None = None
    agency_class: AgencyClass | None = Field(default=None, alias="class") # 'class' is reserved

class Contact(BaseModel):
    name: str | None = None
    role: ContactRole | None = None
    phone: str | None = None
    phoneExt: str | None = None
    email: str | None = None

class Official(BaseModel):
    name: str | None = None
    affiliation: str | None = None
    role: OfficialRole | None = None

class Location(BaseModel):
    facility: str | None = None
    status: RecruitmentStatus | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    country: str | None = None
    contacts: list[Contact] = []
    countryCode: str | None = None
    geoPoint: GeoPoint | None = None

class Retraction(BaseModel):
    pmid: str | None = None
    source: str | None = None

class Reference(BaseModel):
    pmid: str | None = None
    type: ReferenceType | None = None
    citation: str | None = None
    retractions: list[Retraction] = []

class SeeAlsoLink(BaseModel):
    label: str | None = None
    url: str | None = None

class AvailIpd(BaseModel):
    id: str | None = None
    type: str | None = None
    url: str | None = None
    comment: str | None = None

class LimitationsAndCaveats(BaseModel):
    description: str | None = None

class CertainAgreement(BaseModel):
    piSponsorEmployee: bool | None = None
    restrictionType: AgreementRestrictionType | None = None
    restrictiveAgreement: bool | None = None
    otherDetails: str | None = None

class PointOfContact(BaseModel):
    title: str | None = None
    organization: str | None = None
    email: str | None = None
    phone: str | None = None
    phoneExt: str | None = None

class UnpostedEvent(BaseModel):
    type: UnpostedEventType | None = None
    date: date_type | None = None
    dateUnknown: bool | None = None

class UnpostedAnnotation(BaseModel):
    unpostedResponsibleParty: str | None = None
    unpostedEvents: list[UnpostedEvent] = []

class ViolationEvent(BaseModel):
    type: ViolationEventType | None = None
    description: str | None = None
    creationDate: date_type | None = None
    issuedDate: date_type | None = None
    releaseDate: date_type | None = None
    postedDate: date_type | None = None

class ViolationAnnotation(BaseModel):
    violationEvents: list[ViolationEvent] = []

class FirstMcpInfo(BaseModel):
    postDateStruct: DateStruct | None = None

class SubmissionInfo(BaseModel):
    releaseDate: date_type | None = None
    unreleaseDate: date_type | None = None
    unreleaseDateUnknown: bool | None = None
    resetDate: date_type | None = None
    mcpReleaseN: int | None = None

class SubmissionTracking(BaseModel):
    estimatedResultsFirstSubmitDate: date_type | None = None
    firstMcpInfo: FirstMcpInfo | None = None
    submissionInfos: list[SubmissionInfo] = []

class LargeDoc(BaseModel):
    typeAbbrev: str | None = None
    hasProtocol: bool | None = None
    hasSap: bool | None = None
    hasIcf: bool | None = None
    label: str | None = None
    date: date_type | None = None
    uploadDate: DateTimeMinutes = None
    filename: str | None = None
    size: int | None = None

class WebLink(BaseModel):
    label: str
    url: str

class EnumItem(BaseModel):
    """Represents a single value within an enumeration."""
    value: str
    legacyValue: str
    # Assuming string keys and values for exceptions based on spec example context
    exceptions: dict[str, str] | None = None

class EnumInfo(BaseModel):
    """Describes an enumeration type used in the API."""
    type: str
    pieces: list[str]
    values: list[EnumItem]

# --- Models for Metadata Endpoints ---

class FieldNode(BaseModel):
    name: str
    piece: str
    sourceType: str
    type: str
    altPieceNames: list[str] | None = None
    children: list["FieldNode"] | None = None # Recursive definition
    dedLink: WebLink | None = None
    description: str | None = None
    historicOnly: bool | None = None
    indexedOnly: bool | None = None
    isEnum: bool | None = None
    maxChars: int | None = None
    nested: bool | None = None
    rules: str | None = None
    synonyms: bool | None = None
    title: str | None = None

FieldNode.model_rebuild() # Resolve forward reference

class SearchPart(BaseModel):
    isEnum: bool
    isSynonyms: bool
    pieces: list[str]
    type: str
    weight: float

class SearchArea(BaseModel):
    name: str
    parts: list[SearchPart]
    param: str | None = None
    uiLabel: str | None = None

class SearchDocument(BaseModel):
    name: str
    areas: list[SearchArea]

# --- Models for Stats Endpoints ---

class StudySize(BaseModel):
    id: str
    sizeBytes: int

class DistItem(BaseModel):
    sizeRange: str
    studiesCount: int

class GzipStats(BaseModel):
    averageSizeBytes: int
    largestStudies: list[StudySize]
    percentiles: dict[str, Any] # The spec just shows object, assuming Any
    ranges: list[DistItem]
    totalStudies: int

class ListSize(BaseModel):
    size: int
    studiesCount: int

class ListSizes(BaseModel):
    field: str
    piece: str
    uniqueSizesCount: int # Spec says int64, use int
    maxSize: int | None = None
    minSize: int | None = None
    topSizes: list[ListSize] | None = None

class FieldStatsType(str, Enum):
    ENUM = "ENUM"
    STRING = "STRING"
    DATE = "DATE"
    INTEGER = "INTEGER"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"

class ValueCount(BaseModel):
    value: str
    studiesCount: int

class EnumStats(BaseModel):
    field: str
    missingStudiesCount: int
    piece: str
    type: Literal[FieldStatsType.ENUM]
    uniqueValuesCount: int # Spec says int64, use int
    topValues: list[ValueCount] | None = None

class LongestString(BaseModel):
    length: int
    nctId: str
    value: str

class StringStats(BaseModel):
    field: str
    missingStudiesCount: int
    piece: str
    type: Literal[FieldStatsType.STRING]
    uniqueValuesCount: int # Spec says int64, use int
    longest: LongestString | None = None
    topValues: list[ValueCount] | None = None

class DateStats(BaseModel):
    field: str
    formats: list[str]
    missingStudiesCount: int
    piece: str
    type: Literal[FieldStatsType.DATE]
    max: str | None = None
    min: str | None = None

class IntegerStats(BaseModel):
    field: str
    missingStudiesCount: int
    piece: str
    type: Literal[FieldStatsType.INTEGER]
    avg: float | None = None
    max: int | None = None # Spec says int64, use int
    min: int | None = None # Spec says int64, use int

class NumberStats(BaseModel):
    field: str
    missingStudiesCount: int
    piece: str
    type: Literal[FieldStatsType.NUMBER]
    avg: float | None = None
    max: float | None = None
    min: float | None = None

class BooleanStats(BaseModel):
    falseCount: int
    field: str
    missingStudiesCount: int
    piece: str
    trueCount: int
    type: Literal[FieldStatsType.BOOLEAN]

# Union type for the FieldValuesStats endpoint response (anyOf)
FieldValuesStats = Annotated[
    Union[EnumStats, StringStats, DateStats, IntegerStats, NumberStats, BooleanStats],
    Field(discriminator="type")
]

# --- Model for Version Endpoint ---

class Version(BaseModel):
    apiVersion: str
    dataTimestamp: str | None = None # Spec implies required but allow None
