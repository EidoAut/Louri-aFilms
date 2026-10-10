# ==========================================================================
"""http.py
Provide http operations for explicit application requests.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import asyncio
from typing import Any

import httpx

from lourihna_films.core.exceptions import ServiceError

HTTP_MAX_ATTEMPTS = 3
HTTP_MAX_RETRY_DELAY_SECONDS = 15


async def get_json(
    client: httpx.AsyncClient, url: str, **kwargs: Any
) -> dict[str, Any]:
    """Fetch a JSON object with bounded retries; raise ServiceError on terminal failure."""
    for attempt in range(HTTP_MAX_ATTEMPTS):
        try:
            response = await client.get(url, **kwargs)
            if response.status_code in (401, 403):
                raise ServiceError(
                    "Access denied. Check your API credentials and subscription in Settings."
                )
            if response.status_code == 429 or response.status_code >= 500:
                delay = response.headers.get("Retry-After", "")
                wait = float(delay) if delay.isdigit() else 2**attempt
                if (
                    attempt == HTTP_MAX_ATTEMPTS - 1
                    or wait > HTTP_MAX_RETRY_DELAY_SECONDS
                ):
                    raise ServiceError(
                        "The service is busy or rate limited. Please try again later."
                    )
                await asyncio.sleep(max(1, wait))
                continue
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Expected an object")
            return data
        except httpx.RequestError:
            if attempt == HTTP_MAX_ATTEMPTS - 1:
                raise ServiceError(
                    "Unable to connect. Check your connection and try again."
                ) from None
            await asyncio.sleep(2**attempt)
        except (httpx.HTTPStatusError, ValueError):
            raise ServiceError(
                "The service returned an unavailable or invalid response."
            ) from None
