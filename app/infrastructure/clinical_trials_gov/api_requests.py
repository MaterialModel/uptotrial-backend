from app.infrastructure.async_fetch import fetch_external_data

# Standard library imports first
import logging
from typing import Any
from urllib.parse import urlencode, urljoin

# Third-party imports
from pydantic import ValidationError

# Local modules
from app.infrastructure.async_fetch import fetch_external_data
# Import Pydantic models from schemas
from app.infrastructure.clinical_trials_gov.schemas.common import (
    FieldNode,
    FieldValuesStats,
    GzipStats,
    ListSizes,
    SearchDocument,
    Version,
    EnumInfo,
)
from app.infrastructure.clinical_trials_gov.schemas.study import PagedStudies, Study

# Base URL for the ClinicalTrials.gov API v2
CTG_API_BASE_URL = "https://clinicaltrials.gov/api/v2"

# Setup logger
logger = logging.getLogger(__name__)


# Helper function
def _build_ctg_url(base_url: str, path: str, params: dict[str, Any] | None) -> str:
    """Builds the full URL for a CTG API request, handling parameter encoding.

    Handles boolean conversion to lower case strings and joins lists
    with appropriate separators (comma or pipe) based on known API parameter styles.
    Filters out parameters with None values.

    Args:
        base_url: The base API URL.
        path: The specific endpoint path.
        params: Dictionary of query parameters.

    Returns:
        The fully constructed URL string.
    """
    # Ensure base_url ends with a single slash and path starts without one for urljoin
    full_path = urljoin(base_url.rstrip('/') + '/', path.lstrip('/'))

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

