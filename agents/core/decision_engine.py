"""
Decision Engine - Motor de Decisiones Basado en Memoria
=======================================================
Este módulo decide qué opción elegir basándose en datos históricos.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class DecisionEngine:
    """
    Motor de decisiones del agente.
    
    Usa la memoria para tomar decisiones informadas:
    - Seleccionar mejor idea basándose en trends históricos
    - Elegir mejor hook basándose en retención previa
    - Descartar opciones con bajo rendimiento
    """
    
    def __init__(self, memory_manager):
        """
        Inicializa el decision engine.
        
        Args:
            memory_manager: Instancia de MemoryManager para consultar datos
        """
        self.memory = memory_manager
        
    def select_best_idea(
        self,
        ideas: List[Dict],
        patterns: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Selecciona la mejor idea basándose en:
        1. Potencial viral del trend
        2. Patrones aprendidos (qué formatos funcionan mejor)
        3. Relevancia con nichos previos exitosos
        
        Args:
            ideas: Lista de ideas generadas
            patterns: Patrones aprendidos (opcional)
            
        Returns:
            La idea seleccionada
        """
        if not ideas:
            raise ValueError("No hay ideas para seleccionar")
        
        scored_ideas = []
        
        for idea in ideas:
            score = idea.get("viral_potential", 50)
            
            # Ajustar score basado en patrones si hay datos
            if patterns:
                # Si el formato ya funcionó antes, aumentar score
                if idea.get("format") in patterns.get("best_formats", []):
                    score += 15
                    
                # Si el topic es similar a exitosos, aumentar score
                successful_topics = patterns.get("successful_topics", [])
                topic = idea.get("topic", "")
                for successful_topic in successful_topics:
                    if successful_topic.lower() in topic.lower():
                        score += 10
                        break
            
            # Penalizar si recently ya se usó un topic similar
            # (esto se chequea en memoria real)
            
            scored_ideas.append({
                **idea,
                "final_score": score
            })
        
        # Ordenar por score descendente
        scored_ideas.sort(key=lambda x: x["final_score"], reverse=True)
        
        # Retornar la mejor idea
        return scored_ideas[0]
    
    def select_best_hook(
        self,
        hooks: List[Dict],
        performance_log: Optional[List[Dict]] = None
    ) -> str:
        """
        Selecciona el mejor hook basándose en:
        1. Tipo de hook (question, statement, reveal, list, trending)
        2. Datos históricos de retención por tipo
        3. Matching con contenido exitoso previo
        
        Args:
            hooks: Lista de hooks generados
            performance_log: Log de rendimiento previo (opcional)
            
        Returns:
            El texto del mejor hook
        """
        if not hooks:
            return "Hook automático por defecto"
        
        # Scores base por tipo de hook (basados en mejores prácticas)
        hook_type_scores = {
            "question": 85,      # Las preguntas captan atención
            "reveal": 90,        # Los secretos/descubrimientos funcionan bien
            "list": 80,          # Las listas son predecibles pero efectivas
            "statement": 70,     # Los statements necesitan ser fuertes
            "trending": 75      # Usar "trending" puede funcionar
        }
        
        scored_hooks = []
        
        for hook in hooks:
            base_score = hook.get("score", 50)
            hook_type = hook.get("type", "statement")
            
            # Score del tipo
            type_score = hook_type_scores.get(hook_type, 50)
            
            # Ajustar con datos de performance si hay
            final_score = base_score
            if performance_log:
                # Si este tipo funcionó bien antes, aumentar
                type_performance = self._get_type_performance(hook_type, performance_log)
                if type_performance:
                    final_score += type_performance * 0.2
            
            # El score final es combinación
            final_score = (base_score * 0.4) + (type_score * 0.6)
            
            scored_hooks.append({
                **hook,
                "final_score": final_score
            })
        
        # Ordenar por score
        scored_hooks.sort(key=lambda x: x["final_score"], reverse=True)
        
        return scored_hooks[0].get("text", hooks[0].get("text", ""))
    
    def _get_type_performance(
        self,
        hook_type: str,
        performance_log: List[Dict]
    ) -> Optional[float]:
        """
        Obtiene el rendimiento promedio de un tipo de hook.
        
        Args:
            hook_type: Tipo de hook
            performance_log: Log de ejecuciones previas
            
        Returns:
            Score de rendimiento (0-100) o None
        """
        if not performance_log:
            return None
            
        # Filtrar ejecuciones que usaron este tipo de hook
        matching = [
            ex for ex in performance_log
            if ex.get("hook_type") == hook_type
        ]
        
        if not matching:
            return None
            
        # Calcular promedio de retención
        retentions = [
            ex.get("metrics", {}).get("retention_avg", 0)
            for ex in matching
        ]
        
        return sum(retentions) / len(retentions) if retentions else None
    
    def should_continue(
        self,
        current_result: Dict,
        min_quality_threshold: int = 60
    ) -> bool:
        """
        Decide si continuar con el pipeline o abortar.
        
        Args:
            current_result: Resultado actual del paso
            min_quality_threshold: Score mínimo para continuar
            
        Returns:
            True si debe continuar, False si debe abortar
        """
        # Si hay error, no continuar
        if current_result.get("status") == "error":
            return False
            
        # Si el resultado tiene score de calidad, usarlo
        quality_score = current_result.get("quality_score", 100)
        return quality_score >= min_quality_threshold
    
    def get_optimization_suggestions(
        self,
        last_execution: Dict
    ) -> List[str]:
        """
        Genera sugerencias de optimización basadas en la última ejecución.
        
        Args:
            last_execution: Datos de la última ejecución
            
        Returns:
            Lista de sugerencias
        """
        suggestions = []
        
        metrics = last_execution.get("metrics", {})
        
        # Analizar retención
        retention = metrics.get("retention_avg", 0)
        if retention < 60:
            suggestions.append("El hook no está captando atención suficiente - considera hacerlo más corto")
        elif retention > 80:
            suggestions.append("Excelente retención - mantener estilo similar")
        
        # Analizar engagement
        likes = metrics.get("likes", 0)
        comments = metrics.get("comments", 0)
        if comments > likes * 0.1:
            suggestions.append("Alto engagement en comentarios - considera más contenido controversial/participativo")
            
        # Analizar shares
        shares = metrics.get("shares", 0)
        if shares < 50:
            suggestions.append("Pocos shares - considera añadir más valor único al final")
            
        return suggestions
    
    def decide_next_action(
        self,
        current_step: str,
        step_result: Dict,
        full_context: Dict
    ) -> str:
        """
        Decide cuál es el siguiente paso en el pipeline.
        
        Args:
            current_step: Paso actual
            step_result: Resultado del paso actual
            full_context: Contexto completo del ciclo
            
        Returns:
            Nombre del siguiente paso
        """
        # Mapa de siguiente paso por defecto
        next_steps = {
            "get_trends": "generate_idea",
            "generate_idea": "write_script",
            "write_script": "generate_hook",
            "generate_hook": "generate_voice",
            "generate_voice": "generate_video",
            "generate_video": "generate_subtitles",
            "generate_subtitles": "publish",
            "publish": "analyze_performance",
            "analyze_performance": "finished"
        }
        
        # Si el resultado actual tiene calidad baja, ir a retry o skip
        if not self.should_continue(step_result):
            if current_step in ["generate_idea", "write_script"]:
                return "retry"  # Reintentar con otros parámetros
            return "abort"
        
        return next_steps.get(current_step, "finished")
    
    def rank_trends(
        self,
        trends: List[Dict],
        prefer_topics: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Rankea trends por potencial viral, considerando preferencias.
        
        Args:
            trends: Lista de trends
            prefer_topics: Lista de topics preferidos
            
        Returns:
            Lista de trends ordenados por score
        """
        scored_trends = []
        
        for trend in trends:
            score = trend.get("viral_score", 50)
            
            # Boost si es de un topic preferido
            if prefer_topics:
                topic = trend.get("topic", "").lower()
                for pref in prefer_topics:
                    if pref.lower() in topic:
                        score += 15
                        break
            
            scored_trends.append({
                **trend,
                "final_score": score
            })
        
        scored_trends.sort(key=lambda x: x["final_score"], reverse=True)
        return scored_trends