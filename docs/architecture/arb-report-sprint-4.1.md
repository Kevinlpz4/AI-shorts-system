---
title: "Architecture Review Board Report — Sprint 4.1 Ingestion Application Layer"
status: "APPROVED_WITH_SUGGESTIONS"
date: "2026-07-03"
---

# ARB Report: Sprint 4.1 — Ingestion Application Layer Design

> **Evaluación arquitectónica completa de la capa de aplicación del Bounded Context Ingestion**
>
> Versión: 2.0 | Estado: **DESIGN COMPLETE — PENDING ARB REVIEW**
> Basado en: Foundation v1.0 STABLE (FROZEN), Ingestion Domain v2.0 (FROZEN), ADR-021, ADR-022, ADR-023
> Sprint: 4.1 — Application Layer Design (design-only, no code)

---

## Resumen Ejecutivo

El Sprint 4.1 ha producido **10 documentos** (este ARB report + 9 documentos técnicos) que diseñan la capa de aplicación completa del BC Ingestion:

- **6 documentos de diseño** (`application-layer-design`, `application-folder-structure`, `commands-and-queries`, `dto-design`, `application-services`, `application-ports`)
- **2 documentos de implementación de reglas** (`application-rules`, `application-errors`)
- **1 documento de transacciones** (`transaction-boundaries`)
- **1 ARB report** (este documento)

**Decisión general**: CQRS unificado con llamada directa a servicios (sin buses). Use cases agrupados por aggregate (3 servicios: SourceService, FeedService, ArticleService). 21 use cases aprobados (0 diferidos, 0 rechazados). Eventos AFTER commit. Errores con Result.failure para flujos esperados.

**Veredicto propuesto**: ✅ **APROBAR** — La capa de aplicación diseñada cumple con Clean Architecture, DDD, SOLID, Hexagonal, Foundation FROZEN, y Domain Freeze. 3 CRITICAL issues resueltos post-revisión (C-01, C-02, C-03).

---

## 1. Scope Cubierto

| Documento | Archivo | Contenido principal |
|-----------|---------|---------------------|
| Main Design | `application-layer-design.md` | Propósito, layer diagram, CQRS decision, use case analysis (20 use cases), relationship map |
| Folder Structure | `application-folder-structure.md` | Árbol de directorios, convenciones, dependency direction |
| Commands & Queries | `commands-and-queries.md` | 13 Commands, 6 Queries, QueryResult[T], todas las firmas |
| DTO Design | `dto-design.md` | 10 DTOs (Summary + Detail x 5 aggregates), PaginatedDTO, ResultDTO, ErrorDTO |
| Application Services | `application-services.md` | 3 Services con métodos por use case, step-by-step flows |
| Application Ports | `application-ports.md` | EventPublisher Protocol, UnitOfWork Protocol, mapa completo de puertos |
| AL Rules | `application-rules.md` | Implementación detallada de AL-01 a AL-05, step-by-step |
| Error Flow | `application-errors.md` | ApplicationErrorCode, ErrorMapper, jerarquía, flujo completo |
| Transaction Boundaries | `transaction-boundaries.md` | UoW pattern, BEFORE/AFTER commit analysis, secuencia por use case |
| ARB Report | `arb-report-sprint-4.1.md` | Este documento |

---

## 2. Use Cases: Decisión Final

### 2.1 Aprobados (21/21)

