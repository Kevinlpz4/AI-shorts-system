---
title: "Baseline Architecture v1.0"
status: "APPROVED"
state: "FROZEN"
epic: "Epic 1 — News Ingestion Platform"
date: "2026-07-02"
authors:
  - "Architecture Review Board"
  - "Principal Software Architect"
version: "1.0"
breaking_changes: "Ninguno"
adrs:
  - "ADR-001: Separación TechnologyAdapter / ProviderAdapter"
  - "ADR-002: Feed y FeedGroup como Aggregate Roots Independientes"
  - "ADR-003: SyncMode Simplificado (PULL/PUSH/STREAM/MANUAL)"
  - "ADR-004: NormalizedItem como Value Object"
  - "ADR-005: ProviderCapability como Value Object del Dominio"
  - "ADR-006: RawItem como Aggregate Root (por volumen)"
  - "ADR-007: Fetcher y Parser como Responsabilidades Separadas"
  - "ADR-008: Scheduler como Application Service con Driver Intercambiable"
  - "ADR-009: Normalization como Pipeline Interno"
  - "ADR-010: Integration Events via Event Bus"
  - "ADR-011: Operation Pattern en ProviderAdapter"
  - "ADR-012: Diseño de Registries"
  - "ADR-013: PipelineContext over RawItem Mutation"
  - "ADR-014: Domain Events vs Integration Events"
  - "ADR-015: Event Versioning en Integration Events"
related_rfcs: []
validated_by: "Architecture Review Board — 2026-07-02"
next_review: "Al finalizar Epic 2 o si un ADR propuesto rompe esta baseline"
---

# 🏛️ Baseline Architecture v1.0

> **FROZEN** — A partir de esta versión, todo cambio arquitectónico debe responder:
> *"¿Rompe la Baseline v1.0?"* Si la respuesta es sí, requiere justificación, revisión
> del ARB, y un nuevo ADR que modifique explícitamente esta baseline.

---

## 1. Propósito y Alcance

Esta baseline define la arquitectura del **Bounded Context de Ingestion** (Epic 1)
del sistema AI Shorts System. Cubre:

- Adquisición de información desde fuentes externas
- Configuración de fuentes y feeds
- Fetching, parseo y normalización de items
- Publicación de items normalizados para consumo de otros BCs

**NO cubre**:

- Scoring, aprobación o ciclo de vida editorial (Research BC)
- Generación de guiones o contenido (Script/Content BC)
- Infraestructura de deploy, CI/CD, o monitoreo operativo

---

## 2. Architecture Principles

Los siguientes principios gobiernan TODAS las decisiones técnicas del sistema.
Cualquier propuesta de cambio debe respetarlos o justificar explícitamente su
excepción en un ADR.

| # | Principio | Enunciado |
|---|-----------|-----------|
| P1 | **Domain Isolation** | El dominio NO depende de nada externo. Zero imports de infraestructura, frameworks, o librerías externas en `domain/`. Solo Python stdlib + tipos del dominio. |
| P2 | **Port-Driven Boundaries** | Todo cruce de capa se hace a través de un puerto (Protocol). Las dependencias apuntan hacia adentro (DIP). El dominio define puertos, la infraestructura los implementa. |
| P3 | **Config-Driven Sources** | Si la tecnología ya está soportada (RSS, HTTP, etc.), agregar una fuente debe ser solo registrar datos — en DB o configuración — sin escribir código nuevo. Los adapters se resuelven por `ProviderType` y `TechnologyType`. |
| P4 | **Eventual Consistency Between Aggregates** | Cada Aggregate Root es consistente dentro de sí mismo. Entre aggregates diferentes (Source ↔ Feed ↔ RawItem) la consistencia es eventual. Las invariantes cross-aggregate se protegen con domain services + constraints a nivel DB. |
| P5 | **Pipeline over Monolith** | El procesamiento de items (normalización) se modela como un pipeline de steps independientes. Cada step es una unidad testeable, reemplazable, y potencialmente async. No existe un "NormalizerService" monolítico. |
| P6 | **Explicit Integration Boundaries** | Cada Bounded Context se comunica exclusivamente mediante Integration Events publicados en un Event Bus. No hay llamadas directas entre BCs. No hay acceso a repositorios de otro BC. |
| P7 | **Technology Polymorphism** | TechnologyAdapter y ProviderAdapter se resuelven por registro (Registry pattern) usando un key (TechnologyType / ProviderType). No hay condicionales (`if type == RSS`) ni switch statements en el core. |
| P8 | **Fail Isolated, Report Aggregated** | Si una fuente falla, NO afecta a las demás. Los errores se recolectan y reportan en batch. Cada Feed tiene su propio estado de salud y su propia política de retry. |
| P9 | **Coordinator-Decider-Executor** | Application Services coordinan. Domain Services deciden. Infrastructure ejecuta. Ninguna capa hace el trabajo de otra. |

