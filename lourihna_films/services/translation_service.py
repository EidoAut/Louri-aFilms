# ==========================================================================
"""translation_service.py
Free local synopsis translation using public Argos models and CTranslate2.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from lourihna_films.database.repositories import Repository

import asyncio
import hashlib
import json
import re
import tempfile
import threading
import zipfile
from urllib.parse import urlsplit

from lourihna_films.core.exceptions import ServiceError

INDEX_URL = (
    "https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json"
)
MAX_DOWNLOAD = 250 * 1024 * 1024
MAX_UNPACKED = 1024 * 1024 * 1024
TARGETS = {"es", "gl", "fr", "de", "ru"}


def unpack_model(archive: Path, destination: Path, target: str) -> Path:
    """Extract a size-bounded model archive after rejecting unsafe paths."""
    with zipfile.ZipFile(archive) as package:
        entries = package.infolist()
        if sum(item.file_size for item in entries) > MAX_UNPACKED:
            raise ValueError("Model too large")
        for item in entries:
            path = Path(item.filename.replace("\\", "/"))
            if path.is_absolute() or ".." in path.parts or ":" in item.filename:
                raise ValueError("Invalid model path")
        package.extractall(destination)
    for metadata in destination.rglob("metadata.json"):
        data = json.loads(metadata.read_text(encoding="utf-8"))
        if data.get("from_code") == "en" and data.get("to_code") == target:
            root = metadata.parent
            if (root / "sentencepiece.model").is_file() and (
                root / "model/model.bin"
            ).is_file():
                return root
    raise ValueError("Unsupported translation model")


class TranslationService:
    """Own downloaded translation models and serialized CPU inference."""

    def __init__(self, directory: Path, repository: Repository) -> None:
        self.directory, self.repository = Path(directory), repository
        self.lock = asyncio.Lock()
        self.loaded = None
        self.inference_lock = threading.Lock()

    async def ensure_model(self, client: httpx.AsyncClient, target: str) -> Path:
        """Download and validate the optional translation model if it is not cached."""
        destination = self.directory / ("en-" + target)
        if (destination / "model/model.bin").is_file():
            return destination
        self.directory.mkdir(parents=True, exist_ok=True)
        response = await client.get(INDEX_URL, timeout=20)
        response.raise_for_status()
        entry = next(
            (
                item
                for item in response.json()
                if item.get("from_code") == "en" and item.get("to_code") == target
            ),
            None,
        )
        urls = entry.get("links", []) if entry else []
        url = next(
            (
                url
                for url in urls
                if urlsplit(url).scheme == "https"
                and urlsplit(url).hostname == "argos-net.com"
            ),
            None,
        )
        if not url:
            raise ValueError("No supported language model")
        with tempfile.TemporaryDirectory(dir=self.directory) as temporary:
            temporary = Path(temporary)
            archive = temporary / "model.zip"
            size = 0
            async with client.stream(
                "GET", url, timeout=60, follow_redirects=False
            ) as response:
                response.raise_for_status()
                with archive.open("wb") as output:
                    async for block in response.aiter_bytes():
                        size += len(block)
                        if size > MAX_DOWNLOAD:
                            raise ValueError("Model download too large")
                        output.write(block)
            extracted = temporary / "contents"
            root = unpack_model(archive, extracted, target)
            root.rename(destination)
        return destination

    def infer(self, directory: Path, text: str) -> str:
        """Translate text with the locally installed CPU model."""
        with self.inference_lock:
            return self._infer(directory, text)

    def _infer(self, directory, text):
        import ctranslate2
        import sentencepiece

        if not self.loaded or self.loaded[0] != directory:
            self.loaded = (
                directory,
                ctranslate2.Translator(
                    str(directory / "model"),
                    device="cpu",
                    compute_type="int8",
                    intra_threads=2,
                ),
                sentencepiece.SentencePieceProcessor(
                    model_file=str(directory / "sentencepiece.model")
                ),
            )
        _, engine, tokenizer = self.loaded
        sentences = [
            s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()
        ]
        tokens = [tokenizer.encode(sentence, out_type=str) for sentence in sentences]
        if any(len(row) > 500 for row in tokens):
            raise ValueError("Synopsis sentence too long")
        results = engine.translate_batch(tokens, beam_size=2, max_decoding_length=1024)
        return " ".join(tokenizer.decode(result.hypotheses[0]) for result in results)

    async def translate(self, client: httpx.AsyncClient, text: str, target: str) -> str:
        """Return a cached or locally translated synopsis for the target language."""
        target = target.split("-")[0]
        if target == "en":
            return text
        if target not in TARGETS or not text or len(text) > 12000:
            raise ServiceError("No hay traducción local disponible para esta sinopsis.")
        key = "translation-v1:" + hashlib.sha256((target + text).encode()).hexdigest()
        cached = self.repository.cache_get(key)
        if cached is not None:
            return cached["text"]
        try:
            async with self.lock:
                directory = await self.ensure_model(client, target)
                result = await asyncio.to_thread(self.infer, directory, text)
            if not result:
                raise ValueError("Empty translation")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            raise ServiceError(
                "No se pudo traducir. Se conserva la sinopsis original."
            ) from exc
        self.repository.cache_put(
            key, "", "translation", {"text": result}, ttl=365 * 86400
        )
        return result