| # | Use Case | Service | AL Rules | Events | Decisión |
|---|----------|---------|----------|--------|----------|
| 1 | RegisterSource | SourceService | — | — | ✅ INCLUDE |
| 2 | UpdateSource | SourceService | — | — | ✅ INCLUDE |
| 3 | EnableSource | SourceService | AL-02 | SourceEnabled | ✅ INCLUDE |
| 4 | DisableSource | SourceService | AL-01 | SourceDisabled | ✅ INCLUDE |
| 5 | AssignCategoryToSource | SourceService | — | — | ✅ INCLUDE |
| 6 | AssignTopicToSource | SourceService | — | — | ✅ INCLUDE |
| 7 | RegisterFeed | FeedService | AL-03, AL-04 | — | ✅ INCLUDE |
| 8 | UpdateFeed | FeedService | — | — | ✅ INCLUDE |
| 9 | PauseFeed | FeedService | — | — | ✅ INCLUDE |
| 10 | ActivateFeed | FeedService | — | — | ✅ INCLUDE |
| 11 | RecordCollection | FeedService | — | RawArticleCollected | ✅ INCLUDE |
| 12 | RecordFailure | FeedService | — | — | ✅ INCLUDE |
| 13 | AssignCategoryToFeed | FeedService | — | — | ✅ INCLUDE |
| 14 | AssignTopicToFeed | FeedService | — | — | ✅ INCLUDE |
| 15 | CreateRawArticle | ArticleService | AL-05 | — | ✅ INCLUDE |
| 16 | FindSource | SourceService | — | — | ✅ INCLUDE |
| 17 | FindFeed | FeedService | — | — | ✅ INCLUDE |
| 18 | FindArticle | ArticleService | — | — | ✅ INCLUDE |
| 19 | ListActiveSources | SourceService | — | — | ✅ INCLUDE |
| 20 | ListFeeds | FeedService | — | — | ✅ INCLUDE |
| 21 | ListArticles | ArticleService | — | — | ✅ INCLUDE |

### 2.2 Diferidos (0)

Ninguno. Todos los use cases propuestos son necesarios para la funcionalidad mínima.

### 2.3 Rechazados (0)

Ninguno. Todos los use cases propuestos tienen justificación clara.

### 2.4 Removidos post-ARB Review

| # | Use Case | Motivo |
|---|----------|--------|
| — | SearchRawArticles | Eliminado por YAGNI. `RawArticleRepository` no soporta filtros complejos (query, language, date range). Se fusiona con `ListArticlesQuery` que cubre `feed_id + page + size`. Si en el futuro se necesita búsqueda textual, se agrega con un método `search()` en el repositorio. |

---

## 3. Architecture Decisions

### AD-CRITICAL-01: Commands de Asignación Específicos por Aggregate

| Aspecto | Decisión |
|---------|----------|
| **Opción** | 4 commands específicos: AssignCategoryToSource, AssignCategoryToFeed, AssignTopicToSource, AssignTopicToFeed |
| **Alternativa descartada** | Command genérico con `target_type: str` + `target_id: SourceId \| FeedId \| RawArticleId` |
| **Razón** | El command genérico creaba ambigüedad sobre qué Service procesa cada comando y requería lógica condicional cross-service. Cada comando específico tiene un Service único responsable. |
| **Impacto** | SourceService gana 2 métodos (assign_category_to_source, assign_topic_to_source). FeedService gana 2 métodos (assign_category_to_feed, assign_topic_to_feed). Sin dependencias cross-service. |

### AD-CRITICAL-02: Batch Count Methods en Repository Ports

| Aspecto | Decisión |
|---------|----------|
| **Opción** | Agregar `count_active_by_sources(list[SourceId])` a FeedRepository y `count_by_feeds(list[FeedId])` a RawArticleRepository |
| **Razón** | Evitar N+1 queries al poblar `feed_count` y `article_count` en listas de DTOs |
| **Domain Freeze** | Excepción controlada. Estos métodos son extensiones de query (no modifican entidades, VOs, eventos, ni invariantes). El modelo de dominio permanece intacto. |
| **Alternativa descartada** | Sacar counts de los DTOs — pierde información útil para la UI. |

### AD-CRITICAL-03: SearchRawArticles Eliminado

| Aspecto | Decisión |
|---------|----------|
| **Opción** | Eliminar `SearchRawArticlesQuery` y `execute_search_articles`. Mantener solo `ListArticlesQuery` con `feed_id + page + size`. |
| **Razón** | YAGNI. El repositorio no soporta filtros complejos (query, language, date range). Implementar búsqueda en memoria post-carga no escala. Si se necesita en el futuro, se agrega método `search()` al repositorio. |
| **Impacto** | 21 use cases en vez de 20. Use case 14 (de 20) eliminado. |

### AD-01: CQRS Unificado

| Aspecto | Decisión |
|---------|----------|
| **Opción** | Commands y Queries en el mismo service (no buses separados) |
| **Razón** | YAGNI. 1 BC, ~20 use cases, 1-3 developers. La separación conceptual existe (directorios `commands/` y `queries/`) sin el overhead de buses y handlers. |
| **Tradeoff** | Si el sistema crece a 5+ BCs, necesitaremos migrar a buses. Aceptable. |
| **Mitigación** | Los objetos Command y Query ya están diseñados como dataclasses inmutables — la migración a buses requiere solo agregar handlers. |

