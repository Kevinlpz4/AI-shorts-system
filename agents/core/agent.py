"""
AI Shorts Agent - Core Agent Module
=====================================
Agente Maestro que orquesta la creación automática de contenido viral.
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import uuid

from .orchestrator import PipelineOrchestrator
from .decision_engine import DecisionEngine
from .memory_manager import MemoryManager


class AIShortsAgent:
    """
    Agente Maestro del AI Shorts System.
    
    Su función es orquestar la ejecución de skills para generar
    contenido viral en formato short.
    
    NO genera contenido directamente - ORQUESTA la generación.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el agente.
        
        Args:
            config: Configuración opcional del agente
        """
        self.config = config or {}
        self.agent_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow().isoformat()
        
        # Inicializar componentes
        self.memory = MemoryManager()
        self.orchestrator = PipelineOrchestrator()
        self.decision_engine = DecisionEngine(self.memory)
        
        # Estado del agente
        self.current_cycle: Optional[Dict] = None
        self.execution_history: List[Dict] = []
        
    async def run_full_cycle(
        self,
        goal: str,
        niche: Optional[str] = None,
        platform: str = "youtube"
    ) -> Dict[str, Any]:
        """
        Ejecuta un ciclo completo de generación de contenido.
        
        Este es el método principal que orquesta todo el flujo:
        1. Analizar tendencias
        2. Generar ideas
        3. Seleccionar mejor idea (usando memoria)
        4. Generar script
        5. Generar hook
        6. Generar voz
        7. Generar video
        8. Añadir subtítulos
        9. Publicar
        10. Analizar rendimiento
        11. Guardar en memoria
        
        Args:
            goal: Objetivo del contenido (ej: "crear contenido viral sobre IA")
            niche: Nicho específico (opcional)
            platform: Plataforma destino ("youtube", "tiktok", "instagram")
            
        Returns:
            Dict con el resultado completo del ciclo
        """
        cycle_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        self.current_cycle = {
            "cycle_id": cycle_id,
            "goal": goal,
            "niche": niche,
            "platform": platform,
            "start_time": start_time.isoformat(),
            "status": "running",
            "steps": []
        }
        
        try:
            # =========================================
            # STEP 1: ANALIZAR TENDENCIAS
            # =========================================
            await self._log_step("get_trends", "iniciado")
            trends_result = await self.orchestrator.execute_skill(
                "get_trends",
                sources=["twitter", "youtube", "tiktok", "news"],
                niche=niche,
                limit=20
            )
            await self._log_step("get_trends", "completado", trends_result)
            
            if not trends_result.get("trends"):
                return self._error_response("No se encontraron tendencias disponibles")
            
            # =========================================
            # STEP 2: GENERAR IDEAS
            # =========================================
            await self._log_step("generate_idea", "iniciado")
            ideas_result = await self.orchestrator.execute_skill(
                "generate_idea",
                trends=trends_result["trends"],
                niche=niche,
                style=["story", "list", "reaction", "tutorial", "fact"]
            )
            await self._log_step("generate_idea", "completado", ideas_result)
            
            if not ideas_result.get("ideas"):
                return self._error_response("No se generaron ideas")
            
            # =========================================
            # STEP 3: CONSULTAR MEMORIA PARA DECISIÓN
            # =========================================
            # Usar decision engine para seleccionar mejor idea basada en memoria
            selected_idea = self.decision_engine.select_best_idea(
                ideas_result["ideas"],
                await self.memory.get_patterns()
            )
            
            # =========================================
            # STEP 4: GENERAR SCRIPT
            # =========================================
            await self._log_step("write_script", "iniciado")
            script_result = await self.orchestrator.execute_skill(
                "write_script",
                idea=selected_idea,
                duration=45,
                tone="educational"
            )
            await self._log_step("write_script", "completado", script_result)
            
            # =========================================
            # STEP 5: OPTIMIZAR HOOK
            # =========================================
            await self._log_step("generate_hook", "iniciado")
            hook_result = await self.orchestrator.execute_skill(
                "generate_hook",
                script=script_result["script"],
                variations=3
            )
            # Seleccionar mejor hook usando memoria
            best_hook = self.decision_engine.select_best_hook(
                hook_result.get("hooks", []),
                await self.memory.get_performance_log()
            )
            await self._log_step("generate_hook", "completado", {"hook": best_hook})
            
            # =========================================
            # STEP 6: GENERAR VOZ
            # =========================================
            await self._log_step("generate_voice", "iniciado")
            voice_result = await self.orchestrator.execute_skill(
                "generate_voice",
                script_text=f"{best_hook} {script_result['script']['body']}",
                voice_id=self.config.get("default_voice", "default"),
                speed=1.0
            )
            await self._log_step("generate_voice", "completado", voice_result)
            
            # =========================================
            # STEP 7: GENERAR VIDEO
            # =========================================
            await self._log_step("generate_video", "iniciado")
            video_result = await self.orchestrator.execute_skill(
                "generate_video",
                script=script_result["script"],
                audio_path=voice_result.get("audio_path"),
                aspect_ratio="9:16"
            )
            await self._log_step("generate_video", "completado", video_result)
            
            # =========================================
            # STEP 8: AÑADIR SUBTÍTULOS
            # =========================================
            await self._log_step("generate_subtitles", "iniciado")
            subtitles_result = await self.orchestrator.execute_skill(
                "generate_subtitles",
                video_path=video_result.get("video_path"),
                language="es",
                style="burned"
            )
            await self._log_step("generate_subtitles", "completado", subtitles_result)
            
            # =========================================
            # STEP 9: PUBLICAR
            # =========================================
            await self._log_step("publish", "iniciado")
            publish_result = await self.orchestrator.execute_skill(
                "publish",
                video_path=subtitles_result.get("video_path"),
                platform=platform,
                title=best_hook,
                description=script_result["script"]["body"][:100],
                tags=[niche] if niche else []
            )
            await self._log_step("publish", "completado", publish_result)
            
            # =========================================
            # STEP 10: ANALIZAR RENDIMIENTO (ASYNC)
            # =========================================
            # Este paso se hace después de que el video tenga métricas
            # Por ahora guardamos el resultado
            await self._log_step("analyze_performance", "pendiente", 
                                  {"message": "Se ejecutará cuando haya métricas disponibles"})
            
            # Guardar en memoria el ciclo completado
            cycle_result = {
                "cycle_id": cycle_id,
                "goal": goal,
                "niche": niche,
                "platform": platform,
                "status": "completed",
                "start_time": start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "selected_idea": selected_idea,
                "best_hook": best_hook,
                "script": script_result["script"],
                "video_url": publish_result.get("url"),
                "steps": self.current_cycle["steps"]
            }
            
            await self.memory.save_execution(cycle_result)
            self.execution_history.append(cycle_result)
            
            return {
                "status": "success",
                "cycle_id": cycle_id,
                "video_url": publish_result.get("url"),
                "metrics": {
                    "retention": "pending",
                    "engagement": "pending",
                    "viral_score": "pending"
                },
                "recommendations": await self._get_recommendations()
            }
            
        except Exception as e:
            await self._log_step("error", "fallido", {"error": str(e)})
            self.current_cycle["status"] = "failed"
            return self._error_response(str(e))
    
    async def _log_step(self, step_name: str, status: str, data: Optional[Dict] = None):
        """Registra un paso en el ciclo actual."""
        if self.current_cycle:
            self.current_cycle["steps"].append({
                "step": step_name,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            })
    
    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """Genera respuesta de error."""
        return {
            "status": "error",
            "error": error_message,
            "cycle_id": self.current_cycle.get("cycle_id") if self.current_cycle else None
        }
    
    async def _get_recommendations(self) -> List[str]:
        """Obtiene recomendaciones basadas en memoria."""
        patterns = await self.memory.get_patterns()
        recommendations = []
        
        if patterns.get("best_hooks"):
            recommendations.append("Usar hooks de tipo: " + ", ".join(patterns["best_hooks"][:3]))
        
        if patterns.get("best_formats"):
            recommendations.append("Formatos con mejor retención: " + ", ".join(patterns["best_formats"][:3]))
        
        return recommendations
    
    async def get_status(self) -> Dict[str, Any]:
        """Retorna el estado actual del agente."""
        return {
            "agent_id": self.agent_id,
            "created_at": self.created_at,
            "current_cycle": self.current_cycle,
            "total_executions": len(self.execution_history),
            "last_execution": self.execution_history[-1] if self.execution_history else None
        }
    
    async def run_analytics(self, video_id: str, platform: str) -> Dict[str, Any]:
        """
        Ejecuta análisis de rendimiento de un video ya publicado.
        
        Este método se llama después de que el video tiene métricas
        para guardar el análisis en memoria.
        """
        analysis_result = await self.orchestrator.execute_skill(
            "analyze_performance",
            video_id=video_id,
            platform=platform
        )
        
        # Guardar análisis en memoria
        await self.memory.save_performance(video_id, analysis_result)
        
        return analysis_result