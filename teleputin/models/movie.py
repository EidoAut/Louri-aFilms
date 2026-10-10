from pydantic import BaseModel, Field


class CatalogItem(BaseModel):
    id: int
    kind: str
    title: str
    year: str = ""
    poster: str = ""
    backdrop: str = ""
    overview: str = ""
    rating: float = 0
    genres: list[str] = Field(default_factory=list)
    runtime: int | None = None
    alternatives: list[str] = Field(default_factory=list)
    seasons: list[dict] = Field(default_factory=list)
    related: list[dict] = Field(default_factory=list)

    def card(self):
        return {**self.model_dump(), "key": f"{self.kind}:{self.id}", "badge": "TMDB · find a video"}
