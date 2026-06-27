from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class VideoAsset:
    """
    Entidad: un video renderizado listo para publicar.
    """
    id: str = ""
    video_path: str = ""
    width: int = 1080
    height: int = 1920
    duration: float = 45.0
    fps: int = 30
    codec: str = "h264"
    file_size: int = 0
    status: str = "pending"  # pending, rendered, published, error
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def aspect_ratio(self) -> str:
        return f"{self.width}:{self.height}"

    @property
    def is_rendered(self) -> bool:
        return self.status == "rendered" and self.file_size > 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "video_path": self.video_path,
            "resolution": f"{self.width}x{self.height}",
            "duration": self.duration,
            "fps": self.fps,
            "file_size_mb": round(self.file_size / (1024 * 1024), 2),
            "status": self.status,
        }
