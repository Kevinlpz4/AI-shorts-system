# Application Layer Design — Ingestion Bounded Context

> **Documento principal de diseño de la capa de aplicación del BC Ingestion**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-03
> Basado en: Foundation v1.0 (FROZEN), Ingestion Domain v2.0 (FROZEN)
> Sprint: 4.1 — Application Layer Design

---

## 1. Propósito de la Application Layer

> **Orquestar operaciones cross-AR, coordinar repositorios, ejecutar AL rules, publicar eventos, manejar transacciones, y exponer use cases a la presentación.**

### Responsabilidades

| Responsabilidad | Descripción |
|----------------|-------------|
| **Orquestar ARs** | Coordinar operaciones que involucran múltiples Aggregate Roots (ej: crear Feed involucra verificar NewsSource) |
| **Ejecutar AL rules** | Implementar las 5 reglas cross-AR (AL-01 a AL-05) que no pueden estar en el dominio |
| **Manejar transacciones** | Definir fronteras transaccionales, commit/rollback |
| **Publicar eventos** | Recolectar Domain Events de los ARs y publicarlos via EventPublisher |
| **Mapear entities ↔ DTOs** | Convertir entidades de dominio a representaciones públicas (DTOs) y viceversa |
| **Manejar errores** | Capturar excepciones de dominio e infraestructura, traducir a Result.failure |
| **Exponer use cases** | Proveer una interfaz clara para la capa de presentación |

### Lo que NO hace

| No hace | ¿Por qué? |
|---------|-----------|
| **No contiene reglas de negocio** | Las reglas de negocio pertenecen al dominio (invariantes I-01 a I-23) |
| **No valida invariantes de dominio** | Esas las validan los VOs y Entities en su constructor |
| **No implementa persistencia** | La persiste la infraestructura a través de los ports |
| **No sabe de HTTP/CLI/API** | Esas son responsabilidades de la presentación |
| **No modifica el dominio** | Domain está FROZEN |

---

## 2. Diagrama de Capas (Hexagonal Architecture)

```
    ┌─────────────────────────────────────────────────────────────────────┐
    │                         PRESENTATION                                 │
    │              (FastAPI, CLI, WebSocket, Tests)                        │
    │              importa application/services/                           │
    │              recibe Result[DTO]                                      │
    └───────────────────────────┬─────────────────────────────────────────┘
                                │ llama use cases
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                     APPLICATION LAYER                                │  │
│  │                                                                      │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │  │
│  │  │  Commands/   │  │    DTOs      │  │   Mappers    │               │  │
│  │  │  Queries     │  │  (salida)    │  │ (entity↔DTO) │               │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │  │
│  │         │                 │                 │                        │  │
│  │         ▼                 ▼                 ▼                        │  │
│  │  ┌──────────────────────────────────────────────────────────────┐   │  │
│  │  │                    SERVICES                                    │   │  │
│  │  │  SourceService  │  FeedService  │  ArticleService              │   │  │
│  │  │  (orquesta)     │  (orquesta)   │  (orquesta)                  │   │  │
│  │  └──────────────────────────────────────────────────────────────┘   │  │
│  │         │                 │                 │                        │  │
│  │         ▼                 ▼                 ▼                        │  │
│  │  ┌──────────────────────────────────────────────────────────────┐   │  │
│  │  │               PORTS (Output)                                  │   │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │   │  │
│  │  │  │ EventPublisher│  │ UnitOfWork   │  │ Repository Ports │   │   │  │
│  │  │  │ (application) │  │ (application) │  │ (domain/ports/)  │   │   │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────┘   │   │  │
│  │  └──────────────────────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬───────────────────────────────────────┘
                                    │ implementa ports
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                       INFRASTRUCTURE                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  DB Adapters │  │ Event Bus    │  │ HTTP/RSS     │  │ Scheduler    │  │
│  │  (SQLite,    │  │ (Redis,      │  │ Clients      │  │ (APScheduler,│  │
│  │   Postgres)  │  │  RabbitMQ)   │  │ (aiohttp,    │  │  Celery)     │  │
│  │              │  │              │  │  feedparser) │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
```

### Flujo de Datos

```
Presentación → Command/Query → Service → Ports (repos) → Domain → Ports (repos) → DB
                                          → AL rules
                                          → UoW commit
                                          → EventPublisher
                     ← Result[DTO] ←
```

---

## 3. Decisión CQRS

### Análisis

| Criterio | Valor | Impacto en CQRS |
|----------|-------|-----------------|
| Tamaño del proyecto | 1 BC, ~14 use cases | Bajo |
| Equipo actual | 1-3 developers | Bajo |
| Separación de modelos | Commands y Queries usan los mismos aggregates | No justifica modelos separados |
| Escalabilidad de lecturas | Actualmente baja (<100k consultas/día) | No justifica read models |
| Complejidad operativa | 1 deploy, 1 BD | No justifica infraestructura separada |

