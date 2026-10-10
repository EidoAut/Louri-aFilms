# ==========================================================================
"""test_integrated_playback.py
Verify integrated playback contracts using isolated fixtures.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

import pytest

from lourihna_films.core import secrets
from lourihna_films.core.exceptions import ServiceError
from lourihna_films.providers.archive import public_files
from lourihna_films.services.candidate_service import queries


def test_archive_files_are_bounded_public_and_encoded():
    data = {
        "metadata": {},
        "files": [
            {"name": "secret.mp4", "private": "true"},
            {"name": "../bad.mp4"},
            {"name": "large.mp4", "size": "90000"},
            {"name": "film one.mp4", "size": "5000"},
            {"name": "film.webm", "size": "4000"},
            {"name": "thumb.jpg"},
            {"name": "film.ogv", "size": "1000"},
        ],
    }
    result = public_files(data, "item")
    assert len(result) == 4
    assert result[0]["url"] == "https://archive.org/download/item/film%20one.mp4"
    assert all("bad" not in x["url"] and "secret" not in x["url"] for x in result)


@pytest.mark.parametrize(
    "data",
    [
        {"metadata": {}, "files": [{"name": "__ia_thumb.jpg"}]},
        {"is_dark": True, "metadata": {}, "files": [{"name": "film.mp4"}]},
        {
            "metadata": {"access-restricted-item": "true"},
            "files": [{"name": "film.mp4"}],
        },
        {"nodownload": True, "metadata": {}, "files": [{"name": "film.mp4"}]},
    ],
)
def test_archive_missing_or_restricted_video_never_becomes_playable(data):
    with pytest.raises(ServiceError):
        public_files(data, "item")


def test_episode_queries_preserve_both_numbering_and_original_title():
    result = queries(
        {
            "title": "Título",
            "original_title": "Original",
            "episode_number": 3,
            "season_number": 2,
            "episode_title": "Episode",
        }
    )
    assert "Título S02E03" in result
    assert "Original 2x03 Episode" in result
    assert len(result) <= 4


def test_linux_session_credentials_never_persist_plaintext(monkeypatch):
    monkeypatch.setattr(secrets, "WINDOWS", False)
    reference = secrets.protect("test-credential-value")
    assert reference.startswith("session:") and "credential" not in reference
    assert secrets.reveal(reference) == "test-credential-value"
    secrets.SESSION_SECRETS.clear()
    assert secrets.reveal(reference) == ""


def test_archive_malformed_files_and_duplicate_formats():
    with pytest.raises(ServiceError):
        public_files({"metadata": [], "files": None}, "item")
    results = public_files(
        {"files": [{"name": "film.mp4", "size": float("inf")}] * 5}, "item"
    )
    assert len(results) == 1
