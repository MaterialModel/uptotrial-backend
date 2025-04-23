# Standard library imports first
import logging
from typing import Any, Literal
from urllib.parse import urlencode, urljoin

from agents import function_tool

# Third-party imports
from pydantic import ValidationError

# Local modules
from app.infrastructure.async_fetch import fetch_external_data

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
    query_cond: str | None,
    query_term: str | None,
    query_locn: str | None,
    query_titles: str | None,
    query_intr: str | None,
    query_outc: str | None,
    query_spons: str | None,
    query_lead: str | None,
    query_id: str | None,
    query_patient: str | None,
    filter_overall_status: list[Status] | None,
    filter_geo: str | None,
    filter_ids: list[str] | None,
    filter_advanced: str | None,
    filter_synonyms: list[str] | None,
    post_filter_overall_status: list[Status] | None,
    post_filter_geo: str | None,
    post_filter_ids: list[str] | None,
    post_filter_advanced: str | None,
    post_filter_synonyms: list[str] | None,
    agg_filters: str | None,
    geo_decay: str | None,
    fields: list[AllowedField] | None,
    sort: list[str] | None,
    count_total: bool | None,
    page_size: int | None,
    page_token: str | None,
) -> str | None:
    """Returns data of studies matching query and filter parameters.

    Assumes 'json' format is used or fetch_external_data can handle others.
    See: https://clinicaltrials.gov/api/v2/studies (GET)

    Args:
        query_cond: Condition/disease query (Essie syntax). Defaults to None.
        query_term: Other terms query (Essie syntax). Defaults to None.
        query_locn: Location terms query (Essie syntax). Defaults to None.
        query_titles: Title/acronym query (Essie syntax). Defaults to None.
        query_intr: Intervention/treatment query (Essie syntax). Defaults to None.
        query_outc: Outcome measure query (Essie syntax). Defaults to None.
        query_spons: Sponsor/collaborator query (Essie syntax). Defaults to None.
        query_lead: Lead sponsor name query (Essie syntax). Defaults to None.
        query_id: Study IDs query (Essie syntax). Defaults to None.
        query_patient: Patient search query (Essie syntax). Defaults to None.
        filter_overall_status: List of statuses to filter by. Defaults to None.
        filter_geo: Geo-distance filter function string. Defaults to None.
        filter_ids: List of NCT IDs to filter by. Defaults to None.
        filter_advanced: Advanced filter query (Essie syntax). Defaults to None.
        filter_synonyms: List of synonym filters ('area:id'). Defaults to None.
        post_filter_overall_status: Post-aggregation status filter. Uses Status literal. Defaults to None.
        post_filter_geo: Post-aggregation geo filter. Defaults to None.
        post_filter_ids: Post-aggregation NCT ID filter. Defaults to None.
        post_filter_advanced: Post-aggregation advanced filter. Defaults to None.
        post_filter_synonyms: Post-aggregation synonym filter. Defaults to None.
        agg_filters: Aggregation filters string. Defaults to None.
        geo_decay: Geo decay function string. Defaults to None.
        fields: List of specific fields to return (e.g., ["NCTId", "BriefTitle", "OverallStatus"]). Uses AllowedField literal. Defaults to None (returns default set).
        sort: List of fields to sort by. Format: 'FieldName:direction' where FieldName is from AllowedField and direction is from SortDirection (e.g., 'LastUpdatePostDate:desc'). Defaults to None.
        count_total: Whether to return total count. Defaults to False.
        page_size: Number of studies per page. Defaults to 10. Max 1000.
        page_token: Token for retrieving the next page. Defaults to None.

        Status can be ACTIVE_NOT_RECRUITING | COMPLETED | ENROLLING_BY_INVITATION | NOT_YET_RECRUITING | RECRUITING | SUSPENDED | TERMINATED | WITHDRAWN | AVAILABLE | NO_LONGER_AVAILABLE | TEMPORARILY_NOT_AVAILABLE | APPROVED_FOR_MARKETING | WITHHELD | UNKNOWN

    Returns:
        A PagedStudies object containing the list of studies and pagination info, or None on error.
    """
    path = "/studies"
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
        "sort": sort,
        "countTotal": count_total,
        "pageSize": page_size,
        "pageToken": page_token,
    }

    url = _build_ctg_url(CTG_API_BASE_URL, path, params)
    data = await fetch_external_data(url)
    if data:
        return str(data)
    return None


@function_tool
async def fetch_study(
    nct_id: str,
) -> str | None:
    """Returns data of a single study by its NCT ID.

    Assumes 'json' format is used or fetch_external_data can handle others.
    See: https://clinicaltrials.gov/api/v2/studies/{nctId} (GET)

    Args:
        nct_id: The NCT Number (e.g., "NCT04852770"). Required.

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
    data = await fetch_external_data(url)
    if data:
        try:
            return str(data)
        except ValidationError as e:
            logger.error(f"Pydantic validation error for fetch_study ({nct_id}): {e}")
            return None
    return None
