# Persistence Design — EPIC 5

> **Documento de diseño de persistencia para el Bounded Context Ingestion**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-05
> Basado en: Foundation v1.0 (FROZEN), Ingestion Domain v2.0 (FROZEN),
> Repository Contracts v1.0, Transaction Boundaries v1.0
>
> **Este documento especifica el modelo relacional y la estrategia de mapeo ORM.**
> NO implementa SQLAlchemy. NO modifica Foundation. NO modifica Domain.

---

## Table of Contents

1. [Database Schema](#1-database-schema)
   - 1.1 [Table Naming Convention](#11-table-naming-convention)
   - 1.2 [ingestion_news_sources](#12-ingestion_news_sources)
   - 1.3 [ingestion_feeds](#13-ingestion_feeds)
   - 1.4 [ingestion_raw_articles](#14-ingestion_raw_articles)
   - 1.5 [ingestion_categories](#15-ingestion_categories)
   - 1.6 [ingestion_topics](#16-ingestion_topics)
   - 1.7 [Association Tables (M:N)](#17-association-tables-mn)
   - 1.8 [Índices Adicionales](#18-índices-adicionales)
2. [ORM Mapping Strategy](#2-orm-mapping-strategy)
   - 2.1 [TypeDecorator Strategy](#21-typedecorator-strategy)
   - 2.2 [Association Tables](#22-association-tables)
   - 2.3 [Loading Strategy](#23-loading-strategy)
   - 2.4 [Cascade & Delete Policies](#24-cascade--delete-policies)
   - 2.5 [Optimistic Locking](#25-optimistic-locking)
3. [Decisiones Arquitectónicas](#3-decisiones-arquitectónicas)

---

## 1. Database Schema

### 1.1 Table Naming Convention

| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| **Tablas** | `ingestion_{plural_snake}` | `ingestion_news_sources` |
| **Columnas PK** | `id` (toda tabla tiene UUID PK) | `id` |
| **Columnas FK** | `{entity}_id` | `source_id`, `feed_id` |
| **Columnas booleanas** | `is_{adjective}` | `is_active` |
| **Columnas datetime** | `{event}_at` | `created_at`, `fetched_at` |
| **Columnas de configuración** | `{context}_{field}` | `sync_mode`, `max_retries` |
| **Columnas de versión** | `version` (optimistic lock) | `version` |
| **Constraints unique** | `uq_{table}_{fields}` | `uq_feed_source_url` |
| **Constraints FK** | `fk_{child}_{parent}` | `fk_feed_source` |
| **Constraints check** | `ck_{table}_{rule}` | `ck_raw_article_hash_length` |
| **Índices** | `ix_{table}_{fields}` | `ix_raw_articles_feed_fetched` |

**Justificación del prefijo `ingestion_`**: Aislar el BC Ingestion en su propio esquema de nombres evita colisiones cuando otros BCs (Research, Script) agreguen sus tablas. Es el estándar para multi-BC en la misma base de datos.

---

### 1.2 `ingestion_news_sources`

```sql
CREATE TABLE ingestion_news_sources (
    -- PK
    id              UUID PRIMARY KEY,

    -- Atributos del dominio
    name            VARCHAR(255) NOT NULL,
    source_type     VARCHAR(20)  NOT NULL,  -- Enum: RSS, API, SOCIAL_MEDIA, NEWSLETTER
    source_url      VARCHAR(2048) NOT NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,

    -- Optimistic Locking
    version         INTEGER      NOT NULL DEFAULT 1,

    -- Timestamps
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uq_news_source_name UNIQUE (name)
);
```

| Columna | Tipo SQL | Nulo | Defecto | VO/Domain Mapping |
|---------|----------|------|---------|-------------------|
| `id` | UUID | NO | — | `SourceId(EntityId)` via TypeDecorator |
| `name` | VARCHAR(255) | NO | — | `str` primitivo |
| `source_type` | VARCHAR(20) | NO | — | `SourceType` enum via TypeDecorator |
| `source_url` | VARCHAR(2048) | NO | — | `SourceUrl` VO via TypeDecorator |
| `is_active` | BOOLEAN | NO | TRUE | `bool` primitivo |
| `version` | INTEGER | NO | 1 | Optimistic lock counter |
| `created_at` | TIMESTAMPTZ | NO | NOW() | Auditoría |
| `updated_at` | TIMESTAMPTZ | NO | NOW() | Auditoría |

**Notas**:
- `source_url` usa VARCHAR(2048) que es el límite estándar para URLs (RFC 3986).
- `name` es UNIQUE — enforce I-02 a nivel BD (no solo en aplicación).
- `source_type` se almacena como VARCHAR, no como ENUM nativo de PostgreSQL. Esto permite compatibilidad con SQLite en testing (ver Sección 3, Decisión E-02).

---

### 1.3 `ingestion_feeds`

```sql
CREATE TABLE ingestion_feeds (
    -- PK
    id              UUID PRIMARY KEY,

    -- FK al Aggregate padre
    source_id       UUID          NOT NULL,

    -- Atributos del dominio
    url             VARCHAR(2048) NOT NULL,
    label           VARCHAR(500)  NOT NULL,
    language        VARCHAR(2)    NOT NULL,  -- ISO 639-1
    is_active       BOOLEAN       NOT NULL DEFAULT TRUE,

    -- SyncPolicy (descompuesto en columnas separadas)
    sync_mode               VARCHAR(20) NOT NULL DEFAULT 'PULL',
    interval_minutes        INTEGER,
    max_retries             INTEGER     NOT NULL DEFAULT 3,
    backoff_multiplier      FLOAT       NOT NULL DEFAULT 2.0,
    max_backoff_minutes     INTEGER     NOT NULL DEFAULT 60,
    timeout_seconds         INTEGER     NOT NULL DEFAULT 30,
    max_items_per_run       INTEGER     NOT NULL DEFAULT 100,

    -- Estado de ejecución
    retry_count     INTEGER       NOT NULL DEFAULT 0,

    -- Optimistic Locking
    version         INTEGER       NOT NULL DEFAULT 1,

    -- Timestamps
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT fk_feed_source
        FOREIGN KEY (source_id)
        REFERENCES ingestion_news_sources(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_feed_source_url
        UNIQUE (source_id, url)
);
```

| Columna | Tipo SQL | Nulo | Defecto | VO/Domain Mapping |
|---------|----------|------|---------|-------------------|
| `id` | UUID | NO | — | `FeedId(EntityId)` via TypeDecorator |
| `source_id` | UUID | NO | — | `SourceId` via TypeDecorator |
| `url` | VARCHAR(2048) | NO | — | `ArticleUrl` VO via TypeDecorator |
| `label` | VARCHAR(500) | NO | — | `ArticleTitle` VO via TypeDecorator |
| `language` | VARCHAR(2) | NO | — | `Language` VO via TypeDecorator |
| `is_active` | BOOLEAN | NO | TRUE | `bool` primitivo |
| `sync_mode` | VARCHAR(20) | NO | 'PULL' | `SyncMode` enum via TypeDecorator |
| `interval_minutes` | INTEGER | SÍ | NULL | `int\|None` — nullable porque PUSH/STREAM/MANUAL no requieren intervalo |
| `max_retries` | INTEGER | NO | 3 | `int` parte de SyncPolicy |
| `backoff_multiplier` | FLOAT | NO | 2.0 | `float` parte de SyncPolicy |
| `max_backoff_minutes` | INTEGER | NO | 60 | `int` parte de SyncPolicy |
| `timeout_seconds` | INTEGER | NO | 30 | `int` parte de SyncPolicy |
| `max_items_per_run` | INTEGER | NO | 100 | `int` parte de SyncPolicy |
| `retry_count` | INTEGER | NO | 0 | `int` primitivo |
| `version` | INTEGER | NO | 1 | Optimistic lock counter |
| `created_at` | TIMESTAMPTZ | NO | NOW() | Auditoría |
| `updated_at` | TIMESTAMPTZ | NO | NOW() | Auditoría |

**SyncPolicy como columnas separadas**: Se descartó JSON column para SyncPolicy (ver Decisión E-05). Las 7 columnas `sync_*` y `max_*` se reconstruyen como `SyncPolicy` VO en el mapeo ORM usando `composite()`.

**Notas**:
- `interval_minutes` es nullable porque solo es obligatorio para `mode = PULL`. Los modos PUSH, STREAM, MANUAL no lo requieren.
- `uq_feed_source_url` enforce I-06 (URL única dentro del mismo NewsSource).
- El FK a `ingestion_news_sources` usa CASCADE: si se borra un source, se borran sus feeds (ver Decisión C-01 en Cascade Policies).

---

### 1.4 `ingestion_raw_articles`

```sql
CREATE TABLE ingestion_raw_articles (
    -- PK
    id              UUID PRIMARY KEY,

    -- FK al Aggregate padre
    feed_id         UUID          NOT NULL,

    -- Atributos del dominio
    external_id     VARCHAR(512)  NOT NULL,
    content_hash    VARCHAR(64)   NOT NULL,  -- SHA-256: 64 hex chars
    title           VARCHAR(500)  NOT NULL,
    url             VARCHAR(2048) NOT NULL,
    author          VARCHAR(255),
    language        VARCHAR(2),              -- ISO 639-1, nullable hasta detectarse
    published_at    TIMESTAMPTZ,
    fetched_at      TIMESTAMPTZ   NOT NULL,
    content_preview TEXT,
    metadata        JSONB         NOT NULL DEFAULT '{}',

    -- Timestamp de creación (inmutable, única fecha relevante)
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT fk_raw_article_feed
        FOREIGN KEY (feed_id)
        REFERENCES ingestion_feeds(id)
        ON DELETE RESTRICT,  -- No se puede borrar un Feed con artículos

    CONSTRAINT uq_raw_article_feed_external
        UNIQUE (feed_id, external_id),

    CONSTRAINT uq_raw_article_feed_hash
        UNIQUE (feed_id, content_hash),

    CONSTRAINT ck_raw_article_hash_length
        CHECK (LENGTH(content_hash) = 64)
);
```

| Columna | Tipo SQL | Nulo | Defecto | VO/Domain Mapping |
|---------|----------|------|---------|-------------------|
| `id` | UUID | NO | — | `RawArticleId(EntityId)` via TypeDecorator |
| `feed_id` | UUID | NO | — | `FeedId` via TypeDecorator |
| `external_id` | VARCHAR(512) | NO | — | `str` primitivo |
| `content_hash` | VARCHAR(64) | NO | — | `str` primitivo (validado en dominio) |
| `title` | VARCHAR(500) | NO | — | `ArticleTitle` VO via TypeDecorator |
| `url` | VARCHAR(2048) | NO | — | `ArticleUrl` VO via TypeDecorator |
| `author` | VARCHAR(255) | SÍ | NULL | `str\|None` primitivo |
| `language` | VARCHAR(2) | SÍ | NULL | `Language\|None` via TypeDecorator |
| `published_at` | TIMESTAMPTZ | SÍ | NULL | `datetime\|None` |
| `fetched_at` | TIMESTAMPTZ | NO | — | `datetime` (timezone-aware) |
| `content_preview` | TEXT | SÍ | NULL | `str\|None` primitivo |
| `metadata` | JSONB | NO | '{}' | `dict` plano via JSON column |
| `created_at` | TIMESTAMPTZ | NO | NOW() | Auditoría |

**Notas críticas**:
- **NO tiene `version`**: RawArticle es inmutable. No necesita optimistic locking (ver Decisión L-03).
- **NO tiene `updated_at`**: RawArticle nunca se actualiza (I-11).
- **Dos UNIQUE constraints compuestas**:
  - `(feed_id, external_id)` → enforce I-12 (external_id único dentro del Feed).
  - `(feed_id, content_hash)` → enforce I-13 (hash único dentro del Feed).
- **CHECK constraint**: `LENGTH(content_hash) = 64` enforce I-17 (formato SHA-256) a nivel BD como defensa en profundidad.
- **FK con RESTRICT**: No se permite borrar un Feed que tiene RawArticles. Para "eliminar" un feed, se marca como inactivo (soft-delete).
- **`metadata` como JSONB**: PostgreSQL nativo. En SQLite de testing se mapea a TEXT con parseo JSON.
- **Sin relación ORM directa Feed → RawArticles**: La carga de artículos es SIEMPRE paginada vía `RawArticleRepository.find_by_feed()`. Nunca se mapea una relación `relationship()` desde Feed (ver Decisión L-02).

---

### 1.5 `ingestion_categories`

```sql
CREATE TABLE ingestion_categories (
    -- PK
    id              UUID PRIMARY KEY,

    -- Atributos del dominio
    name            VARCHAR(100)  NOT NULL,
    slug            VARCHAR(150)  NOT NULL,
    description     TEXT,
    is_active       BOOLEAN       NOT NULL DEFAULT TRUE,

    -- Self-referencing FK para jerarquía
    parent_id       UUID,

    -- Optimistic Locking
    version         INTEGER       NOT NULL DEFAULT 1,

    -- Timestamps
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT fk_category_parent
        FOREIGN KEY (parent_id)
        REFERENCES ingestion_categories(id)
        ON DELETE SET NULL,  -- Si se borra el padre, la categoría queda como raíz

    CONSTRAINT uq_category_slug UNIQUE (slug),

    CONSTRAINT ck_category_no_self_parent
        CHECK (id != parent_id)
);
```

| Columna | Tipo SQL | Nulo | Defecto | VO/Domain Mapping |
|---------|----------|------|---------|-------------------|
| `id` | UUID | NO | — | `CategoryId(EntityId)` via TypeDecorator |
| `name` | VARCHAR(100) | NO | — | `CategoryName` VO via TypeDecorator |
| `slug` | VARCHAR(150) | NO | — | `str` primitivo |
| `description` | TEXT | SÍ | NULL | `str\|None` primitivo |
| `is_active` | BOOLEAN | NO | TRUE | `bool` primitivo |
| `parent_id` | UUID | SÍ | NULL | `CategoryId\|None` via TypeDecorator |
| `version` | INTEGER | NO | 1 | Optimistic lock counter |

**Notas**:
- `slug` es UNIQUE global (I-18 enforced a nivel BD).
- `parent_id` self-referencia con `ON DELETE SET NULL`: si se borra una categoría padre, las hijas quedan como raíces (no se pierden).
- CHECK constraint evita self-parent (I-19).
- La validación de ciclos (I-20) se hace en Application Layer (requiere consultar el repositorio).

---

### 1.6 `ingestion_topics`

```sql
CREATE TABLE ingestion_topics (
    -- PK
    id              UUID PRIMARY KEY,

    -- Atributos del dominio
    name            VARCHAR(255)  NOT NULL,
    description     TEXT,
    is_active       BOOLEAN       NOT NULL DEFAULT TRUE,

    -- Optimistic Locking
    version         INTEGER       NOT NULL DEFAULT 1,

    -- Timestamps
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uq_topic_name UNIQUE (name)
);
```

| Columna | Tipo SQL | Nulo | Defecto | VO/Domain Mapping |
|---------|----------|------|---------|-------------------|
| `id` | UUID | NO | — | `TopicId(EntityId)` via TypeDecorator |
| `name` | VARCHAR(255) | NO | — | `str` primitivo |
| `description` | TEXT | SÍ | NULL | `str\|None` primitivo |
| `is_active` | BOOLEAN | NO | TRUE | `bool` primitivo |
| `version` | INTEGER | NO | 1 | Optimistic lock counter |

**Nota**: Topic es la entidad más simple del modelo. No tiene VOs propios (name es str primitivo validado en dominio). No tiene FKs. No tiene jerarquía.

---

### 1.7 Association Tables (M:N)

#### `ingestion_news_source_categories`

```sql
CREATE TABLE ingestion_news_source_categories (
    source_id       UUID NOT NULL,
    category_id     UUID NOT NULL,

    PRIMARY KEY (source_id, category_id),

    CONSTRAINT fk_nsc_source
        FOREIGN KEY (source_id)
        REFERENCES ingestion_news_sources(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_nsc_category
        FOREIGN KEY (category_id)
        REFERENCES ingestion_categories(id)
        ON DELETE CASCADE
);
```

#### `ingestion_news_source_topics`

```sql
CREATE TABLE ingestion_news_source_topics (
    source_id       UUID NOT NULL,
    topic_id        UUID NOT NULL,

    PRIMARY KEY (source_id, topic_id),

    CONSTRAINT fk_nst_source
        FOREIGN KEY (source_id)
        REFERENCES ingestion_news_sources(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_nst_topic
        FOREIGN KEY (topic_id)
        REFERENCES ingestion_topics(id)
        ON DELETE CASCADE
);
```

#### `ingestion_feed_categories`

```sql
CREATE TABLE ingestion_feed_categories (
    feed_id         UUID NOT NULL,
    category_id     UUID NOT NULL,

    PRIMARY KEY (feed_id, category_id),

    CONSTRAINT fk_fc_feed
        FOREIGN KEY (feed_id)
        REFERENCES ingestion_feeds(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_fc_category
        FOREIGN KEY (category_id)
        REFERENCES ingestion_categories(id)
        ON DELETE CASCADE
);
```

#### `ingestion_feed_topics`

```sql
CREATE TABLE ingestion_feed_topics (
    feed_id         UUID NOT NULL,
    topic_id        UUID NOT NULL,

    PRIMARY KEY (feed_id, topic_id),

    CONSTRAINT fk_ft_feed
        FOREIGN KEY (feed_id)
        REFERENCES ingestion_feeds(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_ft_topic
        FOREIGN KEY (topic_id)
        REFERENCES ingestion_topics(id)
        ON DELETE CASCADE
);
```

**Diseño consistente para las 4 tablas**:
- **PK compuesta** = par de FKs. Esto previene duplicados naturalmente.
- **Sin `id` propio**: La PK compuesta es suficiente. No hay necesidad de un UUID adicional.
- **Sin timestamps**: Las M:N no tienen semántica temporal. Si se necesita en el futuro (ej: "cuándo se asignó"), se agrega `assigned_at`.
- **CASCADE en ambos FKs**: Si se borra un source/feed/category/topic, las relaciones se limpian automáticamente.
- **Índices**: La PK compuesta ya crea un índice en (FK1, FK2). Para queries inversas (ej: "todos los sources de una categoría"), ver Índices Adicionales.

---

### 1.8 Índices Adicionales

Además de los índices creados automáticamente por PKs y UNIQUE constraints, se requieren los siguientes índices para performance:

```sql
-- ingestion_raw_articles: paginación por feed ordenada por fetched_at DESC
CREATE INDEX ix_raw_articles_feed_fetched
    ON ingestion_raw_articles (feed_id, fetched_at DESC);

-- ingestion_raw_articles: deduplicación por URL dentro del feed
CREATE INDEX ix_raw_articles_feed_url
    ON ingestion_raw_articles (feed_id, url);

-- ingestion_feeds: consultas por source (find_by_source, find_active_by_source)
CREATE INDEX ix_feeds_source_active
    ON ingestion_feeds (source_id, is_active);

-- ingestion_news_sources: consultas de activos
CREATE INDEX ix_news_sources_active
    ON ingestion_news_sources (is_active);

-- ingestion_categories: jerarquía (find_by_parent)
CREATE INDEX ix_categories_parent
    ON ingestion_categories (parent_id);

-- ingestion_categories: consultas de activos
CREATE INDEX ix_categories_active
    ON ingestion_categories (is_active);

-- ingestion_topics: consultas de activos
CREATE INDEX ix_topics_active
    ON ingestion_topics (is_active);

-- Association tables: queries inversas (todos los sources/feeds de una categoría/topic)
CREATE INDEX ix_nsc_category ON ingestion_news_source_categories (category_id);
CREATE INDEX ix_nst_topic    ON ingestion_news_source_topics (topic_id);
CREATE INDEX ix_fc_category  ON ingestion_feed_categories (category_id);
CREATE INDEX ix_ft_topic     ON ingestion_feed_topics (topic_id);
```

**Justificación de índices**:

| Índice | Queries que soporta | Cobertura |
|--------|---------------------|-----------|
| `ix_raw_articles_feed_fetched` | `find_by_feed()` con ORDER BY fetched_at DESC + LIMIT/OFFSET | Cubierto (no necesita lookup adicional) |
| `ix_raw_articles_feed_url` | `exists_by_url()` | Filtra por feed_id + url sin table scan |
| `ix_feeds_source_active` | `find_by_source()`, `find_active_by_source()`, `count_active_by_source()` | Cubre source_id + is_active |
| `ix_news_sources_active` | `find_active()` | 50% selectividad aprox — justificado |
| `ix_categories_parent` | `find_by_parent()` | Jerarquía, lookup por parent_id |
| `ix_nsc_category` | Queries inversas category→source | Sin esto, las queries inversas harían full scan |

---

## 2. ORM Mapping Strategy

### 2.1 TypeDecorator Strategy

| # | Tipo de Dominio | Estrategia | Decorador | Columna subyacente |
|---|---|---|---|---|
| **T-01** | `EntityId` (SourceId, FeedId, RawArticleId, CategoryId, TopicId) | **TypeDecorator genérico** | `EntityIdType[IdT]` parametrizado por clase | `Uuid` |
| **T-02** | `ArticleTitle`, `ArticleUrl`, `CategoryName`, `SourceUrl`, `Language` | **TypeDecorator por tipo** | Uno por cada VO (`ArticleTitleType`, etc.) | `String(N)` |
| **T-03** | `SourceType`, `SyncMode` (str, Enum) | **TypeDecorator por enum** | `SourceTypeType`, `SyncModeType` | `String(20)` |
| **T-04** | `SyncPolicy` (compuesto, 7 campos) | **Columnas separadas + `composite()`** | — | 7 columnas individuales |
| **T-05** | `metadata: dict` (RawArticle) | **JSON column nativa** | — | `JSON` / `JSONB` |
| **T-06** | `datetime` (todos) | **Timezone-aware** | — | `DateTime(timezone=True)` |

#### T-01: EntityIdType — Decorador Genérico

```
EntityIdType[IdT: EntityId]
├── impl: Uuid (SQLAlchemy 2.x nativo)
├── process_bind_param: EntityId → UUID (extrae .value)
└── process_result_value: UUID → IdT(value=uuid) (construye tipo específico)
```

**Decisión: UN decorador genérico, NO uno por ID.**

- **A favor (1 genérico)**: DRY. Los 5 IDs tienen estructura idéntica (UUID). El type safety viene del parámetro `IdT`, no de tener clases separadas. Menos código, menos testing.
- **En contra (1 genérico)**: SQLAlchemy TypeDecorator con genéricos (TypeVar) requiere cuidado en la implementación para que Mypy/Pyright entiendan los tipos. Pero es un problema resoluble con la firma correcta.
- **Veredicto**: Un `EntityIdType[T: EntityId]` parametrizado. La implementación recibe la clase concreta en `__init__` (`EntityIdType(SourceId)`) y la usa para reconstruir en `process_result_value`.

```python
# Pseudocódigo de la API:
from sqlalchemy import TypeDecorator, Uuid

class EntityIdType(TypeDecorator):
    impl = Uuid
    cache_ok = True

    def __init__(self, id_class: type[EntityId]):
        self.id_class = id_class
        super().__init__()

    def process_bind_param(self, value: EntityId | None, dialect) -> UUID | None:
        return value.value if value is not None else None

    def process_result_value(self, value: UUID | None, dialect) -> EntityId | None:
        return self.id_class(value=value) if value is not None else None
```

Uso en el modelo ORM:
```python
class NewsSourceModel(Base):
    id: Mapped[SourceId] = mapped_column(EntityIdType(SourceId), primary_key=True)
    source_url: Mapped[SourceUrl] = mapped_column(SourceUrlType, ...)
```

#### T-02: Value Objects Simples (String)

**Decisión: TypeDecorator por cada VO, NO columna directa.**

Cada VO simple (ArticleTitle, ArticleUrl, CategoryName, SourceUrl, Language) obtiene su propio TypeDecorator porque:

1. **Validación en carga**: Si el dato en BD es inválido (ej: corrupción), el TypeDecorator lanza error al cargar. Defensa en profundidad.
2. **Consistencia**: La lógica de conversión está encapsulada en UN lugar, no dispersa en repositorios.
3. **Type safety**: Las columnas en el modelo ORM tienen tipos de dominio, no `str` genérico. Mypy detecta errores.

| TypeDecorator | impl | Longitud | VO | Validación (en VO) |
|---|---|---|---|---|
| `ArticleTitleType` | `String(500)` | 500 | `ArticleTitle` | No vacío, max 500, sin caracteres de control |
| `ArticleUrlType` | `String(2048)` | 2048 | `ArticleUrl` | URL válida http/https |
| `CategoryNameType` | `String(100)` | 100 | `CategoryName` | No vacío, max 100, solo alfanumérico+guiones |
| `SourceUrlType` | `String(2048)` | 2048 | `SourceUrl` | URL válida http/https, normalizada |
| `LanguageType` | `String(2)` | 2 | `Language` | Código ISO 639-1 válido (en, es, fr, ...) |

```python
# Patrón para cada VO:
class ArticleTitleType(TypeDecorator):
    impl = String(500)
    cache_ok = True

    def process_bind_param(self, value: ArticleTitle | None, dialect) -> str | None:
        return value.value if value is not None else None

    def process_result_value(self, value: str | None, dialect) -> ArticleTitle | None:
        return ArticleTitle(value) if value is not None else None
```

#### T-03: Enums (SourceType, SyncMode)

**Decisión: VARCHAR + TypeDecorator, NO ENUM nativo de PostgreSQL.**

Justificación:
- **Portabilidad**: SQLite no soporta ENUM nativo. Para testing necesitamos el mismo schema.
- **Flexibilidad**: Agregar un nuevo valor al enum no requiere migración de schema.
- **Simplicidad**: VARCHAR(20) es suficiente para los valores actuales y futuros.

```python
class SourceTypeType(TypeDecorator):
    impl = String(20)
    cache_ok = True

    def process_bind_param(self, value: SourceType | None, dialect) -> str | None:
        return value.value if value is not None else None

    def process_result_value(self, value: str | None, dialect) -> SourceType | None:
        return SourceType(value) if value is not None else None
```

| Enum | Tipo Python | Valores | Columna |
|---|---|---|---|
| `SourceType` | `str, Enum` | RSS, API, SOCIAL_MEDIA, NEWSLETTER | VARCHAR(20) |
| `SyncMode` | `str, Enum` | PULL, PUSH, STREAM, MANUAL | VARCHAR(20) |

#### T-04: SyncPolicy (Composite VO)

**Decisión: 7 columnas separadas + reconstrucción vía `composite()`.**

Alternativas descartadas:
- ❌ **JSON column**: Impide consultar campos individuales (ej: "todos los feeds en PULL"). No podemos poner índices en `sync_mode` dentro de un JSON.
- ❌ **TypeDecorator compuesto**: TypeDecorator trabaja con una sola columna. No hay manera de mapear 7 columnas a un VO sin `composite()`.

**Solución elegida**: SQLAlchemy `orm.composite()` mapea múltiples columnas a un solo atributo `SyncPolicy`. La clase `SyncPolicy` ya tiene un constructor que acepta todos los campos como parámetros (mode requerido, el resto opcionales).

```python
# En el modelo ORM:
class FeedModel(Base):
    __tablename__ = "ingestion_feeds"

    # SyncPolicy columns
    sync_mode: Mapped[str] = mapped_column("sync_mode", ...)
    interval_minutes: Mapped[int | None] = mapped_column(...)
    max_retries: Mapped[int] = mapped_column(...)
    backoff_multiplier: Mapped[float] = mapped_column(...)
    max_backoff_minutes: Mapped[int] = mapped_column(...)
    timeout_seconds: Mapped[int] = mapped_column(...)
    max_items_per_run: Mapped[int] = mapped_column(...)

    # Composite mapping
    sync_policy: Mapped[SyncPolicy] = composite(
        SyncPolicy,
        sync_mode,
        interval_minutes,
        max_retries,
        backoff_multiplier,
        max_backoff_minutes,
        timeout_seconds,
        max_items_per_run,
    )
```

**Orden de parámetros**: Debe coincidir con `SyncPolicy.__init__`:
1. `mode` → `sync_mode`
2. `interval_minutes` → `interval_minutes`
3. `max_retries` → `max_retries`
4. `backoff_multiplier` → `backoff_multiplier`
5. `max_backoff_minutes` → `max_backoff_minutes`
6. `timeout_seconds` → `timeout_seconds`
7. `max_items_per_run` → `max_items_per_run`

**Ventaja**: El `SyncPolicy` VO tiene validación en `__post_init__` que se ejecuta automáticamente cuando SQLAlchemy reconstruye el objeto desde la BD. Defensa en profundidad.

#### T-05: metadata como JSON

`metadata: dict` en RawArticle es un blob opaco de datos externos. No se consulta por claves internas. Se mapea directamente como columna JSON:

```python
class RawArticleModel(Base):
    metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
```

En PostgreSQL → `JSONB` (binario, indexable, con constraints). En SQLite → `TEXT` con parseo JSON nativo de SQLAlchemy.

#### T-06: Datetimes con Timezone

TODOS los `datetime` en el modelo deben ser timezone-aware (UTC):

```python
from sqlalchemy import DateTime

created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    server_default=func.now(),
)
```

**Justificación**: Foundation exige UTC con timezone para todos los Domain Events. Consistencia con el estándar del proyecto (ver foundation-design.md §7.3).

---

### 2.2 Association Tables

Las 4 tablas M:N se modelan como **tablas de asociación explícitas** (no `secondary` en la relación, no `association_proxy`).

**¿Por qué explícitas y no `secondary`?**

1. **Control de carga**: Con `secondary`, la relación carga la colección completa. Con tabla explícita, tenemos control granular de la estrategia de carga.
2. **Mantenibilidad**: La tabla explícita es un modelo ORM independiente. Se puede evolucionar (agregar columnas como `assigned_at`) sin tocar la relación.
3. **Testing**: Las tablas explícitas se pueden consultar directamente en tests de integración.

**Estrategia de modelado**:

```python
# Tabla de asociación como modelo ORM (sin necesidad de clase Python si es pura FK pair)
# Opción 1: Usar `Table` directamente (suficiente para pares FK)
news_source_category_table = Table(
    "ingestion_news_source_categories",
    Base.metadata,
    Column("source_id", ...),
    Column("category_id", ...),
    ...
)

# Opción 2: Como clase completa (si se necesitan columnas extra en el futuro)
class NewsSourceCategoryModel(Base):
    __tablename__ = "ingestion_news_source_categories"
    source_id: Mapped[SourceId] = mapped_column(ForeignKey(...), primary_key=True)
    category_id: Mapped[CategoryId] = mapped_column(ForeignKey(...), primary_key=True)
```

**Recomendación**: Usar `Table` (Opción 1) para la implementación inicial. Si en el futuro se necesitan columnas extra (ej: `assigned_by`, `assigned_at`), migrar a clase completa. YAGNI aplicado.

**Relaciones en el modelo ORM**:

```python
# En NewsSourceModel:
categories: Mapped[list[CategoryModel]] = relationship(
    secondary=news_source_category_table,
    lazy="selectin",
    viewonly=True,  # Las mutaciones van vía domain methods, no ORM directo
)

# En CategoryModel (inversa opcional):
sources: Mapped[list[NewsSourceModel]] = relationship(
    secondary=news_source_category_table,
    lazy="selectin",
    viewonly=True,
)
```

**`viewonly=True`**: Las colecciones M:N son **solo lectura** en el modelo ORM. Las mutaciones ocurren exclusivamente a través de los métodos de dominio del aggregate (`assign_category()`, `remove_category()`), que modifican la lista de IDs en memoria. Luego el repositorio persiste los cambios. El ORM refleja el estado, no es el mecanismo de modificación.

Esto simplifica la implementación: el repositorio limpia todas las relaciones M:N del aggregate y las reinserta en cada `save()`. Sin `viewonly=True`, SQLAlchemy podría intentar sincronizar la colección automáticamente, causando dobles escrituras.

---

### 2.3 Loading Strategy

| Relación | Tipo | Estrategia | Justificación |
|---|---|---|---|
| **NewsSource → Feeds** | 1:N | `lazy="select"` | Los feeds son ARs separados. Rara vez se cargan con el source. Domain operations cargan cada AR independientemente. |
| **Feed → RawArticles** | 1:N | **SIN RELACIÓN ORM** | RawArticles se cargan SIEMPRE paginados vía `find_by_feed()`. Una relación ORM cargaría potencialmente millones de objetos. |
| **Category → parent** | self-ref | `lazy="joined"` | El padre se accede frecuentemente al navegar la jerarquía. Un JOIN adicional por categoría cargada es aceptable. |
| **Category → children** | self-ref | `lazy="select"` | Los hijos se consultan explícitamente vía `find_by_parent()`. Rara vez se necesita la colección completa. |
| **NewsSource → Categories** | M:N | `lazy="selectin"` | Colecciones pequeñas (<20). selectin hace 1 query extra con IN clause. Eficiente. |
| **NewsSource → Topics** | M:N | `lazy="selectin"` | Colecciones pequeñas. Misma razón. |
| **Feed → Categories** | M:N | `lazy="selectin"` | Colecciones pequeñas. |
| **Feed → Topics** | M:N | `lazy="selectin"` | Colecciones pequeñas. |

**Decisión clave — selectin vs joined**:

- **selectin**: Emite `SELECT ... WHERE id IN (...)`. 1 query extra, independiente del tamaño de la colección. Preferido cuando la colección es pequeña y las FKs no son parte de la PK de la tabla asociada.
- **joined**: LEFT JOIN en la misma query. Más eficiente para 1:1 o cuando siempre se necesita la relación. Pero puede generar cartesian explosion si hay múltiples joins.
- **lazy="select"**: Query diferida. Se ejecuta cuando se accede al atributo. Default de SQLAlchemy. Bueno para colecciones que rara vez se acceden.

**¿Por qué NO eager loading para Feeds dentro de NewsSource?**

El dominio trata a NewsSource y Feed como ARs separados. Cargar todos los feeds de un source al cargar el source mismo viola la frontera de consistencia del aggregate. Además, un source puede tener docenas de feeds. La mayoría de las operaciones de dominio operan sobre un feed o source individual, no sobre ambos simultáneamente.

**Excepciones para queries de presentación/lectura**:

En Application Layer (queries, no commands), se puede usar `selectinload()` explícito cuando se necesita cargar un source con sus feeds para mostrar en UI:

```python
# En un Query Handler (NO en repositorio de dominio):
query = select(NewsSourceModel).options(
    selectinload(NewsSourceModel.feeds)
)
```

Esto mantiene el repositorio de dominio puro (sin options de carga) y permite que Application Layer optimice las queries de lectura según necesidad. Es el patrón **Query Stack** (ver transaction-boundaries.md §5.2).

---

### 2.4 Cascade & Delete Policies

| Relación | Dirección | ON DELETE | cascade ORM | Justificación |
|---|---|---|---|---|
| **NewsSource → Feeds** | 1:N | `CASCADE` | `save-update, merge` | Si se borra el source, los feeds pierden sentido. Se borran automáticamente. **Sin `delete` cascade ORM** para evitar borrados accidentales desde el modelo. La BD enforcea el CASCADE. |
| **Feed → RawArticles** | 1:N | `RESTRICT` | — | RawArticles son registros de auditoría. NO se borran cuando se borra el feed. RESTRICT previene el borrado si existen artículos. |
| **Category → parent** | self-ref | `SET NULL` | — | Si se borra una categoría padre, las hijas quedan como raíces. No se pierden. |
| **Association M:N** | ambas | `CASCADE` | — | Si se borra cualquiera de las entidades, las relaciones se limpian. |
| **Category (referida desde M:N)** | — | `CASCADE` | — | Al borrar una categoría, sus relaciones en M:N se limpian. La categoría referenciada no puede borrarse si es referenciada como parent_id (SET NULL). |

**Reglas de negocio sobre borrado (soft-delete como estrategia principal)**:

1. **NewsSource**: NO se borra en operación normal. Se desactiva (`is_active = False`). El borrado físico solo ocurre en limpieza administrativa.
2. **Feed**: NO se borra en operación normal. Se desactiva o se pausa. El borrado físico solo si se elimina el source padre (CASCADE).
3. **RawArticle**: NUNCA se borra (I-11). Es inmutable.
4. **Category**: Se puede borrar (SET NULL en parent_id, CASCADE en M:N). Pero en la práctica se desactiva.
5. **Topic**: Similar a Category.

**¿Cascade ORM vs Cascade BD?**:

Se usa CASCADE a nivel BD (DDL `ON DELETE CASCADE`) y NO `cascade="all, delete"` en la relación ORM. Razón:

- **BD enforcea la integridad referencial** aunque alguien borre directamente desde una consola SQL.
- **El ORM no borra accidentalmente** agregados hijos al modificar la colección.
- **Consistencia**: Si en el futuro se usan otros clients (scripts ETL, migraciones), las reglas se mantienen.

La única excepción: En feeds, se usa `cascade="save-update, merge"` (sin `delete`) para que SQLAlchemy pueda persistir las relaciones sin intervención manual.

---

### 2.5 Optimistic Locking

| Entidad | ¿Locking? | Columna | Justificación |
|---|---|---|---|
| **NewsSource** | ✅ Sí | `version` | Aggregate Root mutable. Posible concurrencia: dos admins desactivando/configurando el mismo source. |
| **Feed** | ✅ Sí | `version` | Aggregate Root mutable. Alta concurrencia: el scheduler ejecuta fetch y actualiza retry_count mientras un admin modifica sync_policy. |
| **RawArticle** | ❌ No | — | Inmutable (I-11). Una vez creado, nunca se actualiza. No hay concurrencia que gestionar. |
| **Category** | ✅ Sí | `version` | Entity mutable. Posible concurrencia: dos admins modificando la jerarquía simultáneamente. |
| **Topic** | ✅ Sí | `version` | Entity mutable. Baja concurrencia pero posible. |

**Implementación**:

SQLAlchemy soporta optimistic locking nativo con `version_id_col`:

```python
class NewsSourceModel(Base):
    __tablename__ = "ingestion_news_sources"
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __mapper_args__ = {
        "version_id_col": version,
    }
```

**Comportamiento**:
- En cada `UPDATE`, SQLAlchemy incluye `WHERE version = :old_version`.
- Si otra sesión modificó el registro entre la lectura y la escritura, `version` no coincide → `StaleDataError`.
- SQLAlchemy incrementa `version` automáticamente en cada `UPDATE`.

**Manejo de `StaleDataError`**:

El repositorio SQLAlchemy debe capturar `StaleDataError` y convertirlo en un `InfrastructureError` (o `DomainError` si el conflicto tiene semántica de negocio):

```python
try:
    session.commit()
except StaleDataError:
    raise ConcurrentModificationError(
        f"Feed {feed_id} was modified by another operation"
    )
```

Este error se propaga al Application Service, que puede reintentar la operación (recargando el aggregate) o notificar al usuario.

**RawArticle: sin locking**:

RawArticle es inmutable. Si dos procesos intentan crear el mismo RawArticle (mismo `external_id + feed_id` o `content_hash + feed_id`), la UNIQUE constraint de BD rechaza el segundo intento. No se requiere version column porque nunca hay una actualización — solo inserción.

---

## 3. Decisiones Arquitectónicas

### Decisión E-01: Un TypeDecorator genérico para EntityId (T-01)

| Opción | Tradeoff |
|--------|----------|
| **✅ Un `EntityIdType[T]` genérico** | DRY. Type-safe via TypeVar. Menos código. Requiere `cache_ok` y TypeVar correcto. |
| ❌ 5 decoradores (SourceIdType, FeedIdType, etc.) | Código repetitivo. Cada uno hace exactamente lo mismo. Mayor superficie de testing. |

### Decisión E-02: VARCHAR para enums, no ENUM nativo de PostgreSQL

| Opción | Tradeoff |
|--------|----------|
| **✅ VARCHAR(20) + TypeDecorator** | Portable (SQLite). No requiere migración al agregar valores. Type-safe en Python. |
| ❌ ENUM nativo PostgreSQL | No portable a SQLite. Requiere migración de schema al agregar valores (`ALTER TYPE ... ADD VALUE`). |

### Decisión E-03: `viewonly=True` en relaciones M:N

| Opción | Tradeoff |
|--------|----------|
| **✅ `viewonly=True`** | Las mutaciones van por domain methods. ORM solo refleja el estado. Sin sincronización automática. Control total del repositorio. |
| ❌ Sin viewonly | SQLAlchemy podría intentar sincronizar colecciones automáticamente. Las listas de IDs en el dominio y las tablas M:N podrían desincronizarse. |

### Decisión E-04: Sin relación ORM Feed → RawArticles

| Opción | Tradeoff |
|--------|----------|
| **✅ Sin relación** | Previene cargas masivas accidentales. Toda carga de RawArticles es paginada vía repositorio. |
| ❌ `lazy="dynamic"` | Obsoleto en SQLAlchemy 2.x. Falso sentido de seguridad — un `relationship().all()` aún carga todo. |
| ❌ `lazy="select"` | Permitir `feed.raw_articles` en código sería un antipatrón de performance difícil de detectar en code review. |

### Decisión E-05: SyncPolicy como columnas separadas (no JSON)

| Opción | Tradeoff |
|--------|----------|
| **✅ 7 columnas + `composite()`** | Consultable (WHERE sync_mode='PULL'). Indexable. Con constraints NOT NULL y defaults a nivel BD. Validación en VO reconstruido. |
| ❌ JSON column | No consultable sin extraer del JSON. Sin constraints de tipo. No portable entre PG y SQLite sin cuidados. |

### Decisión E-06: Optimistic Locking en agregados mutables, no en RawArticle

| Opción | Tradeoff |
|--------|----------|
| **✅ Locking en NewsSource, Feed, Category, Topic** | Previene conflictos de concurrencia en escritura. Bajo overhead (1 columna INTEGER). |
| ❌ Locking también en RawArticle | Sin sentido — RawArticle es inmutable. La UNIQUE constraint ya protege contra duplicados. Overhead innecesario de memoria y CPU. |

### Decisión E-07: CASCADE BD vs CASCADE ORM

| Opción | Tradeoff |
|--------|----------|
| **✅ CASCADE en DDL (ON DELETE CASCADE)** | La BD siempre enforcea la regla. Independiente del ORM. Protege contra borrados directos desde SQL. |
| ❌ `cascade="all, delete"` en relación ORM | Solo funciona si se borra desde el ORM. Un DELETE directo desde consola SQL violaría la integridad. Mayor riesgo de borrados accidentales desde código al modificar colecciones. |
