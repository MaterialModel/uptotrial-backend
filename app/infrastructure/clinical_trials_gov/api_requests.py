# Standard library imports first
import logging
from typing import Annotated, Any, Literal
from urllib.parse import urlencode, urljoin

from agents import function_tool

# Third-party imports
from pydantic import BaseModel

# Local modules
from app.infrastructure.fetch import fetch_with_urllib

# Base URL for the ClinicalTrials.gov API v2
CTG_API_BASE_URL = "https://clinicaltrials.gov/api/v2"

# Setup logger
logger = logging.getLogger(__name__)


Status = Literal[
    "ACTIVE_NOT_RECRUITING",
    "COMPLETED",
    "ENROLLING_BY_INVITATION",
    "NOT_YET_RECRUITING",
    "RECRUITING",
    "SUSPENDED",
    "TERMINATED",
    "WITHDRAWN",
    "AVAILABLE",
    "NO_LONGER_AVAILABLE",
    "TEMPORARILY_NOT_AVAILABLE",
    "APPROVED_FOR_MARKETING",
    "WITHHELD",
    "UNKNOWN",
]

# Expanded list of common/useful fields based on CTG documentation
AllowedField = Literal[
    # Identification
    "NCTId",
    "OrgStudyId", # Assuming this corresponds to Study IDs mentioned
    "SecondaryIdInfo", # Often related to other IDs
    "Acronym",

    # Titles & Summaries
    "BriefTitle",
    "OfficialTitle",
    "BriefSummary",
    "DetailedDescription", # Common field, likely available

    # Status & Dates
    "OverallStatus",
    "LastKnownStatus",
    "StartDate",
    "PrimaryCompletionDate", # Common field, likely available
    "CompletionDate",
    "StudyFirstPostDate", # Common field, likely available
    "ResultsFirstPostDate",
    "LastUpdatePostDate",

    # Study Design
    "Phase", # Common field, likely available
    "StudyType", # Common field, likely available
    "DesignInfo", # Often contains design details
    "TargetDuration", # Common field, likely available

    # Conditions & Keywords
    "Condition",
    "ConditionMeshTerm",
    "ConditionAncestorTerm",
    "Keyword",

    # Interventions
    "InterventionName",
    "InterventionType",
    "InterventionDescription", # Common field, likely available
    "InterventionOtherName",
    "ArmGroupInterventionName", # For specific arms

    # Outcomes
    "PrimaryOutcomeMeasure",
    "PrimaryOutcomeDescription", # Often paired with measure
    "PrimaryOutcomeTimeFrame", # Often paired with measure
    "SecondaryOutcomeMeasure",
    "SecondaryOutcomeDescription",
    "SecondaryOutcomeTimeFrame",
    "OtherOutcomeMeasure",

    # Eligibility & Enrollment
    "EligibilityCriteria", # Common field, likely available
    "Gender", # Common field, likely available
    "MinimumAge", # Common field, likely available
    "MaximumAge", # Common field, likely available
    "StdAge",
    "HealthyVolunteers", # Common field, likely available
    "EnrollmentCount", # Common field, likely available
    "EnrollmentType",

    # Locations & Contacts
    "LocationFacility", # Corresponds to Facility Name search
    "LocationCity",
    "LocationState",
    "LocationZip", # Common field, likely available
    "LocationCountry",
    "LocationStatus",
    "LocationContactName", # Common field, likely available
    "LocationContactPhone", # Common field, likely available
    "LocationContactEMail", # Common field, likely available
    "CentralContactName", # Often exists for overall contact
    "CentralContactPhone",
    "CentralContactEMail",
    "OverallOfficialName", # Often exists for main investigator
    "OverallOfficialAffiliation",
    "OverallOfficialRole",

    # Sponsor & Collaborators
    "LeadSponsorName",
    "LeadSponsorClass",
    "CollaboratorName", # Common field, likely available
    "CollaboratorClass",

    # Responsible Party
    "ResponsiblePartyType", # Common field, likely available
    "ResponsiblePartyInvestigatorFullName",
    "ResponsiblePartyInvestigatorTitle",
    "ResponsiblePartyInvestigatorAffiliation",

    # Results & References
    "ResultsReferenceCitation", # Common field, likely available
    "ResultsReferencePMID", # Common field, likely available
    "SeeAlsoLinkURL", # Common field, likely available
    "SeeAlsoLinkLabel", # Common field, likely available

    # IPD Sharing
    "IPDSharing",
    "IPDSharingInfoType",
    "IPDSharingURL", # Often paired with sharing statement

    # Misc
    "StudyDocuments", # If document info is available
    "PointOfContactEMail", # General contact
]

