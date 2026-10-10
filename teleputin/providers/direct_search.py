"""Best-effort reading of the public OK.ru search page; no private API calls."""
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin
from teleputin.core.exceptions import ServiceError
from teleputin.providers.okru import video_id_from_url, normalize_title
from teleputin.core.public_http import PublicPageReader

SEARCH_PAGE = "https://ok.ru/video/search"
SEARCH_LIMIT = 2_000_000


class PublicVideoCards(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.current = [], None
        self.depth, self.description_depth, self.duration_depth = 0, 0, 0
        self.title_open = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if tag == "div" and "video_search_result_video-card" in classes:
            self.current = {"title": "", "description": "", "duration": ""}
            self.depth = 1
            self.description_depth = self.duration_depth = 0
            self.title_open = False
            return
        if self.current is None: return
        if tag == "div": self.depth += 1
        if "video-card_duration" in classes: self.duration_depth = self.depth
        if attrs.get("data-tsid") == "video-description": self.description_depth = self.depth
        if tag == "a":
            url = urljoin(SEARCH_PAGE, attrs.get("href", ""))
            identifier = video_id_from_url(url)
            if identifier: self.current["url"] = f"https://ok.ru/video/{identifier}"
            if attrs.get("data-tsid") == "video-name": self.title_open = True
        if tag == "img" and "video-card_img" in classes:
            self.current["thumbnail"] = {"src": attrs.get("src", "")}
            self.current["fallback_title"] = attrs.get("alt", "")

    def handle_data(self, data):
        if self.current is None: return
        if self.title_open: self.current["title"] += data
        if self.description_depth: self.current["description"] += data
        if self.duration_depth: self.current["duration"] += data

    def handle_endtag(self, tag):
        if self.current is None: return
        if tag == "a": self.title_open = False
        if tag != "div": return
        if self.depth == self.description_depth: self.description_depth = 0
        if self.depth == self.duration_depth: self.duration_depth = 0
        self.depth -= 1
        if self.depth: return
        row = self.current
        row["title"] = normalize_title(row["title"] or row.get("fallback_title", ""))
        parts = row.pop("duration").strip().split(":")
        if 2 <= len(parts) <= 3 and all(part.isdigit() for part in parts):
            seconds = 0
            for part in parts: seconds = seconds * 60 + int(part)
            row["duration_seconds"] = seconds
        if row.get("url") and row["title"]: self.rows.append(row)
        self.current = None


class DirectPublicSearch:
    def __init__(self, client, fallback, reader=None):
        self.client, self.fallback = client, fallback
        self.reader = reader or PublicPageReader(client)
        self.blocked = False
        self.more, self.notice = False, ""
        self.source_name = "OK.ru public search"
        self.cache_namespace = "okru-public-page-v2:" + type(fallback).__name__

    async def search(self, query, page=1):
        self.more, self.notice = False, ""
        if page == 1 and not self.blocked:
            try:
                # Parameters observed in the public anonymous search page; not a private API.
                url = SEARCH_PAGE + "?" + urlencode({"st.cmd": "anonymVideo", "st.ft": "search", "st.gsq": query, "st.m": "SEARCH"})
                parser = PublicVideoCards()
                parser.feed(await self.reader.read(url, SEARCH_LIMIT))
                if parser.rows:
                    self.source_name = "OK.ru public search"
                    return parser.rows
                raise ServiceError("Public OK.ru search returned no readable video cards.")
            except (ServiceError, ValueError) as exc:
                self.blocked = True
                self.notice = str(exc) + " Using external search candidates."
        self.source_name = "External web search"
        rows = await self.fallback.search(query, page)
        self.more = self.fallback.more
        return rows