### Decisión: **CQRS UNIFICADO (commands y queries en el mismo service)**

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| **✅ CQRS unificado** | Commands y Queries viven en el mismo service. Los métodos de query (`execute_find_source`) y command (`execute_disable_source`) coexisten en la misma clase. | **SELECCIONADO** |
| ❌ CQRS separado (CommandBus + QueryBus) | Requiere handlers separados, buses separados, posiblemente read models. Escalable pero caro en complejidad. | Descartado por YAGNI |
| ❌ Solo commands (sin queries) | Simplifica pero fuerza a la presentación a usar repositorios directamente | Descartado — viola Clean Architecture |

### Justificación

Para el tamaño actual del proyecto, tener un CommandBus y QueryBus separados añadiría ~5-10 archivos de infraestructura (handlers, buses, registros) sin beneficio real. Los use cases son pocos y bien definidos. La separación **conceptual** (Commands vs Queries como objetos) ya existe en los directorios `commands/` y `queries/` — eso es suficiente.

**Cuándo migrar a CQRS completo**:
- Cuando 2+ BCs necesiten consumir queries del Ingestion BC
- Cuando las lecturas requieran escalar independientemente
- Cuando el equipo supere 5 developers y necesite boundaries más estrictos

---

## 4. Use Case Analysis

### Metodología

Cada use case se evalúa con:

1. **Business value**: ¿Qué problema resuelve?
2. **YAGNI check**: ¿Lo necesitamos ahora o podemos diferirlo?
3. **AL rules**: ¿Qué reglas cross-AR debe verificar?
4. **Events**: ¿Qué Domain Events publica?
5. **Transaction boundary**: ¿Usa UoW?

---

### 4.1 Source Use Cases

#### ✓ INCLUDE: RegisterSource

| Aspecto | Evaluación |
|---------|-----------|
| **Business value** | Fundamental — sin un NewsSource no hay ingesta. Es el punto de entrada del sistema. |
| **YAGNI** | Necesario ahora. No hay ingesta sin sources. |
| **AL rules** | Ninguna directa. El dominio valida unicidad de nombre. |
| **Events** | Ninguno en creación (SourceCreated descartado por YAGNI). |
| **Transaction** | Sí |

#### ✓ INCLUDE: UpdateSource

| Aspecto | Evaluación |
|---------|-----------|
| **Business value** | Permite corregir configuración (URL, tipo) sin eliminar y recrear. |
| **YAGNI** | Necesario desde el inicio — la configuración inicial rara vez es perfecta. |
| **AL rules** | Ninguna |
| **Events** | Ninguno |
| **Transaction** | Sí |

#### ✓ INCLUDE: EnableSource

| Aspecto | Evaluación |
|---------|-----------|
| **Business value** | Reactivar fuente después de mantenimiento o corrección. |
| **YAGNI** | Necesario — es parte del ciclo de vida del source. |
| **AL rules** | **AL-02**: requiere al menos un Feed activo. |
| **Events** | `SourceEnabled` — notifica al scheduler que reanude Feeds. |
| **Transaction** | Sí |

#### ✓ INCLUDE: DisableSource

| Aspecto | Evaluación |
|---------|-----------|
| **Business value** | Detener ingesta de una fuente (por error, fin de acuerdo, etc.). |
| **YAGNI** | Necesario — es parte del ciclo de vida del source. |
| **AL rules** | **AL-01**: no si tiene Feeds activos. |
| **Events** | `SourceDisabled` — notifica al scheduler que detenga Feeds. |
| **Transaction** | Sí |

---

### 4.2 Category/Topic Use Cases

#### ✓ INCLUDE: AssignCategoryToSource / AssignCategoryToFeed

| Aspecto | Evaluación |
|---------|-----------|
| **Business value** | Clasificar sources y feeds para organización y búsqueda. |
| **YAGNI** | Necesario — la categorización es parte del dominio (atributo `categories: list[CategoryId]`). |
| **AL rules** | Verificar que la categoría existe (vía `CategoryRepository.find_by_id`). |
| **Decisión** | Commands específicos por aggregate (SourceService, FeedService) en vez de un comando genérico — elimina dependencia cross-service. |
| **Events** | Ninguno |
| **Transaction** | Sí |

#### ✓ INCLUDE: AssignTopicToSource / AssignTopicToFeed

