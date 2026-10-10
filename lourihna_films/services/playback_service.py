# ==========================================================================
"""playback_service.py
Resolve official embed navigation only; never resolve media streams.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from typing import Any

from lourihna_films.core.exceptions import ServiceError
from lourihna_films.models.okru_identity import OKRuIdentity


def resolve_okru(item: dict[str, Any]) -> dict[str, Any]:
    """Validate the selected video identity and return its official playback descriptor."""
    if item.get("provider") != "okru" or item.get("kind") != "video":
        raise ServiceError("This video source is unsupported.")
    if item.get("is_embeddable") is False:
        raise ServiceError(
            "Embedding is unavailable for this video. Open the original page."
        )
    identity = OKRuIdentity.from_url(item.get("original_url"))
    return {
        **item,
        "id": identity.identifier,
        "key": f"okru:{identity.identifier}",
        "original_url": identity.original_url,
        "embed_url": identity.embed_url,
    }
