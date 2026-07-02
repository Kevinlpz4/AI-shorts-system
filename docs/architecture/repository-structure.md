# 📁 Repository Structure — Definitive Layout

> **Versión**: 1.0
> **Estado**: APPROVED
> **Vigente desde**: 2026-07-02
>
> Todo código nuevo debe respetar esta estructura.
> El código existente se migrará progresivamente.

---

## 1. Estructura Completa

```
src/
│
├── foundation/                        ← BASE TÉCNICA (stdlib only)
│   ├── __init__.py                    ← API pública del Foundation
│   ├── base/                          ← Entity, AggregateRoot, ValueObject
│   ├── ids/                           ← EntityId
│   ├── result/                        ← Result[T], Success, Failure, Error
│   ├── errors/                        ← FoundationError, DomainError, etc.
│   ├── events/                        ← DomainEvent, IntegrationEvent
│   ├── ports/                         ← ClockPort, UUIDProvider
│   └── types/                         ← IDs específicos del sistema
│
├── ai/                                ← AI CAPABILITIES (shared infra)
│   ├── domain/                        ← AIProvider port, AI ports
│   │   ├── ports/
│   │   └── exceptions/
│   └── infrastructure/                ← OpenRouter, adapters
│       ├── openrouter_provider.py
│       └── ...
│
├── ingestion/                         ← INGESTION BC (Epic 1)
│   ├── domain/
│   │   ├── entities/                  ← Source, Feed, FeedGroup, RawItem
│   │   ├── value_objects/             ← SyncPolicy, IngestionRun, etc.
│   │   ├── ports/                     ← TechnologyAdapter, ProviderAdapter, etc.
│   │   ├── services/                  ← FeedOrchestrator, SourceValidator
│   │   ├── events/                    ← Domain Events del BC
│   │   └── exceptions/
│   ├── application/
│   │   ├── commands/                  ← RegisterSource, TriggerIngestion, etc.
│   │   ├── queries/                   ← GetSourceStatus, ListFeeds, etc.
│   │   └── services/                  ← SchedulerOrchestrator, ProviderRegistry
│   └── infrastructure/
│       ├── persistence/               ← Postgres repos
│       ├── technology_adapters/       ← RssFetcher, HttpFetcher
│       ├── provider_adapters/         ← GenericRssProvider, RedditProvider
│       ├── parsers/                   ← GenericRssParser, RedditParser
│       ├── normalization/             ← Pipeline + steps
│       ├── event_bus/                 ← InProcessEventBus
│       └── scheduler/                 ← InProcessSchedulerDriver
│
├── research/                          ← RESEARCH BC (existing)
│   ├── domain/
│   │   ├── entities/
│   │   ├── value_objects/
│   │   ├── ports/
│   │   ├── services/
│   │   └── events/
│   ├── application/
│   │   └── use_cases/
│   └── infrastructure/
│       ├── persistence/
│       └── sources/
│
├── script_generation/                 ← SCRIPT GENERATION BC (future)
│   ├── domain/
│   ├── application/
│   └── infrastructure/
│
├── shared/                            ← DOMINIO COMPARTIDO ENTRE BCs
│   └── domain/
│       ├── category.py                ← Category entity
│       └── ...
│
└── presentation/                      ← PUNTOS DE ENTRADA
    ├── cli/                           ← CLI interface
    │   ├── commands/
    │   ├── container.py               ← CLI Composition Root
    │   └── main.py
    ├── api/                           ← REST API
    │   ├── routes/
    │   ├── container.py               ← API Composition Root
    │   └── main.py
    └── config/                        ← App-level configuration
        ├── __init__.py
        ├── settings.py                ← Pydantic Settings
        └── bootstrap.py               ← Composition Root central

tests/                                 ← TESTS (espejan src/)
├── foundation/
│   ├── test_entity.py
│   ├── test_value_object.py
│   └── ...
├── ai/
├── ingestion/
├── research/
├── shared/
└── presentation/
```

---

## 2. Mapeo con la estructura actual

| Actual → | Nueva ubicación | ¿Cuándo migrar? |
|----------|----------------|-----------------|
| `research/` | `src/research/` | Refactor post-Epic 1 |
| `domain/exceptions/` | `src/foundation/errors/` | Al implementar Foundation |
| `presentation/` | `src/presentation/` | Refactor post-Epic 1 |
| `infrastructure/ai/` | `src/ai/infrastructure/` | Refactor post-Epic 1 |
| `services/ai_service.py` | `src/ai/` | Refactor post-Epic 1 |
| `services/openai_service.py` | Eliminar (deprecado) | — |
| `app/config.py` | `src/presentation/config/` | Refactor |
| `app/main.py` | `src/presentation/` | Refactor |
| `app/logger.py` | `src/presentation/config/` | Refactor |
| `modules/` | Eliminar (legacy) | — |
| `scripts/` | Eliminar (legacy) | — |

---

## 3. Convenciones de la estructura

### 3.1 Cada BC es independiente

```
src/ingestion/
├── domain/     ← 0 dependencias de infraestructura
├── application/ ← depende de domain/ports
└── infrastructure/ ← depende de domain/ y application/
```

Ningún BC importa de otro BC directamente. La comunicación es por Integration Events.

### 3.2 foundation NO depende de nadie

```
src/foundation/  ← solo stdlib
```

Foundation no importa de ingestion/, research/, ni de ningún otro módulo.

### 3.3 shared/ contiene dominio compartido

```
src/shared/domain/category.py
```

Esto NO es foundation. Es dominio que múltiples BCs deben compartir (Category, etc.).
La diferencia: `foundation/` = mecanismos técnicos. `shared/` = conceptos de dominio.

### 3.4 ai/ es un módulo compartido

```
src/ai/domain/ports/     ← AIProvider port
src/ai/infrastructure/   ← OpenRouter provider
```

No es un BC (no tiene ciclo de vida editorial). Es un módulo de infraestructura
compartida que expone puertos de dominio para interactuar con AIs.

### 3.5 presentation/ contiene los entry points

```
src/presentation/cli/     ← Interfaz de línea de comandos
src/presentation/api/     ← REST API
src/presentation/config/  ← Config, bootstrap, DI
```

Cada sub-módulo de presentation tiene su propio Composition Root.

---

## 4. Reglas de dependencia

```
foundation/  ← nada (stdlib only)
     ↑
     ├── ai/
     ├── shared/
     ├── ingestion/
     ├── research/
     ├── script_generation/
     └── presentation/
          ↑
     (usa todos los BCs para construir composition roots)

Ningún BC importa de otro BC.
Todos importan de foundation.
shared/ puede ser importado por varios BCs.
ai/ puede ser importado por varios BCs.
presentation/ importa de todos (composition root).
```

---

## 5. ADR-022: Repository Structure

| Campo | Valor |
|-------|-------|
| **Estado** | APPROVED |
| **Contexto** | Sin una estructura definida, cada nuevo módulo elige su propia organización. Mover carpetas después duele. |
| **Decisión** | Adoptar la estructura `src/` con módulos independientes por BC. foundation/ como base técnica. shared/ para dominio compartido. ai/ para capacidades de IA compartidas. presentation/ para entry points. |
| **Alternativas** | Monolito plano (descartado — no escala a N BCs). Estructura por capas técnica (descartado — mezcla BCs). |
