import logging
from typing import Optional

from domain.entities.content_idea import ContentIdea
from domain.entities.script import Script
from domain.entities.trend import Trend, TrendSource
from domain.entities.hook import Hook
from domain.entities.voice_audio import VoiceAudio
from domain.entities.video import VideoAsset
from domain.value_objects.viral_score import ViralScore
from domain.value_objects.duration import Duration
from domain.value_objects.hook_type import HookType
from domain.value_objects.platform import Platform
from domain.exceptions.content import (
    IdeaGenerationError, ScriptGenerationError, ContentEvaluationError,
)
from domain.exceptions.ai import AIProviderError
from domain.exceptions.media import VideoRenderError
from domain.exceptions.publishing import PlatformNotSupportedError

from domain.ports.ai_provider import AIProvider, IdeaGeneratorPort, ScriptGeneratorPort
from domain.ports.tts_provider import TTSProvider
from domain.ports.video_renderer import VideoRenderer
from domain.ports.content_repository import ContentRepository
from domain.ports.trend_source import TrendSourcePort
from domain.ports.publisher import PublisherPort, PublishResult
from domain.ports.cache import CachePort
from domain.services.content_evaluator import ContentEvaluator

from application.dto import GenerateContentRequest
from application.dto.responses import ContentResult
from application.error_mapper import ErrorMapper

logger = logging.getLogger(__name__)


