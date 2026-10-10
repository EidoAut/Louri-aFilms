import html
import json
import pytest
from teleputin.providers.public_media import MediaParser, media_url_allowed


def document(identifier="123", url="https://vd296.okcdn.ru/video.mp4?token=test", provider="UPLOADED_ODKL", **extra):
    metadata = {"provider": provider, "movie": {"id": identifier}, "videos": [{"name": "low", "url": url}], **extra}
    return '<div data-options="' + html.escape(json.dumps({"flashvars": {"metadata": json.dumps(metadata)}}), quote=True) + '"></div>'


def test_reads_public_metadata_without_evaluating_scripts():
    parser = MediaParser("123")
    parser.feed(document())
    assert parser.formats == [(2, "https://vd296.okcdn.ru/video.mp4?token=test")]


@pytest.mark.parametrize("page", [document(identifier="456"), document(provider="OTHER"), document(drm=True), document(licenseUrl="https://example.org/license"), '<div data-options="invalid">', '<div data-options="[]">', "Login required"])
def test_rejects_unrelated_restricted_or_changed_markup(page):
    parser = MediaParser("123")
    parser.feed(page)
    assert not parser.formats


@pytest.mark.parametrize("url", ["http://vd296.okcdn.ru/video", "https://okcdn.ru.evil.org/video", "https://127.0.0.1/video", "file:///movie.mp4", "https://user:secret@vd296.okcdn.ru/video", "https://vd296.okcdn.ru:444/video", "https://vd296.okcdn.ru/video#fragment"])
def test_rejects_untrusted_media_urls(url):
    assert not media_url_allowed(url)
