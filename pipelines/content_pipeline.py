"""
Content Pipeline - Pipeline Completo
=====================================
Orquestación completa de generación de contenido.
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.config import settings
from app.logger import logger

# Importar módulos
from modules.trends import TrendsAnalyzer
from modules.idea_generator import IdeaGenerator
from modules.script_generator import ScriptGenerator
from modules.hooks import HookGenerator
from modules.voice_generator import VoiceGenerator
from modules.video_generator import VideoGenerator
from modules.subtitles import SubtitlesGenerator
from modules.publisher import Publisher
from modules.analyzer import Analyzer


class ContentPipeline:
    """
    Pipeline completo de generación de contenido.
    
    Flujo:
    1. Obtener trends
    2. Generar ideas
    3. Escribir guion
    4. Generar hook
    5. Generar voz
    6. Generar video
    7. Añadir subtítulos
    8. Publicar
    9. Analizar (post-publicación)
    """
    
    def __init__(self, niche: Optional[str] = None, platform: str = "youtube"):
        """
        Inicializa el pipeline.
        
        Args:
            niche: Nicho específico
            platform: Plataforma destino
        """
        self.niche = niche
        self.platform = platform
        
        # Inicializar módulos
        self.trends = TrendsAnalyzer()
        self.idea_gen = IdeaGenerator()
        self.script_gen = ScriptGenerator()
        self.hook_gen = HookGenerator()
        self.voice_gen = VoiceGenerator()
        self.video_gen = VideoGenerator()
        self.subtitles = SubtitlesGenerator()
        self.publisher = Publisher()
        self.analyzer = Analyzer()
        
    async def run(self, num_videos: int = 1) -> List[Dict[str, Any]]:
        """
        Ejecuta el pipeline completo.
        
        Args:
            num_videos: Número de videos a generar
            
        Returns:
            Lista de resultados
        """
        logger.info(f"🎬 Iniciando pipeline ({num_videos} videos)")
        
        results = []
        
        for i in range(num_videos):
            logger.info(f"\n{'='*50}")
            logger.info(f"VIDEO {i+1}/{num_videos}")
            logger.info(f"{'='*50}")
            
            result = await self._generate_single_video(i)
            results.append(result)
            
            # Pequeña pausa entre videos
            if i < num_videos - 1:
                await asyncio.sleep(2)
        
        logger.info(f"\n✅ Pipeline completado: {len(results)} videos")
        return results
    
    async def _generate_single_video(self, index: int) -> Dict[str, Any]:
        """Genera un solo video."""
        
        try:
            # =========================================
            # STEP 1: Obtener trends
            # =========================================
            logger.info("\n📡 STEP 1: Obteniendo trends...")
            trends = await self.trends.get_trends(
                sources=["news", "twitter", "youtube"],
                niche=self.niche,
                limit=10
            )
            logger.info(f"   ✓ {len(trends)} trends obtenidos")
            
            if not trends:
                raise Exception("No se encontraron trends")
            
            # =========================================
            # STEP 2: Generar ideas
            # =========================================
            logger.info("\n🧠 STEP 2: Generando ideas...")
            ideas = await self.idea_gen.generate_ideas(
                trends=trends,
                niche=self.niche,
                styles=["story", "list", "tutorial"],
                count=3
            )
            logger.info(f"   ✓ {len(ideas)} ideas generadas")
            
            # Seleccionar mejor idea (la de mayor potencial)
            best_idea = ideas[0]
            logger.info(f"   ✓ Mejor idea: {best_idea.hook[:50]}...")
            
            # =========================================
            # STEP 3: Escribir guion
            # =========================================
            logger.info("\n✍️ STEP 3: Escribiendo guion...")
            script = await self.script_gen.generate_script(
                idea=best_idea,
                duration=45,
                tone="educational"
            )
            logger.info(f"   ✓ Guion de {script.duration}s ({script.word_count} palabras)")
            
            # =========================================
            # STEP 4: Generar hook
            # =========================================
            logger.info("\n🎯 STEP 4: Generando hook...")
            hooks = await self.hook_gen.generate_hooks(
                script=script,
                variations=3
            )
            best_hook = self.hook_gen.select_best_hook(hooks)
            logger.info(f"   ✓ Hook: {best_hook.text[:50]}...")
            
            # =========================================
            # STEP 5: Generar voz
            # =========================================
            logger.info("\n🔊 STEP 5: Generando voz...")
            # Usar el hook + body para la voz
            text_for_voice = f"{best_hook.text}. {script.body}"
            voice_audio = await self.voice_gen.generate_voice(
                text=text_for_voice,
                speed=1.0
            )
            logger.info(f"   ✓ Audio: {voice_audio.audio_path} ({voice_audio.duration:.1f}s)")
            
            # =========================================
            # STEP 6: Generar video
            # =========================================
            logger.info("\n🎬 STEP 6: Generando video...")
            video = await self.video_gen.generate_video(
                audio_path=voice_audio.audio_path,
                script={"duration": script.duration, "topic": best_idea.topic},
                aspect_ratio="9:16"
            )
            logger.info(f"   ✓ Video: {video.video_path}")
            
            # =========================================
            # STEP 7: Añadir subtítulos
            # =========================================
            logger.info("\n📝 STEP 7: Añadiendo subtítulos...")
            script_for_subs = f"{best_hook.text} {script.body} {script.cta}"
            subtitles_path = await self.subtitles.generate_subtitles(
                text=script_for_subs,
                duration=script.duration,
                output_format="srt"
            )
            
            # Burn subtitles en video
            video_with_subs = await self.subtitles.burn_subtitles(
                video_path=video.video_path,
                subtitles_path=subtitles_path
            )
            logger.info(f"   ✓ Subtítulos: {subtitles_path}")
            
            # =========================================
            # STEP 8: Publicar
            # =========================================
            logger.info("\n🚀 STEP 8: Publicando...")
            publish_result = await self.publisher.publish(
                video_path=video_with_subs,
                platform=self.platform,
                title=best_hook.text[:100],
                description=script.body[:200],
                tags=[self.niche] if self.niche else ["ai-shorts"]
            )
            logger.info(f"   ✓Publicado: {publish_result.url}")
            
            # =========================================
            # RESULTADO
            # =========================================
            return {
                "status": "success",
                "video_id": publish_result.video_id,
                "url": publish_result.url,
                "idea": best_idea.hook,
                "script": script.full_text[:100],
                "duration": script.duration,
                "platform": self.platform,
                "niche": self.niche,
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error en generación: {e}")
            return {
                "status": "error",
                "error": str(e),
                "index": index
            }
    
    async def run_single(
        self,
        idea: Any = None,
        niche: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el pipeline para una idea específica.
        
        Args:
            idea: Idea específica (opcional)
            niche: Nicho específico
            
        Returns:
            Resultado de la generación
        """
        # Si no hay idea, generar una
        if not idea:
            trends = await self.trends.get_trends(niche=niche or self.niche)
            ideas = await self.idea_gen.generate_ideas(trends=trends)
            idea = ideas[0]
        
        return await self._generate_single_video(0)