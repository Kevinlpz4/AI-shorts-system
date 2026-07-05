---
title: "Architecture Review Board Report — Sprint 3.1 Ingestion Domain Core"
status: "APPROVED"
date: "2026-07-03"
---

# ARB Report: Sprint 3.1 — Ingestion Domain Core Design

> **Evaluación arquitectónica completa del modelo de dominio del Bounded Context Ingestion**
>
> Versión: 2.0 | Estado: **DOMAIN MODEL FROZEN** ✅
> Basado en: Foundation v1.0 STABLE (FROZEN), ADR-021, ADR-022, ADR-023
> Incluye: Domain Freeze Review (Sprint 3.1.5)

---

## Resumen Ejecutivo

El Sprint 3.1 ha producido **6 documentos** (3,149 líneas), **1 ADR nuevo** (ADR-023), y un modelo de dominio completo con **5 entidades**, **7 Value Objects**, **3 Domain Events**, **5 Repository Ports**, y **0 Domain Services**.

**Veredicto**: ✅ **APROBADO** — El modelo cumple con DDD táctico, Clean Architecture, SOLID, Hexagonal Architecture, ADR-021 (Foundation Stability Policy), ADR-022 (ErrorCode), y mantiene Foundation FROZEN. Se identifican 3 riesgos bajos y 2 oportunidades de mejora post-aprobación.

---

## 1. Evaluación del Modelo de Dominio

### 1.1 Entidades y Aggregates

| Entidad | Tipo | Veredicto |
|---------|------|-----------|
| **NewsSource** | Aggregate Root | ✅ Correcto. Ciclo de vida independiente, punto de entrada de configuración, referenciado por múltiples Feeds. |
| **Feed** | Aggregate Root | ✅ Correcto. Ciclo de vida propio (activo/pausado/inactivo), reglas de negocio (retry, auto-pause), unidad de ejecución. |
| **RawArticle** | Aggregate Root (inmutable) | ✅ Correcto. Volumen masivo justifica AR independiente. ADR-023 documenta herencia de Entity (no AggregateRoot). |
| **Category** | Entity (no AR) | ✅ Correcto. Tiene identidad pero no dependientes transaccionales. Consistencia eventual. |
| **Topic** | Entity (no AR) | ✅ Correcto. Identidad propia, vida simple, referenciado por ID. |

### 1.2 Value Objects (7)

| VO | Justificación |
|----|---------------|
| **SourceUrl** | Validación de URL + unicidad. Comportamiento: `is_valid_url()` |
| **ArticleUrl** | Validación de URL + unicidad dentro del Feed. Comportamiento: `is_valid_url()` |
| **ArticleTitle** | Validación: no vacío, max 500 chars. Comportamiento: `is_empty()`, `truncate()` |
| **Author** | Validación: max 200 chars, opcional. Comportamiento: `is_anonymous()` |
| **Language** | Validación: ISO 639-1. Comportamiento: `is_known()`, `display_name()` |
| **SourceType** | Enum de tipos de fuente conocidos. Comportamiento: `supports_capability()` |
| **CategoryName** | Validación: no vacío, único entre hermanos. |

### 1.3 Domain Events (3)

| Evento | Trigger | Veredicto |
|--------|---------|-----------|
| **RawArticleCollected** | Feed.record_collection() con artículos nuevos | ✅ Necesario. Dispara pipeline de normalización. |
| **SourceEnabled** | NewsSource.enable() | ✅ Necesario. Permite reactivar Feeds downstream. |
| **SourceDisabled** | NewsSource.disable() | ✅ Necesario. Detiene ejecución de Feeds. |

**Descartados por YAGNI**: SourceCreated, CategoryCreated, FeedPaused, FeedFetchStarted, FeedFetchCompleted, FeedFetchFailed, NewItemsDetected — sin consumidores identificados en el dominio.

### 1.4 Repository Ports (5)

| Puerto | Métodos | Veredicto |
|--------|---------|-----------|
| **NewsSourceRepository** | 5 métodos | ✅ Completos |
| **FeedRepository** | 7 métodos | ✅ Incluye `find_due()` para scheduler |
| **RawArticleRepository** | 6 métodos | ✅ Incluye dedup por hash y external_id |
| **CategoryRepository** | 5 métodos | ✅ Incluye jerarquía |
| **TopicRepository** | 4 métodos | ✅ Simple, suficiente |

### 1.5 Domain Services

