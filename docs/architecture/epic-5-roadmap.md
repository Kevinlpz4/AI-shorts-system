# EPIC 5 Roadmap — Persistence & Infrastructure

> **Plan de implementación dividido en sprints incrementales**
>
> Versión: 1.0 | Estado: **SPECIFIED**
> Fecha: 2026-07-05
> Basado en: Persistence Design v1.0, ORM Mapping Strategy v1.0, Repository Implementation Plan v1.0,
> Transaction Strategy v1.0, Migration Strategy v1.0, Configuration Design v1.0, Performance Review v1.0

---

## 0. Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Sprints planificados | 8 |
| Documentos de diseño | 6 (6,728 líneas) |
| Archivos a implementar (estimado) | ~25-35 |
| Tests estimados | 200-300 |
| Dependencias externas nuevas | 2 (SQLAlchemy, Alembic) |
| Foundation modificaciones | **0** (FROZEN) |
| Domain modificaciones | **0** (FROZEN) |
| Application modificaciones | **0** (FROZEN) |
| Riesgos altos | 0 |
| Riesgos medios | 2 |

---

## 1. Sprint 5.1 — Persistence Foundation

**Objetivo**: Establecer la infraestructura base de SQLAlchemy + TypeDecorators sin tocar modelos ORM.

**Dependencias**: Foundation v1.0, Persistence Design, ORM Mapping Strategy

### Stack técnico
- SQLAlchemy 2.x (declarative mapping)
- Base ORM Infrastructure: `DeclarativeBase`, `MetaData`, `naming_convention`
- Engine configuration: `create_engine()` con pooling
- Session factory: `sessionmaker`

### Entregables

| Archivo | Descripción |
|---------|-------------|
| `src/ingestion/infrastructure/persistence/__init__.py` | Exports públicos |
| `src/ingestion/infrastructure/persistence/base.py` | `IngestionBase`, metadata, naming convention |
| `src/ingestion/infrastructure/persistence/types.py` | Catálogo de TypeDecorators |
| `src/ingestion/infrastructure/persistence/engine.py` | `create_ingestion_engine()`, `create_session_factory()` |

### TypeDecorators a implementar (8)

| Decorator | SQL Type | Python Type |
|-----------|----------|-------------|
| `EntityIdType` | `UUID` | `EntityId` (genérico, usado por los 5 IDs) |
| `ArticleTitleType` | `VARCHAR(500)` | `ArticleTitle` |
| `ArticleUrlType` | `VARCHAR(2048)` | `ArticleUrl` |
| `CategoryNameType` | `VARCHAR(100)` | `CategoryName` |
| `SourceUrlType` | `VARCHAR(2048)` | `SourceUrl` |
| `LanguageType` | `VARCHAR(2)` | `Language` |
| `SourceTypeEnum` | `VARCHAR(20)` | `SourceType` |
| `SyncModeEnum` | `VARCHAR(20)` | `SyncMode` |

### Criterios de aceptación
- [ ] 8 TypeDecorators implementados y testeados individualmente
- [ ] `IngestionBase` creada con naming convention correcta
- [ ] `create_ingestion_engine()` funciona en SQLite (test) y PostgreSQL (producción)
- [ ] Session factory sin estado global (no `scoped_session`)
- [ ] 0 modificaciones a Foundation, Domain, o Application
- [ ] Tests de TypeDecorators: round-trip (Python → SQL → Python)

### Riesgos
- **Bajo**: TypeDecorators de Enum requieren manejar valores inválidos en la DB
- **Bajo**: `EntityIdType` genérico necesita TypeVar para typing correcto

### Tests requeridos
- `test_entity_id_type.py` — bind/result parameter, null handling
- `test_value_object_types.py` — round-trip para cada VO TypeDecorator
- `test_enum_types.py` — valores válidos, inválidos, null
- `test_engine.py` — creación, pool settings, echo flag

---

## 2. Sprint 5.2 — ORM Mapping

**Objetivo**: Mapear TODAS las entidades del dominio a modelos SQLAlchemy.
Sin repositorios todavía — solo el mapping puro.

**Dependencias**: Sprint 5.1, ORM Mapping Strategy

### Modelos a implementar

| Modelo | Tabla | Tipo | Relaciones |
|--------|-------|------|------------|
| `NewsSourceModel` | `ingestion_news_sources` | Aggregate Root | 1→N Feed, M:N Category/Topic |
| `FeedModel` | `ingestion_feeds` | Aggregate Root | M→1 Source, M:N Category/Topic, SyncPolicy composite |
| `RawArticleModel` | `ingestion_raw_articles` | AR (Entity herencia) | M→1 Feed (SIN relación ORM directa) |
| `CategoryModel` | `ingestion_categories` | Entity | self-ref parent_id |
| `TopicModel` | `ingestion_topics` | Entity | standalone |
| `NewsSourceCategoryModel` | `ingestion_news_source_categories` | Association | M:N |
| `NewsSourceTopicModel` | `ingestion_news_source_topics` | Association | M:N |
| `FeedCategoryModel` | `ingestion_feed_categories` | Association | M:N |
| `FeedTopicModel` | `ingestion_feed_topics` | Association | M:N |

### Estrategia para RawArticle
- SIN relación ORM `Feed.raw_articles` (volumen masivo)
- Solo FK `RawArticleModel.feed_id` para integridad referencial
- Repositorio maneja paginación directamente (Core queries)

### SyncPolicy composite
- 7 columnas separadas en `ingestion_feeds`
- `composite(SyncPolicy, ...)` con orden exacto de campos
- `SyncPolicy` no tiene `@dataclass(frozen=True)` propio → usar `CompositeProtocol` o adaptar

### Entregables
- `src/ingestion/infrastructure/persistence/models/__init__.py`
- `src/ingestion/infrastructure/persistence/models/news_source.py`
- `src/ingestion/infrastructure/persistence/models/feed.py`
- `src/ingestion/infrastructure/persistence/models/raw_article.py`
- `src/ingestion/infrastructure/persistence/models/category.py`
- `src/ingestion/infrastructure/persistence/models/topic.py`
- `src/ingestion/infrastructure/persistence/models/associations.py`

### Criterios de aceptación
- [ ] Todos los modelos mapean correctamente (round-trip INSERT+SELECT)
- [ ] M:N associations funcionan con `viewonly=True` + `selectin`
- [ ] SyncPolicy composite se construye/descompone correctamente
- [ ] RawArticle solo tiene FK, sin relación ORM inversa
- [ ] `version_id_col` configurado en NewsSource, Feed, Category, Topic
- [ ] Optimistic locking: `StaleDataError` se propaga correctamente
- [ ] 0 modificaciones a Foundation, Domain, o Application

### Riesgos
- **Medio**: `SyncPolicy` es `@dataclass(frozen=True)` → `composite()` requiere `__composite_values__()`. Puede necesitar adaptación del VO sin modificar Domain (usar wrapper en infraestructura).
- **Bajo**: `version_id_col` en Category con self-reference puede causar issues de orden de UPDATE

### Tests requeridos
- `test_orm_mapping.py` — INSERT + SELECT + UPDATE para cada modelo
- `test_associations.py` — M:N round-trip
- `test_sync_policy_composite.py` — composite round-trip con valores reales
- `test_optimistic_lock.py` — version conflict detection
- `test_raw_article_no_relationship.py` — verificar que NO hay `raw_articles` en FeedModel

---

## 3. Sprint 5.3 — Repository Implementation

**Objetivo**: Implementar TODOS los Repository Ports del dominio sobre SQLAlchemy.

**Dependencias**: Sprint 5.2, Repository Implementation Plan

### Repositorios a implementar

| Repositorio | Modelo base | Métodos | Crítico |
|-------------|-------------|---------|---------|
| `SqlAlchemyNewsSourceRepository` | `NewsSourceModel` | 6 | Bajo |
| `SqlAlchemyFeedRepository` | `FeedModel` | 7 | Bajo |
| `SqlAlchemyRawArticleRepository` | `RawArticleModel` | 9 | **ALTO** (volumen) |
| `SqlAlchemyCategoryRepository` | `CategoryModel` | 7 | Bajo |
| `SqlAlchemyTopicRepository` | `TopicModel` | 6 | Bajo |

### Patrones comunes

```python
class SqlAlchemyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session
    
    def _save(self, model: Base) -> None:
        """Merge pattern para ARs mutables."""
        self._session.merge(model)
    
    def _execute(self, stmt) -> Result:
        """Wrapper para queries con error mapping."""
        ...
```

### Estrategia RawArticleRepository (crítico)

```python
def save_batch(self, articles: list[RawArticle]) -> SaveBatchResult:
    """Core insert con ON CONFLICT DO NOTHING + RETURNING."""
    # PostgreSQL: INSERT ... ON CONFLICT ... RETURNING id
    # SQLite: INSERT + IntegrityError catch por savepoint
```

- Batch INSERT via Core `insert()` para performance
- ON CONFLICT DO NOTHING para duplicados en PostgreSQL
- Savepoints para skip de duplicados en SQLite
- Keyset pagination: `WHERE (fetched_at, id) < (cursor, cursor_id)`

### M:N Synchronization
- Patrón DELETE + INSERT (sin diff)
- Dentro de la misma transacción que el AR padre
- `viewonly=True` + flush manual de association models

### Entregables
- `src/ingestion/infrastructure/persistence/repositories/__init__.py`
- `src/ingestion/infrastructure/persistence/repositories/base.py`
- `src/ingestion/infrastructure/persistence/repositories/news_source.py`
- `src/ingestion/infrastructure/persistence/repositories/feed.py`
- `src/ingestion/infrastructure/persistence/repositories/raw_article.py`
- `src/ingestion/infrastructure/persistence/repositories/category.py`
- `src/ingestion/infrastructure/persistence/repositories/topic.py`

### Criterios de aceptación
- [ ] Cada repositorio implementa EXACTAMENTE su Protocol de dominio
- [ ] `save_batch()` maneja 500 artículos en < 1s en SQLite local
- [ ] Duplicate detection sin race condition (ON CONFLICT o IntegrityError)
- [ ] M:N se sincroniza correctamente (DELETE + INSERT atómico)
- [ ] Keyset pagination no salta ni duplica registros
- [ ] 0 modificaciones a Foundation, Domain, o Application
- [ ] Tests pasan contra InMemory Y SQLAlchemy

### Riesgos
- **Medio**: `save_batch()` es el punto más caliente. La implementación varía entre PostgreSQL (ON CONFLICT) y SQLite (IntegrityError). Mantener ambas.
- **Bajo**: M:N sync DELETE+INSERT puede ser ineficiente si las listas crecen mucho (>100 items)

### Tests requeridos
- `test_sqlalchemy_news_source_repo.py` — todos los métodos del Protocol
- `test_sqlalchemy_feed_repo.py` — incluyendo count_active_by_source
- `test_sqlalchemy_raw_article_repo.py` — batch, pagination, dedup, count
- `test_sqlalchemy_category_repo.py` — self-referencing parent
- `test_sqlalchemy_topic_repo.py` — CRUD básico
- `test_sqlalchemy_mn_sync.py` — M:N add/remove/clear

---

## 4. Sprint 5.4 — UnitOfWork + Event Publisher

**Objetivo**: Implementar SQLAlchemy UnitOfWork y Event Publisher con post-commit hooks.

**Dependencias**: Sprint 5.3, Transaction Strategy

### UnitOfWork

```python
class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self.session: Session | None = None
    
    def __enter__(self) -> Self:
        self.session = self._session_factory()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.session.rollback()
        self.session.close()
    
    def commit(self) -> None:
        try:
            self.session.commit()
        except StaleDataError:
            self.session.rollback()
            raise
```

