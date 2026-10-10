# ==========================================================================
"""models.py
Declare persistent database records without opening a database at import time.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lourihna_films.database.models import WatchHistory

from sqlalchemy import Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Own Base state and its explicit application contracts."""

    pass


class Favorite(Base):
    """Own Favorite state and its explicit application contracts."""

    __tablename__ = "favorites"
    id: Mapped[int] = mapped_column(primary_key=True)
    content_identifier: Mapped[str] = mapped_column(String, unique=True)
    content_type: Mapped[str]
    title: Mapped[str]
    poster_url: Mapped[str]
    date_added: Mapped[float]
    payload: Mapped[str] = mapped_column(Text)


class WatchHistory(Base):
    """Own WatchHistory state and its explicit application contracts."""

    __tablename__ = "watch_history"
    __table_args__ = (UniqueConstraint("provider", "video_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str]
    video_id: Mapped[str]
    title: Mapped[str]
    last_watched: Mapped[float]
    position: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[str] = mapped_column(Text)


class SearchHistory(Base):
    """Own SearchHistory state and its explicit application contracts."""

    __tablename__ = "search_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    query: Mapped[str] = mapped_column(unique=True)
    timestamp: Mapped[float]


class SearchCache(Base):
    """Own SearchCache state and its explicit application contracts."""

    __tablename__ = "search_cache"
    key: Mapped[str] = mapped_column(primary_key=True)
    query: Mapped[str]
    provider: Mapped[str]
    results: Mapped[str] = mapped_column(Text)
    created: Mapped[float]
    expires: Mapped[float]


class Setting(Base):
    """Own Setting state and its explicit application contracts."""

    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column(Text)


class LibraryVideo(Base):
    """Own LibraryVideo state and its explicit application contracts."""

    __tablename__ = "library_videos"
    key: Mapped[str] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(default="General")
    payload: Mapped[str] = mapped_column(Text)
    discovered: Mapped[float]
    updated: Mapped[float]
