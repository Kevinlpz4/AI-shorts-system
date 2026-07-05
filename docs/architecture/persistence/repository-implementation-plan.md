# Repository Implementation Plan — EPIC 5

> **Estrategia detallada de implementación de los 5 repositorios SQLAlchemy**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-05
> Basado en: Persistence Design v1.0, ORM Mapping Strategy v1.0,
> Repository Contracts v1.0, Transaction Boundaries v1.0
>
> **Este documento especifica la estrategia de implementación de CADA repositorio.
> NO implementa código SQLAlchemy ejecutable. NO modifica Foundation/Domain/Application.**

---

## Índice

1. [Common Patterns](#1-common-patterns)
    - 1.1 [Session Management](#11-session-management)
    - 1.2 [Error Mapping & Domain Exceptions](#12-error-mapping--domain-exceptions)
    - 1.3 [M:N Synchronization Strategy](#13-mn-synchronization-strategy)
    - 1.4 [Optimistic Locking & Version Handling](#14-optimistic-locking--version-handling)
    - 1.5 [Timestamps: created_at / updated_at](#15-timestamps-created_at--updated_at)
    - 1.6 [Domain ↔ ORM Mapping Methods](#16-domain--orm-mapping-methods)
    - 1.7 [Base Repository Pattern](#17-base-repository-pattern)
2. [NewsSourceRepository](#2-newssourcerepository)
3. [FeedRepository](#3-feedrepository)
4. [RawArticleRepository](#4-rawarticlerepository)
5. [CategoryRepository](#5-categoryrepository)
6. [TopicRepository](#6-topicrepository)

---

## 1. Common Patterns

### 1.1 Session Management

**Estrategia: Session compartida vía UnitOfWork.**

- Los repositorios **NO crean sesiones**. Reciben la sesión por constructor.
- La sesión es creada por el `UnitOfWork` al entrar al context manager (`__enter__`).
- Todos los repositorios dentro de una transacción comparten la **misma** sesión.
- El repositorio nunca hace `session.commit()` ni `session.close()`. Solo usa `session.execute()`, `session.add()`, `session.merge()`, `session.flush()`, y `session.get()`.
- `autoflush=False` en la sesión: el repositorio controla explícitamente cuándo hacer flush.

```python
# Constructor pattern para todos los repositorios:
class SQLAlchemyNewsSourceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session
```

**¿Session per operation vs Session per UnitOfWork?**

| Opción | Decisión |
|--------|----------|
| **✅ Session per UnitOfWork (compartida)** | SELECCIONADO. Todos los repositorios reciben la misma sesión del UoW. Atomicidad real: múltiples saves en un solo commit. |
| ❌ Session per operation | Cada `save()` abre y cierra su propia sesión. Sin atomicidad entre repositorios. No permite transacciones multi-aggregate. |

**¿Qué pasa con las queries (solo lectura)?**

Las queries no usan UnitOfWork. Pueden usar:
1. **Una sesión efímera** creada directamente desde `sessionmaker` para cada query.
2. **Sesión explícita** inyectada por un Query Handler si necesita eager loading.

Para la implementación inicial, las queries de solo lectura crean su propia sesión del `sessionmaker`. No necesitan transaccionalidad.

**Integración con el Query Stack Pattern**:

```python
# En repositories.py (lectura):
class SQLAlchemyRawArticleRepository:
    def find_by_feed(self, feed_id: FeedId, page: int = 1, size: int = 50) -> list[RawArticle]:
        stmt = (
            select(RawArticleModel)
            .where(RawArticleModel.feed_id == feed_id)
            .order_by(RawArticleModel.fetched_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]
```

**No usar `session.get()` con `populate_existing` a menos que se necesite**: La sesión cachea objetos. Para queries de lectura, el cache de primer nivel es beneficioso. Para casos donde se necesita datos frescos (ej: verificación de unicidad), se puede usar `session.refresh()` o una query directa.

---

### 1.2 Error Mapping & Domain Exceptions

**Patrón general: capturar `IntegrityError` de SQLAlchemy y convertirlo a error de dominio.**

```python
from sqlalchemy.exc import IntegrityError
from ingestion.domain.exceptions import InvalidStateError
from ingestion.domain.exceptions.errors import IngestionErrorCode

class IntegrityHandler:
    """Mapea IntegrityError de SQLAlchemy a errores de dominio."""

    @staticmethod
    def handle_unique_violation(
        error: IntegrityError,
        entity_name: str,
        field: str,
        value: str,
        error_code: IngestionErrorCode,
    ) -> InvalidStateError:
        """Convierte una violación de UNIQUE constraint en InvalidStateError."""
        return InvalidStateError(
            f"{error_code.value}: {entity_name} with {field} '{value}' already exists"
        )

    @staticmethod
    def handle_fk_violation(
        error: IntegrityError,
        fk_name: str,
        entity_name: str,
    ) -> InvalidStateError:
        """Convierte una violación de FK en InvalidStateError."""
        return InvalidStateError(
            f"FK_VIOLATION: Referenced {entity_name} not found ({fk_name})"
        )
```

**Mapeo específico por repositorio**:

| Repositorio | Constraint violada | Error Code | Acción |
|---|---|---|---|
| NewsSourceRepository | `uq_news_source_name` | `DUPLICATE_NEWS_SOURCE` | Rollback savepoint + propagar |
| FeedRepository | `uq_feed_source_url` | `DUPLICATE_FEED_URL` | Rollback savepoint + propagar |
| RawArticleRepository | `uq_raw_article_feed_external` | `DUPLICATE_ARTICLE` | Rollback savepoint + propagar |
| RawArticleRepository | `uq_raw_article_feed_hash` | `DUPLICATE_ARTICLE` | Rollback savepoint + propagar |
| CategoryRepository | `uq_category_slug` | `CATEGORY_NOT_FOUND` (slug duplicado) | Rollback + propagar |
| TopicRepository | `uq_topic_name` | `TOPIC_NOT_FOUND` (name duplicado) | Rollback + propagar |

**Estrategia de detección de constraint violada**: parsear el mensaje de error de la BD.

```python
# Driver PostgreSQL:
#   DETAIL:  Key (name)=(MiSource) already exists.
# Driver SQLite:
#   UNIQUE constraint failed: ingestion_news_sources.name

def _is_unique_violation(error: IntegrityError, constraint_name: str) -> bool:
    """Verifica si el IntegrityError es por una constraint específica."""
    msg = str(error.orig).lower()
    if "postgresql" in str(type(error.orig)).lower():
        return constraint_name.lower() in msg
    # SQLite
    return constraint_name.lower().replace("_", " ") in msg
```

**StaleDataError (optimistic lock)**:

```python
from sqlalchemy.orm.exc import StaleDataError

# Se captura en el UnitOfWork.commit(), no en el repositorio.
# El repositorio solo hace session.merge() — el check de version
# ocurre en el flush/commit.
```

Ver sección 1.4 para el manejo completo.

**Excepciones vs Result[T]**:

| Capa | Mecanismo |
|------|-----------|
| **Infrastructure (repositorio)** | Lanza excepciones (Python exceptions) para errores de integridad, concurrencia, conexión. **NO** retorna `Result[T]`. |
| **Application (service)** | Captura las excepciones del repositorio y las mapea a `Result.failure()` con los códigos de dominio. |

Esto es intencional: el repositorio (infrastructure) no sabe de `Result[T]`. Usa el mecanismo de error estándar de Python. El Application Service es el orquestador que traduce errores de infraestructura a errores de dominio.

---

### 1.3 M:N Synchronization Strategy

**Estrategia: DELETE + INSERT (no diff).**

Para las 4 tablas M:N:
- `ingestion_news_source_categories`
- `ingestion_news_source_topics`
- `ingestion_feed_categories`
- `ingestion_feed_topics`

```python
def _sync_many_to_many(
    session: Session,
    association_table: Table,
    owner_id_column,
    owner_id: EntityId,
    related_ids: list[EntityId],
    related_id_column,
) -> None:
    """Sincroniza una relación M:N eliminando y reinsertando.

    Args:
        session: Sesión SQLAlchemy compartida.
        association_table: Tabla de asociación (Table, no modelo).
        owner_id_column: Columna FK del owner (ej: news_source_categories.c.source_id).
        owner_id: ID del owner.
        related_ids: Lista de IDs de las entidades relacionadas.
        related_id_column: Columna FK de la entidad relacionada.

    NOTA: Esto NO es un diff. Elimina TODO y reinserta TODO.
    Es correcto porque las colecciones son pequeñas (<50 elementos).
    """
    # Eliminar todas las relaciones existentes del owner
    delete_stmt = association_table.delete().where(
        owner_id_column == owner_id
    )
    session.execute(delete_stmt)

    # Reinsertar todas las relaciones actuales
    for rid in related_ids:
        insert_stmt = association_table.insert().values(
            {owner_id_column: owner_id, related_id_column: rid}
        )
        session.execute(insert_stmt)
```

**¿Por qué DELETE + INSERT y no diff?**

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| **✅ DELETE + INSERT** | Simple, correcto, predecible. 2 queries siempre. Las M:N son colecciones pequeñas (<50). El costo de DELETE + INSERT de 50 filas es insignificante. | **SELECCIONADO** |
| ❌ Diff (comparar sets) | Más queries de lectura (SELECT existentes). Código más complejo. Para colecciones pequeñas, el ahorro de escritura es despreciable. | Descartado |
| ❌ `relationship()` con `viewonly=False` | SQLAlchemy sincronizaría automáticamente, pero con `viewonly=True` (decidido en ORM Mapping Strategy) no podemos usar esta opción. | Descartado |

**¿Cuándo se sincroniza?**

En el método `save()` de cada repositorio que tenga M:N:
- `NewsSourceRepository.save()` → sincroniza categories y topics
- `FeedRepository.save()` → sincroniza categories y topics
- `CategoryRepository` y `TopicRepository` NO sincronizan (son el lado referenciado, no el owner de las M:N)

**Transaccionalidad**: La sincronización ocurre DENTRO de la misma transacción del UoW. Si el DELETE + INSERT falla, TODO se revierte.

---

### 1.4 Optimistic Locking & Version Handling

**Estrategia: `version_id_col` de SQLAlchemy para NewsSource, Feed, Category, Topic.**

```python
class NewsSourceModel(Base):
    __tablename__ = "ingestion_news_sources"
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __mapper_args__ = {
        "version_id_col": version,
        "version_id_generator": lambda v: (v or 0) + 1,
    }
```

**¿Merge vs Add para save()?**

| Operación | ¿Usa version? | Comportamiento |
|-----------|---------------|----------------|
| **`session.merge(model)`** | ✅ Sí | SQLAlchemy detecta si es INSERT o UPDATE. En UPDATE, incluye `WHERE version = :old`. Si no coincide → `StaleDataError`. |
| **`session.add(model)`** | ❌ No | Siempre asume INSERT. Si la PK ya existe → error. Para entidades nuevas funciona, pero para actualizaciones falla. |

**Decisión: `session.merge()` para NewsSource, Feed, Category, Topic.**

`merge()` es el patrón correcto porque:
1. El repositorio recibe una instancia de entidad de dominio (desconectada del ORM).
2. `merge()` la adjunta a la sesión, detectando si es nueva o existente.
3. Si es existente, genera un UPDATE con `WHERE version = :old`.
4. Si otra sesión modificó la fila, `StaleDataError` en commit.

```python
def save(self, source: NewsSource) -> None:
    model = self._domain_to_model(source)
    self._session.merge(model)
    # StaleDataError ocurrirá en session.commit() (en el UoW),
    # no aquí. El merge solo prepara el objeto.
```

**¿Dónde se captura `StaleDataError`?**

En el **UnitOfWork.commit()**, no en el repositorio:

```python
class SQLAlchemyUnitOfWork:
    def commit(self) -> None:
        try:
            self._session.commit()
        except StaleDataError as e:
            self._session.rollback()
            raise ConcurrentModificationError(
                f"Optimistic lock conflict: {e}"
            ) from e
```

**RawArticle: sin version (inmutable)**.

RawArticle es inmutable (I-11). Siempre se inserta, nunca se actualiza. Usa `session.add()` + `session.flush()` con manejo de `IntegrityError`. No tiene version column.

---

### 1.5 Timestamps: created_at / updated_at

**`created_at`**: Se asigna UNA VEZ en la creación. Se usa `server_default=func.now()` y también se setea en Python por si el driver no soporta server_default:

```python
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    server_default=func.now(),
    default=lambda: datetime.now(timezone.utc),
)
```

**`updated_at`**: Se actualiza AUTOMÁTICAMENTE en cada UPDATE. Estrategias:

| Opción | Mecanismo | Decisión |
|--------|-----------|----------|
| **✅ Evento `before_update` de SQLAlchemy** | Listener SQLAlchemy que setea `updated_at` antes de cada UPDATE. Funciona hasta que se hace un UPDATE directo desde SQL. | **SELECCIONADO** |
| ✅ **Trigger de BD** | Trigger PostgreSQL `BEFORE UPDATE`. Funciona incluso con SQL directo. Pero no portable a SQLite para testing. | Descartado por testing |
| ❌ **Columna `onupdate=func.now()`** | SQLAlchemy `onupdate` en la columna. Simple, pero se dispara incluso si el valor no cambió realmente. | Descartado por overhead innecesario |

```python
# Listener SQLAlchemy para updated_at automático:
from sqlalchemy import event
from sqlalchemy.orm import Mapper

AUDIT_TABLES = {NewsSourceModel, FeedModel, CategoryModel, TopicModel}

@event.listens_for(Mapper, "before_update")
def set_updated_at(mapper, connection, target) -> None:
    """Actualiza updated_at antes de cada UPDATE si el modelo tiene el campo."""
    if hasattr(target, "updated_at"):
        target.updated_at = datetime.now(timezone.utc)
```

**¿Por qué no `onupdate` en la columna?**

`onupdate` funciona pero se dispara SIEMPRE, incluso si el UPDATE no cambió realmente el valor de la fila. El listener es más eficiente porque se dispara solo en `before_update` real.

**RawArticle**: No tiene `updated_at` (es inmutable). Su `created_at` es el único timestamp.

---

### 1.6 Domain ↔ ORM Mapping Methods

TODOS los repositorios SQLAlchemy implementan dos métodos de conversión:

```python
class SQLAlchemyNewsSourceRepository:
    # ── Domain → ORM ──────────────────────────────────
    def _domain_to_model(self, source: NewsSource) -> NewsSourceModel:
        """Convierte NewsSource (domain) → NewsSourceModel (ORM).

        NOTA: Los TypeDecorators convierten automáticamente los VOs.
        Este método solo pasa los valores del dominio al modelo.
        """
        return NewsSourceModel(
            id=source.id,                        # SourceId → UUID via TypeDecorator
            name=source.name,                    # str directo
            source_type=source.source_type,      # SourceType → VARCHAR via TypeDecorator
            source_url=source.source_url,        # SourceUrl → VARCHAR via TypeDecorator
            is_active=source.is_active,
            # version se maneja automáticamente (merge usa el valor actual)
        )
        # NOTA: Las relaciones M:N (categories, topics) se sincronizan
        # en _sync_associations(), no en el constructor.

    # ── ORM → Domain ──────────────────────────────────
    def _model_to_domain(self, model: NewsSourceModel) -> NewsSource:
        """Convierte NewsSourceModel (ORM) → NewsSource (domain).

        NOTA: Los TypeDecorators ya convirtieron las columnas a tipos de dominio.
        Solo necesitamos construir el objeto de dominio con esos valores.
        """
        return NewsSource(
            id=model.id,                         # Ya es SourceId (TypeDecorator)
            name=model.name,
            source_type=model.source_type,       # Ya es SourceType (TypeDecorator)
            source_url=model.source_url,         # Ya es SourceUrl (TypeDecorator)
            is_active=model.is_active,
            categories=list(model.categories),   # list[CategoryId] desde la relación M:N viewonly
            topics=list(model.topics),           # list[TopicId] desde la relación M:N viewonly
        )
```

**Reglas de conversión**:

1. **Domain → ORM**: Los TypeDecorators convierten automáticamente en `process_bind_param`. El repositorio solo pasa el valor de dominio directamente al constructor del modelo ORM.
2. **ORM → Domain**: Los TypeDecorators convierten automáticamente en `process_result_value`. El repositorio recibe los valores ya convertidos y los pasa al constructor de la entidad de dominio.
3. **SyncPolicy** (Feed): `composite()` maneja automáticamente la conversión entre las 7 columnas y el VO `SyncPolicy`.
4. **Relaciones M:N**: `model.categories` es una `list[Category]` (modelos ORM completos). El repositorio extrae solo los IDs para el dominio: `[cat.id for cat in model.categories]`.

**Diferencia clave entre domain y ORM para M:N**:

- **Domain**: `NewsSource.categories` es `list[CategoryId]` — solo IDs.
- **ORM**: `NewsSourceModel.categories` es `list[CategoryModel]` — modelos completos.

El repositorio es responsable de convertir entre estas representaciones.

---

### 1.7 Base Repository Pattern

**Estrategia: NO hay clase base abstracta. Cada repositorio implementa el Protocol independientemente.**

Razones:
- **YAGNI**: Solo 5 repositorios. Una clase base sería premature abstraction.
- **Simplicidad**: Cada repositorio tiene suficiente singularidad (M:N, batch, paginación) como para justificar implementación separada.
- **Testing**: Sin herencia, cada repositorio se testea de forma aislada sin mockear comportamientos heredados.

**Lo COMPARTIDO** se logra mediante:
1. **Funciones helper** (`_sync_many_to_many`, `_is_unique_violation`) — reutilizables entre repositorios.
2. **Patrones consistentes** (merge, flush, error mapping) — documentados aquí, implementados igual en cada repositorio.
3. **`IntegrityHandler`** — clase estática para mapeo de errores.

```python
# Funciones helper compartidas (en un módulo helper, no en clase base):
# src/ingestion/infrastructure/sqlalchemy/helpers.py

def sync_many_to_many(
    session: Session,
    association_table: Table,
    owner_id_column,
    owner_id: EntityId,
    related_ids: list[EntityId],
    related_id_column,
) -> None: ...

def is_unique_violation(error: IntegrityError, constraint_name: str) -> bool: ...
```

---

## 2. NewsSourceRepository

### 2.1 Resumen

| Aspecto | Detalle |
|---------|---------|
| **Entidad** | `NewsSource` (Aggregate Root) |
| **Modelo ORM** | `NewsSourceModel` |
| **Tabla** | `ingestion_news_sources` |
| **M:N** | Sí: categories, topics |
| **Optimistic Lock** | Sí (version column) |
| **`save()` method** | `session.merge()` |
| **Catálogo** | Pequeño (< 100 registros) |

### 2.2 Métodos

#### `save(source: NewsSource) -> None`

```
1. Convertir dominio → ORM: model = _domain_to_model(source)
2. session.merge(model)
3. Sincronizar M:N: _sync_associations(source)
   └── _sync_many_to_many(session, nsc_table, source_id_col, source.id, source.categories, category_id_col)
   └── _sync_many_to_many(session, nst_table, source_id_col, source.id, source.topics, topic_id_col)

NOTAS:
- merge() detecta INSERT vs UPDATE automáticamente.
- StaleDataError se maneja en UoW.commit(), no aquí.
- Las M:N se sincronizan DESPUÉS del merge (el modelo necesita estar
  adjunto a la sesión antes de ejecutar DELETE en la tabla asociada).
```

**¿Por qué `merge` y no `add`?**

`merge()` es necesario porque el repositorio recibe una instancia de dominio **desconectada** (no asociada a ninguna sesión SQLAlchemy). `merge()` la copia a la sesión actual, detectando si debe hacer INSERT o UPDATE. Con `add()`, si el objeto ya existe en BD, fallaría por PK duplicada.

**M:N synchronization**: Se usa `viewonly=True` en las relaciones ORM, así que el repositorio debe manejar manualmente las tablas de asociación. Se sincroniza DESPUÉS del merge porque el modelo necesita estar adjunto a la sesión para que los queries en la tabla asociada estén dentro de la misma transacción.

**Flujo completo de `save()` con M:N**:

```python
def save(self, source: NewsSource) -> None:
    # 1. Convertir y merge (INSERT o UPDATE)
    model = self._domain_to_model(source)
    merged = self._session.merge(model)

    # 2. Sincronizar M:N (el merged model ya está en la sesión)
    self._sync_associations(source)

def _sync_associations(self, source: NewsSource) -> None:
    """Sincroniza categories y topics del source con las tablas M:N."""
    # Categories
    sync_many_to_many(
        session=self._session,
        association_table=news_source_category_table,
        owner_id_column=news_source_category_table.c.source_id,
        owner_id=source.id,
        related_ids=source.categories,
        related_id_column=news_source_category_table.c.category_id,
    )
    # Topics
    sync_many_to_many(
        session=self._session,
        association_table=news_source_topic_table,
        owner_id_column=news_source_topic_table.c.source_id,
        owner_id=source.id,
        related_ids=source.topics,
        related_id_column=news_source_topic_table.c.topic_id,
    )
```

#### `find_by_id(id: SourceId) -> Result[NewsSource]`

```
1. model = session.get(NewsSourceModel, id)
2. Si model is None → return Result.failure(NEWS_SOURCE_NOT_FOUND)
3. return Result.success(_model_to_domain(model))

NOTAS:
- session.get() usa el cache de primer nivel (identity map).
- Si el modelo ya está en la sesión (por ejemplo, si se cargó antes
  en el mismo UoW), no se hace query a BD.
- Esto es beneficioso: si el service cargó el source al inicio,
  find_by_id en el mismo UoW no hará otra query.
```

#### `find_by_name(name: str) -> Result[NewsSource]`

```
1. stmt = select(NewsSourceModel).where(NewsSourceModel.name == name)
2. model = session.execute(stmt).scalar_one_or_none()
3. Si model is None → return Result.failure(NEWS_SOURCE_NOT_FOUND)
4. return Result.success(_model_to_domain(model))

NOTAS:
- name tiene UNIQUE constraint y es indexed (PK de negocio).
- .scalar_one_or_none() es más seguro que .first():
  - Si hay DUPLICADOS (no debería, pero defensa en profundidad),
    .scalar_one_or_none() lanza MultipleResultsFound.
  - Detectaríamos corrupción de datos temprano.
```

#### `find_all() -> list[NewsSource]`

```
1. stmt = select(NewsSourceModel).order_by(NewsSourceModel.name)
2. models = session.execute(stmt).scalars().all()
3. return [_model_to_domain(m) for m in models]

NOTAS:
- Sin paginación (catálogo pequeño, <100).
- Ordenado por name para consistencia en UI.
```

#### `find_active() -> list[NewsSource]`

```
1. stmt = (
    select(NewsSourceModel)
    .where(NewsSourceModel.is_active == True)
    .order_by(NewsSourceModel.name)
  )
2. models = session.execute(stmt).scalars().all()
3. return [_model_to_domain(m) for m in models]

NOTAS:
- Usa índice ix_news_sources_active.
```

#### `exists_by_name(name: str) -> bool`

```
1. stmt = select(
    session.query(NewsSourceModel)
    .where(NewsSourceModel.name == name)
    .exists()
  )
2. result = session.query(stmt).scalar()
3. return bool(result)

NOTA: Usar EXISTS es más eficiente que traer el registro completo.
Equivalente a: SELECT 1 FROM ingestion_news_sources WHERE name = :name LIMIT 1
```

**Alternativa con `select().limit(1)`**:

```python
# También válida y más legible:
stmt = select(NewsSourceModel.id).where(NewsSourceModel.name == name).limit(1)
result = session.execute(stmt).first()
return result is not None
```

**Decisión**: Usar `.limit(1)` por legibilidad. La diferencia de performance con EXISTS es despreciable para esta tabla pequeña.

---

## 3. FeedRepository

### 3.1 Resumen

| Aspecto | Detalle |
|---------|---------|
| **Entidad** | `Feed` (Aggregate Root) |
| **Modelo ORM** | `FeedModel` |
| **Tabla** | `ingestion_feeds` |
| **M:N** | Sí: categories, topics |
| **Optimistic Lock** | Sí (version column) |
| **`save()` method** | `session.merge()` |
| **Composite VO** | `SyncPolicy` via `composite()` |

### 3.2 Métodos

#### `save(feed: Feed) -> None`

```
1. Convertir dominio → ORM: model = _domain_to_model(feed)
   └── SyncPolicy se descompone automáticamente por composite()
2. session.merge(model)
3. Sincronizar M:N: _sync_associations(feed)
   └── categories: sync_many_to_many(session, fc_table, feed_id_col, ...)
   └── topics: sync_many_to_many(session, ft_table, feed_id_col, ...)
```

**Mapeo de SyncPolicy**: `composite()` maneja la conversión automáticamente:

```python
def _domain_to_model(self, feed: Feed) -> FeedModel:
    return FeedModel(
        id=feed.id,
        source_id=feed.source_id,
        url=feed.url,
        label=feed.label,
        language=feed.language,
        is_active=feed.is_active,
        sync_policy=feed.sync_policy,  # composite() descompone en 7 columnas
        retry_count=feed.retry_count,
    )
```

**¿Composite en `_model_to_domain()`?**

```python
def _model_to_domain(self, model: FeedModel) -> Feed:
    return Feed(
        id=model.id,
        source_id=model.source_id,
        url=model.url,
        label=model.label,
        language=model.language,
        is_active=model.is_active,
        sync_policy=model.sync_policy,  # composite() reconstruye SyncPolicy desde 7 columnas
        categories=[cat.id for cat in model.categories],  # IDs solamente
        topics=[topic.id for topic in model.topics],
        retry_count=model.retry_count,
    )
```

#### `find_by_id(id: FeedId) -> Result[Feed]`

```
1. model = session.get(FeedModel, id)
   └── carga también source (lazy="joined") y M:N (lazy="selectin")
2. Si model is None → return Result.failure(FEED_NOT_FOUND)
3. return Result.success(_model_to_domain(model))
```

#### `find_by_source(source_id: SourceId) -> list[Feed]`

```
1. stmt = (
    select(FeedModel)
    .where(FeedModel.source_id == source_id)
    .order_by(FeedModel.label)
  )
2. models = session.execute(stmt).scalars().all()
3. return [_model_to_domain(m) for m in models]

NOTAS:
- Usa índice ix_feeds_source_active (source_id, is_active).
- No filtra por is_active — retorna todos los feeds del source.
- Ordenado por label para consistencia.
```

#### `find_by_url(source_id: SourceId, url: ArticleUrl) -> Result[Feed]`

```
1. stmt = (
    select(FeedModel)
    .where(FeedModel.source_id == source_id)
    .where(FeedModel.url == url)
  )
2. model = session.execute(stmt).scalar_one_or_none()
3. Si model is None → return Result.failure(FEED_NOT_FOUND)
4. return Result.success(_model_to_domain(model))

NOTAS:
- La UNIQUE compuesta (source_id, url) garantiza que haya 0 o 1 resultado.
- .scalar_one_or_none() detecta duplicados inesperados.
```

#### `find_active_by_source(source_id: SourceId) -> list[Feed]`

```
1. stmt = (
    select(FeedModel)
    .where(FeedModel.source_id == source_id)
    .where(FeedModel.is_active == True)
    .order_by(FeedModel.label)
  )
2. models = session.execute(stmt).scalars().all()
3. return [_model_to_domain(m) for m in models]

NOTAS:
- Cubierto por ix_feeds_source_active (source_id, is_active).
- Usado por AL-01 (verificar que source no tiene feeds activos).
```

#### `exists_by_source_and_url(source_id: SourceId, url: ArticleUrl) -> bool`

```
1. stmt = (
    select(FeedModel.id)
    .where(FeedModel.source_id == source_id)
    .where(FeedModel.url == url)
    .limit(1)
  )
2. result = session.execute(stmt).first()
3. return result is not None
```

#### `count_active_by_source(source_id: SourceId) -> int`

```
1. stmt = (
    select(func.count(FeedModel.id))
    .where(FeedModel.source_id == source_id)
    .where(FeedModel.is_active == True)
  )
2. count = session.execute(stmt).scalar()
3. return count or 0

NOTAS:
- Usa COUNT agregado, no carga filas.
- Cubierto por ix_feeds_source_active.
```

### 3.3 Unique Constraint Handling

**Error**: `DUPLICATE_FEED_URL`

```python
def save(self, feed: Feed) -> None:
    try:
        model = self._domain_to_model(feed)
        self._session.merge(model)
        self._sync_associations(feed)
    except IntegrityError as e:
        if is_unique_violation(e, "uq_feed_source_url"):
            raise InvalidStateError(
                f"DUPLICATE_FEED_URL: Feed with URL '{feed.url}' "
                f"already exists in source '{feed.source_id}'"
            ) from e
        raise  # Otra violación de integridad — propagar
```

---

## 4. RawArticleRepository

### 4.1 Resumen

| Aspecto | Detalle |
|---------|---------|
| **Entidad** | `RawArticle` (Aggregate Root, Inmutable) |
| **Modelo ORM** | `RawArticleModel` |
| **Tabla** | `ingestion_raw_articles` |
| **M:N** | No |
| **Optimistic Lock** | No (inmutable) |
| **`save()` method** | `session.add()` + `session.flush()` |
| **Volumen** | ALTO (millones de registros) |
| **Carga** | Siempre paginada |

### 4.2 `save()` — Individu con IntegrityError Handling

```python
def save(self, article: RawArticle) -> None:
    """Persiste un RawArticle (siempre es creación).

    Raises:
        InvalidStateError: Si viola UNIQUE constraint (DUPLICATE_ARTICLE).
    """
    try:
        model = self._domain_to_model(article)
        self._session.add(model)
        self._session.flush()  # Forzar detección de duplicados
    except IntegrityError as e:
        self._session.rollback()  # Rollback parcial (savepoint implícito)
        if is_unique_violation(e, "uq_raw_article_feed_external"):
            raise InvalidStateError(
                f"DUPLICATE_ARTICLE: external_id '{article.external_id}' "
                f"already exists in feed '{article.feed_id}'"
            ) from e
        if is_unique_violation(e, "uq_raw_article_feed_hash"):
            raise InvalidStateError(
                f"DUPLICATE_ARTICLE: content_hash '{article.content_hash}' "
                f"already exists in feed '{article.feed_id}'"
            ) from e
        raise  # Otra violación — propagar

    # NO hacer commit — el UoW maneja el commit global.

NOTAS:
- session.add() es correcto porque RawArticle SIEMPRE es nuevo (inmutable).
- session.flush() fuerza la inserción ahora, capturando IntegrityError
  dentro del repositorio (no en commit del UoW).
- El rollback después de IntegrityError revierte SOLO la operación que falló
  (savepoint implícito de SQLAlchemy), permitiendo continuar la transacción.
```

**¿Por qué `add` y no `merge`?** RawArticle siempre es creación (inmutable). `merge()` haría un SELECT innecesario para verificar existencia. Con `add()` + `flush()`, la verificación ocurre en la UNIQUE constraint de BD, que es más eficiente.

**¿Por qué `flush()` explícito?** Si no hacemos flush, el `IntegrityError` ocurriría en `session.commit()` del UoW. El UoW no sabe cómo mapear el error específico de RawArticle — es responsabilidad del repositorio. Haciendo flush, capturamos el error dentro del repositorio y devolvemos un error semántico (`DUPLICATE_ARTICLE`).

### 4.3 `save_batch()` — Estrategia Batch

```python
def save_batch(self, articles: list[RawArticle]) -> None:
    """Persiste múltiples RawArticles atómicamente.

    Estrategia: INSERT usando Core (bulk) con fallback a individual.
    Si el INSERT bulk falla por duplicado, se reintenta individualmente
    para identificar cuál(es) artículo(s) causaron el error.
    """
    # ── Opción 1: Bulk INSERT mappings (más rápido) ──
    try:
        mappings = [self._domain_to_dict(a) for a in articles]
        self._session.execute(
            insert(RawArticleModel),  # Core Insert, no ORM
            mappings
        )
        self._session.flush()
        return  # Todos exitosos
    except IntegrityError:
        self._session.rollback()  # Revierte todo el batch

    # ── Opción 2: Fallback a individual ──
    # Si el bulk falló, intentamos uno por uno
    # para persistir los no-duplicados
    for article in articles:
        try:
            self.save(article)  # Llama al save() individual
        except InvalidStateError:
            pass  # Duplicado → skip, continuar con el resto
    
    # NOTA: Esto es una decisión de diseño.
    # Alternativa: fallar completamente si hay duplicados.
    # La elección depende del caso de uso:
    # - Fetch de feed: skip duplicados, persistir el resto
    # - Migración de datos: fallar si hay duplicados

NOTAS:
- bulk INSERT con Core es ~2-3x más rápido que session.add() por fila.
  No pasa por el identity map ni dispara eventos ORM.
- Si el bulk falla, hacemos fallback a individual.
- Cada individual fallido (duplicado) se skipea con pass.
- Los artículos NO duplicados se persisten.
```

**¿Por qué bulk INSERT con Core y no con ORM?**

| Opción | Performance | Atomicidad | Identity Map |
|--------|-------------|------------|--------------|
| **✅ Core `insert()`** | ALTA (batch directo a BD) | Por batch (todo o nada) | No pasa (más rápido) |
| ❌ `session.add_all()` + `flush()` | BAJA (cada fila pasa por ORM) | Individual | Sí (más overhead) |
| ❌ `session.bulk_insert_mappings()` | MEDIA | Obsoleto en SA 2.0 | No recomendado |

**Decisión**: Usar Core `insert()` para performance. Fallback a individual para duplicados.

**Mappings a dict**:

```python
def _domain_to_dict(self, article: RawArticle) -> dict:
    """Convierte RawArticle a dict para bulk INSERT.

    NOTA: No pasa por TypeDecorators porque Core Insert recibe
    valores ya serializados. Los TypeDecorators se usan con ORM.
    """
    return {
        "id": article.id.value,            # UUID
        "feed_id": article.feed_id.value,  # UUID
        "external_id": article.external_id,
        "content_hash": article.content_hash,
        "title": article.title.value,      # str del VO
        "url": article.url.value,          # str del VO
        "author": article.author,
        "language": article.language.code if article.language else None,
        "published_at": article.published_at,
        "fetched_at": article.fetched_at,
        "content_preview": article.content_preview,
        "metadata": article.metadata or {},
    }
```

### 4.4 `find_by_feed()` — Paginación

```python
def find_by_feed(
    self, feed_id: FeedId, page: int = 1, size: int = 50
) -> list[RawArticle]:
    """Retorna RawArticles de un Feed paginados por fetched_at DESC."""
    stmt = (
        select(RawArticleModel)
        .where(RawArticleModel.feed_id == feed_id)
        .order_by(RawArticleModel.fetched_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    models = self._session.execute(stmt).scalars().all()
    return [self._model_to_domain(m) for m in models]
```

**¿LIMIT/OFFSET vs Cursor-based pagination?**

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| **✅ LIMIT/OFFSET** | Simple. El OFFSET se vuelve lento con muchas páginas (el motor igual escanea las filas saltadas). Para el volumen actual (< 10M artículos), es aceptable. | **SELECCIONADO** para primera iteración |
| ❌ Cursor-based (keyset pagination) | Más eficiente para grandes volúmenes (usa `WHERE fetched_at < :cursor LIMIT :size`). Más complejo de implementar. Requiere que el cliente conozca el cursor. | Futuro: adoptar cuando OFFSET sea瓶颈 |

**Índice**: `ix_raw_articles_feed_fetched` cubre exactamente este query (feed_id, fetched_at DESC).

### 4.5 `find_by_hash()` y `exists_by_*`

```python
def find_by_hash(self, feed_id: FeedId, content_hash: str) -> Result[RawArticle]:
    stmt = (
        select(RawArticleModel)
        .where(RawArticleModel.feed_id == feed_id)
        .where(RawArticleModel.content_hash == content_hash)
    )
    model = self._session.execute(stmt).scalar_one_or_none()
    if model is None:
        return Result.failure(...)
    return Result.success(self._model_to_domain(model))

def exists_by_url(self, feed_id: FeedId, url: ArticleUrl) -> bool:
    stmt = (
        select(RawArticleModel.id)
        .where(RawArticleModel.feed_id == feed_id)
        .where(RawArticleModel.url == url)
        .limit(1)
    )
    return self._session.execute(stmt).first() is not None

def exists_by_hash(self, feed_id: FeedId, content_hash: str) -> bool:
    stmt = (
        select(RawArticleModel.id)
        .where(RawArticleModel.feed_id == feed_id)
        .where(RawArticleModel.content_hash == content_hash)
        .limit(1)
    )
    return self._session.execute(stmt).first() is not None

def count_by_feed(self, feed_id: FeedId) -> int:
    stmt = select(func.count(RawArticleModel.id)).where(
        RawArticleModel.feed_id == feed_id
    )
    count = self._session.execute(stmt).scalar()
    return count or 0
```

### 4.6 Consideraciones de Performance para Alto Volumen

| Aspecto | Estrategia |
|---------|------------|
| **Batch size** | 500 artículos por batch (por experiencia: balance entre latencia y overhead de transacción) |
| **IDs auto-generados** | RawArticle usa UUID generado en dominio (no autoincrement). No hay problema de IDs secuenciales. |
| **Index maintenance** | Los índices compuestos (feed_id, external_id) y (feed_id, content_hash) son estrechos y eficientes. |
| **Table partitioning** | No necesaria en primera iteración. Si el volumen supera 50M filas, particionar por feed_id o por mes. |
| **VACUUM (PostgreSQL)** | Las inserciones intensivas generan dead tuples. Programar VACUUM periódico fuera de horas pico. |
| **Connection pooling** | Pool de 5 conexiones con 10 overflow. Suficiente para inserts secuenciales. |

---

## 5. CategoryRepository

### 5.1 Resumen

| Aspecto | Detalle |
|---------|---------|
| **Entidad** | `Category` (Entity, no Aggregate Root) |
| **Modelo ORM** | `CategoryModel` |
| **Tabla** | `ingestion_categories` |
| **M:N** | No (es el lado referenciado) |
| **Optimistic Lock** | Sí (version column) |
| **`save()` method** | `session.merge()` |
| **Jerarquía** | Self-referencing (parent_id) |

### 5.2 Métodos

#### `save(category: Category) -> None`

```
1. model = _domain_to_model(category)
2. session.merge(model)

NOTAS:
- La jerarquía se maneja via parent_id (FK self-referencing).
- No se valida la jerarquía aquí (I-19, I-20 se validan en dominio/application).
- merge() maneja INSERT/UPDATE automáticamente.
- StaleDataError se maneja en UoW.
```

**Mapeo de parent_id**:

```python
def _domain_to_model(self, category: Category) -> CategoryModel:
    return CategoryModel(
        id=category.id,
        name=category.name,
        slug=category.slug,
        description=category.description,
        is_active=category.is_active,
        parent_id=category.parent_id,  # CategoryId | None → UUID | None via TypeDecorator
    )

def _model_to_domain(self, model: CategoryModel) -> Category:
    return Category(
        id=model.id,
        name=model.name,
        slug=model.slug,
        description=model.description,
        is_active=model.is_active,
        parent_id=model.parent_id,  # UUID | None → CategoryId | None via TypeDecorator
    )
```

#### `find_by_id(id: CategoryId) -> Result[Category]`

```
1. model = session.get(CategoryModel, id)
   └── carga también parent (lazy="joined")
2. Si model is None → Result.failure(CATEGORY_NOT_FOUND)
3. return Result.success(_model_to_domain(model))
```

#### `find_by_slug(slug: str) -> Result[Category]`

```
1. stmt = select(CategoryModel).where(CategoryModel.slug == slug)
2. model = session.execute(stmt).scalar_one_or_none()
3. Si model is None → Result.failure(CATEGORY_NOT_FOUND)
4. return Result.success(_model_to_domain(model))

NOTAS:
- slug tiene UNIQUE constraint.
- .scalar_one_or_none() para detectar duplicados inesperados.
```

#### `find_all() -> list[Category]`

```
1. stmt = select(CategoryModel).order_by(CategoryModel.name)
2. models = session.execute(stmt).scalars().all()
3. return [_model_to_domain(m) for m in models]
```

#### `find_active() -> list[Category]`

```
1. stmt = (
    select(CategoryModel)
    .where(CategoryModel.is_active == True)
    .order_by(CategoryModel.name)
  )
2. models = session.execute(stmt).scalars().all()
3. return [_model_to_domain(m) for m in models]

NOTA: Usa índice ix_categories_active.
```

#### `find_by_parent(parent_id: CategoryId) -> list[Category]`

```
1. stmt = (
    select(CategoryModel)
    .where(CategoryModel.parent_id == parent_id)
    .order_by(CategoryModel.name)
  )
2. models = session.execute(stmt).scalars().all()
3. return [_model_to_domain(m) for m in models]

NOTA: Usa índice ix_categories_parent.
```

#### `exists_by_slug(slug: str) -> bool`

```
1. stmt = select(CategoryModel.id).where(CategoryModel.slug == slug).limit(1)
2. return session.execute(stmt).first() is not None
```

### 5.3 Jerarquía: ¿Cómo se maneja el árbol?

**`parent_id` es SUFICIENTE para la primera iteración.**

Esto soporta:
- **Obtener hijos directos**: `find_by_parent(parent_id)` — query indexada.
- **Validar ciclos (I-20)**: En Application Layer, se carga la cadena de padres recursivamente y se verifica que el nuevo `parent_id` no cree un ciclo.
- **Cascade de desactivación (I-21)**: En Application Layer, se cargan hijos recursivamente y se desactivan.

**Lo que NO se soporta (y está bien)**:
- **Árbol completo en una query**: Obtener TODOS los descendientes de una categoría requiere múltiples queries o CTEs recursivos. No es necesario para las operaciones actuales. Si se necesita en el futuro, se puede usar:
  - **PostgreSQL**: `WITH RECURSIVE` CTE.
  - **SQLAlchemy**: `session.execute(text("WITH RECURSIVE ..."))`.

**Validación de ciclos en Application Layer**:

```python
# Pseudocódigo para I-20 (sin implementar):
def _validate_no_cycle(
    category_repo: CategoryRepository,
    category_id: CategoryId,
    new_parent_id: CategoryId,
) -> bool:
    """Verifica que asignar new_parent_id a category_id no cree un ciclo."""
    current = new_parent_id
    visited = {category_id}
    while current is not None:
        if current in visited:
            return False  # Ciclo detectado
        visited.add(current)
        parent_result = category_repo.find_by_id(current)
        if parent_result.is_failure:
            break
        current = parent_result.value.parent_id
    return True
```

---

## 6. TopicRepository

### 6.1 Resumen

| Aspecto | Detalle |
|---------|---------|
| **Entidad** | `Topic` (Entity, no Aggregate Root) |
| **Modelo ORM** | `TopicModel` |
| **Tabla** | `ingestion_topics` |
| **M:N** | No (es el lado referenciado) |
| **Optimistic Lock** | Sí (version column) |
| **`save()` method** | `session.merge()` |
| **Complejidad** | BAJA — entidad más simple del modelo |

### 6.2 Métodos

TopicRepository es el repositorio más simple. Todos los métodos siguen los patrones establecidos sin particularidades.

#### `save(topic: Topic) -> None`

```
1. model = _domain_to_model(topic)
2. session.merge(model)

NOTA: Topic es simple:
- No tiene M:N (es el lado referenciado).
- No tiene jerarquía.
- No tiene VOs propios (name es str primitivo ya validado en dominio).
```

```python
def _domain_to_model(self, topic: Topic) -> TopicModel:
    return TopicModel(
        id=topic.id,
        name=topic.name,
        description=topic.description,
        is_active=topic.is_active,
    )

def _model_to_domain(self, model: TopicModel) -> Topic:
    return Topic(
        id=model.id,
        name=model.name,
        description=model.description,
        is_active=model.is_active,
    )
```

#### `find_by_id(id: TopicId) -> Result[Topic]`

```
1. model = session.get(TopicModel, id)
2. Si model is None → Result.failure(TOPIC_NOT_FOUND)
3. return Result.success(_model_to_domain(model))
```

#### `find_by_name(name: str) -> Result[Topic]`

```
1. stmt = select(TopicModel).where(TopicModel.name == name)
2. model = session.execute(stmt).scalar_one_or_none()
3. Si model is None → Result.failure(TOPIC_NOT_FOUND)
4. return Result.success(_model_to_domain(model))
```

#### `find_all() -> list[Topic]`

```
1. stmt = select(TopicModel).order_by(TopicModel.name)
2. models = session.execute(stmt).scalars().all()
3. return [_model_to_domain(m) for m in models]
```

#### `find_active() -> list[Topic]`

```
1. stmt = (
    select(TopicModel)
    .where(TopicModel.is_active == True)
    .order_by(TopicModel.name)
  )
2. models = session.execute(stmt).scalars().all()
3. return [_model_to_domain(m) for m in models]

NOTA: Usa índice ix_topics_active.
```

#### `exists_by_name(name: str) -> bool`

```
1. stmt = select(TopicModel.id).where(TopicModel.name == name).limit(1)
2. return session.execute(stmt).first() is not None
```
