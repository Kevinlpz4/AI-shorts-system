"""
Global Cache - Sistema de caché centralizado
============================================
Proporciona cache en memoria para evitar requests duplicados.

TTL por defecto: 1 hora
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Optional


class GlobalCache:
    """
    Cache global para todo el sistema.
    
    Uso:
    - Cache de ideas por topic
    - Cache de scripts por idea_id
    - Cache de hooks por script
    - Cache de trends por nicho
    """
    
    _cache: dict = {}
    _ttl: int = 3600  # 1 hora en segundos
    _hits: int = 0
    _misses: int = 0
    
    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """Obtiene valor del cache si existe y no expiró."""
        if key in cls._cache:
            entry = cls._cache[key]
            age = (datetime.now() - entry['created_at']).total_seconds()
            
            if age < cls._ttl:
                cls._hits += 1
                logger.info(f"💾 Cache HIT: {key[:20]}... (hits: {cls._hits})")
                return entry['value']
            else:
                # Expirado
                del cls._cache[key]
        
        cls._misses += 1
        return None
    
    @classmethod
    def set(cls, key: str, value: Any):
        """Guarda valor en cache."""
        cls._cache[key] = {
            'value': value,
            'created_at': datetime.now()
        }
        logger.info(f"💾 Cache SET: {key[:20]}... (total: {len(cls._cache)})")
    
    @classmethod
    def generate_key(cls, *args, **kwargs) -> str:
        """Genera key únicahash a partir de argumentos."""
        content = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    @classmethod
    def clear(cls):
        """Limpia todo el cache."""
        cls._cache.clear()
        cls._hits = 0
        cls._misses = 0
        logger.info("💾 Cache limpiado")
    
    @classmethod
    def get_stats(cls) -> dict:
        """Retorna estadísticas de uso."""
        return {
            'size': len(cls._cache),
            'hits': cls._hits,
            'misses': cls._misses,
            'hit_rate': cls._hits / (cls._hits + cls._misses) if (cls._hits + cls._misses) > 0 else 0
        }


# Import logger
from app.logger import logger


def cached(ttl: int = 3600):
    """
    Decorador para cachear funciones.
    
    Uso:
    @cached(ttl=1800)  # 30 minutos
    async def mi_funcion():
        ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            key = GlobalCache.generate_key(func.__name__, *args, **kwargs)
            
            # Intentar obtener del cache
            result = GlobalCache.get(key)
            if result is not None:
                return result
            
            # Ejecutar y guardar en cache
            result = await func(*args, **kwargs)
            GlobalCache.set(key, result)
            return result
        
        return wrapper
    return decorator


# =========================================
# CACHE ESPECÍFICO POR TIPO
# =========================================

class CacheManager:
    """Administrador de cache por tipo de recurso."""
    
    @staticmethod
    def cache_idea(topic: str, idea) -> None:
        """Guarda idea en cache."""
        key = GlobalCache.generate_key("idea", topic)
        GlobalCache.set(key, idea)
    
    @staticmethod
    def get_cached_idea(topic: str) -> Optional[Any]:
        """Obtiene idea del cache."""
        key = GlobalCache.generate_key("idea", topic)
        return GlobalCache.get(key)
    
    @staticmethod
    def cache_script(idea_id: str, script) -> None:
        """Guarda script en cache."""
        key = GlobalCache.generate_key("script", idea_id)
        GlobalCache.set(key, script)
    
    @staticmethod
    def get_cached_script(idea_id: str) -> Optional[Any]:
        """Obtiene script del cache."""
        key = GlobalCache.generate_key("script", idea_id)
        return GlobalCache.get(key)
    
    @staticmethod
    def cache_trends(niche: str, trends) -> None:
        """Guarda trends en cache."""
        key = GlobalCache.generate_key("trends", niche)
        GlobalCache.set(key, trends)
    
    @staticmethod
    def get_cached_trends(niche: str) -> Optional[Any]:
        """Obtiene trends del cache."""
        key = GlobalCache.generate_key("trends", niche)
        return GlobalCache.get(key)