| Aspecto | Evaluación |
|---------|-----------|
| **Business value** | Asociar temas de interés a sources/feeds. |
| **YAGNI** | Necesario — los topics son parte del diseño de dominio. |
| **AL rules** | Verificar que el topic existe (vía `TopicRepository.find_by_id`). |
| **Decisión** | Commands específicos por aggregate, mismo patrón que categorías. |
| **Events** | Ninguno |
| **Transaction** | Sí |

---

### 4.3 Feed Use Cases

#### ✓ INCLUDE: RegisterFeed

| Aspecto | Evaluación |
|---------|-----------|
| **Business value** | Crear un stream de contenido bajo un NewsSource. Sin feeds no hay fetch. |
| **YAGNI** | Necesario ahora. |
| **AL rules** | **AL-03**: source existe. **AL-04**: source activo. |
| **Events** | Ninguno |
| **Transaction** | Sí |

#### ✓ INCLUDE: UpdateFeed

| Aspecto | Evaluación |
|---------|-----------|
| **Business value** | Corregir configuración del feed (label, sync_policy). |
| **YAGNI** | Necesario — la configuración puede requerir ajustes. |
| **AL rules** | Ninguna |
| **Events** | Ninguno |
| **Transaction** | Sí |

#### ✓ INCLUDE: PauseFeed

| Aspecto | Evaluación |
|---------|-----------|
| **Business value** | Pausa manual para detener fetch temporalmente. |
| **YAGNI** | Necesario — el scheduler necesita pausar feeds por mantenimiento. |
| **AL rules** | Ninguna |
| **Events** | Ninguno (FeedPaused descartado por YAGNI) |
| **Transaction** | Sí |

#### ✓ INCLUDE: ActivateFeed

| Aspecto | Evaluación |
|---------|-----------|
| **Business value** | Reactivar feed pausado o inactivo. |
| **YAGNI** | Necesario — complemento de PauseFeed. |
| **AL rules** | Ninguna |
| **Events** | Ninguno |
| **Transaction** | Sí |

#### ✓ INCLUDE: RecordCollection

| Aspecto | Evaluación |
|---------|-----------|
| **Business value** | Registrar fetch exitoso, resetear retry_count, disparar pipeline. |
| **YAGNI** | Necesario — es el core del ciclo de fetch. |
| **AL rules** | Ninguna directa (el Feed existe, es el caller quien lo carga). |
| **Events** | `RawArticleCollected` — activa el pipeline de normalización. |
| **Transaction** | Sí |

#### ✓ INCLUDE: RecordFailure

| Aspecto | Evaluación |
|---------|-----------|
| **Business value** | Registrar fallo de fetch, incrementar retry_count, posible auto-pause. |
| **YAGNI** | Necesario — manejo de errores del scheduler. |
| **AL rules** | Ninguna (el dominio maneja auto-pause internamente). |
| **Events** | Ninguno |
| **Transaction** | Sí |

---

### 4.4 RawArticle Use Cases

#### ✓ INCLUDE: CreateRawArticle

| Aspecto | Evaluación |
|---------|-----------|
| **Business value** | Persistir un artículo crudo obtenido de un feed. |
| **YAGNI** | Necesario — es el output del fetch. |
| **AL rules** | **AL-05**: feed existe. |
| **Events** | Ninguno (el RawArticle es inmutable, no emite eventos). |
| **Transaction** | Sí |

---

### 4.5 Query Use Cases

#### ✓ INCLUDE: FindSource

| Business value | YAGNI | AL rules | Transaction |
|---------------|-------|----------|-------------|
| Obtener detalle de un source | Necesario | Ninguna | No |

#### ✓ INCLUDE: FindFeed

| Business value | YAGNI | AL rules | Transaction |
|---------------|-------|----------|-------------|
| Obtener detalle de un feed | Necesario | Ninguna | No |

#### ✓ INCLUDE: FindArticle

| Business value | YAGNI | AL rules | Transaction |
|---------------|-------|----------|-------------|
| Obtener detalle de un artículo | Necesario | Ninguna | No |

#### ✓ INCLUDE: ListActiveSources

| Business value | YAGNI | AL rules | Transaction |
|---------------|-------|----------|-------------|
| Listar sources activos (para scheduler, UI) | Necesario | Ninguna | No |

#### ✓ INCLUDE: ListFeeds

| Business value | YAGNI | AL rules | Transaction |
|---------------|-------|----------|-------------|
| Listar feeds de un source | Necesario | Ninguna | No |

#### ✓ INCLUDE: ListArticles

| Business value | YAGNI | AL rules | Transaction |
|---------------|-------|----------|-------------|
| Listar artículos de un feed (paginated) | Necesario | Ninguna | No |

---

### 4.6 Tabla de Decisión Final