---

## 3. Bounded Context: Ingestion

### 3.1 Responsabilidad

> Obtener información desde fuentes externas, normalizarla y publicarla para
> consumo de otros Bounded Contexts.

**NO** conoce de:
- IA, scoring, o clasificación semántica
- Ciclo de vida editorial (aprobación, rechazo)
- Generación de contenido
- Usuarios, roles, o autenticación

### 3.2 Lenguaje Ubicuo

| Término | Definición |
|---------|-----------|
| **Source** | Un origen externo de información. Tiene tipo tecnológico y config global. Ej: Reddit, Google News. |
| **Feed** | Un stream específico dentro de un Source. Es la unidad configurable de ingesta. Ej: `r/programming`, `top` de HN. |
| **FeedGroup** | Agrupación operativa de Feeds dentro de un Source. Provee políticas heredables (sync, categoría). |
| **RawItem** | Una pieza individual de información cruda obtenida de un Feed. Inmutable después de creado. |
| **NormalizedItem** | Value Object — salida del pipeline de normalización. Inmutable. Sin identidad. |
| **TechnologyAdapter** | Implementación de un protocolo de transporte (RSS, HTTP, WebSocket). Solo sabe de comunicación. |
| **ProviderAdapter** | Implementación de un proveedor específico (Reddit, Steam, HN). Coordina TechnologyAdapter + Parser. |
| **SyncPolicy** | Política de sincronización de un Feed. Modos: PULL, PUSH, STREAM, MANUAL. |
| **IngestionRun** | Resultado de una ejecución de fetch para un Feed. Estado: SUCCESS, FAILED, PARTIAL. |
| **ProviderCapability** | Operación soportada por un ProviderAdapter. Ej: FETCH, SEARCH, TRENDING. |

### 3.3 Mapa de Contexto

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Shorts System                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐    ┌─────────────────────┐             │
│  │   INGESTION BC      │    │   RESEARCH BC        │             │
│  │  (E P I C   1)      │    │                      │             │
│  │                     │    │  Topic Discovery      │             │
│  │  Source/Feed Config │    │  Scoring              │             │
│  │  Fetch Orchestration│    │  Approval             │             │
│  │  Parse + Normalize  │───▶│  Semantic Dedup       │             │
│  │  Domain Events      │    │                      │             │
│  │                     │    │  ResearchTopic AR     │             │
│  │  Source (AR)        │    └──────────────────────┘             │
│  │  Feed (AR)          │                                         │
│  │  FeedGroup (AR)     │    ┌─────────────────────┐             │
│  │  RawItem (AR)       │    │   SCRIPT BC          │             │
│  │  Category (Entity)  │    │                      │             │
│  └─────────────────────┘    │  Script Generation    │             │
│                             │  Content Production   │             │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │           INTEGRATION EVENT BUS                          │     │
│  │  NewRawItemsAvailable | TopicDiscovered | TopicApproved │     │
│  └─────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Modelo de Dominio

### 4.1 Aggregates

```
┌───────────────────────────────────────────────────────────────────┐
│ Source (AR)                                                       │
├───────────────────────────────────────────────────────────────────┤
│ SourceId (UUID)                     # Identidad                    │
│ name: str                           # "Reddit"                    │
│ provider_type: str                  # "reddit"                    │
│ technology_type: TechnologyType     # HTTP                        │
│ is_active: bool                                                    │
│ config: SourceConfig                # JSONB (ver sección 4.3)     │
└───────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│ Feed (AR)                                                         │
├───────────────────────────────────────────────────────────────────┤
│ FeedId (UUID)                                                     │
│ source_id: SourceId                     # Referencia              │
│ group_id: Optional[FeedGroupId]         # 0..1 grupo              │
│ url: str                                                        │
│ label: str                             # "r/programming"         │
│ is_active: bool                                                   │
│ sync: SyncPolicy                       # PULL/PUSH/STREAM/MANUAL │
│ categories: list[CategoryId]           # merge con grupo          │
│ last_run: Optional[IngestionRun]       # resultado último fetch   │
│ retry_count: int = 0                                             │
│ next_retry_at: Optional[datetime]                                 │
└───────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│ FeedGroup (AR)                                                    │
├───────────────────────────────────────────────────────────────────┤
│ FeedGroupId (UUID)                                                │
│ source_id: SourceId                                                │
│ name: str                           # "tech"                     │
│ is_active: bool                                                   │
│ default_sync: SyncPolicy             # heredado por feeds         │
│ default_category: Optional[CategoryId]                            │
└───────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│ RawItem (AR)                                                      │
├───────────────────────────────────────────────────────────────────┤
│ RawItemId (UUID)                                                  │
│ feed_id: FeedId                                                   │
│ batch_id: UUID                       # para recovery              │
│ external_id: str                     # ID en el source externo    │
│ hash: str                            # SHA-256 del contenido      │
│ title: str                                                        │
│ description: str                                                  │
│ content: str                                                      │
│ url: str                                                          │
│ author: Optional[str]                                             │
│ published_at: Optional[datetime]                                  │
│ fetched_at: datetime                                              │
│ metadata: dict                          # datos específicos       │
└───────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│ Category (Entity)                                                │
├───────────────────────────────────────────────────────────────────┤
│ CategoryId (UUID)                                                 │
│ name: str                           # "Technology"               │
│ slug: str                           # "technology"               │
│ parent_id: Optional[CategoryId]      # jerarquía opcional         │
│ is_active: bool                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### 4.2 Value Objects

| VO | Atributos clave | Inmutable |
|----|----------------|-----------|
| SyncPolicy | mode (PULL/PUSH/STREAM/MANUAL), pull_interval, pull_cron, push_secret_ref, stream_heartbeat, retry, timeout, max_items | ✅ |
| IngestionRun | status (SUCCESS/FAILED/PARTIAL), items_count, duration_ms, error_message, started_at, finished_at | ✅ |
| NormalizedItem | raw_item_id, title, content, url, author, language, quality_score, categories, metadata | ✅ |
| SourceConfig | base_url, auth_method, api_key_ref, rate_limit, timeout_seconds (JSONB) | ✅ |
| RetryPolicy | max_retries, backoff_multiplier, max_backoff_seconds | ✅ |
| ProviderCapability | Enum: FETCH, SEARCH, TRENDING, STREAM, SUBMIT, RELEASES, VIDEOS | ✅ |

### 4.3 SourceConfig (JSONB)

```json
{
  "// technology": "Campos de transporte",
  "timeout_seconds": 30,
  "max_redirects": 5,
  "user_agent": "AI-Shorts/1.0",

  "// provider": "Campos específicos del provider",
  "base_url": "https://www.reddit.com",
  "auth_method": "oauth2",
  "api_key_ref": "REDDIT_CLIENT_ID",

  "// source": "Campos de la instancia",
  "default_category": null,
  "notes": "Reddit feeds for tech content"
}
```

### 4.4 Domain Events (bus interno del BC)

| Evento | Publicado por | Consumido por |
|--------|--------------|---------------|
| FeedFetchStarted | FeedOrchestrator | Metrics, Logger |
| FeedFetchCompleted | FeedOrchestrator | Scheduler (next_run), Metrics |
| FeedFetchFailed | FeedOrchestrator | Scheduler (retry), AlertService |
| FeedPaused | Scheduler | Metrics, Logger |
| NewItemsDetected | FeedOrchestrator | Pipeline (normalización) |

### 4.5 Integration Events (bus externo, cruce de BCs)

| Evento | Versión | Payload | Consumido por |
|--------|---------|---------|---------------|
| NewRawItemsAvailable | 1 | batch_id, feed_id, item_count, fetched_at | Research BC |

---

## 5. Arquitectura Hexagonal

### 5.1 Capas y Dependencias

```
┌────────────────────────────────────────────────────────────────────┐
│                       COMPOSITION ROOT                             │
│              Registra adapters, inicia scheduler                   │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                              │
│                                                                    │
│  Commands: RegisterSource, ConfigureFeed, TriggerIngestion,        │
│           HandleWebhook, RetryIngestion                            │
│  Queries: GetSourceStatus, ListFeeds, GetRawItems                 │
│  Services: SchedulerOrchestrator, ProviderRegistry,                │
│            TechnologyRegistry                                      │
│                                                                    │
│  ⚠️ Depende de: domain/ports, domain/entities, domain/services    │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                       DOMAIN LAYER                                 │
│                                                                    │
│  entities/     — Source, Feed, FeedGroup, RawItem, Category       │
│  value_objects/ — SyncPolicy, IngestionRun, NormalizedItem, ...   │
│  ports/        — Protocols: TechnologyAdapter, ProviderAdapter,    │
│                  Parser, NormalizationPipeline, EventPublisher,     │
│                  SourceRepository, FeedRepository, RawItemRepo,    │
│                  CategoryRepository, SchedulerDriver               │
│  services/     — FeedOrchestrator, SourceValidator                │
│  events/       — Domain Events (in-process)                       │
│  exceptions/   — Domain exceptions                                │
│                                                                    │
│  ⚠️ NO importa nada de application/ o infrastructure/             │
│  ⚠️ NO importa librerías externas (solo stdlib)                   │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                             │
│                                                                    │
│  persistence/     — PostgresSourceRepo, PostgresFeedRepo, ...     │
│  technology_adapters/ — RssFetcher, HttpFetcher, WebSocketFetcher│
│  provider_adapters/  — GenericRssProvider, RedditProvider, ...    │
│  parsers/           — GenericRssParser, RedditJsonParser, ...     │
│  normalization/     — Pipeline + steps (Sanitizer, LanguageDetect,│
│                       QualityFilter)                              │
│  event_bus/         — InProcessEventBus (domain + integration)    │
│  scheduler/          — InProcessSchedulerDriver                   │
│  wrappers/           — CircuitBreaker, Observable metrics          │
│                                                                    │
│  ⚠️ IMPORTA domain/ports y domain/entities                        │
│  ⚠️ NO importa de otros BCs                                       │
└────────────────────────────────────────────────────────────────────┘
```

### 5.2 Puertos Clave

```python
# TechnologyAdapter: solo transporte. URL → bytes.
class TechnologyAdapter(Protocol):
    technology_type: TechnologyType
    async def fetch(self, options: FetchOptions) -> RawResponse: ...

# ProviderAdapter: coordina TechnologyAdapter + Parser.
# fetch() es universal. execute() para capabilities adicionales.
class ProviderAdapter(Protocol):
    provider_name: str
    technology_type: TechnologyType
    capabilities: set[ProviderCapability]
    async def fetch(self, feed, context) -> list[RawItem]: ...
    async def execute(self, operation, feed, params, context) -> list[RawItem]: ...

# Parser: RawResponse → RawItems. Sin lógica de transporte.
class Parser(Protocol):
    provider_name: str
    async def parse(self, response: RawResponse, feed: Feed) -> list[RawItem]: ...

# NormalizationPipeline: RawItems → NormalizedItems via PipelineContext.
class NormalizationPipelinePort(Protocol):
    async def execute(self, items: list[RawItem], feed: Feed) -> list[NormalizedItem]: ...

# EventPublisher: Integration Events a otros BCs.
class EventPublisher(Protocol):
    async def publish(self, event: IntegrationEvent) -> None: ...

# SchedulerDriver: timing real para PULL feeds.
class ISchedulerDriver(Protocol):
    async def get_due_feeds(self) -> list[FeedId]: ...
    async def schedule_retry(self, feed_id, delay) -> None: ...
```

### 5.3 Operation Pattern

```python
# ProviderAdapter usa Operation Pattern para capacidades adicionales.
# fetch() es método de primera clase (todos lo implementan).
# execute() despacha por ProviderCapability via operation registry.

# Nuevas capacidades:
#   1. Agregar valor a ProviderCapability enum
#   2. Agregar handler privado en el provider
#   3. Registrar en _ops dict
#   4. Agregar a capabilities set
#   → Protocol NO cambia
```

### 5.4 Normalization con PipelineContext

```
RawItem (INMUTABLE)
  │
  ▼
PipelineContext(raw_item)
  │
  ├──► SanitizerStep.process(context)     → contexto.sanitized_*
  ├──► LanguageDetectorStep.process()     → contexto.language
  ├──► QualityFilterStep.process()        → contexto.skipped = True/False
  └──► ... (futuros)
  │
  ▼
  context.to_normalized_item()  → NormalizedItem (VO inmutable)
