import zipfile
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import pytest
from teleputin.services.translation_service import TranslationService, unpack_model
from teleputin.services.tmdb_service import TMDBService
from teleputin.core.exceptions import ServiceError


@pytest.mark.asyncio
async def test_missing_synopsis_translates_english_but_keeps_original():
    translator = SimpleNamespace(translate=AsyncMock(return_value="Sinopsis traducida"))
    service = TMDBService(None, language="gl-ES", translator=translator)
    service.request = AsyncMock(side_effect=[{"id": 1, "title": "Film", "overview": ""}, {"overview": "English synopsis"}])
    result = await service.details(1, "movie")
    assert result["overview"] == "Sinopsis traducida"
    assert result["overview_original"] == "English synopsis"
    assert result["overview_translated"]
    assert service.request.call_args.kwargs["language"] == "en-US"


@pytest.mark.asyncio
async def test_existing_localized_synopsis_never_translates():
    translator = SimpleNamespace(translate=AsyncMock())
    service = TMDBService(None, translator=translator)
    service.request = AsyncMock(return_value={"id": 1, "title": "Film", "overview": "Existing"})
    assert (await service.details(1, "movie"))["overview"] == "Existing"
    translator.translate.assert_not_awaited()


@pytest.mark.asyncio
async def test_translation_failure_retains_english():
    service = TMDBService(None, language="es-ES", translator=SimpleNamespace(translate=AsyncMock(side_effect=ServiceError("Unavailable"))))
    service.request = AsyncMock(side_effect=[{"id": 1, "title": "Film"}, {"overview": "Original"}])
    result = await service.details(1, "movie")
    assert result["overview"] == "Original" and result["translation_notice"]


@pytest.mark.asyncio
async def test_cached_translation_never_downloads(tmp_path):
    service = TranslationService(tmp_path, SimpleNamespace(cache_get=Mock(return_value={"text": "Cached"})))
    client = SimpleNamespace(get=AsyncMock())
    assert await service.translate(client, "Synopsis", "es-ES") == "Cached"
    client.get.assert_not_awaited()


def test_model_archive_rejects_traversal(tmp_path):
    archive = tmp_path / "model.zip"
    with zipfile.ZipFile(archive, "w") as z: z.writestr("../escape", "bad")
    with pytest.raises(ValueError): unpack_model(archive, tmp_path / "output", "es")
