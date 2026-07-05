# Application Layer Folder Structure — Ingestion Bounded Context

> **Estructura de directorios y módulos para la capa de aplicación del BC Ingestion**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-03
> Basado en: Sprint 4.1 Design — Application Layer
> Dependencias: Foundation v1.0 (FROZEN), Ingestion Domain v2.0 (FROZEN)

---

## 1. Estructura Completa

```
src/ingestion/
├── __init__.py
├── domain/                           (EXISTENTE — FROZEN)
│   ├── __init__.py
│   ├── entities/
│   ├── value_objects/
│   ├── events/
│   ├── ports/
│   └── exceptions/
│
└── application/                      (NUEVO — este diseño)
    ├── __init__.py
    │
    ├── commands/                     ← Objetos Command (datos inmutables)
    │   ├── __init__.py
    │   ├── source_commands.py        ← RegisterSource, UpdateSource, EnableSource, DisableSource
    │   ├── feed_commands.py          ← RegisterFeed, UpdateFeed, PauseFeed, ActivateFeed,
    │   │                                RecordCollection, RecordFailure
    │   ├── article_commands.py       ← CreateRawArticle
    │   ├── source_category_commands.py ← AssignCategoryToSource, AssignTopicToSource
    │   └── feed_category_commands.py   ← AssignCategoryToFeed, AssignTopicToFeed
    │
    ├── queries/                      ← Objetos Query (datos inmutables)
    │   ├── __init__.py
    │   ├── source_queries.py         ← FindSource, ListActiveSources
    │   ├── feed_queries.py           ← FindFeed, ListFeeds
    │   └── article_queries.py        ← FindArticle, ListArticles
    │
    ├── dto/                          ← Data Transfer Objects
    │   ├── __init__.py
    │   ├── common.py                 ← QueryResult[T], PaginatedDTO, ResultDTO, ErrorDTO
    │   ├── source_dto.py             ← SourceSummaryDTO, SourceDetailDTO
    │   ├── feed_dto.py               ← FeedSummaryDTO, FeedDetailDTO
    │   ├── article_dto.py            ← RawArticleSummaryDTO, RawArticleDetailDTO
    │   ├── category_dto.py           ← CategorySummaryDTO, CategoryDetailDTO
    │   └── topic_dto.py              ← TopicSummaryDTO, TopicDetailDTO
    │
    ├── ports/                        ← Output Ports (Application Layer)
    │   ├── __init__.py
    │   ├── event_publisher.py        ← EventPublisher Protocol
    │   └── unit_of_work.py           ← UnitOfWork Protocol
    │
    ├── mappers/                      ← Entity ↔ DTO conversion
    │   ├── __init__.py
    │   ├── source_mapper.py          ← NewsSource → SourceSummaryDTO / SourceDetailDTO
    │   ├── feed_mapper.py            ← Feed → FeedSummaryDTO / FeedDetailDTO
    │   ├── article_mapper.py         ← RawArticle → RawArticleSummaryDTO / RawArticleDetailDTO
    │   ├── category_mapper.py        ← Category → CategorySummaryDTO / CategoryDetailDTO
    │   └── topic_mapper.py           ← Topic → TopicSummaryDTO / TopicDetailDTO
    │
    ├── services/                     ← Application Services (orquestan use cases)
    │   ├── __init__.py
    │   ├── source_service.py         ← Use cases grouped by aggregate: Register, Update, Enable, Disable
    │   ├── feed_service.py           ← Use cases grouped by aggregate: Register, Update, Pause, Activate,
    │   │                                RecordCollection, RecordFailure
    │   └── article_service.py        ← Use cases: CreateRawArticle, Search queries
    │
    └── exceptions/                   ← Application Layer errors
        ├── __init__.py
        └── application_errors.py     ← ApplicationError, ApplicationErrorCode
```

---

## 2. Justificación de Decisiones Estructurales

### 2.1 Commands y Queries separados