### Event Publisher + Post-Commit Hooks

```python
class SqlAlchemyUnitOfWork:
    _pending_events: list[DomainEvent] = []
    
    def collect_events(self, aggregates: list[AggregateRoot]) -> None:
        for ar in aggregates:
            self._pending_events.extend(ar.pull_events())
    
    def commit(self) -> None:
        self.session.commit()
        self._publish_pending()
    
    def _publish_pending(self) -> None:
        events = self._pending_events[:]
        self._pending_events.clear()
        self._event_publisher.publish_batch(events)
```

**Decisión**: **Opción A — Post-Commit Hooks** (elegida)
- 3 eventos de dominio solamente (SourceEnabled, SourceDisabled, RawArticleCollected)
- Volumen bajo: ~100-1000 eventos/día
- Si el publisher falla: pérdida aceptable con consistencia eventual
- Outbox Pattern sería premature optimization → pospuesto a EPIC 6 si se necesitan garantías stronger

### Entregables
- `src/ingestion/infrastructure/persistence/unit_of_work.py`
- `src/ingestion/infrastructure/persistence/event_publisher.py`
- `src/ingestion/infrastructure/persistence/repositories/__init__.py` (actualizar DI)

### Criterios de aceptación
- [ ] UnitOfWork es un reemplazo directo de `InMemoryUnitOfWork`
- [ ] commit() persiste + publica eventos en orden
- [ ] rollback() en __exit__ con excepción
- [ ] rollback() también limpia `_pending_events`
- [ ] StaleDataError capturado y propagado
- [ ] 0 modificaciones a Application (los services no cambian)

### Tests requeridos
- `test_sqlalchemy_unit_of_work.py` — commit, rollback, nested, error
- `test_event_publisher.py` — publicación post-commit
- `test_uow_event_order.py` — commit ANTES de publish
- `test_uow_rollback_clears_events.py` — eventos no se publican si hay rollback

---

## 5. Sprint 5.5 — Alembic + Migrations

**Objetivo**: Configurar Alembic, crear migración inicial + seeds.

**Dependencias**: Sprint 5.2 (modelos ORM listos)

### Estructura

```
alembic/
├── versions/
│   ├── 0001_initial_schema.py
│   ├── 0002_seed_data.py
│   └── ...
├── env.py
├── script.py.mako
alembic.ini
```

### Migraciones

| Versión | Contenido |
|---------|-----------|
| `0001` | Schema completo: 9 tablas, todos los índices, constraints |
| `0002` | Seed data: 9 categorías por defecto (UUIDs fijos) |

### Seed Data (9 categorías iniciales)

| CategoryId (UUID fijo) | Name | Slug | Description |
|------------------------|------|------|-------------|
| `a1b2c3d4-...-0001` | Technology | `technology` | Technology & computing |
| `a1b2c3d4-...-0002` | Science | `science` | Scientific research & discoveries |
| `a1b2c3d4-...-0003` | Gaming | `gaming` | Video games & esports |
| `a1b2c3d4-...-0004` | Entertainment | `entertainment` | Movies, TV & music |
| `a1b2c3d4-...-0005` | Business | `business` | Business & finance |
| `a1b2c3d4-...-0006` | Sports | `sports` | Sports & athletics |
| `a1b2c3d4-...-0007` | Politics | `politics` | Politics & government |
| `a1b2c3d4-...-0008` | Health | `health` | Health & wellness |
| `a1b2c3d4-...-0009` | World News | `world-news` | International news |

### Entregables
- `alembic/env.py`
- `alembic/script.py.mako`
- `alembic/versions/0001_initial_schema.py`
- `alembic/versions/0002_seed_data.py`
- `alembic.ini`
- `scripts/manage_db.py` (helper commands)
- `Makefile` targets (db-upgrade, db-downgrade, db-seed)