SortDirection = Literal["asc", "desc"]

class SortField(BaseModel):
    field: AllowedField
    direction: SortDirection


# Helper function
def _build_ctg_url(base_url: str, path: str, params: dict[str, Any] | None) -> str:
    """Builds the full URL for a CTG API request, handling parameter encoding.

    Handles boolean conversion to lower case strings and joins lists
    with appropriate separators (comma or pipe) based on known API parameter styles.
    Filters out parameters with None values.

    Args:
        base_url: The base API URL.
        path: The specific endpoint path.
        params: Dictionary of query parameters. Defaults to None.

    Returns:
        The fully constructed URL string.
    """
    # Ensure base_url ends with a single slash and path starts without one for urljoin
    full_path = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))

    if not params:
        return full_path

    query_params = {}
    # Filter out None values before processing
    processed_params = {k: v for k, v in params.items() if v is not None}

    for key, value in processed_params.items():
        # Parameter styles based on OpenAPI spec (style: pipeDelimited, explode: false)
        # Default is comma-separated or standard encoding for non-list types
        list_param_style = {
            "filter.overallStatus": "|",
            "filter.ids": "|",
            "filter.synonyms": "|",
            "postFilter.overallStatus": "|",
            "postFilter.ids": "|",
            "postFilter.synonyms": "|",
            "fields": "|",
            "sort": "|",
            "types": "|", # For /stats/field/values
        }

        if isinstance(value, list):
            # Ensure list is not empty before joining
            if not value:
                continue # Skip empty lists
            separator = list_param_style.get(key, ",")
            # Ensure all list items are strings before joining
            str_values = [str(item) for item in value]
            query_params[key] = separator.join(str_values)
        elif isinstance(value, bool):
            query_params[key] = str(value).lower() # API uses 'true'/'false'
        else:
            # Convert all other values to string for urlencode
            # This handles integers, floats, etc. consistently
             query_params[key] = str(value)

    # Only add query string if there are parameters
    if not query_params:
        return full_path

    # Use urlencode for robust encoding of values like spaces, special chars
    query_string = urlencode(query_params)
    return f"{full_path}?{query_string}"