**CERO.** ✅ Correcto. FeedOrchestrator pertenece a Application Layer. SourceValidator es responsabilidad del AR o Application Service. YAGNI aplicado estrictamente.

---

## 2. Bounded Context Evaluation

### 2.1 Límites del Contexto

| Aspecto | Evaluación |
|---------|------------|
| **Responsabilidad** | Obtener información desde fuentes externas, normalizarla y publicarla. ✅ Claro, bien definido. |
| **Límites** | Comienza en configuración de fuente, termina en integración event. ✅ Correcto. |
| **Relaciones externas** | Publica Integration Events → Research BC. ✅ Sin acoplamiento directo. |
| **Lenguaje propio** | NewsSource, Feed, RawArticle, Topic. ✅ Diferenciado de otros BCs. |

### 2.2 Relaciones con Foundation

| Componente Foundation | Uso en Ingestion | Veredicto |
|-----------------------|-------------------|-----------|
| EntityId (base class) | SourceId, FeedId, RawArticleId, CategoryId, TopicId | ✅ Heredan, viven en Ingestion |
| Entity | RawArticle, Category, Topic | ✅ |
| AggregateRoot | NewsSource, Feed | ✅ |
| ValueObject | 7 VOs | ✅ |
| DomainEvent | 3 eventos | ✅ |
| Result/Error/DomainError | En repositorios y operaciones | ✅ Previsto |
| ClockPort / UUIDProvider | En creación de RawArticle | ✅ Consumido, no modificado |

**Foundation FROZEN**: ✅ En ningún momento se propone modificar Foundation.

---

## 3. Aggregate Boundaries

### 3.1 Fronteras de Consistencia

