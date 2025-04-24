import json
from typing import Annotated, TypeVar

from agents import function_tool

from app.config import get_settings
from app.infrastructure.fetch import fetch_with_urllib

settings = get_settings()

T = TypeVar("T", bound=dict | list)

def recursive_remove_key(d: T, key: str) -> T:
    if isinstance(d, dict):
        for k, v in d.items():
            if  key in k:
                del d[k]
            elif isinstance(v, dict | list):
                recursive_remove_key(v, key)
    elif isinstance(d, list):
        for item in d:
            recursive_remove_key(item, key)
    return d


@function_tool
def search_places(query: Annotated[str, "The text string to search for (e.g., 'Boston')"]) -> str | None:
    """Search for places using a text query via Google Places API.
       This can be useful to provide valid locations for a clinical trials api.

    Returns:
        dict: Response from Google Places API containing search results
    """
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={settings.google_places_api_key}"
    val = fetch_with_urllib(url)
    if val:
        try:
            d = json.loads(val)
            assert isinstance(d, dict | list)
            d = recursive_remove_key(d, "photo")
            return json.dumps(d)
        except json.JSONDecodeError:
            pass
    return val
