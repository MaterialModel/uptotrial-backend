import logging
import urllib.error
import urllib.request
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
def fetch_with_urllib(url: str, timeout: int = 30) -> str | None:
    """Fetches data using the standard library's urllib.
    
    This function doesn't depend on httpx and uses only standard library components.

    Args:
        url: The URL of the external API endpoint.
        timeout: Request timeout in seconds.

    Returns:
        A string containing the raw response content, or None if an error occurs.
        Logs errors encountered during the request.

    Raises:
        urllib.error.HTTPError: If the API returns an error status code (4xx or 5xx).
        urllib.error.URLError: For network-related errors.
    """
    
    try:
        logger.debug(f"Attempting to fetch data from: {url}")
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            logger.debug(f"Successfully fetched data, status code: {status_code}")
            raw_data = response.read()
            data = raw_data.decode("utf-8")
            return str(data)
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP error occurred: {e.code} - {e.read().decode('utf-8')}")
        raise
    except urllib.error.URLError as e:
        logger.error(f"URL error occurred: {e.reason}")
        parsed_url = urlparse(url)
        logger.error(f"URL components: scheme={parsed_url.scheme}, netloc={parsed_url.netloc}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise
