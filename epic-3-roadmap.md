# EPIC 3 — Ingestion Domain Core — Roadmap

> **Documento de planificación preliminar**
> Estado: **DRAFT** | Fecha: 2026-07-02
> Basado en: Baseline Architecture v1.0 (FROZEN) + Foundation v1.0 STABLE
> **Requiere aprobación del ARB antes de comenzar implementación.**

---

## 1. Objetivo del Epic

Implementar el **núcleo del dominio de Ingestion**: las entidades, value objects, puertos, eventos de dominio, y servicios de dominio que modelan la capacidad de obtener información desde fuentes externas, configurar feeds, ejecutar fetch/parseo/normalización, y publicar resultados para consumo de otros Bounded Contexts.

**NO incluye** en este Epic:
- Infraestructura (repositorios, adapters tecnológicos, event bus concreto)
- Application Services (casos de uso, schedulers, registries)
- Composition Root / wiring
- APIs o CLIs

Todo eso son Epics posteriores (Epic 4 — Ingestion Infrastructure, Epic 5 — Wiring).

---

## 2. Bounded Context Involucrado

**Nombre**: Ingestion BC
**Responsabilidad**: Obtener información desde fuentes externas, normalizarla y publicarla para consumo de otros BCs.
**NO conoce de**: IA, scoring, aprobación, generación de contenido, usuarios.