# --- API Functions ---
@function_tool
async def list_studies(
    query_cond: Annotated[str | None, "Condition/disease query (Essie syntax)"],
    query_term: Annotated[str | None, "Other terms query (Essie syntax)"],
    query_locn: Annotated[str | None, "Location terms query (Essie syntax)"],
    query_titles: Annotated[str | None, "Title/acronym query (Essie syntax)"],
    query_intr: Annotated[str | None, "Intervention/treatment query (Essie syntax)"],
    query_outc: Annotated[str | None, "Outcome measure query (Essie syntax)"],
    query_spons: Annotated[str | None, "Sponsor/collaborator query (Essie syntax)"],
    query_lead: Annotated[str | None, "Lead sponsor name query (Essie syntax)"],
    query_id: Annotated[str | None, "Study IDs query (Essie syntax)"],
    query_patient: Annotated[str | None, "Patient search query (Essie syntax)"],
    filter_overall_status: Annotated[list[Status] | None, "List of statuses to filter by"],
    filter_ids: Annotated[list[str] | None, "List of NCT IDs to filter by"],
    filter_advanced: Annotated[str | None, "Advanced filter query (Essie syntax)"],
    filter_synonyms: Annotated[list[str] | None, "List of synonym filters ('area:id')"],
    post_filter_overall_status: Annotated[list[Status] | None, "Post-aggregation status filter"],
    post_filter_ids: Annotated[list[str] | None, "Post-aggregation NCT ID filter"],
    post_filter_advanced: Annotated[str | None, "Post-aggregation advanced filter"],
    post_filter_synonyms: Annotated[list[str] | None, "Post-aggregation synonym filter"],
    agg_filters: Annotated[str | None, "Aggregation filters string"],
    geo_decay: Annotated[str | None, "Geo decay function string"],
    fields: Annotated[list[AllowedField] | None, "List of specific fields to return (e.g., ['NCTId', 'BriefTitle', 'OverallStatus']). Returns default set if None"],
    sort_fields: Annotated[list[SortField] | None, "List of fields to sort by. Format: 'FieldName:direction' (e.g., 'LastUpdatePostDate:desc')"],
    count_total: Annotated[bool | None, "Whether to return total count"],
    page_size: Annotated[int | None, "Number of studies per page. Defaults to 10. Max 1000"],
    page_token: Annotated[str | None, "Token for retrieving the next page"],
) -> str | None:
    """Returns data of studies matching query and filter parameters.

    Assumes 'json' format is used or fetch_with_urllib can handle others.
    See: https://clinicaltrials.gov/api/v2/studies (GET)

    Status can be ACTIVE_NOT_RECRUITING | COMPLETED | ENROLLING_BY_INVITATION | NOT_YET_RECRUITING | RECRUITING | SUSPENDED | TERMINATED | WITHDRAWN | AVAILABLE | NO_LONGER_AVAILABLE | TEMPORARILY_NOT_AVAILABLE | APPROVED_FOR_MARKETING | WITHHELD | UNKNOWN

    Returns:
        A PagedStudies object containing the list of studies and pagination info, or None on error.
    """
    path = "/studies"
    filter_geo = None
    post_filter_geo = None

    if sort_fields:
        sort_strings: list[str] | None = [f"{s.field}:{s.direction}" for s in sort_fields]
    else:
        sort_strings = None

    params = {
        "format": "json",
        "markupFormat": "markdown",
        "query.cond": query_cond,
        "query.term": query_term,
        "query.locn": query_locn,
        "query.titles": query_titles,
        "query.intr": query_intr,
        "query.outc": query_outc,
        "query.spons": query_spons,
        "query.lead": query_lead,
        "query.id": query_id,
        "query.patient": query_patient,
        "filter.overallStatus": filter_overall_status,
        "filter.geo": filter_geo,
        "filter.ids": filter_ids,
        "filter.advanced": filter_advanced,
        "filter.synonyms": filter_synonyms,
        "postFilter.overallStatus": post_filter_overall_status,
        "postFilter.geo": post_filter_geo,
        "postFilter.ids": post_filter_ids,
        "postFilter.advanced": post_filter_advanced,
        "postFilter.synonyms": post_filter_synonyms,
        "aggFilters": agg_filters,
        "geoDecay": geo_decay,
        "fields": fields,
        "sort": sort_strings,
        "countTotal": count_total,
        "pageSize": page_size,
        "pageToken": page_token,
    }

    url = _build_ctg_url(CTG_API_BASE_URL, path, params)
    return fetch_with_urllib(url)


@function_tool
async def fetch_study(
    nct_id: Annotated[str, "The NCT Number (e.g., 'NCT04852770'). Required"],
) -> str | None:
    """Returns data of a single study by its NCT ID.

    Assumes 'json' format is used or fetch_with_urllib can handle others.
    See: https://clinicaltrials.gov/api/v2/studies/{nctId} (GET)

    Returns:
        A Study object containing the detailed study data, or None on error.

    Raises:
        ValueError: If nct_id is empty or None.
    """
    if not nct_id:
        raise ValueError("nct_id cannot be empty")
    path = f"/studies/{nct_id}"
    params = {
        "format":  "json",
        "markupFormat": "markdown",
        "fields": None,
    }
    url = _build_ctg_url(CTG_API_BASE_URL, path, params)
    return fetch_with_urllib(url)
