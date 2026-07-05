# Migration Strategy — EPIC 5

> **Estrategia completa de migraciones con Alembic para el Bounded Context Ingestion**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-05
> Stack: Alembic 1.13+, SQLAlchemy 2.x, Python 3.12, PostgreSQL (prod), SQLite (testing)
>
> **Este documento especifica la estructura, convenciones y políticas de migraciones.**
> NO implementa código ejecutable. NO modifica Foundation/Domain/Application.

---

## Table of Contents

1. [Directory Structure](#1-directory-structure)
2. [Alembic Configuration Files](#2-alembic-configuration-files)
   - 2.1 [alembic.ini](#21-alembicini)
   - 2.2 [env.py — Discovery Strategy](#22-envpy--discovery-strategy)
   - 2.3 [script.py.mako — Template](#23-scriptpymako--template)
3. [Naming Convention](#3-naming-convention)
4. [Version Strategy](#4-version-strategy)
5. [Initial Schema Migration (0001)](#5-initial-schema-migration-0001)
   - 5.1 [Tablas sin FKs (categories, topics)](#51-tablas-sin-fks-categories-topics)
   - 5.2 [Tablas con FKs simples (news_sources)](#52-tablas-con-fks-simples-news_sources)
   - 5.3 [Tablas con FKs (feeds → news_sources)](#53-tablas-con-fks-feeds--news_sources)
   - 5.4 [Tablas con FKs (raw_articles → feeds)](#54-tablas-con-fks-raw_articles--feeds)
   - 5.5 [Tablas M:N](#55-tablas-mn)
   - 5.6 [Índices Adicionales](#56-índices-adicionales)
   - 5.7 [Orden Completo de la Migración 0001](#57-orden-completo-de-la-migración-0001)
6. [Seed Data](#6-seed-data)
7. [Rollback Policy](#7-rollback-policy)
8. [Testing Strategy](#8-testing-strategy)
9. [Foundation Stability Protection](#9-foundation-stability-protection)
10. [Decisiones Arquitectónicas](#10-decisiones-arquitectónicas)

---

## 1. Directory Structure

### 1.1 Estructura Propuesta

```
project/
├── alembic/                              # → Carpeta de migraciones Alembic
│   ├── versions/                         #    → Versiones de migración
│   │   ├── 0001_initial_schema.py        #       Migración inicial
│   │   ├── 0002_seed_default_data.py     #       Seed data inicial
│   │   └── ...                           #       Migraciones futuras
│   ├── env.py                            #    → Entorno Alembic (descubre modelos)
│   ├── script.py.mako                    #    → Template para auto-generación
│   └── README_ALEMBIC.md                 #    → Instrucciones de uso
│
├── alembic.ini                           # → Configuración Alembic (proyecto raíz)
│
├── src/
│   └── ingestion/
│       └── infrastructure/
│           └── persistence/              # → Capa de persistencia del BC Ingestion
│               ├── __init__.py
│               ├── base.py               #    → DeclarativeBase (IngestionBase)
│               ├── models.py             #    → Modelos ORM (todas las tablas)
│               ├── types.py              #    → TypeDecorators (EntityIdType, etc.)
│               └── engine.py             #    → Factory de engine + sessionmaker
│
└── docs/
    └── architecture/
        └── persistence/
            ├── persistence-design.md     # → Diseño del schema relacional
            ├── orm-mapping-strategy.md   # → Estrategia de mapeo ORM
            ├── migration-strategy.md     # → **Este documento**
            └── configuration-design.md   # → Configuración de BD
```

### 1.2 ¿Por qué `alembic/` en la raíz y no dentro de `src/`?

| Opción | Tradeoff |
|--------|----------|
| **✅ `alembic/` en raíz** | Convención estándar de Alembic. Fácil de encontrar. `alembic.ini` en raíz funciona out-of-the-box. Separación clara entre código de aplicación y tooling de BD. |
| ❌ `src/ingestion/infrastructure/persistence/alembic/` | Alembic espera cierta estructura. Tendríamos que configurar `script_location` relativo. Mezcla código de aplicación con herramientas de migración. |
| ❌ `db/` o `migrations/` en raíz | También válido, pero `alembic/` es la convención que Alembic espera por defecto. Cambiarlo requiere configuración extra. |

**Veredicto**: `alembic/` en raíz. Es lo que Alembic espera, sin configuración extra.

### 1.3 Ubicación de los Modelos ORM

Los modelos ORM viven en `src/ingestion/infrastructure/persistence/models.py`, NO en `alembic/`. Esto sigue Clean Architecture:

```
Domain (entities, VOs)
    ↕  (mapeo en repositorio)
Infrastructure.Persistence (ORM models, TypeDecorators, engine)
    ↕  (Alembic descubre modelos desde aquí)
alembic/env.py (importa modelos, genera migraciones)
```

### 1.4 ¿Symlink o alembic.ini directo?

Usar `alembic.ini` DIRECTAMENTE en la raíz del proyecto, no symlink. Razones:

- Alembic lo espera en el directorio desde donde se ejecuta.
- `alembic.ini` es pequeño y rara vez cambia.
- Symlinks son problemáticos en Windows (y el equipo puede usar Windows).
- Un solo `alembic.ini` para todo el proyecto es suficiente (los BCs comparten la misma BD).

---

## 2. Alembic Configuration Files

### 2.1 `alembic.ini`

```ini
# ── Configuración global de Alembic ───────────────────────
# Este archivo referencia la ubicación de las migraciones
# y de los modelos ORM. NO contiene DATABASE_URL en texto plano.
#
# La DATABASE_URL se pasa vía env.py desde variables de entorno.
# ──────────────────────────────────────────────────────────

[alembic]
# Ruta a la carpeta de versiones de migración
script_location = alembic

# Formato de los nombres de archivo de migración
# Ejemplo: 0001_initial_schema.py, 0002_seed_default_data.py
file_template = %%(rev)s_%%(slug)s

# SQLAlchemy URL — se define en env.py desde DATABASE_URL
# Dejar vacío: lo configuramos programáticamente en env.py
sqlalchemy.url =

# Tiempo de espera para operación (segundos)
# Útil para migraciones lentas en producción
timeout = 30

# Nombre de la rama (para migraciones ramificadas, futuro multi-BC)
trunk_branch.name = ingestion

# Permitir migraciones más allá del último rev_id conocido
# (útil cuando se mergean ramas)
allow_branch_merge = False

# Soporte para migraciones parciales (no usar en producción)
# Se deja en False por seguridad
downgrade_token = None

# Logging
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### 2.2 `env.py` — Discovery Strategy

`env.py` es el punto de entrada de Alembic. Su responsabilidad es:

1. Obtener `DATABASE_URL` del entorno (PRODUCCIÓN) o de `.env` (desarrollo).
2. Importar los modelos ORM para que Alembic los descubra.
3. Configurar `target_metadata` con el metadata de los modelos.
4. Configurar el naming convention.

```python
"""
Alembic environment configuration for AI Shorts System.

Estrategia de descubrimiento de modelos:
────────────────────────────────────────
1. Se importa `IngestionBase` desde ingestion.infrastructure.persistence.base.
2. Alembic usa `IngestionBase.metadata` como `target_metadata`.
3. Al importar base, se importan automáticamente los modelos ORM
   (porque models.py importa base).
4. Alembic compara el metadata actual con el estado de la BD
   para generar migraciones automáticas.

Variables de entorno requeridas:
────────────────────────────────
- DATABASE_URL: URL de conexión (producción/testing/desarrollo).
  Si no está definida, se intenta cargar desde .env.

Soporte multi-entorno:
─────────────────────
- DEVELOPMENT: DATABASE_URL desde .env, logging INFO.
- TESTING: DATABASE_URL desde variable de entorno, logging WARN.
- PRODUCTION: DATABASE_URL desde variable de entorno del sistema,
  logging WARN, dry-run antes de aplicar.
"""

import os
import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Asegurar que src/ está en sys.path ──
# Esto permite importar src.ingestion.infrastructure.persistence
_PROJECT_ROOT = Path(__file__).parent.parent
_SRC_PATH = str(_PROJECT_ROOT / "src")
if _SRC_PATH not in sys.path:
    sys.path.insert(0, _SRC_PATH)

# ── Configuración de logging (desde alembic.ini) ──
if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)

# ── Descubrimiento de modelos ORM ──
# Al importar base.py, se ejecutan sus imports y Alembic descubre
# todos los modelos registrados en IngestionBase.metadata.
from ingestion.infrastructure.persistence.base import IngestionBase

# ── Target metadata para auto-generación ──
target_metadata = IngestionBase.metadata

# ── Naming convention (consistente con orm-mapping-strategy.md §7.2) ──
target_metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# ── Database URL ──
def get_database_url() -> str:
    """Obtiene DATABASE_URL del entorno.

    Orden de resolución:
    1. Variable de entorno DATABASE_URL (producción/CI).
    2. Archivo .env en la raíz del proyecto (desarrollo).
    3. Error si no está disponible.

    Returns:
        Database URL string.

    Raises:
        ValueError: Si DATABASE_URL no está configurada.
    """
    url = os.environ.get("DATABASE_URL")
    if url is not None:
        return url

    # Fallback: intentar cargar desde .env
    dotenv_path = _PROJECT_ROOT / ".env"
    if dotenv_path.exists():
        from dotenv import load_dotenv
        load_dotenv(dotenv_path)
        url = os.environ.get("DATABASE_URL")

    if url is None:
        raise ValueError(
            "DATABASE_URL no está configurada. "
            "Definila en .env o como variable de entorno del sistema."
        )
    return url


# ── Funciones de migración ─────────────────────────────────────

def run_migrations_offline() -> None:
    """Genera SQL para migración offline (sin conexión a BD).

    Útil para:
    - Generar scripts SQL para revisión manual.
    - Entornos donde el migrador no tiene acceso directo a la BD.
    - Auditoría: ver exactamente qué SQL se ejecutará.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,       # Detecta cambios de tipo en columnas
        compare_server_default=True,  # Detecta cambios en defaults
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta migraciones con conexión directa a BD.

    Usa poolclass=NOPOOL para evitar conexiones persistentes
    durante migraciones (cada migración es su propia conexión).
    """
    url = get_database_url()
    cfg = context.config.get_section(context.config.config_ini_section)
    cfg["sqlalchemy.url"] = url

    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Sin pooling para migraciones
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ── Entry point ──
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

#### Estrategia de Discovery: Import por Capas

`env.py` importa `IngestionBase` desde `ingestion.infrastructure.persistence.base`. Al hacerlo, se ejecutan los imports de `base.py`, que a su vez importan `models.py`, registrando todos los modelos ORM en `IngestionBase.metadata`.

```
alembic/env.py
    └── import IngestionBase
            └── from .base import IngestionBase  (DeclarativeBase)
                    └── from . import models      (registra modelos en metadata)
                            ├── class NewsSourceModel(Base)
                            ├── class FeedModel(Base)
                            ├── class RawArticleModel(Base)
                            ├── class CategoryModel(Base)
                            ├── class TopicModel(Base)
                            └── 4 association tables (Table objects)
```

Esto asegura que Alembic vea TODOS los modelos sin imports manuales en `env.py`.

### 2.3 `script.py.mako` — Template

Template para auto-generación de migraciones con `alembic revision --autogenerate`:

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

Auto-generada por Alembic. Revisar ANTES de aplicar.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

**Nota**: El template incluye `Union[str, None]` explícito para compatibilidad con Python 3.12 y SQLAlchemy 2.x.

---

## 3. Naming Convention

### 3.1 Convención de Constraints (Alembic)

Se usa el `naming_convention` estándar de SQLAlchemy 2.x aplicado al `metadata` de `IngestionBase`:

```python
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
```

### 3.2 Ejemplos de Nombres Generados

| Constraint | Tabla | Columna(s) | Nombre generado |
|-----------|-------|------------|-----------------|
| PK | `ingestion_news_sources` | `id` | `pk_ingestion_news_sources` |
| FK | `ingestion_feeds` | `source_id` → `ingestion_news_sources` | `fk_ingestion_feeds_source_id_ingestion_news_sources` |
| UQ | `ingestion_news_sources` | `name` | `uq_ingestion_news_sources_name` |
| CK | `ingestion_raw_articles` | `content_hash` | `ck_ingestion_raw_articles_content_hash` |
| IX | `ingestion_raw_articles` | `feed_id` | `ix_ingestion_raw_articles_feed_id` |

### 3.3 Nombres Manuales (Constraints Explícitas)

Para constraints con nombres semánticos (check constraints, unique compuestas), se usa `__table_args__`:

```python
__table_args__ = (
    UniqueConstraint(
        "source_id", "url",
        name="uq_feed_source_url"  # nombre semántico corto
    ),
    CheckConstraint(
        "LENGTH(content_hash) = 64",
        name="ck_raw_article_hash_length"
    ),
)
```

**¿Por qué nombres manuales para algunas?** Porque el nombre auto-generado puede ser muy largo (ej: `uq_ingestion_raw_articles_feed_id_content_hash` vs `uq_raw_article_feed_hash`). Para mensajes de error y debugging, nombres cortos y semánticos son mejores.

### 3.4 Mapeo Completo Naming Convention → Tablas

| Tabla | PK | FKs | UQs | CKs | Índices |
|-------|----|-----|-----|-----|---------|
| `ingestion_news_sources` | `pk_ingestion_news_sources` | — | `uq_ingestion_news_sources_name` | — | `ix_ingestion_news_sources_is_active` |
| `ingestion_feeds` | `pk_ingestion_feeds` | `fk_ingestion_feeds_source_id_ingestion_news_sources` | `uq_feed_source_url` (manual) | `ck_ingestion_feeds_interval_minutes` (si no nulo) | `ix_ingestion_feeds_source_id_is_active` |
| `ingestion_raw_articles` | `pk_ingestion_raw_articles` | `fk_ingestion_raw_articles_feed_id_ingestion_feeds` | `uq_raw_article_feed_external` (manual), `uq_raw_article_feed_hash` (manual) | `ck_raw_article_hash_length` (manual) | `ix_ingestion_raw_articles_feed_id_fetched_at`, `ix_ingestion_raw_articles_feed_id_url` |
| `ingestion_categories` | `pk_ingestion_categories` | `fk_ingestion_categories_parent_id_ingestion_categories` | `uq_ingestion_categories_slug` | `ck_category_no_self_parent` (manual) | `ix_ingestion_categories_parent_id`, `ix_ingestion_categories_is_active` |
| `ingestion_topics` | `pk_ingestion_topics` | — | `uq_ingestion_topics_name` | — | `ix_ingestion_topics_is_active` |
| `ingestion_news_source_categories` | `pk_ingestion_news_source_categories` | `fk_..._source_id_ingestion_news_sources`, `fk_..._category_id_ingestion_categories` | (PK compuesta) | — | `ix_ingestion_news_source_categories_category_id` |
| `ingestion_news_source_topics` | `pk_ingestion_news_source_topics` | `fk_..._source_id_ingestion_news_sources`, `fk_..._topic_id_ingestion_topics` | (PK compuesta) | — | `ix_ingestion_news_source_topics_topic_id` |
| `ingestion_feed_categories` | `pk_ingestion_feed_categories` | `fk_..._feed_id_ingestion_feeds`, `fk_..._category_id_ingestion_categories` | (PK compuesta) | — | `ix_ingestion_feed_categories_category_id` |
| `ingestion_feed_topics` | `pk_ingestion_feed_topics` | `fk_..._feed_id_ingestion_feeds`, `fk_..._topic_id_ingestion_topics` | (PK compuesta) | — | `ix_ingestion_feed_topics_topic_id` |

---

## 4. Version Strategy

### 4.1 Sequential vs Timestamp

| Criterio | Sequential (0001, 0002...) | Timestamp (20260705_1200...) |
|----------|---------------------------|------------------------------|
| **Legibilidad humana** | ✅ Excelente — orden claro | ❌ Dificultad — números largos |
| **Conflictos en merge** | ❌ Posibles si dos ramas crean `0002` | ✅ Imposibles (timestamps únicos) |
| **Orden natural** | ✅ 0001 < 0002 < 0003 | ✅ 2026... < 2026... |
| **Historial git** | ❌ Rebase cambia números | ✅ Timestamp es estable |
| **Proyectos multi-equipo** | ❌ Conflictos frecuentes | ✅ Ideal |

**Decisión**: **Sequential (0001, 0002...)**.

Justificación:
- **Equipo único**: No hay múltiples equipos generando migraciones en paralelo que causen conflictos.
- **Legibilidad**: `0001_initial_schema.py` es inmediatamente entendible. `20260705_120045_initial_schema.py` no.
- **Simplicidad**: No requiere coordinación de timestamps.
- **Si hay conflicto**: Es trivial de resolver (renumerar la migración conflictiva).

### 4.2 Estrategia: Mega-migración Inicial + Migraciones Modulares

**FASE 1 (ahora)**: Una mega-migración inicial (`0001_initial_schema.py`) que crea las 9 tablas completas con todos los índices y constraints. Esto es correcto porque:

- No hay datos en producción que migrar (BD vacía).
- Es más rápido que 9 migraciones separadas para la creación inicial.
- El downgrade es trivial: `DROP TABLE` en orden inverso.

**FASE 2 (futuro)**: Migraciones modulares pequeñas para cada cambio:

| # | Migración | Contenido |
|---|-----------|-----------|
| `0001` | Initial Schema | Creación de 9 tablas + índices + constraints |
| `0002` | Seed Default Data | Insert de categorías, idiomas por defecto |
| `0003` | Add Column | Ej: `ingestion_feeds.last_fetched_at` |
| `0004` | New Index | Ej: `ix_raw_articles_language` |
| `0005` | New Table | Ej: `ingestion_source_metrics` |

### 4.3 Formato de Archivo

```
{rev}_{slug}.py
```

Donde:
- `rev`: Número secuencial de 4 dígitos (0001, 0002, 0010...).
- `slug`: Descripción corta en snake_case.

Ejemplos:
- `0001_initial_schema.py`
- `0002_seed_default_data.py`
- `0003_add_last_fetched_at_to_feeds.py`

### 4.4 Ramas (Branch Labels)

Alembic soporta branch labels para migraciones ramificadas. En este proyecto:

```python
# En cada migración:
branch_labels = None  # Sin ramas por ahora

# En el futuro, si otro BC necesita su propia rama:
branch_labels = ("ingestion",)  # Rama del BC Ingestion
```

Por ahora, `branch_labels = None` en todas las migraciones. Si en el futuro Research o Script necesitan sus propias tablas, pueden crear su propia rama de migraciones.

### 4.5 Dependencias (`depends_on`)

No usar `depends_on` en la migración inicial. Para migraciones futuras:

```python
# Si la migración 0003 depende de que 0002 esté aplicada:
down_revision = "0002_xxxx"
depends_on = None  # La cadena de revisiones ya define el orden
```

`depends_on` solo es necesario cuando hay ramas. En una cadena lineal, `down_revision` es suficiente.

---

## 5. Initial Schema Migration (0001)

### 5.1 Orden de Creación

El orden sigue las dependencias de Foreign Keys:

```
1. ingestion_categories          # Sin FKs
2. ingestion_topics              # Sin FKs

3. ingestion_news_sources        # Sin FKs a otras tablas (solo metadatos)

4. ingestion_feeds               # FK → news_sources

5. ingestion_raw_articles        # FK → feeds

6. ingestion_news_source_categories  # FK → news_sources, categories
7. ingestion_news_source_topics      # FK → news_sources, topics

8. ingestion_feed_categories     # FK → feeds, categories
9. ingestion_feed_topics         # FK → feeds, topics
```

El downgrade hace el orden inverso: DROP de M:N primero, luego raw_articles, feeds, news_sources, categories, topics.

### 5.2 Especificación de cada CREATE TABLE

#### 5.2.1 `ingestion_categories`

```python
"""
CREATE TABLE ingestion_categories (
    id              UUID NOT NULL,
    name            VARCHAR(100) NOT NULL,
    slug            VARCHAR(150) NOT NULL,
    description     TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    parent_id       UUID,
    version         INTEGER NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_ingestion_categories PRIMARY KEY (id),
    CONSTRAINT fk_ingestion_categories_parent_id_ingestion_categories
        FOREIGN KEY (parent_id) REFERENCES ingestion_categories(id)
        ON DELETE SET NULL,
    CONSTRAINT uq_ingestion_categories_slug UNIQUE (slug),
    CONSTRAINT ck_category_no_self_parent CHECK (id != parent_id)
);
"""
```

- **parent_id**: Self-referencing FK, nullable, ON DELETE SET NULL.
- **slug**: UNIQUE global (I-18).
- **CHECK**: Self-parent prevention (I-19).
- **version**: Optimistic locking.

#### 5.2.2 `ingestion_topics`

```python
"""
CREATE TABLE ingestion_topics (
    id              UUID NOT NULL,
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    version         INTEGER NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_ingestion_topics PRIMARY KEY (id),
    CONSTRAINT uq_ingestion_topics_name UNIQUE (name)
);
"""
```

- Entidad más simple: sin FKs, sin jerarquía.
- **name**: UNIQUE (I-23).

#### 5.2.3 `ingestion_news_sources`

```python
"""
CREATE TABLE ingestion_news_sources (
    id              UUID NOT NULL,
    name            VARCHAR(255) NOT NULL,
    source_type     VARCHAR(20) NOT NULL,
    source_url      VARCHAR(2048) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    version         INTEGER NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_ingestion_news_sources PRIMARY KEY (id),
    CONSTRAINT uq_ingestion_news_sources_name UNIQUE (name)
);
"""
```

- **source_type**: VARCHAR(20), NO como ENUM nativo (ver Decisión E-02 en persistence-design.md).
- **source_url**: VARCHAR(2048) — límite RFC 3986.
- **name**: UNIQUE (I-02).

#### 5.2.4 `ingestion_feeds`

```python
"""
CREATE TABLE ingestion_feeds (
    id                  UUID NOT NULL,
    source_id           UUID NOT NULL,
    url                 VARCHAR(2048) NOT NULL,
    label               VARCHAR(500) NOT NULL,
    language            VARCHAR(2) NOT NULL,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,

    -- SyncPolicy columns (composite mapping)
    sync_mode           VARCHAR(20) NOT NULL DEFAULT 'PULL',
    interval_minutes    INTEGER,                -- nullable para PUSH/STREAM/MANUAL
    max_retries         INTEGER NOT NULL DEFAULT 3,
    backoff_multiplier  FLOAT NOT NULL DEFAULT 2.0,
    max_backoff_minutes INTEGER NOT NULL DEFAULT 60,
    timeout_seconds     INTEGER NOT NULL DEFAULT 30,
    max_items_per_run   INTEGER NOT NULL DEFAULT 100,

    -- Estado de ejecución
    retry_count         INTEGER NOT NULL DEFAULT 0,

    -- Optimistic Locking
    version             INTEGER NOT NULL DEFAULT 1,

    -- Timestamps
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_ingestion_feeds PRIMARY KEY (id),
    CONSTRAINT fk_ingestion_feeds_source_id_ingestion_news_sources
        FOREIGN KEY (source_id) REFERENCES ingestion_news_sources(id)
        ON DELETE CASCADE,
    CONSTRAINT uq_feed_source_url UNIQUE (source_id, url),

    -- Check constraints de SyncPolicy
    CONSTRAINT ck_feed_interval_positive CHECK (
        interval_minutes IS NULL OR interval_minutes > 0
    ),
    CONSTRAINT ck_feed_retries_positive CHECK (max_retries > 0),
    CONSTRAINT ck_feed_timeout_positive CHECK (timeout_seconds > 0),
    CONSTRAINT ck_feed_backoff_positive CHECK (backoff_multiplier > 0),
    CONSTRAINT ck_feed_retry_count_non_negative CHECK (retry_count >= 0)
);
"""
```

- **source_id**: FK → ingestion_news_sources con CASCADE.
- **url**: UNIQUE compuesta con source_id (I-06).
- **sync_mode**: VARCHAR(20), no ENUM nativo.
- **interval_minutes**: NULLABLE — solo obligatorio para PULL.
- **Check constraints**: Validan dominio de SyncPolicy a nivel BD.
- **Optimistic locking**: vía `version` column.

#### 5.2.5 `ingestion_raw_articles`

```python
"""
CREATE TABLE ingestion_raw_articles (
    id              UUID NOT NULL,
    feed_id         UUID NOT NULL,
    external_id     VARCHAR(512) NOT NULL,
    content_hash    VARCHAR(64) NOT NULL,
    title           VARCHAR(500) NOT NULL,
    url             VARCHAR(2048) NOT NULL,
    author          VARCHAR(255),
    language        VARCHAR(2),
    published_at    TIMESTAMPTZ,
    fetched_at      TIMESTAMPTZ NOT NULL,
    content_preview TEXT,
    metadata        JSONB NOT NULL DEFAULT '{}',

    -- Timestamp único (inmutable)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_ingestion_raw_articles PRIMARY KEY (id),
    CONSTRAINT fk_ingestion_raw_articles_feed_id_ingestion_feeds
        FOREIGN KEY (feed_id) REFERENCES ingestion_feeds(id)
        ON DELETE RESTRICT,
    CONSTRAINT uq_raw_article_feed_external UNIQUE (feed_id, external_id),
    CONSTRAINT uq_raw_article_feed_hash UNIQUE (feed_id, content_hash),
    CONSTRAINT ck_raw_article_hash_length CHECK (LENGTH(content_hash) = 64)
);
"""
```

- **Sin version**: RawArticle es inmutable (I-11).
- **Sin updated_at**: RawArticle nunca se actualiza.
- **FK con RESTRICT**: No se borra un Feed con artículos.
- **Dos UNIQUE compuestas**: (feed_id, external_id) y (feed_id, content_hash).
- **CHECK**: content_hash SHA-256 = 64 caracteres hex (I-17).
- **metadata**: JSONB en PostgreSQL, TEXT en SQLite.
- **language**: NULLABLE — se detecta después.

#### 5.2.6 `ingestion_news_source_categories` (M:N)

```python
"""
CREATE TABLE ingestion_news_source_categories (
    source_id       UUID NOT NULL,
    category_id     UUID NOT NULL,

    CONSTRAINT pk_ingestion_news_source_categories
        PRIMARY KEY (source_id, category_id),
    CONSTRAINT fk_ingestion_news_source_categories_source_id_ingestion_news_sources
        FOREIGN KEY (source_id) REFERENCES ingestion_news_sources(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ingestion_news_source_categories_category_id_ingestion_categories
        FOREIGN KEY (category_id) REFERENCES ingestion_categories(id)
        ON DELETE CASCADE
);
"""
```

#### 5.2.7 `ingestion_news_source_topics` (M:N)

```python
"""
CREATE TABLE ingestion_news_source_topics (
    source_id       UUID NOT NULL,
    topic_id        UUID NOT NULL,

    CONSTRAINT pk_ingestion_news_source_topics
        PRIMARY KEY (source_id, topic_id),
    CONSTRAINT fk_ingestion_news_source_topics_source_id_ingestion_news_sources
        FOREIGN KEY (source_id) REFERENCES ingestion_news_sources(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ingestion_news_source_topics_topic_id_ingestion_topics
        FOREIGN KEY (topic_id) REFERENCES ingestion_topics(id)
        ON DELETE CASCADE
);
"""
```

#### 5.2.8 `ingestion_feed_categories` (M:N)

```python
"""
CREATE TABLE ingestion_feed_categories (
    feed_id         UUID NOT NULL,
    category_id     UUID NOT NULL,

    CONSTRAINT pk_ingestion_feed_categories
        PRIMARY KEY (feed_id, category_id),
    CONSTRAINT fk_ingestion_feed_categories_feed_id_ingestion_feeds
        FOREIGN KEY (feed_id) REFERENCES ingestion_feeds(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ingestion_feed_categories_category_id_ingestion_categories
        FOREIGN KEY (category_id) REFERENCES ingestion_categories(id)
        ON DELETE CASCADE
);
"""
```

#### 5.2.9 `ingestion_feed_topics` (M:N)

```python
"""
CREATE TABLE ingestion_feed_topics (
    feed_id         UUID NOT NULL,
    topic_id        UUID NOT NULL,

    CONSTRAINT pk_ingestion_feed_topics
        PRIMARY KEY (feed_id, topic_id),
    CONSTRAINT fk_ingestion_feed_topics_feed_id_ingestion_feeds
        FOREIGN KEY (feed_id) REFERENCES ingestion_feeds(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ingestion_feed_topics_topic_id_ingestion_topics
        FOREIGN KEY (topic_id) REFERENCES ingestion_topics(id)
        ON DELETE CASCADE
);
"""
```

### 5.3 Índices Adicionales

Después de crear todas las tablas, se crean los índices adicionales (ver persistence-design.md §1.8):

```sql
-- Paginación y deduplicación en RawArticles
CREATE INDEX ix_raw_articles_feed_fetched
    ON ingestion_raw_articles (feed_id, fetched_at DESC);
CREATE INDEX ix_raw_articles_feed_url
    ON ingestion_raw_articles (feed_id, url);

-- Consultas por source en Feeds
CREATE INDEX ix_feeds_source_active
    ON ingestion_feeds (source_id, is_active);

-- Sources activos
CREATE INDEX ix_news_sources_active
    ON ingestion_news_sources (is_active);

-- Jerarquía de categorías
CREATE INDEX ix_categories_parent
    ON ingestion_categories (parent_id);
CREATE INDEX ix_categories_active
    ON ingestion_categories (is_active);

-- Topics activos
CREATE INDEX ix_topics_active
    ON ingestion_topics (is_active);

-- Queries inversas en M:N
CREATE INDEX ix_nsc_category
    ON ingestion_news_source_categories (category_id);
CREATE INDEX ix_nst_topic
    ON ingestion_news_source_topics (topic_id);
CREATE INDEX ix_fc_category
    ON ingestion_feed_categories (category_id);
CREATE INDEX ix_ft_topic
    ON ingestion_feed_topics (topic_id);
```

### 5.4 Downgrade de 0001

```sql
-- Orden inverso: M:N primero, luego tablas con FKs, luego sin FKs
DROP TABLE IF EXISTS ingestion_feed_topics;
DROP TABLE IF EXISTS ingestion_feed_categories;
DROP TABLE IF EXISTS ingestion_news_source_topics;
DROP TABLE IF EXISTS ingestion_news_source_categories;
DROP TABLE IF EXISTS ingestion_raw_articles;
DROP TABLE IF EXISTS ingestion_feeds;
DROP TABLE IF EXISTS ingestion_news_sources;
DROP TABLE IF EXISTS ingestion_topics;
DROP TABLE IF EXISTS ingestion_categories;
```

---

## 6. Seed Data

### 6.1 Estrategia: Migración Separada (0002)

Los datos iniciales se cargan en una migración **separada** (`0002_seed_default_data.py`), no en la migración inicial. Razones:

1. **Separación de concerns**: Schema ≠ Data.
2. **Rollback granular**: Se puede revertir datos sin revertir schema.
3. **Idempotencia**: La migración de datos usa `INSERT ... ON CONFLICT DO NOTHING` para ser ejecutable múltiples veces.
4. **Testing**: Los seeds se pueden cargar independientemente en tests.

### 6.2 Datos Iniciales

#### Categorías por Defecto

```sql
INSERT INTO ingestion_categories (id, name, slug, description, is_active)
VALUES
    ('a0000000-0000-0000-0000-000000000001', 'Technology',      'technology',      'Technology and software news',       TRUE),
    ('a0000000-0000-0000-0000-000000000002', 'Science',         'science',         'Scientific discoveries and research', TRUE),
    ('a0000000-0000-0000-0000-000000000003', 'Politics',        'politics',        'Political news and analysis',         TRUE),
    ('a0000000-0000-0000-0000-000000000004', 'Business',        'business',        'Business and finance news',           TRUE),
    ('a0000000-0000-0000-0000-000000000005', 'Entertainment',   'entertainment',   'Entertainment and pop culture',       TRUE),
    ('a0000000-0000-0000-0000-000000000006', 'Sports',          'sports',          'Sports news and updates',             TRUE),
    ('a0000000-0000-0000-0000-000000000007', 'Health',          'health',          'Health and medical news',             TRUE),
    ('a0000000-0000-0000-0000-000000000008', 'Education',       'education',       'Education and learning',              TRUE),
    ('a0000000-0000-0000-0000-000000000009', 'World',           'world',           'World news and international affairs', TRUE)
ON CONFLICT (slug) DO NOTHING;
```

**IDs fijos**: Se usan UUIDs predecibles (no aleatorios) para que sean referenciables en otras migraciones y tests. El formato `a0000000-...` es deliberado para distinguirlos de IDs generados por el sistema.

#### Idiomas por Defecto

Los idiomas no son una tabla separada (son Value Objects en el dominio), pero la migración de seed puede insertar datos de referencia si se decide crear una tabla `ingestion_languages` en el futuro.

Por ahora, los idiomas se definen como constantes en el código del dominio:

```python
# src/ingestion/domain/value_objects/language.py
SUPPORTED_LANGUAGES = frozenset({
    "en",  # English
    "es",  # Spanish
    "fr",  # French
    "de",  # German
    "pt",  # Portuguese
    "it",  # Italian
})
```

No se requiere seed para idiomas porque no hay tabla de idiomas — es una validación en el VO.

### 6.3 Data Fixtures para Tests

Los fixtures de test NO se cargan vía Alembic. Se cargan usando:

1. **Pytest fixtures**: Funciones `@pytest.fixture` que insertan datos en la BD de test.
2. **Archivos JSON/YAML**: Si hay muchos datos (ej: 50 categorías de prueba), se cargan desde archivos en `tests/fixtures/`.
3. **Factories**: Usar `factory_boy` o clases factory para generar datos de prueba.

```python
# tests/fixtures/ingestion.py
@pytest.fixture
def default_categories(db_session):
    """Carga las categorías por defecto en la BD de test."""
    from ingestion.infrastructure.persistence.models import CategoryModel
    categories = [
        CategoryModel(id=CAT_ID_TECH, name="Technology", slug="technology"),
        CategoryModel(id=CAT_ID_SCIENCE, name="Science", slug="science"),
        # ...
    ]
    for cat in categories:
        db_session.add(cat)
    db_session.commit()
    return categories
```

**Estructura de fixtures**:

```
tests/
├── conftest.py              # Configuración global (engine, session)
├── fixtures/
│   ├── __init__.py
│   ├── ingestion.py         # Fixtures del BC Ingestion
│   ├── categories.py        # Categorías de prueba
│   ├── sources.py           # NewsSources de prueba
│   └── articles.py          # RawArticles de prueba
└── ingestion/
    └── infrastructure/
        └── test_repositories.py  # Tests de repositorios
```

---

## 7. Rollback Policy

### 7.1 Regla Fundamental

> **TODAS las migraciones DEBEN tener `downgrade()`.**

No hay excepciones. Incluso las migraciones de datos (seeds) deben tener downgrade.

### 7.2 Tipos de Rollback

| Tipo | Downgrade | Ejemplo |
|------|-----------|---------|
| **Schema Change** | `DROP TABLE`, `ALTER TABLE ... DROP COLUMN` | Crear/Eliminar tabla, agregar/quitar columna |
| **Index Change** | `DROP INDEX` | Agregar/quitar índice |
| **Data Migration** | `DELETE` inverso o `UPDATE` inverso | Insertar seeds, poblar columna nueva |
| **Renaming** | Renombrar de vuelta | Renombrar columna/tabla |

### 7.3 Data Migrations (One-way)

Algunas migraciones de datos son inherentemente one-way (ej: poblar una columna nueva desde un API externo). Para estos casos:

```python
def upgrade():
    """Puebla columna 'language' desde API de detección de idioma."""
    connection = op.get_bind()
    rows = connection.execute(
        sa.text("SELECT id, content_preview FROM ingestion_raw_articles WHERE language IS NULL")
    ).fetchall()

    for row in rows:
        detected = detect_language(row.content_preview)  # API externa
        connection.execute(
            sa.text("UPDATE ingestion_raw_articles SET language = :lang WHERE id = :id"),
            {"lang": detected, "id": row.id},
        )

def downgrade():
    """Revierte: limpia los valores detectados automáticamente."""
    op.execute(
        "UPDATE ingestion_raw_articles SET language = NULL WHERE language IS NOT NULL"
    )
```

**Regla**: Incluso las data migrations one-way tienen downgrade — aunque sea un "reset to NULL" o "restore from backup". Si la migración es realmente irreversible (ej: datos obtenidos de API externa que ya no existe), se documenta explícitamente en el código y en el docstring.

### 7.4 Estrategia de Rollback en Producción

```
┌─────────────────────────────────────────────────────────────────┐
│                   PROCEDIMIENTO DE ROLLBACK                      │
│                                                                  │
│  1. DETECTAR EL PROBLEMA                                         │
│     ├── Monitoreo: alertas de error posteriores a migración     │
│     ├── Tests: rollback automático si tests de humo fallan      │
│     └── Humano: revisión manual antes de aplicar                │
│                                                                  │
│  2. DECIDIR: ROLLBACK vs HOTFIX                                  │
│     ├── ¿El error bloquea operaciones? → ROLLBACK               │
│     ├── ¿El error es cosmético? → HOTFIX (nueva migración)      │
│     └── ¿El error afecta datos? → ROLLBACK obligatorio          │
│                                                                  │
│  3. EJECUTAR ROLLBACK                                            │
│     ├── alembic downgrade -1  (revertir última migración)       │
│     ├── alembic downgrade -2  (revertir dos migraciones)        │
│     └── alembic downgrade <target>  (revertir hasta versión)    │
│                                                                  │
│  4. VERIFICAR                                                    │
│     ├── Tests de integración                                     │
│     ├── Verificar datos                                          │
│     └── Notificar al equipo                                      │
│                                                                  │
│  5. CORREGIR Y AVANZAR                                          │
│     ├── Crear nueva migración con la corrección                 │
│     ├── NO reabrir la migración fallida                         │
│     └── Aplicar nueva migración                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Principio**: **Nunca se modifica una migración ya aplicada en producción.** Siempre se avanza hacia adelante con una nueva migración que corrige el error.

### 7.5 Comandos de Rollback

```bash
# Revertir la última migración
alembic downgrade -1

# Revertir a una versión específica
alembic downgrade 0001

# Revertir todo (BD vacía)
alembic downgrade base

# Ver historial de migraciones aplicadas
alembic history

# Ver migración actual
alembic current
```

### 7.6 Protección contra Rollback en Producción

En producción, se recomienda:

1. **Siempre hacer backup** de la BD antes de aplicar migraciones.
2. **Ejecutar `alembic upgrade --sql`** primero para generar el SQL y revisarlo.
3. **Usar transacciones**: Por defecto, Alembic envuelve cada migración en una transacción. Si una migración falla, todo se revierte.
4. **Rollback automático en CI/CD**: Si los tests de humo fallan después de una migración, el pipeline revierte automáticamente.

---

## 8. Testing Strategy

### 8.1 ¿Las migraciones se aplican en tests?

**SÍ**. Los tests de integración de repositorios SQLAlchemy aplican las migraciones de Alembic sobre una base de datos SQLite en memoria.

### 8.2 Estrategia: migrate + truncate (NO recreate)

| Estrategia | Descripción | Velocidad | Aislamiento | Veredicto |
|-----------|-------------|-----------|-------------|-----------|
| **✅ migrate + truncate** | Aplicar migraciones UNA VEZ por sesión de test. Truncar tablas entre tests. | ✅ Rápido | ✅ Bueno | **Elegida** |
| ❌ recreate (create_all + drop_all) | Crear y destruir schema en cada test. | ❌ Lento | ✅ Excelente | Descartada |
| ❌ migrate + rollback | Aplicar y revertir migraciones en cada test. | ❌ Lentísimo | ❌ Malo (depende del orden de migraciones) | Descartada |

### 8.3 Implementación en conftest.py

```python
"""
Configuración de pytest para tests de persistencia.

Estrategia:
1. Crear engine SQLite en memoria (una vez por sesión).
2. Aplicar migraciones de Alembic (una vez por sesión).
3. Para cada test: iniciar transacción + crear tablas temporales.
4. Al finalizar cada test: rollback de la transacción (las tablas temporales desaparecen).
5. Close session: cerrar sesión, no dropear tablas.

Esto es ~10x más rápido que recreate por test.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from alembic.config import Config
from alembic.command import upgrade as alembic_upgrade

from ingestion.infrastructure.persistence.base import IngestionBase


@pytest.fixture(scope="session")
def engine():
    """Crea engine SQLite en memoria (una vez por sesión de test).

    SQLite en memoria es ~10x más rápido que archivo temporal.
    """
    return create_engine(
        "sqlite:///:memory:",
        echo=False,  # Silencioso en tests
    )


@pytest.fixture(scope="session")
def alembic_config(engine):
    """Configura Alembic para usar el engine de test.

    Crea una config de Alembic programática (sin archivo .ini).
    Apunta a la carpeta de migraciones del proyecto.
    """
    config = Config()
    config.set_main_option("script_location", "alembic")
    config.set_main_option("sqlalchemy.url", str(engine.url))
    return config


@pytest.fixture(scope="session", autouse=True)
def apply_migrations(engine, alembic_config):
    """Aplica TODAS las migraciones de Alembic UNA VEZ por sesión.

    Esto asegura que el schema de test está siempre sincronizado
    con las migraciones. Si una migración nueva se agrega, los tests
    la aplican automáticamente.
    """
    alembic_upgrade(alembic_config, "head")


@pytest.fixture
def db_session(engine):
    """Provee una sesión de BD con aislamiento por test.

    Usa transacciones anidadas (savepoints) para que cada test
    vea un estado limpio sin necesidad de truncar.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    # Cada test opera dentro de una transacción que se revierte al final
    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sessionmaker_fixture(engine, db_session):
    """Provee un sessionmaker para tests que usan UoW.

    El UoW crea sus propias sesiones, pero queremos que todas
    estén dentro de la misma transacción de test para que el
    rollback al final limpie todo.
    """
    def _get_session():
        return db_session

    return sessionmaker(bind=engine)
```

### 8.4 Fixture para Probar Migraciones Específicas

Para tests que verifican que una migración específica funciona:

```python
@pytest.fixture(scope="module")
def engine_empty():
    """Engine SIN migraciones aplicadas."""
    return create_engine("sqlite:///:memory:", echo=False)


def test_migration_0001_creates_tables(engine_empty, alembic_config):
    """Verifica que la migración 0001 crea las 9 tablas esperadas."""
    from alembic.command import upgrade

    # Aplicar solo la migración 0001
    alembic_config.set_main_option("sqlalchemy.url", str(engine_empty.url))
    upgrade(alembic_config, "0001")

    # Verificar que las tablas existen
    inspector = inspect(engine_empty)
    tables = inspector.get_table_names()
    expected_tables = {
        "ingestion_categories",
        "ingestion_topics",
        "ingestion_news_sources",
        "ingestion_feeds",
        "ingestion_raw_articles",
        "ingestion_news_source_categories",
        "ingestion_news_source_topics",
        "ingestion_feed_categories",
        "ingestion_feed_topics",
    }
    assert expected_tables.issubset(set(tables))


def test_migration_0001_downgrade(engine_empty, alembic_config):
    """Verifica que el downgrade de 0001 elimina todas las tablas."""
    from alembic.command import upgrade, downgrade

    alembic_config.set_main_option("sqlalchemy.url", str(engine_empty.url))

    # Upgrade
    upgrade(alembic_config, "0001")
    inspector = inspect(engine_empty)
    assert len(inspector.get_table_names()) == 9

    # Downgrade
    downgrade(alembic_config, "base")
    inspector = inspect(engine_empty)
    assert len(inspector.get_table_names()) == 0
```

### 8.5 Fixture para Data Seeds

```python
@pytest.fixture
def with_seed_data(db_session):
    """Carga los seeds de 0002 sobre la BD de test."""
    # Cargar categorías por defecto
    categories = [
        CategoryModel(id=UUID("a0000000-...-000000000001"), name="Technology", slug="technology"),
        # ...
    ]
    for cat in categories:
        db_session.add(cat)
    db_session.commit()
    return categories
```

### 8.6 Integración con Tests Existentes

Los tests existentes usan repositorios in-memory. Los nuevos tests de integración SQLAlchemy usarán esta estrategia de migraciones. Ambos coexisten:

```
tests/
├── conftest.py                           # Configuración global
├── ingestion/
│   ├── domain/                           # Tests de dominio (sin BD)
│   ├── application/                      # Tests de aplicación (in-memory)
│   └── infrastructure/
│       ├── conftest.py                   # Fixtures de BD (engine, session)
│       ├── test_migrations.py            # Tests de migraciones
│       └── test_repositories_sqlalchemy.py  # Tests de repositorios SQLAlchemy
└── foundation/                           # Tests de foundation (sin BD)
```

---

## 9. Foundation Stability Protection

### 9.1 ¿Cómo se asegura que Foundation no se modifique?

1. **`env.py` importa modelos de Ingestion, NO de Foundation.**
   - `target_metadata = IngestionBase.metadata`
   - No incluye `FoundationBase.metadata` ni ningún metadata de Foundation.
   - Foundation no tiene tablas en la BD (es código, no datos).

2. **Alembic `--autogenerate` solo compara con `target_metadata`.**
   - Si alguien modifica Foundation, `--autogenerate` no lo detecta porque Foundation no está en `target_metadata`.
   - Las migraciones generadas solo afectan tablas del BC Ingestion.

3. **Los modelos ORM de Ingestion no heredan de Foundation.**
   - Heredan de `IngestionBase` (DeclarativeBase propia del BC).
   - No hay `FoundationBase` con tablas.

4. **Foundation Stability Policy** (ver `FOUNDATION_STABILITY_POLICY.md`):
   - Foundation v1.0 es FROZEN.
   - Cualquier cambio requiere ADR + 5 criterios + aprobación del ARB.
   - Alembic no puede modificar Foundation porque Foundation no tiene representación en BD.

### 9.2 Protección en CI/CD

```yaml
# CI step: verificar que Foundation no fue modificado
- name: Check Foundation integrity
  run: |
    # Verificar que los archivos de Foundation no cambiaron
    git diff --name-only HEAD~1 | grep -q "src/foundation/" && {
      echo "❌ Foundation modificado! Esto requiere ADR y aprobación del ARB."
      exit 1
    } || echo "✅ Foundation intacto"
```

---

## 10. Decisiones Arquitectónicas

### Decisión M-01: Sequential versioning (no timestamps)

| Opción | Tradeoff |
|--------|----------|
| **✅ Sequential (0001, 0002...)** | Legible, orden claro. Conflictos posibles pero en equipo único son triviales de resolver. |
| ❌ Timestamp-based | Único pero ilegible. Para equipos distribuidos grandes. No es el caso. |

### Decisión M-02: Mega-migración inicial (no modular)

| Opción | Tradeoff |
|--------|----------|
| **✅ Una migración 0001 con 9 tablas** | Rápido, simple, downgrade trivial. BD vacía → no hay datos que preservar. |
| ❌ 9 migraciones separadas | 9 archivos, 9 revisiones, 9 downgrades. Sin beneficio real para la creación inicial. |

### Decisión M-03: Migración de seeds separada (0002)

| Opción | Tradeoff |
|--------|----------|
| **✅ Seed en migración separada** | Rollback granular. Separación schema vs data. Se puede omitir en tests si no se necesita. |
| ❌ Seeds en 0001 | Mezcla schema + data. No se puede revertir datos sin revertir schema. |
| ❌ Seeds en script externo | Fuera del control de versiones de Alembic. No hay registro de qué seeds se aplicaron. |

### Decisión M-04: migrate + truncate en tests (no recreate)

| Opción | Tradeoff |
|--------|----------|
| **✅ Migrar una vez, truncar entre tests** | Rápido (~100ms por sesión de test). Aislamiento aceptable. |
| ❌ create_all + drop_all por test | Lento (~500ms por test). Garantiza schema limpio pero el costo es alto. |
| ❌ migrate + rollback por test | Lentísimo. Cada test aplica y revierte N migraciones. |

### Decisión M-05: Branch labels desactivados por ahora

| Opción | Tradeoff |
|--------|----------|
| **✅ `branch_labels = None`** | Simple. Un solo flujo lineal de migraciones. Suficiente para un solo BC. |
| ❌ `branch_labels = ("ingestion",)` | Prepara para multi-BC pero agrega complejidad innecesaria hoy. Se puede agregar cuando Research o Script necesiten sus propias tablas. |

---

*Documento diseñado durante EPIC 5 del proyecto AI Shorts System.*
*Basado en: persistence-design.md v1.0, orm-mapping-strategy.md v1.0, FOUNDATION_STABILITY_POLICY.md v1.0*
