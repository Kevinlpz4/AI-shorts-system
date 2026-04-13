"""
Content Evaluator - Evaluador y Optimizador de Contenido
=========================================================
Evalúa y optimiza ideas y scripts para maximizar viralidad.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from app.logger import logger


@dataclass
class EvaluationResult:
    """Resultado de evaluación de contenido."""
    score_total: float
    clasificacion: str  # excelente, aceptable, malo
    criterios: Dict[str, float]
    recomendaciones: List[str]
    optimizado: bool = False


class ContentEvaluator:
    """
    Evaluador y optimizador de contenido viral.
    
    Evalúa ideas y scripts antes de continuar el pipeline.
    """
    
    def __init__(self):
        self.score_threshold_excelente = 8.0
        self.score_threshold_aceptable = 6.0
        self.max_intentos_optimizacion = 2
    
    async def evaluate_idea(
        self,
        idea: Any
    ) -> EvaluationResult:
        """
        Evalúa una idea según criterios de viralidad.
        
        Args:
            idea: Objeto Idea a evaluar
            
        Returns:
            EvaluationResult con score y clasificación
        """
        hook = idea.hook
        format_type = idea.format
        
        # Evaluar cada criterio
        criterios = {
            "curiosidad": self._eval_curiosidad(hook),
            "impacto_emocional": self._eval_emocion(hook),
            "claridad": self._eval_claridad(hook),
            "potencial_viral": self._eval_viral(hook, format_type),
            "hook_implicito": self._eval_hook_inicial(hook)
        }
        
        # Calcular score total (promedio)
        score_total = sum(criterios.values()) / len(criterios)
        
        # Clasificar
        if score_total >= self.score_threshold_excelente:
            clasificacion = "excelente"
        elif score_total >= self.score_threshold_aceptable:
            clasificacion = "aceptable"
        else:
            clasificacion = "malo"
        
        # Generar recomendaciones
        recomendaciones = self._generar_recomendaciones(criterios)
        
        logger.info(f"📊 Idea evaluada: score={score_total:.1f}/10 ({clasificacion})")
        
        return EvaluationResult(
            score_total=score_total,
            clasificacion=clasificacion,
            criterios=criterios,
            recomendaciones=recomendaciones
        )
    
    async def evaluate_script(
        self,
        script: Any
    ) -> EvaluationResult:
        """
        Evalúa un script según criterios de retención.
        
        Args:
            script: Objeto Script a evaluar
            
        Returns:
            EvaluationResult con score y clasificación
        """
        hook = script.hook
        body = script.body
        cta = script.cta
        
        # Evaluar cada criterio
        criterios = {
            "hook_fuerte": self._eval_hook_script(hook),
            "ritmo_rapido": self._eval_ritmo(body),
            "claridad_narrativa": self._eval_claridad_narrativa(body),
            "final_con_impacto": self._eval_final(cta),
            "longitud_apropiada": self._eval_duracion(script.duration)
        }
        
        # Calcular score total
        score_total = sum(criterios.values()) / len(criterios)
        
        # Clasificar
        if score_total >= self.score_threshold_excelente:
            clasificacion = "excelente"
        elif score_total >= self.score_threshold_aceptable:
            clasificacion = "aceptable"
        else:
            clasificacion = "malo"
        
        recomendaciones = self._generar_recomendaciones(criterios)
        
        logger.info(f"📊 Script evaluado: score={score_total:.1f}/10 ({clasificacion})")
        
        return EvaluationResult(
            score_total=score_total,
            clasificacion=clasificacion,
            criterios=criterios,
            recomendaciones=recomendaciones
        )
    
    async def optimizar_idea(
        self,
        idea: Any,
        recomendaciones: List[str]
    ) -> Any:
        """
        Optimiza una idea según las recomendaciones.
        
        Args:
            idea: Idea a optimizar
            recomendaciones: Lista de recomendaciones
            
        Returns:
            Idea optimizada
        """
        logger.info("🔧 Optimizando idea...")
        
        hook = idea.hook
        
        # Aplicar mejoras
        hook_optimizado = hook
        
        # Si hay recomendaciones de curiosidad, mejorar el hook
        if "curiosidad" in str(recomendaciones).lower():
            hook_optimizado = self._mejorar_curiosidad(hook_optimizado)
        
        if "emocion" in str(recomendaciones).lower():
            hook_optimizado = self._mejorar_emocion(hook_optimizado)
        
        if "claridad" in str(recomendaciones).lower():
            hook_optimizado = self._mejorar_claridad(hook_optimizado)
        
        # Crear nueva idea optimizada
        from modules.idea_generator import Idea
        idea_optimizada = Idea(
            id=f"{idea.id}_opt",
            trend_id=idea.trend_id,
            topic=idea.topic,
            hook=hook_optimizado,
            format=idea.format,
            viral_potential=min(100, idea.viral_potential + 10),
            description=idea.description,
            target_audience=idea.target_audience,
            keywords=idea.keywords
        )
        
        logger.info(f"✅ Idea optimizada: {hook_optimizado[:50]}...")
        
        return idea_optimizada
    
    async def optimizar_script(
        self,
        script: Any,
        recomendaciones: List[str]
    ) -> Any:
        """
        Optimiza un script según las recomendaciones.
        
        Args:
            script: Script a optimizar
            recomendaciones: Lista de recomendaciones
            
        Returns:
            Script optimizado
        """
        logger.info("🔧 Optimizando script...")
        
        hook = script.hook
        body = script.body
        cta = script.cta
        
        # Mejorar hook si es necesario
        if "hook" in str(recomendaciones).lower():
            hook = self._mejorar_hook_script(hook)
        
        # Mejorar ritmo si es necesario
        if "ritmo" in str(recomendaciones).lower():
            body = self._mejorar_ritmo(body)
        
        # Mejorar final si es necesario
        if "final" in str(recomendaciones).lower():
            cta = self._mejorar_cta(cta)
        
        # Crear nuevo script optimizado
        from modules.script_generator import Script
        script_optimizado = Script(
            id=f"{script.id}_opt",
            idea_id=script.idea_id,
            topic=script.topic,  # Agregado
            hook=hook,
            body=body,
            cta=cta,
            full_text=f"{hook}. {body} {cta}",
            duration=script.duration,
            word_count=script.word_count,
            tone=script.tone,
            format=script.format
        )
        
        logger.info("✅ Script optimizado")
        
        return script_optimizado
    
    # =========================================
    # CRITERIOS DE EVALUACIÓN (0-10)
    # =========================================
    
    def _eval_curiosidad(self, text: str) -> float:
        """Evalúa nivel de curiosidad del hook."""
        palabras_curiosas = [
            "secret", "descubrir", "nadie", "verdad", "shock",
            "increíble", "sorprendente", "no vas a creer", "esto cambió",
            "error", "malo", "peligro", "warning", "hack"
        ]
        
        text_lower = text.lower()
        score = 5.0  # Base
        
        for palabra in palabras_curiosas:
            if palabra in text_lower:
                score += 1.0
        
        # Preguntas generan curiosidad
        if "?" in text:
            score += 1.5
        
        # Números específicos generan curiosidad (ej: "5 cosas")
        import re
        if re.search(r'\d+', text):
            score += 1.0
        
        return min(10, score)
    
    def _eval_emocion(self, text: str) -> float:
        """Evalúa impacto emocional."""
        palabras_emocionales = [
            "miedo", "terror", "peligro", "increíble", "asombroso",
            "revolucionario", "destruye", "cambia todo", "nunca más",
            "fatal", "error", "alerta", "importante", "urgente"
        ]
        
        text_lower = text.lower()
        score = 5.0
        
        for palabra in palabras_emocionales:
            if palabra in text_lower:
                score += 1.0
        
        return min(10, score)
    
    def _eval_claridad(self, text: str) -> float:
        """Evalúa claridad del mensaje."""
        # Demasiado largo = menos claro
        if len(text) > 100:
            return 5.0
        elif len(text) > 60:
            return 7.0
        elif len(text) > 30:
            return 8.5
        else:
            return 9.0
    
    def _eval_viral(self, text: str, format_type: str) -> float:
        """Evalúa potencial viral."""
        # Formatos con alto potencial viral
        formatos_virales = {
            "list": 8.5,    # "5 cosas..."
            "fact": 8.0,   # Datos curiosos
            "reaction": 7.5,
            "tutorial": 7.0,
            "story": 6.5
        }
        
        return formatos_virales.get(format_type, 6.0)
    
    def _eval_hook_inicial(self, text: str) -> float:
        """Evalúa si el hook captura atención."""
        hooks_fuertes = [
            "¿sabías", "descubre", "atención", "importante",
            "esto", "nunca", "5 ", "3 ", "secret"
        ]
        
        text_lower = text.lower()
        score = 5.0
        
        for hook in hooks_fuertes:
            if hook in text_lower:
                score += 1.0
        
        return min(10, score)
    
    def _eval_hook_script(self, hook: str) -> float:
        """Evalúa strength del hook en script."""
        # Hooks cortos y directos son mejores
        if len(hook) < 30:
            return 9.0
        elif len(hook) < 50:
            return 7.5
        elif len(hook) < 80:
            return 6.0
        else:
            return 4.0
    
    def _eval_ritmo(self, body: str) -> float:
        """Evalúa si el ritmo es rápido (oraciones cortas)."""
        oraciones = body.split(".")
        
        if len(oraciones) < 3:
            return 5.0  # Muy pocas oraciones
        
        # Oraciones cortas = ritmo rápido
        promedio_palabras = sum(len(o.split()) for o in oraciones) / len(oraciones)
        
        if promedio_palabras < 10:
            return 9.0
        elif promedio_palabras < 15:
            return 7.5
        elif promedio_palabras < 20:
            return 6.0
        else:
            return 4.5
    
    def _eval_claridad_narrativa(self, text: str) -> float:
        """Evalúa claridad narrativa del body."""
        # Oraciones muy largas = menos claro
        oraciones = text.split(".")
        if not oraciones:
            return 5.0
        
        promedio_letras = sum(len(o) for o in oraciones) / len(oraciones)
        
        if promedio_letras < 50:
            return 9.0
        elif promedio_letras < 80:
            return 7.5
        elif promedio_letras < 120:
            return 6.0
        else:
            return 4.5
    
    def _eval_final(self, cta: str) -> float:
        """Evalúa si el final tiene impacto."""
        cta_lower = cta.lower()
        
        # CTAs con urgencia funcionan mejor
        if "ahora" in cta_lower or "ya" in cta_lower:
            return 8.5
        elif "sígueme" in cta_lower or "like" in cta_lower:
            return 7.5
        else:
            return 6.0
    
    def _eval_duracion(self, duration: int) -> float:
        """Evalúa si la duración es apropiada."""
        # Shorts óptimos son 30-60 segundos
        if 30 <= duration <= 60:
            return 9.0
        elif duration < 30:
            return 7.0
        elif duration < 90:
            return 6.0
        else:
            return 4.0
    
    def _generar_recomendaciones(self, criterios: Dict[str, float]) -> List[str]:
        """Genera recomendaciones basadas en criterios bajos."""
        recomendaciones = []
        
        for criterio, score in criterios.items():
            if score < 6.0:
                if criterio == "curiosidad":
                    recomendaciones.append("Mejora la curiosidad del hook")
                elif criterio == "impacto_emocional":
                    recomendaciones.append("Añade más impacto emocional")
                elif criterio == "claridad":
                    recomendaciones.append("Haz el texto más claro y directo")
                elif criterio == "potencial_viral":
                    recomendaciones.append("Usa un formato más viral (list, fact)")
                elif criterio == "hook_implicito":
                    recomendaciones.append("Mejora el hook inicial")
                elif criterio == "hook_fuerte":
                    recomendaciones.append("Mejora el hook del script")
                elif criterio == "ritmo_rapido":
                    recomendaciones.append("Mejora el ritmo (oraciones más cortas)")
                elif criterio == "claridad_narrativa":
                    recomendaciones.append("Mejora la claridad narrativa")
                elif criterio == "final_con_impacto":
                    recomendaciones.append("Mejora el final/CTA")
                elif criterio == "longitud_apropiada":
                    recomendaciones.append("Ajusta la duración")
        
        return recomendaciones
    
    # =========================================
    # MÉTODOS DE OPTIMIZACIÓN
    # =========================================
    
    def _mejorar_curiosidad(self, hook: str) -> str:
        """Mejora la curiosidad del hook."""
        hooks_mejorados = [
            f"¿Sabías esto sobre {hook}?",
            f"El secreto de {hook} que nadie te cuenta",
            f"Por esto {hook} es trending ahora",
        ]
        return hooks_mejorados[0]
    
    def _mejorar_emocion(self, hook: str) -> str:
        """Mejora el impacto emocional."""
        return f"⚠️ {hook} - Esto va a cambiar todo"
    
    def _mejorar_claridad(self, hook: str) -> str:
        """Mejora la claridad."""
        # Acortar si es muy largo
        if len(hook) > 50:
            words = hook.split()
            return " ".join(words[:7]) + "..."
        return hook
    
    def _mejorar_hook_script(self, hook: str) -> str:
        """Mejora el hook del script."""
        return f"🎯 {hook}"
    
    def _mejorar_ritmo(self, body: str) -> str:
        """Mejora el ritmo del body."""
        # Acortar oraciones
        oraciones = body.split(".")
        oraciones_mejoradas = [o.strip() for o in oraciones if len(o.strip()) > 10]
        return ". ".join(oraciones_mejoradas[:4]) + "."
    
    def _mejorar_cta(self, cta: str) -> str:
        """Mejora el CTA."""
        return f"🔥 {cta} Sígueme para más!"
