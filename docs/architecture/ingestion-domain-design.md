# 🏗️ Ingestion Domain — Domain Design Document

> **Documento oficial de diseño del dominio del Bounded Context Ingestion**
>
> Versión: 1.0-draft | Estado: **DRAFT — Pendiente de aprobación ARB**
> Fecha: 2026-07-02
> Basado en: Baseline Architecture v1.0 (FROZEN), Foundation v1.0 STABLE
>
> **Este documento especifica, NO implementa.** Ninguna clase aquí definida
> debe ser codificada hasta que el ARB apruebe el diseño completo.

---

## Tabla de Contenidos

1. [Propósito del Bounded Context](#1-propósito-del-bounded-context)
2. [Lenguaje Ubicuo](#2-lenguaje-ubicuo)
3. [Entidades](#3-entidades)
4. [Value Objects](#4-value-objects)
5. [Aggregates](#5-aggregates)
6. [Domain Events](#6-domain-events)
7. [Domain Services](#7-domain-services)
8. [Repositories](#8-repositories)
9. [Ports](#9-ports)
10. [Casos de Uso del Dominio](#10-casos-de-uso-del-dominio)
11. [Invariantes](#11-invariantes)
12. [Diagramas Conceptuales](#12-diagramas-conceptuales)
13. [Roadmap de Implementación](#13-roadmap-de-implementación)

---

## 1. Propósito del Bounded Context

### 1.1 Responsabilidad Fundamental

> **Obtener información desde fuentes externas, normalizarla y publicarla para consumo de otros Bounded Contexts.**

El Ingestion BC es la puerta de entrada de información al sistema. Su responsabilidad comienza cuando una fuente externa es descubierta o configurada, y termina cuando los datos normalizados están disponibles para que otros BCs los consuman.

### 1.2 Límites del Contexto

```
                    ┌──────────────────────────────────────┐
                    │         SISTEMA EXTERIOR             │
                    │  (Reddit, Steam, HN, RSS feeds, etc.) │
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
| **Configuración** | Definir fuentes externas (Source), sus streams (Feed), y agrupaciones (FeedGroup) |
| **Adquisición** | Ejecutar fetch de feeds vía PULL, procesar webhooks PUSH, manejar streams STREAM |
| **Parseo** | Transformar respuestas crudas en items estructurados (RawItem) |
| **Normalización** | Limpiar, sanitizar, deduplicar y enriquecer items |
| **Publicación** | Emitir eventos de integración para consumo de otros BCs |
| **Monitoreo** | Tracking de ejecuciones (IngestionRun), reintentos, estados de salud |
| **Categorización** | Clasificación temática de feeds y items |

### 1.4 Qué NO Pertenece al BC

| Área | Excluido porque... | Va en |
|------|-------------------|-------|
| Scoring, clasificación semántica | Es análisis de contenido, no adquisición | Research BC |
| Aprobación/rechazo editorial | Es ciclo de vida editorial | Research BC |
| Generación de contenido | Es producción de guiones | Script BC |
| Usuarios, roles, autenticación | No hay usuarios en el dominio de ingesta | — |
| Conexión a bases de datos | Es infraestructura | Infraestructura del BC |
| Configuración de la app (.env, settings) | Es configuración de aplicación | `presentation/config/` |
| Implementación de HTTP/RSS/WS | Son adapters tecnológicos | Infraestructura del BC |

### 1.5 Relación con los Demás BCs

| BC | Relación | Mecanismo |
|----|----------|-----------|
| **Research BC** | Ingestion provee items normalizados para su análisis | Integration Event: `NewRawItemsAvailable` |
| **Script BC** | Indirecta — Script consume de Research, no de Ingestion | — |
| **Shared Domain** | Ingestion referencia `Category` (vive en shared) | Composición de dominio |

**Principio**: Ingestion NO conoce la existencia de Research o Script. Solo publica eventos. Quien los consume es decisión de otros BCs.

---

## 2. Lenguaje Ubicuo

### 2.1 Términos del Núcleo del Dominio

#### Source (Fuente)

| Campo | Valor |
|-------|-------|
| **Definición** | Un origen externo de información del cual se pueden obtener datos de forma estructurada. Representa un servicio, plataforma, o repositorio de contenido. |
| **Ejemplos** | Reddit, Steam News, Hacker News, GitHub Trends, Google News, YouTube |
| **Tipo** | Aggregate Root |
| **Identidad** | `SourceId` |
| **Ciclo de vida** | Creada → Activa (configurada) → Inactiva/Archivada |
| **Cardinalidad** | 1 Source → N Feeds, 1 Source → N FeedGroups |

**Reglas semánticas**:
- Una Source representa una **plataforma/proveedor**, no una URL individual
- Dos Sources no pueden tener el mismo nombre
- Una Source define la tecnología de transporte y la configuración global
- Una Source desactivada no puede tener Feeds activos

---

#### Feed

| Campo | Valor |
|-------|-------|
| **Definición** | Un stream específico de información dentro de un Source. Es la unidad configurable y ejecutable de ingesta. |
| **Ejemplos** | `r/programming` en Reddit, `top` en Hacker News, un canal de YouTube |
| **Tipo** | Aggregate Root |
| **Identidad** | `FeedId` |
| **Ciclo de vida** | Creado → Activo (con SyncPolicy configurada) → Pausado (por errores) → Inactivo |
| **Cardinalidad** | N Feeds → 1 Source, N Feeds → 0..1 FeedGroup |

**Reglas semánticas**:
- Un Feed pertenece EXACTAMENTE a un Source
- Un Feed puede pertenecer a 0 o 1 FeedGroup
- La URL del Feed debe ser única dentro del Source
- Cada Feed tiene su propia SyncPolicy (independiente de otros Feeds)
- Un Feed puede tener categorías propias además de las heredadas del grupo

---

#### FeedGroup

| Campo | Valor |
|-------|-------|
| **Definición** | Agrupación operativa de Feeds dentro de un Source. Permite gestionar políticas comunes (sync, categorización) para múltiples Feeds de forma consistente. |
| **Ejemplos** | "Tech" (agrupa feeds de tecnología), "Gaming" (agrupa feeds de gaming) |
| **Tipo** | Aggregate Root |
| **Identidad** | `FeedGroupId` |
| **Ciclo de vida** | Creado → Activo → Inactivo |
| **Cardinalidad** | N FeedGroups → 1 Source, 1 FeedGroup → N Feeds (opcional) |

**Reglas semánticas**:
- Un FeedGroup pertenece EXACTAMENTE a un Source
- Un Feed pertenece a 0 o 1 FeedGroup
- Las políticas del grupo son **defaults** que los Feeds pueden sobrescribir
- Si un Feed no tiene categorías propias, hereda la del grupo
- Eliminar un FeedGroup NO elimina sus Feeds (solo se desasignan)

---

#### RawItem

| Campo | Valor |
|-------|-------|
| **Definición** | Una pieza individual de información cruda obtenida de un Feed. Representa el estado más granular de la información antes de cualquier procesamiento. |
| **Ejemplos** | Un post de Reddit, un artículo de HN, un commit de GitHub |
| **Tipo** | Aggregate Root |
| **Identidad** | `RawItemId` |
| **Ciclo de vida** | Creado (inmutable después de creación) |
| **Cardinalidad** | N RawItems → 1 Feed, N RawItems → 1 Batch |

**Reglas semánticas**:
- Un RawItem es **INMUTABLE** después de creado. No se modifica, no se actualiza, no se elimina.
- La `external_id` debe ser única dentro del Feed (deduplicación por ID externo)
- El `hash` (SHA-256 del contenido) debe ser único dentro del Feed (deduplicación por contenido)
- Un RawItem pertenece EXACTAMENTE a un Feed
- Un RawItem pertenece EXACTAMENTE a un Batch (una ejecución de fetch)

---

#### Category

| Campo | Valor |
|-------|-------|
| **Definición** | Clasificación temática que permite organizar, filtrar y agrupar contenido. Puede tener jerarquía (subcategorías). |
| **Ejemplos** | "Technology", "Science", "Gaming", "World News" |
| **Tipo** | Entity |
| **Identidad** | `CategoryId` |
| **Ciclo de vida** | Creada → Activa → Inactiva |
| **Cardinalidad** | 1 Category → 0..N subcategorías (parent_id), N Feeds → N Categories (relación M:N) |

**Nota**: Category es dominio compartido. Podría migrar a `shared/domain/` si Research BC también la necesita.

---

#### Batch

| Campo | Valor |
|-------|-------|
| **Definición** | Agrupación conceptual de RawItems obtenidos en una misma ejecución de fetch. NO es una entidad con identidad propia — es un conjunto de RawItems que comparten el mismo `batch_id`. |
| **Tipo** | Concepto (identificador UUID) |
| **Identidad** | `batch_id: UUID` (no tiene tipo propio — es un UUID simple) |

**Reglas semánticas**:
- Un Batch representa una **ejecución atómica de fetch**: todos los RawItems del batch se obtuvieron en la misma operación
- El `batch_id` se genera al inicio del fetch y se asigna a todos los RawItems producidos
- Sirve para: recovery (reprocesar un batch completo), trazabilidad (vincular RawItems con su fetch), y publicación (notificar a Research BC sobre nuevos items)

---

#### NormalizedItem

| Campo | Valor |
|-------|-------|
| **Definición** | La representación procesada, limpia y enriquecida de un RawItem. Es el resultado del pipeline de normalización. |
| **Tipo** | Value Object |
| **Identidad** | No tiene — es un VO derivado de un RawItem |

**Reglas semánticas**:
- Siempre se deriva de UN RawItem específico
- Es inmutable
- Se publica vía Integration Events a otros BCs
- NO se persiste en el BC Ingestion (se publica y se descarta)
- El Research BC es responsable de persistir los datos que necesite

---

### 2.2 Términos de Configuración y Operación

#### SyncPolicy

| Campo | Valor |
|-------|-------|
| **Definición** | Política que determina cómo y cuándo se obtienen datos de un Feed. Especifica el modo de sincronización y sus parámetros asociados. |
| **Tipo** | Value Object |
| **Modos** | `PULL` (el sistema consulta periódicamente), `PUSH` (el source notifica al sistema), `STREAM` (conexión persistente), `MANUAL` (solo bajo demanda) |

---

#### IngestionRun

| Campo | Valor |
|-------|-------|
| **Definición** | Resultado de una ejecución de fetch para un Feed. Captura métricas y estado de la operación. |
| **Tipo** | Value Object |
| **Estados** | `SUCCESS` (completado sin errores), `FAILED` (error irrecuperable), `PARTIAL` (algunos items obtenidos, otros fallaron) |

---

#### SourceConfig

| Campo | Valor |
|-------|-------|
| **Definición** | Configuración técnica y operativa de un Source. Incluye parámetros de transporte y específicos del proveedor. |
| **Tipo** | Value Object |
| **Contenido típico** | URL base, método de autenticación, rate limiting, timeout, user-agent |

---

#### RetryPolicy

| Campo | Valor |
|-------|-------|
| **Definición** | Política de reintentos para fetches fallidos de un Feed. Define cuántas veces reintentar y con qué espaciado. |
| **Tipo** | Value Object |

---

#### ProviderCapability

| Campo | Valor |
|-------|-------|
| **Definición** | Operación específica que un ProviderAdapter soporta, más allá del fetch básico. |
| **Tipo** | Enum (Value Object) |
| **Valores** | `FETCH`, `SEARCH`, `TRENDING`, `STREAM`, `SUBMIT`, `RELEASES`, `VIDEOS` |

---

### 2.3 Términos de Proveedores (Provider Types)

Estos NO son entidades del dominio. Son **valores** del campo `provider_type` de Source.

| Provider | Descripción | TechnologyType típico |
|----------|-------------|----------------------|
| **RSS** | Fuente RSS/Atom genérica. Cualquier feed RSS estándar. | RSS |
| **Reddit** | Contenido de Reddit (subreddits, usuario). API JSON. | HTTP |
| **Steam** | Noticias de Steam, actualizaciones de juegos. | HTTP |
| **GitHub** | Repositorios, releases, tendencias de GitHub. | HTTP |
| **Hacker News** | Contenido de news.ycombinator.com (firebase API). | HTTP |
| **YouTube** | Videos, canales, búsquedas de YouTube. | HTTP |
| **Google News** | Noticias agregadas de Google News. | RSS o HTTP |

---

### 2.4 Términos de Tecnología (Technology Types)

| Tipo | Descripción |
|------|-------------|
| **RSS** | Protocolo de sindicación (RSS/Atom). Feed basado en XML. |
| **HTTP** | API REST o scraper HTTP. Respuesta JSON/HTML. |
| **WebSocket** | Conexión persistente para streams en tiempo real. |

---

## 3. Entidades

### 3.1 Source

| Aspecto | Especificación |
|---------|---------------|
| **Responsabilidad** | Representar y configurar un origen externo de información. Es el punto de entrada para la configuración de ingesta. |
| **Identidad** | `SourceId(EntityId)` — Identidad única, inmutable, type-safe |
| **Tipo** | Aggregate Root |
| **Inmutabilidad** | Mutable (tiene ciclo de vida: activa → inactiva) |

**Atributos conceptuales**:

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `id` | `SourceId` | Identidad única |
| `name` | `str` | Nombre único y legible (ej: "Reddit", "Steam News") |
| `provider_type` | `str` | Identificador del proveedor (ej: "reddit", "steam", "generic_rss") |
| `technology_type` | `TechnologyType` | Tecnología de transporte (RSS, HTTP, WebSocket) |
| `is_active` | `bool` | Si está habilitada para ingesta |
| `config` | `SourceConfig` | Configuración técnica del Source |

**Métodos de dominio esperados**:

| Método | Descripción |
|--------|-------------|
| `activate()` | Marca el Source como activo |
| `deactivate()` | Marca el Source como inactivo (requiere que no haya Feeds activos) |
| `update_config(new_config)` | Actualiza la configuración técnica |
| `change_provider(provider_type)` | Cambia el tipo de proveedor (solo si no tiene Feeds) |

**Invariantes**:
- `name` no puede ser vacío ni duplicado entre Sources
- `provider_type` debe ser un identificador válido conocido
- `config` debe ser válida según el `provider_type` y `technology_type`
- No se puede desactivar un Source si tiene Feeds activos

**Relaciones**:
- Un Source tiene N Feeds (1:N)
- Un Source tiene N FeedGroups (1:N)
- Un Source tiene una SourceConfig (1:1)

---

### 3.2 Feed

| Aspecto | Especificación |
|---------|---------------|
| **Responsabilidad** | Representar un stream configurable de información dentro de un Source. Es la unidad de ejecución de fetch. |
| **Identidad** | `FeedId(EntityId)` — Identidad única, inmutable, type-safe |
| **Tipo** | Aggregate Root |
| **Inmutabilidad** | Mutable (tiene ciclo de vida: activo → pausado → inactivo) |

**Atributos conceptuales**:

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `id` | `FeedId` | Identidad única |
| `source_id` | `SourceId` | Referencia al Source padre |
| `group_id` | `FeedGroupId \| None` | Referencia opcional al FeedGroup |
| `url` | `str` | URL del feed (endpoint de consulta) |
| `label` | `str` | Etiqueta legible (ej: "r/programming", "top-hn") |
| `is_active` | `bool` | Si está habilitado para fetch |
| `sync` | `SyncPolicy` | Política de sincronización |
| `categories` | `list[CategoryId]` | Categorías asignadas (se fusionan con las del grupo) |
| `last_run` | `IngestionRun \| None` | Resultado de la última ejecución |
| `retry_count` | `int` | Contador de reintentos actuales (se resetea en éxito) |
| `next_retry_at` | `datetime \| None` | Próximo momento permitido para reintentar |

**Métodos de dominio esperados**:

| Método | Descripción |
|--------|-------------|
| `activate()` | Marca el Feed como activo, resetea retry_count |
| `deactivate()` | Marca el Feed como inactivo |
| `pause(reason)` | Pausa el Feed por errores |
| `record_run(run)` | Actualiza last_run, resetea retry_count si fue exitoso |
| `record_failure(error)` | Incrementa retry_count, calcula next_retry_at |
| `can_retry()` | `True` si retry_count < max_retries de la SyncPolicy |
| `update_sync(policy)` | Cambia la política de sincronización |
| `assign_to_group(group_id)` | Asigna el Feed a un FeedGroup |
| `remove_from_group()` | Desasigna el Feed de su grupo actual |
| `add_category(category_id)` | Agrega una categoría |
| `remove_category(category_id)` | Remueve una categoría |
| `effective_categories()` | Retorna categorías propias + heredadas del grupo |

**Invariantes**:
- `url` debe ser única dentro del Source
- `source_id` debe referenciar un Source activo
- No se puede ejecutar fetch si `is_active = False`
- `retry_count` se resetea a 0 después de un fetch exitoso
- Si `retry_count >= max_retries` y el fetch falla, el Feed se pausa automáticamente

**Relaciones**:
- N Feeds → 1 Source (N:1)
- N Feeds → 0..1 FeedGroup (N:0..1)
- 1 Feed → N Categorías (N:M vía CategoryId)
- 1 Feed → 1 SyncPolicy (1:1)
- 1 Feed → 0..1 IngestionRun (0..1:1)
- 1 Feed → N RawItems (1:N)

---

### 3.3 FeedGroup

| Aspecto | Especificación |
|---------|---------------|
| **Responsabilidad** | Agrupar Feeds operativamente para compartir políticas de sincronización y categorización. |
| **Identidad** | `FeedGroupId(EntityId)` — Identidad única, inmutable, type-safe |
| **Tipo** | Aggregate Root |
| **Inmutabilidad** | Mutable |

**Atributos conceptuales**:

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `id` | `FeedGroupId` | Identidad única |
| `source_id` | `SourceId` | Referencia al Source padre |
| `name` | `str` | Nombre del grupo (ej: "tech", "gaming") |
| `is_active` | `bool` | Si el grupo está activo |
| `default_sync` | `SyncPolicy \| None` | Política default para Feeds del grupo |
| `default_category` | `CategoryId \| None` | Categoría default para Feeds del grupo |

**Métodos de dominio esperados**:

| Método | Descripción |
|--------|-------------|
| `activate()` | Marca el grupo como activo |
| `deactivate()` | Marca el grupo como inactivo (NO desasigna Feeds) |
| `set_default_sync(policy)` | Establece la SyncPolicy default |
| `set_default_category(category_id)` | Establece la categoría default |

**Invariantes**:
- `name` debe ser único dentro del Source
- Eliminar un FeedGroup NO elimina sus Feeds (solo se desasignan)
- Si se cambia `default_sync`, los Feeds que NO tengan SyncPolicy propia heredan la nueva

**Relaciones**:
- N FeedGroups → 1 Source (N:1)
- 1 FeedGroup → N Feeds (1:N, opcional)

---

### 3.4 RawItem

| Aspecto | Especificación |
|---------|---------------|
| **Responsabilidad** | Almacenar de forma inmutable una pieza de información cruda obtenida de un Feed. Es el registro de auditoría de todo lo que se ha obtenido. |
| **Identidad** | `RawItemId(EntityId)` — Identidad única, inmutable, type-safe |
| **Tipo** | Aggregate Root |
| **Inmutabilidad** | **INMUTABLE después de creado** — No tiene setters, no tiene métodos que modifiquen estado |

**Atributos conceptuales**:

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `id` | `RawItemId` | Identidad única |
| `feed_id` | `FeedId` | Feed del que se obtuvo |
| `batch_id` | `UUID` | Batch al que pertenece esta ejecución de fetch |
| `external_id` | `str` | ID único en el sistema externo (ej: el ID del post en Reddit) |
| `hash` | `str` | SHA-256 del contenido (para deduplicación) |
| `title` | `str` | Título del item |
| `description` | `str` | Descripción o extracto |
| `content` | `str` | Contenido completo |
| `url` | `str` | URL original del item |
| `author` | `str \| None` | Autor o creador |
| `published_at` | `datetime \| None` | Fecha de publicación original |
| `fetched_at` | `datetime` | Fecha en que se obtuvo |
| `metadata` | `dict` | Datos adicionales específicos del proveedor |

**Métodos de dominio esperados**:

| Método | Descripción |
|--------|-------------|
| Constructor | Todos los atributos son requeridos en creación. No hay setters. No hay métodos de modificación. |

**Invariantes**:
- **INMUTABLE** — Una vez creado, ningún atributo cambia
- `external_id` + `feed_id` deben ser únicos (no hay dos RawItems con el mismo external_id en el mismo Feed)
- `hash` debe ser único dentro del Feed (deduplicación por contenido)
- `fetched_at` debe ser >= `published_at` si `published_at` está presente
- `url` debe ser una URL válida (puede validarse en creación)

**Relaciones**:
- N RawItems → 1 Feed (N:1)
- N RawItems → 1 Batch (N:1, batch_id como UUID)

---

### 3.5 Category

| Aspecto | Especificación |
|---------|---------------|
| **Responsabilidad** | Clasificar temáticamente Feeds y NormalizedItems. Provee una estructura jerárquica opcional. |
| **Identidad** | `CategoryId(EntityId)` — Identidad única, inmutable, type-safe |
| **Tipo** | Entity |
| **Inmutabilidad** | Mutable |

**Atributos conceptuales**:

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `id` | `CategoryId` | Identidad única |
| `name` | `str` | Nombre legible (ej: "Technology") |
| `slug` | `str` | Slug URL-friendly (ej: "technology") |
| `parent_id` | `CategoryId \| None` | Categoría padre (para jerarquía) |
| `is_active` | `bool` | Si está activa |

**Métodos de dominio esperados**:

| Método | Descripción |
|--------|-------------|
| `activate()` | Marca como activa |
| `deactivate()` | Marca como inactiva |
| `change_parent(new_parent_id)` | Cambia la categoría padre |

**Invariantes**:
- `slug` debe ser único (no hay dos categorías con el mismo slug)
- La jerarquía no debe tener ciclos (Category A no puede ser ancestro de Category B si B también es ancestro de A)
- Una categoría no puede ser padre de sí misma
- Si se desactiva una categoría con subcategorías activas, las subcategorías heredan el estado

**Relaciones**:
- 1 Category → 0..N subcategorías (a través de `parent_id`)
- N Feeds → N Categories (relación M:M vía listas de CategoryId)

---

## 4. Value Objects

### 4.1 SyncPolicy

| Aspecto | Especificación |
|---------|---------------|
| **Propósito** | Define cómo y cuándo se ejecuta el fetch de un Feed. |
| **Inmutabilidad** | ✅ `@dataclass(frozen=True)` |
| **Atributos** | |

| Atributo | Tipo | Default | Descripción |
|----------|------|---------|-------------|
| `mode` | `SyncMode` | (requerido) | Modo de sincronización: PULL, PUSH, STREAM, MANUAL |
| `pull_interval` | `int \| None` | `None` | Intervalo en minutos entre fetches (PULL) |
| `pull_cron` | `str \| None` | `None` | Expresión cron para programar fetches (PULL) |
| `push_secret_ref` | `str \| None` | `None` | Referencia al secreto para validar webhooks (PUSH) |
| `stream_heartbeat` | `int \| None` | `None` | Heartbeat en segundos para conexión (STREAM) |
| `retry` | `RetryPolicy` | `RetryPolicy()` | Política de reintentos |
| `timeout` | `int` | `30` | Timeout en segundos para cada fetch |
| `max_items` | `int` | `100` | Máximo de items a obtener por ejecución |

**Validaciones**:
- `mode PULL` requiere `pull_interval` o `pull_cron` (al menos uno)
- `mode PUSH` requiere `push_secret_ref`
- `mode STREAM` requiere `stream_heartbeat`
- `mode MANUAL` no requiere campos adicionales
- `timeout` debe ser > 0
- `max_items` debe ser > 0

**Métodos de dominio**:
- `is_due(now, last_run) → bool`: Determina si el Feed debe ejecutarse según el tiempo actual y la última ejecución
- `next_run(now, last_run) → datetime | None`: Calcula la próxima ejecución programada

#### SyncMode (Enum)

| Valor | Descripción |
|-------|-------------|
| `PULL` | El sistema consulta periódicamente al Source. Requiere intervalo o cron. |
| `PUSH` | El Source notifica al sistema mediante webhook. Requiere secreto de validación. |
| `STREAM` | Conexión persistente con el Source. Requiere heartbeat. |
| `MANUAL` | Solo se ejecuta bajo demanda explícita. |

---

### 4.2 IngestionRun

| Aspecto | Especificación |
|---------|---------------|
| **Propósito** | Capturar el resultado y métricas de una ejecución de fetch. |
| **Inmutabilidad** | ✅ `@dataclass(frozen=True)` |
| **Atributos** | |

| Atributo | Tipo | Default | Descripción |
|----------|------|---------|-------------|
| `status` | `IngestionStatus` | (requerido) | Resultado de la ejecución |
| `items_count` | `int` | `0` | Cantidad de items obtenidos |
| `duration_ms` | `int` | `0` | Duración total en milisegundos |
| `error_message` | `str \| None` | `None` | Mensaje de error si falló |
| `started_at` | `datetime` | (requerido) | Inicio de la ejecución |
| `finished_at` | `datetime` | (requerido) | Fin de la ejecución |

**Validaciones**:
- `finished_at` >= `started_at`
- `items_count` >= 0
- Si `status == FAILED`, `error_message` no debe ser vacío
- `duration_ms` >= 0

#### IngestionStatus (Enum)

| Valor | Descripción |
|-------|-------------|
| `SUCCESS` | Todos los items se obtuvieron correctamente |
| `FAILED` | Error irrecuperable, no se obtuvo ningún item |
| `PARTIAL` | Algunos items se obtuvieron, otros fallaron |

---

### 4.3 SourceConfig

| Aspecto | Especificación |
|---------|---------------|
| **Propósito** | Configuración técnica y operativa de un Source. |
| **Inmutabilidad** | ✅ `@dataclass(frozen=True)` |
| **Atributos** | |

| Atributo | Tipo | Default | Descripción |
|----------|------|---------|-------------|
| `base_url` | `str` | `""` | URL base del Source |
| `auth_method` | `str \| None` | `None` | Método de autenticación (oauth2, api_key, basic, etc.) |
| `api_key_ref` | `str \| None` | `None` | Referencia a la API key en el secrets manager |
| `rate_limit` | `int \| None` | `None` | Requests por minuto permitidos |
| `timeout_seconds` | `int` | `30` | Timeout default para requests |
| `max_redirects` | `int` | `5` | Máximo de redirecciones HTTP permitidas |
| `user_agent` | `str` | `"AI-Shorts/1.0"` | User-Agent para requests HTTP |

---

### 4.4 RetryPolicy

| Aspecto | Especificación |
|---------|---------------|
| **Propósito** | Define la estrategia de reintentos para fetches fallidos. |
| **Inmutabilidad** | ✅ `@dataclass(frozen=True)` |
| **Atributos** | |

| Atributo | Tipo | Default | Descripción |
|----------|------|---------|-------------|
| `max_retries` | `int` | `3` | Máximo de reintentos antes de pausar el Feed |
| `backoff_multiplier` | `float` | `2.0` | Multiplicador para backoff exponencial |
| `max_backoff_seconds` | `int` | `3600` | Backoff máximo en segundos (1 hora) |

**Métodos de dominio**:
- `next_retry_delay(attempt) → int`: Calcula el delay para el reintento `attempt` usando backoff exponencial: `min(base_delay * multiplier^attempt, max_backoff_seconds)`

---

### 4.5 NormalizedItem

| Aspecto | Especificación |
|---------|---------------|
| **Propósito** | Representación procesada y limpia de un RawItem. Es el producto del pipeline de normalización. |
| **Inmutabilidad** | ✅ `@dataclass(frozen=True)` |
| **Atributos** | |

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `raw_item_id` | `RawItemId` | RawItem del que se deriva |
| `title` | `str` | Título sanitizado |
| `content` | `str` | Contenido limpio (sin HTML, sin ruido) |
| `url` | `str` | URL original |
| `author` | `str \| None` | Autor (si se pudo extraer) |
| `language` | `str \| None` | Código ISO del idioma detectado |
| `quality_score` | `float \| None` | Score de calidad (si el pipeline lo calcula) |
| `categories` | `list[CategoryId]` | Categorías inferidas |
| `metadata` | `dict` | Metadatos adicionales del pipeline |

---

### 4.6 ProviderCapability (Enum)

| Valor | Descripción |
|-------|-------------|
| `FETCH` | Obtener items desde un feed |
| `SEARCH` | Buscar items por query |
| `TRENDING` | Obtener tendencias/top |
| `STREAM` | Conexión en tiempo real |
| `SUBMIT` | Enviar datos al Source |
| `RELEASES` | Obtener releases/versiones |
| `VIDEOS` | Obtener videos/canal |

---

## 5. Aggregates

### 5.1 Decisiones de Diseño

| Aggregate | ¿Por qué es Aggregate Root? | Decisión arquitectónica |
|-----------|---------------------------|------------------------|
| **Source** | Tiene ciclo de vida independiente. Es referenciado por múltiples Feeds. Si estuviera dentro de otro AR, sería imposible cargarlo sin cargar todos los Feeds. | ADR-002 lo establece como AR independiente |
| **Feed** | Tiene ciclo de vida y estado propio (sync, retry, last_run). Es la unidad de ejecución. Múltiples Feeds referencian al mismo Source. | ADR-002 lo establece como AR independiente |
| **FeedGroup** | Tiene ciclo de vida independiente. Múltiples Feeds pueden pertenecer al mismo grupo. | ADR-002 lo establece como AR independiente |
| **RawItem** | **Volumen**. Puede haber millones de RawItems. Si fuera una entidad dentro de Feed, cargar un Feed cargaría todos sus RawItems — inviable. | ADR-006 lo establece como AR independiente |

### 5.2 Fronteras de Consistencia

```
┌─────────────────────────────────────────────────────────────────┐
│                   FRONTERAS TRANSACCIONALES                      │
│                                                                  │
│  Cada Aggregate Root es una frontera de consistencia:            │
│  - Source: consistencia inmediata dentro de Source              │
│  - Feed: consistencia inmediata dentro de Feed                  │
│  - FeedGroup: consistencia inmediata dentro de FeedGroup        │
│  - RawItem: consistencia inmediata dentro de RawItem            │
│                                                                  │
│  Entre aggregates: CONSISTENCIA EVENTUAL                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Ejemplo:                                                        │
│  1. FeedOrchestrator ejecuta fetch                              │
│  2. Crea RawItem (AR) ← consistencia inmediata                 │
│  3. Actualiza Feed.last_run (AR) ← consistencia inmediata      │
│  4. Publica DomainEvent ← consistencia eventual                 │
│                                                                  │
│  Si el paso 3 falla después del paso 2:                         │
│  - RawItem existe, Feed.last_run no se actualizó                │
│  - El próximo fetch detectará duplicados por hash/external_id  │
│  - Esto es aceptable (consistencia eventual)                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Reglas de Consistencia entre Aggregates

| Regla | Tipo | Protección |
|-------|------|------------|
| Un Feed referencia un Source que existe | Consistencia eventual | Se verifica en Application Service al crear Feed |
| Un FeedGroup referencia un Source que existe | Consistencia eventual | Se verifica en Application Service |
| Un Feed referencia un FeedGroup que existe (si aplica) | Consistencia eventual | Se verifica en Application Service |
| Un RawItem referencia un Feed que existe | Consistencia eventual | Se verifica en Application Service |
| Feed.effective_categories = Feed.categories ∪ FeedGroup.default_category | Consistencia en lectura | Se computa en el momento (no se almacena) |

---

## 6. Domain Events

### 6.1 Intra-BC Domain Events

Estos eventos son **internos del BC Ingestion**. Se usan para comunicación entre componentes del mismo BC.

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOMAIN EVENTS (INTRA-BC)                      │
│                                                                  │
│  FeedOchestrator ──┬──► FeedFetchStarted                        │
│                    ├──► FeedFetchCompleted                       │
│                    ├──► FeedFetchFailed                          │
│                    └──► NewItemsDetected                         │
│                                                                  │
│  Scheduler ──────────► FeedPaused                               │
└─────────────────────────────────────────────────────────────────┘
```

#### FeedFetchStarted

| Campo | Especificación |
|-------|---------------|
| **Nombre** | `FeedFetchStarted` |
| **Cuándo ocurre** | Cuando se inicia una ejecución de fetch para un Feed (antes de ejecutar la llamada externa) |
| **Significado** | "Un Feed ha comenzado su proceso de fetch". Permite tracking, métricas, logging. |
| **Payload** | `feed_id: FeedId`, `started_at: datetime`, `batch_id: UUID` |
| **Publicado por** | FeedOrchestrator |
| **Consumido por** | MetricsService, Logger |

#### FeedFetchCompleted

| Campo | Especificación |
|-------|---------------|
| **Nombre** | `FeedFetchCompleted` |
| **Cuándo ocurre** | Cuando una ejecución de fetch finaliza exitosamente (sin importar si se encontraron items nuevos o no) |
| **Significado** | "El fetch ha terminado bien". Permite actualizar scheduler, registrar métricas. |
| **Payload** | `feed_id: FeedId`, `items_count: int`, `duration_ms: int`, `batch_id: UUID`, `completed_at: datetime` |
| **Publicado por** | FeedOrchestrator |
| **Consumido por** | Scheduler (calcula próxima ejecución), MetricsService |

#### FeedFetchFailed

| Campo | Especificación |
|-------|---------------|
| **Nombre** | `FeedFetchFailed` |
| **Cuándo ocurre** | Cuando una ejecución de fetch encuentra un error irrecuperable (timeout, HTTP error, parse error) |
| **Significado** | "El fetch ha fallado". Permite decidir reintento o pausa. |
| **Payload** | `feed_id: FeedId`, `error_message: str`, `attempt: int`, `batch_id: UUID`, `failed_at: datetime` |
| **Publicado por** | FeedOrchestrator |
| **Consumido por** | Scheduler (decide reintento), AlertService |

#### FeedPaused

| Campo | Especificación |
|-------|---------------|
| **Nombre** | `FeedPaused` |
| **Cuándo ocurre** | Cuando un Feed alcanza el máximo de reintentos y se pausa automáticamente |
| **Significado** | "Este Feed no se volverá a ejecutar hasta que alguien lo reactive". Requiere intervención. |
| **Payload** | `feed_id: FeedId`, `reason: str` (ej: "max retries exceeded"), `paused_at: datetime` |
| **Publicado por** | Scheduler (o FeedOrchestrator tras detectar retry_count >= max_retries) |
| **Consumido por** | MetricsService, Logger, AlertService |

#### NewItemsDetected

| Campo | Especificación |
|-------|---------------|
| **Nombre** | `NewItemsDetected` |
| **Cuándo ocurre** | Cuando se han creado RawItems nuevos (después de deduplicación) durante un fetch |
| **Significado** | "Hay items nuevos para normalizar". Dispara el pipeline de normalización. |
| **Payload** | `feed_id: FeedId`, `batch_id: UUID`, `count: int` (cantidad de RawItems nuevos) |
| **Publicado por** | FeedOrchestrator |
| **Consumido por** | NormalizationPipeline (inicia procesamiento) |

### 6.2 Integration Event (Cross-BC)

```
┌─────────────────────────────────────────────────────────────────┐
│                  INTEGRATION EVENT (CROSS-BC)                    │
│                                                                  │
│  Ingestion BC ───► NewRawItemsAvailable ────► Research BC       │
│                                                                  │
│  ESV: Event Storming Version                                      │
│  Versión 1: payload mínimo con batch_id                           │
└─────────────────────────────────────────────────────────────────┘
```

#### NewRawItemsAvailable

| Campo | Especificación |
|-------|---------------|
| **Nombre** | `NewRawItemsAvailable` |
| **Cuándo ocurre** | Cuando el pipeline de normalización completa el procesamiento de un batch de RawItems |
| **Significado** | "Hay contenido nuevo disponible para que Research BC lo analice". Es el evento que cruza el límite del BC. |
| **Payload** | `batch_id: UUID` (para que Research BC pueda recuperar los NormalizedItems), `feed_id: FeedId`, `item_count: int`, `fetched_at: datetime`, `normalized_at: datetime` |
| **Versión** | 1 (incrementar solo en cambios incompatibles) |
| **Garantías** | Idempotente por `batch_id`. Research BC debe manejar duplicados. |

---

## 7. Domain Services

### 7.1 Criterio de Selección

> Un Domain Service existe cuando una operación **no pertenece naturalmente a ninguna entidad o value object** porque involucra múltiples aggregates, o porque la lógica es sobre un concepto que no es una entidad.

NO se debe crear un Domain Service para mover lógica que pertenece a una entidad.

### 7.2 FeedOrchestrator

| Aspecto | Especificación |
|---------|---------------|
| **Responsabilidad** | Coordinar el ciclo completo de fetch para un Feed: cargar configuración → ejecutar fetch → parsear → deduplicar → crear RawItems → actualizar estado del Feed. |
| **¿Por qué es Domain Service?** | Involucra múltiples aggregates (Feed, RawItem) y múltiples puertos (TechnologyAdapter, ProviderAdapter, Parser, repositorios). Ninguna entidad individual tiene toda la información para orquestar esto. |
| **¿Qué NO hace?** | No ejecuta HTTP (eso es TechnologyAdapter). No parsea (eso es Parser). No normaliza (eso es NormalizationPipelinePort). No publica eventos (eso es EventPublisher). |

**Interacción esperada**:

```
FeedOrchestrator.execute(feed_id)
    │
    ├── 1. Cargar Feed (FeedRepository)
    │
    ├── 2. Validar que Feed está activo
    │
    ├── 3. Publicar FeedFetchStarted (DomainEvent)
    │
    ├── 4. Obtener ProviderAdapter para el Source (ProviderAdapter)
    │      └── TechnologyAdapter.fetch() → RawResponse
    │      └── ProviderAdapter.parse() → list[RawItem]
    │
    ├── 5. Deduplicar (RawItemRepository.exists_by_hash / exists_by_external_id)
    │
    ├── 6. Persistir RawItems nuevos (RawItemRepository.save_batch)
    │
    ├── 7. Actualizar Feed.last_run (Feed)
    │      └── Persistir Feed (FeedRepository)
    │
    ├── 8. Publicar FeedFetchCompleted o FeedFetchFailed (DomainEvent)
    │
    └── 9. Si hay items nuevos → publicar NewItemsDetected (DomainEvent)
```

**Métodos**:

| Método | Descripción |
|--------|-------------|
| `execute(feed_id, context) → Result[IngestionRun]` | Ejecuta el ciclo completo de fetch para un Feed |

**Errores esperados (resultados Failure)**:
- `FeedNotFoundError` — feed_id no existe
- `FeedNotActiveError` — Feed está desactivado
- `FetchExecutionError` — error en la ejecución del fetch externo
- `ParseError` — error al parsear la respuesta

---

### 7.3 SourceValidator

| Aspecto | Especificación |
|---------|---------------|
| **Responsabilidad** | Validar que una Source puede ser registrada antes de crearla. Verifica que la configuración sea coherente con el tipo de proveedor y tecnología. |
| **¿Por qué es Domain Service?** | La validación involucra lógica específica del tipo de Source (RSS vs HTTP vs Reddit vs Steam) y puede requerir verificar contra datos existentes (nombres duplicados, configuraciones inválidas). No es responsabilidad de la entidad Source (que es solo un contenedor de datos). |
| **¿Qué NO hace?** | No ejecuta llamadas externas para "probar" la conexión. No persiste nada. |

**Métodos**:

| Método | Descripción |
|--------|-------------|
| `validate(name, provider_type, technology_type, config) → Result[None]` | Valida que la configuración sea correcta para el tipo de Source |

**Validaciones que realiza**:
- `name` no está duplicado en el repositorio
- `provider_type` es un identificador conocido
- `technology_type` es compatible con `provider_type`
- `config` tiene los campos requeridos según `provider_type` y `technology_type`

---

### 7.4 Lo que NO es Domain Service

| Operación | ¿Por qué NO es Domain Service? | Dónde vive |
|-----------|-------------------------------|------------|
| Calcular si un Feed debe ejecutarse | Es responsabilidad de `SyncPolicy.is_due()` — es lógica de Value Object | `SyncPolicy` (VO) |
| Calcular delay de reintento | Es responsabilidad de `RetryPolicy.next_retry_delay()` | `RetryPolicy` (VO) |
| Fusionar categorías de Feed con grupo | Es responsabilidad de `Feed.effective_categories()` | `Feed` (Entity) |
| Decidir si un Feed debe pausarse | Es responsabilidad de `Feed.can_retry()` | `Feed` (Entity) |
| Generar batch_id | Es una función utilitaria sin estado | Función helper o llamada a UUIDProvider |

---

## 8. Repositories

### 8.1 Principios

- Son **interfaces** (Protocols en Python), no implementaciones
- Definen el **contrato de persistencia** que el dominio necesita
- NO mencionan SQL, Redis, archivos, ni ninguna tecnología
- Cada Aggregate Root tiene SU propio repositorio
- Category (Entity, no AR) también tiene repositorio

### 8.2 SourceRepository

| Método | Descripción |
|--------|-------------|
| `save(source) → None` | Persiste un Source (crea o actualiza) |
| `find_by_id(id) → Result[Source]` | Busca un Source por su ID |
| `find_by_name(name) → Result[Source]` | Busca un Source por su nombre único |
| `find_all() → list[Source]` | Retorna todos los Sources |
| `find_active() → list[Source]` | Retorna solo Sources activos |

### 8.3 FeedRepository

| Método | Descripción |
|--------|-------------|
| `save(feed) → None` | Persiste un Feed |
| `find_by_id(id) → Result[Feed]` | Busca un Feed por su ID |
| `find_by_source(source_id) → list[Feed]` | Retorna todos los Feeds de un Source |
| `find_by_group(group_id) → list[Feed]` | Retorna todos los Feeds de un FeedGroup |
| `find_by_url(source_id, url) → Result[Feed]` | Busca un Feed por URL dentro de un Source |
| `find_due(now, limit) → list[Feed]` | Retorna Feeds PULL que deben ejecutarse según su SyncPolicy |
| `find_by_status(is_active) → list[Feed]` | Retorna Feeds activos o inactivos |

### 8.4 FeedGroupRepository

| Método | Descripción |
|--------|-------------|
| `save(group) → None` | Persiste un FeedGroup |
| `find_by_id(id) → Result[FeedGroup]` | Busca un FeedGroup por su ID |
| `find_by_source(source_id) → list[FeedGroup]` | Retorna todos los grupos de un Source |

### 8.5 RawItemRepository

| Método | Descripción |
|--------|-------------|
| `save(item) → None` | Persiste un RawItem |
| `save_batch(items) → None` | Persiste múltiples RawItems atómicamente |
| `find_by_id(id) → Result[RawItem]` | Busca un RawItem por su ID |
| `find_by_feed(feed_id, page, size) → list[RawItem]` | Retorna RawItems de un Feed (paginado) |
| `find_by_batch(batch_id) → list[RawItem]` | Retorna todos los RawItems de un Batch |
| `find_by_hash(feed_id, hash) → Result[RawItem]` | Busca por hash (deduplicación) |
| `exists_by_external_id(feed_id, external_id) → bool` | Verifica si existe un RawItem con ese external_id en el Feed |
| `count_by_feed(feed_id) → int` | Cantidad de RawItems de un Feed |

### 8.6 CategoryRepository

| Método | Descripción |
|--------|-------------|
| `save(category) → None` | Persiste una Category |
| `find_by_id(id) → Result[Category]` | Busca una Category por su ID |
| `find_all() → list[Category]` | Retorna todas las categorías |
| `find_active() → list[Category]` | Retorna solo categorías activas |
| `find_by_parent(parent_id) → list[Category]` | Retorna subcategorías de una categoría |

---

## 9. Ports

### 9.1 TechnologyAdapter

**Propósito**: Abstraer el transporte de datos. Solo sabe de comunicación — recibe una URL/request, devuelve una respuesta cruda.

| Método | Descripción |
|--------|-------------|
| `technology_type → TechnologyType` | Propiedad que identifica qué tecnología implementa |
| `fetch(options) → Result[RawResponse]` | Ejecuta una petición y retorna la respuesta cruda |

**RawResponse** (Value Object del port):

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `body` | `bytes` | Cuerpo de la respuesta |
| `content_type` | `str` | Tipo MIME (application/json, application/rss+xml, etc.) |
| `status_code` | `int` | Código HTTP (o equivalente) |
| `headers` | `dict` | Headers de la respuesta |
| `fetched_at` | `datetime` | Momento de la obtención |

**FetchOptions** (Value Object del port):

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `url` | `str` | URL a consultar |
| `method` | `str` | Método HTTP (GET, POST, etc.) |
| `headers` | `dict` | Headers adicionales |
| `timeout` | `int` | Timeout en segundos |
| `max_redirects` | `int` | Máximo de redirecciones |

---

### 9.2 ProviderAdapter

**Propósito**: Coordinar la obtención de datos de un proveedor específico. Conecta el TechnologyAdapter con el Parser adecuado.

| Método | Descripción |
|--------|-------------|
| `provider_name → str` | Nombre del proveedor (ej: "reddit", "steam") |
| `technology_type → TechnologyType` | Tecnología que usa |
| `capabilities → set[ProviderCapability]` | Capacidades soportadas |
| `fetch(feed, context) → Result[list[RawItem]]` | Obtiene y parsea items de un Feed |
| `execute(operation, feed, params, context) → Result[list[RawItem]]` | Ejecuta una operación específica (SEARCH, TRENDING, etc.) |

---

### 9.3 Parser

**Propósito**: Transformar una respuesta cruda (RawResponse) en RawItems estructurados. No sabe de transporte — solo de formato.

| Método | Descripción |
|--------|-------------|
| `provider_name → str` | Proveedor para el que parsea |
| `parse(response, feed, batch_id) → Result[list[RawItem]]` | Transforma RawResponse en RawItems |

---

### 9.4 NormalizationPipelinePort

**Propósito**: Ejecutar el pipeline de normalización sobre RawItems para producir NormalizedItems.

| Método | Descripción |
|--------|-------------|
| `execute(items, feed) → Result[list[NormalizedItem]]` | Normaliza una lista de RawItems |

---

### 9.5 EventPublisher

**Propósito**: Publicar Integration Events para consumo de otros Bounded Contexts.

| Método | Descripción |
|--------|-------------|
| `publish(event) → Result[None]` | Publica un Integration Event en el bus |

---

### 9.6 SchedulerDriver (port de aplicación)

> Aunque vive en `domain/ports/`, es un port de **aplicación** — el dominio define el contrato, pero el scheduler es orquestación.

| Método | Descripción |
|--------|-------------|
| `get_due_feeds() → Result[list[FeedId]]` | Retorna los Feeds PULL que deben ejecutarse |
| `schedule_retry(feed_id, delay) → Result[None]` | Programa un reintento para un Feed |
| `pause_feed(feed_id, reason) → Result[None]` | Pausa un Feed (después de máximos reintentos) |
| `get_feed_status(feed_id) → Result[FeedStatus]` | Obtiene el estado operativo de un Feed |

---

### 9.7 Mapa Completo de Puertos

```
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION DOMAIN PORTS                        │
│                                                                  │
│  DOMINIO PURO:                                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ SourceRepository        ← Persistencia de Sources           │ │
│  │ FeedRepository          ← Persistencia de Feeds             │ │
│  │ FeedGroupRepository     ← Persistencia de FeedGroups        │ │
│  │ RawItemRepository       ← Persistencia de RawItems          │ │
│  │ CategoryRepository      ← Persistencia de Categories        │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  INFRAESTRUCTURA (contratos):                                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ TechnologyAdapter        ← Transporte (HTTP, RSS, WS)      │ │
│  │ ProviderAdapter          ← Orquestación proveedor específico│ │
│  │ Parser                   ← Parseo de respuestas            │ │
│  │ NormalizationPipelinePort← Normalización de contenido      │ │
│  │ EventPublisher           ← Publicación cross-BC            │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  APLICACIÓN (contratos en domain/ports/):                        │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ SchedulerDriver          ← Timing y scheduling              │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Casos de Uso del Dominio

### 10.1 Clasificación por Tipo

```
┌─────────────────────────────────────────────────────────────────┐
│                    CASOS DE USO DEL DOMINIO                      │
│                                                                  │
│  GESTIÓN DE CONFIGURACIÓN:                                       │
│  ├── Registrar Source                                           │
│  ├── Actualizar Source                                          │
│  ├── Desactivar Source                                          │
│  ├── Registrar Feed                                             │
│  ├── Configurar Feed (SyncPolicy, categorías)                   │
│  ├── Asignar Feed a FeedGroup                                   │
│  ├── Desasignar Feed de FeedGroup                               │
│  ├── Crear FeedGroup                                            │
│  ├── Actualizar FeedGroup                                       │
│  ├── Gestionar Categorías                                       │
│  │                                                               │
│  EJECUCIÓN:                                                     │
│  ├── Ejecutar Fetch (PULL)                                      │
│  ├── Procesar Webhook (PUSH)                                    │
│  ├── Procesar Stream (STREAM)                                   │
│  ├── Reintentar Fetch Fallido                                   │
│  │                                                               │
│  NORMALIZACIÓN:                                                 │
│  ├── Ejecutar Pipeline de Normalización                         │
│  ├── Publicar Items Normalizados                                │
│  │                                                               │
│  CONSULTA:                                                      │
│  ├── Obtener Estado de Source                                   │
│  ├── Listar Feeds por Source                                    │
│  ├── Obtener RawItems por Feed                                  │
│  ├── Obtener RawItems por Batch                                 │
│  ├── Consultar Estado de Salud de Feed                          │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 Flujos Principales Detallados

#### Registrar Source

```
Actor: Administrador del sistema (o CLI/API)
Disparador: Solicitud de registro de nueva fuente

Flujo:
  1. Recibir: name, provider_type, technology_type, config
  2. VALIDAR (SourceValidator):
     - name no existe ya
     - provider_type es conocido
     - technology_type es compatible
     - config es válida
  3. CREAR Source con estado activo
  4. PERSISTIR Source
  5. RETORNAR SourceId

Postcondiciones:
  - Source existe en el repositorio
  - Source está activa
  - No hay otro Source con el mismo name
```

#### Ejecutar Fetch (PULL)

```
Actor: Scheduler (o trigger manual)
Disparador: Scheduler determina que un Feed PULL está pendiente

Flujo:
  1. CARGAR Feed por feed_id
  2. VALIDAR que Feed está activo
  3. GENERAR batch_id
  4. PUBLICAR FeedFetchStarted
  5. PARA CADA intento (hasta max_retries):
     a. OBTENER ProviderAdapter según Source.provider_type
     b. EJECUTAR ProviderAdapter.fetch(feed, context)
     c. SI éxito → continuar
     d. SI fallo → REGISTRAR error, si puede reintentar → esperar backoff
  6. DEDUPLICAR: por external_id y hash contra RawItems existentes
  7. CREAR RawItems nuevos con el batch_id
  8. PERSISTIR RawItems (save_batch)
  9. ACTUALIZAR Feed.last_run con IngestionRun exitoso
  10. RESETEAR Feed.retry_count a 0
  11. PERSISTIR Feed
  12. PUBLICAR FeedFetchCompleted
  13. SI hay items nuevos → PUBLICAR NewItemsDetected
  14. RETORNAR IngestionRun

Postcondiciones:
  - RawItems nuevos persisten en el repositorio
  - Feed.last_run refleja la ejecución
  - Feed.retry_count se reseteó (si éxito)
  - Domain Events publicados

Si todos los reintentos fallan:
  - Feed.retry_count se incrementa
  - Si retry_count >= max_retries → Feed se pausa
  - PUBLICAR FeedFetchFailed
  - PUBLICAR FeedPaused (si corresponde)
  - RETORNAR IngestionRun con status FAILED
```

#### Procesar Webhook (PUSH)

```
Actor: Sistema externo (vía API endpoint)
Disparador: Source externo envía un POST a nuestro webhook endpoint

Flujo:
  1. RECIBIR payload del webhook + secret de validación
  2. VALIDAR webhook:
     - Verificar firma/secret contra Feed.sync.push_secret_ref
     - Identificar Feed por URL/webhook_id
  3. SI webhook inválido → RECHAZAR
  4. GENERAR batch_id
  5. PARSEAR payload a RawItems
  6. DEDUPLICAR contra RawItems existentes
  7. CREAR RawItems nuevos
  8. PERSISTIR RawItems
  9. PUBLICAR NewItemsDetected
  10. RETORNAR éxito

Postcondiciones:
  - RawItems nuevos persisten
  - No se modifica Feed.last_run (PUSH no altera el scheduler)
```

---

## 11. Invariantes

### 11.1 Invariantes de Source

| # | Invariante | Explicación |
|---|-----------|-------------|
| I-01 | `name` no puede ser vacío | Un Source debe tener un nombre identificable |
| I-02 | No pueden existir dos Sources con el mismo `name` | El nombre es el identificador semántico |
| I-03 | `provider_type` debe ser un identificador no vacío | Cada Source sabe qué tipo de proveedor es |
| I-04 | `technology_type` debe ser un valor válido de `TechnologyType` | RSS, HTTP o WebSocket |
| I-05 | `config` debe ser válida según `provider_type` y `technology_type` | La configuración debe ser coherente con el tipo |
| I-06 | No se puede desactivar un Source si tiene Feeds activos | Fuente inactiva no puede tener feeds consumiendo |

### 11.2 Invariantes de Feed

| # | Invariante | Explicación |
|---|-----------|-------------|
| I-07 | `url` no puede ser vacía | Un Feed siempre tiene una URL |
| I-08 | `url` debe ser única dentro del Source | No puede haber dos Feeds con la misma URL en el mismo Source |
| I-09 | `source_id` debe referenciar un Source existente | Un Feed no puede existir sin un Source |
| I-10 | `source_id` DEBE referenciar un Source activo | No se pueden crear Feeds en Sources inactivos |
| I-11 | Si `group_id` está presente, debe referenciar un FeedGroup existente | El grupo debe existir |
| I-12 | `sync` debe ser válida según las reglas de SyncPolicy | PULL requiere intervalo/cron, PUSH requiere secret, etc. |
| I-13 | `retry_count` se resetea a 0 después de un fetch exitoso | Los reintentos son consecutivos, no acumulativos en el tiempo |
| I-14 | Si `retry_count >= sync.retry.max_retries` y el fetch falla, el Feed se pausa | Protege contra consumo infinito de recursos |

### 11.3 Invariantes de FeedGroup

| # | Invariante | Explicación |
|---|-----------|-------------|
| I-15 | `name` debe ser único dentro del Source | No hay dos grupos con el mismo nombre en el mismo Source |
| I-16 | `source_id` debe referenciar un Source existente | Un grupo no puede existir sin un Source |
| I-17 | Eliminar un FeedGroup NO elimina sus Feeds | Los Feeds se desasignan, no se eliminan |

### 11.4 Invariantes de RawItem

| # | Invariante | Explicación |
|---|-----------|-------------|
| I-18 | **INMUTABLE** — Una vez creado, ningún atributo puede modificarse | RawItem es un registro de auditoría |
| I-19 | `external_id` + `feed_id` deben ser únicos | No puede haber dos RawItems con el mismo ID externo en el mismo Feed |
| I-20 | `hash` (SHA-256) debe ser único dentro del Feed | Deduplicación por contenido |
| I-21 | `feed_id` debe referenciar un Feed existente | Un RawItem siempre pertenece a un Feed |
| I-22 | `fetched_at` >= `published_at` si `published_at` está presente | No se puede obtener un item antes de su publicación |
| I-23 | `title` no puede ser vacío | Un item siempre tiene título |

### 11.5 Invariantes de Category

| # | Invariante | Explicación |
|---|-----------|-------------|
| I-24 | `slug` debe ser único | No hay dos categorías con el mismo slug |
| I-25 | `parent_id` no puede ser el mismo `id` | Una categoría no puede ser padre de sí misma |
| I-26 | La jerarquía no debe contener ciclos | No puede haber A→B→C→A |

### 11.6 Invariantes Operacionales

| # | Invariante | Explicación |
|---|-----------|-------------|
| I-27 | SyncPolicy.mode determina qué campos son requeridos | PULL requiere intervalo/cron; PUSH requiere secret; STREAM requiere heartbeat |
| I-28 | Un Feed PULL no puede ejecutarse si está inactivo | Feed desactivado → no fetch |
| I-29 | Un Feed PULL no puede ejecutarse si está pausado | Feed pausado requiere reactivación manual |
| I-30 | Dos Feeds del mismo Source pueden tener diferentes SyncPolicies | Cada Feed es independiente |
| I-31 | Un Batch contiene RawItems de UN SOLO Feed | No se mezclan feeds en un mismo batch |
| I-32 | Un RawItem pertenece a EXACTAMENTE UN Batch | No se reasigna de batch |

---

## 12. Diagramas Conceptuales

### 12.1 Modelo de Dominio General

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INGESTION DOMAIN                             │
│                                                                     │
│  ┌────────────────────────┐        ┌──────────────────────────┐    │
│  │       Source (AR)       │        │      FeedGroup (AR)       │    │
│  │────────────────────────│        │──────────────────────────│    │
│  │  SourceId              │        │  FeedGroupId              │    │
│  │  name: str             │──1:N──▶│  source_id: SourceId     │    │
│  │  provider_type: str    │        │  name: str                │    │
│  │  technology_type: enum │        │  is_active: bool          │    │
│  │  is_active: bool       │        │  default_sync: SyncPolicy │    │
│  │  config: SourceConfig  │        │  default_category: CatId  │    │
│  └────────────────────────┘        └──────────────────────────┘    │
│           │                              │                          │
│           │ 1:N                          │ 0..1 : N                 │
│           ▼                              ▼                          │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                     Feed (AR)                               │    │
│  │────────────────────────────────────────────────────────────│    │
│  │  FeedId | source_id | group_id? | url | label              │    │
│  │  is_active | sync: SyncPolicy | categories: list[CatId]    │    │
│  │  last_run: IngestionRun? | retry_count | next_retry_at?    │    │
│  └────────────────────────────────────────────────────────────┘    │
│           │                                                         │
│           │ 1:N                                                     │
│           ▼                                                         │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                   RawItem (AR) [INMUTABLE]                   │    │
│  │────────────────────────────────────────────────────────────│    │
│  │  RawItemId | feed_id | batch_id | external_id | hash       │    │
│  │  title | description | content | url | author              │    │
│  │  published_at? | fetched_at | metadata: dict               │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              Category (Entity) [COMPARTIDA]                 │    │
│  │────────────────────────────────────────────────────────────│    │
│  │  CategoryId | name | slug | parent_id? | is_active         │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 12.2 Value Objects y Relaciones

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VALUE OBJECTS                                │
│                                                                     │
│  SourceConfig              SyncPolicy                               │
│  ────────────              ──────────                               │
│  base_url: str             mode: SyncMode                           │
│  auth_method: str?         pull_interval: int?                      │
│  api_key_ref: str?         pull_cron: str?                          │
│  rate_limit: int?          push_secret_ref: str?                    │
│  timeout_seconds: int      stream_heartbeat: int?                   │
│  max_redirects: int        retry: RetryPolicy                       │
│  user_agent: str           timeout: int                             │
│                             max_items: int                          │
│                                                                    │
│  IngestionRun              RetryPolicy                             │
│  ────────────              ───────────                             │
│  status: IngestionStatus   max_retries: int                        │
│  items_count: int          backoff_multiplier: float               │
│  duration_ms: int          max_backoff_seconds: int                │
│  error_message: str?                                                │
│  started_at: datetime                                               │
│  finished_at: datetime                                              │
│                                                                     │
│  NormalizedItem            ProviderCapability (Enum)               │
│  ──────────────            ──────────────────────                  │
│  raw_item_id: RawItemId    FETCH, SEARCH, TRENDING                 │
│  title: str                STREAM, SUBMIT, RELEASES                │
│  content: str              VIDEOS                                  │
│  url: str                                                          │
│  author: str?             TechnologyType (Enum)                    │
│  language: str?            RSS, HTTP, WEBSOCKET                    │
│  quality_score: float?                                              │
│  categories: list[CatId]  SyncMode (Enum)                          │
│  metadata: dict            PULL, PUSH, STREAM, MANUAL              │
│                                                                    │
│                           IngestionStatus (Enum)                   │
│                            SUCCESS, FAILED, PARTIAL                │
└─────────────────────────────────────────────────────────────────────┘
```

### 12.3 Relaciones Aggregate ↔ Repository ↔ Port

```
┌──────────────────────────────────────────────────────────────────────┐
│              AGGREGATES          PERSISTENCE PORTS    INFRA PORTS    │
│                                                                      │
│  ┌──────────────┐            ┌───────────────────┐                  │
│  │   Source (AR) │──────────▶│  SourceRepository  │                  │
│  └──────────────┘            └───────────────────┘                  │
│                                                                      │
│  ┌──────────────┐            ┌───────────────────┐  ┌─────────────┐ │
│  │   Feed (AR)   │──────────▶│  FeedRepository   │  │Technology   │ │
│  └──────────────┘            └───────────────────┘  │Adapter      │ │
│                                                      └─────────────┘ │
│  ┌─────────────────┐       ┌──────────────────────┐                 │
│  │  FeedGroup (AR)  │──────▶│  FeedGroupRepository │  ┌─────────────┐ │
│  └─────────────────┘       └──────────────────────┘  │Provider     │ │
│                                                       │Adapter      │ │
│  ┌──────────────┐            ┌───────────────────┐  └─────────────┘ │
│  │  RawItem (AR) │──────────▶│  RawItemRepository │                 │
│  └──────────────┘            └───────────────────┘  ┌─────────────┐ │
│                                                      │Parser       │ │
│  ┌──────────────┐            ┌───────────────────┐  └─────────────┘ │
│  │  Category     │──────────▶│  CategoryRepo     │                 │
│  │  (Entity)     │            └───────────────────┘  ┌─────────────┐ │
│  └──────────────┘                                     │Normalization│ │
│                                                       │PipelinePort │ │
│  ┌──────────────────────────────────────────────┐   └─────────────┘ │
│  │      FeedOrchestrator (Domain Service)        │                  │
│  │                                              │  ┌─────────────┐ │
│  │  Usa: FeedRepository, RawItemRepository,     │  │Event        │ │
│  │       ProviderAdapter, Parser,               │  │Publisher    │ │
│  │       EventPublisher                         │  └─────────────┘ │
│  └──────────────────────────────────────────────┘                  │
└──────────────────────────────────────────────────────────────────────┘
```

### 12.4 Flujo de Fetch (PULL)

```
                        FEED PULL FLOW
                            │
                            ▼
                    ┌─────────────────┐
                    │  FetchTrigger    │ (Scheduler o manual)
                    │  feed_id         │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  FeedOrchestrator│
                    │  .execute()      │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────┐  ┌──────────────┐  ┌──────────────┐
     │ Load Feed  │  │ Publish      │  │ Get Provider │
     │ (FeedRepo) │  │ FetchStarted │  │ Adapter      │
     └─────┬──────┘  │ (DomainEv)   │  └──────┬───────┘
           │         └──────────────┘         │
           ▼                                  ▼
     ┌────────────┐                   ┌────────────────┐
     │ Validate   │                   │ ProviderAdapter│
     │ Feed active│                   │ .fetch()       │
     └─────┬──────┘                   └───────┬────────┘
           │                                  │
           │                     ┌────────────┼────────────┐
           │                     ▼            ▼            ▼
           │              ┌──────────┐ ┌──────────┐ ┌──────────┐
           │              │Technology│ │  Parser  │ │  Create  │
           │              │ Adapter  │ │ .parse() │ │ RawItems │
           │              │ .fetch() │ └──────────┘ └────┬─────┘
           │              └──────────┘                   │
           │                                             ▼
           │                                    ┌────────────────┐
           │                                    │ Dedup &        │
           │                                    │ Save RawItems  │
           │                                    │ (RawItemRepo)  │
           │                                    └───────┬────────┘
           │                                            │
           ├────────────────────────────────────────────┘
           ▼
     ┌──────────────────────────────────────┐
     │  Update Feed.last_run                │
     │  Reset retry_count                   │
     │  Save Feed (FeedRepo)                │
     └──────────────────┬───────────────────┘
                        ▼
              ┌──────────────────────┐
              │  Publish             │
              │  FetchCompleted      │
              │  (DomainEvent)       │
              │                      │
              │  If items > 0:       │
              │  Publish             │
              │  NewItemsDetected    │
              │  (DomainEvent)       │
              └──────────────────────┘
```

---

## 13. Roadmap de Implementación

### 13.1 División en Sprints

```
Sprint 3.1 ──→ Sprint 3.2 ──→ Sprint 3.3 ──→ Sprint 3.4 ──→ Sprint 3.5
    │              │              │              │              │
    ▼              ▼              ▼              ▼              ▼
 Ingestion      Value          Aggregates     Domain         Domain
 Identity       Objects        Source,        Events +       Services
 System                        Feed,          Ports          FeedOrchestrator
 (IDs)                         FeedGroup,                    SourceValidator
                               RawItem,
                               Category
```

### 13.2 Sprint 3.1 — Ingestion Identity System

**Objetivo**: Establecer los tipos de identidad específicos del BC Ingestion.

**Componentes**:
- `SourceId(EntityId)` — ID para Source
- `FeedId(EntityId)` — ID para Feed
- `FeedGroupId(EntityId)` — ID para FeedGroup
- `RawItemId(EntityId)` — ID para RawItem
- `CategoryId(EntityId)` — ID para Category
- `IngestionErrorCode(str, Enum)` — Códigos de error del BC

**Paquete**: `src/ingestion/domain/entities/ids.py`

**Dependencias**: Foundation v1.0 (EntityId, DomainError)

**Criterios de aceptación**:
- Todos los IDs heredan de EntityId
- `SourceId(x) != FeedId(x)` aunque tengan el mismo UUID interno
- Cada ID tiene `from_string()`, `generate()`, `__str__`
- `IngestionErrorCode` define códigos base del BC
- Tests existentes de Foundation siguen pasando
- Zero dependencias externas

---

### 13.3 Sprint 3.2 — Ingestion Value Objects

**Objetivo**: Implementar todos los Value Objects del dominio.

**Componentes**:
- `SyncMode(str, Enum)` — PULL, PUSH, STREAM, MANUAL
- `TechnologyType(str, Enum)` — RSS, HTTP, WEBSOCKET
- `IngestionStatus(str, Enum)` — SUCCESS, FAILED, PARTIAL
- `ProviderCapability(str, Enum)` — FETCH, SEARCH, TRENDING, etc.
- `SyncPolicy` — `@dataclass(frozen=True)` con validación por modo
- `IngestionRun` — `@dataclass(frozen=True)` con resultados de fetch
- `SourceConfig` — `@dataclass(frozen=True)` con configuración técnica
- `RetryPolicy` — `@dataclass(frozen=True)` con backoff exponencial
- `NormalizedItem` — `@dataclass(frozen=True)` con item procesado

**Paquete**: `src/ingestion/domain/value_objects/`

**Dependencias**: Sprint 3.1 (IDs), Foundation (ValueObject)

**Criterios de aceptación**:
- Todos los VOs son `@dataclass(frozen=True)` (inmutables)
- `SyncPolicy` valida campos requeridos según modo
- `SyncPolicy.is_due()` y `SyncPolicy.next_run()` implementados
- `RetryPolicy.next_retry_delay()` implementa backoff exponencial
- `IngestionRun` valida `finished_at >= started_at`
- `NormalizedItem` no tiene identidad
- Tests unitarios para cada VO cubriendo casos borde

---

### 13.4 Sprint 3.3 — Ingestion Aggregates

**Objetivo**: Implementar las entidades y aggregates del dominio.

**Componentes**:
- `Source(AggregateRoot)` — Origen externo de información
- `Feed(AggregateRoot)` — Stream configurable de ingesta
- `FeedGroup(AggregateRoot)` — Agrupación operativa de Feeds
- `RawItem(AggregateRoot)` — Item crudo e inmutable
- `Category(Entity)` — Clasificación temática
- Domain exceptions del BC (subclases de DomainError)

**Paquete**: `src/ingestion/domain/entities/`

**Dependencias**: Sprint 3.1 (IDs), Sprint 3.2 (VOs), Foundation (AggregateRoot, Entity, DomainError)

**Criterios de aceptación**:
- Source, Feed, FeedGroup, RawItem heredan de AggregateRoot
- Category hereda de Entity
- RawItem es inmutable después de construcción
- Feed tiene `record_run()`, `record_failure()`, `can_retry()`, `effective_categories()`
- Source tiene `activate()`, `deactivate()` con validación de Feeds activos
- FeedGroup tiene `set_default_sync()`, `set_default_category()`
- Cada AR tiene igualdad por identidad (heredada)
- Cada AR registra DomainEvents vía `register_event()` / `pull_events()`
- Invariantes documentadas se verifican en tests

---

### 13.5 Sprint 3.4 — Domain Events + Domain Ports

**Objetivo**: Implementar los Domain Events y los puertos del dominio.

**Componentes**:
- Domain Events:
  - `FeedFetchStarted(DomainEvent)`
  - `FeedFetchCompleted(DomainEvent)`
  - `FeedFetchFailed(DomainEvent)`
  - `FeedPaused(DomainEvent)`
  - `NewItemsDetected(DomainEvent)`
- Integration Events:
  - `NewRawItemsAvailable(IntegrationEvent)`
- Repository Ports (Protocols):
  - `SourceRepository`
  - `FeedRepository`
  - `FeedGroupRepository`
  - `RawItemRepository`
  - `CategoryRepository`
- Infrastructure Ports (Protocols):
  - `TechnologyAdapter`
  - `ProviderAdapter`
  - `Parser`
  - `NormalizationPipelinePort`
  - `EventPublisher`
  - `SchedulerDriver`

**Paquetes**:
- `src/ingestion/domain/events/`
- `src/ingestion/domain/ports/`

**Dependencias**: Sprint 3.3 (Aggregates), Foundation (DomainEvent, IntegrationEvent)

**Criterios de aceptación**:
- Cada DomainEvent tiene event_id, event_name, occurred_at
- Cada DomainEvent transporta payload específico del dominio
- NewRawItemsAvailable tiene event_version, source_boundary, correlation_id
- Todos los repositorios son Protocols (no implementaciones)
- Todos los ports de infraestructura son Protocols
- Ningún port menciona SQL, Redis, HTTP, ni infraestructura concreta
- Tests de eventos verifican construcción y propiedades

---

### 13.6 Sprint 3.5 — Domain Services

**Objetivo**: Implementar los servicios de dominio puros.

**Componentes**:
- `FeedOrchestrator` — Coordina fetch → parse → dedup → persist → notify
- `SourceValidator` — Valida configuración de Source

**Paquete**: `src/ingestion/domain/services/`

**Dependencias**: Sprint 3.4 (Events + Ports), Sprint 3.3 (Aggregates), Sprint 3.2 (VOs)

**Criterios de aceptación**:
- `FeedOrchestrator.execute()` cubre el flujo completo de fetch
- `FeedOrchestrator` retorna `Result[IngestionRun]`
- `FeedOrchestrator` publica DomainEvents en cada etapa
- `FeedOrchestrator` maneja reintentos vía RetryPolicy
- `FeedOrchestrator` pausa Feed si supera max_retries
- `SourceValidator.validate()` retorna `Result[None]`
- `SourceValidator` verifica unicidad de nombre, compatibilidad de tipos, validez de config
- Ambos servicios son stateless (toda la configuración viene de los aggregates/ports)
- Tests con mocks de repositorios y puertos

---

### 13.7 Dependencias entre Sprints

```
Foundation v1.0
    │
    ▼
Sprint 3.1 (IDs)  ← Foundation: EntityId, DomainError
    │
    ▼
Sprint 3.2 (VOs)  ← Foundation: ValueObject; Sprint 3.1: IDs
    │
    ▼
Sprint 3.3 (Aggregates)  ← Foundation: Entity, AggregateRoot, DomainError
    │                         Sprint 3.1: IDs
    │                         Sprint 3.2: VOs
    │
    ├──────────────────┐
    ▼                  ▼
Sprint 3.4a         Sprint 3.4b
(Domain Events)     (Domain Ports)
    │                  │
    └──────┬───────────┘
           ▼
    Sprint 3.5 (Services)  ← TODO LO ANTERIOR
```

**Nota**: Sprint 3.4a y 3.4b NO dependen el uno del otro — pueden implementarse en paralelo.

---

### 13.8 Criterios de Aceptación Generales del Epic 3

- [ ] Todos los IDs del BC definidos y tipados
- [ ] Todos los VOs implementados con inmutabilidad y validación
- [ ] Todos los Aggregates implementados con sus invariantes
- [ ] Todos los Domain Events definidos con payload específico
- [ ] Todos los Ports definidos como Protocols
- [ ] Todos los Domain Services implementados y testeables con mocks
- [ ] Ninguna dependencia externa (stdlib + Foundation solamente)
- [ ] Foundation NO se modifica — todo es aditivo en Ingestion
- [ ] Domain Events NO sustituyen Integration Events (son conceptos diferentes)
- [ ] Repositories NO mencionan infraestructura
- [ ] Ninguna entidad conoce de HTTP, DB, o cualquier tecnología externa
- [ ] Tests pasando para todos los componentes

---

*Documento de diseño de dominio preparado por el Architecture Review Board.*
*Estado: DRAFT — Pendiente de aprobación.*
*Próximo paso: Revisión ARB → Aprobación → Inicio Sprint 3.1.*
