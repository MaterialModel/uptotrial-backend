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

Phase = Literal["NA", "EARLY_PHASE1", "PHASE1", "PHASE2", "PHASE3", "PHASE4"]

StudyType = Literal["EXPANDED_ACCESS", "INTERVENTIONAL", "OBSERVATIONAL"]

Sex = Literal["FEMALE", "MALE", "ALL"]

StandardAge = Literal["CHILD", "ADULT", "OLDER_ADULT"]

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

# New Pydantic models for more semantic parameter grouping
class DiseaseInfo(BaseModel):
    """Information about a disease/condition and its synonyms."""
    name: str
    synonyms: list[str] | None = None

class SubtypeInfo(BaseModel):
    """Information about disease subtypes (mutations, histology, stage, etc.)."""
    name: str
    synonyms: list[str] | None = None

class InterventionInfo(BaseModel):
    """Information about an intervention/treatment and its synonyms."""
    name: str
    synonyms: list[str] | None = None

# New helper function for creating Essie syntax queries
def _or_block(term: str, synonyms: list[str] | None = None) -> str:
    """Return `(foo OR "bar baz")` in Essie syntax.
    
    Args:
        term: Main search term
        synonyms: Optional list of synonyms or alternative terms
        
    Returns:
        Essie syntax query string with terms combined with OR
    """
    if not term:
        return ""
    toks = [term] + (synonyms or [])
    toks = [f'"{t}"' if " " in t else t for t in toks]
    return f"({' OR '.join(toks)})"


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
    # Semantic disease/condition parameters
    disease: Annotated[DiseaseInfo | None, "Information about the disease/condition to search for"],
    subtype: Annotated[SubtypeInfo | None, "Information about disease subtype (mutations, histology, stage, etc.)"],
    intervention: Annotated[InterventionInfo | None, "Information about the intervention/treatment to search for"],
    location: Annotated[str | None, "Geographic location for the study (city, state, country)"],
    
    # Study characteristics using Literals for validation
    phases: Annotated[list[Phase] | None, "List of study phases to include"],
    study_types: Annotated[list[StudyType] | None, "List of study types to include"],
    statuses: Annotated[list[Status] | None, "List of study statuses to filter by"],
    
    # Demographic filters using Literals for validation
    sexes: Annotated[list[Sex] | None, "List of sex categories to include"],
    standard_ages: Annotated[list[StandardAge] | None, "List of age groups to include"],
    
    # Results filter
    with_results: Annotated[bool | None, "Filter to studies with posted results"],
    
    # Additional query parameters (preserved from original)
    query_titles: Annotated[str | None, "Title/acronym query (Essie syntax)"],
    query_outc: Annotated[str | None, "Outcome measure query (Essie syntax)"],
    query_spons: Annotated[str | None, "Sponsor/collaborator query (Essie syntax)"],
    query_lead: Annotated[str | None, "Lead sponsor name query (Essie syntax)"],
    query_id: Annotated[str | None, "Study IDs query (Essie syntax)"],
    query_patient: Annotated[str | None, "Patient search query (Essie syntax)"],
    
    # ID filtering
    filter_ids: Annotated[list[str] | None, "List of NCT IDs to filter by"],
    filter_synonyms: Annotated[list[str] | None, "List of synonym filters ('area:id')"],
    
    # Geographic filters
    filter_geo: Annotated[str | None, "Geo-distance filter (e.g., 'distance(lat,lon,radius)')"],
    geo_decay: Annotated[str | None, "Geo decay function string"],
    
    # Post-filtering parameters
    post_filter_overall_status: Annotated[list[Status] | None, "Post-aggregation status filter"],
    post_filter_geo: Annotated[str | None, "Post-aggregation geo filter"],
    post_filter_ids: Annotated[list[str] | None, "Post-aggregation NCT ID filter"],
    post_filter_advanced: Annotated[str | None, "Post-aggregation advanced filter"],
    post_filter_synonyms: Annotated[list[str] | None, "Post-aggregation synonym filter"],
    
    # Other parameters
    agg_filters: Annotated[str | None, "Aggregation filters string"],
    fields: Annotated[list[AllowedField] | None, "List of specific fields to return (e.g., ['NCTId', 'BriefTitle', 'OverallStatus']). Returns default set if None"],
    sort_fields: Annotated[list[SortField] | None, "List of fields to sort by"],
    count_total: Annotated[bool | None, "Whether to return total count"],
    page_size: Annotated[int | None, "Number of studies per page. Defaults to 10. Max 1000"],
    page_token: Annotated[str | None, "Token for retrieving the next page"],
) -> str | None:
    """Returns data of studies matching query and filter parameters.
    
    Provides semantically meaningful parameters (disease, subtype, intervention)
    while preserving the original API parameters for advanced use cases.
    
    Examples:
        To search for "Phase 2 or 3 IDH mutant ICC immunotherapy trials for adults":
        
        disease=DiseaseInfo(
            name="Intrahepatic Cholangiocarcinoma",
            synonyms=["biliary cancer", "cholangiocarcinoma"]
        ),
        subtype=SubtypeInfo(
            name="IDH mutant",
            synonyms=["IDH1 mutant", "IDH2 mutant"]
        ),
        intervention=InterventionInfo(
            name="immunotherapy",
            synonyms=["immune checkpoint inhibitor", "pembrolizumab"]
        ),
        phases=["PHASE2", "PHASE3"],
        standard_ages=["ADULT"]

    Returns:
        A PagedStudies object containing the list of studies and pagination info, or None on error.
    """
    path = "/studies"
    
    # Build query parameters from semantic parameters
    query_cond = None
    query_term = None
    query_locn = location
    query_intr = None
    filter_advanced = None
    
    # Convert disease info to condition query
    if disease:
        query_cond = _or_block(disease.name, disease.synonyms)
    
    # Build query term from subtype and intervention
    query_components = []
    
    if subtype:
        query_components.append(_or_block(subtype.name, subtype.synonyms))
    
    if intervention:
        query_intr = _or_block(intervention.name, intervention.synonyms)
    
    if query_components:
        query_term = " AND ".join(query_components)
    
    # Build advanced filter components for study characteristics
    adv_chunks = []
    
    if phases:
        adv_chunks.append("(" + " OR ".join(f"AREA[Phase]{p}" for p in phases) + ")")
    
    if sexes:
        adv_chunks.append("(" + " OR ".join(f"AREA[Sex]{s}" for s in sexes) + ")")
    
    if standard_ages:
        adv_chunks.append("(" + " OR ".join(f"AREA[StdAge]{a}" for a in standard_ages) + ")")
    
    if study_types:
        adv_chunks.append("(" + " OR ".join(f"AREA[StudyType]{st}" for st in study_types) + ")")
    
    # Combine advanced filter components
    if adv_chunks:
        filter_advanced = " AND ".join(adv_chunks)
    
    # Handle with_results filter (studies that have posted results)
    if with_results:
        if agg_filters:
            agg_filters = f"{agg_filters},results:with"
        else:
            agg_filters = "results:with"
    
    # Format sort fields
    if sort_fields:
        sort_strings = [f"{s.field}:{s.direction}" for s in sort_fields]
    else:
        # Default to relevance and enrollment count
        sort_strings = ["@relevance", "EnrollmentCount:desc"]
    
    # Build final parameters
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
        "filter.overallStatus": statuses,
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
