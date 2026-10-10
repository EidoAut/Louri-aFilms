import json
import time
import math
from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session
from teleputin.database.models import Favorite, WatchHistory, SearchHistory, SearchCache, Setting, LibraryVideo


class Repository:
    def __init__(self, engine): self.engine = engine

    def save_videos(self, items, category=None):
        with Session(self.engine) as s, s.begin():
            for item in items:
                if not isinstance(item, dict) or item.get("kind") != "video" or item.get("provider") not in ("okru", "archive"): continue
                from teleputin.providers.okru import video_id_from_url
                from teleputin.providers.archive import archive_id_from_url
                identify = archive_id_from_url if item["provider"] == "archive" else video_id_from_url
                identifier = identify(item.get("original_url", ""))
                if not identifier: continue
                item = {**item, "key": f"{item['provider']}:{identifier}", "id": identifier}
                row = s.get(LibraryVideo, item["key"])
                previous = json.loads(row.payload) if row else {}
                merged = {**item, **previous, **{k: v for k, v in item.items() if v not in (None, "")}}
                if previous.get("title") and item.get("title") == f"OK.ru video {identifier}": merged["title"] = previous["title"]
                if previous.get("local_title"): merged["title"] = previous["title"]
                chosen = category if category is not None else row.category if row else item.get("category", "General")
                merged["category"] = chosen.strip()[:60] or "General"
                if row is None:
                    row = LibraryVideo(key=item["key"], discovered=time.time(), updated=time.time(), payload="{}")
                    s.add(row)
                row.category, row.payload, row.updated = merged["category"], json.dumps(merged), time.time()
                favorite = s.scalar(select(Favorite).where(Favorite.content_identifier == item["key"]))
                if favorite: favorite.payload, favorite.title = row.payload, merged["title"]

    def library(self, query="", category=None):
        with Session(self.engine) as s:
            statement = select(LibraryVideo).order_by(LibraryVideo.discovered.desc())
            if category: statement = statement.where(LibraryVideo.category == category)
            items = [json.loads(row.payload) for row in s.scalars(statement)]
        words = query.casefold().split()
        return [item for item in items if all(word in " ".join(str(item.get(k) or "") for k in ("title", "description", "overview", "category", "original_url")).casefold() for word in words)]

    def organize(self, key, title, category):
        with Session(self.engine) as s, s.begin():
            row = s.get(LibraryVideo, key)
            if not row: return None
            item = json.loads(row.payload)
            item.update(title=title.strip()[:1000] or item["title"], local_title=True, category=category.strip()[:60] or "General")
            row.payload, row.category = json.dumps(item), item["category"]
            favorite = s.scalar(select(Favorite).where(Favorite.content_identifier == key))
            if favorite: favorite.payload, favorite.title = row.payload, item["title"]
            history = s.scalar(select(WatchHistory).where(WatchHistory.provider == item["provider"], WatchHistory.video_id == item["id"]))
            if history:
                history.payload = json.dumps({**json.loads(history.payload), **item})
                history.title = item["title"]
            return item

    def recover_library(self):
        # One-time, idempotent recovery of previously discovered version 1 data.
        if self.settings().get("library_recovered") == "yes": return
        with Session(self.engine) as s:
            cached = [json.loads(row.results).get("items", []) for row in s.scalars(select(SearchCache))]
        for items in cached + [self.favorites(), self.history()]: self.save_videos(items)
        self.save_settings({"library_recovered": "yes"})

    def settings(self):
        with Session(self.engine) as s:
            return {x.key: x.value for x in s.scalars(select(Setting))}

    def save_settings(self, values):
        with Session(self.engine) as s, s.begin():
            for key, value in values.items(): s.merge(Setting(key=key, value=value))

    def favorites(self):
        with Session(self.engine) as s:
            return [json.loads(x.payload) for x in s.scalars(select(Favorite).order_by(Favorite.date_added.desc()))]

    def toggle_favorite(self, item):
        with Session(self.engine) as s, s.begin():
            existing = s.scalar(select(Favorite).where(Favorite.content_identifier == item["key"]))
            if existing: s.delete(existing)
            else: s.add(Favorite(content_identifier=item["key"], content_type=item["kind"], title=item["title"], poster_url=item.get("poster", ""), date_added=time.time(), payload=json.dumps(item)))

    def record_open(self, video):
        with Session(self.engine) as s, s.begin():
            row = s.scalar(select(WatchHistory).where(WatchHistory.provider == video["provider"], WatchHistory.video_id == video["id"]))
            if row is None:
                row = WatchHistory(provider=video["provider"], video_id=video["id"], title=video["title"], payload=json.dumps(video), last_watched=time.time())
                s.add(row)
            row.last_watched = time.time()
            previous = json.loads(row.payload)
            video = {**video, "continue_watching": previous.get("continue_watching", False), "finished": previous.get("finished", False)}
            row.title, row.payload, row.duration = video["title"], json.dumps(video), video.get("duration_seconds") or row.duration
            # An opened player is not proof of watching; position remains NULL.

    def history(self):
        with Session(self.engine) as s:
            return [self.history_item(x) for x in s.scalars(select(WatchHistory).order_by(WatchHistory.last_watched.desc()).limit(40))]

    @staticmethod
    def history_item(row):
        item = json.loads(row.payload)
        item.update(position_ms=int((row.position or 0) * 1000), duration_ms=int((row.duration or 0) * 1000))
        return item

    def save_progress(self, provider, identifier, position_ms, duration_ms, finished=False):
        if not all(math.isfinite(x) and x >= 0 for x in (position_ms, duration_ms)): return
        with Session(self.engine) as s, s.begin():
            row = s.scalar(select(WatchHistory).where(WatchHistory.provider == provider, WatchHistory.video_id == identifier))
            if row is None: return
            row.position = min(position_ms, duration_ms) / 1000 if duration_ms else position_ms / 1000
            if duration_ms: row.duration = int(duration_ms / 1000)
            item = json.loads(row.payload)
            item.update(finished=bool(finished), continue_watching=not finished and position_ms > 0)
            row.payload, row.last_watched = json.dumps(item), time.time()

    def keep_watching(self, provider, video_id, enabled):
        with Session(self.engine) as s, s.begin():
            row = s.scalar(select(WatchHistory).where(WatchHistory.provider == provider, WatchHistory.video_id == video_id))
            if row:
                item = json.loads(row.payload)
                item["continue_watching"] = bool(enabled)
                row.payload = json.dumps(item)

    def continuing(self):
        with Session(self.engine) as s:
            rows = s.scalars(select(WatchHistory).order_by(WatchHistory.last_watched.desc()))
            return [item for row in rows if (item := self.history_item(row)).get("continue_watching") and not item.get("finished")]

    def remember_query(self, query):
        with Session(self.engine) as s, s.begin():
            row = s.scalar(select(SearchHistory).where(SearchHistory.query == query))
            if row: row.timestamp = time.time()
            else: s.add(SearchHistory(query=query, timestamp=time.time()))
            keep = select(SearchHistory.id).order_by(SearchHistory.timestamp.desc()).limit(30)
            s.execute(delete(SearchHistory).where(SearchHistory.id.not_in(keep)))

    def recent_searches(self):
        with Session(self.engine) as s:
            return list(s.scalars(select(SearchHistory.query).order_by(SearchHistory.timestamp.desc()).limit(12)))

    def cache_get(self, key, allow_stale=False):
        with Session(self.engine) as s:
            row = s.get(SearchCache, key)
            if row and (allow_stale or row.expires > time.time()): return json.loads(row.results)

    def cache_put(self, key, query, provider, result, ttl=1800):
        with Session(self.engine) as s, s.begin():
            s.execute(delete(SearchCache).where(SearchCache.expires < time.time() - 30 * 86400))
            s.merge(SearchCache(key=key, query=query, provider=provider, results=json.dumps(result), created=time.time(), expires=time.time() + ttl))

    def expire_discovery(self):
        with Session(self.engine) as s, s.begin():
            s.execute(update(SearchCache).where(SearchCache.provider.in_(["discovery", "archive", "okru", "tmdb", "rarefilmm"])).values(expires=time.time() - 1))

    def clear_history(self):
        with Session(self.engine) as s, s.begin():
            for model in (WatchHistory, SearchHistory, SearchCache): s.execute(delete(model))