| # | Use Case | Service | Decisión | Razón |
|---|----------|---------|----------|-------|
| 1 | RegisterSource | SourceService | ✅ INCLUDE | Esencial, punto de entrada |
| 2 | UpdateSource | SourceService | ✅ INCLUDE | Configuración dinámica |
| 3 | EnableSource | SourceService | ✅ INCLUDE | Ciclo de vida (AL-02) |
| 4 | DisableSource | SourceService | ✅ INCLUDE | Ciclo de vida (AL-01) |
| 5 | AssignCategoryToSource | SourceService | ✅ INCLUDE | Categorización de sources |
| 6 | AssignTopicToSource | SourceService | ✅ INCLUDE | Topics en sources |
| 7 | RegisterFeed | FeedService | ✅ INCLUDE | Esencial (AL-03, AL-04) |
| 8 | UpdateFeed | FeedService | ✅ INCLUDE | Configuración dinámica |
| 9 | PauseFeed | FeedService | ✅ INCLUDE | Control operativo |
| 10 | ActivateFeed | FeedService | ✅ INCLUDE | Ciclo de vida |
| 11 | RecordCollection | FeedService | ✅ INCLUDE | Core del fetch |
| 12 | RecordFailure | FeedService | ✅ INCLUDE | Manejo de errores |
| 13 | AssignCategoryToFeed | FeedService | ✅ INCLUDE | Categorización de feeds |
| 14 | AssignTopicToFeed | FeedService | ✅ INCLUDE | Topics en feeds |
| 15 | CreateRawArticle | ArticleService | ✅ INCLUDE | Core del fetch (AL-05) |
| 16 | FindSource | SourceService | ✅ INCLUDE | Consulta básica |
| 17 | FindFeed | FeedService | ✅ INCLUDE | Consulta básica |
| 18 | FindArticle | ArticleService | ✅ INCLUDE | Consulta básica |
| 19 | ListActiveSources | SourceService | ✅ INCLUDE | Consulta básica |
| 20 | ListFeeds | FeedService | ✅ INCLUDE | Consulta básica |
| 21 | ListArticles | ArticleService | ✅ INCLUDE | Consulta básica |

**Ningún use case fue DEFERIDO o RECHAZADO**. SearchRawArticles fue eliminado post-ARB Review por YAGNI — el repositorio no soporta filtros complejos y no se justifica implementar búsqueda en memoria. Todos los use cases propuestos son necesarios para la funcionalidad mínima del sistema. Esto es esperable — el dominio ya fue diseñado con YAGNI estricto, por lo que los use cases que emergen del dominio son los mínimos necesarios.

---

## 5. Relationship Between Layers

```
┌────────────────────────────────────────────────────────────────────┐
│ PRESENTATION:                                                      │
│   command = RegisterSourceCommand(name="Reddit", ...)              │
│   result = source_service.execute_register_source(command)         │
│   if result.is_success: return JSON(result.value)                  │
│   if result.is_failure: return error(result.error)                │
└──────────────────────────┬─────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────────┐
│ APPLICATION:                                                        │
│   SourceService.execute_register_source(cmd):                       │
│     1. source_repo.exists_by_name(cmd.name) → ok                   │
│     2. source = NewsSource(name=cmd.name, ...)                      │
│     3. source_repo.save(source)                      ← Domain Port │
│     4. uow.commit()                                 ← App Port     │
│     5. return Result.success(dto)                                   │
└──────────────────────────┬─────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────────┐
│ INFRASTRUCTURE:                                                     │
│   class SQLiteNewsSourceRepository(NewsSourceRepository):           │
│     def save(self, source): conn.execute("INSERT INTO ...")        │
│                                                                     │
│   class SQLLiteUnitOfWork(UnitOfWork):                              │
│     def commit(self): conn.commit()                                 │
└────────────────────────────────────────────────────────────────────┘
```

---

## 6. Resumen de Decisiones Arquitectónicas

| Decisión | Opción seleccionada | Alternativa descartada |
|----------|--------------------|-----------------------|
| **CQRS** | Unificado (commands + queries en mismo service) | Separado (bus) por YAGNI |
| **Use Case pattern** | 1 service class por aggregate | 1 use case class por operación |
| **Command/Query objects** | Dataclasses frozen inmutables | Objetos con validación |
| **DTOs** | 2 niveles: Summary + Detail | Single DTO (pierde flexibilidad) |
| **Mappers** | Clases estáticas separadas | Métodos en DTOs o entities |
| **Event publishing** | AFTER commit | Before commit (riesgo) |
| **Error handling** | Result.failure para flujos esperados | Excepciones everywhere |
| **Transaction** | UnitOfWork con context manager | Transacciones explícitas begin/commit |
| **Input ports** | Llamada directa a services | CommandBus/QueryBus |
| **Output ports** | EventPublisher + UnitOfWork (Protocols) | Acoplamiento directo a infraestructura |