### Criterios de aceptación
- [ ] `alembic upgrade head` crea todas las tablas correctamente
- [ ] `alembic downgrade -1` revierte correctamente (todas las migraciones tienen downgrade)
- [ ] Seed data se inserta en `0002` y se revierte en downgrade
- [ ] `env.py` NO importa Foundation (protección contra modificación accidental)
- [ ] CI job verifica que `Foundation` no tiene metadata de BD
- [ ] Las migraciones funcionan tanto en SQLite como en PostgreSQL

### Tests requeridos
- `test_migration_upgrade.py` — upgrade + verify schema
- `test_migration_downgrade.py` — upgrade → downgrade → verify reversión
- `test_migration_seed.py` — seed data insertada correctamente
- `test_migration_foundation_protection.py` — Foundation no tiene tablas

---

## 6. Sprint 5.6 — Composition Root + DI + Configuration

**Objetivo**: Conectar todo mediante inyección de dependencias y configuración.

**Dependencias**: Sprint 5.4 (UoW + repos listos), Configuration Design

### Composition Root

```python
class IngestionInfrastructure:
    """Composition Root para infraestructura de Ingestion."""
    
    def __init__(self, settings: IngestionSettings) -> None:
        self._settings = settings
        self._engine = create_ingestion_engine(settings)
        self._session_factory = create_session_factory(self._engine)
    
    def new_unit_of_work(self) -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(
            session_factory=self._session_factory,
            event_publisher=SqlAlchemyEventPublisher(),
        )
    
    def news_source_repository(self, session: Session) -> NewsSourceRepository:
        return SqlAlchemyNewsSourceRepository(session)
    
    # ... etc para cada repositorio
```

### Configuración
- Pydantic `BaseSettings` para validación automática
- `.env` file para desarrollo
- Variables de entorno para producción
- Config levels: `development`, `testing`, `production`

### Entregables
- `src/ingestion/infrastructure/persistence/composition_root.py`
- `src/ingestion/infrastructure/persistence/config.py`
- `src/ingestion/infrastructure/__init__.py` (actualizar exports)

### Criterios de aceptación
- [ ] Composition Root expone factories para UoW y repositorios
- [ ] Config se lee de `.env` / environment / defaults
- [ ] Sin estado global (singletons, module-level state)
- [ ] Cada componente puede ser reemplazado individualmente (testability)
- [ ] Legacy InMemory repos siguen funcionando como alternativa

### Tests requeridos
- `test_composition_root.py` — creación, inyección, defaults
- `test_config.py` — valores default, override con env vars
- `test_infrastructure_di.py` — integration test del wiring completo

---

## 7. Sprint 5.7 — Observability

**Objetivo**: Agregar logging, tracing opcional y health checks a la infraestructura.

**Dependencias**: Sprint 5.6 (DI configurada)

### Logging

| Nivel | Logger | Qué se loggea |
|-------|--------|---------------|
| DEBUG | `sqlalchemy.engine` | SQL queries (solo dev) |
| INFO | `ingestion.infrastructure` | Operaciones: save, find, count |
| WARNING | `ingestion.infrastructure` | Slow queries (>500ms), pool exhaustion |
| ERROR | `ingestion.infrastructure` | IntegrityError, StaleDataError, connection failures |

### Slow Query Detection
```python
@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info["query_start"] = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info["query_start"]
    if total > settings.slow_query_threshold:
        logger.warning("Slow query: %.2fs | %s", total, statement[:200])
```

### Health Checks
- `GET /health/db` — `SELECT 1` + pool stats (active, idle, overflow connections)
- `GET /health/ready` — DB connection + migrate status

### Entregables
- `src/ingestion/infrastructure/persistence/logging.py`
- `src/ingestion/infrastructure/persistence/health.py`
- `src/ingestion/infrastructure/persistence/events.py` (SQLAlchemy event listeners)

### Criterios de aceptación
- [ ] SQL logging condicional por entorno (no loggear en producción)
- [ ] Slow query threshold configurable
- [ ] Health check endpoint funcional
- [ ] Pool stats expuestas (para Prometheus later)
- [ ] 0 overhead en hot path cuando logging está desactivado

