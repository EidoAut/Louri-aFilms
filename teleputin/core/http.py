import asyncio
import httpx
from teleputin.core.exceptions import ServiceError


async def get_json(client, url, **kwargs):
    for attempt in range(3):
        try:
            response = await client.get(url, **kwargs)
            if response.status_code in (401, 403):
                raise ServiceError("Access denied. Check your API credentials and subscription in Settings.")
            if response.status_code == 429 or response.status_code >= 500:
                delay = response.headers.get("Retry-After", "")
                wait = float(delay) if delay.isdigit() else 2 ** attempt
                if attempt == 2 or wait > 15:
                    raise ServiceError("The service is busy or rate limited. Please try again later.")
                await asyncio.sleep(max(1, wait))
                continue
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Expected an object")
            return data
        except httpx.RequestError:
            if attempt == 2:
                raise ServiceError("Unable to connect. Check your connection and try again.") from None
            await asyncio.sleep(2 ** attempt)
        except (httpx.HTTPStatusError, ValueError):
            raise ServiceError("The service returned an unavailable or invalid response.") from None
