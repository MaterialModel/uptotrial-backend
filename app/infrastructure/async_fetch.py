from typing import Any, cast

import httpx


async def fetch_external_data(url: str) -> dict[str, Any] | None:
    """Fetches data asynchronously from an external URL.

    Args:
        url: The URL of the external API endpoint.

    Returns:
        A dictionary containing the JSON response, or None if an error occurs.
        Logs errors encountered during the request.

    Raises:
        httpx.HTTPStatusError: If the API returns an error status code (4xx or 5xx).
        httpx.RequestError: For other request-related issues (network, timeout, etc.).
    """
    try:
        async with httpx.AsyncClient() as client:
            print(f"Attempting to fetch data from: {url}")
            response = await client.get(url)
            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
            print(f"Successfully fetched data, status code: {response.status_code}")
            return cast(dict[str, Any], response.json())
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        # Re-raise or handle specific status codes as needed
        raise
    except httpx.RequestError as e:
        print(f"An error occurred while requesting {e.request.url!r}: {e}")
        # Handle network errors, timeouts, etc.
        raise # Or return None, depending on desired behavior
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Handle other potential errors (e.g., JSON decoding)
        raise # Or return None
