from typing import Protocol, Optional, Any


class CachePort(Protocol):
    """
    Puerto: Sistema de caché.
    
    Implementaciones: Memoria, Redis, Archivo.
    """
    
    def get(self, key: str) -> Optional[Any]:
        ...

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ...

    def clear(self) -> None:
        ...

    def get_stats(self) -> dict:
        ...
