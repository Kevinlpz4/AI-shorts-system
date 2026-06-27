from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class VoiceAudio:
    """
    Entidad: audio generado por TTS.
    """
    id: str = ""
    text: str = ""
    audio_path: str = ""
    duration: float = 0.0
    voice_id: str = ""
    speed: float = 1.0
    provider: str = ""
    status: str = "pending"  # pending, success, mock, error
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def is_mock(self) -> bool:
        return self.status == "mock"

    @property
    def is_success(self) -> bool:
        return self.status == "success"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "audio_path": self.audio_path,
            "duration": self.duration,
            "voice_id": self.voice_id,
            "speed": self.speed,
            "provider": self.provider,
            "status": self.status,
        }