| Decisión | Alternativa | Razón |
|----------|-------------|-------|
| **✅ Separar commands/ de queries/** | Un solo directorio `messages/` | Claridad semántica. Commands mutan estado, Queries no. Separarlos por directorio hace explícita la intención. El costo (un directorio extra) es despreciable. |

### 2.2 Services por aggregate (NO 1 class per use case)

| Decisión | Alternativa | Razón |
|----------|-------------|-------|
| **✅ Un Service class por aggregate** (SourceService, FeedService, ArticleService) | Un use case class por operación (RegisterSourceUseCase, etc.) | **YAGNI**. Con 10-14 use cases total, crear una clase por cada uno genera ~12 archivos extra sin beneficio real. Agrupar por aggregate mantiene cohesión y reduce navegación. Se puede migrar a 1 clase por use case si el service supera las 300 líneas. |

### 2.3 DTOs separados de Mappers

| Decisión | Alternativa | Razón |
|----------|-------------|-------|
| **✅ DTOs en `dto/`, Mappers en `mappers/`** | DTOs con métodos to_domain/from_domain | **SRP**. Los DTOs son datos. Los mappers son transformación. Mezclarlos genera acoplamiento entre representación y conversión. Además, los DTOs se importan desde presentation/, mientras que los mappers solo se usan en application/. |

### 2.4 Output Ports en `application/ports/`

| Decisión | Alternativa | Razón |
|----------|-------------|-------|
| **✅ EventPublisher y UnitOfWork en `application/ports/`** | En un directorio `ports/` raíz o en `domain/ports/` | Domain ports (repo protocols) definen lo que el DOMINIO necesita. Application ports (EventPublisher, UnitOfWork) definen lo que la APLICACIÓN necesita. Son conceptos diferentes. Además, domain/ports/ está FROZEN. |

### 2.5 Excepciones de aplicación separadas

| Decisión | Alternativa | Razón |
|----------|-------------|-------|
| **✅ `application/exceptions/` propio** | Reusar exceptions del domain | Las excepciones de application (comando inválido, recurso no encontrado en aplicación) son diferentes de las de dominio (reglas de negocio violadas). Mezclarlas violaría SRP y dificultaría el mapeo de errores. |

---

## 3. Dirección de Dependencias

```
    ┌──────────────────────────────┐
    │       PRESENTATION           │
    │  (CLI, API, WebSocket)       │
    │  importa application/        │
    └──────────┬───────────────────┘
               │ llama servicios
               ▼
    ┌──────────────────────────────┐
    │       APPLICATION            │
    │  ┌────────────────────────┐  │
    │  │ services/              │  │  ← Orquesta use cases
    │  │ mappers/               │  │  ← Convierte entidades ↔ DTOs
    │  │ commands/ queries/     │  │  ← Pure data
    │  │ dto/                   │  │  ← Data transfer objects
    │  │ ports/ (output)        │  │  ← EventPublisher, UnitOfWork
    │  │ exceptions/            │  │  ← Application errors
    │  └────────────────────────┘  │
    │         │                     │
    │         ▼                     │
    │  ┌────────────────────────┐  │
    │  │       DOMAIN           │  │  ← IMPORTADO, no modificado
    │  │  (FROZEN)              │  │
    │  └────────────────────────┘  │
    └──────────────────────────────┘
               │
               ▼ (implementa ports)
    ┌──────────────────────────────┐
    │     INFRASTRUCTURE           │
    │  (DB adapters, event bus,    │
    │   HTTP clients, scheduler)   │
    └──────────────────────────────┘
```

**Reglas estrictas**:
- `application/` → SOLO importa `domain/` y `foundation/`
- `application/` → **NO importa** `infrastructure/`, `presentation/`
- `application/` → **NO modifica** `domain/` (FROZEN)
- `application/ports/` → define Protocols que `infrastructure/` implementa
- `application/mappers/` → conoce domain entities y DTOs (no al revés)

---

## 4. Convenciones de Nomenclatura

| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| Command | `{Verbo}{Sustantivo}Command` | `RegisterSourceCommand` |
| Query | `{Verbo}{Sustantivo}Query` | `FindSourceQuery` |
| Summary DTO | `{Sustantivo}SummaryDTO` | `SourceSummaryDTO` |
| Detail DTO | `{Sustantivo}DetailDTO` | `SourceDetailDTO` |
| Service | `{Sustantivo}Service` | `SourceService` |
| Mapper | `{Sustantivo}Mapper` | `SourceMapper` |
| Use Case method | `execute_{verbo}_{sustantivo}` | `execute_register_source` |
| Application Error | `{Adjetivo}{Contexto}Error` | `CommandValidationError` |

---

## 5. Archivos y su Responsabilidad

| Archivo | Responsabilidad | Importa de |
|---------|----------------|------------|
| `commands/*.py` | Definir dataclasses inmutables de comandos | domain/ (IDs, VOs), foundation |
| `queries/*.py` | Definir dataclasses inmutables de consultas | domain/ (IDs), foundation |
| `dto/*.py` | Definir dataclasses de salida (públicas) | foundation, Python stdlib |
| `dto/common.py` | QueryResult[T], PaginatedDTO, ResultDTO | foundation |
| `ports/event_publisher.py` | Protocol para publicar eventos | foundation.events |
| `ports/unit_of_work.py` | Protocol para transacciones | foundation |
| `mappers/*.py` | Convertir domain entity ↔ DTO | domain/entities, dto/ |
| `services/*.py` | Orquestar use cases completos | commands, queries, dto, mappers, ports, domain/ports, domain/exceptions |
| `exceptions/*.py` | Definir errores de capa aplicación | foundation.errors |

---

## 6. Migración desde Diseño Actual

El directorio `application/` es **nuevo**. No hay migración de archivos existentes. El domain/ permanece intacto y FROZEN.

**Orden de implementación recomendado**:
1. `application/exceptions/` — errores base (sin dependencias)
2. `application/commands/` y `application/queries/` — datos inmutables
3. `application/dto/` — estructuras de salida
4. `application/ports/` — contratos de infraestructura
5. `application/mappers/` — conversión entities ↔ DTOs
6. `application/services/` — lógica de orquestación (depende de todo lo anterior)
