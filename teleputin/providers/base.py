from abc import ABC, abstractmethod
from teleputin.models.video import VideoResult


class VideoProvider(ABC):
    @abstractmethod
    async def search(self, query: str, page: int = 1) -> list[VideoResult]: ...

    @abstractmethod
    async def get_video(self, video_id: str) -> VideoResult: ...

    @abstractmethod
    async def get_embed_url(self, video_id: str) -> str | None: ...