```

---

## 6. Índice de ADRs

| ADR | Título | Estado |
|-----|--------|--------|
| 001 | Separación TechnologyAdapter / ProviderAdapter | APPROVED |
| 002 | Feed y FeedGroup como Aggregate Roots Independientes | APPROVED |
| 003 | SyncMode Simplificado (PULL/PUSH/STREAM/MANUAL) | APPROVED |
| 004 | NormalizedItem como Value Object | APPROVED |
| 005 | ProviderCapability como Value Object del Dominio | APPROVED |
| 006 | RawItem como Aggregate Root (por volumen) | APPROVED |
| 007 | Fetcher y Parser como Responsabilidades Separadas | APPROVED |
| 008 | Scheduler como Application Service con Driver Intercambiable | APPROVED |
| 009 | Normalization como Pipeline Interno | APPROVED |
| 010 | Integration Events via Event Bus | APPROVED |
| 011 | Operation Pattern en ProviderAdapter | APPROVED |
| 012 | Diseño de Registries | APPROVED |
| 013 | PipelineContext over RawItem Mutation | APPROVED |
| 014 | Domain Events vs Integration Events | APPROVED |
| 015 | Event Versioning en Integration Events | APPROVED |

### 6.1 Cómo se documenta un ADR

Todos los ADRs se almacenan en `docs/architecture/adr/` con el formato:

```markdown
# ADR-{NUM}: {Título}

| Campo | Valor |
|-------|-------|
| **Estado** | APPROVED | PROPOSED | SUPERSEDED BY ADR-NNN |
| **Contexto** | ... |
| **Decisión** | ... |
| **Consecuencias** | ... |
| **Alternativas** | ... |
```

Cada ADR es un archivo individual. Este documento mantiene el índice y la
referencia rápida. Para el detalle completo, ir al archivo.

---

## 7. Política de Breaking Changes

### 7.1 ¿Qué constituye un Breaking Change?

Un cambio rompe la Baseline v1.0 si:

1. **Modifica la responsabilidad del BC** — Ingestion empieza a conocer de IA, scoring, o aprobación
2. **Elimina o modifica un puerto (Protocol)** sin pasar por ADR — cambiar la firma de `fetch()`, eliminar `ProviderAdapter`, etc.
3. **Agrega una dependencia de dominio a infraestructura** — violación de DIP
4. **Introduce acoplamiento directo entre BCs** — un caso de uso de Ingestion importa algo de Research
5. **Cambia el modelo de datos de un Integration Event** de forma incompatible sin incrementar versión
6. **Elimina un principio arquitectónico** sin reemplazo documentado

### 7.2 Proceso de cambio

```
1. Propuesta de cambio → documento breve (RFC o ADR proposal)
2. Evaluación contra Baseline v1.0:
     ¿Rompe la baseline?
       │
       No → Implementar sin tocar baseline
       |
       Sí → 3. Revisión del ARB
             4. Si se aprueba:
                  a. Nuevo ADR que modifica explícitamente la baseline
                  b. Se actualiza este documento → v1.1
                  c. Se documenta qué cambió y por qué
             5. Si se rechaza:
                  → No se implementa el cambio
```

### 7.3 Excepciones

Cualquier desarrollador puede solicitar una excepción enviando un ADR proposal
al ARB. La excepción debe justificar:

- Por qué el cambio es necesario
- Por qué no se puede lograr respetando la baseline
- Cuál es el impacto de NO hacer el cambio
- Cuál es el costo de hacerlo (deuda técnica, mantenibilidad)

---

## 8. Registro de Cambios de la Baseline

| Versión | Fecha | Cambio | ADR |
|---------|-------|--------|-----|
| 1.0 | 2026-07-02 | Versión inicial. Baseline FROZEN del Epic 1. | — |

---

## 9. Firmas

| Rol | Nombre | Fecha |
|-----|--------|-------|
| Principal Software Architect | — | 2026-07-02 |
| Architecture Review Board | — | 2026-07-02 |

---

> **🔒 FROZEN** — Esta baseline no puede modificarse sin pasar por el proceso
> definido en la sección 7. Cualquier cambio no autorizado en la implementación
> que desvíe la arquitectura documentada constituye deuda técnica y debe ser
> refactorizado.
