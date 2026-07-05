"""
SourceType Enum — Clasificación del tipo de fuente externa.

Determina qué tecnología de fetch y parseo se utiliza para obtener
contenido de un NewsSource.
"""

from __future__ import annotations

from enum import Enum


class SourceType(str, Enum):
    """Tipo de plataforma externa que un NewsSource representa.

    Reemplaza al par ``provider_type`` + ``technology_type`` del diseño
    anterior. Un único enum simplifica el modelo.

    Valores:
        RSS: Fuente con feed RSS/Atom (ej: blogs, sitios de noticias).
        API: Fuente con API REST/GraphQL (ej: Steam News, GitHub).
        SOCIAL_MEDIA: Plataforma de redes sociales (ej: Reddit, Twitter).
        NEWSLETTER: Boletín por correo electrónico.
    """

    RSS = "RSS"
    API = "API"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    NEWSLETTER = "NEWSLETTER"
