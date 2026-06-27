import logging
from typing import Optional
from pathlib import Path
from datetime import datetime

from domain.entities.video import VideoAsset
from domain.entities.script import Script
from domain.exceptions.media import VideoRenderError

logger = logging.getLogger(__name__)


class MockVideoRenderer:
    """
    Renderizador de video Mock.
    
    Puerto que implementa: VideoRenderer
    
    Crea un archivo de video vacío simulando el renderizado.
    """
    
    def __init__(self, output_dir: str = "assets/video"):
        self._output_dir = Path(output_dir)

    @property
    def available(self) -> bool:
        return True

    async def render(
        self,
        audio_path: str,
        script: Script,
        aspect_ratio: str = "9:16",
        template: str = "default",
    ) -> VideoAsset:
        """Renderiza video mock."""
        self._output_dir.mkdir(parents=True, exist_ok=True)

        output_path = self._output_dir / f"video_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.mp4"
        output_path.touch()

        logger.info(f"🎬 [MOCK] Video renderizado: {output_path}")

        return VideoAsset(
            id=f"video_mock_{output_path.stem}",
            video_path=str(output_path),
            width=1080,
            height=1920,
            duration=float(int(script.duration)),
            fps=30,
            codec="h264",
            file_size=output_path.stat().st_size,
            status="rendered",
        )
