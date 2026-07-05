# Transaction Boundaries Design — Ingestion Bounded Context

> **Diseño de transacciones, commits, y publicación de eventos**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-03

---

## 1. Principios de Diseño

1. **Cada use case = una transacción**: No hay transacciones largas que abarquen múltiples use cases.
2. **Atomicidad**: Dentro de una transacción, todas las operaciones de persistencia pasan o ninguna.
3. **Eventos AFTER commit**: Los Domain Events se publican DESPUÉS del commit, no antes.
4. **UoW para mutaciones, no para lecturas**: Las queries (solo lectura) no usan UnitOfWork.
5. **Rollback en cualquier error**: Si algo falla dentro del bloque transaccional, todo se revierte.
6. **Eventos fuera de la transacción de BD**: La publicación de eventos es un paso separado del commit.

---

## 2. Flujo Estándar de Transacción

```
┌─────────────────────────────────────────────────────────────────────┐
│  APPLICATION SERVICE                                                 │
│                                                                      │
│  1. VALIDATE COMMAND                                                 │
│     ├── Verificar tipos y campos requeridos                         │
│     └── Si inválido → Result.failure (sin transacción)              │
│                                                                      │
│  2. LOAD AGGREGATES                                                  │
│     ├── Load source: NewsSourceRepository.find_by_id()              │
│     ├── Load feed: FeedRepository.find_by_id()                      │
│     └── Si no existe → Result.failure (sin transacción)            │
│                                                                      │
│  3. EXECUTE AL RULES                                                 │
│     ├── AL-01: count_active_by_source() > 0? → error               │
│     ├── AL-02: count_active_by_source() == 0? → error              │
│     ├── AL-03: source exist? → error                              │
│     ├── AL-04: source active? → error                              │
│     └── AL-05: feed exist? → error                                │
│                                                                      │
│  ╔══════════════════════════════════════════════════════════════════╗ │
│  ║  4. UoW BEGIN (unit_of_work.__enter__)                          ║ │
│  ║                                                                  ║ │
│  ║  5. CALL DOMAIN METHODS                                          ║ │
│  ║     ├── source.disable(reason)  → registra SourceDisabled       ║ │
│  ║     ├── feed.record_collection() → registra RawArticleCollected ║ │
│  ║     └── source.enable()  → registra SourceEnabled               ║ │
│  ║                                                                  ║ │
│  ║  6. SAVE AGGREGATES                                              ║ │
│  ║     ├── source_repo.save(source)                                ║ │
│  ║     ├── feed_repo.save(feed)                                    ║ │
│  ║     └── raw_article_repo.save(article)                          ║ │
│  ║                                                                  ║ │
│  ║  7. UoW COMMIT (unit_of_work.__exit__)                          ║ │
│  ╚══════════════════════════════════════════════════════════════════╝ │
│                                                                      │
│  8. PULL EVENTS                                                      │
│     ├── source.pull_events() → [SourceDisabled, ...]                │
│     └── feed.pull_events() → [RawArticleCollected]                  │
│                                                                      │
│  9. PUBLISH EVENTS (via EventPublisher)                              │
│     ├── event_publisher.publish_many(source_events)                 │
│     └── event_publisher.publish_many(feed_events)                   │
│                                                                      │
│  10. RETURN Result.success(dto)                                      │
│                                                                      │
│  11. (FUTURO) Publicar Integration Events                           │
│      └── Si hay IntegrationEvents, publicar aquí                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. ¿Qué está DENTRO y FUERA de la transacción?

### Dentro del UoW (transaccional)

| Operación | ¿Por qué? |
|-----------|-----------|
| `source_repo.save(source)` | Persistencia del aggregate |
| `feed_repo.save(feed)` | Persistencia del aggregate |
| `raw_article_repo.save(article)` | Persistencia del aggregate |
| `category_repo.save(category)` | Persistencia de entidad |
| `topic_repo.save(topic)` | Persistencia de entidad |
| `raw_article_repo.save_batch(articles)` | Persistencia batch atómica |

### Fuera del UoW (no transaccional)

| Operación | ¿Por qué? |
|-----------|-----------|
| Validación de comandos | No toca BD |
| AL rules verificaciones | Son lecturas, no mutaciones. Si la verificación y el commit no son atómicos, la ventana de inconsistencia es aceptable (consistencia eventual). |
| `pull_events()` | Opera en memoria, no toca BD |
| `event_publisher.publish()` | Publicación de eventos. No debe estar en la misma transacción de BD (riesgo de acoplar la disponibilidad del message broker a la BD). |
| Mapeo a DTOs | Operación en memoria, no toca BD |

### Decisión: AL rules FUERA de la transacción

Las AL rules (count_active_by_source, find_by_id para verificar existencia) se ejecutan **FUERA** del bloque transaccional. Esto es intencional:

- **Rendimiento**: Las lecturas no bloquean recursos de escritura.
- **Consistencia eventual aceptable**: Hay una ventana de inconsistencia entre la verificación y el commit (ej: se crea un Feed activo entre la verificación AL-01 y el disable). Esto es aceptable — el evento `SourceDisabled` se publica y el scheduler detiene los Feeds.
- **Complejidad evitada**: Mantener las lecturas fuera del UoW simplifica la implementación.

**Si en el futuro se requiere consistencia estricta**, se puede mover la verificación dentro del UoW usando `SELECT ... FOR UPDATE` o equivalente. Pero eso es premature optimization hoy.

---

## 4. Secuencia de Eventos vs Transacción

### 4.1 ¿Por qué AFTER commit?

```
✅ AFTER COMMIT (seleccionado):
  Commit BD → éxito → Publicar eventos
  Si publicar falla → BD ya commitió → eventos perdidos (at-least-once en futuro)

❌ BEFORE COMMIT:
  Publicar eventos → éxito → Commit BD
  Si commit BD falla → eventos ya publicados → estado inconsistente

❌ DENTRO DE LA MISMA TRANSACCIÓN (2PC):
  Commit BD + Publicar eventos en misma transacción
  Requiere XA/2PC → complejidad, no todos los brokers lo soportan
```

**Decisión: AFTER COMMIT (Outbox Pattern en el futuro)**

Para la primera iteración, publicar eventos después del commit es suficiente. Si un evento se pierde (commit ok, publish falla), no hay inconsistencia de datos — solo un retraso en la reacción. Para el pipeline de normalización, el próximo fetch del Feed eventualmente detectará los artículos.

**En el futuro**: Implementar Outbox Pattern (guardar eventos en la misma BD que los aggregates, un worker los lee y publica). Esto garantiza at-least-once delivery.

### 4.2 ¿Qué pasa si publish falla?

```
Escenario:
  1. Commit BD → OK (Feeds, RawArticles, etc. persistidos)
  2. event_publisher.publish(RawArticleCollected) → FALLA (broker caído)

Estado:
  - Los datos están persistidos
  - El evento no se publicó
  - El pipeline de normalización no se activa

Recuperación:
  - El próximo fetch del Feed creará RawArticles duplicados (detectados por
    exists_by_hash/exists_by_url) y llamará record_collection(count=0)
  - No hay pérdida de datos, solo retraso en el procesamiento
  - Aceptable para primera iteración

Mitigación futura:
  - Implementar Outbox Pattern (guardar eventos en tabla de eventos,
    worker dedicado publica con reintentos)