**Límites del contexto**:
```
┌─────────────────────────────────────────────────────────────────┐
│                      INGESTION BC                                │
│                                                                  │
│  domain/                                                         │
│  ├── entities/      Source, Feed, FeedGroup, RawItem, Category   │
│  ├── value_objects/ SyncPolicy, IngestionRun, NormalizedItem,    │
│  │                   SourceConfig, RetryPolicy, ProviderCapability│
│  ├── ports/         TechnologyAdapter, ProviderAdapter, Parser,   │
│  │                   NormalizationPipelinePort, EventPublisher,   │
│  │                   SourceRepo, FeedRepo, RawItemRepo, etc.     │
│  ├── services/      FeedOrchestrator, SourceValidator            │
│  ├── events/        Domain Events intra-BC                       │
│  └── exceptions/    Domain exceptions (subclases de DomainError) │
│                                                                  │
│  Comunica con: Research BC via Integration Events                 │
│  Depende de: Foundation v1.0 STABLE (todo excepto ports)         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Lenguaje Ubicuo Esperado

| Término | Definición | Tipo |
|---------|-----------|------|
| **Source** | Origen externo de información. Tiene tipo tecnológico y config global. | Aggregate Root |
| **Feed** | Stream específico dentro de un Source. Unidad configurable de ingesta. | Aggregate Root |
| **FeedGroup** | Agrupación operativa de Feeds dentro de un Source. Provee políticas heredables. | Aggregate Root |
| **RawItem** | Pieza individual de información cruda obtenida de un Feed. Inmutable después de creado. | Aggregate Root |
| **Category** | Clasificación temática. Jerarquía opcional. | Entity |
| **NormalizedItem** | Salida del pipeline de normalización. Sin identidad. | Value Object |
| **SyncPolicy** | Política de sincronización de un Feed: PULL, PUSH, STREAM, MANUAL. | Value Object |
| **IngestionRun** | Resultado de una ejecución de fetch para un Feed. | Value Object |
| **SourceConfig** | Configuración específica de una Source (URL base, auth, rate limit). | Value Object |
| **RetryPolicy** | Política de reintentos para fetches fallidos. | Value Object |
| **ProviderCapability** | Operación soportada por un ProviderAdapter (FETCH, SEARCH, TRENDING, etc.). | Value Object |
| **TechnologyAdapter** | Implementación de protocolo de transporte (RSS, HTTP, WebSocket). | Port (Protocol) |
| **ProviderAdapter** | Implementación de un proveedor específico (Reddit, Steam, HN). | Port (Protocol) |
| **Parser** | Transforma respuesta cruda en RawItems. | Port (Protocol) |
| **NormalizationPipeline** | Pipeline de steps para normalizar RawItems. | Port (Protocol) |
| **IngestionRun** | Resultado de la ejecución de fetch. Estado: SUCCESS, FAILED, PARTIAL. | Value Object |
| **FeedOrchestrator** | Coordina la ejecución de fetch de un Feed (fetch → parse → normalize → publish). | Domain Service |
| **SourceValidator** | Valida configuración de Source antes de registrar. | Domain Service |

---

## 4. Entidades Previstas

### Source (Aggregate Root)

```
Source
├── id: SourceId                      ← SourceId(EntityId)
├── name: str                         ← "Reddit", "Steam News"
├── provider_type: str                ← "reddit", "steam", "generic_rss"
├── technology_type: TechnologyType   ← Enum: RSS, HTTP, WEBSOCKET
├── is_active: bool
├── config: SourceConfig              ← SourceConfig (VO)
└── metadata: dict                    ← Datos adicionales libres
```

### Feed (Aggregate Root)

```
Feed
├── id: FeedId
├── source_id: SourceId               ← Referencia a Source (FK lógica)
├── group_id: FeedGroupId | None      ← 0..1 grupo
├── url: str                          ← URL del feed
├── label: str                        ← "r/programming", "top-hn"
├── is_active: bool
├── sync: SyncPolicy                  ← SyncPolicy (VO)
├── categories: list[CategoryId]      ← IDs de categorías
├── last_run: IngestionRun | None     ← Último resultado
├── retry_count: int = 0
└── next_retry_at: datetime | None
```

### FeedGroup (Aggregate Root)

```
FeedGroup
├── id: FeedGroupId
├── source_id: SourceId
├── name: str
├── is_active: bool
├── default_sync: SyncPolicy | None
└── default_category: CategoryId | None
```

### RawItem (Aggregate Root)

```
RawItem
├── id: RawItemId
├── feed_id: FeedId
├── batch_id: UUID                    ← Para recovery / trazabilidad
├── external_id: str                  ← ID en el source externo
├── hash: str                         ← SHA-256 del contenido (dedup)
├── title: str
├── description: str
├── content: str
├── url: str
├── author: str | None
├── published_at: datetime | None
├── fetched_at: datetime
└── metadata: dict
```

### Category (Entity — NO Aggregate Root)

```
Category
├── id: CategoryId
├── name: str
├── slug: str
├── parent_id: CategoryId | None
└── is_active: bool
```

---

## 5. Value Objects Previstos

| VO | Campos clave | Inmutable |
|----|-------------|-----------|
| **SyncPolicy** | `mode: SyncMode` (PULL/PUSH/STREAM/MANUAL), `pull_interval: int \| None`, `pull_cron: str \| None`, `push_secret_ref: str \| None`, `stream_heartbeat: int \| None`, `retry: RetryPolicy`, `timeout: int`, `max_items: int` | ✅ |
| **IngestionRun** | `status: IngestionStatus` (SUCCESS/FAILED/PARTIAL), `items_count: int`, `duration_ms: int`, `error_message: str \| None`, `started_at: datetime`, `finished_at: datetime` | ✅ |
| **NormalizedItem** | `raw_item_id: RawItemId`, `title: str`, `content: str`, `url: str`, `author: str \| None`, `language: str \| None`, `quality_score: float \| None`, `categories: list[CategoryId]`, `metadata: dict` | ✅ |
| **SourceConfig** | `base_url: str`, `auth_method: str \| None`, `api_key_ref: str \| None`, `rate_limit: int \| None`, `timeout_seconds: int \| None` | ✅ |
| **RetryPolicy** | `max_retries: int`, `backoff_multiplier: float`, `max_backoff_seconds: int` | ✅ |
| **ProviderCapability** | Enum: FETCH, SEARCH, TRENDING, STREAM, SUBMIT, RELEASES, VIDEOS | ✅ |

### Enums previstos

| Enum | Valores |
|------|---------|
| `SyncMode` | PULL, PUSH, STREAM, MANUAL |
| `IngestionStatus` | SUCCESS, FAILED, PARTIAL |
| `TechnologyType` | RSS, HTTP, WEBSOCKET (extensible por cada BC) |

---

## 6. Aggregates Previstos

| Aggregate Root | ID Type | Depende de | Eventos que emite |
|---------------|---------|-----------|-------------------|
| Source | SourceId | SourceConfig | (configuración, no emite eventos de negocio) |
| Feed | FeedId | SourceId, SyncPolicy, FeedGroupId (opcional) | FeedFetchStarted, FeedFetchCompleted, FeedFetchFailed, FeedPaused |
| FeedGroup | FeedGroupId | SourceId, SyncPolicy | (administrativo, no emite eventos de negocio) |
| RawItem | RawItemId | FeedId | (inmutable después de creado — no emite eventos) |

### Reglas de consistencia entre Aggregates

| Regla | Tipo | ¿Cómo se protege? |
|-------|------|-------------------|
| Un Feed pertenece a un Source existente | Consistencia eventual | Se verifica en Application Service antes de crear |
| Un FeedGroup pertenece a un Source existente | Consistencia eventual | Se verifica en Application Service |
| Un Feed opcionalmente pertenece a un FeedGroup | Consistencia eventual | Validación en dominio o aplicación |
| RawItem siempre pertenece a un Feed | Consistencia eventual | Se pasa feed_id en creación |
| Un Feed no puede quedar sin categorías si su Source lo requiere | Invariante de dominio | `SourceValidator` |

---

## 7. Domain Events Previstos

| Evento | Publicado por | Payload | Consumido por |
|--------|--------------|---------|---------------|
| FeedFetchStarted | FeedOrchestrator | feed_id, started_at | Metrics, Logger |
| FeedFetchCompleted | FeedOrchestrator | feed_id, items_count, duration_ms | Scheduler (next_run), Metrics |
| FeedFetchFailed | FeedOrchestrator | feed_id, error_message, attempt | Scheduler (retry), AlertService |
| FeedPaused | Scheduler | feed_id, reason | Metrics, Logger |
| NewItemsDetected | FeedOrchestrator | feed_id, batch_id, count | Pipeline (normalización) |

---

## 8. Ports Previstos (Domain Protocols)

### Repository Ports (persistencia)

| Port | Métodos | Aggregate |
|------|---------|-----------|
| `SourceRepository` | `save(source)`, `find_by_id(id)`, `find_all()`, `find_active()` | Source |
| `FeedRepository` | `save(feed)`, `find_by_id(id)`, `find_by_source(source_id)`, `find_due(now)`, `find_by_group(group_id)` | Feed |
| `FeedGroupRepository` | `save(group)`, `find_by_id(id)`, `find_by_source(source_id)` | FeedGroup |
| `RawItemRepository` | `save(item)`, `find_by_id(id)`, `find_by_feed(feed_id)`, `find_by_hash(hash)`, `find_by_batch(batch_id)` | RawItem |
| `CategoryRepository` | `save(category)`, `find_by_id(id)`, `find_all()`, `find_by_parent(parent_id)` | Category |

### Infrastructure Ports

| Port | Métodos | Responsabilidad |
|------|---------|----------------|
| `TechnologyAdapter` | `fetch(options) → RawResponse` | Solo transporte (URL → bytes) |
| `ProviderAdapter` | `fetch(feed, context) → list[RawItem]`, `execute(operation, feed, params, context) → list[RawItem]` | Coordina TechnologyAdapter + Parser |
| `Parser` | `parse(response, feed) → list[RawItem]` | Transforma respuesta cruda en RawItems |
| `NormalizationPipelinePort` | `execute(items, feed) → list[NormalizedItem]` | Pipeline completo de normalización |
| `EventPublisher` | `publish(event) → None` | Publica Integration Events cross-BC |
| `ISchedulerDriver` | `get_due_feeds() → list[FeedId]`, `schedule_retry(feed_id, delay)` | Timing para PULL feeds |

---

## 9. Domain Services Previstos

| Service | Responsabilidad | Métodos públicos |
|---------|----------------|-----------------|
| `FeedOrchestrator` | Coordina fetch → parse → normalize → publish para un Feed | `execute_feed(feed_id, context) → Result[IngestionRun]` |
| `SourceValidator` | Valida que una Source pueda ser registrada | `validate(config) → Result[None]` |

---

## 10. Application Services Previstos (no se implementan en este Epic)

> Listados aquí para visión completa. Se implementan en Epic 4.

| Service | Comando/Query | Descripción |
|---------|--------------|-------------|
| `RegisterSourceUseCase` | `RegisterSourceCommand` | Registra una nueva Source |
| `ConfigureFeedUseCase` | `ConfigureFeedCommand` | Configura o actualiza un Feed |
| `TriggerIngestionUseCase` | `TriggerIngestionCommand` | Dispara fetch manual de un Feed |
| `HandleWebhookUseCase` | `HandleWebhookCommand` | Procesa webhook (PUSH) |
| `RetryIngestionUseCase` | `RetryIngestionCommand` | Reintenta fetch fallido |
| `GetSourceStatusQuery` | `GetSourceStatusQuery` | Obtiene estado de una Source |
| `ListFeedsQuery` | `ListFeedsQuery` | Lista Feeds de una Source |
| `GetRawItemsQuery` | `GetRawItemsQuery` | Obtiene RawItems de un Feed |

---

## 11. Orden Recomendado de Implementación

```
Sprint 3.1 ──→ Sprint 3.2 ──→ Sprint 3.3 ──→ Sprint 3.4 ──→ Sprint 3.5
    │              │              │              │              │
    ▼              ▼              ▼              ▼              ▼
 Ingestion IDs   Value          Aggregates    Domain        Domain
 SourceId        Objects        Source,      Events +      Services
 FeedId          SyncPolicy     Feed,        Ports         FeedOrchestrator
 FeedGroupId     IngestionRun   FeedGroup,                  SourceValidator
 RawItemId       SourceConfig   RawItem
 CategoryId      RetryPolicy    Category
                 ProviderCap.
```

### Detalle por Sprint

#### Sprint 3.1 — Ingestion Identity System

**Depende de**: Foundation v1.0 (EntityId)
**Dependencias futuras**: Todos los sprints siguientes

| Componente | Archivo |
|-----------|---------|
| `SourceId(EntityId)` | `src/ingestion/domain/entities/ids.py` |
| `FeedId(EntityId)` | mismo archivo |
| `FeedGroupId(EntityId)` | mismo archivo |
| `RawItemId(EntityId)` | mismo archivo |
| `CategoryId(EntityId)` | mismo archivo |
| `IngestionErrorCode(str, Enum)` | `src/ingestion/domain/exceptions/errors.py` |

**Output**: 5 tipos de ID específicos del BC + ErrorCode propio.

#### Sprint 3.2 — Ingestion Value Objects

**Depende de**: Sprint 3.1 (IDs)
**Dependencias futuras**: Sprint 3.3 (Aggregates)

| Componente | Archivo |
|-----------|---------|
| `SyncPolicy` (frozen dataclass) | `src/ingestion/domain/value_objects/sync_policy.py` |
| `IngestionRun` (frozen dataclass) | `src/ingestion/domain/value_objects/ingestion_run.py` |
| `SourceConfig` (frozen dataclass) | `src/ingestion/domain/value_objects/source_config.py` |
| `RetryPolicy` (frozen dataclass) | `src/ingestion/domain/value_objects/retry_policy.py` |
| `ProviderCapability` (Enum) | `src/ingestion/domain/value_objects/provider_capability.py` |
| `SyncMode` (Enum) | `src/ingestion/domain/value_objects/sync_mode.py` |
| `TechnologyType` (Enum) | `src/ingestion/domain/value_objects/technology_type.py` |
| `NormalizedItem` (frozen dataclass) | `src/ingestion/domain/value_objects/normalized_item.py` |

**Output**: 8 VOs que modelan los conceptos de configuración y operación del BC.

#### Sprint 3.3 — Ingestion Aggregates

**Depende de**: Sprint 3.1 (IDs), Sprint 3.2 (VOs)
**Dependencias futuras**: Sprint 3.4 (Events + Ports)

| Componente | Archivo |
|-----------|---------|
| `Source(AggregateRoot)` | `src/ingestion/domain/entities/source.py` |
| `Feed(AggregateRoot)` | `src/ingestion/domain/entities/feed.py` |
| `FeedGroup(AggregateRoot)` | `src/ingestion/domain/entities/feed_group.py` |
| `RawItem(AggregateRoot)` | `src/ingestion/domain/entities/raw_item.py` |
| `Category(Entity)` | `src/ingestion/domain/entities/category.py` |
| Domain exceptions | `src/ingestion/domain/exceptions/` |
| `__init__.py` exports | `src/ingestion/domain/__init__.py` |

**Output**: 5 entidades/ARs que modelan el core del dominio de Ingestion.

#### Sprint 3.4 — Domain Events + Domain Ports

**Depende de**: Sprint 3.3 (Aggregates)
**Dependencias futuras**: Sprint 3.5 (Services)

| Componente | Archivo |
|-----------|---------|
| `FeedFetchStarted(DomainEvent)` | `src/ingestion/domain/events/feed_events.py` |
| `FeedFetchCompleted(DomainEvent)` | mismo archivo |
| `FeedFetchFailed(DomainEvent)` | mismo archivo |
| `FeedPaused(DomainEvent)` | mismo archivo |
| `NewItemsDetected(DomainEvent)` | mismo archivo |
| `SourceRepository(Protocol)` | `src/ingestion/domain/ports/repositories.py` |
| `FeedRepository(Protocol)` | mismo archivo |
| `FeedGroupRepository(Protocol)` | mismo archivo |
| `RawItemRepository(Protocol)` | mismo archivo |
| `CategoryRepository(Protocol)` | mismo archivo |
| `TechnologyAdapter(Protocol)` | `src/ingestion/domain/ports/technology.py` |
| `ProviderAdapter(Protocol)` | `src/ingestion/domain/ports/provider.py` |
| `Parser(Protocol)` | `src/ingestion/domain/ports/parser.py` |
| `NormalizationPipelinePort(Protocol)` | `src/ingestion/domain/ports/normalization.py` |
| `EventPublisher(Protocol)` | `src/ingestion/domain/ports/event_publisher.py` |
| `ISchedulerDriver(Protocol)` | `src/ingestion/domain/ports/scheduler.py` |

**Output**: 5 Domain Events + 10 Ports (5 repos + 5 infra).

#### Sprint 3.5 — Domain Services

**Depende de**: Sprint 3.4 (Events + Ports)
**Dependencias futuras**: Epic 4 (Application Layer + Infrastructure)

| Componente | Archivo |
|-----------|---------|
| `FeedOrchestrator` | `src/ingestion/domain/services/feed_orchestrator.py` |
| `SourceValidator` | `src/ingestion/domain/services/source_validator.py` |

**Output**: 2 Domain Services que implementan la lógica de negocio pura del BC.

---

## 12. Dependencias entre Sprints

```
Foundation v1.0 STABLE
    │
    ▼
Sprint 3.1 (IDs)
    │
    ▼
Sprint 3.2 (VOs)
    │
    ▼
Sprint 3.3 (Aggregates)
    │
    ├────────────────────┐
    ▼                    ▼
Sprint 3.4 (Events)    Sprint 3.4 (Ports)
    │                    │
    └────────┬───────────┘
             ▼
      Sprint 3.5 (Services)
             │
             ▼
      EPIC 4 — Ingestion
      Infrastructure + Application
```

### Reglas de dependencia

1. **Ningún sprint salta dependencias**: No se puede implementar Sprint 3.3 sin tener Sprint 3.1 y 3.2 completos.
2. **Sprint 3.4 puede dividirse en paralelo**: Events y Ports no dependen el uno del otro — pueden implementarse simultáneamente.
3. **Sprint 3.5 requiere ambos**: FeedOrchestrator y SourceValidator necesitan tanto Events como Ports.
4. **Foundation es prerequisito de TODO**: Sin Foundation, el dominio de Ingestion no tiene EntityId, ValueObject, Entity, AggregateRoot, Result, Error, DomainEvent ni excepciones base.

### Compatibilidad con Foundation

Todo el dominio de Ingestion se construye sobre Foundation v1.0:

| Necesidad Foundation | Componente Foundation |
|---------------------|---------------------|
| IDs tipados | `EntityId` (Sprint 2.1) |
| Building Blocks | `ValueObject`, `Entity`, `AggregateRoot` (Sprint 2.2) |
| Resultados | `Result[T]`, `Error` (Sprint 2.3) |
| Eventos | `DomainEvent` (Sprint 2.4) |
| Excepciones | `DomainError`, `ApplicationError` (Sprint 2.5) |
| Clock (tests) | `ClockPort`, `FrozenClock` (Sprint 2.6) |
| UUIDs (tests) | `UUIDProvider`, `SequentialUUIDProvider` (Sprint 2.6) |

---

## 13. Prerequisitos para comenzar Epic 3

- [x] Foundation v1.0 STABLE declarado y documentado
- [x] Foundation Stability Policy ratificada
- [x] Foundation Release Notes publicadas
- [x] ADRs 016-022 aprobados
- [x] Baseline Architecture v1.0 FROZEN
- [x] Repository Structure definido y aprobado

### Checklist de inicio

- [ ] ARB aprueba este roadmap
- [ ] Sprint 3.1 specification escrita y aprobada
- [ ] Estructura `src/ingestion/domain/` creada
- [ ] Tests configurados para el BC Ingestion
- [ ] Se confirma que Foundation NO necesita cambios

---

## 14. Riesgos del Epic 3

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Domain Events del diseño original no cubren todos los casos | Media | Medio | Los eventos son aditivos — se agregan sin breaking changes |
| NormalizedItem como VO puede necesitar evolución temprana | Media | Bajo | Es un VO frozen — se reemplaza, no se muta |
| SyncPolicy muy complejo para un solo sprint | Media | Medio | Dividir: primero soporte PULL (el más común), luego PUSH/STREAM/MANUAL |
| ProviderCapability como Enum puede necesitar extensión | Baja | Bajo | Los Enums de Python 3.12 soportan `str, Enum` — agregar valores es aditivo |

---

*Documento preparado por el Architecture Review Board durante el cierre de Epic 2.*
*Requiere aprobación del ARB antes del inicio de Epic 3.*
