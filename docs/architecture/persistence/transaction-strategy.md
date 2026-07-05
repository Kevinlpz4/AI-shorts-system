# Transaction Strategy — EPIC 5

> **Estrategia completa de transacciones y publicación de eventos**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-05
> Basado en: Application Ports (UnitOfWork, EventPublisher), Transaction Boundaries v1.0
>
> **Este documento diseña la implementación SQLAlchemy del UnitOfWork,
> la estrategia de publicación de eventos post-commit, y la integración
> con los Application Services. NO implementa código ejecutable.**

---

## Índice

1. [UnitOfWork Design](#1-unitofwork-design)
    - 1.1 [Session Lifecycle](#11-session-lifecycle)
    - 1.2 [commit() / rollback()](#12-commit--rollback)
    - 1.3 [__exit__ Protocol](#13-__exit__-protocol)
    - 1.4 [SQLAlchemyUnitOfWork Implementation Blueprint](#14-sqlalchemyunitofwork-implementation-blueprint)
2. [Event Publication Strategy](#2-event-publication-strategy)
    - 2.1 [Opción A: Post-Commit Hooks (básico)](#21-opción-a-post-commit-hooks-básico)
    - 2.2 [Opción B: Outbox Pattern (completo)](#22-opción-b-outbox-pattern-completo)
    - 2.3 [Opción C: Two-Phase (híbrido)](#23-opción-c-two-phase-híbrido)
    - 2.4 [Evaluación y Decisión](#24-evaluación-y-decisión)
    - 2.5 [Implementación de la Opción Elegida](#25-implementación-de-la-opción-elegida)
3. [Nested Transactions (Savepoints)](#3-nested-transactions-savepoints)
4. [Isolation Levels](#4-isolation-levels)
5. [Error Handling: IntegrityError → Domain Errors](#5-error-handling-integrityerror--domain-errors)
    - 5.1 [Catálogo de IntegrityErrors](#51-catálogo-de-integrityerrors)
    - 5.2 [Mapeo Centralizado](#52-mapeo-centralizado)
    - 5.3 [ConcurrentModificationError (Optimistic Lock)](#53-concurrentmodificationerror-optimistic-lock)
    - 5.4 [Infrastructure Error Hierarchy](#54-infrastructure-error-hierarchy)
6. [UnitOfWork in Services](#6-unitofwork-in-services)
    - 6.1 [Patrón de Uso](#61-patrón-de-uso)
    - 6.2 [Wiring (Inyección de Dependencias)](#62-wiring-inyección-de-dependencias)
    - 6.3 [Queries (Solo Lectura)](#63-queries-solo-lectura)
    - 6.4 [Múltiples Agregados en una Transacción](#64-múltiples-agregados-en-una-transacción)

---

## 1. UnitOfWork Design

### 1.1 Session Lifecycle

**Estrategia: Session creada por el UnitOfWork, compartida con todos los repositorios.**

```
┌──────────────────────────────────────────────────────────┐
│ Application Service                                       │
│                                                          │
│  with self._uow:          ← __enter__: session = factory()│
│      repo1.save(e1)       ← usa self._session            │
│      repo2.save(e2)       ← usa self._session            │
│      self._uow.commit()   ← session.commit()             │
│                                                          │
│  (exit normally)          ← __exit__: session.close()    │
│                                                          │
│  Si excepción:            ← __exit__: rollback + close   │
└──────────────────────────────────────────────────────────┘
```

**¿El UnitOfWork crea la session o la recibe?**

| Opción | Decisión |
|--------|----------|
| **✅ UnitOfWork crea la session** | Recibe un `sessionmaker` en el constructor. En cada `__enter__`, llama `sessionmaker()` para crear una nueva sesión. Esto garantiza que cada UoW tenga su propia sesión aislada. **SELECCIONADO.** |
| ❌ UnitOfWork recibe la session | El caller debe crear y pasar la sesión. Más control externo pero mayor responsabilidad para el service. Riesgo de reutilizar sesiones entre UoWs. |

**¿Autoflush? ¿Autocommit?**

| Propiedad | Valor | Razón |
|-----------|-------|-------|
| `autocommit` | `False` | El commit es explícito. El UoW controla cuándo se persisten los cambios. |
| `autoflush` | `False` | El repositorio hace flush cuando lo necesita (RawArticle.save() para detectar duplicados). Sin flushes automáticos que puedan causar efectos laterales inesperados. |

**Configuración de la session factory**:

```python
session_factory = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=True,  # Los objetos se marcan como expirados después de commit
)
```

**`expire_on_commit=True`**: Después de `commit()`, todos los objetos ORM se marcan como "expirados". El próximo acceso a cualquier atributo hará un refresh desde BD. Esto es importante porque:
- Previene usar objetos stale después del commit.
- Fuerza al Application Service a recargar datos si los necesita después del commit (ej: para generar DTOs con datos actualizados).

El Application Service debe construir los DTOs ANTES del commit o usar objetos de dominio (no ORM) que no se ven afectados por expire.

### 1.2 commit() / rollback()

#### commit()

```
commit():
    1. session.commit()
       Internamente SQLAlchemy hace:
         a. flush() — sincroniza cambios pendientes con BD
         b. commit() — COMMIT a la BD
         c. expire_all() — expira objetos (si expire_on_commit=True)

    2. Si StaleDataError:
         a. session.rollback()
         b. raise ConcurrentModificationError(...)

    3. Si IntegrityError (no esperado):
         a. session.rollback()
         b. raise InfrastructureError(...)

    4. DBAPIError (pérdida de conexión, etc.):
         a. session.rollback()
         b. raise InfrastructureError(...)
```

**Manejo de StaleDataError (optimistic locking)**:

```python
from sqlalchemy.orm.exc import StaleDataError
from ingestion.application.exceptions.error_code import ApplicationErrorCode

class ConcurrentModificationError(Exception):
    """Error de concurrencia: optimistic lock detectó modificación concurrente."""
    code = ApplicationErrorCode.CONCURRENCY_CONFLICT

    def __init__(self, message: str, entity_id: str | None = None):
        self.entity_id = entity_id
        super().__init__(message)
```

`StaleDataError` se captura SOLO en `commit()`, no en cada `save()` del repositorio. Esto mantiene los repositorios simples — ellos solo invocan `merge()` y el check de version ocurre en el flush implícito de `commit()`.

#### rollback()

```
rollback():
    1. session.rollback()
       — Descarta todos los cambios no commiteados en la transacción actual.
       — La sesión queda en un estado limpio para reutilizar (aunque
         normalmente se cierra después de rollback).

NOTA: rollback() es idempotente. Llamarlo múltiples veces es seguro.
```

### 1.3 __exit__ Protocol

```python
def __exit__(self, exc_type, exc_val, exc_tb):
    """Finaliza la transacción.

    Si exc_type no es None (hubo excepción dentro del with):
        - rollback(): descarta cambios pendientes
    siempre:
        - session.close(): libera la conexión al pool
    """
    try:
        if exc_type is not None:
            self._session.rollback()
    finally:
        self._session.close()
        self._session = None
```

**¿Rollback solo en excepción o también si no se llamó commit()?**

Se hace rollback SOLO si hay excepción. Si no hay excepción pero el service no llamó `commit()` explícitamente, los cambios no persisten (no hay autocommit). Al cerrar la sesión sin commit, SQLAlchemy hace rollback implícito en `session.close()` (si la transacción está activa).

Esto es intencional: el **service debe llamar `commit()` explícitamente**. Si "olvida" hacerlo, los cambios se pierden (rollback implícito en close). Esto es mejor que un autocommit implícito que podría persistir cambios incompletos.

### 1.4 SQLAlchemyUnitOfWork Implementation Blueprint

```python
class SQLAlchemyUnitOfWork:
    """UnitOfWork basado en SQLAlchemy Session.

    Crea una sesión al entrar al context manager y la cierra al salir.
    Comparte la sesión con los repositorios a través de una propiedad.

    Uso:
        with SQLAlchemyUnitOfWork(session_factory) as uow:
            source_repo.save(source)  # usa uow.session internamente
            feed_repo.save(feed)      # usa uow.session internamente
            uow.commit()
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self._committed: bool = False

    def __enter__(self) -> SQLAlchemyUnitOfWork:
        """Crea una nueva sesión para esta transacción."""
        self._session = self._session_factory()
        self._committed = False
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Limpia la sesión. Rollback si hubo excepción."""
        try:
            if exc_type is not None:
                if self._session is not None:
                    self._session.rollback()
        finally:
            if self._session is not None:
                self._session.close()
                self._session = None

    @property
    def session(self) -> Session:
        """Retorna la sesión activa.

        Raises:
            RuntimeError: Si se accede fuera del context manager.
        """
        if self._session is None:
            raise RuntimeError("UnitOfWork: no active session")
        return self._session

    def commit(self) -> None:
        """Persiste los cambios acumulados.

        Captura StaleDataError y lo convierte en ConcurrentModificationError.
        """
        if self._session is None:
            raise RuntimeError("UnitOfWork: no active session")
        try:
            self._session.commit()
            self._committed = True
        except StaleDataError as e:
            self._session.rollback()
            raise ConcurrentModificationError(str(e)) from e
        except IntegrityError as e:
            self._session.rollback()
            raise InfrastructureError(f"Integrity violation: {e}") from e
        except DBAPIError as e:
            self._session.rollback()
            raise InfrastructureError(f"Database error: {e}") from e

    def rollback(self) -> None:
        """Descarta los cambios acumulados."""
        if self._session is not None:
            self._session.rollback()

    @property
    def is_committed(self) -> bool:
        return self._committed
```

**¿Cómo acceden los repositorios a la sesión?**

Los repositorios reciben la sesión por constructor:

```python
# En el wiring:
with uow:
    source_repo = SQLAlchemyNewsSourceRepository(uow.session)
    feed_repo = SQLAlchemyFeedRepository(uow.session)
    # ... operaciones ...
    uow.commit()
```

O los repositorios se crean con la sesión antes de entrar al UoW:

```python
# Opción alternativa: crear repositorios con la sesión ya asignada
session = uow.session
source_repo = SQLAlchemyNewsSourceRepository(session)
feed_repo = SQLAlchemyFeedRepository(session)
```

Para el wiring con Dependency Injection, ver sección 6.2.

---

## 2. Event Publication Strategy

### 2.1 Opción A: Post-Commit Hooks (básico)

**Descripción**: El Application Service recolecta eventos de los aggregates DESPUÉS del commit y los publica vía `EventPublisher`.

```
┌─────────────────────────────────────────────────────────────────┐
│ Service.execute_disable_source()                                 │
│                                                                  │
│  1. source.disable(reason)      → registra SourceDisabled        │
│  2. source_repo.save(source)                                     │
│  3. uow.commit()                → OK (source persistido)         │
│                                                                  │
│  ── POST-COMMIT ──                                               │
│                                                                  │
│  4. events = source.pull_events()  → [SourceDisabled]            │
│  5. event_publisher.publish_many(events)                         │
│     └── Si falla: evento perdido (log + alerta)                  │
└─────────────────────────────────────────────────────────────────┘
```

**Ventajas**:
- Simplicidad total. Sin infraestructura adicional.
- Sin latencia: el evento se publica inmediatamente después del commit.
- El service controla explícitamente el ciclo evento-publicación.

**Desventajas**:
- **Sin garantía de entrega**: Si `publish()` falla (broker caído, red), el evento se pierde permanentemente.
- **Sin reintentos**: No hay mecanismo de retry integrado.
- **Acoplamiento temporal**: El service espera a que el publish termine antes de retornar.

**Caso de fallo**:
```
1. commit() → OK (BD actualizada: Source is_active = False)
2. publish(SourceDisabled) → FALLA (Redis caído)
3. El evento se pierde
4. El scheduler no sabe que el Source se deshabilitó
5. Recuperación: en el próximo ciclo, el scheduler verifica source.is_active
   antes de fetchear. Esto es aceptable para el caso actual.
```

### 2.2 Opción B: Outbox Pattern (completo)

**Descripción**: Se crea una tabla `event_outbox` en la misma BD. Los eventos se insertan en la outbox DENTRO de la misma transacción que los datos. Un worker separado lee la outbox, publica los eventos, y los marca como publicados.

```
┌──────────────────────────────────────────────────────────────────┐
│ Service.execute_disable_source()                                 │
│                                                                  │
│  ── DENTRO DE LA TRANSACCIÓN (UoW) ──                           │
│  1. source.disable(reason)      → registra SourceDisabled        │
│  2. source_repo.save(source)                                     │
│  3. outbox.append(SourceDisabled)  → INSERT en event_outbox      │
│  4. uow.commit()                → source + outbox persistidos    │
│                                                                  │
│  ── POST-COMMIT (fuera del UoW) ──                              │
│  5. (Opcional) publicar inmediatamente desde el service          │
│                                                                  │
│  ── ASYNC WORKER ──                                              │
│  6. Worker: SELECT FROM event_outbox WHERE published = FALSE     │
│  7. Worker: publish(events)                                      │
│  8. Worker: UPDATE event_outbox SET published = TRUE             │
└──────────────────────────────────────────────────────────────────┘
```

**Ventajas**:
- **Garantía de persistencia**: El evento está en la misma BD que los datos. Si el commit es exitoso, el evento existe.
- **At-least-once delivery**: El worker reintenta eventos fallidos.
- **Desacoplamiento**: El service no espera a que el evento se publique.

**Desventajas**:
- **Complejidad**: Tabla adicional, worker, lógica de retry, cleanup.
- **Latencia**: Entre el commit y la publicación hay una ventana (eventual consistency).
- **Eventual consistency**: Los consumidores del evento no ven el cambio inmediatamente.
- **Overhead de escritura**: INSERT adicional en la misma transacción.
- **Dead letters**: Eventos que nunca se publican requieren monitoreo.

**Esquema de tabla `event_outbox`**:

```sql
CREATE TABLE ingestion_event_outbox (
    id              UUID PRIMARY KEY,
    aggregate_id    UUID NOT NULL,
    event_type      VARCHAR(255) NOT NULL,  -- ej: "ingestion.SourceDisabled"
    event_data      JSONB NOT NULL,          -- payload serializado
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at    TIMESTAMPTZ,             -- NULL = no publicado aún
    retry_count     INTEGER NOT NULL DEFAULT 0,
    last_error      TEXT                     -- último error de publicación
);

CREATE INDEX ix_outbox_unpublished
    ON ingestion_event_outbox (created_at)
    WHERE published_at IS NULL;
```

### 2.3 Opción C: Two-Phase (híbrido)

**Descripción**: Combina lo mejor de ambos mundos. Los eventos se guardan en la outbox DENTRO de la transacción (garantía de persistencia), y el service INTENTA publicar inmediatamente después del commit (baja latencia). Si el publish falla, el outbox worker es el safety net.

```
┌─────────────────────────────────────────────────────────────────┐
│ Service.execute_disable_source()                                 │
│                                                                  │
│  ── DENTRO DE LA TRANSACCIÓN (UoW) ──                           │
│  1. source.disable(reason)      → registra SourceDisabled        │
│  2. source_repo.save(source)                                     │
│  3. outbox.append(SourceDisabled)  → INSERT en event_outbox      │
│  4. uow.commit()                → source + outbox persistidos    │
│                                                                  │
│  ── POST-COMMIT (intento inmediato) ──                          │
│  5. events = source.pull_events()                                │
│  6. try:                                                         │
│       event_publisher.publish_many(events)                       │
│       outbox.mark_published(events)     → opcional, no crítico   │
│     except Exception:                                            │
│       log.error("Publish failed, outbox will retry")             │
│       # El worker se encargará de publicar este evento           │
│                                                                  │
│  ── ASYNC WORKER (safety net) ──                                │
│  7. Worker periódico: SELECT FROM outbox WHERE published_at NULL │
│  8. Worker: publish(events)                                      │
│  9. Worker: UPDATE published_at = NOW()                          │
└─────────────────────────────────────────────────────────────────┘
```

**Ventajas**:
- **Baja latencia**: En el caso normal (broker disponible), el evento se publica inmediatamente.
- **Garantía de persistencia**: Si el publish inmediato falla, la outbox tiene el evento para retry.
- **Safety net**: El worker es el respaldo, no la vía principal.

**Desventajas**:
- **Dos writes**: El evento se escribe en outbox (garantía) y se publica al broker.
- **Complejidad**: Outbox + worker + lógica de publish inmediato.
- **Posible duplicación**: Si el publish inmediato es exitoso pero el commit del mark_published falla, el worker podría republicar. Se necesita idempotencia en el consumidor.

### 2.4 Evaluación y Decisión

**Decisión final: Opción A (Post-Commit Hooks) para la primera iteración.**

Justificación:

1. **Simplicidad > Features prematuras**. El sistema actual tiene 3 eventos (`SourceEnabled`, `SourceDisabled`, `RawArticleCollected`). Ninguno es crítico en tiempo real. La pérdida de un evento no causa inconsistencia de datos (los datos están en BD).

2. **Recuperación natural**. Para `SourceDisabled`/`SourceEnabled`: el scheduler verifica `source.is_active` antes de cada fetch. Para `RawArticleCollected`: el próximo fetch del feed eventualmente detectará artículos nuevos (la deduplicación por hash evita duplicados).

3. **Outlay de desarrollo**. El Outbox Pattern requiere: tabla, worker, lógica de retry, dead letters, monitoreo. Es una inversión significativa que no se justifica para el volumen actual de eventos.

4. **Evolución clara**. La migración a Opción C (Two-Phase) es directa:
   - Agregar tabla `event_outbox`.
   - En el `UnitOfWork.commit()`, insertar eventos en la outbox (necesitamos pasar los eventos al UoW).
   - Agregar worker.
   - Mantener el publish inmediato como opcional.

**Plan de evolución**:

| Iteración | Estrategia | Cuándo |
|-----------|-----------|--------|
| **1 (ahora)** | Opción A — Post-Commit Hooks | MVP, primer release |
| **2 (futuro)** | Opción C — Two-Phase (sin worker) | Cuando la pérdida de eventos sea problemática |
| **3 (futuro)** | Opción C completo (con worker) | Cuando se requiera at-least-once delivery |

**Caso de negocio: ¿qué pasa si un evento se pierde?**

- **SourceDisabled**: El scheduler intenta fetchear un source deshabilitado → falla rápido → log. No hay daño.
- **SourceEnabled**: El scheduler no fetchea un source habilitado → se pierde un ciclo de fetch → el próximo ciclo lo detecta.
- **RawArticleCollected**: El normalizador no procesa los artículos → se pierde una iteración → el próximo fetch los traerá (hash dedup los ignora).

En todos los casos, la consistencia es eventual. No hay pérdida de datos. Esto es ACEPTABLE para la primera iteración.

### 2.5 Implementación de la Opción Elegida

El Application Service sigue este patrón:

```python
def execute_disable_source(self, cmd: DisableSourceCommand) -> Result[SourceDetailDTO]:
    # ── FUERA DE TRANSACCIÓN ──
    source_id = SourceId.from_string(cmd.source_id)
    active_feeds = self._feed_repo.count_active_by_source(source_id)
    if active_feeds > 0:
        return Result.failure(Error(code=IngestionErrorCode.HAS_ACTIVE_FEEDS, ...))

    source_result = self._source_repo.find_by_id(source_id)
    if source_result.is_failure:
        return Result.failure(ErrorMapper.map_result_error(source_result.error))

    source = source_result.value

    # ── DENTRO DE TRANSACCIÓN ──
    try:
        with self._uow:
            source.disable(reason=cmd.reason)
            self._source_repo.save(source)
            self._uow.commit()

        # ── POST-COMMIT ──
        events = source.pull_events()
        if events:
            self._event_publisher.publish_many(events)

        return Result.success(SourceMapper.to_detail(source))

    except DomainError as e:
        return Result.failure(ErrorMapper.map_domain_error(e))
    except ConcurrentModificationError as e:
        return Result.failure(Error(
            code=ApplicationErrorCode.CONCURRENCY_CONFLICT,
            message=str(e),
        ))
    except InfrastructureError as e:
        return Result.failure(ErrorMapper.map_infra_error(e))
    except Exception as e:
        return Result.failure(Error(
            code=ApplicationErrorCode.OPERATION_FAILED,
            message=str(e),
        ))
```

**NOTA**: El `with self._uow:` crea la sesión en `__enter__` y la cierra en `__exit__`. Los repositorios ya tienen la sesión asignada (ver sección 6.2 para wiring).

**¿Qué pasa si `publish_many` falla?**

```python
# El service captura el error, lo loggea, pero NO falla la operación.
# El Result.success(dto) ya se retornó (o se retorna igual).
try:
    self._event_publisher.publish_many(events)
except Exception as e:
    logger.error(f"Failed to publish events for source {source_id}: {e}")
    # No propagar — el commit ya fue exitoso
```

**¿Por qué no propagar?** El commit de BD ya ocurrió. Devolver un error al cliente sería mentiroso (la operación fue exitosa). El evento perdido se recupera eventualmente (ver caso de negocio arriba). Esta es una decisión consciente de tradeoff entre consistencia y disponibilidad.

---

## 3. Nested Transactions (Savepoints)

**Estrategia: Savepoints para manejo granular de errores dentro de una transacción.**

```python
class SQLAlchemyUnitOfWork:
    def begin_savepoint(self) -> None:
        """Crea un savepoint dentro de la transacción actual."""
        if self._session is None:
            raise RuntimeError("UnitOfWork: no active session")
        self._session.begin_nested()

    def rollback_savepoint(self) -> None:
        """Revierte al savepoint anterior."""
        if self._session is None:
            raise RuntimeError("UnitOfWork: no active session")
        self._session.rollback()  # Revierte SOLO el savepoint activo
```

**Uso principal: RawArticleRepository.save_batch()**.

Cuando `save_batch()` inserta 500 artículos y el artículo #300 es duplicado, queremos:
1. Revertir SOLO el artículo #300 (no todo el batch).
2. Continuar con los artículos #301-#500.
3. Informar al caller cuántos se insertaron y cuántos fallaron.

Sin savepoints, un `IntegrityError` en cualquier punto revolvería toda la transacción (incluyendo el UPDATE del Feed que podría estar en la misma transacción).

```python
# Pseudocódigo de save_batch con savepoints:
def save_batch_with_report(self, articles: list[RawArticle]) -> BatchReport:
    """Persiste RawArticles. Los duplicados se saltan, no se revierte todo.

    Returns:
        BatchReport con inserted=count, skipped=count.
    """
    inserted = 0
    skipped = 0

    for article in articles:
        try:
            self._session.begin_nested()  # ← SAVEPOINT
            self._session.add(self._domain_to_model(article))
            self._session.flush()         # detecta IntegrityError aquí
            inserted += 1
        except IntegrityError:
            self._session.rollback()      # revierte SOLO este savepoint
            skipped += 1

    return BatchReport(inserted=inserted, skipped=skipped)
```

**¿Siempre usar savepoints?** NO. Savepoints tienen overhead (cada uno requiere un `SAVEPOINT` / `ROLLBACK TO SAVEPOINT` en BD). Se usan SOLO donde hay riesgo de errores granulares:
- `RawArticleRepository.save_batch()` — duplicados esperados.
- Operaciones que verifican unicidad antes de insertar (pre-check + insert).

Para operaciones normales (`save()`, `merge()`), no se usan savepoints. Si algo falla, toda la transacción se revierte.

**¿Qué pasa con `session.rollback()` en `save()` individual?** Ver sección 5.2.

---

## 4. Isolation Levels

### Estrategia por Entorno

| Entorno | Motor | Isolation Level | Razón |
|---------|-------|-----------------|-------|
| **Producción** | PostgreSQL | `READ COMMITTED` (default) | Suficiente para el modelo actual. Sin dirty reads, sin phantom reads problemáticos. |
| **Testing** | SQLite | `SERIALIZABLE` (default de SQLite) | SQLite solo tiene SERIALIZABLE. No hay opción. Es más restrictivo que PostgreSQL, pero para tests es aceptable (y detecta bugs de concurrencia temprano). |
| **Desarrollo** | PostgreSQL/SQLite | `READ COMMITTED` | Mismo que producción. |

### ¿Necesitamos REPEATABLE READ para algo?

| Escenario | ¿Necesita REPEATABLE READ? |
|-----------|---------------------------|
| Verificar `exists_by_name` + `save()` en la misma transacción | **NO**. READ COMMITTED es suficiente. Si entre el exists y el insert alguien más crea el mismo nombre, la UNIQUE constraint de BD rechazará el insert. |
| `count_active_by_source` + `disable(source)` | **NO**. La ventana entre count y disable es aceptable (consistencia eventual). |
| Optimistic locking | **NO**. El `version_id_col` de SQLAlchemy ya maneja concurrencia a nivel de fila. No se necesita isolation más fuerte. |

**Decisión**: Usar `READ COMMITTED` en producción. No hay casos que requieran `REPEATABLE READ` o `SERIALIZABLE` para las operaciones actuales.

**Configuración**:

```python
# PostgreSQL: el default ya es READ COMMITTED. No se requiere configuración extra.
engine = create_engine(
    "postgresql://...",
    isolation_level="READ COMMITTED",  # explícito por claridad
)

# SQLite: no se puede cambiar (siempre SERIALIZABLE). Ignorar.
```

---

## 5. Error Handling: IntegrityError → Domain Errors

### 5.1 Catálogo de IntegrityErrors

| # | Constraint | Origen | Error Code | ¿Dónde se captura? |
|---|------------|--------|------------|-------------------|
| 1 | `uq_news_source_name` | `save()` vía merge | `DUPLICATE_NEWS_SOURCE` | En el repositorio (capturando `IntegrityError` post-merge+flush) |
| 2 | `uq_feed_source_url` | `save()` vía merge | `DUPLICATE_FEED_URL` | En el repositorio |
| 3 | `uq_raw_article_feed_external` | `save()` vía add+flush | `DUPLICATE_ARTICLE` | En el repositorio |
| 4 | `uq_raw_article_feed_hash` | `save()` vía add+flush | `DUPLICATE_ARTICLE` | En el repositorio |
| 5 | `uq_category_slug` | `save()` vía merge | `CATEGORY_NOT_FOUND` (slug duplicado) | En el repositorio |
| 6 | `uq_topic_name` | `save()` vía merge | `TOPIC_NOT_FOUND` (name duplicado) | En el repositorio |
| 7 | `ck_raw_article_hash_length` | `save()` / `save_batch()` | `InvalidStateError` (I-17 violada) | En el dominio (RawArticle.__init__) |
| 8 | FK violación (source_id, feed_id, etc.) | `save()` | `InfrastructureError` (FK_VIOLATION) | En el repositorio |

### 5.2 Mapeo Centralizado

**Estrategia**: Cada repositorio captura `IntegrityError` y lo mapea a su error de dominio específico. NO hay un mapper global de IntegrityErrors porque el contexto (qué constraint se violó, qué entidad) es específico del repositorio.

```python
# En cada repositorio, el patrón es:
def save(self, entity) -> None:
    try:
        model = self._domain_to_model(entity)
        self._session.merge(model)
        self._session.flush()  # Forzar detección de violaciones
    except IntegrityError as e:
        self._session.rollback()  # Rollback parcial
        self._raise_domain_error(e, entity)

def _raise_domain_error(self, error: IntegrityError, entity) -> None:
    """Analiza el IntegrityError y lanza el error de dominio correspondiente."""
    if is_unique_violation(error, "uq_news_source_name"):
        raise InvalidStateError(
            f"DUPLICATE_NEWS_SOURCE: Source name '{entity.name}' already exists"
        )
    if is_unique_violation(error, "uq_feed_source_url"):
        raise InvalidStateError(
            f"DUPLICATE_FEED_URL: Feed URL '{entity.url}' already exists in source"
        )
    # Si no se reconoce, propagar como InfrastructureError
    raise InfrastructureError(f"Unexpected integrity error: {error}")
```

**¿Por qué `session.flush()` después de `merge()`?**

`merge()` no envía SQL inmediatamente. Acumula cambios para enviarlos en el próximo `flush()` (que ocurre automáticamente en `commit()`). Si queremos capturar `IntegrityError` dentro del repositorio, necesitamos `flush()` explícito.

Sin embargo, `flush()` después de `merge()` tiene un efecto secundario: si la entidad es nueva (INSERT), la fila se escribe en BD inmediatamente. Si después ocurre otro error en la transacción, esa fila se revierte con el rollback. Es seguro.

**Alternativa: Pre-check antes de insertar**.

En vez de capturar `IntegrityError`, algunos prefieren verificar la unicidad antes de insertar:

```python
def save(self, source: NewsSource) -> None:
    # Pre-check
    if self.exists_by_name(source.name):
        raise InvalidStateError(f"DUPLICATE_NEWS_SOURCE: ...")
    model = self._domain_to_model(source)
    self._session.merge(model)
```

**Decisión**: Usar pre-check + IntegrityError capture como defensa en profundidad.

- **Pre-check**: Mejor experiencia (error semántico inmediato, sin depender de parseo de mensajes de BD).
- **IntegrityError**: Defensa en profundidad para condiciones de carrera (el pre-check no es atómico con el insert).

```python
def save(self, source: NewsSource) -> None:
    # Pre-check para mejor experiencia
    if self.exists_by_name(source.name):
        raise InvalidStateError(
            f"DUPLICATE_NEWS_SOURCE: Source name '{source.name}' already exists"
        )
    try:
        model = self._domain_to_model(source)
        self._session.merge(model)
        self._session.flush()
    except IntegrityError as e:
        # Defensa en profundidad (condición de carrera)
        if is_unique_violation(e, "uq_news_source_name"):
            raise InvalidStateError(
                f"DUPLICATE_NEWS_SOURCE: Source name '{source.name}' already exists"
            ) from e
        raise InfrastructureError(...) from e
```

**NOTA**: El pre-check en repositorio DUPLICA la verificación que el Application Service ya hace. Esto es intencional:
- El service verifica unicidad antes de construir la entidad (evita trabajo desperdiciado).
- El repositorio verifica unicidad como defensa en profundidad (protege contra condiciones de carrera).

### 5.3 ConcurrentModificationError (Optimistic Lock)

**¿Dónde se captura?**

| Lugar | ¿Captura? | Razón |
|-------|-----------|-------|
| **Repositorio** | ❌ No | El repositorio llama `merge()`. `StaleDataError` ocurre en `flush()` o `commit()`. El repositorio no debería hacer flush después de merge (el merge solo prepara el objeto para sincronización). |
| **UnitOfWork.commit()** | ✅ Sí | Es el lugar correcto: capturamos `StaleDataError` durante el commit y lo convertimos en `ConcurrentModificationError`. |
| **Application Service** | ✅ Sí | Captura `ConcurrentModificationError` y lo mapea a `Result.failure(CONCURRENCY_CONFLICT)`. |

**¿Qué esperar de `ConcurrentModificationError`?**

```python
class ConcurrentModificationError(Exception):
    """Error de concurrencia: optimistic lock detectó modificación concurrente."""
    code = ApplicationErrorCode.CONCURRENCY_CONFLICT

    def __init__(self, message: str, entity_id: str | None = None):
        self.entity_id = entity_id
        super().__init__(message)
```

**¿Cómo se recupera?**

El Application Service puede:
1. **Reintentar**: Recargar el aggregate (con los datos actualizados) y re-aplicar la operación.
2. **Notificar**: Devolver `Result.failure(CONCURRENCY_CONFLICT)` para que el cliente decida.

Para la primera iteración, se recomienda la opción 2 (notificar). El reintento automático es complejo y propenso a loops infinitos.

### 5.4 Infrastructure Error Hierarchy

```python
class InfrastructureError(Exception):
    """Base de errores de infraestructura.
    
    Códigos de error mapeables en Application Layer:
    - DATABASE_CONNECTION_ERROR: La BD no está disponible.
    - INTEGRITY_VIOLATION: Violación de integridad no esperada.
    - QUERY_TIMEOUT: La query excedió el tiempo máximo.
    """
    code = "INFRASTRUCTURE_ERROR"

class DatabaseConnectionError(InfrastructureError):
    code = "DATABASE_CONNECTION_ERROR"

class IntegrityViolationError(InfrastructureError):
    code = "INTEGRITY_VIOLATION"

class QueryTimeoutError(InfrastructureError):
    code = "QUERY_TIMEOUT"
```

**Mapeo en Application Layer**:

```python
class ErrorMapper:
    """Mapeo de errores de infraestructura a errores de aplicación."""

    @staticmethod
    def map_infra_error(error: InfrastructureError) -> Error:
        """Convierte InfrastructureError a Error (Result.failure)."""
        if isinstance(error, ConcurrentModificationError):
            return Error(
                code=ApplicationErrorCode.CONCURRENCY_CONFLICT,
                message=str(error),
            )
        return Error(
            code=ApplicationErrorCode.OPERATION_FAILED,
            message=str(error),
        )
```

---

## 6. UnitOfWork in Services

### 6.1 Patrón de Uso

**Estrategia: El Application Service recibe el UnitOfWork por inyección de dependencia.**

```python
class SourceService:
    def __init__(
        self,
        source_repo: NewsSourceRepository,
        feed_repo: FeedRepository,
        category_repo: CategoryRepository,
        topic_repo: TopicRepository,
        uow: UnitOfWork,              # ← Inyectado
        event_publisher: EventPublisher,
        clock: ClockPort,
        uuid_provider: UUIDProvider,
    ) -> None:
        self._source_repo = source_repo
        self._feed_repo = feed_repo
        # ...
        self._uow = uow
        self._event_publisher = event_publisher
```

**¿Cómo se garantiza que el Service use la misma Session para todas las operaciones?**

Los repositorios SQLAlchemy obtienen su sesión del UnitOfWork activo. Hay dos enfoques:

**Enfoque A: Repositorios creados con la sesión del UoW (recomendado)**

```python
# En el wiring / Composition Root:
def execute_disable_source(cmd: DisableSourceCommand) -> Result[SourceDetailDTO]:
    with uow:  # uow crea una sesión
        # Crear repositorios con la sesión activa
        source_repo = SQLAlchemyNewsSourceRepository(uow.session)
        feed_repo = SQLAlchemyFeedRepository(uow.session)

        service = SourceService(
            source_repo=source_repo,
            feed_repo=feed_repo,
            uow=uow,
            event_publisher=event_publisher,
            clock=clock,
            uuid_provider=uuid_provider,
        )
        return service.execute_disable_source(cmd)
    # Al salir del with, uow cierra la sesión
```

**Enfoque B: Repositorios con "session holder" (más complejo)**

```python
class SessionHolder:
    """Holder de sesión que cambia según el UoW activo."""
    _current_session: Session | None = None

    def set_session(self, session: Session) -> None:
        self._current_session = session

    def clear(self) -> None:
        self._current_session = None

    @property
    def session(self) -> Session:
        if self._current_session is None:
            raise RuntimeError("No active session")
        return self._current_session

# Los repositorios referencian al holder:
class SQLAlchemyNewsSourceRepository:
    def __init__(self, session_holder: SessionHolder):
        self._session_holder = session_holder

    @property
    def _session(self) -> Session:
        return self._session_holder.session
```

**Decisión: Enfoque A (recomendado)**. Es más simple, más explícito, y no requiere estado global. El overhead de crear repositorios por transacción es despreciable (son objetos ligeros).

**El UnitOfWork como context manager en el Service**:

El patrón actual en los Services es:

```python
def execute_disable_source(self, cmd: ...) -> Result[SourceDetailDTO]:
    # ── Validación y AL rules (fuera de transacción) ──
    ...

    # ── Transacción ──
    with self._uow:
        try:
            # Operaciones de dominio
            source.disable(cmd.reason)
            self._source_repo.save(source)
            self._uow.commit()
        except DomainError as e:
            return Result.failure(...)
        except Exception as e:
            return Result.failure(...)

    # ── Post-commit ──
    events = source.pull_events()
    if events:
        self._event_publisher.publish_many(events)

    return Result.success(...)
```

**¿Qué está MAL en este patrón?** El `with self._uow` abre la transacción, pero si `return Result.failure(...)` se ejecuta DENTRO del `with`, el `__exit__` hará rollback (por la excepción no capturada — pero no hay excepción, solo un return).

**Corrección**: El return temprano (por AL rules) debe estar FUERA del `with`, no dentro. El patrón correcto es:

```python
def execute_disable_source(self, cmd: ...) -> Result[SourceDetailDTO]:
    # ── Validación y AL rules (fuera de transacción) ──
    source_result = self._source_repo.find_by_id(source_id)
    if source_result.is_failure:
        return Result.failure(...)  # ← return ANTES de abrir transacción
    source = source_result.value

    # ── Transacción ──
    with self._uow:
        try:
            source.disable(cmd.reason)
            self._source_repo.save(source)
            self._uow.commit()
        except DomainError as e:
            return Result.failure(...)
        except Exception as e:
            return Result.failure(...)

    # ── Post-commit ──
    events = source.pull_events()
    if events:
        self._event_publisher.publish_many(events)
    return Result.success(...)
```

### 6.2 Wiring (Inyección de Dependencias)

**Composition Root** (diagrama de flujo):

```
┌─────────────────────────────────────────────────────────────────┐
│ Composition Root                                                 │
│                                                                  │
│  1. Crear engine                                                 │
│     engine = create_engine(DATABASE_URL, ...)                    │
│                                                                  │
│  2. Crear session factory                                        │
│     session_factory = sessionmaker(bind=engine, ...)             │
│                                                                  │
│  3. Crear UnitOfWork (compartido)                                │
│     uow = SQLAlchemyUnitOfWork(session_factory)                  │
│                                                                  │
│  4. Para CADA transacción:                                       │
│     with uow:                                                    │
│         source_repo = SQLAlchemyNewsSourceRepository(uow.session)│
│         feed_repo = SQLAlchemyFeedRepository(uow.session)        │
│         # ... otros repos con la misma sesión ...                │
│                                                                  │
│         service = SourceService(                                 │
│             source_repo=source_repo,                             │
│             feed_repo=feed_repo,                                 │
│             uow=uow,                                             │
│             event_publisher=event_publisher,                     │
│             clock=clock,                                         │
│             uuid_provider=uuid_provider,                         │
│         )                                                        │
│         result = service.execute_register_source(cmd)            │
└─────────────────────────────────────────────────────────────────┘
```

**Alternativa: Fábrica de Services que crea repositorios automáticamente**:

```python
class ServiceFactory:
    """Fábrica que crea services con repositorios SQLAlchemy correctamente wireados."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        event_publisher: EventPublisher,
        clock: ClockPort,
        uuid_provider: UUIDProvider,
    ):
        self._session_factory = session_factory
        self._event_publisher = event_publisher
        self._clock = clock
        self._uuid_provider = uuid_provider

    def create_source_service(self) -> SourceService:
        """Crea SourceService con repositorios SQLAlchemy y UoW compartido."""
        uow = SQLAlchemyUnitOfWork(self._session_factory)

        # NOTA: Los repositorios se crean DENTRO del context manager del UoW.
        # Esto es responsabilidad del caller (o de un helper method).
        # Ver create_transactional() abajo.

        return SourceService(
            source_repo=SQLAlchemyNewsSourceRepository(...),  # necesita session
            feed_repo=SQLAlchemyFeedRepository(...),
            uow=uow,
            event_publisher=self._event_publisher,
            clock=self._clock,
            uuid_provider=self._uuid_provider,
        )
```

**Patrón `transactional` helper**:

```python
from contextlib import contextmanager
from collections.abc import Iterator

@contextmanager
def transactional(
    session_factory: sessionmaker[Session],
    event_publisher: EventPublisher,
    clock: ClockPort,
    uuid_provider: UUIDProvider,
) -> Iterator[SourceService]:
    """Context manager que provee un SourceService listo para usar.

    Uso:
        with transactional(session_factory, ...) as service:
            result = service.execute_disable_source(cmd)
    """
    with SQLAlchemyUnitOfWork(session_factory) as uow:
        source_repo = SQLAlchemyNewsSourceRepository(uow.session)
        feed_repo = SQLAlchemyFeedRepository(uow.session)
        category_repo = SQLAlchemyCategoryRepository(uow.session)
        topic_repo = SQLAlchemyTopicRepository(uow.session)

        yield SourceService(
            source_repo=source_repo,
            feed_repo=feed_repo,
            category_repo=category_repo,
            topic_repo=topic_repo,
            uow=uow,
            event_publisher=event_publisher,
            clock=clock,
            uuid_provider=uuid_provider,
        )
    # Al salir, el UoW cierra la sesión.
```

### 6.3 Queries (Solo Lectura)

**Los queries NO usan UnitOfWork**. Se crea una sesión efímera para cada query:

```python
class SQLAlchemySourceQueries:
    """Queries de solo lectura para NewsSource.

    NO usa UnitOfWork. Crea su propia sesión para cada query.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def find_by_id(self, source_id: SourceId) -> Result[SourceDetailDTO]:
        """Busca source y retorna DTO directamente (sin cargar entidad de dominio)."""
        with self._session_factory() as session:
            model = session.get(NewsSourceModel, source_id)
            if model is None:
                return Result.failure(...)
            # Mapear directamente a DTO (query optimization)
            return Result.success(SourceMapper.model_to_detail(model))

    def list_active_with_counts(self) -> list[SourceSummaryDTO]:
        """Lista sources activos con count de feeds en UNA query (optimizado)."""
        with self._session_factory() as session:
            stmt = (
                select(
                    NewsSourceModel,
                    func.count(FeedModel.id).label("feed_count"),
                )
                .outerjoin(FeedModel)
                .where(NewsSourceModel.is_active == True)
                .group_by(NewsSourceModel.id)
                .order_by(NewsSourceModel.name)
            )
            rows = session.execute(stmt).all()
            return [
                SourceSummaryDTO(
                    id=str(row.NewsSourceModel.id),
                    name=row.NewsSourceModel.name,
                    feed_count=row.feed_count,
                )
                for row in rows
            ]
```

**IMPORTANTE**: Las queries de solo lectura pueden optimizarse mapeando directamente a DTOs en vez de a entidades de dominio. Esto es el **Query Stack Pattern** (ver transaction-boundaries.md §5.2). Los repositorios de dominio cargan entidades completas; las queries de aplicación pueden hacer proyecciones optimizadas.

### 6.4 Múltiples Agregados en una Transacción

**Caso: RecordCollection + RawArticle save_batch en la misma transacción.**

```
┌─────────────────────────────────────────────────────────────┐
│ FeedService.execute_record_collection(...)                   │
│                                                              │
│  with self._uow:                                             │
│      # 1. Persistir RawArticles (batch)                     │
│      self._article_repo.save_batch(new_articles)              │
│                                                              │
│      # 2. Actualizar Feed (retry_count = 0)                  │
│      feed.record_collection(count=len(new_articles))          │
│      self._feed_repo.save(feed)                               │
│                                                              │
│      # 3. Commit atómico: RawArticles + Feed en UN commit   │
│      self._uow.commit()                                       │
│                                                              │
│  # 4. Post-commit: publicar evento                           │
│  events = feed.pull_events()                                  │
│  if events:                                                   │
│      self._event_publisher.publish_many(events)               │
└─────────────────────────────────────────────────────────────┘
```

**¿Es correcto mezclar dos tipos de AR en la misma transacción?**

**Sí**. Aunque cada AR es su propia frontera de consistencia, el Application Service puede coordinar múltiples ARs en una sola transacción. La frontera de consistencia significa que un AR no debe cargar otro AR para validar sus invariantes, pero el service puede persistir ambos en el mismo commit.

**Riesgo**: Transacciones largas (muchos inserts de RawArticle) pueden mantener locks por más tiempo. Si `save_batch()` procesa 500 artículos, la fila de Feed queda lockeada hasta el commit. Para el volumen actual, esto es aceptable.

**Recomendación**: Mantener transacciones cortas. Si `save_batch()` supera los 1000 artículos, considerar dividir en múltiples transacciones más pequeñas (cada una con su propio commit y evento).
