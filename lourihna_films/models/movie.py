# ==========================================================================
"""movie.py
Represent catalog metadata independently of playback availability.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

from pydantic import BaseModel, Field


class CatalogItem(BaseModel):
    """Represent movie or series metadata independently of public video availability."""

    id: int
    kind: str
    title: str
    year: str = ""
    poster: str = ""
    backdrop: str = ""
    overview: str = ""
    rating: float = 0
    genres: list[str] = Field(default_factory=list)
    runtime: int | None = None
    alternatives: list[str] = Field(default_factory=list)
    seasons: list[dict] = Field(default_factory=list)
    related: list[dict] = Field(default_factory=list)

    def card(self) -> dict[str, Any]:
        """Normalize this item into the existing QML card schema."""
        return {
            **self.model_dump(),
            "key": f"{self.kind}:{self.id}",
            "badge": "TMDB · find a video",
        }
