"""
DuplicateDetector — Detección de duplicados con Strategy Pattern
=================================================================
Eliminar noticias duplicadas es una regla de negocio.

El patrón Strategy permite tener múltiples estrategias de detección
y combinarlas sin modificar el dominio.

Estrategias incluidas:
  - UrlNormalizerStrategy: detecta duplicados por URL normalizada
  - TitleNormalizerStrategy: detecta duplicados por título normalizado

Estrategias futuras (sin modificar este archivo):
  - SemanticSimilarityStrategy: usando embeddings (IA)
  - FuzzyMatchStrategy: fuzzy matching de contenido
  - CompositeStrategy: combinación ponderada de varias estrategias

Uso:
    detector = CompositeDuplicateDetector([
        UrlNormalizerStrategy(),
        TitleNormalizerStrategy(),
    ])
    is_dup = detector.is_duplicate(new_topic, existing_topics)
"""

import hashlib
import re
from abc import ABC, abstractmethod
from typing import Optional

from research.domain.entities.research_topic import ResearchTopic


class DuplicateDetectionStrategy(ABC):
    """
    Strategy: define cómo se detecta un duplicado.

    Cada estrategia:
    1. Calcula un hash del topic
    2. Compara contra hashes existentes
    3. Retorna True si es duplicado
    """

    @abstractmethod
    def compute_hash(self, topic: ResearchTopic) -> Optional[str]:
        """
        Calcula un hash único para el topic según esta estrategia.

        Returns:
            String hash, o None si no se puede calcular
            (ej: URL strategy no puede calcular hash si no hay URL)
        """
        ...

    def is_duplicate(
        self,
        topic: ResearchTopic,
        existing_hashes: set[str],
    ) -> bool:
        """
        Evalúa si el topic es duplicado según esta estrategia.

        Args:
            topic: Topic a evaluar
            existing_hashes: Hashes de topics ya existentes

        Returns:
            True si el hash del topic coincide con algún hash existente
        """
        hash_value = self.compute_hash(topic)
        if hash_value is None:
            return False
        return hash_value in existing_hashes


class UrlNormalizerStrategy(DuplicateDetectionStrategy):
    """
    Estrategia: detecta duplicados por URL normalizada.

    Normaliza URLs eliminando:
      - protocolo (http/https)
      - trailing slashes
      - parámetros de tracking (utm_*, fbclid, etc.)
    """

    def compute_hash(self, topic: ResearchTopic) -> Optional[str]:
        if not topic.url:
            return None

        url = topic.url.strip()

        # Normalizar: minúsculas y sin protocolo
        url = url.lower()
        url = re.sub(r'^https?://', '', url)

        # Eliminar trailing slash
        url = url.rstrip('/')

        # Eliminar parámetros de tracking
        url = re.sub(r'(\?|&)(utm_[^&]+|fbclid=[^&]+|gclid=[^&]+)', '', url)

        # Limpiar parámetros vacíos
        url = re.sub(r'\?$|&$', '', url)

        return hashlib.md5(url.encode()).hexdigest()


class TitleNormalizerStrategy(DuplicateDetectionStrategy):
    """
    Estrategia: detecta duplicados por título normalizado.

    Normaliza títulos eliminando:
      - espacios extras
      - signos de puntuación
      - mayúsculas/minúsculas
      - artículos/preposiciones comunes
    """

    # Palabras a ignorar en la comparación
    _STOP_WORDS: frozenset = frozenset({
        "el", "la", "los", "las", "un", "una", "unos", "unas",
        "de", "del", "en", "con", "para", "por", "y", "e", "o", "u",
        "a", "al", "lo", "le", "que", "es", "se", "su", "the", "a",
        "an", "of", "in", "to", "and", "is", "it", "on", "for",
    })

    def compute_hash(self, topic: ResearchTopic) -> Optional[str]:
        if not topic.title:
            return None

        title = topic.title.lower()

        # Eliminar puntuación
        title = re.sub(r'[^\w\s]', ' ', title)

        # Tokenizar y eliminar stop words
        tokens = [
            w for w in title.split()
            if w and w not in self._STOP_WORDS
        ]

        if not tokens:
            return None

        # Tomar las primeras 5 palabras significativas
        normalized = " ".join(tokens[:5])

        return hashlib.md5(normalized.encode()).hexdigest()


class CompositeDuplicateDetector:
    """
    Combina múltiples estrategias de detección de duplicados.

    Un topic es duplicado si CUALQUIER estrategia lo detecta como tal.
    Esto permite capturar duplicados por URL, por título, y en el
    futuro por similitud semántica, todo en paralelo.

    OCP ✅: para agregar una nueva estrategia, solo crear la clase
    que implemente DuplicateDetectionStrategy y agregarla acá.
    No se modifica ninguna clase existente.
    """

    def __init__(self, strategies: list[DuplicateDetectionStrategy]):
        if not strategies:
            raise ValueError("Se requiere al menos una estrategia de detección")
        self._strategies = strategies

    def compute_hashes(self, topic: ResearchTopic) -> set[str]:
        """
        Calcula TODOS los hashes del topic según las estrategias configuradas.

        Returns:
            Set de hashes (puede estar vacío si ninguna estrategia aplica)
        """
        hashes: set[str] = set()
        for strategy in self._strategies:
            h = strategy.compute_hash(topic)
            if h:
                hashes.add(h)
        return hashes

    def is_duplicate(
        self,
        topic: ResearchTopic,
        existing_hashes: set[str],
    ) -> bool:
        """
        Evalúa si el topic es duplicado según ALGUNA estrategia.

        Args:
            topic: Topic a evaluar
            existing_hashes: Set de hashes de topics existentes

        Returns:
            True si alguna estrategia detecta duplicado
        """
        topic_hashes = self.compute_hashes(topic)
        return bool(topic_hashes & existing_hashes)

    def filter_duplicates(
        self,
        topics: list[ResearchTopic],
        existing_hashes: set[str],
    ) -> tuple[list[ResearchTopic], list[ResearchTopic]]:
        """
        Filtra topics duplicados.

        Args:
            topics: Topics nuevos a evaluar
            existing_hashes: Hashes de topics ya existentes

        Returns:
            Tuple (no_duplicados, duplicados)
        """
        unique: list[ResearchTopic] = []
        duplicates: list[ResearchTopic] = []

        # Acumular hashes de los nuevos topics únicos
        # para detectar duplicados DENTRO del mismo batch
        batch_hashes: set[str] = set(existing_hashes)

        for topic in topics:
            topic_hashes = self.compute_hashes(topic)
            if topic_hashes & batch_hashes:
                duplicates.append(topic)
            else:
                unique.append(topic)
                batch_hashes.update(topic_hashes)

        return unique, duplicates
