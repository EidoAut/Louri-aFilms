from datetime import datetime
from pydantic import BaseModel, Field


class VideoResult(BaseModel):
    id: str
    provider: str
    title: str
    description: str | None = None
    thumbnail_url: str | None = None
    duration_seconds: int | None = Field(default=None, ge=0)
    published_at: datetime | None = None
    original_url: str
    embed_url: str | None = None
    is_embeddable: bool | None = None
    source_name: str = ""

    def card(self):
        data = self.model_dump(mode="json")
        data.update(kind="video", poster=self.thumbnail_url or "", overview=self.description or "", year="", badge="OK.ru · embedding unknown", key=f"{self.provider}:{self.id}")
        return data
