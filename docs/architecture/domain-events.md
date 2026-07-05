# Domain Events Catalog — Ingestion Bounded Context

> **Catálogo de eventos de dominio del BC Ingestion**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-03
> Basado en: Sprint 3.1 Design v2.0 (T-01), Aggregate Design v1.0 (T-03)
>
> **Este documento cataloga los 3 Domain Events del BC Ingestion.**
> Los Domain Events son intra-BC — nunca cruzan el límite del Bounded Context.

---

## Tabla de Contenidos

1. [Principios de Diseño](#1-principios-de-diseño)
2. [RawArticleCollected](#2-rawarticlecollected)
3. [SourceEnabled](#3-sourceenabled)
4. [SourceDisabled](#4-sourcedisabled)
5. [Eventos Descartados (YAGNI)](#5-eventos-descartados-yagni)
6. [Consideraciones de Event Sourcing](#6-consideraciones-de-event-sourcing)

---

## 1. Principios de Diseño

### 1.1 Definiciones Base

Todos los Domain Events heredan de `DomainEvent` (Foundation):

```python
@dataclass(frozen=True)
class DomainEvent:
    event_id: UUID        # Identidad única del evento
    event_name: str       # Nombre del evento (ej: "RawArticleCollected")
    occurred_at: datetime  # Timestamp de ocurrencia
```

Los eventos se registran en los Aggregate Roots vía `register_event(event)` y se recolectan vía `pull_events()`.

### 1.2 Principios

1. **Los Domain Events son INMUTABLES**: `@dataclass(frozen=True)`. Una vez creados, no se modifican.
2. **Son intra-BC**: Los Domain Events solo existen dentro del BC Ingestion. Para comunicación cross-BC se usan Integration Events (definidos en Application Layer).
3. **Representan hechos consumados**: El nombre del evento está en pasado (`SourceEnabled`, `RawArticleCollected`). No son comandos ni solicitudes.
4. **Cada evento tiene un publisher y uno o más consumidores**: Los consumidores son componentes dentro del mismo BC.
5. **YAGNI estricto**: Solo se definen eventos que tienen al menos un consumidor identificado. Eventos sin consumidor se agregan cuando sean necesarios.

### 1.3 Mecanismo de Publicación

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOMAIN EVENT FLOW                            │
│                                                                  │
│  1. AR ejecuta método de dominio:                               │
│     Feed.record_collection() → RawArticleCollected              │
│     NewsSource.enable() → SourceEnabled                         │
│     NewsSource.disable() → SourceDisabled                       │
│                                                                  │
│  2. AR llama a self.register_event(event) — acumula en _events  │
│                                                                  │
│  3. Application Service llama a ar.pull_events() — obtiene      │
│     los eventos acumulados y los envía al bus interno           │
│                                                                  │
│  4. Los consumidores reciben el evento y ejecutan su lógica     │
│                                                                  │
│  Nota: El AR solo REGISTRA el evento. No lo publica.            │
│  La publicación es responsabilidad del Application Service.      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. RawArticleCollected

### 2.1 Ficha del Evento

| Campo | Especificación |
|-------|---------------|
| **Nombre** | `RawArticleCollected` |
| **Definición** | Indica que uno o más RawArticles han sido recolectados exitosamente de un Feed después del proceso de fetch y deduplicación. |
| **Cuándo ocurre** | Cuando `Feed.record_collection(batch_id, count)` es llamado exitosamente con `count > 0`. |
| **Categoría** | Domain Event (intra-BC) |
| **Publisher** | `Feed` (Aggregate Root) — llamado desde Application Service |
| **Consumidores** | Application Service → Normalization Pipeline |
| **Caso de uso** | Sprint 3.6+ (cuando exista el pipeline de normalización) |

### 2.2 Firma Técnica

```python
@dataclass(frozen=True)
class RawArticleCollected(DomainEvent):
    # Hereda de DomainEvent (Foundation):
    #   event_id: UUID          — auto-generado
    #   event_version: int = 1  — schema version
    #   occurred_at: datetime   — auto-generado
    #   event_name: str         — property, inferido del class name

    # Payload específico
    feed_id: FeedId       # Feed del que se recolectaron los artículos
    batch_id: UUID        # Batch al que pertenecen los artículos
    count: int            # Cantidad de artículos nuevos (post-dedup)
    collected_at: datetime  # Momento exacto de la colección
```

### 2.3 Semántica

```
¿Qué significa?
  "Hay count artículos crudos nuevos en el batch batch_id,
  obtenidos del feed feed_id, listos para normalizar."

¿Qué NO significa?
  ❌ No significa que los artículos ya estén normalizados
  ❌ No significa que estén disponibles para Research BC
  ✅ Solo significa que hay materia prima nueva para procesar

¿Por qué existe?
  Es el evento más importante del BC. Sin él, el pipeline de
  normalización no se activa. Es el puente entre la ingesta
  cruda (RawArticle) y el procesamiento (Normalization).
```

### 2.4 Secuencia de Publicación

```
ApplicationService.execute_fetch(feed_id):
  1. Carga Feed (FeedRepository)
  2. Ejecuta fetch externo → obtiene RawArticle candidates
  3. Deduplica (RawArticleRepository.exists_by_hash / exists_by_url)
  4. Crea RawArticles nuevos (RawArticleRepository.save_batch)
  5. Si count > 0:
     a. Feed.record_collection(batch_id, count)
        → Feed registra RawArticleCollected internamente
     b. FeedRepository.save(feed)
     c. events = feed.pull_events()
     d. EventBus.publish(events)  → NormalizationPipeline.execute()
```

### 2.5 Consumidores

| Consumidor | Acción | Efecto |
|-----------|--------|--------|
| **Normalization Pipeline** (Application Service) | `execute(batch_id)` | Inicia el pipeline: carga RawArticles del batch, los normaliza, produce NormalizedItems, publica IntegrationEvent. |

---

## 3. SourceEnabled

### 3.1 Ficha del Evento

| Campo | Especificación |
|-------|---------------|
| **Nombre** | `SourceEnabled` |
| **Definición** | Indica que un NewsSource ha sido habilitado para ingesta. Los schedulers deben reanudar la ingesta de sus Feeds. |
| **Cuándo ocurre** | Cuando `NewsSource.enable()` es llamado exitosamente desde un Application Service. |
| **Categoría** | Domain Event (intra-BC) |
| **Publisher** | `NewsSource` (Aggregate Root) |
| **Consumidores** | Application Service → SchedulerDriver, Monitor, Logger |

### 3.2 Firma Técnica

```python
@dataclass(frozen=True)
class SourceEnabled(DomainEvent):
    # Hereda de DomainEvent (Foundation):
    #   event_id: UUID          — auto-generado
    #   event_version: int = 1  — schema version
    #   occurred_at: datetime   — auto-generado
    #   event_name: str         — property, inferido del class name

    # Payload específico
    source_id: SourceId    # NewsSource que se habilitó
    enabled_at: datetime   # Momento exacto de la habilitación
```

### 3.3 Semántica

```
¿Qué significa?
  "El NewsSource source_id ahora está activo. Sus Feeds deben
  reanudar su programación normal de fetch."

¿Qué NO significa?
  ❌ No significa que los Feeds estén activos (pueden estar pausados)
  ❌ No significa que el fetch se reanude inmediatamente
  ✅ Significa que el scheduler debe considerar los Feeds de este
     source como candidatos para fetch

¿Por qué existe?
  Permite que componentes externos reaccionen a la reactivación
  de una fuente sin tener que pollear el estado. Sin este evento,
  el scheduler tendría que consultar periódicamente si hay sources
  que se reactivaron.
```

### 3.4 Secuencia de Publicación

```
ApplicationService.enable_source(source_id):
  1. Carga NewsSource (NewsSourceRepository)
  2. NewsSource.enable()
     → NewsSource registra SourceEnabled internamente
     → Verifica AL-02 (al menos un Feed activo)
  3. NewsSourceRepository.save(news_source)
  4. events = news_source.pull_events()
  5. EventBus.publish(events) → SchedulerDriver.resume_source(source_id)
```

### 3.5 Consumidores

| Consumidor | Acción | Efecto |
|-----------|--------|--------|
| **SchedulerDriver** (Application Port) | `resume_source(source_id)` | Reanuda la programación de todos los Feeds PULL del source |
| **Monitor** (Application Service) | Actualiza estado del source en dashboard | Visualización de estado |
| **Logger** | Registra el evento | Auditoría |

---

## 4. SourceDisabled

### 4.1 Ficha del Evento

| Campo | Especificación |
|-------|---------------|
| **Nombre** | `SourceDisabled` |
| **Definición** | Indica que un NewsSource ha sido deshabilitado y toda ingesta desde ese source debe detenerse inmediatamente. |
| **Cuándo ocurre** | Cuando `NewsSource.disable(reason)` es llamado exitosamente desde un Application Service. |
| **Categoría** | Domain Event (intra-BC) |
| **Publisher** | `NewsSource` (Aggregate Root) |
| **Consumidores** | Application Service → SchedulerDriver, AlertService, Logger |

### 4.2 Firma Técnica

```python
@dataclass(frozen=True)
class SourceDisabled(DomainEvent):
    # Hereda de DomainEvent (Foundation):
    #   event_id: UUID          — auto-generado
    #   event_version: int = 1  — schema version
    #   occurred_at: datetime   — auto-generado
    #   event_name: str         — property, inferido del class name

    # Payload específico
    source_id: SourceId    # NewsSource que se deshabilitó
    reason: str           # Razón de la deshabilitación
    disabled_at: datetime  # Momento exacto de la deshabilitación
```

### 4.3 Semántica

```
¿Qué significa?
  "El NewsSource source_id ha sido deshabilitado por la razón
  especificada. Todos los Feeds de este source deben pausarse."

¿Qué NO significa?
  ❌ No significa que los Feeds se hayan desactivado individualmente
  ❌ No significa que los datos existentes se hayan eliminado
  ✅ Significa que el scheduler debe detener TODO fetch de Feeds
     de este source inmediatamente

¿Por qué existe?
  Es crítico detener la ingesta cuando una fuente se deshabilita.
  Sin este evento, los Feeds seguirían ejecutándose contra una
  fuente deshabilitada, desperdiciando recursos y potencialmente
  trayendo datos no deseados.
```

### 4.4 Secuencia de Publicación

```
ApplicationService.disable_source(source_id, reason):
  1. Carga NewsSource (NewsSourceRepository)
  2. Verifica can_be_disabled() → count_active_by_source > 0?
  3. Si no puede deshabilitarse → Result.failure(HAS_ACTIVE_FEEDS)
  4. NewsSource.disable(reason)
     → NewsSource registra SourceDisabled internamente
  5. NewsSourceRepository.save(news_source)
  6. events = news_source.pull_events()
  7. EventBus.publish(events)
     → SchedulerDriver.pause_source(source_id)
     → AlertService.notify(f"Source {source_id} disabled: {reason}")
     → Logger.info(...)
```

### 4.5 Consumidores

| Consumidor | Acción | Efecto |
|-----------|--------|--------|
| **SchedulerDriver** (Application Port) | `pause_source(source_id)` | Detiene TODA programación de Feeds del source |
| **AlertService** (Application Service) | `notify("source_disabled", ...)` | Alerta al operador sobre la deshabilitación |
| **Logger** | Registra el evento con razón | Auditoría completa |

---

## 5. Eventos Descartados (YAGNI)

### 5.1 Tabla de Eventos Descartados

| Evento | Propuesto en | Razón de descarte | Re-abrir si... |
|--------|-------------|-------------------|----------------|
| `SourceCreated` | Draft v1.0 | Ningún consumidor identificado dentro del BC. Crear un source no dispara procesos adicionales. | Aparece un consumidor que necesita reaccionar a la creación (ej: enviar notificación). |
| `CategoryCreated` | Draft v1.0 | Las categorías son datos de referencia. Su creación no dispara procesos. | Aparece un consumidor (ej: sincronización con sistema externo de taxonomía). |
| `FeedPaused` | Draft v1.0 | Se maneja como estado interno de Feed + log. No requiere notificación cross-AR. Es un hecho local al Feed. | Aparece un consumidor que necesita reaccionar al pause (ej: enviar alerta al operador). |
| `FeedFetchStarted` | Draft v1.0 | Es un evento de monitoreo/telemetría, no un evento de dominio. Pertenece a Application Layer o infraestructura. | Se necesita trazabilidad distribuida que requiera eventos explícitos. |
| `FeedFetchCompleted` | Draft v1.0 | Similar a FeedFetchStarted. Es monitoreo, no dominio. El scheduler puede deducir el estado consultando Feed.last_run. | Se necesita orquestación basada en eventos. |
| `FeedFetchFailed` | Draft v1.0 | El manejo de fallos es responsabilidad de Feed.record_failure() + scheduler. No requiere evento. | Se necesita notificación externa de fallos. |
| `NewItemsDetected` | Draft v1.0 | Reemplazado por RawArticleCollected, que es semánticamente más preciso y transporta información más rica. | — (ya cubierto) |

### 5.2 Principio de Decisión

> **"If a tree falls in a forest and no one is around to hear it, does it make a sound?"**
>
> Si un evento ocurre pero ningún consumidor lo escucha, no es un Domain Event.
> Es un log, una métrica, o ruido.

Cada Domain Event definido tiene al menos un consumidor identificado dentro del BC Ingestion.

---

## 6. Consideraciones de Event Sourcing

### 6.1 Inmutabilidad de Eventos

Todos los Domain Events son `@dataclass(frozen=True)` — inmutables por diseño. Esto es un requisito para cualquier consideración futura de Event Sourcing.

### 6.2 Idempotencia

| Evento | ¿Idempotente? | Mecanismo |
|--------|---------------|-----------|
| `RawArticleCollected` | Sí | `event_id` único. Si el mismo evento se procesa dos veces, el consumidor (Normalization Pipeline) debe detectar que el batch ya fue procesado. |
| `SourceEnabled` | Sí | Verificar `is_active` del NewsSource antes de ejecutar. Si ya está activo, no hacer nada. |
| `SourceDisabled` | Sí | Verificar `is_active` antes de ejecutar. Si ya está inactivo, no hacer nada. |

### 6.3 Volumen y Retención

| Evento | Volumen esperado | Retención recomendada |
|--------|-----------------|----------------------|
| `RawArticleCollected` | Alto (cada fetch exitoso) | 30 días (o hasta que el batch sea procesado) |
| `SourceEnabled` | Bajo (operaciones administrativas) | 90 días |
| `SourceDisabled` | Bajo (operaciones administrativas) | 90 días |

### 6.4 Schema Evolution

Los Domain Events pueden evolucionar mediante versionado. Actualmente todos están en **v1**. Si se necesita agregar un campo:

```python
# v1 original
@dataclass(frozen=True)
class RawArticleCollected(DomainEvent):
    feed_id: FeedId
    batch_id: UUID
    count: int
    collected_at: datetime

# v2 con campo nuevo (campo opcional retrocompatible)
@dataclass(frozen=True)
class RawArticleCollectedV2(DomainEvent):
    feed_id: FeedId
    batch_id: UUID
    count: int
    collected_at: datetime
    feed_label: str | None = None  # Nuevo campo opcional
```

Los consumidores deben manejar versiones v1 y v2 durante el período de transición.
