import time
import hashlib
import json
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


class MemoryCache:
    """
    Caché en memoria con TTL.
    
    Puerto que implementa: CachePort (domain/ports/cache.py)
    
    Features:
    - TTL configurable por item o global
    - Hit/miss tracking
    - Thread-safe (no lock necesario para asyncio single-thread)
    """
    
    def __init__(self, default_ttl: int = 3600):
        self._default_ttl = default_ttl
        self._cache: dict[str, dict] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Obtiene valor del caché si existe y no expiró."""
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None

        age = time.time() - entry["created_at"]
        if age < entry["ttl"]:
            self._hits += 1
            logger.debug(f"💾 Cache HIT: {key[:30]}... (hits: {self._hits})")
            return entry["value"]

        # Expirado
        del self._cache[key]
        self._misses += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Guarda valor en caché."""
        self._cache[key] = {
            "value": value,
            "created_at": time.time(),
            "ttl": ttl or self._default_ttl,
        }
        logger.debug(f"💾 Cache SET: {key[:30]}... (total: {len(self._cache)})")

    def clear(self) -> None:
        """Limpia todo el caché."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("💾 Cache limpiado")

    def get_stats(self) -> dict:
        """Estadísticas de uso."""
        total = self._hits + self._misses
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 3) if total > 0 else 0,
        }

    @staticmethod
    def make_key(*args, **kwargs) -> str:
        """Genera key única a partir de argumentos."""
        content = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.md5(content.encode()).hexdigest()
