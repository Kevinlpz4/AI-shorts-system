# ORM Mapping Strategy

> **Estrategia completa de mapeo ORM para el Bounded Context Ingestion**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-05
> Stack: SQLAlchemy 2.x, Python 3.12, PostgreSQL (prod), SQLite (testing)
>
> **Este documento detalla CADA TypeDecorator, CADA relación, y CADA decisión
> de configuración ORM. NO implementa código SQLAlchemy ejecutable.**

---

## Table of Contents

1. [TypeDecorator Catalog](#1-typedecorator-catalog)
   - 1.1 [EntityIdType (Generic)](#11-entityidtype-generic)
   - 1.2 [ArticleTitleType](#12-articletitletype)
   - 1.3 [ArticleUrlType](#13-articleurltype)
   - 1.4 [CategoryNameType](#14-categorynametype)
   - 1.5 [SourceUrlType](#15-sourceurltype)
   - 1.6 [LanguageType](#16-languagetype)
   - 1.7 [SourceTypeType](#17-sourcetypetype)
   - 1.8 [SyncModeType](#18-syncmodetype)
2. [Composite Value Objects](#2-composite-value-objects)
   - 2.1 [SyncPolicy — Composite Mapping](#21-syncpolicy--composite-mapping)
3. [Enum Mapping](#3-enum-mapping)
4. [JSON Columns](#4-json-columns)
5. [Relationship Configuration](#5-relationship-configuration)
   - 5.1 [NewsSource → Feeds (1:N)](#51-newssource--feeds-1n)
   - 5.2 [Feed → RawArticles (1:N)](#52-feed--rawarticles-1n)
   - 5.3 [Category → parent/children (self-ref)](#53-category--parentchildren-self-ref)
   - 5.4 [NewsSource ↔ Category (M:N)](#54-newssource--category-mn)
   - 5.5 [NewsSource ↔ Topic (M:N)](#55-newssource--topic-mn)
   - 5.6 [Feed ↔ Category (M:N)](#56-feed--category-mn)
   - 5.7 [Feed ↔ Topic (M:N)](#57-feed--topic-mn)
6. [Table Naming Convention](#6-table-naming-convention)
7. [Base ORM Infrastructure](#7-base-orm-infrastructure)
   - 7.1 [DeclarativeBase](#71-declarativebase)
   - 7.2 [Registry and Naming Conventions](#72-registry-and-naming-conventions)
   - 7.3 [Engine Configuration](#73-engine-configuration)
   - 7.4 [Session Factory](#74-session-factory)
8. [Repository Implementation Strategy](#8-repository-implementation-strategy)
   - 8.1 [Patrón Base de Repositorio SQLAlchemy](#81-patrón-base-de-repositorio-sqlalchemy)
   - 8.2 [Mapeo ORM ↔ Domain](#82-mapeo-orm--domain)
   - 8.3 [Manejo de Duplicados en RawArticle](#83-manejo-de-duplicados-en-rawarticle)

---

## 1. TypeDecorator Catalog

### 1.1 EntityIdType (Generic)

```python
"""
TypeDecorator genérico para TODOS los EntityId del BC Ingestion.

Convierte automáticamente entre:
  - DB:   UUID (nativo PostgreSQL / string SQLite)
  - Python: SourceId | FeedId | RawArticleId | CategoryId | TopicId

Uso:
    id: Mapped[SourceId] = mapped_column(
        EntityIdType(SourceId), primary_key=True
    )
    source_id: Mapped[SourceId] = mapped_column(
        EntityIdType(SourceId), ForeignKey("ingestion_news_sources.id")
    )

Type safety: El parámetro id_class define el tipo de retorno.
    EntityIdType(SourceId) → process_result_value retorna SourceId
    EntityIdType(FeedId)   → process_result_value retorna FeedId
"""
```

| Propiedad | Valor |
|-----------|-------|
| **Nombre** | `EntityIdType` |
| **Tipo genérico** | `EntityIdType[IdT: EntityId]` |
| **`impl`** | `Uuid` (SQLAlchemy 2.x nativo) |
| **`cache_ok`** | `False` (cada instancia tiene `id_class` diferente) |
| **`process_bind_param`** | `EntityId | None → UUID | None` via `value.value` |
| **`process_result_value`** | `UUID | None → IdT | None` via `id_class(value=uuid)` |
| **`process_literal_param`** | `EntityId | None → str | None` via `str(value)` |

**Diagrama de flujo**:

```
[Python]                           [SQLAlchemy]              [DB]
SourceId(value=UUID(x))  ──bind──▶  EntityIdType  ──────────▶ UUID(x)
                                                    ◀──────────
SourceId(value=UUID(x))  ◀──result── EntityIdType  ◀────────── UUID(x)
```

**Casos borde**:
- `None` → pasa `None` en ambos sentidos (para FK opcionales como `parent_id` en Category).
- UUID inválido en DB → `ValueError` de `UUID(value)` propaga como `IntegrityError`.
- EntityId con `value=None` → no ocurre (EntityId siempre tiene UUID, default_factory=uuid4).

**Colección de tipos que maneja**: `SourceId`, `FeedId`, `RawArticleId`, `CategoryId`, `TopicId`.

---

### 1.2 ArticleTitleType

```python
"""
TypeDecorator para ArticleTitle Value Object.

Convierte entre:
  - DB:   VARCHAR(500)
  - Python: ArticleTitle (frozen dataclass wrapping str)

Validación: ArticleTitle.__post_init__ valida no vacío, max 500 chars,
            sin caracteres de control, trim automático.
"""
```

| Propiedad | Valor |
|-----------|-------|
| **`impl`** | `String(500)` |
| **`cache_ok`** | `True` |
| **`process_bind_param`** | `ArticleTitle | None → str | None` via `value.value` |
| **`process_result_value`** | `str | None → ArticleTitle | None` via `ArticleTitle(value)` |

**Columnas que usa**:
- `ingestion_feeds.label` → `VARCHAR(500) NOT NULL`
- `ingestion_raw_articles.title` → `VARCHAR(500) NOT NULL`

---

### 1.3 ArticleUrlType

```python
"""
TypeDecorator para ArticleUrl Value Object.

Convierte entre:
  - DB:   VARCHAR(2048)
  - Python: ArticleUrl (frozen dataclass wrapping str)

Validación: ArticleUrl.__post_init__ valida URL http/https,
            sin fragmentos, sin caracteres de control.
"""
```

| Propiedad | Valor |
|-----------|-------|
| **`impl`** | `String(2048)` |
| **`cache_ok`** | `True` |
| **`process_bind_param`** | `ArticleUrl | None → str | None` via `value.value` |
| **`process_result_value`** | `str | None → ArticleUrl | None` via `ArticleUrl(value)` |

**Columnas que usa**:
- `ingestion_feeds.url` → `VARCHAR(2048) NOT NULL`
- `ingestion_raw_articles.url` → `VARCHAR(2048) NOT NULL`

---

### 1.4 CategoryNameType

```python
"""
TypeDecorator para CategoryName Value Object.

Convierte entre:
  - DB:   VARCHAR(100)
  - Python: CategoryName (frozen dataclass wrapping str)

Validación: CategoryName.__post_init__ valida no vacío, max 100 chars,
            solo alfanumérico + guiones + espacios, trim automático.
"""
```

| Propiedad | Valor |
|-----------|-------|
| **`impl`** | `String(100)` |
| **`cache_ok`** | `True` |
| **`process_bind_param`** | `CategoryName | None → str | None` via `value.value` |
| **`process_result_value`** | `str | None → CategoryName | None` via `CategoryName(value)` |

**Columnas que usa**:
- `ingestion_categories.name` → `VARCHAR(100) NOT NULL`

---

### 1.5 SourceUrlType

```python
"""
TypeDecorator para SourceUrl Value Object.

Convierte entre:
  - DB:   VARCHAR(2048)
  - Python: SourceUrl (frozen dataclass wrapping str)

Validación: SourceUrl.__post_init__ valida URL http/https, normaliza
            (lowercase scheme, sin trailing slash).
"""
```

| Propiedad | Valor |
|-----------|-------|
| **`impl`** | `String(2048)` |
| **`cache_ok`** | `True` |
| **`process_bind_param`** | `SourceUrl | None → str | None` via `value.value` |
| **`process_result_value`** | `str | None → SourceUrl | None` via `SourceUrl(value)` |

**Columnas que usa**:
- `ingestion_news_sources.source_url` → `VARCHAR(2048) NOT NULL`

---

### 1.6 LanguageType

```python
"""
TypeDecorator para Language Value Object (ISO 639-1).

Convierte entre:
  - DB:   VARCHAR(2)
  - Python: Language (frozen dataclass wrapping str)

Validación: Language.__post_init__ valida código ISO 639-1 de 2 letras,
            normaliza a lowercase. Lista de códigos permitidos.
"""
```

| Propiedad | Valor |
|-----------|-------|
| **`impl`** | `String(2)` |
| **`cache_ok`** | `True` |
| **`process_bind_param`** | `Language | None → str | None` via `value.code` |
| **`process_result_value`** | `str | None → Language | None` via `Language(value)` |

**Diferencia con otros VOs**: Language usa `.code` como atributo interno (no `.value`). Esto es importante: `process_bind_param` debe extraer `value.code`, no `value.value`.

**Columnas que usa**:
- `ingestion_feeds.language` → `VARCHAR(2) NOT NULL`
- `ingestion_raw_articles.language` → `VARCHAR(2)` (nullable hasta detectarse)

---

### 1.7 SourceTypeType

```python
"""
TypeDecorator para SourceType Enum.

Convierte entre:
  - DB:   VARCHAR(20)
  - Python: SourceType (str, Enum)

Valores: RSS, API, SOCIAL_MEDIA, NEWSLETTER

NOTA: Se almacena como VARCHAR, no como ENUM nativo de PostgreSQL.
      Esto permite compatibilidad con SQLite en testing.
"""
```

| Propiedad | Valor |
|-----------|-------|
| **`impl`** | `String(20)` |
| **`cache_ok`** | `True` |
| **`process_bind_param`** | `SourceType | None → str | None` via `value.value` |
| **`process_result_value`** | `str | None → SourceType | None` via `SourceType(value)` |

**Columnas que usa**:
- `ingestion_news_sources.source_type` → `VARCHAR(20) NOT NULL`

**¿Qué pasa si la DB tiene un valor inválido?**: `SourceType(valor_inválido)` lanza `ValueError`. Esto es deliberado — defensa en profundidad. Si hay datos corruptos en DB, queremos fallar rápido.

---

### 1.8 SyncModeType

```python
"""
TypeDecorator para SyncMode Enum.

Convierte entre:
  - DB:   VARCHAR(20)
  - Python: SyncMode (str, Enum)

Valores: PULL, PUSH, STREAM, MANUAL
"""
```

| Propiedad | Valor |
|-----------|-------|
| **`impl`** | `String(20)` |
| **`cache_ok`** | `True` |
| **`process_bind_param`** | `SyncMode | None → str | None` via `value.value` |
| **`process_result_value`** | `str | None → SyncMode | None` via `SyncMode(value)` |

**Columnas que usa**:
- `ingestion_feeds.sync_mode` → `VARCHAR(20) NOT NULL DEFAULT 'PULL'`

---

## 2. Composite Value Objects

### 2.1 SyncPolicy — Composite Mapping

| Atributo SyncPolicy | Columna DB | Tipo SQL | Nulo | Defecto |
|---|---|---|---|---|
| `mode` | `sync_mode` | VARCHAR(20) | NO | 'PULL' |
| `interval_minutes` | `interval_minutes` | INTEGER | SÍ | NULL |
| `max_retries` | `max_retries` | INTEGER | NO | 3 |
| `backoff_multiplier` | `backoff_multiplier` | FLOAT | NO | 2.0 |
| `max_backoff_minutes` | `max_backoff_minutes` | INTEGER | NO | 60 |
| `timeout_seconds` | `timeout_seconds` | INTEGER | NO | 30 |
| `max_items_per_run` | `max_items_per_run` | INTEGER | NO | 100 |

**Estrategia**: SQLAlchemy `orm.composite()` mapea las 7 columnas al `SyncPolicy` VO.

```
┌──────────────────────────────────────────────────────────┐
│ ingestion_feeds                                           │
│                                                          │
│  sync_mode (VARCHAR)  ─────┐                              │
│  interval_minutes (INT) ───┤                              │
│  max_retries (INT) ────────┤                              │
│  backoff_multiplier (FLT) ─┤─── composite() ──▶ SyncPolicy│
│  max_backoff_minutes (INT)─┤                              │
│  timeout_seconds (INT) ────┤                              │
│  max_items_per_run (INT) ──┘                              │
└──────────────────────────────────────────────────────────┘
```

**Requisito**: El orden de columnas en `composite()` debe coincidir con el orden de parámetros de `SyncPolicy.__init__`:

```python
# SyncPolicy.__init__ signature:
def __init__(self, mode, interval_minutes=None, max_retries=3,
             backoff_multiplier=2.0, max_backoff_minutes=60,
             timeout_seconds=30, max_items_per_run=100):
```

**Ventajas del composite**:
- `FeedModel.sync_policy` es un `SyncPolicy` real con métodos de dominio.
- La validación del VO se ejecuta al cargar desde DB (defensa en profundidad).
- El VO es inmutable — no se puede modificar accidentalmente.
- Se puede acceder a campos individuales: `feed.sync_policy.mode`.
- Se puede actualizar todo el VO: `feed.sync_policy = new_policy`.

**Actualización parcial**: No se permite actualizar campos individuales de SyncPolicy. Siempre se reemplaza el VO completo:

```python
# ✅ Correcto: reemplazo completo
feed.update_sync_policy(SyncPolicy(mode=SyncMode.PULL, interval_minutes=15))

# ❌ Incorrecto: modificación directa de campos
feed.sync_policy.interval_minutes = 15  # SyncPolicy es frozen!
```

**Sincronización con DB**: SQLAlchemy `composite()` maneja la descomposición automáticamente. Al asignar un nuevo `SyncPolicy`, las 7 columnas se actualizan en el próximo flush.

---

## 3. Enum Mapping

| Enum | Tipo Python | Almacenamiento | Valores |
|---|---|---|---|
| `SourceType` | `str, Enum` | VARCHAR(20) | RSS, API, SOCIAL_MEDIA, NEWSLETTER |
| `SyncMode` | `str, Enum` | VARCHAR(20) | PULL, PUSH, STREAM, MANUAL |

**Decisión: VARCHAR sobre ENUM nativo.**

Justificación completa en `persistence-design.md` §3 Decisión E-02. Resumen:

1. **Portabilidad**: SQLite no soporta ENUM. Testing con el mismo schema.
2. **Evolución**: Agregar `NEWSLETTER` o `STREAM` no requiere `ALTER TYPE ... ADD VALUE`.
3. **Simplicidad**: El TypeDecorator encapsula la conversión. El enum en Python es type-safe.

**Mapeo bidireccional**:

```
DB: VARCHAR ──▶ TypeDecorator ──▶ Python str, Enum
     'RSS'                       SourceType.RSS
     'PUSH'                      SyncMode.PUSH

Python str, Enum ──▶ TypeDecorator ──▶ DB: VARCHAR
     SourceType.RSS                'RSS'
     SyncMode.PUSH                 'PUSH'
```

**Validación en carga**: Si la DB tiene `'INVALID'`, `SourceType('INVALID')` lanza `ValueError`. Esto rompe rápido y detecta corrupción de datos.

---

## 4. JSON Columns

| Columna | Tabla | Tipo DB | Tipo Python | Nulo | Defecto |
|---|---|---|---|---|---|
| `metadata` | `ingestion_raw_articles` | JSONB (PG) / TEXT (SQLite) | `dict` | NO | `'{}'` |

**Propósito**: `metadata` almacena datos opacos del proveedor externo. No tiene schema fijo porque cada fuente (Reddit, Steam, RSS) envía campos diferentes.

**Por qué JSON y no una tabla EAV o columnas separadas**:
- **Sin queries sobre metadata**: No se consulta por claves internas. Solo se almacena y se recupera como blob.
- **Volumen**: Cada RawArticle tiene metadata diferente. Columnas separadas serían mayormente NULL.
- **Evolución**: Nuevos proveedores agregan campos sin migración.

**Mapeo en SQLAlchemy**:

```python
from sqlalchemy import JSON

class RawArticleModel(Base):
    __tablename__ = "ingestion_raw_articles"

    metadata: Mapped[dict] = mapped_column(
        JSON(none_as_null=False),  # No convertir {} a NULL
        nullable=False,
        server_default="{}",
        default=dict,
    )
```

**`none_as_null=False`**: Queremos que `{}` vacío se almacene como `'{}'`, no como NULL. La columna es NOT NULL.

**Compatibilidad SQLite**: SQLAlchemy mapea `JSON` → `TEXT` en SQLite. La serialización/deserialización la maneja SQLAlchemy automáticamente.

**Defecto en dos niveles**:
- `server_default="{}"` → Si se inserta desde SQL directo, el default es `'{}'`.
- `default=dict` → Si se crea el modelo desde Python sin metadata, se usa `dict()`.

---

## 5. Relationship Configuration

### 5.1 NewsSource → Feeds (1:N)

| Propiedad | Valor |
|-----------|-------|
| **Dirección** | NewsSource → Feeds (1:N) |
| **Tipo** | AR → AR (relación entre aggregates) |
| **Carga** | `lazy="select"` (lazy, diferida) |
| **Cascade ORM** | `save-update, merge` (sin `delete`) |
| **Cascade BD** | `ON DELETE CASCADE` |
| **`viewonly`** | `True` |
| **FK del lado** | `ingestion_feeds.source_id` |

```python
class NewsSourceModel(Base):
    __tablename__ = "ingestion_news_sources"

    feeds: Mapped[list[FeedModel]] = relationship(
        back_populates="source",
        lazy="select",
        cascade="save-update, merge",
        viewonly=True,
    )

class FeedModel(Base):
    __tablename__ = "ingestion_feeds"

    source_id: Mapped[SourceId] = mapped_column(
        EntityIdType(SourceId),
        ForeignKey("ingestion_news_sources.id", ondelete="CASCADE"),
        nullable=False,
    )

    source: Mapped[NewsSourceModel] = relationship(
        back_populates="feeds",
        lazy="joined",  # El source padre se carga siempre con el feed
        viewonly=True,
    )
```

**Justificación de `viewonly=True`**: La mutación de la relación (asignar un feed a un source) se hace a través del repositorio, no manipulando colecciones ORM. El `viewonly` previene que SQLAlchemy intente sincronizar la colección automáticamente.

**Justificación de `lazy="joined"` en Feed→Source**: Cuando se carga un Feed, casi siempre se necesita conocer su NewsSource padre (para mostrar en UI, para verificar AL rules). Un JOIN adicional es aceptable. Para queries batch, se puede override con `selectinload()`.

---

### 5.2 Feed → RawArticles (1:N)

| Propiedad | Valor |
|-----------|-------|
| **Dirección** | Feed → RawArticles (1:N) |
| **Tipo** | AR → AR (relación entre aggregates) |
| **Relación ORM** | **NO EXISTE** |
| **Carga** | N/A — siempre paginada vía repositorio |

**NO se mapea una relación ORM de Feed a RawArticles por decisión arquitectónica.**

Razones:
- RawArticle puede tener millones de instancias por Feed. Cualquier acceso accidental a `feed.raw_articles` sería catastrófico.
- Toda carga de RawArticles es paginada explícitamente vía `RawArticleRepository.find_by_feed(feed_id, page, size)`.
- La FK `feed_id` en `ingestion_raw_articles` existe solo para integridad referencial y queries del repositorio.

**Alternativa descartada — `lazy="dynamic"`**: Obsoleto en SQLAlchemy 2.x. Además, `dynamic` aún permite `feed.raw_articles.all()` que carga todo. El riesgo de error humano es demasiado alto.

**Cómo se accede a RawArticles desde el dominio**:

```python
# ✅ En un Application Service:
class CollectArticlesUseCase:
    def execute(self, cmd: CollectCommand):
        feed = self._feed_repo.find_by_id(cmd.feed_id)  # Carga Feed
        articles = self._article_repo.find_by_feed(      # Carga RawArticles paginados
            feed_id=cmd.feed_id,
            page=1,
            size=50,
        )
```

---

### 5.3 Category → parent/children (self-ref)

| Propiedad | Valor |
|-----------|-------|
| **Dirección** | Category → parent (self-ref N:1) |
| **Carga (parent)** | `lazy="joined"` |
| **Dirección** | Category → children (self-ref 1:N) |
| **Carga (children)** | No mapeada como relación (usar `find_by_parent()`) |
| **Cascade BD** | `ON DELETE SET NULL` |
| **FK** | `ingestion_categories.parent_id` |

```python
class CategoryModel(Base):
    __tablename__ = "ingestion_categories"

    parent_id: Mapped[CategoryId | None] = mapped_column(
        EntityIdType(CategoryId),
        ForeignKey("ingestion_categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Solo relación al padre (no a hijos)
    parent: Mapped[CategoryModel | None] = relationship(
        remote_side="CategoryModel.id",
        lazy="joined",
        viewonly=True,
    )
```

**¿Por qué no relación a children?** La colección de hijos se accede exclusivamente vía `CategoryRepository.find_by_parent()`. No hay operación de dominio que requiera `category.children` — las invariantes de cascade (I-21) se verifican en Application Layer consultando el repositorio.

**`remote_side`**: SQLAlchemy necesita saber qué lado de la self-referencia es el "remoto" (padre). `remote_side="CategoryModel.id"` indica que `parent_id` apunta a `id` de otra fila.

---

### 5.4 — 5.7 M:N Relationships

Todas las relaciones M:N siguen el mismo patrón:

| Propiedad | Valor |
|-----------|-------|
| **Carga** | `lazy="selectin"` |
| **`viewonly`** | `True` |
| **Cascade BD** | `ON DELETE CASCADE` en ambos FKs |
| **Tabla asociada** | `Table` (no clase modelo) |

#### 5.4 NewsSource ↔ Category

```python
news_source_category_table = Table(
    "ingestion_news_source_categories",
    Base.metadata,
    Column("source_id", EntityIdType(SourceId),
           ForeignKey("ingestion_news_sources.id", ondelete="CASCADE"),
           primary_key=True),
    Column("category_id", EntityIdType(CategoryId),
           ForeignKey("ingestion_categories.id", ondelete="CASCADE"),
           primary_key=True),
)

class NewsSourceModel(Base):
    categories: Mapped[list[CategoryModel]] = relationship(
        secondary=news_source_category_table,
        lazy="selectin",
        viewonly=True,
    )
```

#### 5.5 NewsSource ↔ Topic

```python
news_source_topic_table = Table(
    "ingestion_news_source_topics",
    Base.metadata,
    Column("source_id", EntityIdType(SourceId),
           ForeignKey("ingestion_news_sources.id", ondelete="CASCADE"),
           primary_key=True),
    Column("topic_id", EntityIdType(TopicId),
           ForeignKey("ingestion_topics.id", ondelete="CASCADE"),
           primary_key=True),
)

class NewsSourceModel(Base):
    topics: Mapped[list[TopicModel]] = relationship(
        secondary=news_source_topic_table,
        lazy="selectin",
        viewonly=True,
    )
```

#### 5.6 Feed ↔ Category

```python
feed_category_table = Table(
    "ingestion_feed_categories",
    Base.metadata,
    Column("feed_id", EntityIdType(FeedId),
           ForeignKey("ingestion_feeds.id", ondelete="CASCADE"),
           primary_key=True),
    Column("category_id", EntityIdType(CategoryId),
           ForeignKey("ingestion_categories.id", ondelete="CASCADE"),
           primary_key=True),
)

class FeedModel(Base):
    categories: Mapped[list[CategoryModel]] = relationship(
        secondary=feed_category_table,
        lazy="selectin",
        viewonly=True,
    )
```

#### 5.7 Feed ↔ Topic

```python
feed_topic_table = Table(
    "ingestion_feed_topics",
    Base.metadata,
    Column("feed_id", EntityIdType(FeedId),
           ForeignKey("ingestion_feeds.id", ondelete="CASCADE"),
           primary_key=True),
    Column("topic_id", EntityIdType(TopicId),
           ForeignKey("ingestion_topics.id", ondelete="CASCADE"),
           primary_key=True),
)

class FeedModel(Base):
    topics: Mapped[list[TopicModel]] = relationship(
        secondary=feed_topic_table,
        lazy="selectin",
        viewonly=True,
    )
```

**¿Por qué `selectin` y no `joined`?**

La relación M:N entre dos tablas con `joined` generaría un LEFT JOIN que, combinado con otras relaciones, puede causar **cartesian explosion** (filas duplicadas). `selectin` emite una segunda query:

```sql
-- selectin: 2 queries simples
SELECT * FROM ingestion_news_sources WHERE ...;
SELECT * FROM ingestion_categories WHERE id IN (SELECT category_id FROM ingestion_news_source_categories WHERE source_id IN (...));
```

Para colecciones pequeñas (<50 elementos), `selectin` es igual o más rápido que `joined`, y evita la explosion cartesiana.

---

## 6. Table Naming Convention

### 6.1 Convención General

| Elemento | Formato | Ejemplo |
|---|---|---|
| **Tablas** | `ingestion_{plural_noun}` | `ingestion_news_sources`, `ingestion_feeds` |
| **Columnas PK** | `id` | `id` |
| **Columnas FK** | `{referenced_table_singular}_id` | `source_id`, `feed_id`, `parent_id` |
| **Columnas booleanas** | `is_{adjective}` | `is_active` |
| **Columnas datetime** | `{event}_at` | `created_at`, `fetched_at`, `published_at`, `updated_at` |
| **Columnas string** | `{descriptive_name}` | `name`, `slug`, `label`, `external_id` |
| **Columnas numéricas** | `{descriptive_name}` | `retry_count`, `max_retries`, `version` |
| **Columnas enum** | `{entity}_{field}` | `source_type`, `sync_mode` |
| **Columnas composite VO** | prefijo `{vo_context}_` | `sync_mode`, `interval_minutes`, `max_retries`, etc. |

### 6.2 Nombres de Constraints

| Tipo | Prefijo | Formato | Ejemplo |
|---|---|---|---|
| **Primary Key** | — | `{table}_pkey` (automático) | — |
| **Foreign Key** | `fk_` | `fk_{child}_{parent}` | `fk_feed_source`, `fk_nsc_category` |
| **Unique** | `uq_` | `uq_{table}_{fields}` | `uq_news_source_name`, `uq_feed_source_url` |
| **Check** | `ck_` | `ck_{table}_{rule}` | `ck_raw_article_hash_length`, `ck_category_no_self_parent` |
| **Index** | `ix_` | `ix_{table}_{fields}` | `ix_raw_articles_feed_fetched`, `ix_feeds_source_active` |

### 6.3 Nombres de Columnas — Mapeo Dominio → DB

| Dominio (Python) | DB (columna) | Razón |
|---|---|---|
| `NewsSource.id` | `id` | Convención universal |
| `NewsSource.name` | `name` | 1:1 |
| `NewsSource.source_type` | `source_type` | Prefijo `source_` desambigua (Type vs otras cosas) |
| `NewsSource.source_url` | `source_url` | Prefijo `source_` |
| `Feed.url` | `url` | 1:1 |
| `Feed.label` | `label` | 1:1 |
| `Feed.sync_policy.mode` | `sync_mode` | Prefijo `sync_` para agrupar campos de SyncPolicy |
| `Feed.sync_policy.interval_minutes` | `interval_minutes` | Sin prefijo `sync_` por brevedad y porque está en contexto de sync |
| `RawArticle.external_id` | `external_id` | 1:1 |
| `RawArticle.content_hash` | `content_hash` | 1:1 |
| `RawArticle.fetched_at` | `fetched_at` | 1:1 |
| `Category.name` | `name` | 1:1 |
| `Topic.name` | `name` | 1:1 |

---

## 7. Base ORM Infrastructure

### 7.1 DeclarativeBase

```python
"""
Base ORM compartida para el BC Ingestion.

TODOS los modelos ORM del BC Ingestion heredan de esta clase.
NO se mezclan con modelos de otros BCs en la misma Base.
"""

from sqlalchemy.orm import DeclarativeBase


class IngestionBase(DeclarativeBase):
    """Base declarativa para modelos del BC Ingestion.

    Attributes:
        metadata: Metadata de SQLAlchemy para el BC Ingestion.
                  Aislada de otros BCs (Research, Script) que
                  tienen su propia Base.
    """

    @classmethod
    def get_tablename(cls, entity_name: str) -> str:
        """Genera el nombre de tabla siguiendo la convención.

        Uso:
            >>> IngestionBase.get_tablename("news_source")
            'ingestion_news_sources'
        """
        return f"ingestion_{entity_name}s"
```

**¿Por qué una Base separada para Ingestion?**

- **Aislamiento**: Cada BC tiene su propio `metadata`. Esto permite crear tablas por BC (útil en tests).
- **Migraciones**: Alembic puede diferenciar qué tablas pertenecen a qué BC.
- **Testing**: Se puede crear `IngestionBase.metadata.create_all(bind=test_engine)` sin crear tablas de otros BCs.

### 7.2 Registry and Naming Conventions

```python
"""
Convention for automatic constraint naming.

SQLAlchemy 2.x puede generar nombres de constraints automáticamente
si se configura el naming convention en el registry. Esto asegura
nombres consistentes sin declararlos explícitamente en cada modelo.
"""

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

IngestionBase.metadata.naming_convention = convention
```

**Ventaja**: No es necesario escribir `__table_args__` con nombres de constraints en cada modelo. SQLAlchemy los genera automáticamente con nombres consistentes.

### 7.3 Engine Configuration

```python
"""
Configuración del Engine para el BC Ingestion.

Producción: PostgreSQL con asyncpg (futuro) o psycopg2 (sync).
Testing: SQLite en memoria.
"""

from sqlalchemy import create_engine


def create_ingestion_engine(
    database_url: str,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
) -> Engine:
    """Crea un engine configurado para Ingestion.

    Args:
        database_url: URL de conexión (postgresql://... o sqlite://).
        echo: Log de SQL (para debugging).
        pool_size: Tamaño del pool de conexiones (solo PostgreSQL).
        max_overflow: Conexiones extra bajo demanda (solo PostgreSQL).

    Returns:
        Engine de SQLAlchemy configurado.

    Nota:
        SQLite ignora pool_size y max_overflow (no tiene pooling).
    """
    return create_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,  # Verificar conexión antes de usar
        pool_size=pool_size if "sqlite" not in database_url else None,
        max_overflow=max_overflow if "sqlite" not in database_url else None,
    )
```

**Pool de conexiones**:
- **PostgreSQL**: `pool_pre_ping=True` evita usar conexiones stale (caídas por timeout). Pool de 5 conexiones con 10 extras bajo demanda.
- **SQLite**: No tiene pooling. `pool_pre_ping` es innecesario pero inocuo.

### 7.4 Session Factory

```python
"""
Session factory para el BC Ingestion.

Produce sesiones con autocommit=False y autoflush=False.
El Application Service (UoW) controla el commit/rollback explícitamente.
"""

from sqlalchemy.orm import sessionmaker


def create_ingestion_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Crea una session factory configurada para Ingestion.

    Configuración:
        - autocommit=False: El commit es explícito (UoW pattern).
        - autoflush=False: No flush automático antes de queries.
          El repositorio hace flush cuando es necesario.

    Returns:
        sessionmaker que produce sesiones listas para usar.
    """
    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )
```

**`autocommit=False`**: Obligatorio para el patrón UoW. El Application Service inicia una transacción (implícitamente al obtener la sesión), ejecuta operaciones, y hace commit/rollback explícitamente.

**`autoflush=False`**: Prevenimos flushes automáticos antes de cada query. El repositorio llama `session.flush()` cuando necesita asegurar que los cambios pendientes estén visibles para la misma transacción (ej: verificar unicidad antes de insertar).

**Integración con el UnitOfWork existente**:

El `UoW` actual (ver `src/ingestion/infrastructure/inmemory/unit_of_work.py`) se adaptará para usar la sesión SQLAlchemy:

```python
class SQLAlchemyUnitOfWork:
    """UnitOfWork basado en SQLAlchemy Session.

    Uso:
        with SQLAlchemyUnitOfWork(session_factory) as uow:
            source_repo.save(source)
            feed_repo.save(feed)
            uow.commit()  # session.commit()
    """

    def __init__(self, session_factory: sessionmaker):
        self._session_factory = session_factory
        self._session: Session | None = None

    def __enter__(self) -> SQLAlchemyUnitOfWork:
        self._session = self._session_factory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._session.rollback()
        self._session.close()

    def commit(self):
        self._session.commit()

    @property
    def session(self) -> Session:
        return self._session
```

---

## 8. Repository Implementation Strategy

### 8.1 Patrón Base de Repositorio SQLAlchemy

Cada repositorio SQLAlchemy implementa el Protocol correspondiente usando una sesión SQLAlchemy:

```python
class SQLAlchemyNewsSourceRepository:
    """Implementación SQLAlchemy de NewsSourceRepository.

    Recibe una sesión del UoW. No maneja commits — eso es
    responsabilidad del Application Service.
    """

    def __init__(self, session: Session):
        self._session = session

    def save(self, source: NewsSource) -> None:
        """Persiste un NewsSource.

        Convierte dominio → ORM, hace merge/upsert.
        """
        # Convertir dominio a ORM model
        model = self._domain_to_model(source)
        # Merge: si existe (por PK), actualiza; si no, inserta
        self._session.merge(model)

    def find_by_id(self, id: SourceId) -> Result[NewsSource]:
        """Busca por SourceId."""
        model = self._session.get(NewsSourceModel, id)
        if model is None:
            return Result.failure(Error(
                code=IngestionErrorCode.NEWS_SOURCE_NOT_FOUND,
                message=f"Source '{id}' not found",
            ))
        return Result.success(self._model_to_domain(model))
```

**Patrón `session.merge()`**:
- **Ventaja**: Un solo método para insertar y actualizar. SQLAlchemy detecta si la PK existe y hace INSERT o UPDATE automáticamente.
- **Riesgo**: Merge puede hacer SELECT antes de INSERT/UPDATE (para verificar existencia). Para RawArticle (altas inserciones), considerar `session.add()` + `session.flush()` con manejo explícito de `IntegrityError`.

### 8.2 Mapeo ORM ↔ Domain

Cada repositorio implementa dos métodos privados para la conversión bidireccional:

```python
class SQLAlchemyNewsSourceRepository:
    # ── Domain → ORM ──────────────────────────────────

    def _domain_to_model(self, source: NewsSource) -> NewsSourceModel:
        """Convierte NewsSource (domain) → NewsSourceModel (ORM)."""
        return NewsSourceModel(
            id=source.id,
            name=source.name,
            source_type=source.source_type,
            source_url=source.source_url,
            is_active=source.is_active,
            version=source.version if hasattr(source, 'version') else 1,
            # SyncState: created_at y updated_at los maneja el modelo
        )

    # ── ORM → Domain ──────────────────────────────────

    def _model_to_domain(self, model: NewsSourceModel) -> NewsSource:
        """Convierte NewsSourceModel (ORM) → NewsSource (domain).

        NOTA: Los TypeDecorators ya convirtieron las columnas
        a tipos de dominio (SourceId, SourceUrl, etc.).
        Solo necesitamos construir el objeto de dominio.
        """
        source = NewsSource(
            id=model.id,              # Ya es SourceId (TypeDecorator)
            name=model.name,          # str
            source_type=model.source_type,  # Ya es SourceType (TypeDecorator)
            source_url=model.source_url,    # Ya es SourceUrl (TypeDecorator)
            is_active=model.is_active,
            categories=model.categories,  # Ya es list[CategoryId]
            topics=model.topics,          # Ya es list[TopicId]
        )
        return source
```

**M:N relationships** — Sincronización en `save()`:

```python
def _sync_associations(self, source: NewsSource, model: NewsSourceModel) -> None:
    """Sincroniza las listas de IDs de categorías y topics con las tablas M:N.

    Estrategia:
        1. Obtener IDs actuales del modelo de dominio (source.categories).
        2. Obtener registros actuales en DB (model.categories).
        3. Calcular diff: eliminar los que sobran, insertar los que faltan.

    Simplificación: Eliminar todos y reinsertar (OK para colecciones pequeñas).
    """
    # Eliminar asociaciones existentes
    self._session.execute(
        news_source_category_table.delete().where(
            news_source_category_table.c.source_id == source.id
        )
    )
    # Insertar nuevas
    for cat_id in source.categories:
        self._session.execute(
            news_source_category_table.insert().values(
                source_id=source.id,
                category_id=cat_id,
            )
        )
```

**¿Por qué delete + reinsert y no diff?**:
- Las M:N son colecciones pequeñas (<50). El costo de diff no justifica el ahorro.
- Simplicidad: el código es trivial y correcto.
- `ON DELETE CASCADE` no aplica aquí porque no borramos las categorías/topics, solo las relaciones.

### 8.3 Manejo de Duplicados en RawArticle

RawArticle tiene dos UNIQUE constraints compuestas:
- `(feed_id, external_id)` — I-12
- `(feed_id, content_hash)` — I-13

El repositorio debe detectar violaciones y convertirlas en `DUPLICATE_ARTICLE`:

```python
class SQLAlchemyRawArticleRepository:
    def save(self, article: RawArticle) -> None:
        """Persiste un RawArticle. Detecta duplicados vía UNIQUE constraints."""
        try:
            self._session.add(self._domain_to_model(article))
            self._session.flush()  # Forzar inserción para detectar duplicados
        except IntegrityError as e:
            self._session.rollback()  # Rollback de la operación fallida
            raise InvalidStateError(
                f"DUPLICATE_ARTICLE: {self._analyze_duplicate(e, article)}"
            ) from e

    def _analyze_duplicate(self, error: IntegrityError, article: RawArticle) -> str:
        """Analiza qué constraint de unicidad se violó.

        Examina el mensaje de error para determinar si fue
        external_id+feed_id o content_hash+feed_id.
        """
        msg = str(error).lower()
        if "uq_raw_article_feed_external" in msg:
            return f"external_id '{article.external_id}' already exists in feed '{article.feed_id}'"
        if "uq_raw_article_feed_hash" in msg:
            return f"content_hash '{article.content_hash}' already exists in feed '{article.feed_id}'"
        return str(error)
```

**`flush()` después de `add()`**: Sin flush, el `IntegrityError` solo ocurriría en `commit()`, que está fuera del repositorio (en el UoW). Haciendo flush explícito, capturamos el error dentro del repositorio y podemos devolver un error semántico (`DUPLICATE_ARTICLE`) en lugar de un error genérico de integridad.

**Rollback parcial**: `session.rollback()` revierte SOLO la operación que falló (savepoint implícito), sin afectar otras operaciones en la misma transacción. Esto permite `save_batch()`:
- Si el artículo 5 de 10 es duplicado, se revierte solo el artículo 5.
- Los artículos 1-4 y 6-10 se pueden reintentar individualmente.

**`save_batch()`**:
```python
def save_batch(self, articles: list[RawArticle]) -> None:
    """Persiste múltiples RawArticles.

    Usa savepoints para atomicidad: o todos o ninguno.
    Pero ante DUPLICATE_ARTICLE, falla todo el batch.
    """
    try:
        for article in articles:
            self._session.add(self._domain_to_model(article))
        self._session.flush()
    except IntegrityError:
        self._session.rollback()
        raise InvalidStateError("DUPLICATE_ARTICLE: One or more articles are duplicates")
```