---

## 8. Sprint 5.8 — Architecture Verification

**Objetivo**: Auditoría final de la infraestructura SQL. ARB Report.

**Dependencias**: TODOS los sprints anteriores

### Lo que se audita

| Aspecto | Método |
|---------|--------|
| Clean Architecture | Import analysis: infraestructura NO importa capas superiores |
| Hexagonal | Repository ports implementados correctamente |
| DDD | Aggregates persistidos sin romper invariantes |
| SOLID | SRP, OCP, LSP, ISP, DIP verificados |
| Foundation FROZEN | 0 archivos de Foundation modificados |
| Domain FROZEN | 0 archivos de Domain modificados |
| Application FROZEN | 0 archivos de Application modificados |
| Performance | N+1 analysis, query count, batch performance |
| Migration | Upgrade/downgrade round-trip, seed data |

### Entregables
- `docs/architecture/arb-report-epic-5.md` (este documento)
- Reporte de findings clasificados

---

## 9. Sprint Dependencies Graph

```
5.1 Foundation ──→ 5.2 ORM Mapping ──→ 5.3 Repositories ──→ 5.4 UoW + Events
                     │                                              │
                     ↓                                              ↓
                   5.5 Alembic ───────────────────────────────── 5.6 DI + Config
                                                                      │
                                                                      ↓
                                                                  5.7 Observability
                                                                      │
                                                                      ↓
                                                                  5.8 ARB Audit
```

Dependencias clave:
- 5.3 → 5.2 → 5.1 (lineal, obligatorio)
- 5.5 necesita 5.2 (modelos listos) pero NO 5.3/5.4
- 5.6 necesita 5.4 (UoW) y puede correr en paralelo con 5.5
- 5.7 necesita 5.6 (DI configurada)
- 5.8 necesita todo

---

## 10. Estimación de Esfuerzo

| Sprint | Archivos estimados | Tests estimados | Días estimados |
|--------|-------------------|-----------------|----------------|
| 5.1 Foundation | 5 | ~30 | 2-3 |
| 5.2 ORM Mapping | 10 | ~40 | 3-4 |
| 5.3 Repositories | 8 | ~60 | 4-5 |
| 5.4 UoW + Events | 3 | ~20 | 2-3 |
| 5.5 Alembic | 7 | ~15 | 2-3 |
| 5.6 DI + Config | 4 | ~15 | 1-2 |
| 5.7 Observability | 3 | ~10 | 1-2 |
| 5.8 ARB Audit | 1 | ~0 | 1 |
| **Total** | **~41** | **~190** | **16-23 días** |

---

## 11. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| SyncPolicy composite incompatible con @dataclass(frozen=True) | Media | Medio | Wrapper de infraestructura + unit tests específicos |
| Batch INSERT performance inferior a lo esperado | Baja | Alto | Benchmark en Sprint 5.3, ajustar batch size |
| Migration conflicts entre miembros del equipo | Baja | Medio | Sequential versioning, CI check de migraciones duplicadas |
| N+1 no detectado en desarrollo | Media | Alto | `lazy="raise_on_sql"` en modelos + code review |
| Foundation modificado accidentalmente | Baja | Crítico | CI job detecta cambios en `src/foundation/` |
| Post-commit hook falla y eventos perdidos | Baja | Bajo | Solo 3 eventos, baja criticidad. Outbox en EPIC 6 si necesario |

---

## 12. Dependencias Externas

| Paquete | Versión mínima | Uso |
|---------|---------------|-----|
| `sqlalchemy` | 2.0.30 | ORM, Core, engine, session |
| `alembic` | 1.13.0 | Migrations |
| `psycopg2-binary` | 2.9.9 | PostgreSQL driver (production) |
| `aiosqlite` | 0.20.0 | SQLite async (testing, si aplica) |
| `pydantic-settings` | 2.2.0 | Configuration management |

Actualizar `requirements.txt` / `pyproject.toml` al inicio del Sprint 5.1.
