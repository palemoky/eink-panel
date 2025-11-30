"""VPS data usage provider using 64clouds API.

Fetches VPS data usage percentage with caching.
"""

import logging

import httpx

from src.config import Config
from src.core import cached
from src.exceptions import ProviderError

logger = logging.getLogger(__name__)

VPS_API_URL = "https://api.64clouds.com/v1/getServiceInfo"


@cached(ttl=600)  # Cache for 10 minutes
async def get_vps_info(client: httpx.AsyncClient) -> int:
    """Fetch VPS data usage percentage.

    Args:
        client: Async HTTP client instance

    Returns:
        Data usage percentage (0-100)

    Raises:
        ProviderError: If API request fails
    """
    if not Config.VPS_API_KEY:
        logger.warning("VPS API key not configured")
        return 0

    url = VPS_API_URL
    params = {"veid": Config.VPS_API_KEY}

    try:
        res = await client.get(url, params=params, timeout=10.0)
        res.raise_for_status()
        data = res.json()

        logger.debug(f"VPS API Response: {data}")

        # Check for API error
        error_code = data.get("error")
        if error_code is not None and error_code != 0:
            logger.warning(f"VPS API returned error code: {error_code}")
            return 0

        # Extract data usage
        data_counter = data.get("data_counter")
        plan_monthly_data = data.get("plan_monthly_data")

        if data_counter is None or plan_monthly_data is None:
            logger.error(
                f"VPS API missing required fields. data_counter={data_counter}, plan_monthly_data={plan_monthly_data}"
            )
            return 0

        if plan_monthly_data == 0:
            logger.warning("VPS plan_monthly_data is 0, cannot calculate percentage")
            return 0

        percentage = int((data_counter / plan_monthly_data) * 100)
        logger.info(f"VPS Data Usage: {percentage}% ({data_counter}/{plan_monthly_data} bytes)")
        return percentage

    except httpx.HTTPError as e:
        logger.error(f"VPS API Error: {e}")
        raise ProviderError("vps", "Failed to fetch VPS info", e) from e
    except Exception as e:
        logger.error(f"VPS API Error: {e}")
        raise ProviderError("vps", "Unexpected error", e) from e
