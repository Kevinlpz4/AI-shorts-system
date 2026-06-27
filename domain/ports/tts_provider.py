from typing import Protocol, Optional

from domain.entities.voice_audio import VoiceAudio


class TTSProvider(Protocol):
    """
    Puerto: Proveedor de Text-to-Speech.
    
    Implementaciones: ElevenLabs, Azure, Google TTS, Mock.
    """
    
    async def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        output_path: Optional[str] = None,
    ) -> VoiceAudio:
        """Convierte texto a voz."""
        ...

    @property
    def name(self) -> str:
        ...

    @property
    def available(self) -> bool:
        ...