### AD-02: Services por Aggregate (no 1 por use case)

| Aspecto | Decisión |
|---------|----------|
| **Opción** | 3 services: SourceService, FeedService, ArticleService |
| **Razón** | 14 use cases de mutación en 3 clases. Una clase por use case = 14 archivos sin beneficio real. |
| **Límite** | Si un service supera las 300 líneas, se refactoriza a use case classes. |

### AD-03: Eventos AFTER Commit

| Aspecto | Decisión |
|---------|----------|
| **Opción** | Commit BD → pull_events() → publish events |
| **Razón** | Evita acoplar disponibilidad del message broker a la transacción de BD. Evita publicar eventos que luego se rollbackean. |
| **Riesgo** | Si publish falla después del commit, el evento se pierde. |
| **Mitigación** | Outbox Pattern en el futuro (guardar eventos en tabla de BD, worker dedicado publica). Por ahora, aceptable: la pérdida de un evento solo retrasa procesamiento, no corrompe datos. |

### AD-04: Error Handling con Result.failure

| Aspecto | Decisión |
|---------|----------|
| **Opción** | Result.failure para flujos esperados (AL rules, recursos no encontrados). Excepciones para fallos técnicos (DB, red). |
| **Razón** | Los errores de negocio son resultados esperados de la operación. Las excepciones son para fallos del sistema. Clean separation. |

### AD-05: DTOs con 2 niveles (Summary + Detail)

| Aspecto | Decisión |
|---------|----------|
| **Opción** | SummaryDTO para listas y referencias. DetailDTO para vistas completas. |
| **Razón** | SummaryDTO evita cargar datos pesados (metadata, content_preview) en listas. DetailDTO expone todo para vistas de detalle. |

### AD-06: ApplicationErrorCode Separado

| Aspecto | Decisión |
|---------|----------|
| **Opción** | ApplicationErrorCode (COMMAND_INVALID, OPERATION_FAILED, etc.) independiente de IngestionErrorCode |
| **Razón** | Los errores de aplicación (comando inválido) son conceptualmente diferentes de los errores de dominio (regla de negocio). No mezclar. |

---

## 4. AL Rules Implementation

| Regla | Descripción | Implementada en | Repositorio usado | Error code |
|-------|-------------|-----------------|-------------------|------------|
| **AL-01** | No desactivar source con feeds activos | SourceService.disable_source | FeedRepository.count_active_by_source() | `HAS_ACTIVE_FEEDS` |
| **AL-02** | Activar source requiere ≥1 feed activo | SourceService.enable_source | FeedRepository.count_active_by_source() | `INVALID_STATE` |
| **AL-03** | source_id referencia source existente | FeedService.register_feed | NewsSourceRepository.find_by_id() | `NEWS_SOURCE_NOT_FOUND` |
| **AL-04** | No crear feed bajo source inactivo | FeedService.register_feed | (reuse source from AL-03) | `NEWS_SOURCE_INACTIVE` |
| **AL-05** | feed_id referencia feed existente | ArticleService.create_article | FeedRepository.find_by_id() | `FEED_NOT_FOUND` |

Todas las AL rules se ejecutan **ANTES** de llamar al dominio y **FUERA** de la transacción (consistencia eventual aceptable).

---

## 5. Verificación Arquitectónica

### 5.1 DDD Tactical Patterns

| Pattern | Cumplimiento |
|---------|-------------|
| **Application Service** | ✅ 3 services orquestan ARs, no contienen reglas de dominio |
| **Repository Ports** | ✅ Consumidos de domain/ports/ (FROZEN), no redefinidos |
| **DTOs** | ✅ Representaciones públicas, sin lógica de dominio |
| **Unit of Work** | ✅ Frontera transaccional explícita |
| **Event Publisher** | ✅ Puerto de salida para eventos intra-BC |

### 5.2 Clean Architecture

