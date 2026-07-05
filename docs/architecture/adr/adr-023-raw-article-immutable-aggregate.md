---
adr: "ADR-023"
title: "RawArticle Immutable Aggregate Pattern"
status: "APPROVED"
date: "2026-07-03"
---

# ADR-023: RawArticle Immutable Aggregate Pattern

## Contexto

El Bounded Context Ingestion define `RawArticle` como una entidad que representa
un artículo crudo obtenido de un Feed externo. Es un registro de auditoría —
una vez creado, nunca cambia.

RawArticle tiene dos características que crean una tensión arquitectónica:

1. **Es conceptualmente un Aggregate Root (AR)**: puede haber millones de
instancias, cada una debe ser cargable y persistible independientemente
(no puede vivir dentro de Feed), y tiene invariantes de creación que
proteger (unicidad de `external_id + feed_id`, unicidad de `content_hash`).

2. **Es técnicamente inmutable**: no tiene métodos de mutación, no tiene
ciclo de vida (solo existe el estado "creado"), no emite eventos de dominio,
y no requiere control de concurrencia posterior a la creación.

En Foundation v1.0, `AggregateRoot` hereda de `Entity` y agrega dos capacidades:
`_events` (lista de Domain Events) y los métodos `register_event()` /
`pull_events()`. RawArticle nunca necesita ninguna de estas capacidades.

El diseño del BC Ingestion debe decidir cómo modelar RawArticle: ¿hereda de
`AggregateRoot` (fiel al concepto de AR) o de `Entity` (evitando overhead
innecesario)?

## Decisión

**RawArticle hereda de `Entity` (Foundation), NO de `AggregateRoot`.**
Se documenta como Aggregate Root por convención (frontera de consistencia
propia, volumen masivo, persistencia independiente).

### Implementación

```python
from foundation.entities import Entity
from ingestion.domain.entities.ids import RawArticleId

class RawArticle(Entity):
    """Artículo crudo e inmutable recolectado de un Feed.

    ES un Aggregate Root por convención (frontera de consistencia, volumen).
    NO hereda de AggregateRoot porque es inmutable y no emite eventos.

    Ver ADR-023 para la justificación completa.
    """

    id: RawArticleId
    feed_id: FeedId
    # ... demás atributos inmutables

    def __init__(self, ...):
        # Constructor con validación de invariantes
        # NO tiene register_event(), NO tiene pull_events()
        # NO tiene setters, NO tiene métodos de mutación
```

### Lo que NO se hace

- NO se hereda de `AggregateRoot` (evita overhead de `_events`)
- NO se usa un decorador `@aggregate_root` (Foundation FROZEN lo impide)
- NO se modifica Foundation (FROZEN — no se toca)

## Consecuencias

### Positivas ✅

- **Sin overhead innecesario**: RawArticle no carga `_events` ni métodos
  que nunca usará. Cada instancia es más liviana.
- **Semántica correcta**: `Entity` significa "tiene identidad". RawArticle
  tiene identidad (`RawArticleId`). AggregateRoot significa "frontera de
  consistencia + eventos". RawArticle tiene frontera pero no eventos.
  Entity es técnicamente correcto.
- **Simplicidad**: El constructor de RawArticle no necesita inicializar
  `_events` ni preocuparse por `register_event()`. Es una clase plana
  con validación en el constructor.
- **Foundation permanece FROZEN**: No se requieren cambios en Foundation.
- **Menos código de test**: No hay que testear comportamiento de eventos
  en una entidad inmutable que nunca los emite.

### Negativas ⚠️

- **Confusión conceptual**: Un desarrollador que lea el código verá
  `class RawArticle(Entity)` y podría preguntarse "¿esto es un AR o no?".
  La documentación (docstring, ADR, diseño) debe compensar esto.
- **Violación de "pureza DDD"**: Algunos puristas argumentarían que
  "todo AR debe heredar de AggregateRoot". La realidad del código
  debe priorizar la corrección técnica sobre la pureza teórica.
- **Futura migración**: Si Foundation agrega un `AggregateRootMarker`
  o similar en el futuro, RawArticle deberá migrar para mantener
  consistencia con otros ARs.
- **Herramientas de análisis**: Herramientas que escanean la jerarquía
  de clases para identificar ARs podrían no detectar RawArticle.
  Esto se mitiga con el docstring y naming claro.

## Alternativas Consideradas

### Alternativa 1: Heredar de AggregateRoot (descartada)

- **Descripción**: RawArticle hereda de `AggregateRoot` como cualquier otro
  AR, aunque nunca use `_events`, `register_event()`, o `pull_events()`.
- **Ventaja**: Consistencia técnica — "todo AR hereda de AggregateRoot".
  Coherencia con NewsSource y Feed.
- **Desventaja**: Overhead de memoria (lista de eventos vacía por instancia),
  overhead de inicialización, métodos públicos que no deberían existir
  (`register_event()` en una entidad inmutable es confuso).
- **Descartada por**: El overhead es pequeño por instancia pero se multiplica
  por millones de RawArticles. Y la confusión semántica de tener
  `register_event()` en una entidad inmutable es un smell de diseño.

### Alternativa 2: Decorador @aggregate_root o marker class (descartada)

- **Descripción**: Usar un decorador de Python o una clase marker como
  `AggregateRootMarker` para señalar que una clase que hereda de Entity
  debe ser tratada como Aggregate Root.
- **Ventaja**: Proporciona una señal explícita en el código sin herencia
  real de AggregateRoot.
- **Desventaja**: Requiere modificar Foundation (FROZEN — no permitido).
  Si se implementa dentro de Ingestion, duplica mecanismos de Foundation.
- **Descartada por**: Foundation FROZEN. Se reconsidera si Foundation
  introduce este mecanismo en el futuro.

### Alternativa 3: RawArticle como Entity + AR por naming (SELECCIONADA)

- **Descripción**: RawArticle hereda de Entity. Se nombra y documenta
  como Aggregate Root. Docstring y ADR explican la decisión.
- **Ventaja**: Simple, sin overhead, Foundation FROZEN, semánticamente
  correcto.
- **Desventaja**: Requiere documentación explícita y disciplina del equipo.
- **Seleccionada por**: Es la opción más pragmática. La confusión potencial
  se mitiga con documentación y revisión de código.

## Compliance

- **Principios**: P2 (Clean Architecture), P4 (DDD táctico)
- **Baseline**: v1.0 (no rompe)
- **ADR relacionados**: ADR-021 (Foundation FROZEN — no modificar Foundation),
  ADR-022 (ErrorCode enum separado, independiente)
- **Foundation**: No se modifica. Permanece FROZEN.

### Documentación Relacionada

- `docs/architecture/ingestion-domain-design.md` — Sección 2.4 (RawArticle entity)
- `docs/architecture/aggregate-design.md` — Sección 10 (Entity-inheritance decision)
- `docs/architecture/repository-contracts.md` — RawArticleRepository (trata RawArticle como AR para persistencia)

### Cumplimiento Futuro

Si en el futuro Foundation introduce:
- Un marcador `AggregateRootMarker` → RawArticle lo adopta
- `AggregateRoot` se vuelve más ligero (ej: sin `_events` obligatorio) →
  RawArticle migra a `AggregateRoot`
- Un mecanismo de mixins → RawArticle usa `AggregateRootCapability` o similar
