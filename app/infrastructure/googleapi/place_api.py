import json
from typing import Annotated, TypeVar
from urllib.parse import quote

from agents import function_tool

from app.config import get_settings
from app.infrastructure.fetch import fetch_with_urllib

settings = get_settings()

T = TypeVar("T", bound=dict | list)


def recursive_remove_key(d: T, keys: list[str]) -> T:
    if isinstance(d, dict):
        keys_to_remove = [k for k in d.keys() if any(key in k for key in keys)]
        for k in keys_to_remove:
            del d[k]
        for v in d.values():
            if isinstance(v, dict | list):
                recursive_remove_key(v, keys)
    elif isinstance(d, list):
        for item in d:
            recursive_remove_key(item, keys)
    return d


@function_tool
def search_places(query: Annotated[str, "The text string to search for (e.g., 'Boston')"]) -> str | None:
    """Search for places using a text query via Google Places API.
       This can be useful to provide valid locations for a clinical trials api.

    Returns:
        dict: Response from Google Places API containing search results
    """
    encoded_query = quote(query)
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={encoded_query}&key={settings.google_places_api_key}"
    val = fetch_with_urllib(url)
    if val:
        try:
            d = json.loads(val)
            assert isinstance(d, dict | list)
            d = recursive_remove_key(d, ["photo", "icon"])
            return json.dumps(d)
        except json.JSONDecodeError:
            pass
    return val