async def list_studies(
    format: str | None = "json",
    markup_format: str | None = "markdown",
    query_cond: str | None = None,
    query_term: str | None = None,
    query_locn: str | None = None,
    query_titles: str | None = None,
    query_intr: str | None = None,
    query_outc: str | None = None,
    query_spons: str | None = None,
    query_lead: str | None = None,
    query_id: str | None = None,
    query_patient: str | None = None,
    filter_overall_status: list[str] | None = None,
    filter_geo: str | None = None,
    filter_ids: list[str] | None = None,
    filter_advanced: str | None = None,
    filter_synonyms: list[str] | None = None,
    post_filter_overall_status: list[str] | None = None,
    post_filter_geo: str | None = None,
    post_filter_ids: list[str] | None = None,
    post_filter_advanced: str | None = None,
    post_filter_synonyms: list[str] | None = None,
    agg_filters: str | None = None,
    geo_decay: str | None = None,
    fields: list[str] | None = None,
    sort: list[str] | None = None,
    count_total: bool | None = False,
    page_size: int | None = 10,
    page_token: str | None = None,
) -> PagedStudies | None:
    """Returns data of studies matching query and filter parameters.

    Assumes 'json' format is used or fetch_external_data can handle others.
    See: https://clinicaltrials.gov/api/v2/studies (GET)

    Args:
        format: Response format ('csv' or 'json'). Defaults to 'json'. Non-json may not work reliably.
        markup_format: Format for markup fields ('markdown' or 'legacy'). Defaults to 'markdown'.
        query_cond: Condition/disease query (Essie syntax).
        query_term: Other terms query (Essie syntax).
        query_locn: Location terms query (Essie syntax).
        query_titles: Title/acronym query (Essie syntax).
        query_intr: Intervention/treatment query (Essie syntax).
        query_outc: Outcome measure query (Essie syntax).
        query_spons: Sponsor/collaborator query (Essie syntax).
        query_lead: Lead sponsor name query (Essie syntax).
        query_id: Study IDs query (Essie syntax).
        query_patient: Patient search query (Essie syntax).
        filter_overall_status: List of statuses to filter by.
        filter_geo: Geo-distance filter function string.
        filter_ids: List of NCT IDs to filter by.
        filter_advanced: Advanced filter query (Essie syntax).
        filter_synonyms: List of synonym filters ('area:id').
        post_filter_overall_status: Post-aggregation status filter.
        post_filter_geo: Post-aggregation geo filter.
        post_filter_ids: Post-aggregation NCT ID filter.
        post_filter_advanced: Post-aggregation advanced filter.
        post_filter_synonyms: Post-aggregation synonym filter.
        agg_filters: Aggregation filters string.
        geo_decay: Geo decay function string.
        fields: List of fields to return.
        sort: List of fields to sort by (e.g., 'LastUpdatePostDate:desc').
        count_total: Whether to return total count. Defaults to False.
        page_size: Number of studies per page. Defaults to 10. Max 1000.
        page_token: Token for retrieving the next page.

    Returns:
        A PagedStudies object containing the list of studies and pagination info, or None on error.
    """
    path = "/studies"
    params = {
        "format": format,
        "markupFormat": markup_format,
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
        try:
            return PagedStudies.model_validate(data)
        except ValidationError as e:
            logger.error(f"Pydantic validation error for list_studies: {e}")
            return None
    return None


async def fetch_study(
    nct_id: str,
    format: str | None = "json",
    markup_format: str | None = "markdown",
    fields: list[str] | None = None,
) -> Study | None:
    """Returns data of a single study by its NCT ID.

    Assumes 'json' format is used or fetch_external_data can handle others.
    See: https://clinicaltrials.gov/api/v2/studies/{nctId} (GET)

    Args:
        nct_id: The NCT Number (e.g., "NCT04852770"). Required.
        format: Response format ('csv', 'json', 'json.zip', 'fhir.json', 'ris'). Defaults to 'json'. Non-json may not work reliably.
        markup_format: Format for markup fields ('markdown' or 'legacy'). Defaults to 'markdown'. Applicable to 'json' format only.
        fields: List of fields to return. Applicable to 'csv', 'json', 'json.zip', 'ris'.

    Returns:
        A Study object containing the detailed study data, or None on error.

    Raises:
        ValueError: If nct_id is empty or None.
    """
    if not nct_id:
        raise ValueError("nct_id cannot be empty")
    path = f"/studies/{nct_id}"
    params = {
        "format": format,
        "markupFormat": markup_format,
        "fields": fields,
    }
    url = _build_ctg_url(CTG_API_BASE_URL, path, params)
    data = await fetch_external_data(url)
    if data:
        try:
            return Study.model_validate(data)
        except ValidationError as e:
            logger.error(f"Pydantic validation error for fetch_study ({nct_id}): {e}")
            return None
    return None


async def studies_metadata(
    include_indexed_only: bool | None = False,
    include_historic_only: bool | None = False,
) -> list[FieldNode] | None:
    """Returns study data model fields.

    See: https://clinicaltrials.gov/api/v2/studies/metadata (GET)

    Args:
        include_indexed_only: Include indexed-only fields if True. Defaults to False.
        include_historic_only: Include fields available only in historic data if True. Defaults to False.

    Returns:
        A list of FieldNode objects describing the data model, or None on error.
    """
    path = "/studies/metadata"
    params = {
        "includeIndexedOnly": include_indexed_only,
        "includeHistoricOnly": include_historic_only,
    }
    url = _build_ctg_url(CTG_API_BASE_URL, path, params)
    data = await fetch_external_data(url)
    if isinstance(data, list):
        try:
            return [FieldNode.model_validate(item) for item in data]
        except ValidationError as e:
            logger.error(f"Pydantic validation error for studies_metadata: {e}")
            return None
    elif data:
        logger.error(f"Unexpected data type for studies_metadata: {type(data)}")
    return None


async def search_areas() -> list[SearchDocument] | None:
    """Returns search documents and their search areas.

    See: https://clinicaltrials.gov/api/v2/studies/search-areas (GET)

    Returns:
        A list of SearchDocument objects, or None on error.
    """
    path = "/studies/search-areas"
    url = _build_ctg_url(CTG_API_BASE_URL, path, None)
    data = await fetch_external_data(url)
    if isinstance(data, list):
        try:
            return [SearchDocument.model_validate(item) for item in data]
        except ValidationError as e:
            logger.error(f"Pydantic validation error for search_areas: {e}")
            return None
    elif data:
        logger.error(f"Unexpected data type for search_areas: {type(data)}")
    return None


async def enums() -> list[EnumInfo] | None:
    """Returns enumeration types and their values.

    See: https://clinicaltrials.gov/api/v2/studies/enums (GET)

    Returns:
        A list of EnumInfo objects describing API enums, or None on error.
    """
    path = "/studies/enums"
    url = _build_ctg_url(CTG_API_BASE_URL, path, None)
    data = await fetch_external_data(url)
    if isinstance(data, list):
        try:
            return [EnumInfo.model_validate(item) for item in data]
        except ValidationError as e:
            logger.error(f"Pydantic validation error for enums: {e}")
            return None
    elif data:
        logger.error(f"Unexpected data type for enums: {type(data)}")
    return None


async def size_stats() -> GzipStats | None:
    """Returns statistics of study JSON sizes.

    See: https://clinicaltrials.gov/api/v2/stats/size (GET)

    Returns:
        A GzipStats object containing statistics about study JSON sizes, or None on error.
    """
    path = "/stats/size"
    url = _build_ctg_url(CTG_API_BASE_URL, path, None)
    data = await fetch_external_data(url)
    if data:
        try:
            return GzipStats.model_validate(data)
        except ValidationError as e:
            logger.error(f"Pydantic validation error for size_stats: {e}")
            return None
    return None


async def field_values_stats(
    types: list[str] | None = None, fields: list[str] | None = None
) -> list[FieldValuesStats] | None:
    """Returns value statistics of the study leaf fields.

    See: https://clinicaltrials.gov/api/v2/stats/field/values (GET)

    Args:
        types: List of field types to filter by (e.g., ['ENUM', 'BOOLEAN']).
        fields: List of piece names or field paths to filter by.

    Returns:
        A list of FieldValuesStats objects containing value statistics, or None on error.
    """
    path = "/stats/field/values"
    params = {
        "types": types,
        "fields": fields,
    }
    url = _build_ctg_url(CTG_API_BASE_URL, path, params)
    data = await fetch_external_data(url)
    if isinstance(data, list):
        try:
            return [FieldValuesStats.model_validate(item) for item in data]
        except ValidationError as e:
            logger.error(f"Pydantic validation error for field_values_stats: {e}")
            return None
    elif data:
        logger.error(f"Unexpected data type for field_values_stats: {type(data)}")
    return None


async def list_field_sizes_stats(
    fields: list[str] | None = None
) -> list[ListSizes] | None:
    """Returns sizes of list/array fields.

    See: https://clinicaltrials.gov/api/v2/stats/field/sizes (GET)

    Args:
        fields: List of piece names or field paths to filter by.

    Returns:
        A list of ListSizes objects with statistics, or None on error.
    """
    path = "/stats/field/sizes"
    params = {"fields": fields}
    url = _build_ctg_url(CTG_API_BASE_URL, path, params)
    data = await fetch_external_data(url)
    if isinstance(data, list):
        try:
            return [ListSizes.model_validate(item) for item in data]
        except ValidationError as e:
            logger.error(f"Pydantic validation error for list_field_sizes_stats: {e}")
            return None
    elif data:
        logger.error(f"Unexpected data type for list_field_sizes_stats: {type(data)}")
    return None


async def version() -> Version | None:
    """Returns API and data versions.

    See: https://clinicaltrials.gov/api/v2/version (GET)

    Returns:
        A Version object containing API and data timestamp, or None on error.
    """
    path = "/version"
    url = _build_ctg_url(CTG_API_BASE_URL, path, None)
    data = await fetch_external_data(url)
    if data:
        try:
            return Version.model_validate(data)
        except ValidationError as e:
            logger.error(f"Pydantic validation error for version: {e}")
            return None
    return None
