# Ingestion Domain — Domain Design Document v2.0

> **Documento oficial de diseño del dominio del Bounded Context Ingestion**
>
> Versión: 2.0 | Estado: **DESIGNED**
> Fecha: 2026-07-03
> Basado en: Foundation v1.0 STABLE (FROZEN), ADR-021, ADR-022
> Reemplaza: ingestion-domain-design.md v1.0-draft
>
> **Este documento especifica el diseño del dominio. NO implementa.**
> Sprint 3.1 es **design-only**. Ningún código será escrito hasta aprobación del ARB.

---

## Tabla de Contenidos

1. [Propósito del Bounded Context](#1-propósito-del-bounded-context)
2. [Entidades](#2-entidades)
3. [Value Objects](#3-value-objects)
4. [Aggregates](#4-aggregates)
5. [Domain Events](#5-domain-events)
6. [Repository Ports](#6-repository-ports)
7. [Invariantes Completas](#7-invariantes-completas)
8. [Decisiones de Diseño](#8-decisiones-de-diseño)
9. [Arquitectura y Cumplimiento](#9-arquitectura-y-cumplimiento)
10. [Estructura de Archivos](#10-estructura-de-archivos)
11. [Mapa de Puertos y Relaciones](#11-mapa-de-puertos-y-relaciones)

---

## 1. Propósito del Bounded Context

### 1.1 Responsabilidad Fundamental

> **Obtener información desde fuentes externas, normalizarla y publicarla para consumo de otros Bounded Contexts.**

El Ingestion BC es la puerta de entrada de información al sistema. Su responsabilidad comienza cuando una fuente externa es descubierta o configurada, y termina cuando los datos normalizados están disponibles para que otros BCs los consuman.

### 1.2 Límites del Contexto

```
                    ┌──────────────────────────────────────┐
                    │         SISTEMA EXTERIOR             │
                    │  (Plataformas externas de contenido)  │
                    └──────────────┬───────────────────────┘
                                   │ HTTP, RSS, WebSocket
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                     INGESTION BC                                   │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐    │
│  │  Configurar   │  │   Fetch +    │  │   Normalización +    │    │
│  │  Fuentes/     │─▶│   Parsear    │─▶│   Publicación        │    │
│  │  Feeds        │  │              │  │                      │    │
│  └──────────────┘  └──────────────┘  └───────────┬──────────┘    │
│                                                   │              │
│              ┌────────────────────────────────────┘              │
│              ▼                                                     │
│        Integration Event: NewRawItemsAvailable                    │
└──────────────────────────────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │      RESEARCH BC      │
              │  (Topic Discovery,    │
              │   Scoring, Approval)   │
              └──────────────────────┘
```

### 1.3 Qué Pertenece al BC

| Área | Incluye |
|------|---------|
| **Configuración** | Definir fuentes externas (NewsSource) y sus streams (Feed) |
| **Adquisición** | Ejecutar fetch de feeds vía PULL, procesar webhooks PUSH, manejar streams STREAM |
| **Parseo** | Transformar respuestas crudas en artículos estructurados (RawArticle) |
| **Normalización** | Limpiar, sanitizar, deduplicar y enriquecer artículos |
| **Publicación** | Emitir eventos de integración para consumo de otros BCs |
| **Monitoreo** | Tracking de ejecuciones, reintentos, estados de salud |
| **Categorización** | Clasificación temática de fuentes, feeds y artículos |

### 1.4 Qué NO Pertenece al BC

| Área | Excluido porque... | Va en |
|------|-------------------|-------|
| Scoring, clasificación semántica | Es análisis de contenido, no adquisición | Research BC |
| Aprobación/rechazo editorial | Es ciclo de vida editorial | Research BC |
| Generación de contenido | Es producción de guiones | Script BC |
| Usuarios, roles, autenticación | No hay usuarios en el dominio de ingesta | — |
| Conexión a bases de datos | Es infraestructura | Infraestructura del BC |
| Configuración de la app (.env, settings) | Es configuración de aplicación | Application Layer |
| Implementación de HTTP/RSS/WS | Son adapters tecnológicos | Infraestructura del BC |
| FeedGroup | Agrupación operativa sin reglas de negocio | Application/Infra |
| Domain Services (FeedOrchestrator) | Orquestación cross-AR | Application Layer |

### 1.5 Relación con los Demás BCs

| BC | Relación | Mecanismo |
|----|----------|-----------|
| **Research BC** | Ingestion provee artículos normalizados para su análisis | Integration Event: `NewRawItemsAvailable` |
| **Script BC** | Indirecta — Script consume de Research, no de Ingestion | — |
| **Shared / Foundation** | Ingestion referencia `Entity`, `AggregateRoot`, `ValueObject`, `DomainEvent`, `EntityId`, `Result`, `DomainError` | Herencia y composición |

**Principio**: Ingestion NO conoce la existencia de Research o Script. Solo publica eventos. Quien los consume es decisión de otros BCs.

---

## 2. Entidades

### 2.1 Identidades (IDs)

Todos los IDs del BC Ingestion heredan de `EntityId` (Foundation) pero **viven en el BC Ingestion** (ADR-021: multi-BC criterion — estos IDs solo los usa Ingestion).

| ID | Hereda de | Propósito |
|----|-----------|-----------|
| `SourceId` | `EntityId` | Identidad de NewsSource |
| `FeedId` | `EntityId` | Identidad de Feed |
| `RawArticleId` | `EntityId` | Identidad de RawArticle |
| `CategoryId` | `EntityId` | Identidad de Category |
| `TopicId` | `EntityId` | Identidad de Topic |

**Contrato de cada ID**:
- `from_string(value: str) -> Self` — construye desde representación string
- `generate() -> Self` — genera nuevo UUID
- `__str__() -> str` — representación string
- **Type-safety**: `SourceId(x) != FeedId(x)` aunque tengan el mismo UUID interno

---

### 2.2 NewsSource (Aggregate Root)

| Aspecto | Especificación |
|---------|---------------|
| **Responsabilidad** | Representar y configurar un origen externo de información (plataforma, sitio web, API). Es el punto de entrada para la configuración de ingesta. |
| **Identidad** | `SourceId` — Identidad única, inmutable, type-safe |
| **Tipo** | Aggregate Root (hereda de `AggregateRoot` en Foundation) |
| **Ciclo de vida** | Creado → Activo (`is_active = True`) → Inactivo (`is_active = False`) |
| **Inmutabilidad** | Mutable — tiene métodos que cambian su estado |

**Atributos**:

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `id` | `SourceId` | Identidad única |
| `name` | `str` | Nombre único y legible (ej: "Reddit", "Steam News") |
| `source_type` | `SourceType` | Tipo de fuente (RSS, API, SOCIAL_MEDIA, NEWSLETTER) |
| `source_url` | `SourceUrl` | URL base de la fuente (validada por VO) |
| `is_active` | `bool` | Si está habilitada para ingesta |
| `categories` | `list[CategoryId]` | Categorías asignadas a esta fuente (M:N, referencias por ID) |
| `topics` | `list[TopicId]` | Topics de interés que cubre (M:N, referencias por ID) |

**Comportamiento**:

| Método | Descripción |
|--------|-------------|
| `enable() -> None` | Marca como activo. Emite `SourceEnabled` domain event. |
| `disable(reason: str) -> None` | Marca como inactivo con razón. Emite `SourceDisabled`. |
| `change_url(new_url: SourceUrl) -> None` | Actualiza la URL base (validada por SourceUrl VO). |
| `change_source_type(new_type: SourceType) -> None` | Cambia el tipo de fuente. |
| `assign_category(category_id: CategoryId) -> None` | Agrega una categoría a la fuente. |
| `remove_category(category_id: CategoryId) -> None` | Remueve una categoría de la fuente. |
| `assign_topic(topic_id: TopicId) -> None` | Agrega un topic a la fuente. |
| `remove_topic(topic_id: TopicId) -> None` | Remueve un topic de la fuente. |

**Invariantes**:

| # | Invariante | Explicación |
|---|-----------|-------------|
| I-01 | `name` MUST NOT be empty | Una fuente debe tener un nombre identificable |
| I-02 | `name` MUST be unique across all NewsSources | El nombre es el identificador semántico |
| I-03 | `source_type` MUST be a valid SourceType | El tipo debe ser un valor conocido del enum SourceType |
| I-04 | `source_url` MUST be a valid URL (validated by SourceUrl VO) | La URL base debe ser válida |

> **Nota**: Las reglas "no desactivar si tiene Feeds activos" y "requiere al menos un Feed activo" NO son invariantes de NewsSource. Cruzan la frontera del AR (requieren consultar FeedRepository). Se implementan como **reglas de orquestación en Application Layer**. Ver Sección 7.6.

**Eventos emitidos**:
- `SourceEnabled` — cuando `enable()` es llamado exitosamente
- `SourceDisabled` — cuando `disable(reason)` es llamado exitosamente

**Relaciones**:
- 1 NewsSource → N Feeds (1:N, Feeds referencian por `source_id`)
- 1 NewsSource → N Categories (M:N vía `list[CategoryId]`)
- 1 NewsSource → M Topics (M:N vía `list[TopicId]`)

**Repositorio**: `NewsSourceRepository`

**Justificación como AR**: NewsSource tiene ciclo de vida independiente (creado → activo → inactivo). Es el punto de entrada natural para la configuración. Múltiples Feeds referencian un solo NewsSource. Si no fuera AR, no tendría aggregate padre al cual pertenecer — ES la raíz.

---

### 2.3 Feed (Aggregate Root)

| Aspecto | Especificación |
|---------|---------------|
| **Responsabilidad** | Representar un stream específico y configurable de información dentro de un NewsSource. Es la unidad ejecutable de ingesta con reglas de reintentos, pausa automática y categorización. |
| **Identidad** | `FeedId` — Identidad única, inmutable, type-safe |
| **Tipo** | Aggregate Root (hereda de `AggregateRoot` en Foundation) |
| **Ciclo de vida** | Creado → Activo (fetch habilitado) → Pausado (por errores) → Inactivo (deshabilitado manualmente) |
| **Inmutabilidad** | Mutable — tiene ciclo de vida, estado de reintentos, categorías asignadas |

**Atributos**:

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `id` | `FeedId` | Identidad única |
| `source_id` | `SourceId` | Referencia al NewsSource padre (por ID, no por objeto) |
| `url` | `ArticleUrl` | URL del feed (endpoint de consulta, validada por VO) |
| `label` | `ArticleTitle` | Título o etiqueta legible (ej: "r/programming", "top-hn") |
| `language` | `Language` | Idioma del contenido del feed |
| `is_active` | `bool` | Si está habilitado para fetch |
| `sync_policy` | `SyncPolicy` | Política de sincronización (modo, intervalo, reintentos) |
| `categories` | `list[CategoryId]` | Categorías asignadas directamente al feed |
| `topics` | `list[TopicId]` | Topics de interés asociados |
| `retry_count` | `int` | Contador de fallos consecutivos actuales (se resetea a 0 en éxito) |

**Comportamiento**:

| Método | Descripción |
|--------|-------------|
| `record_collection(batch_id: UUID, count: int) -> None` | Registra un fetch exitoso. Resetea `retry_count` a 0. Emite `RawArticleCollected`. |
| `record_failure(error: str) -> FeedFailureResult` | Incrementa `retry_count`. Si `not can_retry()`, marca auto-pause. Retorna el resultado. |
| `can_retry() -> bool` | Retorna `True` si `retry_count < max_retries` (de sync_policy). |
| `pause(reason: str) -> None` | Marca `is_active = False`. Requiere reactivación manual. |
| `activate() -> None` | Marca `is_active = True`, resetea `retry_count` a 0. |
| `assign_category(category_id: CategoryId) -> None` | Agrega una categoría. No valida existencia (consistencia eventual). |
| `remove_category(category_id: CategoryId) -> None` | Remueve una categoría. |
| `assign_topic(topic_id: TopicId) -> None` | Agrega un topic. |
| `remove_topic(topic_id: TopicId) -> None` | Remueve un topic. |
| `update_sync_policy(policy: SyncPolicy) -> None` | Actualiza la política de sincronización. |

**Invariantes**:

| # | Invariante | Explicación |
|---|-----------|-------------|
| I-05 | `url` MUST NOT be empty | Un feed siempre tiene una URL |
| I-06 | `url` MUST be unique within the parent NewsSource | No dos feeds con la misma URL en el mismo source |
| I-07 | `retry_count` MUST be 0 after successful collection | Los reintentos son consecutivos |
| I-08 | MUST pause if `retry_count >= max_retries` and fetch fails | Protege contra consumo infinito de recursos |
| I-09 | MUST NOT fetch while paused | Feed pausado requiere reactivación manual |
| I-10 | MUST NOT fetch if `is_active = False` | Feed desactivado no ejecuta fetch |

> **Cross-AR**: Las reglas "source_id referencia existente" y "no crear bajo NewsSource inactivo" son reglas de Application Layer (AL-03, AL-04). Ver Sección 7.6.

**Eventos emitidos**:
- `RawArticleCollected` — cuando `record_collection()` es llamado con count > 0

**Relaciones**:
- N Feeds → 1 NewsSource (N:1, referenciado por `source_id`)
- 1 Feed → N Categories (M:N vía `list[CategoryId]`)
- 1 Feed → M Topics (M:N vía `list[TopicId]`)
- 1 Feed → N RawArticles (1:N, RawArticles referencian por `feed_id`)
- 1 Feed → 1 SyncPolicy (1:1, composición vía VO)

**Repositorio**: `FeedRepository`

**Justificación como AR**: Feed tiene ciclo de vida propio (activo → pausado → inactivo), estado independiente (retry_count, sync_policy), y reglas de negocio (auto-pause, categorización). Es la unidad de ejecución referenciada por schedulers. Cargar NewsSource con todos sus Feeds sería inviable — cada Feed es modificado independientemente por operaciones de fetch. Las reglas de reintentos, pausa automática y categorización son lógica de dominio, no infraestructura.

---

### 2.4 RawArticle (Aggregate Root) — INMUTABLE

| Aspecto | Especificación |
|---------|---------------|
| **Responsabilidad** | Almacenar de forma inmutable una pieza de contenido crudo obtenido de un Feed. Es un registro de auditoría — una vez creado, nunca cambia. |
| **Identidad** | `RawArticleId` — Identidad única, inmutable, type-safe |
| **Tipo** | Aggregate Root (frontera de consistencia por volumen). Técnicamente hereda de `Entity` (no de `AggregateRoot`) por ser inmutable y no emitir eventos. Ver ADR-023. |
| **Ciclo de vida** | Creado (inmutable después de creación). No tiene cambios de estado. |
| **Inmutabilidad** | **TOTALMENTE INMUTABLE** — No tiene setters. No tiene métodos que modifiquen estado. Todos los atributos se asignan en el constructor. |

**Atributos**:

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `id` | `RawArticleId` | Identidad única |
| `feed_id` | `FeedId` | Feed del que se obtuvo (por ID) |
| `external_id` | `str` | ID único en el sistema externo (ej: ID del post en Reddit) |
| `content_hash` | `str` | SHA-256 del contenido (64 caracteres hex, para deduplicación) |
| `title` | `ArticleTitle` | Título del artículo (validado por VO) |
| `url` | `ArticleUrl` | URL canónica del artículo original (validado por VO) |
| `author` | `str \| None` | Autor o creador (primitivo, opcional) |
| `language` | `Language \| None` | Código ISO 639-1 del idioma (opcional, puede ser None hasta detectarse) |
| `published_at` | `datetime \| None` | Fecha de publicación original (opcional) |
| `fetched_at` | `datetime` | Momento en que se obtuvo el artículo |
| `content_preview` | `str \| None` | Extracto o resumen corto del contenido (atributo plano, NO es VO) |
| `metadata` | `dict` | Datos adicionales específicos del proveedor (atributo plano, NO es VO) |

**Comportamiento**:

| Método | Descripción |
|--------|-------------|
| Constructor | Todos los atributos requeridos se proveen en creación. Validación de invariantes en el constructor. |
| `article_url` (property) | Accede al VO ArticleUrl encapsulado. |
| `article_title` (property) | Accede al VO ArticleTitle encapsulado. |

NO tiene métodos de mutación. NO emite eventos de dominio.

**Invariantes**:

| # | Invariante | Explicación |
|---|-----------|-------------|
| I-11 | **IMMUTABLE** — No modification after creation | Es un registro de auditoría. No se modifica ni actualiza ni elimina. |
| I-12 | `external_id + feed_id` MUST be unique | Deduplicación por ID externo dentro del Feed |
| I-13 | `content_hash` MUST be unique within the same Feed | Deduplicación por contenido |
| I-14 | `fetched_at` >= `published_at` (if published_at present) | No se puede obtener antes de su publicación |
| I-15 | `title` MUST NOT be empty (validated by ArticleTitle VO) | Un artículo siempre tiene título |
| I-16 | `url` MUST be a valid URL (validated by ArticleUrl VO) | La URL del artículo debe ser válida |
| I-17 | `content_hash` MUST be a valid SHA-256 (64 hex chars) | El hash debe tener formato correcto |

> **Cross-AR**: La regla "feed_id referencia un Feed existente" es regla de Application Layer (AL-05). Ver Sección 7.6.

**Relaciones**:
- N RawArticles → 1 Feed (N:1, referenciado por `feed_id`)
- N RawArticles → M Topics (M:N futura, vía referencias de TopicId)

**Repositorio**: `RawArticleRepository`

**Justificación como AR (volumen + inmutabilidad)**:
RawArticle es AR por **razones de volumen**. Pueden existir millones de instancias. Si RawArticle fuera una entidad hija dentro de Feed, cargar un Feed cargaría TODOS sus RawArticles — arquitectónicamente inviable. Cada RawArticle debe ser cargable y persistible independientemente.

La **inmutabilidad** simplifica la consistencia: una vez creado, no se requieren locks, ni actualizaciones, ni control de concurrencia. La frontera del AR protege las invariantes de creación.

**Nota técnica**: RawArticle hereda de `Entity` (no de `AggregateRoot` de Foundation) porque es inmutable y no emite eventos. No necesita `_events` ni `register_event()`. Se documenta como AR por convención. Ver ADR-023 para la decisión completa.

---

### 2.5 Category (Entity)

| Aspecto | Especificación |
|---------|---------------|
| **Responsabilidad** | Clasificación temática con jerarquía opcional. Organiza contenido (NewsSources, Feeds, RawArticles) por tema. |
| **Identidad** | `CategoryId` — Identidad única, inmutable, type-safe |
| **Tipo** | Entity (hereda de `Entity` en Foundation). NO es Aggregate Root. |
| **Ciclo de vida** | Creada → Activa → Inactiva |
| **Inmutabilidad** | Mutable — tiene métodos de cambio de estado |

**Atributos**:

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `id` | `CategoryId` | Identidad única |
| `name` | `CategoryName` | Nombre legible (ej: "Technology"), validado por VO |
| `slug` | `str` | Slug URL-friendly, único globalmente (ej: "technology") |
| `parent_id` | `CategoryId \| None` | Referencia opcional a categoría padre (para jerarquía) |
| `is_active` | `bool` | Si está habilitada |

**Comportamiento**:

| Método | Descripción |
|--------|-------------|
| `activate() -> None` | Marca como activa |
| `deactivate() -> None` | Marca como inactiva. Si tiene subcategorías activas, DEBE cascadear el estado. |
| `change_parent(new_parent: CategoryId \| None) -> None` | Cambia la categoría padre. Valida: no auto-referencia, no ciclos. |

**Invariantes**:

| # | Invariante | Explicación |
|---|-----------|-------------|
| I-23 | `slug` MUST be unique across all categories | No dos categorías con el mismo slug |
| I-24 | `parent_id` MUST NOT equal `id` (no self-parent) | Una categoría no puede ser padre de sí misma |
| I-25 | Hierarchy MUST NOT contain cycles | No puede haber A→B→C→A |
| I-26 | Deactivating a category with active subcategories MUST cascade | Desactivar categoría padre desactiva subcategorías |

**Relaciones**:
- 1 Category → 0..N subcategorías (a través de `parent_id`, jerarquía)
- N NewsSources → N Categories (M:N vía `list[CategoryId]`)
- N Feeds → N Categories (M:N vía `list[CategoryId]`)

**Repositorio**: `CategoryRepository`

**Justificación como Entity (no AR)**: Category tiene identidad y ciclo de vida pero no tiene entidades dependientes que requieran consistencia transaccional. Es referenciada por ID desde múltiples agregados (NewsSource, Feed). Su frontera de consistencia es eventual — las categorías se crean independientemente de sus referenciadores. No justifica ser Aggregate Root.

---

### 2.6 Topic (Entity)

| Aspecto | Especificación |
|---------|---------------|
| **Responsabilidad** | Representar un tema o tópico de interés que guía la ingesta. Los artículos y fuentes pueden asociarse a topics (ej: "Artificial Intelligence", "Climate Change"). |
| **Identidad** | `TopicId` — Identidad única, inmutable, type-safe |
| **Tipo** | Entity (hereda de `Entity` en Foundation). NO es Aggregate Root. |
| **Ciclo de vida** | Creado → Activo → Inactivo |
| **Inmutabilidad** | Mutable — tiene métodos de cambio de estado |

**Atributos**:

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `id` | `TopicId` | Identidad única |
| `name` | `str` | Nombre del topic, único globalmente (ej: "Artificial Intelligence") |
| `description` | `str \| None` | Descripción opcional del topic |
| `is_active` | `bool` | Si está habilitado |

**Comportamiento**:

| Método | Descripción |
|--------|-------------|
| `rename(new_name: str) -> None` | Actualiza el nombre. Valida unicidad. |
| `update_description(desc: str \| None) -> None` | Actualiza la descripción. |
| `activate() -> None` | Marca como activo. |
| `deactivate() -> None` | Marca como inactivo. |

**Invariantes**:

| # | Invariante | Explicación |
|---|-----------|-------------|
| I-27 | `name` MUST NOT be empty | Un topic debe tener nombre |
| I-28 | `name` MUST be unique across all Topics | No dos topics con el mismo nombre |

**Relaciones**:
- N NewsSources → M Topics (M:N vía `list[TopicId]`)
- N Feeds → M Topics (M:N vía `list[TopicId]`)
- RawArticles → Topics (M:N futura, aún no implementada)

**Repositorio**: `TopicRepository`

**Justificación como Entity (no AR)**: Topic tiene identidad y es referenciable por ID desde NewsSource y Feed. No tiene ciclo de vida complejo, no tiene invariantes transaccionales fuertes, y no emite eventos. Hacerlo AR agregaría complejidad sin justificación. No es VO porque debe ser referenciable por ID (un VO sería copiado en cada RawArticle, haciendo imposible renombrar un topic centralizadamente).

---

## 3. Value Objects

Todos los Value Objects siguen: `@dataclass(frozen=True)` — inmutables con validación en `__post_init__`.

### 3.1 SourceUrl

| Aspecto | Especificación |
|---------|---------------|
| **Propósito** | Encapsular y validar la URL base de un NewsSource |
| **Inmutabilidad** | ✅ `@dataclass(frozen=True)` |
| **Atributos** | `value: str` |

**Validaciones** (`__post_init__`):
- No vacío
- Esquema http o https (rechazar ftp, file, etc.)
- Formato URL válido (puede usar `urllib.parse.urlparse`)
- Sin fragmentos (#) ni caracteres no permitidos
- Sin espacios ni caracteres de control

**Normalización**:
- `normalized() -> str`: retorna URL normalizada (scheme lowercase, sin trailing slash)

**Errores**:
- `INVALID_SOURCE_URL` si la validación falla

---

### 3.2 ArticleUrl

| Aspecto | Especificación |
|---------|---------------|
| **Propósito** | Encapsular y validar la URL canónica de un RawArticle |
| **Inmutabilidad** | ✅ `@dataclass(frozen=True)` |
| **Atributos** | `value: str` |

**Validaciones**:
- No vacío
- Esquema http o https
- Formato URL válido
- Sin espacios, sin caracteres de control

**Comportamiento**:
- `normalized() -> str`: retorna URL canónica normalizada
- `domain() -> str`: extrae el dominio (ej: "reddit.com")

**Errores**:
- `INVALID_ARTICLE_URL` si la validación falla

---

### 3.3 ArticleTitle

| Aspecto | Especificación |
|---------|---------------|
| **Propósito** | Encapsular y validar el título de un artículo |
| **Inmutabilidad** | ✅ `@dataclass(frozen=True)` |
| **Atributos** | `value: str` |

**Validaciones**:
- No vacío (trim previo)
- Longitud máxima: 500 caracteres
- Sin caracteres de control (excepto whitespace estándar)
- Trim automático de espacios leading/trailing
- Sanitización de caracteres de control

---

---

> **Author**: Eliminado como Value Object por YAGNI. `author` en RawArticle es `str | None` (atributo plano). No tiene comportamiento de dominio suficiente (solo valida max length y opcional). Si en el futuro requiere lógica de normalización o verificación, se reevalúa como VO.

### 3.5 Language

| Aspecto | Especificación |
|---------|---------------|
| **Propósito** | Representar un código de idioma ISO 639-1 |
| **Inmutabilidad** | ✅ `@dataclass(frozen=True)` |
| **Atributos** | `code: str` |

**Validaciones**:
- Código ISO 639-1 válido (2 letras)
- Lista de códigos permitidos: `en`, `es`, `fr`, `de`, `pt`, `it`, `ja`, `ko`, `zh`, `ru`, `ar`
- Normalización automática a lowercase

**Comportamiento**:
- `display_name() -> str`: nombre legible del idioma (opcional, para UI)
- `is_rtl() -> bool`: `True` si es idioma right-to-left (árabe, hebreo)

**Errores**:
- `INVALID_LANGUAGE` si el código no es válido

---

### 3.6 SourceType (Enum)

```python
class SourceType(str, Enum):
    RSS = "RSS"
    API = "API"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    NEWSLETTER = "NEWSLETTER"
```

**Responsabilidad**: Clasificar el tipo de fuente externa. Determina qué tecnología de fetch y parseo se usa.

**Nota**: SourceType es un enum unificado que reemplaza al par `provider_type` + `technology_type` del diseño v1.0-draft. Esto simplifica el modelo: un solo enum captura la categoría del proveedor sin necesidad de dos campos separados.

---

### 3.7 CategoryName

| Aspecto | Especificación |
|---------|---------------|
| **Propósito** | Encapsular y validar el nombre de una categoría |
| **Inmutabilidad** | ✅ `@dataclass(frozen=True)` |
| **Atributos** | `value: str` |

**Validaciones**:
- No vacío
- Longitud máxima: 100 caracteres
- Sin caracteres especiales (solo letras, espacios, números, guiones, guiones bajos)
- Trim automático de espacios leading/trailing

---

### 3.8 SyncPolicy (Value Object)

| Aspecto | Especificación |
|---------|---------------|
| **Propósito** | Configuración de sincronización para un Feed. Define modo, intervalo, reintentos y timeout. |
| **Inmutabilidad** | ✅ `@dataclass(frozen=True)` |
| **Nota** | NO incluye lógica de timing (`is_due`, `next_run`). Es un VO de configuración pura. El scheduler (Application Layer) decide cuándo ejecutar basado en estos datos. |

**Atributos**:

| Atributo | Tipo | Default | Descripción |
|----------|------|---------|-------------|
| `mode` | `SyncMode` | (requerido) | Modo de sincronización |
| `interval_minutes` | `int \| None` | `None` | Intervalo en minutos entre fetches (modo PULL) |
| `max_retries` | `int` | `3` | Máximo de reintentos antes de pausar el Feed |
| `backoff_multiplier` | `float` | `2.0` | Multiplicador para backoff exponencial |
| `max_backoff_minutes` | `int` | `60` | Backoff máximo en minutos |
| `timeout_seconds` | `int` | `30` | Timeout en segundos para cada fetch |
| `max_items_per_run` | `int` | `100` | Máximo de items a obtener por ejecución |

**Validaciones**:
- `mode PULL` requiere `interval_minutes` (no None)
- `mode PUSH` y `STREAM` no requieren intervalo
- `mode MANUAL` no requiere campos adicionales
- `max_retries` >= 0
- `timeout_seconds` > 0
- `max_items_per_run` > 0

#### SyncMode (Enum)

| Valor | Descripción |
|-------|-------------|
| `PULL` | El sistema consulta periódicamente al Source. Requiere `interval_minutes`. |
| `PUSH` | El Source notifica al sistema mediante webhook. |
| `STREAM` | Conexión persistente con el Source. |
| `MANUAL` | Solo se ejecuta bajo demanda explícita. |

---

## 4. Aggregates

### 4.1 Tabla de Aggregates

| Aggregate Root | ¿Por qué AR? | Frontera de Consistencia | Referencias entre ARs |
|----------------|-------------|--------------------------|----------------------|
| **NewsSource** | Ciclo de vida independiente. Punto de entrada de configuración. Múltiples Feeds lo referencian. | Inmediata dentro de NewsSource. Sus Feeds son consistencia eventual. | Por ID: `Feed.source_id` → `SourceId` |
| **Feed** | Ciclo de vida propio (activo/pausado/inactivo). Reglas de negocio (retry, auto-pause). Unidad de ejecución. | Inmediata dentro de Feed. Sus RawArticles son ARs separados. | Por ID: `RawArticle.feed_id` → `FeedId` |
| **RawArticle** | Volumen (millones de instancias). Inmutable, sin dependencias. | Inmediata en creación. No hay consistencia posterior (inmutable). | Por ID: `RawArticle.feed_id` → `FeedId` |

### 4.2 Entidades NO Aggregate Root

| Entity | ¿Por qué NO es AR? |
|--------|-------------------|
| **Category** | Tiene identidad y ciclo de vida, pero no tiene entidades dependientes que requieran consistencia transaccional. Es referenciada por ID. Su consistencia es eventual. |
| **Topic** | Tiene identidad pero no tiene vida compleja ni invariantes transaccionales. Es un concepto de referencia. No emite eventos. |

### 4.3 Fronteras de Consistencia

```
┌─────────────────────────────────────────────────────────────────┐
│                   FRONTERAS TRANSACCIONALES                      │
│                                                                  │
│  Cada Aggregate Root es una frontera de consistencia:            │
│  - NewsSource: consistencia inmediata dentro de NewsSource      │
│  - Feed: consistencia inmediata dentro de Feed                  │
│  - RawArticle: consistencia inmediata en creación (inmutable)   │
│                                                                  │
│  Entre aggregates: CONSISTENCIA EVENTUAL                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Ejemplo de fetch exitoso:                                      │
│  1. Application Service carga Feed (AR) — consistencia inmediata│
│  2. Ejecuta fetch externo, crea RawArticle (AR) — inmediata     │
│  3. Actualiza Feed.retry_count (AR) — inmediata                 │
│  4. Feed.record_collection() emite RawArticleCollected          │
│                                                                  │
│  Si el paso 3 falla después del paso 2:                         │
│  - RawArticle existe, Feed.retry_count no se reseteó            │
│  - El próximo fetch detectará duplicados por content_hash       │
│  - Esto es aceptable (consistencia eventual)                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Reglas de Consistencia entre Aggregates

| Regla | Tipo | Protección |
|-------|------|------------|
| Feed.source_id referencia un NewsSource que existe | Consistencia eventual | Se verifica en Application Service al crear Feed |
| RawArticle.feed_id referencia un Feed que existe | Consistencia eventual | Se verifica en Application Service |
| Category.parent_id referencia una Category que existe | Consistencia eventual | Se verifica en Application Service |
| Las listas de CategoryId/TopicId en NewsSource/Feed referencian entidades existentes | Consistencia eventual | Se verifica en Application Service |
| No hay dos Feeds con la misma URL en el mismo NewsSource | Consistencia inmediata | Se verifica en FeedRepository.exists_by_source_and_url() |

---

## 5. Domain Events

Todos los Domain Events heredan de `DomainEvent` (Foundation): `@dataclass(frozen=True)`, con `event_id: UUID`, `event_name: str`, `occurred_at: datetime`. Se registran vía `register_event()` en el AR y se recolectan vía `pull_events()`.

### 5.1 RawArticleCollected

| Aspecto | Especificación |
|---------|---------------|
| **Nombre** | `RawArticleCollected` |
| **Cuándo ocurre** | Cuando `Feed.record_collection()` es llamado exitosamente con count > 0 (después de deduplicación) |
| **Significado** | "Hay artículos crudos nuevos disponibles para normalizar". Dispara el pipeline de normalización. |
| **Payload** | `feed_id: FeedId`, `batch_id: UUID`, `count: int` (artículos nuevos), `collected_at: datetime` |
| **Publisher** | `Feed` (AR) vía `register_event()` |
| **Consumidor** | Application Service → Normalization Pipeline |
| **¿Por qué existe?** | Es el evento más importante del BC. Sin él, el pipeline de normalización no se activa. |

### 5.2 SourceEnabled

| Aspecto | Especificación |
|---------|---------------|
| **Nombre** | `SourceEnabled` |
| **Cuándo ocurre** | Cuando `NewsSource.enable()` es llamado exitosamente |
| **Significado** | "Un NewsSource se ha habilitado". Los schedulers deben reanudar la ingesta de sus Feeds. |
| **Payload** | `source_id: SourceId`, `enabled_at: datetime` |
| **Publisher** | `NewsSource` (AR) vía `register_event()` |
| **Consumidor** | Application Service → SchedulerDriver (reanuda polling de Feeds del source) |
| **¿Por qué existe?** | Permite que componentes externos reaccionen a la reactivación sin tener que pollear el estado. |

### 5.3 SourceDisabled

| Aspecto | Especificación |
|---------|---------------|
| **Nombre** | `SourceDisabled` |
| **Cuándo ocurre** | Cuando `NewsSource.disable(reason)` es llamado exitosamente |
| **Significado** | "Un NewsSource se ha deshabilitado". Toda ingesta debe detenerse inmediatamente. |
| **Payload** | `source_id: SourceId`, `reason: str`, `disabled_at: datetime` |
| **Publisher** | `NewsSource` (AR) vía `register_event()` |
| **Consumidor** | Application Service → SchedulerDriver (detiene polling), AlertService, Logger |
| **¿Por qué existe?** | Es crítico detener la ingesta. Sin este evento, los Feeds seguirían ejecutándose contra una fuente deshabilitada. |

### 5.4 Eventos Descartados (YAGNI)

| Evento | Razón de descarte |
|--------|-------------------|
| `SourceCreated` | Nadie lo consume dentro del BC. Se agrega cuando haya un consumidor real. |
| `CategoryCreated` | Misma razón. Las categorías son datos de referencia. |
| `FeedPaused` | Se maneja como estado interno de Feed + log. No requiere notificación cross-AR hasta que haya un consumidor. |

---

## 6. Repository Ports

Todos los repositorios son **Protocols** (interfaces). Definen el **contrato de persistencia** que el dominio necesita. NO mencionan SQL, Redis, archivos, ni ninguna tecnología concreta.

Cada Aggregate Root tiene su propio repositorio. Category y Topic (Entities, no ARs) también tienen repositorio porque necesitan ser persistidas independientemente.

### 6.1 NewsSourceRepository

```python
class NewsSourceRepository(Protocol):
    def save(self, source: NewsSource) -> None: ...
    def find_by_id(self, id: SourceId) -> Result[NewsSource]: ...
    def find_by_name(self, name: str) -> Result[NewsSource]: ...
    def find_all(self) -> list[NewsSource]: ...
    def find_active(self) -> list[NewsSource]: ...
    def exists_by_name(self, name: str) -> bool: ...
```

**Errores**:
- `find_by_id` → `NEWS_SOURCE_NOT_FOUND`
- `find_by_name` → `NEWS_SOURCE_NOT_FOUND`

### 6.2 FeedRepository

```python
class FeedRepository(Protocol):
    def save(self, feed: Feed) -> None: ...
    def find_by_id(self, id: FeedId) -> Result[Feed]: ...
    def find_by_source(self, source_id: SourceId) -> list[Feed]: ...
    def find_by_url(self, source_id: SourceId, url: ArticleUrl) -> Result[Feed]: ...
    def find_active_by_source(self, source_id: SourceId) -> list[Feed]: ...
    def exists_by_source_and_url(self, source_id: SourceId, url: ArticleUrl) -> bool: ...
    def count_active_by_source(self, source_id: SourceId) -> int: ...
```

**Errores**:
- `find_by_id` → `FEED_NOT_FOUND`
- `find_by_url` → `FEED_NOT_FOUND`

### 6.3 RawArticleRepository

```python
class RawArticleRepository(Protocol):
    def save(self, article: RawArticle) -> None: ...
    def save_batch(self, articles: list[RawArticle]) -> None: ...
    def find_by_id(self, id: RawArticleId) -> Result[RawArticle]: ...
    def find_by_feed(self, feed_id: FeedId, page: int, size: int) -> list[RawArticle]: ...
    def find_by_hash(self, feed_id: FeedId, content_hash: str) -> Result[RawArticle]: ...
    def exists_by_url(self, feed_id: FeedId, url: ArticleUrl) -> bool: ...
    def exists_by_hash(self, feed_id: FeedId, content_hash: str) -> bool: ...
    def count_by_feed(self, feed_id: FeedId) -> int: ...
```

**Errores**:
- `find_by_id` → `RAW_ARTICLE_NOT_FOUND`
- `find_by_hash` → `RAW_ARTICLE_NOT_FOUND`
- `save` puede fallar → `DUPLICATE_ARTICLE` (url o hash duplicados dentro del Feed)

### 6.4 CategoryRepository

```python
class CategoryRepository(Protocol):
    def save(self, category: Category) -> None: ...
    def find_by_id(self, id: CategoryId) -> Result[Category]: ...
    def find_by_slug(self, slug: str) -> Result[Category]: ...
    def find_all(self) -> list[Category]: ...
    def find_active(self) -> list[Category]: ...
    def find_by_parent(self, parent_id: CategoryId) -> list[Category]: ...
    def exists_by_slug(self, slug: str) -> bool: ...
```

**Errores**:
- `find_by_id` → `CATEGORY_NOT_FOUND`
- `find_by_slug` → `CATEGORY_NOT_FOUND`

### 6.5 TopicRepository

```python
class TopicRepository(Protocol):
    def save(self, topic: Topic) -> None: ...
    def find_by_id(self, id: TopicId) -> Result[Topic]: ...
    def find_by_name(self, name: str) -> Result[Topic]: ...
    def find_all(self) -> list[Topic]: ...
    def find_active(self) -> list[Topic]: ...
    def exists_by_name(self, name: str) -> bool: ...
```

**Errores**:
- `find_by_id` → `TOPIC_NOT_FOUND`
- `find_by_name` → `TOPIC_NOT_FOUND`

---

## 7. Invariantes Completas

### 7.1 NewsSource

| # | Invariante | ¿Cruza AR? | Explicación |
|---|-----------|-----------|-------------|
| I-01 | `name` MUST NOT be empty | ❌ No | Una fuente debe tener un nombre identificable |
| I-02 | `name` MUST be unique across all NewsSources | ❌ No (intra-AR, enforcement repositorio) | El nombre es el identificador semántico |
| I-03 | `source_type` MUST be a valid SourceType | ❌ No | El tipo debe ser un valor conocido del enum |
| I-04 | `source_url` MUST be a valid URL | ❌ No | Validado por SourceUrl VO |

### 7.2 Feed

| # | Invariante | ¿Cruza AR? | Explicación |
|---|-----------|-----------|-------------|
| I-05 | `url` MUST NOT be empty | ❌ No | Un feed siempre tiene una URL |
| I-06 | `url` MUST be unique within the parent NewsSource | ❌ No (intra-AR, enforcement repositorio) | No dos feeds con la misma URL en el mismo source |
| I-07 | `retry_count` MUST be 0 after successful collection | ❌ No | Reintentos son consecutivos, se resetean en éxito |
| I-08 | MUST pause if `retry_count >= max_retries` and fetch fails | ❌ No | Protege contra consumo infinito de recursos |
| I-09 | MUST NOT fetch while paused | ❌ No | Feed pausado requiere reactivación manual |
| I-10 | MUST NOT fetch if `is_active = False` | ❌ No | Feed desactivado no ejecuta fetch |

### 7.3 RawArticle

| # | Invariante | ¿Cruza AR? | Explicación |
|---|-----------|-----------|-------------|
| I-11 | **IMMUTABLE** — No modification after creation | ❌ No | Registro de auditoría |
| I-12 | `external_id + feed_id` MUST be unique | ❌ No (intra-tipo, enforcement repositorio) | No dos RawArticles con mismo ID externo en mismo Feed |
| I-13 | `content_hash` MUST be unique within the same Feed | ❌ No (intra-tipo, enforcement repositorio) | Deduplicación por contenido |
| I-14 | `fetched_at` >= `published_at` (if published_at present) | ❌ No | No se puede obtener antes de publicar |
| I-15 | `title` MUST NOT be empty | ❌ No | Validado por ArticleTitle VO |
| I-16 | `url` MUST be a valid URL | ❌ No | Validado por ArticleUrl VO |
| I-17 | `content_hash` MUST be a valid SHA-256 (64 hex chars) | ❌ No | Formato de hash correcto |

### 7.4 Category

| # | Invariante | ¿Cruza AR? | Explicación |
|---|-----------|-----------|-------------|
| I-18 | `slug` MUST be unique across all categories | ❌ No (intra-tipo, enforcement repositorio) | No dos categorías con el mismo slug |
| I-19 | `parent_id` MUST NOT equal `id` (no self-parent) | ❌ No | No puede ser padre de sí misma |
| I-20 | Hierarchy MUST NOT contain cycles | ❌ No (intra-tipo) | No puede haber A→B→C→A |
| I-21 | Deactivating a category with active subcategories MUST cascade | ❌ No | Desactivar padre desactiva hijos |

### 7.5 Topic

| # | Invariante | ¿Cruza AR? | Explicación |
|---|-----------|-----------|-------------|
| I-22 | `name` MUST NOT be empty | ❌ No | Un topic debe tener nombre |
| I-23 | `name` MUST be unique across all Topics | ❌ No (intra-tipo, enforcement repositorio) | No dos topics con el mismo nombre |

### 7.6 Reglas de Application Layer (Cross-AR)

Las siguientes reglas cruzan fronteras de Aggregate y NO pueden ser invariantes de dominio. Se verifican en los Application Services que orquestan operaciones:

| # | Regla | Origen | Destino | ¿Por qué no es invariante de dominio? |
|---|-------|--------|---------|--------------------------------------|
| AL-01 | NewsSource no puede desactivarse si tiene Feeds activos | `disable()` en NewsSource | Feed (AR separado) | NewsSource no puede consultar FeedRepository. Requiere Application Service que verifique `FeedRepository.count_active_by_source()`. |
| AL-02 | NewsSource solo puede activarse si tiene al menos un Feed activo | `enable()` en NewsSource | Feed (AR separado) | Misma razón: cruza frontera de AR. Application Service verifica antes de llamar a `enable()`. |
| AL-03 | `source_id` debe referenciar un NewsSource existente al crear/actualizar Feed | Creación/actualización de Feed | NewsSource (AR separado) | Feed no puede cargar NewsSource. Application Service verifica existencia. |
| AL-04 | No crear Feed bajo un NewsSource inactivo | Creación de Feed | NewsSource (AR separado) | Feed no puede conocer el estado de NewsSource. Application Service verifica `is_active`. |
| AL-05 | `feed_id` debe referenciar un Feed existente al crear RawArticle | Creación de RawArticle | Feed (AR separado) | RawArticle es inmutable al crearse. Application Service verifica existencia del Feed. |

**Implementación**: Estas reglas se ejecutan en los Application Services correspondientes (ej: `CreateFeedUseCase`, `EnableNewsSourceUseCase`, `CollectArticlesUseCase`) antes de llamar a los métodos de dominio.

### Decisión 1: Feed como Aggregate Root (no VO ni Entity dentro de NewsSource)

| Opción | Tradeoff |
|--------|----------|
| **✅ Aggregate Root** | Tiene identidad, ciclo de vida, invariantes (retry, auto-pause, categorización). Es referenciado por RawArticle. Las reglas de negocio pertenecen al dominio. |
| ❌ VO o Entity dentro de NewsSource | Forzaría a que Feed esté dentro de NewsSource. Cargar NewsSource con todos sus Feeds sería inviable. Pérdida de comportamiento de dominio (retry, pause). |

**Decisión**: Feed ES Aggregate Root.

### Decisión 2: Topic como Entity (no AR, no VO)

| Opción | Tradeoff |
|--------|----------|
| **✅ Entity** | Tiene identidad (TopicId), nombre único, ciclo de vida. Referenciable desde NewsSource y Feed. |
| ❌ AR | Overhead innecesario. Topic no tiene dependientes, no requiere frontera transaccional, no emite eventos. |
| ❌ VO | Sería solo un string. Sin identidad ni ciclo de vida. Imposible renombrar centralizadamente. |

**Decisión**: Topic es **Entity**.

### Decisión 3: Category como Entity (no AR)

| Opción | Tradeoff |
|--------|----------|
| **✅ Entity** | Tiene identidad, ciclo de vida, jerarquía. Consistencia eventual. Referenciada por ID. |
| ❌ AR | Overhead innecesario para un concepto de referencia. |

**Decisión**: Category es **Entity**.

### Decisión 4: Cero Domain Services

| Servicio | Decisión | Justificación |
|----------|----------|---------------|
| FeedOrchestrator | 🟡 **Application Layer** | La orquestación cross-AR es responsabilidad de Application Services. YAGNI para Domain Service. |
| SourceValidator | ❌ **No existe** | Validar unicidad de nombre y configuración es del NewsSource o Application Service. |
| DeduplicationService | ❌ **No existe** | La deduplicación la maneja RawArticleRepository (exists_by_hash, exists_by_url). |

**Decisión**: 0 Domain Services. Aplicación estricta de YAGNI.

### Decisión 5: FeedGroup NO está en dominio

| Opción | Tradeoff |
|--------|----------|
| **✅ Fuera del dominio (Application/Infraestructura)** | FeedGroup es agrupación operativa sin reglas de negocio reales. YAGNI. |
| ❌ En dominio (Entity o AR) | Agrega complejidad (repositorio, ID, relaciones). Las reglas de herencia son defaults de configuración, no invariantes. |

**Decisión**: FeedGroup NO pertenece al dominio.

### Decisión 6: SyncPolicy simplificado (sin lógica de timing)

| Opción | Tradeoff |
|--------|----------|
| **✅ VO de configuración pura** | Elimina `is_due`, `next_run`. SRP: el VO almacena configuración, el scheduler decide cuándo ejecutar. SyncPolicy más simple y testeable. |
| ❌ VO con timing | SyncPolicy requeriría ClockPort. Mezcla configuración con orquestación temporal. |

**Decisión**: SyncPolicy es VO de configuración pura.

### Decisión 7: RawArticle hereda de Entity (no de AggregateRoot)

Ver ADR-023 para análisis completo.

| Opción | Tradeoff |
|--------|----------|
| **✅ Entity + documentado como AR** | RawArticle es inmutable y no emite eventos → no necesita `_events`. Se documenta como AR por volumen. |
| ❌ AggregateRoot | Mayor claridad técnica pero carga innecesaria. RawArticle nunca usa register_event(). |

**Decisión**: RawArticle hereda de `Entity`, se documenta como AR.

---

## 9. Arquitectura y Cumplimiento

### 9.1 Clean Architecture Layers

| Capa | Contiene | Verificación |
|------|----------|-------------|
| **domain/** | Entities, VOs, Events, Repository Ports, Exceptions | ✅ domain/ no importa nada externo. |
| **application/** | Application Services (futuro Sprint 3.6+) | ✅ importa solo domain/. |
| **infrastructure/** | Adapters, Repos implementados (futuro) | ✅ implementa domain/ports/. |
| **presentation/** | FastAPI, CLI (futuro) | ✅ llama application/. |

Sprint 3.1 cubre exclusivamente **domain/**. No hay dependencias de infraestructura, aplicación ni presentación.

### 9.2 DDD Tactical Patterns

| Pattern | Implementado | Verificación |
|---------|-------------|-------------|
| **Aggregate Root** | `NewsSource`, `Feed`, `RawArticle` | Cada uno es frontera de consistencia. Referencias entre ARs por ID. |
| **Entity** | `Category`, `Topic` | Identidad propia. Mutable con métodos de dominio. |
| **Value Object** | 6 VOs (`@dataclass(frozen=True)`) | Inmutables. Validación en `__post_init__`. Comportamiento de dominio. |
| **Domain Event** | 3 eventos | Registrados vía `register_event()`, recolectados vía `pull_events()`. |
| **Repository** | 5 Protocols | Sin mención de tecnología. Métodos en lenguaje de dominio. |
| **Domain Service** | 0 (CERO) | YAGNI aplicado. FeedOrchestrator va en Application Layer. |

### 9.3 SOLID

| Principio | Verificación |
|-----------|-------------|
| **SRP** | Cada AR tiene una responsabilidad: NewsSource (configurar fuente), Feed (ejecutar fetch + retry), RawArticle (registrar artículo inmutable). Cada VO encapsula UNA regla de validación. |
| **OCP** | Repository Ports son Protocols → extensibles por implementación. SourceType es Enum → nuevos tipos se agregan sin modificar dominio. |
| **LSP** | Todos los IDs heredan de EntityId sin alterar comportamiento. Todos los VOs heredan de ValueObject. |
| **ISP** | 5 interfaces de repositorio pequeñas (4-7 métodos cada una). Protocols segregados. |
| **DIP** | domain/ports/ define interfaces. Infrastructure/ implementa. Domain no conoce infraestructura. |

### 9.4 ADR-021 — Foundation Stability Policy

| Criterio | Cumplimiento |
|----------|-------------|
| **MULTI-BC**: ¿Usado por 2+ BCs? | ❌ NO. Todos los IDs (SourceId, FeedId, RawArticleId, CategoryId, TopicId) solo los usa Ingestion. |
| **NO BUSINESS RULES** | ✅ Los IDs no tienen reglas de negocio. |
| **ZERO DEPENDENCIES** | ✅ Heredan de EntityId stdlib-only. |
| **NO COUPLING** | ✅ No incrementan acoplamiento entre BCs. |
| **MECHANISM, NOT POLICY** | ✅ Son IDs específicos de dominio, no mecanismo transversal. |

**Conclusión**: Los IDs PERMANECEN en Ingestion BC. Foundation solo tiene `EntityId` genérico. Cumple ADR-021.

### 9.5 ADR-022 — ErrorCode Enum Inheritance

`IngestionErrorCode` es un `str, Enum` independiente (NO hereda de Foundation `ErrorCode`).

```python
class IngestionErrorCode(str, Enum):
    NEWS_SOURCE_NOT_FOUND = "NEWS_SOURCE_NOT_FOUND"
    FEED_NOT_FOUND = "FEED_NOT_FOUND"
    RAW_ARTICLE_NOT_FOUND = "RAW_ARTICLE_NOT_FOUND"
    CATEGORY_NOT_FOUND = "CATEGORY_NOT_FOUND"
    TOPIC_NOT_FOUND = "TOPIC_NOT_FOUND"
    DUPLICATE_NEWS_SOURCE = "DUPLICATE_NEWS_SOURCE"
    DUPLICATE_FEED_URL = "DUPLICATE_FEED_URL"
    DUPLICATE_ARTICLE = "DUPLICATE_ARTICLE"
    INVALID_SOURCE_URL = "INVALID_SOURCE_URL"
    INVALID_ARTICLE_URL = "INVALID_ARTICLE_URL"
    INVALID_LANGUAGE = "INVALID_LANGUAGE"
    NEWS_SOURCE_INACTIVE = "NEWS_SOURCE_INACTIVE"
    FEED_INACTIVE = "FEED_INACTIVE"
    HAS_ACTIVE_FEEDS = "HAS_ACTIVE_FEEDS"
    CYCLE_DETECTED = "CYCLE_DETECTED"
    FEED_MAX_RETRIES_EXCEEDED = "FEED_MAX_RETRIES_EXCEEDED"
    FEED_ALREADY_PAUSED = "FEED_ALREADY_PAUSED"
```

### 9.6 Foundation FROZEN — No Modificaciones

Foundation v1.0 está FROZEN. El BC Ingestion lo CONSUME. No se modifica, no se extiende, no se parchea. Sprint 3.1 solo importa de Foundation:
- `Entity`, `AggregateRoot`, `ValueObject`
- `EntityId`
- `DomainEvent`
- `Result`, `Error`, `DomainError`

### 9.7 Resumen de Cambios respecto al Draft v1.0

| Concepto | Draft v1.0 | Sprint 3.1 v2.0 | Razón |
|----------|------------|------------------|-------|
| Source → NewsSource | Source | NewsSource | Precisión semántica |
| RawItem → RawArticle | RawItem | RawArticle | Refleja que son artículos |
| Topic | NO EXISTE | Entity (nuevo) | Concepto solicitado |
| FeedGroup | Aggregate Root | ❌ Fuera del dominio | YAGNI, es operativo |
| SyncPolicy | VO con timing | VO de configuración pura | SRP, scheduler decide |
| SourceType (Enum) | provider_type + technology_type | SourceType único | Simplificación |
| RetryPolicy | VO separado | Atributos en SyncPolicy | Simplificación |
| Domain Events | 5 eventos intra-BC + 1 integración | 3 eventos intra-BC | YAGNI (SourceCreated, CategoryCreated eliminados) |
| Domain Services | FeedOrchestrator, SourceValidator | 0 servicios | Van en Application Layer |
| Repositorios | Source, Feed, FeedGroup, RawItem, Category | NewsSource, Feed, RawArticle, Category, Topic | FeedGroup fuera, Topic agregado |
| VOs | 6 aprobados | 6 (CategoryName + SourceType simplificado; Author eliminado por YAGNI) | CategoryName necesario, Author colapsado a `str \| None` |
| ArticleDescription como VO | ❌ NO | ❌ NO (atributo plano) | Sin reglas de negocio |
| PublishedAt como VO | ❌ NO | ❌ NO (atributo plano) | Sin reglas de negocio |
| Metadata como VO | ❌ NO | ❌ NO (dict plano) | Sin comportamiento |
| RawArticle herencia | AggregateRoot | Entity (documentado como AR) | ADR-023 |

---

## 10. Estructura de Archivos

```
src/ingestion/domain/
├── __init__.py
├── entities/
│   ├── __init__.py
│   ├── ids.py                    # SourceId, FeedId, RawArticleId, CategoryId, TopicId
│   ├── news_source.py            # NewsSource (AR)
│   ├── feed.py                   # Feed (AR)
│   ├── raw_article.py            # RawArticle (AR, inmutable, hereda Entity)
│   ├── category.py               # Category (Entity)
│   └── topic.py                  # Topic (Entity)
├── value_objects/
│   ├── __init__.py
│   ├── source_url.py             # SourceUrl
│   ├── article_url.py            # ArticleUrl
│   ├── article_title.py          # ArticleTitle
│   ├── language.py               # Language
│   ├── source_type.py            # SourceType (Enum)
│   ├── category_name.py          # CategoryName
│   └── sync_policy.py            # SyncPolicy + SyncMode (simplificado)
├── events/
│   ├── __init__.py
│   ├── ingestion_events.py       # RawArticleCollected
│   └── source_events.py          # SourceEnabled, SourceDisabled
├── ports/
│   ├── __init__.py
│   └── repositories.py           # Todos los repositorios (Protocols)
└── exceptions/
    ├── __init__.py
    └── errors.py                 # IngestionErrorCode (str, Enum)
```

---

## 11. Mapa de Puertos y Relaciones

```
┌──────────────────────────────────────────────────────────────────────┐
│              AGGREGATES          PERSISTENCE PORTS    INFRA PORTS    │
│                                                                      │
│  ┌──────────────────┐         ┌───────────────────────┐             │
│  │  NewsSource (AR)  │────────▶│  NewsSourceRepository │             │
│  └──────────────────┘         └───────────────────────┘             │
│           │                                                          │
│           │ 1:N (source_id)                                          │
│           ▼                                                          │
│  ┌──────────────────┐         ┌───────────────────────┐             │
│  │    Feed (AR)      │────────▶│    FeedRepository     │             │
│  └──────────────────┘         └───────────────────────┘             │
│           │                                                          │
│           │ 1:N (feed_id)                                            │
│           ▼                                                          │
│  ┌──────────────────┐         ┌───────────────────────┐             │
│  │  RawArticle (AR)  │────────▶│  RawArticleRepository │             │
│  │   [INMUTABLE]     │         └───────────────────────┘             │
│  └──────────────────┘                                                │
│                                                                      │
│  ┌──────────────────┐         ┌───────────────────────┐             │
│  │  Category (Ent.)  │────────▶│  CategoryRepository   │             │
│  └──────────────────┘         └───────────────────────┘             │
│                                                                      │
│  ┌──────────────────┐         ┌───────────────────────┐             │
│  │   Topic (Ent.)    │────────▶│   TopicRepository     │             │
│  └──────────────────┘         └───────────────────────┘             │
└──────────────────────────────────────────────────────────────────────┘
```