```

---

## 5. Transacciones por Tipo de Use Case

### 5.1 Use Cases de Mutación (usan UoW)

| # | Use Case | Agregados cargados | Agregados guardados | Eventos publicados |
|---|----------|-------------------|---------------------|-------------------|
| 1 | RegisterSource | — | NewsSource | — |
| 2 | UpdateSource | NewsSource | NewsSource | — |
| 3 | EnableSource | NewsSource | NewsSource | SourceEnabled |
| 4 | DisableSource | NewsSource | NewsSource | SourceDisabled |
| 5 | AssignCategoryToSource | Source, Category | Source | — |
| 6 | AssignTopicToSource | Source, Topic | Source | — |
| 7 | AssignCategoryToFeed | Feed, Category | Feed | — |
| 8 | AssignTopicToFeed | Feed, Topic | Feed | — |
| 9 | RegisterFeed | NewsSource (AL-03, AL-04) | Feed | — |
| 10 | UpdateFeed | Feed | Feed | — |
| 11 | PauseFeed | Feed | Feed | — |
| 12 | ActivateFeed | Feed | Feed | — |
| 13 | RecordCollection | Feed | Feed | RawArticleCollected |
| 14 | RecordFailure | Feed | Feed | — |
| 15 | CreateRawArticle | Feed (AL-05) | RawArticle | — |

### 5.2 Use Cases de Consulta (SIN UoW)

| # | Use Case | Repositorio | Paginación |
|---|----------|-------------|------------|
| 16 | FindSource | NewsSourceRepository | No |
| 17 | FindFeed | FeedRepository | No |
| 18 | FindArticle | RawArticleRepository | No |
| 19 | ListActiveSources | NewsSourceRepository | No |
| 20 | ListFeeds | FeedRepository | No |
| 21 | ListArticles | RawArticleRepository | Sí (page, size) |

---

## 6. Implementación en Código

```python
class SourceService:
    # ...

    def execute_disable_source(self, cmd: DisableSourceCommand) -> Result[SourceDetailDTO]:
        # ── FUERA DE TRANSACCIÓN ──
        # 1. Validación de comando
        if not cmd.reason.strip():
            raise CommandValidationError("Disable reason must not be empty")

        # 2. Cargar aggregate
        source_result = self._source_repo.find_by_id(cmd.source_id)
        if source_result.is_failure:
            return source_result  # propaga NEWS_SOURCE_NOT_FOUND

        source = source_result.value

        # 3. AL rules (verificaciones pre-transacción)
        active_count = self._feed_repo.count_active_by_source(cmd.source_id)
        if active_count > 0:
            return Result.failure(Error(
                code=IngestionErrorCode.HAS_ACTIVE_FEEDS,
                message=f"Source has {active_count} active feed(s)",
            ))

        # ── DENTRO DE TRANSACCIÓN ──
        try:
            with self._uow:
                # 4. Llamada al dominio
                source.disable(reason=cmd.reason)

                # 5. Persistencia
                self._source_repo.save(source)

            # ── DESPUÉS DEL COMMIT ──

            # 6. Recolectar eventos (en memoria)
            events = source.pull_events()

            # 7. Publicar eventos
            for event in events:
                self._event_publisher.publish(event)

            # 8. Mapear y retornar
            return Result.success(
                SourceMapper.to_detail(source)
            )

        except IngestionError as e:
            # Rollback automático por UnitOfWork.__exit__
            return Result.failure(ErrorMapper.map_domain_error(e))

        except InfrastructureError as e:
            # Rollback automático
            return Result.failure(ErrorMapper.map_infra_error(e))

        except Exception as e:
            # Rollback automático
            logger.exception(f"Unexpected error disabling source {cmd.source_id}")
            return Result.failure(Error(
                code=ErrorCode.UNKNOWN,
                message="Unexpected error",
            ))
```

---

## 7. Casos Especiales

### 7.1 RecordCollection + RawArticle (dos ARs en una transacción)

En un fetch, queremos:
1. Crear múltiples RawArticles (ARs)
2. Actualizar el Feed (AR): resetear retry_count

Esto involucra **dos tipos de AR** en la misma transacción. ¿Es correcto?

**Sí, es aceptable**. Aunque cada AR es su propia frontera de consistencia, el Application Service puede coordinar múltiples ARs en una sola transacción. La frontera de consistencia se refiere a que un AR no debe cargar a otro AR para validar invariantes — pero el Application Service puede guardar ambos en la misma transacción.

**Transacción**:
1. `raw_article_repo.save_batch(new_articles)` — persiste RawArticles
2. `feed_repo.save(feed)` — persiste Feed con retry_count reseteado
3. Commit
4. `feed.pull_events()` → RawArticleCollected
5. `event_publisher.publish(RawArticleCollected)`

### 7.2 Transacciones con save_batch

`RawArticleRepository.save_batch()` es atómico dentro de su implementación. Si el repositorio no soporta transacciones nativas, debe implementar compensación manual. El Application Service lo trata como una operación atómica dentro del UoW.

### 7.3 Optimistic Locking

Los aggregates mutables (NewsSource, Feed, Category, Topic) deben soportar optimistic locking. El Application Service no maneja esto explícitamente — es responsabilidad del repositorio. Si hay un conflicto de concurrencia, el repositorio lanza `InfrastructureError` que el service captura y mapea a `Result.failure`.
