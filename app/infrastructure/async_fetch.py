from typing import Any, cast
import json
import urllib.request
import urllib.error
from urllib.parse import urlparse


def fetch_with_urllib(url: str, timeout: int = 30) -> dict[str, Any] | None:
    """Fetches data using the standard library's urllib.
    
    This function doesn't depend on httpx and uses only standard library components.

    Args:
        url: The URL of the external API endpoint.
        timeout: Request timeout in seconds.

    Returns:
        A dictionary containing the JSON response, or None if an error occurs.
        Logs errors encountered during the request.

    Raises:
        urllib.error.HTTPError: If the API returns an error status code (4xx or 5xx).
        urllib.error.URLError: For network-related errors.
    """
    
    try:
        print(f"Attempting to fetch data from: {url}")
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            print(f"Successfully fetched data, status code: {status_code}")
            data = response.read().decode('utf-8')
            return cast(dict[str, Any], json.loads(data))
    except urllib.error.HTTPError as e:
        print(f"HTTP error occurred: {e.code} - {e.read().decode('utf-8')}")
        raise
    except urllib.error.URLError as e:
        print(f"URL error occurred: {e.reason}")
        parsed_url = urlparse(url)
        print(f"URL components: scheme={parsed_url.scheme}, netloc={parsed_url.netloc}")
        raise
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise
