import logging
from typing import Optional
from pathlib import Path

from domain.entities.voice_audio import VoiceAudio
from domain.exceptions.media import TTSError

logger = logging.getLogger(__name__)


class MockTTSProvider:
    """
    Proveedor TTS Mock para desarrollo/testing.
    
    Puerto que implementa: TTSProvider
    
    Crea archivos de audio vacíos simulando la generación.
    Útil cuando ElevenLabs está bloqueado o no hay API key.
    """
    
    def __init__(self, output_dir: str = "assets/audio"):
        self._name = "mock-tts"
        self._output_dir = Path(output_dir)

    @property
    def name(self) -> str:
        return self._name

    @property
    def available(self) -> bool:
        return True

    async def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        output_path: Optional[str] = None,
    ) -> VoiceAudio:
        """Genera audio mock."""
        self._output_dir.mkdir(parents=True, exist_ok=True)

        if not output_path:
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            output_path = str(self._output_dir / f"voice_mock_{text_hash}.mp3")

        # Crear archivo vacío
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.touch()

        # Duración estimada
        word_count = len(text.split())
        duration = (word_count / 150 * 60) / speed

        logger.info(f"🎤 Mock TTS: {output_path} ({duration:.1f}s)")

        return VoiceAudio(
            id=f"voice_mock_{output_file.stem}",
            text=text,
            audio_path=output_path,
            duration=duration,
            voice_id=voice_id or "mock",
            speed=speed,
            provider=self._name,
            status="mock",
        )