class GenerateContentUseCase:
    """
    Caso de uso: GENERAR CONTENIDO COMPLETO.
    
    Orquesta el pipeline completo:
    Trends → Ideas → Script → Hook → Voz → Video → Subtítulos → Publicación
    
    NO sabe qué implementaciones concretas usa.
    Recibe todo por inyección de dependencias.
    """
    
    def __init__(
        self,
        ai_provider: AIProvider,
        tts_provider: TTSProvider,
        video_renderer: VideoRenderer,
        repository: ContentRepository,
        trend_sources: list[TrendSourcePort],
        publisher: PublisherPort,
        cache: CachePort,
        evaluator: ContentEvaluator,
    ):
        self._ai = ai_provider
        self._tts = tts_provider
        self._renderer = video_renderer
        self._repo = repository
        self._trend_sources = trend_sources
        self._publisher = publisher
        self._cache = cache
        self._evaluator = evaluator

    async def execute(self, request: GenerateContentRequest) -> ContentResult:
        """
        Ejecuta el pipeline completo de generación.
        
        Flujo:
        1. Obtener tendencias
        2. Generar idea
        3. Evaluar idea (y optimizar si es necesario)
        4. Generar guion
        5. Evaluar guion (y optimizar si es necesario)
        6. Generar voz
        7. Renderizar video
        8. (Opcional) Publicar
        9. Guardar todo
        """
        logger.info(f"🎬 Iniciando generación (nicho: {request.niche or 'general'})")

        try:
            # ── STEP 1: Trends ──
            trends = await self._fetch_trends(request)
            if not trends:
                logger.info("📡 Sin trends reales, usando generación sin trends")

            # ── STEP 2: Idea ──
            idea = await self._generate_idea(trends, request)
            
            # ── STEP 3: Evaluar/Optimizar idea ──
            idea = await self._evaluate_and_optimize_idea(idea)
            
            # ── STEP 4: Script ──
            script = await self._generate_script(idea, request)
            
            # ── STEP 5: Evaluar/Optimizar script ──
            script = await self._evaluate_and_optimize_script(script)
            
            # ── STEP 6: Voz ──
            audio = await self._generate_voice(script)
            
            # ── STEP 7: Video ──
            video = await self._generate_video(audio, script)
            
            # ── STEP 8: Guardar ──
            await self._repo.save_idea(idea)
            await self._repo.save_script(script)
            await self._repo.save_video(video)
            
            # ── STEP 9: Publicar si aplica ──
            publish_result = None
            if request.platform:
                publish_result = await self._publish_video(
                    video, idea, request
                )

            logger.info(f"✅ Contenido generado exitosamente")
            return ContentResult.ok(data={
                "idea": idea.to_dict(),
                "script": script.to_dict(),
                "audio": audio.to_dict(),
                "video": video.to_dict(),
                "publish": publish_result.to_dict() if publish_result else None,
            })

        except AIProviderError as e:
            level, msg, status = ErrorMapper.map(e)
            logger.log(level, f"{msg}: {e.detail}")
            return ContentResult.fallback(
                data={"error": e.code, "detail": e.detail},
                message=msg,
            )
        except Exception as e:
            logger.error(f"❌ Error en generación: {e}", exc_info=True)
            return ContentResult.error(str(e), status=500)

    async def _fetch_trends(self, request: GenerateContentRequest) -> list[Trend]:
        """Obtiene tendencias de todas las fuentes configuradas."""
        all_trends = []
        for source in self._trend_sources:
            try:
                if source.available:
                    trends = await source.fetch_trends(
                        niche=request.niche,
                        limit=10,
                    )
                    all_trends.extend(trends)
                    logger.info(f"📡 {source.source_name}: {len(trends)} trends")
            except Exception as e:
                logger.warning(f"⚠️ {source.source_name} falló: {e}")

        all_trends.sort(key=lambda t: int(t.viral_score), reverse=True)
        return all_trends[:20]

    async def _generate_idea(
        self,
        trends: list[Trend],
        request: GenerateContentRequest,
    ) -> ContentIdea:
        """Genera una idea usando IA."""
        logger.info("🧠 Generando idea...")

        if trends:
            trends_text = "\n".join([f"- {t.topic}" for t in trends[:5]])
            prompt = (
                f"Generá UNA idea viral para YouTube Shorts sobre {request.niche or 'temas generales'}.\n\n"
                f"Tendencias actuales:\n{trends_text}\n\n"
                f"Formato: {request.tone}\n"
                f"Responde en JSON:\n"
                f'{{"hook": "...", "format": "story|list|fact", '
                f'"description": "...", "audience": "..."}}'
            )
        else:
            prompt = (
                f"Generá UNA idea viral para YouTube Shorts sobre {request.niche or 'temas generales'}.\n\n"
                f"Responde en JSON:\n"
                f'{{"hook": "...", "format": "story|list|fact", '
                f'"description": "...", "audience": "..."}}'
            )

        try:
            result = await self._ai.generate_json(prompt, temperature=0.9)
            return ContentIdea(
                hook=result.get("hook", "Idea generada automáticamente"),
                topic=request.niche or "general",
                format=result.get("format", "story"),
                description=result.get("description", ""),
                target_audience=result.get("audience", "general"),
                viral_score=ViralScore(70),
                trend_id=trends[0].id if trends else None,
                keywords=[request.niche] if request.niche else [],
            )
        except Exception as e:
            logger.warning(f"⚠️ Error generando idea: {e}")
            raise IdeaGenerationError(str(e))

    async def _evaluate_and_optimize_idea(self, idea: ContentIdea) -> ContentIdea:
        """Evalúa la idea y la optimiza si es necesario."""
        result = self._evaluator.evaluate_idea(idea)
        logger.info(f"📊 Idea evaluada: {result.score_total:.1f}/10 ({result.classification})")

        if not result.is_acceptable:
            logger.info(f"🔧 Optimizando idea: {result.recommendations}")
            idea = self._evaluator.optimize_idea(idea, result.recommendations)
            # Reevaluar
            result = self._evaluator.evaluate_idea(idea)
            logger.info(f"📊 Idea después de optimizar: {result.score_total:.1f}/10")

        return idea

    async def _generate_script(
        self,
        idea: ContentIdea,
        request: GenerateContentRequest,
    ) -> Script:
        """Genera guion basado en la idea."""
        logger.info("✍️ Generando guion...")

        prompt = (
            f"Generá un guion para YouTube Shorts (~{request.duration}s) sobre:\n\n"
            f"Tema: {idea.topic}\n"
            f"Hook: {idea.hook}\n"
            f"Formato: {idea.format}\n"
            f"Tono: {request.tone}\n\n"
            f"Responde en JSON:\n"
            f'{{"hook": "{idea.hook}", "body": "...", "cta": "..."}}'
        )

        try:
            result = await self._ai.generate_json(prompt, temperature=0.8)
            return Script(
                idea_id=idea.id,
                topic=idea.topic,
                hook=result.get("hook", idea.hook),
                body=result.get("body", "Contenido del video..."),
                cta=result.get("cta", "Seguime para más contenido 🔥"),
                duration=Duration(request.duration),
                tone=request.tone,
                format=idea.format,
            )
        except Exception as e:
            logger.warning(f"⚠️ Error generando script: {e}")
            raise ScriptGenerationError(str(e))

    async def _evaluate_and_optimize_script(self, script: Script) -> Script:
        """Evalúa y optimiza el guion."""
        result = self._evaluator.evaluate_script(script)
        logger.info(f"📊 Script evaluado: {result.score_total:.1f}/10 ({result.classification})")

        if not result.is_acceptable:
            logger.info(f"🔧 Optimizando script: {result.recommendations}")
            script = self._evaluator.optimize_script(script, result.recommendations)

        return script

    async def _generate_voice(self, script: Script) -> VoiceAudio:
        """Genera voz para el guion."""
        logger.info("🔊 Generando voz...")
        text = f"{script.hook}. {script.body} {script.cta}"

        try:
            if self._tts.available:
                audio = await self._tts.synthesize(text=text, speed=1.0)
                logger.info(f"   ✓ Audio generado: {audio.duration:.1f}s")
                return audio
        except Exception as e:
            logger.warning(f"⚠️ TTS falló: {e}")

        # Mock audio
        logger.info("   Usando audio mock (TTS no disponible)")
        return VoiceAudio(
            id=f"voice_mock_{id(script)}",
            text=text,
            audio_path="",
            duration=float(int(script.duration)),
            status="mock",
        )

    async def _generate_video(self, audio: VoiceAudio, script: Script) -> VideoAsset:
        """Renderiza el video."""
        logger.info("🎬 Generando video...")

        try:
            if self._renderer.available:
                video = await self._renderer.render(
                    audio_path=audio.audio_path,
                    script=script,
                )
                logger.info(f"   ✓ Video renderizado: {video.video_path}")
                return video
        except Exception as e:
            logger.warning(f"⚠️ Video render falló: {e}")
            raise VideoRenderError(str(e))

        # Mock video
        logger.info("   Usando video mock (render no disponible)")
        return VideoAsset(
            id=f"video_mock_{id(script)}",
            video_path="",
            duration=float(int(script.duration)),
            status="pending",
        )

    async def _publish_video(
        self,
        video: VideoAsset,
        idea: ContentIdea,
        request: GenerateContentRequest,
    ) -> PublishResult:
        """Publica el video si hay publisher."""
        try:
            platform = Platform.from_string(request.platform)
            result = await self._publisher.publish(
                video=video,
                title=idea.hook[:100],
                description=f"{idea.description}\n\n#AI #Shorts #{request.niche or 'general'}",
                tags=[request.niche] if request.niche else ["ai-shorts"],
            )
            logger.info(f"🚀 Publicado: {result.url}")
            return result
        except Exception as e:
            logger.warning(f"⚠️ Publicación falló: {e}")
            return PublishResult(
                platform=request.platform,
                status="error",
                error=str(e),
            )