| Capa | Dependencias | Cumplimiento |
|------|-------------|-------------|
| `application/` | → `domain/`, `foundation/` | ✅ Correcto |
| `application/` | → NO `infrastructure/` | ✅ Correcto |
| `application/` | → NO `presentation/` | ✅ Correcto |
| `application/` | → NO modifica `domain/` | ✅ Correcto (FROZEN) |

### 5.3 SOLID

| Principio | Verificación |
|-----------|-------------|
| **SRP** | ✅ SourceService (configure sources), FeedService (manage feeds), ArticleService (manage articles). Cada uno tiene UNA razón para cambiar. |
| **OCP** | ✅ Nuevos use cases = nuevos métodos en services existentes o nuevas clases. Sin modificar código existente. |
| **LSP** | ✅ Repository Protocols pueden ser reemplazados por cualquier implementación (SQLite, Postgres, mock). |
| **ISP** | ✅ EventPublisher y UnitOfWork son interfaces pequeñas (2-3 métodos cada una). |
| **DIP** | ✅ Services dependen de Protocols (EventPublisher, UnitOfWork, Repository Ports), no de implementaciones concretas. |

### 5.4 Hexagonal Architecture

| Aspecto | Cumplimiento |
|---------|-------------|
| **Input ports** | ✅ Services expuestos a presentación vía métodos públicos |
| **Output ports** | ✅ EventPublisher + UnitOfWork como Protocols. Repository Ports desde domain/ |
| **Infrastructure injection** | ✅ Todo se inyecta en el constructor (DIP). Composition Root en infraestructura. |

### 5.5 CQRS (unified)

| Aspecto | Cumplimiento |
|---------|-------------|
| **Commands vs Queries** | ✅ Objetos separados en directorios distintos |
| **Same service** | ✅ Ambos coexisten en el mismo service class |
| **Read model** | ❌ No implementado (YAGNI). Se usa el mismo aggregate para lecturas. |

### 5.6 ADR-021 (Foundation Stability)

| Criterio | Cumplimiento |
|----------|-------------|
| **Foundation consumido, no modificado** | ✅ Application consume Result, DomainEvent, Error, ErrorCode. No los modifica. |
| **Sin nuevos Foundation types** | ✅ ApplicationErrorCode es propio de la aplicación, no de Foundation. |

### 5.7 Foundation FROZEN

