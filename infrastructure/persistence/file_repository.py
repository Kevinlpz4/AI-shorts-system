import json
import logging
from pathlib import Path
from typing import Optional

from domain.entities.content_idea import ContentIdea
from domain.entities.script import Script
from domain.entities.video import VideoAsset
from domain.value_objects.viral_score import ViralScore
from domain.value_objects.duration import Duration

logger = logging.getLogger(__name__)


class FileRepository:
    """
    Repositorio basado en archivos JSON.
    
    Puerto que implementa: ContentRepository (domain/ports/content_repository.py)
    
    Almacena ideas, scripts y videos en archivos JSON separados.
    """
    
    def __init__(self, data_dir: str = "data"):
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)

    async def save_idea(self, idea: ContentIdea) -> None:
        """Guarda idea en archivo JSON."""
        filepath = self._data_dir / "ideas.json"
        ideas = await self._load_all("ideas.json")
        ideas[idea.id] = idea.to_dict()
        self._save_json(filepath, ideas)
        logger.info(f"💾 Idea guardada: {idea.id}")

    async def save_script(self, script: Script) -> None:
        """Guarda script en archivo JSON."""
        filepath = self._data_dir / "scripts.json"
        scripts = await self._load_all("scripts.json")
        scripts[script.id] = script.to_dict()
        self._save_json(filepath, scripts)
        logger.info(f"💾 Script guardado: {script.id}")

    async def save_video(self, video: VideoAsset) -> None:
        """Guarda video en archivo JSON."""
        filepath = self._data_dir / "videos.json"
        videos = await self._load_all("videos.json")
        videos[video.id] = video.to_dict()
        self._save_json(filepath, videos)
        logger.info(f"💾 Video guardado: {video.id}")

    async def get_idea(self, idea_id: str) -> Optional[ContentIdea]:
        """Obtiene idea por ID."""
        ideas = await self._load_all("ideas.json")
        data = ideas.get(idea_id)
        if not data:
            return None
        return ContentIdea(
            id=data["id"],
            hook=data.get("hook", ""),
            topic=data.get("topic", ""),
            format=data.get("format", "story"),
            description=data.get("description", ""),
            target_audience=data.get("audience", "general"),
            viral_score=ViralScore(data.get("viral_score", 50)),
            keywords=data.get("keywords", []),
            trend_id=data.get("trend_id"),
        )

    async def get_script(self, script_id: str) -> Optional[Script]:
        """Obtiene script por ID."""
        scripts = await self._load_all("scripts.json")
        data = scripts.get(script_id)
        if not data:
            return None
        return Script(
            id=data["id"],
            idea_id=data.get("idea_id", ""),
            topic=data.get("topic", ""),
            hook=data.get("hook", ""),
            body=data.get("body", ""),
            cta=data.get("cta", ""),
            duration=Duration(data.get("duration", 45)),
            tone=data.get("tone", "educational"),
            format=data.get("format", "story"),
        )

    async def list_ideas(self, limit: int = 20) -> list[ContentIdea]:
        """Lista ideas guardadas."""
        ideas = await self._load_all("ideas.json")
        sorted_ids = sorted(ideas.keys(), reverse=True)[:limit]
        result = []
        for idea_id in sorted_ids:
            idea = await self.get_idea(idea_id)
            if idea:
                result.append(idea)
        return result

    async def list_videos(self, limit: int = 20) -> list[VideoAsset]:
        """Lista videos guardados."""
        videos = await self._load_all("videos.json")
        sorted_ids = sorted(videos.keys(), reverse=True)[:limit]
        return [
            VideoAsset(
                id=v["id"],
                video_path=v.get("video_path", ""),
                width=v.get("width", 1080),
                height=v.get("height", 1920),
                duration=v.get("duration", 45),
                status=v.get("status", "pending"),
            )
            for v_id in sorted_ids
            if (v := videos.get(v_id))
        ]

    async def _load_all(self, filename: str) -> dict:
        """Carga todo el contenido de un archivo JSON."""
        filepath = self._data_dir / filename
        if not filepath.exists():
            return {}
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_json(self, filepath: Path, data: dict) -> None:
        """Guarda datos en archivo JSON."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
