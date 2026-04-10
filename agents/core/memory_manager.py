"""
Memory Manager - Gestor de Memoria Persistente del Agente
==========================================================
Maneja la persistencia de datos entre ejecuciones del agente.
"""

import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path


class MemoryManager:
    """
    Gestor de memoria persistente del agente.
    
    Maneja:
    - agent_memory.json: Contexto general del agente
    - performance_log.json: Historial de métricas
    - patterns.json: Patrones aprendidos (hooks, formatos exitosos)
    
    La memoria es bidireccional:
    - LEE antes de tomar decisiones
    - ESCRIBE después de analizar resultados
    """
    
    def __init__(self, memory_dir: str = "agents/memory"):
        """
        Inicializa el memory manager.
        
        Args:
            memory_dir: Directorio donde se guardan los archivos de memoria
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Rutas de archivos
        self.agent_memory_path = self.memory_dir / "agent_memory.json"
        self.performance_log_path = self.memory_dir / "performance_log.json"
        self.patterns_path = self.memory_dir / "patterns.json"
        
        # Inicializar archivos si no existen
        self._init_memory_files()
    
    def _init_memory_files(self):
        """Inicializa los archivos de memoria si no existen."""
        
        # Agent Memory
        if not self.agent_memory_path.exists():
            self._save_json(self.agent_memory_path, {
                "agent_id": None,
                "created_at": datetime.utcnow().isoformat(),
                "total_cycles": 0,
                "successful_cycles": 0,
                "failed_cycles": 0,
                "last_cycle": None,
                "preferences": {
                    "preferred_niche": None,
                    "preferred_platform": "youtube",
                    "preferred_tone": "educational"
                },
                "current_context": {}
            })
        
        # Performance Log
        if not self.performance_log_path.exists():
            self._save_json(self.performance_log_path, {
                "executions": [],
                "total_videos": 0,
                "avg_retention": 0,
                "avg_engagement": 0
            })
        
        # Patterns
        if not self.patterns_path.exists():
            self._save_json(self.patterns_path, {
                "best_hooks": [],
                "best_formats": [],
                "successful_topics": [],
                "failed_patterns": [],
                "trend_history": []
            })
    
    def _save_json(self, path: Path, data: Dict):
        """Guarda datos JSON en un archivo."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_json(self, path: Path) -> Dict:
        """Carga datos JSON de un archivo."""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # =========================================
    # OPERACIONES DE LECTURA
    # =========================================
    
    async def get_agent_memory(self) -> Dict[str, Any]:
        """Obtiene la memoria general del agente."""
        return self._load_json(self.agent_memory_path)
    
    async def get_performance_log(self) -> List[Dict]:
        """Obtiene el log de rendimiento completo."""
        data = self._load_json(self.performance_log_path)
        return data.get("executions", [])
    
    async def get_patterns(self) -> Dict[str, Any]:
        """Obtiene los patrones aprendidos."""
        return self._load_json(self.patterns_path)
    
    async def get_last_execution(self) -> Optional[Dict]:
        """Obtiene la última ejecución."""
        memory = await self.get_agent_memory()
        return memory.get("last_cycle")
    
    async def get_top_performers(self, limit: int = 5) -> List[Dict]:
        """Obtiene las mejores ejecuciones por retención."""
        executions = await self.get_performance_log()
        sorted_exec = sorted(
            executions,
            key=lambda x: x.get("metrics", {}).get("retention_avg", 0),
            reverse=True
        )
        return sorted_exec[:limit]
    
    async def get_avg_metrics(self) -> Dict[str, float]:
        """Obtiene los promedios de métricas."""
        log = await self.get_performance_log()
        if not log:
            return {"retention": 0, "engagement": 0, "views": 0}
        
        total = len(log)
        return {
            "retention": sum(e.get("metrics", {}).get("retention_avg", 0) for e in log) / total,
            "engagement": sum(
                e.get("metrics", {}).get("likes", 0) + 
                e.get("metrics", {}).get("comments", 0) +
                e.get("metrics", {}).get("shares", 0)
                for e in log
            ) / total,
            "views": sum(e.get("metrics", {}).get("views", 0) for e in log) / total
        }
    
    # =========================================
    # OPERACIONES DE ESCRITURA
    # =========================================
    
    async def save_execution(self, execution: Dict):
        """
        Guarda una ejecución completa en la memoria.
        
        Args:
            execution: Datos de la ejecución
        """
        # 1. Guardar en performance log
        performance = self._load_json(self.performance_log_path)
        
        execution_entry = {
            "execution_id": execution.get("cycle_id"),
            "timestamp": execution.get("start_time"),
            "goal": execution.get("goal"),
            "niche": execution.get("niche"),
            "platform": execution.get("platform"),
            "status": execution.get("status"),
            "hook": execution.get("best_hook"),
            "format": execution.get("selected_idea", {}).get("format"),
            "metrics": execution.get("metrics", {})
        }
        
        performance["executions"].append(execution_entry)
        performance["total_videos"] += 1
        
        # Recalcular promedios
        if execution.get("metrics"):
            views = execution["metrics"].get("views", 0)
            retention = execution["metrics"].get("retention", 0)
            engagement = execution["metrics"].get("engagement", 0)
            
            n = performance["total_videos"]
            old_avg = performance.get("avg_retention", 0)
            performance["avg_retention"] = ((old_avg * (n-1)) + retention) / n
            performance["avg_engagement"] = ((performance.get("avg_engagement", 0) * (n-1)) + engagement) / n
        
        self._save_json(self.performance_log_path, performance)
        
        # 2. Actualizar agent memory
        memory = self._load_json(self.agent_memory_path)
        memory["total_cycles"] += 1
        if execution.get("status") == "completed":
            memory["successful_cycles"] += 1
        else:
            memory["failed_cycles"] += 1
        memory["last_cycle"] = execution
        
        self._save_json(self.agent_memory_path, memory)
        
        # 3. Actualizar patrones si hay métricas
        if execution.get("metrics"):
            await self._update_patterns(execution)
    
    async def save_performance(self, video_id: str, analysis: Dict):
        """
        Guarda el análisis de rendimiento de un video.
        
        Args:
            video_id: ID del video
            analysis: Datos del análisis
        """
        # Buscar la ejecución en el log y actualizar
        performance = self._load_json(self.performance_log_path)
        
        for exec in performance["executions"]:
            if exec.get("execution_id") == video_id:
                exec["metrics"] = analysis.get("metrics", {})
                exec["recommendations"] = analysis.get("recommendations", [])
                exec["analyzed_at"] = datetime.utcnow().isoformat()
                break
        
        self._save_json(self.performance_log_path, performance)
        
        # Actualizar patrones
        await self._update_patterns({
            "metrics": analysis.get("metrics", {}),
            "selected_idea": {"format": "unknown"},
            "best_hook": "unknown"
        })
    
    async def _update_patterns(self, execution: Dict):
        """
        Actualiza los patrones aprendidos basándose en la ejecución.
        
        Args:
            execution: Datos de la ejecución
        """
        patterns = self._load_json(self.patterns_path)
        
        metrics = execution.get("metrics", {})
        retention = metrics.get("retention_avg", metrics.get("retention", 0))
        
        # Si el video va bien (retention > 60), aprender de él
        if retention > 60:
            # Aprender hook
            hook = execution.get("best_hook")
            if hook and hook not in patterns["best_hooks"]:
                patterns["best_hooks"].append(hook)
                # Mantener solo los últimos 20
                patterns["best_hooks"] = patterns["best_hooks"][-20:]
            
            # Aprender formato
            fmt = execution.get("selected_idea", {}).get("format")
            if fmt and fmt not in patterns["best_formats"]:
                patterns["best_formats"].append(fmt)
            
            # Aprender topic
            topic = execution.get("selected_idea", {}).get("topic")
            if topic and topic not in patterns["successful_topics"]:
                patterns["successful_topics"].append(topic)
                patterns["successful_topics"] = patterns["successful_topics"][-30:]
        
        # Si va mal (retention < 40), registrar como fracaso
        elif retention > 0 and retention < 40:
            failed = {
                "hook": execution.get("best_hook"),
                "format": execution.get("selected_idea", {}).get("format"),
                "retention": retention,
                "timestamp": datetime.utcnow().isoformat()
            }
            patterns["failed_patterns"].append(failed)
            patterns["failed_patterns"] = patterns["failed_patterns"][-20:]
        
        self._save_json(self.patterns_path, patterns)
    
    async def update_preferences(self, preferences: Dict):
        """
        Actualiza las preferencias del agente.
        
        Args:
            preferences: Nuevas preferencias
        """
        memory = self._load_json(self.agent_memory_path)
        memory["preferences"].update(preferences)
        self._save_json(self.agent_memory_path, memory)
    
    # =========================================
    # UTILIDADES
    # =========================================
    
    async def clear_old_data(self, days: int = 30):
        """
        Limpia datos antiguos.
        
        Args:
            days: Eliminar datos de más de X días
        """
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Limpiar performance log
        performance = self._load_json(self.performance_log_path)
        performance["executions"] = [
            e for e in performance["executions"]
            if datetime.fromisoformat(e.get("timestamp", "2000-01-01")) > cutoff
        ]
        self._save_json(self.performance_log_path, performance)
        
        # Limpiar patterns
        patterns = self._load_json(self.patterns_path)
        patterns["trend_history"] = [
            t for t in patterns.get("trend_history", [])
            if datetime.fromisoformat(t.get("timestamp", "2000-01-01")) > cutoff
        ]
        self._save_json(self.patterns_path, patterns)
    
    async def get_memory_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen del estado de la memoria."""
        return {
            "total_cycles": (await self.get_agent_memory()).get("total_cycles", 0),
            "successful": (await self.get_agent_memory()).get("successful_cycles", 0),
            "failed": (await self.get_agent_memory()).get("failed_cycles", 0),
            "avg_metrics": await self.get_avg_metrics(),
            "top_performers": await self.get_top_performers(3),
            "patterns": {
                "hooks_count": len((await self.get_patterns()).get("best_hooks", [])),
                "formats_count": len((await self.get_patterns()).get("best_formats", [])),
                "topics_count": len((await self.get_patterns()).get("successful_topics", []))
            }
        }