# Aggregate Design — Ingestion Bounded Context

> **Decisiones de diseño de aggregates para el BC Ingestion**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-03
> Basado en: Sprint 3.1 Design v2.0 (T-01), Ubiquitous Language v1.0 (T-02)
>
> **Este documento detalla por qué cada entidad es o no es Aggregate Root,
> sus fronteras de consistencia, y las reglas de integridad entre aggregates.**

---

## Tabla de Contenidos

1. [Resumen de Aggregates](#1-resumen-de-aggregates)
2. [NewsSource (Aggregate Root)](#2-newssource-aggregate-root)
3. [Feed (Aggregate Root)](#3-feed-aggregate-root)
4. [RawArticle (Aggregate Root, Inmutable)](#4-rawarticle-aggregate-root-inmutable)
5. [Category (Entity, NO Aggregate Root)](#5-category-entity-no-aggregate-root)
6. [Topic (Entity, NO Aggregate Root)](#6-topic-entity-no-aggregate-root)
7. [Consistencia entre Aggregates](#7-consistencia-entre-aggregates)
8. [Escenarios de Falla y Recuperación](#8-escenarios-de-falla-y-recuperación)
9. [Concurrencia](#9-concurrencia)
10. [RawArticle: Entity-inheritance Decision](#10-rawarticle-entity-inheritance-decision)

---

## 1. Resumen de Aggregates

| Aggregate | Tipo | Identidad | ¿AR? | ¿Por qué? |
|-----------|------|-----------|------|-----------|
| **NewsSource** | Aggregate Root | `SourceId` | ✅ Sí | Ciclo de vida independiente. Punto de entrada de configuración. Múltiples Feeds lo referencian. |
| **Feed** | Aggregate Root | `FeedId` | ✅ Sí | Ciclo de vida propio (activo/pausado/inactivo). Reglas de negocio (retry, auto-pause, categorización). Unidad de ejecución. Referenciado por RawArticle. |
| **RawArticle** | Aggregate Root (inmutable) | `RawArticleId` | ✅ Sí | Volumen (millones de instancias). Frontera de consistencia en creación. Inmutable — sin concurrencia posterior. |
| **Category** | Entity | `CategoryId` | ❌ No | Tiene identidad pero no dependientes transaccionales. Consistencia eventual. Referenciada por ID. |
| **Topic** | Entity | `TopicId` | ❌ No | Tiene identidad pero no vida compleja ni invariantes transaccionales. Referenciado por ID. |

### Mapa de Referencias entre Aggregates

```
┌──────────────────┐
│   NewsSource     │ (AR)
│   id: SourceId   │
└────────┬─────────┘
         │ 1:N (referencia por source_id)
         ▼
┌──────────────────┐
│      Feed        │ (AR)
│   id: FeedId     │
│   source_id      │──→ SourceId
└────────┬─────────┘
         │ 1:N (referencia por feed_id)
         ▼
┌──────────────────┐
│   RawArticle     │ (AR, Inmutable)
│   id: RawArtId   │
│   feed_id        │──→ FeedId
└──────────────────┘
```

**Principio**: Las referencias entre aggregates son SIEMPRE por ID, nunca por objeto. Esto mantiene las fronteras de consistencia independientes y evita cascade-loading.

---

## 2. NewsSource (Aggregate Root)

### 2.1 ¿Por qué es Aggregate Root?

NewsSource es Aggregate Root por las siguientes razones:

1. **Ciclo de vida independiente**: NewsSource se crea, activa y desactiva de forma independiente. No pertenece a ningún otro aggregate — ES la raíz.
2. **Punto de entrada de configuración**: Es la primera entidad que se configura cuando se quiere ingerir contenido de una nueva plataforma.
3. **Referenciado por múltiples Feeds**: Varios Feeds referencian un solo NewsSource mediante `source_id`. Si NewsSource no fuera AR, los Feeds no tendrían un aggregate padre al cual pertenecer.
4. **Frontera de consistencia propia**: Las invariantes de NewsSource (nombre único, URL válida) son independientes del estado de sus Feeds. Las reglas que cruzan a Feed (desactivación, feeds activos) pertenecen al Application Layer.

### 2.2 Frontera de Consistencia

La frontera transaccional de NewsSource incluye:
- Sus propios atributos (`name`, `source_type`, `source_url`, `is_active`)
- Sus listas de referencias (`categories: list[CategoryId]`, `topics: list[TopicId]`)

**NO incluye**:
- Los objetos Feed que le pertenecen (son ARs separados)
- Los objetos Category o Topic referenciados (consistencia eventual)

### 2.3 Invariantes Transaccionales

| # | Invariante | ¿Cuándo se verifica? | ¿Cruza AR? |
|---|-----------|---------------------|-----------|
| I-01 | `name` MUST NOT be empty | En creación y modificación del nombre | ❌ No |
| I-02 | `name` MUST be unique across all NewsSources | En creación y cambio (vía repositorio) | ❌ No (intra-AR) |
| I-03 | `source_type` MUST be a valid SourceType | En creación y cambio de tipo | ❌ No |
| I-04 | `source_url` MUST be a valid URL | En creación y cambio (validado por VO) | ❌ No |

**Reglas movidas a Application Layer**:
- ~~I-05~~ "No desactivar si tiene Feeds activos" → **AL-01** (cruza a Feed AR)
- ~~I-06~~ "Requiere al menos un Feed activo" → **AL-02** (cruza a Feed AR)

### 2.4 Eventos que Cruzan la Frontera

| Evento | Cuándo | Consumidor esperado |
|--------|--------|---------------------|
| `SourceEnabled` | `enable()` exitoso | SchedulerDriver (reanuda Feeds del source) |
| `SourceDisabled` | `disable(reason)` exitoso | SchedulerDriver (detiene Feeds), AlertService |

### 2.5 Reglas de Referencia

| Referencia | Tipo | Regla |
|-----------|------|-------|
| `categories: list[CategoryId]` | Por ID (M:N) | No valida existencia de Category. Consistencia eventual. |
| `topics: list[TopicId]` | Por ID (M:N) | No valida existencia de Topic. Consistencia eventual. |
| Feeds que referencian este NewsSource | Inversa (1:N) | No se cargan al cargar NewsSource. Se consultan mediante FeedRepository. |

---

## 3. Feed (Aggregate Root)

### 3.1 ¿Por qué es Aggregate Root?

Feed es Aggregate Root por las siguientes razones:

1. **Ciclo de vida propio**: Feed tiene estados (activo, pausado, inactivo) que evolucionan independientemente de su NewsSource padre.
2. **Estado independiente**: `retry_count`, `sync_policy`, `categories`, `topics` — todo esto es estado interno que cambia por operaciones de fetch.
3. **Reglas de negocio de dominio**: La lógica de reintentos (`can_retry()`), auto-pausa al alcanzar `max_retries`, y categorización pertenece al dominio, no a infraestructura.
4. **Unidad de ejecución**: El scheduler referencia Feeds individualmente. Cada Feed tiene su propia política de sincronización.
5. **Referenciado por RawArticle**: RawArticle referencia Feed por `feed_id`. Si Feed no fuera AR, RawArticle no tendría un aggregate padre consistente.
6. **Rendimiento**: Si Feed fuera una entidad dentro de NewsSource, cargar NewsSource cargaría todos sus Feeds. Con N NewsSources y M Feeds por source, sería inviable. Cada Feed se carga y persiste independientemente.

### 3.2 Frontera de Consistencia

La frontera transaccional de Feed incluye:
- Sus propios atributos (`url`, `label`, `language`, `is_active`, `retry_count`)
- `sync_policy` (VO encapsulado)
- `categories: list[CategoryId]`, `topics: list[TopicId]`

**NO incluye**:
- El NewsSource padre (referenciado por `source_id` — consistencia eventual)
- Los RawArticles que le pertenecen (son ARs separados)
- Los objetos Category o Topic referenciados

### 3.3 Invariantes Transaccionales

| # | Invariante | ¿Cuándo se verifica? | ¿Cruza AR? |
|---|-----------|---------------------|-----------|
| I-05 | `url` MUST NOT be empty | En creación | ❌ No |
| I-06 | `url` MUST be unique within the parent NewsSource | En creación y cambio (vía repositorio) | ❌ No (intra-tipo) |
| I-07 | `retry_count` MUST be 0 after successful collection | En `record_collection()` | ❌ No |
| I-08 | MUST pause if `retry_count >= max_retries` | En `record_failure()` | ❌ No |
| I-09 | MUST NOT fetch while paused | En Application Service | ❌ No |
| I-10 | MUST NOT fetch if `is_active = False` | En Application Service | ❌ No |

**Reglas movidas a Application Layer**:
- ~~I-09~~ "source_id reference existente" → **AL-03** (cruza a NewsSource AR)
- ~~I-10~~ "no crear bajo NewsSource inactivo" → **AL-04** (cruza a NewsSource AR)

### 3.4 Eventos que Cruzan la Frontera

| Evento | Cuándo | Consumidor esperado |
|--------|--------|---------------------|
| `RawArticleCollected` | `record_collection()` con count > 0 | Normalization Pipeline (vía Application Service) |

### 3.5 Reglas de Referencia

| Referencia | Tipo | Regla |
|-----------|------|-------|
| `source_id: SourceId` | Por ID (N:1) | No se carga el NewsSource. Consistencia eventual. |
| `categories: list[CategoryId]` | Por ID (M:N) | No valida existencia de Category. Consistencia eventual. |
| `topics: list[TopicId]` | Por ID (M:N) | No valida existencia de Topic. Consistencia eventual. |
| RawArticles que referencian este Feed | Inversa (1:N) | No se cargan al cargar Feed. Se consultan mediante RawArticleRepository. |

### 3.6 Reglas de Retry y Auto-pause

```
Feed.record_failure(error):
  1. Incrementa retry_count en 1
  2. Si NOT can_retry() (retry_count >= sync_policy.max_retries):
     a. Marca is_active = False (auto-pause)
     b. Retorna FeedFailureResult(paused=True, retry_count=retry_count)
  3. Si can_retry():
     a. Retorna FeedFailureResult(paused=False, retry_count=retry_count)

Feed.record_collection(batch_id, count):
  1. Resetea retry_count a 0
  2. Emite RawArticleCollected si count > 0

Feed.can_retry():
  → retry_count < sync_policy.max_retries
```

---

## 4. RawArticle (Aggregate Root, Inmutable)

### 4.1 ¿Por qué es Aggregate Root?

RawArticle es Aggregate Root por **razones de volumen y consistencia en creación**:

1. **Volumen**: Pueden existir millones de RawArticles. Si RawArticle fuera una entidad hija dentro de Feed, cargar un Feed cargaría TODOS sus RawArticles — arquitectónicamente inviable. Cada RawArticle debe ser cargable y persistible independientemente.

2. **Frontera de consistencia en creación**: Aunque es inmutable (sin consistencia posterior), la creación misma requiere protección de invariantes:
   - Unicidad de `external_id + feed_id`
   - Unicidad de `content_hash` dentro del Feed
   - Validación de todos los VOs en el constructor

3. **Sin dependencias externas**: RawArticle no depende del estado de ningún otro aggregate para su consistencia. Esto lo hace un AR ideal — frontera pequeña y bien definida.

### 4.2 ¿Por qué NO es Aggregate Root por herencia técnica?

RawArticle **hereda de `Entity`** (no de `AggregateRoot` de Foundation) porque:

- Es **inmutable**: no tiene métodos de mutación, no hay transacciones que commitear.
- **No emite eventos**: no necesita `_events` ni `register_event()`.
- AggregateRoot en Foundation proporciona `_events` y `pull_events()`, que RawArticle nunca usaría.

RawArticle se **documenta como Aggregate Root** por convención — su frontera de consistencia y necesidades de persistencia independiente lo hacen AR en la práctica. Ver ADR-023.

### 4.3 Frontera de Consistencia

La frontera transaccional de RawArticle es **unicamente su creación**:
- Todos los atributos se validan y asignan en el constructor
- Una vez creado, no hay operaciones de modificación
- No hay referencias a otros aggregates que necesiten validación transaccional

**NO incluye**:
- El Feed padre (referenciado por `feed_id` — consistencia eventual)
- Topics (futura relación M:N, consistencia eventual)

### 4.4 Invariantes Transaccionales

| # | Invariante | ¿Cuándo se verifica? | ¿Cruza AR? |
|---|-----------|---------------------|-----------|
| I-11 | **IMMUTABLE** — No modification after creation | En diseño (sin setters, sin métodos) | ❌ No |
| I-12 | `external_id + feed_id` MUST be unique | En creación (vía repositorio) | ❌ No (intra-tipo) |
| I-13 | `content_hash` MUST be unique within the same Feed | En creación (vía repositorio) | ❌ No (intra-tipo) |
| I-14 | `fetched_at` >= `published_at` (if present) | En el constructor | ❌ No |
| I-15 | `title` MUST NOT be empty | Validado por ArticleTitle VO | ❌ No |
| I-16 | `url` MUST be a valid URL | Validado por ArticleUrl VO | ❌ No |
| I-17 | `content_hash` MUST be a valid SHA-256 (64 hex chars) | En el constructor | ❌ No |

**Regla movida a Application Layer**:
- ~~I-21~~ "feed_id reference existente" → **AL-05** (cruza a Feed AR)

### 4.5 Reglas de Referencia

| Referencia | Tipo | Regla |
|-----------|------|-------|
| `feed_id: FeedId` | Por ID (N:1) | No se carga el Feed. Consistencia eventual. |
| Topics (futuro) | Por ID (M:N futura) | No implementado en Sprint 3.1. |

---

## 5. Category (Entity, NO Aggregate Root)

### 5.1 ¿Por qué NO es Aggregate Root?

Category NO es Aggregate Root por las siguientes razones:

1. **Sin entidades dependientes**: Category tiene identidad y ciclo de vida, pero no tiene entidades hijas que requieran consistencia transaccional. Sus "hijos" (subcategorías) son la misma entidad Category con un `parent_id`.
2. **Consistencia eventual**: Category es referenciada por ID desde NewsSource y Feed. No hay invariantes que requieran que Category y sus referenciadores estén en la misma transacción.
3. **Referencia, no contención**: Category es un concepto de referencia (como una etiqueta). No contiene a NewsSource ni a Feed. Son los agregados quienes contienen listas de `CategoryId`.
4. **Sin eventos de dominio**: Category no emite eventos. No hay procesos que deban dispararse cuando una categoría cambia.

### 5.2 ¿Por qué NO es Value Object?

Category debe tener identidad (`CategoryId`) porque es referenciada por múltiples agregados. Si fuera un VO:
- Se copiaría (incrustaría) en cada NewsSource y Feed que la use
- Renombrar una categoría requeriría actualizar todas las copias
- No se podría cambiar el slug o la jerarquía centralizadamente

### 5.3 Consistencia de Jerarquía

La jerarquía de categorías (vía `parent_id`) es una estructura de árbol que debe mantener:

| Regla | Verificación |
|-------|-------------|
| No auto-referencia (`parent_id != id`) | En `change_parent()` |
| No ciclos (A→B→C→A) | En `change_parent()` — recorrido hacia arriba |
| Cascade de desactivación | En `deactivate()` — desactiva subcategorías activas |
| Slug único global | En creación y cambio de slug (vía repositorio) |

---

## 6. Topic (Entity, NO Aggregate Root)

### 6.1 ¿Por qué NO es Aggregate Root?

Topic NO es Aggregate Root por las siguientes razones:

1. **Sin complejidad transaccional**: Topic solo tiene nombre, descripción y estado activo/inactivo. No hay invariantes que crucen agregados.
2. **Sin entidades dependientes**: Nadie depende de Topic para su consistencia. Es un concepto de referencia puro.
3. **Sin eventos de dominio**: Topic no emite eventos.
4. **Volumen bajo**: Los topics son una lista curada y limitada. No se justifica una frontera transaccional independiente.

### 6.2 ¿Por qué NO es Value Object?

Topic debe tener identidad (`TopicId`) porque:
- Es referenciado por ID desde NewsSource y Feed
- Renombrar un topic debe ser posible sin modificar todos los agregados que lo referencian
- Ciclo de vida (activar/desactivar) implica cambio de estado, no es un valor inmutable

---

## 7. Consistencia entre Aggregates

### 7.1 Principios Generales

1. **Todas las referencias entre aggregates son por ID** (nunca por objeto)
2. **Cada AR es una frontera de consistencia transaccional**
3. **Entre ARs: consistencia eventual** — los cambios en un AR pueden no ser visibles inmediatamente en otro
4. **Las referencias a Entities (Category, Topic) también son por ID y consistencia eventual**
5. **La validación de existencia de referencias se hace en Application Service**, no en el dominio

### 7.2 Tabla de Reglas de Consistencia

| Regla | Desde | Hacia | Tipo | Protección | Ref. |
|-------|-------|-------|------|------------|------|
| R-01 | Feed.source_id | NewsSource | Eventual | Application Service verifica existencia | AL-03 |
| R-02 | Feed bajo NewsSource inactivo | Feed → NewsSource | Eventual | Application Service verifica is_active | AL-04 |
| R-03 | RawArticle.feed_id | Feed | Eventual | Application Service verifica existencia | AL-05 |
| R-04 | NewsSource disable con Feeds activos | NewsSource → Feed | Eventual | Application Service verifica count | AL-01 |
| R-05 | NewsSource enable sin Feeds activos | NewsSource → Feed | Eventual | Application Service verifica count | AL-02 |
| R-06 | Category.parent_id | Category | Eventual + Jerarquía | `change_parent()` valida no-ciclo y no-self-parent | — |
| R-07 | NewsSource.categories | Category | Eventual | Application Service verifica existencia | — |
| R-08 | Feed.categories | Category | Eventual | Application Service verifica existencia | — |
| R-09 | NewsSource.topics | Topic | Eventual | Application Service verifica existencia | — |
| R-10 | Feed.topics | Topic | Eventual | Application Service verifica existencia | — |
| R-11 | Url única por source | Feed | Inmediata | `FeedRepository.exists_by_source_and_url()` | I-06 |
| R-12 | external_id único por feed | RawArticle | Inmediata | `RawArticleRepository` en save | I-12 |
| R-13 | content_hash único por feed | RawArticle | Inmediata | `RawArticleRepository` en save | I-13 |

### 7.3 Justificación de Consistencia Eventual

La consistencia eventual entre ARs es aceptable porque:

- **No hay invariantes跨-aggregate que requieran atomicidad**: Un Feed puede existir sin que su NewsSource esté cargado. Un RawArticle puede existir sin que su Feed esté cargado.
- **El costo de la consistencia inmediata es alto**: Requeriría transacciones distribuidas o locks que escalan mal.
- **La ventana de inconsistencia es pequeña**: Las operaciones de creación/actualización de referencias ocurren en el mismo request, generalmente en milisegundos.
- **Los mecanismos de detección existen**: Si un Feed referencia un NewsSource que no existe (escenario de borrado), el sistema lo detecta en el próximo fetch y puede alertar.

---

## 8. Escenarios de Falla y Recuperación

### 8.1 Falla en Feed.fetch: RawArticle creado pero Feed.retry_count no reseteado

```
Escenario:
  1. Application Service ejecuta fetch para Feed X
  2. Obtiene artículos, crea RawArticle (AR) → OK
  3. Llama a Feed.record_collection() → FALLA (error de infraestructura)

Estado resultante:
  - RawArticle existe en el repositorio
  - Feed.retry_count NO se reseteó
  - Feed.last_run NO se actualizó

Recuperación:
  - En el próximo fetch, los artículos duplicados se detectan por
    RawArticleRepository.exists_by_hash() o exists_by_url()
  - No se crean RawArticles duplicados
  - El fetch reporta count=0 (todos duplicados) y record_collection()
    se llama con count=0 — el retry_count se resetea

Impacto:
  - Una ejecución "perdida": los artículos se recolectaron pero el estado
    del Feed no se actualizó hasta el próximo fetch
  - Aceptable: no hay pérdida de datos, solo retraso en el reset de retry_count
```

### 8.2 Falla en Feed.fetch: RawArticle NO creado pero retry_count incrementado

```
Escenario:
  1. Application Service ejecuta fetch para Feed X
  2. Fetch externo falla (timeout, HTTP error)
  3. Llama a Feed.record_failure(error) → OK, retry_count incrementado
  4. Intenta guardar Feed → FALLA

Estado resultante:
  - RawArticle no existe (no se creó)
  - Feed.retry_count se incrementó en memoria pero NO se persiste

Recuperación:
  - El próximo intento de fetch comienza con el retry_count anterior
  - El reintento ocurre según la política de backoff del scheduler
  - No hay pérdida de datos porque no se crearon RawArticles

Impacto:
  - Se "pierde" un intento de retry del contador
  - El Feed podría tardar un intento más en llegar a auto-pause
  - Aceptable: el auto-pause eventualmente ocurrirá
```

### 8.3 Desactivación de NewsSource con Feeds activos

```
Escenario:
  1. Usuario llama a NewsSource.disable(reason)
  2. NewsSource.can_be_disabled() verifica si tiene Feeds activos
  3. La verificación se hace contra el repositorio (no contra objetos en memoria)
     → FeedRepository.count_active_by_source(source_id) > 0

Protección:
  - Si count_active_by_source > 0 → disable() retorna Result.failure(HAS_ACTIVE_FEEDS)
  - El usuario debe primero desactivar/pausar todos los Feeds del source

Consistencia:
  - Hay una ventana de inconsistencia entre la verificación y la desactivación
    (otro proceso podría crear un Feed activo en ese intervalo)
  - Aceptable: el evento SourceDisabled se publica y el scheduler detiene los Feeds
  - Cualquier Feed creado después del disable tendrá source_id de un NewsSource inactivo,
    pero I-10 lo protege en creación
```

### 8.4 Duplicación de RawArticle por concurrencia

```
Escenario:
  1. Dos workers ejecutan fetch para el mismo Feed simultáneamente
  2. Ambos obtienen el mismo artículo
  3. Ambos intentan crear RawArticle con el mismo external_id y feed_id

Protección:
  - RawArticleRepository.save() verifica DUPLICATE_ARTICLE en la capa de persistencia
  - El segundo save falla con error de unicidad
  - El Application Service captura el error y lo maneja (log, skip)

Impacto:
  - Un worker "pierde" la creación pero no hay datos corruptos
  - La deduplicación en memoria (pre-save) reduce la probabilidad
```

---

## 9. Concurrencia

### 9.1 Estrategia por Aggregate

| Aggregate | Estrategia de Concurrencia | Justificación |
|-----------|---------------------------|---------------|
| **NewsSource** | Optimistic Lock (versión/fecha) | Baja contención. Principalmente operaciones de configuración. |
| **Feed** | Optimistic Lock (versión) | Contención media (fetches concurrentes). `retry_count` es la principal fuente de conflicto. |
| **RawArticle** | Sin concurrencia (inmutable) | Solo creación. No hay actualizaciones concurrentes. La unicidad se protege a nivel BD (unique constraints). |
| **Category** | Optimistic Lock (versión) | Baja contención. Operaciones administrativas. |
| **Topic** | Optimistic Lock (versión) | Baja contención. Operaciones administrativas. |

### 9.2 Consideraciones para Feed (alta contención)

Feed es el aggregate con mayor probabilidad de contención porque:
- Es la unidad de fetch — múltiples workers pueden intentar actualizar el mismo Feed
- `retry_count` es un punto de contención: dos fallos concurrentes pueden incrementarlo dos veces

**Mecanismo de protección**:
- Cada Feed tiene un `version` (o `updated_at`) para optimistic locking
- Si dos workers actualizan concurrentemente, uno gana y el otro reintenta
- `record_collection()` resetea `retry_count` a 0 — si un worker exitoso gana y otro fallido pierde, el contador se resetea correctamente

### 9.3 RawArticle: Sin Concurrencia

RawArticle es inmutable: una vez creado, nunca se modifica. Esto elimina toda posibilidad de conflictos de escritura concurrente. La única consideración es:
- **Unique constraints**: `(feed_id, external_id)` y `(feed_id, content_hash)` deben ser únicos a nivel BD
- **Deduplicación pre-save**: Verificar existencia antes de crear reduce escrituras fallidas

---

## 10. RawArticle: Entity-inheritance Decision

### 10.1 El Problema

RawArticle es conceptualmente un Aggregate Root (frontera de consistencia propia, volumen masivo, persistencia independiente). Sin embargo, es **técnicamente inmutable** — no tiene métodos de mutación, no emite eventos de dominio, y no requiere `_events` ni `register_event()`.

En Foundation, `AggregateRoot` hereda de `Entity` y agrega:
- `_events: list[DomainEvent]` — acumula eventos para ser despachados
- `register_event(event)` — registra un evento
- `pull_events()` — recolecta y limpia los eventos

RawArticle nunca usa ninguna de estas capacidades.

### 10.2 Alternativas Consideradas

| Alternativa | Descripción | Decisión |
|-------------|-------------|----------|
| **A: Heredar de AggregateRoot** | RawArticle hereda de AggregateRoot aunque nunca use eventos. | ❌ Descartada. Overhead innecesario y confusión semántica (RawArticle no tiene "comportamiento de aggregate"). |
| **B: Heredar de Entity** | RawArticle hereda de Entity. Se documenta como AR por convención. | ✅ SELECCIONADA. Simple, sin overhead, semánticamente correcto (Entity = tiene identidad). |
| **C: Decorador/Marker** | Usar un decorador `@aggregate_root` o clase marker `AggregateRootMarker` para indicar que Entity actúa como AR. | ❌ Descartada por ahora. Foundation FROZEN impide agregar markers. Se reconsidera si Foundation agrega este mecanismo. |

### 10.3 Decisión Final

**RawArticle hereda de `Entity` (Foundation), se documenta como Aggregate Root.**

Esta decisión:
- Elimina el overhead de `_events` para una entidad inmutable que nunca emite eventos
- Mantiene la semántica correcta (Entity = tiene identidad; AR = frontera de consistencia)
- Requiere documentación explícita (este documento y ADR-023)
- Puede migrarse en el futuro si Foundation introduce un marcador `AggregateRootMarker`

### 10.4 Impacto en Código

```python
# En lugar de:
class RawArticle(AggregateRoot):  # ❌ Overhead innecesario
    ...

# Se implementa:
class RawArticle(Entity):  # ✅ Hereda de Entity, documentado como AR
    id: RawArticleId
    feed_id: FeedId
    # ... demás atributos

    def __init__(self, ...):
        # Constructor con validación de invariantes
        # NO tiene register_event(), NO tiene pull_events()
        # NO tiene setters, NO tiene métodos de mutación
```

### 10.5 Documentación Relacionada

- **ADR-023**: Archivo ADR formal con contexto completo, consecuencias y alternativas
- **Sección 4** de este documento: Detalle de la frontera de consistencia de RawArticle
- **T-01 (Ingestion Domain Design v2.0)**: Sección 2.4 con especificación completa de RawArticle