```
┌─────────────────────────────────────────────────────────────────┐
│  NewsSource (AR)           Feed (AR)           RawArticle (AR)  │
│  ┌─────────────────┐      ┌──────────────┐    ┌──────────────┐  │
│  │ • name           │      │ • url         │    │ • title       │  │
│  │ • source_type    │      │ • is_active   │    │ • content_hash│  │
│  │ • source_url     │      │ • retry_count │    │ • external_id │  │
│  │ • is_active      │      │ • categories  │    │ • fetched_at  │  │
│  └─────────────────┘      │ • topics      │    └──────────────┘  │
│                            └──────────────┘                      │
│  ────────────────────────────────────────────────────────────    │
│  Category (Entity)        Topic (Entity)                         │
│  ┌─────────────────┐      ┌──────────────┐                      │
│  │ • name           │      │ • name        │                      │
│  │ • slug           │      │ • is_active   │                      │
│  │ • parent_id      │      └──────────────┘                      │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Reglas de Consistencia entre Aggregates

| Regla | Tipo | Correcta? |
|-------|------|-----------|
| Feed refiere NewsSource por SourceId | Consistencia eventual | ✅ |
| RawArticle refiere Feed por FeedId | Consistencia eventual | ✅ |
| NewsSource no se desactiva si tiene Feeds activos | Verificado en creación/desactivación | ✅ |
| Feed no se crea bajo NewsSource inactivo | Verificado en aplicación | ✅ |
| Category refs por CategoryId desde Feed/NewsSource | Consistencia eventual | ✅ |
| Topic refs por TopicId desde Feed/RawArticle | Consistencia eventual | ✅ |

### 3.3 Decisión RawArticle-Entity (ADR-023)

RawArticle hereda de `Entity`, no de `AggregateRoot`, a pesar de ser AR por concepto. 
- ✅ **Razón**: Es inmutable, no emite eventos, no necesita `_events` ni `register_event()`.
- ✅ **Mitigación**: Documentado en ADR-023 + docstring + documentación de diseño.
- ⚠️ **Riesgo**: Confusión conceptual mitigada con documentación explícita.

---

## 4. Consistencia del Lenguaje Ubicuo

### 4.1 Verificación de Términos

| Término | Docs | Código (esperado) | Consistente? |
|---------|------|-------------------|--------------|
| NewsSource | 5 documentos | src/ingestion/domain/entities/news_source.py | ✅ |
| Feed | 5 documentos | src/ingestion/domain/entities/feed.py | ✅ |
| RawArticle | 5 documentos | src/ingestion/domain/entities/raw_article.py | ✅ |
| Category | 5 documentos | src/ingestion/domain/entities/category.py | ✅ |
| Topic | 5 documentos | src/ingestion/domain/entities/topic.py | ✅ |
| SourceId | 5 documentos | src/ingestion/domain/entities/ids.py | ✅ |
| FeedId | 5 documentos | src/ingestion/domain/entities/ids.py | ✅ |
| RawArticleId | 5 documentos | src/ingestion/domain/entities/ids.py | ✅ |
| CategoryId | 5 documentos | src/ingestion/domain/entities/ids.py | ✅ |
| TopicId | 5 documentos | src/ingestion/domain/entities/ids.py | ✅ |
| IngestionErrorCode | 4 documentos | src/ingestion/domain/exceptions/errors.py | ✅ |

### 4.2 Términos Excluidos del Dominio

| Término | Destino | Razón |
|---------|---------|-------|
| FeedGroup | Application/Infrastructure | Agrupación operativa sin invariantes de dominio |
| Batch (UUID) | Concepto (no entidad) | Identificador de ejecución, sin comportamiento |
| IngestionRun | Application Layer | Resultado de ejecución, no invariante de dominio |
| SyncPolicy | VO de configuración pura | Timing pertenece al scheduler (Application) |
| SourceConfig | Reemplazado por SourceUrl + SourceType | Atributos planos en NewsSource |

---

## 5. Dependencias

### 5.1 Internas

| Dependencia | Tipo | Correcta? |
|-------------|------|-----------|
| Foundation v1.0 | Consumo (FROZEN) | ✅ |
| Ingestion BC → Foundation | Domain/ importa foundation.* | ✅ Solo consume, no modifica |

### 5.2 Externas

| Dependencia | Evaluación |
|-------------|------------|
| **Ninguna dependencia externa** | ✅ El dominio puro no importa nada externo a Foundation. Sin HTTP, sin DB, sin APIs, sin frameworks. |

---

## 6. Riesgos Identificados

| # | Riesgo | Severidad | Mitigación |
|---|--------|-----------|------------|
| **R-01** | **RawArticle-Entity confusión**: Desarrolladores futuros pueden preguntarse si RawArticle es AR o no. | 🔶 Baja | ADR-023 + docstring + documentación explícita. Code review debe verificar. |
| **R-02** | **NewsSource desactivación con Feeds activos**: Si la verificación no se implementa en Application Layer, puede quedar en estado inconsistente. | 🔶 Baja | La invariante está documentada en 3 documentos. Debe implementarse en el Application Service que orquesta enable/disable. |
| **R-03** | **Crecimiento de RawArticle**: Millones de instancias pueden presionar el repositorio. | 🟡 Media | El diseño RawArticleRepository incluye paginación (`find_by_feed(page, size)`). La implementación de infraestructura debe optimizar el store. |
| **R-04** | **Jerarquía de Category sin control de ciclos**: La validación de ciclos debe implementarse correctamente. | 🔶 Baja | Documentado como invariante. Debe implementarse en Category.change_parent(). |
| **R-05** | **Eventos sin consumidores en el BC**: RawArticleCollected no tiene consumidor dentro del dominio — depende de Application Layer. | 🔶 Baja | Esto es intencional. El dominio define el evento, Application/Infrastructure lo maneja. |

---

## 7. Oportunidades de Simplificación

| # | Oportunidad | Impacto | Recomendación |
|---|-------------|---------|---------------|
| **S-01** | **Unificar CategoryName con atributo name plano**: CategoryName es un VO con validación de no-vacío. ¿Realmente necesita ser VO? | Bajo | Por ahora mantenerlo. Si en implementación se ve que solo valida "no vacío", colapsar a `str` en Category. Evaluar en Sprint 3.2+. |
| **S-02** | **Author podría ser `str | None` en vez de VO**: Solo valida max length y opcional. Mismo caso que S-01. | Bajo | Mantener como VO. Si el Author no desarrolla comportamiento adicional, colapsar. |

---

## 8. Violaciones DDD Detectadas

| # | Violación | Severidad | Estado |
|---|-----------|-----------|--------|
| **V-01** | **RawArticle hereda Entity, no AggregateRoot**: Técnicamente correcto (inmutable, sin eventos), pero conceptualmente es un AR. | ⚠️ Leve | Mitigado por ADR-023. Aceptado. |
| **Ninguna otra violación DDD detectada** | ✅ | — | — |

---

## 9. Recomendaciones del ARB

### 9.1 Aprobación

✅ **El Architecture Review Board recomienda APROBAR el diseño del Sprint 3.1 — Ingestion Domain Core.**

### 9.2 Recomendaciones para Implementación (Sprint 3.2+)

1. **Implementar Feed como AggregateRoot** (hereda de `AggregateRoot`) con `_events` y `pull_events()`.
2. **Implementar NewsSource como AggregateRoot** con eventos SourceEnabled/SourceDisabled.
3. **Implementar RawArticle como Entity** (hereda de `Entity`, NO de `AggregateRoot`) según ADR-023.
4. **Implementar Category y Topic como Entity** (hereda de `Entity`).
5. **Crear IngestionErrorCode** como `str, Enum` independiente (no hereda Foundation ErrorCode).
6. **Application Layer** debe implementar FeedOrchestrator como Application Service (no Domain Service).
7. **FeedGroup** debe diseñarse en Application/Infrastructure, NO en dominio.
8. **Integration Events** (NewRawItemsAvailable) se diseñan en un sprint posterior.

### 9.3 No Aplazar

| Acción | Sprint |
|--------|--------|
| Validación de ciclos en Category | Sprint 3.2 |
| Control de Feeds activos al desactivar NewsSource | Sprint 3.2 |
| Deduplicación por hash + external_id en RawArticle | Sprint 3.3+ |

---

## 10. Artefactos del Sprint

| Artefacto | Archivo | Líneas |
|-----------|---------|--------|
| Domain Design v2.0 | `docs/architecture/ingestion-domain-design.md` | 1,098 |
| Ubiquitous Language | `docs/architecture/ubiquitous-language.md` | 349 |
| Aggregate Design | `docs/architecture/aggregate-design.md` | 512 |
| Repository Contracts | `docs/architecture/repository-contracts.md` | 668 |
| Domain Events | `docs/architecture/domain-events.md` | 361 |
| ADR-023 | `docs/architecture/adr/adr-023-raw-article-immutable-aggregate.md` | 161 |
| ARB Report | `docs/architecture/arb-report-sprint-3.1.md` | (este) |

**Total**: ~3,149 líneas de especificación. **CERO líneas de código.**

---

## Veredicto Final

| Criterio | Resultado |
|----------|-----------|
| **DDD Tactical Patterns** | ✅ Cumple (Entities, VOs, ARs, Events, Repositories, 0 Domain Services) |
| **Clean Architecture** | ✅ Capas definidas, domain/ no importa infraestructura |
| **SOLID** | ✅ SRP, OCP, LSP, ISP, DIP verificados |
| **Hexagonal Architecture** | ✅ Ports (Protocols) definidos, adapters son futuro |
| **ADR-021 Foundation Stability Policy** | ✅ IDs permanecen en Ingestion, no contaminan Foundation |
| **ADR-022 ErrorCode Enum** | ✅ IngestionErrorCode propio (str, Enum), independiente |
| **Foundation FROZEN** | ✅ No se modifica Foundation |
| **YAGNI** | ✅ 0 Domain Services, 3 eventos (no 10), FeedGroup fuera |
| **Consistencia Cross-doc** | ✅ 8 reglas de consistencia verificadas |

---

---

## 11. Domain Freeze Review (Sprint 3.1.5)

### 11.1 Resumen de Correcciones

| Hallazgo | Acción | Estado |
|----------|--------|--------|
| **H-01**: I-05, I-06 cruzaban fronteras de AR NewsSource | Movidas a Application Layer (AL-01, AL-02) | ✅ Corregido |
| **H-01**: I-09, I-10 (Feed → NewsSource) cruzaban AR | Movidas a Application Layer (AL-03, AL-04) | ✅ Corregido |
| **H-01**: I-21 (RawArticle → Feed) cruzaba AR | Movida a Application Layer (AL-05) | ✅ Corregido |
| **H-02**: Author como VO sin comportamiento suficiente | Eliminado. `author` es `str \| None` en RawArticle | ✅ Corregido |
| Invariantes re-numeradas: 28 → 23 (secuencia I-01 a I-23) | Consistente en todos los documentos | ✅ |

### 11.2 Auditoría de Aggregate Roots

| AR | ¿Por qué AR? | ¿Podría ser Entity? | Veredicto |
|----|-------------|---------------------|-----------|
| **NewsSource** | Ciclo de vida independiente, punto de entrada, referenciado por Feeds | ❌ No. Sin AR, Feed no tendría aggregate padre. | ✅ AR correcto |
| **Feed** | Ciclo de vida propio (activo/pausado/inactivo), reglas de negocio, unidad de ejecución | ❌ No. Si fuera hijo de NewsSource, cargar el source cargaría todos los Feeds. | ✅ AR correcto |
| **RawArticle** | Volumen masivo, frontera de consistencia en creación | ❌ No. Si fuera hijo de Feed, cargar un feed cargaría millones de RawArticles. Hereda Entity técnicamente (ADR-023). | ✅ AR correcto |

### 11.3 Auditoría de Value Objects

| VO | Responsabilidad | ¿Por qué no es primitivo? | ¿Por qué no es Entity? | Veredicto |
|----|----------------|--------------------------|----------------------|-----------|
| **SourceUrl** | Validar URL base de NewsSource | Validación + normalización | Sin identidad | ✅ Mantener |
| **ArticleUrl** | Validar URL de RawArticle | Validación + extracción de dominio | Sin identidad | ✅ Mantener |
| **ArticleTitle** | Validar título (no vacío, max 500) | Validación + sanitización | Sin identidad | ✅ Mantener |
| **Language** | Validar código ISO 639-1 | Validación + display_name + is_rtl | Sin identidad | ✅ Mantener |
| **SourceType** | Clasificar tipo de fuente | Enum con semántica de dominio | Sin identidad | ✅ Mantener |
| **CategoryName** | Validar nombre de categoría | Validación + caracteres permitidos | Sin identidad | ✅ Mantener |

> **Author**: ❌ **Eliminado**. Solo validaba max length y opcional. Sin comportamiento de dominio suficiente. Reemplazado por `str \| None`.

### 11.4 Auditoría de Domain Events

| Evento | Publisher | Trigger | Consumidor potencial | Veredicto |
|--------|-----------|---------|---------------------|-----------|
| **RawArticleCollected** | `Feed.record_collection()` | Artículos nuevos después de dedup | Normalization Pipeline | ✅ Esencial |
| **SourceEnabled** | `NewsSource.enable()` | Source activado | SchedulerDriver (reanuda Feeds) | ✅ Necesario |
| **SourceDisabled** | `NewsSource.disable()` | Source desactivado | SchedulerDriver (detiene Feeds), AlertService | ✅ Crítico |

**Descartados por YAGNI**: SourceCreated, CategoryCreated, FeedPaused, FeedFetchStarted, FeedFetchCompleted, FeedFetchFailed, NewItemsDetected.

### 11.5 Métricas del Domain Freeze

| Métrica | Valor |
|---------|-------|
| Invariantes de dominio | 23 (I-01 a I-23) |
| Reglas Application Layer | 5 (AL-01 a AL-05) |
| Value Objects | 6 |
| Domain Events | 3 |
| Aggregate Roots | 3 |
| Entities (no AR) | 2 (Category, Topic) |
| Repository Ports | 5 |
| Domain Services | 0 |
| Archivos modificados | 3 (ingestion-domain-design.md, aggregate-design.md, ubiquitous-language.md) |

---

## 🏆 Veredicto Final: Domain Model FROZEN

| Criterio | Resultado |
|----------|-----------|
| **Aggregate Boundaries** | ✅ 3 ARs, 2 Entities, fronteras correctas, referencias por ID |
| **Invariants Ownership** | ✅ 23 invariantes intra-AR, 5 reglas cross-AR en Application Layer |
| **Value Objects Audit** | ✅ 6 VOs justificados, 1 eliminado por YAGNI |
| **Domain Events Audit** | ✅ 3 eventos con consumidores, 7 descartados por YAGNI |
| **YAGNI Compliance** | ✅ 0 Domain Services, FeedGroup fuera, Author eliminado, eventos mínimos |
| **Clean Architecture** | ✅ domain/ puro, zero infraestructura, zero dependencias externas |
| **DDD Tactical Patterns** | ✅ Entities, VOs, ARs, Events, Repositories, Services (cero) |
| **Foundation Compatibility** | ✅ Foundation FROZEN, IDs en Ingestion, ErrorCode propio |
| **Cross-document Consistency** | ✅ 8 reglas de verificación, 0 desviaciones |

> ## ✅ DOMAIN MODEL FROZEN
>
> El Architecture Review Board declara oficialmente:
>
> - El modelo de dominio del Ingestion BC está **COMPLETO, VERIFICADO y FROZEN**.
> - No se agregarán nuevas entidades, VOs, ARs, eventos, o relaciones sin una **Request for Architecture Decision (RAD)**.
> - Queda **AUTORIZADO** el inicio del **Sprint 3.2 — Ingestion Domain Core Implementation**.