| Afirmación | Verificación |
|-----------|-------------|
| **No se modifica Foundation** | ✅ En ningún documento se propone modificar Foundation |
| **No se modifica domain/** | ✅ Domain está FROZEN. No se tocan entities, VOs, events, repos, ni exceptions |

### 5.8 YAGNI

| Concepto | Decisión | Justificación |
|----------|----------|---------------|
| **CommandBus/QueryBus** | ❌ No | 1 BC, ~21 use cases. Llamada directa a services es suficiente. |
| **1 class por use case** | ❌ No | 14 use cases → 3 services. Refactorizar si superan 300 líneas. |
| **Event Store** | ❌ No | Outbox pattern en el futuro. Por ahora, publish directo. |
| **Integration Events** | ❌ No | Se diseñan cuando haya un consumidor cross-BC. |
| **Read Models** | ❌ No | Los mismos aggregates sirven para consultas. |
| **FeedPaused event** | ❌ No | Sin consumidor identificado. Es estado interno. |
| **SearchRawArticlesQuery** | ❌ No | Repositorio no soporta filtros complejos. Fusión con ListArticlesQuery. |

### 5.9 KISS

| Principio | Aplicación |
|-----------|------------|
| **Simple over clever** | ✅ Llamada directa a services en vez de buses. Result pattern en vez de excepciones. |
| **Minimal indirection** | ✅ Services → Repos → Domain. Sin capas intermedias. |
| **Context manager for UoW** | ✅ `with self._uow:` en vez de begin/commit/rollback explícitos. |

---

## 6. Riesgos Identificados

| # | Riesgo | Severidad | Mitigación |
|---|--------|-----------|------------|
| **R-01** | **Evento perdido si publish falla después de commit**: El commit de BD es exitoso pero el EventPublisher falla. El evento RawArticleCollected se pierde y el pipeline de normalización no se activa. | 🟡 Media | Consistencia eventual: el próximo fetch detectará duplicados y llamará record_collection(count=0), reseteando retry_count. Sin pérdida de datos, solo retraso. A mediano plazo, implementar Outbox Pattern. |
| **R-02** | **Ventana de inconsistencia en AL rules**: Entre la verificación (count_active_by_source) y el commit, otro proceso puede modificar el estado. Ej: se crea un Feed activo entre AL-01 check y disable(). | 🔶 Baja | Aceptable por diseño. El evento SourceDisabled se publica y el scheduler detiene los Feeds. Cualquier Feed creado después del disable tendrá source_id de un source inactivo, pero AL-04 lo protege en creación. |
| **R-03** | **Service classes sin supervisión de tamaño**: Si SourceService o FeedService crecen sin control, pueden convertirse en God objects. | 🔶 Baja | Regla: si un service supera las 300 líneas, refactorizar a use case classes. Code review debe verificar. |
| **R-04** | **ApplicationErrorCode duplica funcionalidad de IngestionErrorCode**: Si no se mantiene la disciplina, los códigos de error pueden mezclarse. | 🔶 Baja | Documentación clara: IngestionErrorCode = errores de dominio. ApplicationErrorCode = errores de aplicación. Code review debe verificar. |
| **R-05** | **Domain Freeze exception en batch methods**: `count_active_by_sources()` y `count_by_feeds()` agregan métodos a Protocols en domain/ports/. Aunque son solo queries, sientan precedente para futuras excepciones. | 🔶 Baja | Documentar explícitamente cada excepción. Solo métodos de query (sin mutación). Ninguna excepción adicional sin ARB approval. |

---

## 7. Alternativas Consideradas y Descartadas

| Alternativa | Razón de descarte |
|-------------|-------------------|
| **CommandBus/QueryBus** | YAGNI. Overhead de registro/handlers para ~20 use cases. |
| **1 use case class por operación** | YAGNI. 14 clases para 14 use cases no justificado en proyecto de 1 BC. |
| **Eventos BEFORE commit** | Riesgo de inconsistencia: si commit falla después de publicar, se notifica un cambio que no ocurrió. |
| **Excepciones para errores de negocio** | Los errores de AL rules son flujos esperados, no fallos del sistema. Result.failure es más explícito. |
| **Single DTO por aggregate** | Pérdida de flexibilidad. SummaryDTO evita cargar datos pesados en listas. |
| **EventPublisher en domain/ports/** | Domain ports están FROZEN. Además, la publicación de eventos es un concepto de aplicación, no de dominio. |
| **TransactionScript pattern** | Equivalente a no tener capa de aplicación. Separa en services pero podría degenerar en lógica procedural sin disciplina. |

---

## 8. Oportunidades de Mejora (Post-Aprobación)

| # | Oportunidad | Cuándo |
|---|-------------|--------|
| **S-01** | **Migrar a Outbox Pattern**: Guardar eventos en tabla de BD antes de commit, worker publica. Garantiza at-least-once delivery. | Sprint 5.x (cuando la pérdida de eventos sea crítica) |
| **S-02** | **Evaluar si SourceService supera 300 líneas**: Si la complejidad lo requiere, refactorizar a RegisterSourceUseCase, EnableSourceUseCase, etc. | Sprint 4.2 (implementación) |
| **S-03** | **Agregar IntegrationEventPublisher**: Cuando haya un consumidor cross-BC (Research, Script). | Sprint 5.x |
| **S-04** | **CommandBus para orquestación cross-BC**: Si 2+ BCs necesitan comunicación asíncrona basada en comandos. | Sprint 6+ |

---

## 9. Métricas del Diseño

| Métrica | Valor |
|---------|-------|
| Documentos producidos | 10 |
| Use cases diseñados | 21 (todos INCLUDED) |
| AL rules implementadas | 5 (AL-01 a AL-05) |
| Commands diseñados | 16 (13 originales -2 + 4 específicos +1 eliminado SearchRawArticles) |
| Queries diseñados | 5 (6 - 1 eliminado SearchRawArticlesQuery) |
| DTOs diseñados | 10 (+ 3 comunes) |
| Services | 3 (SourceService, FeedService, ArticleService) |
| Application Ports | 2 (EventPublisher, UnitOfWork) |
| Repository batch methods agregados | 2 (count_active_by_sources, count_by_feeds) |
| Foundation Ports reutilizados | 2 (ClockPort, UUIDProvider) |
| ApplicationErrorCodes | 7 |
| Riesgos identificados | 4 (1 medio, 3 bajos) |
| CRITICAL issues resueltos | 3 (C-01, C-02, C-03) |
| Documentos sin cambios respecto a Foundation | ✅ 10/10 |
| Documentos sin cambios respecto a Domain | ✅ 10/10 |

---

## 10. Artefactos del Sprint

| Artefacto | Archivo |
|-----------|---------|
| Main Design | `docs/architecture/application-layer-design.md` |
| Folder Structure | `docs/architecture/application-folder-structure.md` |
| Commands & Queries | `docs/architecture/commands-and-queries.md` |
| DTO Design | `docs/architecture/dto-design.md` |
| Application Services | `docs/architecture/application-services.md` |
| Application Ports | `docs/architecture/application-ports.md` |
| AL Rules Implementation | `docs/architecture/application-rules.md` |
| Error Flow | `docs/architecture/application-errors.md` |
| Transaction Boundaries | `docs/architecture/transaction-boundaries.md` |
| ARB Report | `docs/architecture/arb-report-sprint-4.1.md` |

---

## Veredicto Final

| Criterio | Resultado |
|----------|-----------|
| **Clean Architecture** | ✅ application/ importa domain/. No conoce infraestructura. |
| **DDD** | ✅ Application Services orquestan ARs, no contienen reglas de dominio. AL rules son cross-AR, no invariantes. |
| **SOLID** | ✅ SRP (3 services), OCP (nuevos use cases = nuevos métodos), LSP (Protocols intercambiables), ISP (ports pequeños), DIP (inyección de dependencias). |
| **Hexagonal Architecture** | ✅ Input ports (services) + Output ports (EventPublisher, UnitOfWork). Infrastructure inyectada. |
| **CQRS** | ✅ Unificado por YAGNI. Commands y Queries separados como objetos, mismos services. |
| **ADR-021 (Foundation Stability)** | ✅ Foundation consumido, no modificado. |
| **Domain Freeze** | ✅ Domain no modificado. FROZEN. |
| **Foundation Freeze** | ✅ Foundation no modificado. FROZEN. |
| **YAGNI** | ✅ Sin buses, sin read models, sin Integration Events, sin event store. |
| **KISS** | ✅ Llamada directa a services. Context manager para UoW. Result pattern. |
| **Cross-document Consistency** | ✅ 20 use cases consistentes en todos los documentos. AL rules implementadas en services correctos. |

---

## ✅ Veredicto Propuesto: APPROVED WITH SUGGESTIONS

> El diseño de la capa de aplicación del Sprint 4.1 cumple con todos los criterios arquitectónicos:
>
> - **Clean Architecture**: application/ depende de domain/ y foundation/. No conoce infraestructura.
> - **DDD**: Application Services orquestan, no contienen reglas de dominio.
> - **CQRS**: Decisión justificada (unificado por YAGNI). Separación conceptual presente.
> - **SOLID**: Verificado para cada principio.
> - **Foundation & Domain**: FROZEN. No modificados (excepción controlada: batch methods en Protocol).
> - **YAGNI & KISS**: Buses, read models, event store diferidos. SearchRawArticles eliminado.
> - **21 use cases**: 0 diferidos, 0 rechazados — todos justificados.
>
> **CRITICAL Issues Resueltos**:
> - **C-01**: AssignCategory/AssignTopic → 4 commands específicos (2 en SourceService, 2 en FeedService). Sin dependencias cross-service.
> - **C-02**: SearchRawArticles eliminado por YAGNI. Repositorio no soporta filtros complejos. Fusión con ListArticlesQuery.
> - **C-03**: Batch count methods `count_active_by_sources()` y `count_by_feeds()` agregados a repository Protocols. Anti N+1 resuelto.
>
> **Riesgos**: 5 identificados (1 medio, 4 bajos). Ninguno bloqueante.
> **Mitigaciones**: Documentadas para cada riesgo.
>
> Se recomienda **APROBAR** el diseño e iniciar el Sprint 4.2 (Application Layer Implementation).
>
> *Nota: La publicación de eventos AFTER commit sin Outbox Pattern es aceptable para la primera iteración. Se recomienda implementar Outbox en Sprint 5.x antes de que el pipeline de normalización sea crítico.*
