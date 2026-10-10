from sqlalchemy import String, Text, Float, Integer, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase): pass


class Favorite(Base):
    __tablename__ = "favorites"
    id: Mapped[int] = mapped_column(primary_key=True)
    content_identifier: Mapped[str] = mapped_column(String, unique=True)
    content_type: Mapped[str]
    title: Mapped[str]
    poster_url: Mapped[str]
    date_added: Mapped[float]
    payload: Mapped[str] = mapped_column(Text)


class WatchHistory(Base):
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
    __tablename__ = "search_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    query: Mapped[str] = mapped_column(unique=True)
    timestamp: Mapped[float]


class SearchCache(Base):
    __tablename__ = "search_cache"
    key: Mapped[str] = mapped_column(primary_key=True)
    query: Mapped[str]
    provider: Mapped[str]
    results: Mapped[str] = mapped_column(Text)
    created: Mapped[float]
    expires: Mapped[float]


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column(Text)


class LibraryVideo(Base):
    __tablename__ = "library_videos"
    key: Mapped[str] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(default="General")
    payload: Mapped[str] = mapped_column(Text)
    discovered: Mapped[float]
    updated: Mapped[float]
