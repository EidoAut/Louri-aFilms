"""Bounded title variants and transparent heuristic ranking, never availability claims."""
import re
import unicodedata
from teleputin.core.exceptions import ServiceError
from teleputin.core.policy import CANDIDATE_QUERY_LIMIT, CANDIDATE_METADATA_LIMIT, CANDIDATE_LIMIT, FEATURE_MINUTES
from teleputin.core.policy import TITLE_MATCH_WEIGHT, YEAR_MATCH_WEIGHT, DIRECTOR_MATCH_WEIGHT, RUNTIME_MATCH_WEIGHT, FEATURE_LENGTH_WEIGHT, CLIP_PENALTY, STRONG_TITLE_MATCH, RUNTIME_TOLERANCE_SECONDS, RUNTIME_TOLERANCE_RATIO
from teleputin.services.metadata_service import MetadataService
from teleputin.providers.public_metadata import PublicMetadata


def words(value):
    value = unicodedata.normalize("NFKD", str(value)).casefold()
    return set(re.findall(r"[^\W_]+", "".join(c for c in value if not unicodedata.combining(c))))


def queries(item):
    titles = list(dict.fromkeys(filter(None, [item.get("title"), item.get("original_title"), *item.get("alternatives", [])])))
    year = item.get("year", "")
    if item.get("episode_number") is not None and titles:
        season, episode = item.get("season_number", 1), item["episode_number"]
        return [f"{title} {suffix}" for title in titles[:2] for suffix in
                (f"S{season:02}E{episode:02}", f"{season}x{episode:02} {item.get('episode_title', '')}")][:CANDIDATE_QUERY_LIMIT]
    result = [f"{title} {year}".strip() for title in titles[:CANDIDATE_QUERY_LIMIT - 1]]
    if item.get("directors") and titles: result.insert(1, f"{titles[0]} {year} {item['directors'][0]}".strip())
    return list(dict.fromkeys(result))[:CANDIDATE_QUERY_LIMIT]


def rank(items, catalog):
    titles = [words(x) for x in [catalog.get("title", ""), catalog.get("original_title", ""), *catalog.get("alternatives", [])] if x]
    unique = {}
    for item in items:
        key = item.get("key")
        if not key: continue
        previous = unique.get(key, {})
        unique[key] = {**previous, **{k: v for k, v in item.items() if v not in (None, "")}}
        if previous.get("source_url"):
            for field in ("source_name", "source_url", "source_entry", "badge"):
                if field in previous: unique[key][field] = previous[field]
    ranked = []
    for item in unique.values():
        text = words(item.get("title", ""))
        overlap = max((len(title & text) / len(title) for title in titles if title), default=0)
        score, reasons = overlap * TITLE_MATCH_WEIGHT, []
        if overlap >= STRONG_TITLE_MATCH: reasons.append("Title match")
        if str(catalog.get("year", "")) in text:
            score += YEAR_MATCH_WEIGHT; reasons.append("Year match")
        directors = words(" ".join(catalog.get("directors", [])))
        if directors and directors <= words(item.get("title", "") + " " + (item.get("description") or "")):
            score += DIRECTOR_MATCH_WEIGHT; reasons.append("Director match")
        duration = item.get("duration_seconds")
        runtime = catalog.get("runtime")
        if duration and runtime and abs(duration - runtime * 60) <= max(RUNTIME_TOLERANCE_SECONDS, runtime * 60 * RUNTIME_TOLERANCE_RATIO):
            score += RUNTIME_MATCH_WEIGHT; reasons.append("Similar runtime")
        elif duration and duration >= FEATURE_MINUTES * 60 and catalog.get("kind") == "movie":
            score += FEATURE_LENGTH_WEIGHT; reasons.append("Feature length")
        if text & {"trailer", "teaser", "clip", "трейлер", "tráiler"}: score -= CLIP_PENALTY; reasons.append("May be a clip")
        ranked.append({**item, "match_score": round(score), "match_reason": " · ".join(reasons) or "Uncertain match"})
    return sorted(ranked, key=lambda x: (-x["match_score"], x["key"]))[:CANDIDATE_LIMIT]


class CandidateService:
    def __init__(self, search, repository, client):
        self.search, self.repo, self.client = search, repository, client
        self.metadata = getattr(search, "metadata", None) or MetadataService(repository, PublicMetadata(client))

    async def find(self, catalog):
        items, notices = [], []
        for query in queries(catalog):
            try:
                result = await self.search.search(query, remember=False)
                items.extend(result["items"])
                if result.get("notice"): notices.append(result["notice"])
            except ServiceError as exc:
                notices.append(str(exc))
                # Do not keep probing a challenged or rate-limited search backend.
                break
        # Archive search uses its own bounded, documented pagination independently.
        if not items and "archive" in getattr(self.search, "providers", {}):
            for query in queries(catalog)[:2]:
                try:
                    result = await self.search.search(query, provider="archive", remember=False)
                    items.extend(result["items"])
                except ServiceError:
                    notices.append("Internet Archive no está disponible ahora.")
                    break
        ordered = rank(items, catalog)
        # Enrich a bounded batch without importing placeholder titles into the library.
        if ordered:
            enriched = await self.metadata.enrich(ordered[:CANDIDATE_METADATA_LIMIT])
            ordered = rank(enriched + ordered[CANDIDATE_METADATA_LIMIT:], catalog)
            if self.metadata.notice: notices.append(self.metadata.notice)
        self.repo.save_videos(ordered)
        return {"items": ordered, "notice": " ".join(dict.fromkeys(notices))}
