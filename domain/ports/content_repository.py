from typing import Protocol, Optional
from uuid import UUID

from domain.entities.content_idea import ContentIdea
from domain.entities.script import Script
from domain.entities.video import VideoAsset


class ContentRepository(Protocol):
    """
    Puerto: Repositorio de contenido.
    
    Abstrae la persistencia: archivos, DB, nube, etc.
    """
    
    async def save_idea(self, idea: ContentIdea) -> None:
        ...

    async def save_script(self, script: Script) -> None:
        ...

    async def save_video(self, video: VideoAsset) -> None:
        ...

    async def get_idea(self, idea_id: str) -> Optional[ContentIdea]:
        ...

    async def get_script(self, script_id: str) -> Optional[Script]:
        ...

    async def list_ideas(self, limit: int = 20) -> list[ContentIdea]:
        ...

    async def list_videos(self, limit: int = 20) -> list[VideoAsset]:
        ...
