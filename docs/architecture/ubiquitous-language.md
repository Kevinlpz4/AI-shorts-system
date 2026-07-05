# Ubiquitous Language Dictionary — Ingestion Bounded Context

> **Documento de Lenguaje Ubicuo del Bounded Context Ingestion**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-03
> Basado en: Foundation v1.0 STABLE (FROZEN), Sprint 3.1 Design
>
> **Todo el equipo y el código DEBEN usar estos términos de forma consistente.**
> Si un término no está aquí, no pertenece al dominio de Ingestion.

---

## Tabla de Contenidos

1. [Aggregate Roots](#1-aggregate-roots)
2. [Entities](#2-entities)
3. [Value Objects](#3-value-objects)
4. [Enums](#4-enums)
5. [Domain Events](#5-domain-events)
6. [Repository Ports](#6-repository-ports)
7. [Conceptos](#7-conceptos)
8. [Términos Excluidos del Dominio](#8-términos-excluidos-del-dominio)

---

## 1. Aggregate Roots

### NewsSource

| Campo | Valor |
|-------|-------|
| **Definición** | Un origen externo de información — una plataforma, sitio web o API desde la cual se obtiene contenido. Es la entidad de configuración de más alto nivel en el BC Ingestion. |
| **Tipo** | Aggregate Root |
| **Identidad** | `SourceId` |
| **Responsabilidad** | Representar, configurar y controlar el ciclo de vida de una fuente externa de información. |
| **Ciclo de vida** | Creado → Activo (`is_active = True`) → Inactivo (`is_active = False`) |
| **Cardinalidades** | 1 NewsSource → N Feeds, 1 NewsSource → N Categories, 1 NewsSource → M Topics |
| **Ejemplos** | "Reddit", "Steam News", "Hacker News", "GitHub Trends", "YouTube" |
| **Reglas semánticas** | • El nombre debe ser único globalmente<br>• Una URL base válida es requerida<br>• La verificación de Feeds activos (desactivación/activación) es regla de Application Layer (AL-01, AL-02) — no cruza frontera del AR |
| **Eventos que emite** | `SourceEnabled` (al activarse), `SourceDisabled` (al desactivarse) |
| **Repositorio** | `NewsSourceRepository` |

---

### Feed

| Campo | Valor |
|-------|-------|
| **Definición** | Un stream específico y configurable de información dentro de un NewsSource. Es la unidad ejecutable de ingesta con reglas de reintentos, pausa automática y categorización. |
| **Tipo** | Aggregate Root |
| **Identidad** | `FeedId` |
| **Responsabilidad** | Ejecutar la obtención de contenido desde un endpoint específico, manejar reintentos, auto-pausa al alcanzar el límite de fallos, y gestionar categorías/topics asociados. |
| **Ciclo de vida** | Creado → Activo (fetch habilitado) → Pausado (por exceso de errores) → Inactivo (deshabilitado manualmente) |
| **Cardinalidades** | N Feeds → 1 NewsSource, 1 Feed → N Categories, 1 Feed → M Topics, 1 Feed → N RawArticles |
| **Ejemplos** | Subreddit "r/programming" en Reddit, feed "top" en Hacker News, canal de YouTube |
| **Reglas semánticas** | • Pertenece EXACTAMENTE a un NewsSource<br>• La URL debe ser única dentro del NewsSource<br>• Se pausa automáticamente al alcanzar el máximo de reintentos<br>• No puede ejecutar fetch si está inactivo o pausado<br>• `retry_count` se resetea a 0 después de un fetch exitoso<br>• La verificación de NewsSource activo al crear es regla de Application Layer (AL-04) |
| **Eventos que emite** | `RawArticleCollected` (al registrar una colección exitosa con artículos nuevos) |
| **Repositorio** | `FeedRepository` |

---

### RawArticle

| Campo | Valor |
|-------|-------|
| **Definición** | Representación inmutable de un artículo crudo obtenido desde un Feed. Es un registro de auditoría — una vez creado, nunca cambia. Es Aggregate Root por razones de volumen (pueden haber millones de instancias). |
| **Tipo** | Aggregate Root (técnicamente hereda de `Entity`, documentado como AR — ver ADR-023) |
| **Identidad** | `RawArticleId` |
| **Responsabilidad** | Almacenar de forma permanente e inmutable el contenido crudo obtenido de un Feed, con todos sus metadatos originales, para propósitos de auditoría, deduplicación y procesamiento posterior. |
| **Ciclo de vida** | Creado → (inmutable) |
| **Cardinalidades** | N RawArticles → 1 Feed |
| **Ejemplos** | Un post de Reddit, un artículo de Hacker News, una release de GitHub, un video de YouTube |
| **Reglas semánticas** | • **INMUTABLE** — ningún atributo puede modificarse después de creación<br>• La combinación `external_id + feed_id` debe ser única (deduplicación por ID externo)<br>• `content_hash` (SHA-256) debe ser único dentro del Feed (deduplicación por contenido)<br>• `fetched_at` >= `published_at` si `published_at` está presente<br>• `title` no puede ser vacío (validado por ArticleTitle VO)<br>• `url` debe ser una URL válida (validado por ArticleUrl VO) |
| **Eventos que emite** | Ninguno (es inmutable, no emite eventos) |
| **Repositorio** | `RawArticleRepository` |

---

## 2. Entities

### Category

| Campo | Valor |
|-------|-------|
| **Definición** | Clasificación temática que permite organizar, filtrar y agrupar contenido. Puede tener una jerarquía opcional de padre-hijo (subcategorías). |
| **Tipo** | Entity (NO es Aggregate Root) |
| **Identidad** | `CategoryId` |
| **Responsabilidad** | Proveer una taxonomía de temas para clasificar NewsSources, Feeds y RawArticles. Las categorías son referenciadas por ID desde múltiples agregados. |
| **Ciclo de vida** | Creada → Activa → Inactiva (desactivar una categoría padre cascada a subcategorías) |
| **Cardinalidades** | 1 Category → 0..N subcategorías (vía `parent_id`), N NewsSources → N Categories, N Feeds → N Categories |
| **Ejemplos** | "Technology", "Science", "Gaming", "World News", "Sports" |
| **Reglas semánticas** | • `slug` debe ser único globalmente<br>• Una categoría no puede ser padre de sí misma<br>• La jerarquía no debe contener ciclos (A→B→C→A es inválido)<br>• Desactivar una categoría padre desactiva sus subcategorías activas<br>• Es referenciada por ID — no incrustada |
| **Repositorio** | `CategoryRepository` |

---

### Topic

| Campo | Valor |
|-------|-------|
| **Definición** | Un tema o tópico de interés que guía la ingesta y clasificación de contenido. Representa un área temática específica (ej: "Artificial Intelligence", "Climate Change"). |
| **Tipo** | Entity (NO es Aggregate Root) |
| **Identidad** | `TopicId` |
| **Responsabilidad** | Proveer una lista curada de temas de interés que pueden ser asignados a NewsSources, Feeds y (futuramente) RawArticles para guiar la selección y clasificación de contenido. |
| **Ciclo de vida** | Creado → Activo → Inactivo |
| **Cardinalidades** | N NewsSources → M Topics, N Feeds → M Topics, N RawArticles → M Topics (futuro) |
| **Ejemplos** | "Artificial Intelligence", "Climate Change", "Quantum Computing", "World Politics" |
| **Reglas semánticas** | • El nombre debe ser único globalmente<br>• El nombre no puede ser vacío<br>• Es referenciado por ID — no incrustado<br>• NO es un VO porque necesita identidad para ser referenciado y poder renombrarse centralizadamente |
| **Repositorio** | `TopicRepository` |

---

## 3. Value Objects

Todos los Value Objects son `@dataclass(frozen=True)` (inmutables) con validación en `__post_init__`.

### SourceUrl

| Campo | Valor |
|-------|-------|
| **Definición** | URL base de un NewsSource. Representa el endpoint raíz de la plataforma externa. |
| **Tipo** | Value Object |
| **Atributo** | `value: str` |
| **Validaciones** | No vacío, esquema http/https, formato URL válido, sin fragmentos, sin caracteres de control |
| **Comportamiento** | `normalized()` — retorna URL normalizada (scheme lowercase, sin trailing slash) |
| **Errores** | `INVALID_SOURCE_URL` si la validación falla |
| **Ejemplos** | `https://www.reddit.com`, `https://news.ycombinator.com` |

### ArticleUrl

| Campo | Valor |
|-------|-------|
| **Definición** | URL canónica de un artículo individual obtenido de un Feed. Apunta al contenido original en la fuente externa. |
| **Tipo** | Value Object |
| **Atributo** | `value: str` |
| **Validaciones** | No vacío, http/https, formato URL válido, sin espacios ni caracteres de control |
| **Comportamiento** | `normalized()` — URL canónica; `domain()` — extrae dominio (ej: "reddit.com") |
| **Errores** | `INVALID_ARTICLE_URL` si la validación falla |
| **Ejemplos** | `https://www.reddit.com/r/programming/comments/abc123/` |

### ArticleTitle

| Campo | Valor |
|-------|-------|
| **Definición** | Título de un artículo obtenido de un Feed. Es la representación textual del encabezado del contenido. |
| **Tipo** | Value Object |
| **Atributo** | `value: str` |
| **Validaciones** | No vacío, máximo 500 caracteres, sin caracteres de control, trim automático |
| **Ejemplos** | "New AI Breakthrough Achieves Human-Level Reasoning", "Cómo aprender DDD en 30 días" |

### Author

| Campo | Valor |
|-------|-------|
| **Definición** | Nombre del creador o autor de un artículo. Es opcional (se representa como `Author \| None` en RawArticle). |
| **Tipo** | Value Object |
| **Atributo** | `value: str` |
| **Validaciones** | Si se provee: no vacío, máximo 200 caracteres, sin caracteres de control, trim y compresión de espacios |
| **Comportamiento** | `is_known()` — retorna `False` si es "unknown", "anonymous", etc. |
| **Ejemplos** | "Jane Doe", "John Smith", `None` (desconocido) |

### Language

| Campo | Valor |
|-------|-------|
| **Definición** | Código de idioma ISO 639-1 que identifica el lenguaje del contenido de un artículo o feed. |
| **Tipo** | Value Object |
| **Atributo** | `code: str` |
| **Validaciones** | Código ISO 639-1 válido (2 letras), lista permitida: en, es, fr, de, pt, it, ja, ko, zh, ru, ar. Normalización a lowercase. |
| **Comportamiento** | `display_name()` — nombre legible; `is_rtl()` — True para árabe, hebreo |
| **Errores** | `INVALID_LANGUAGE` si el código no es válido |
| **Ejemplos** | `Language("en")`, `Language("es")`, `Language("fr")` |

### SourceType

| Campo | Valor |
|-------|-------|
| **Definición** | Clasificación del tipo de plataforma externa que un NewsSource representa. Determina qué tecnología de fetch y parseo se utilizará. |
| **Tipo** | Enum (Value Object) |
| **Valores** | `RSS`, `API`, `SOCIAL_MEDIA`, `NEWSLETTER` |
| **Nota** | Es un enum unificado que reemplaza al par `provider_type` + `technology_type` del diseño anterior. Simplifica el modelo. |
| **Ejemplos** | `SourceType.RSS` para un blog con feed RSS, `SourceType.API` para Steam News, `SourceType.SOCIAL_MEDIA` para Reddit |

### CategoryName

| Campo | Valor |
|-------|-------|
| **Definición** | Nombre legible de una categoría. Es la representación textual de la clasificación temática. |
| **Tipo** | Value Object |
| **Atributo** | `value: str` |
| **Validaciones** | No vacío, máximo 100 caracteres, solo letras/espacios/números/guiones/guiones bajos, trim automático |
| **Ejemplos** | `CategoryName("Technology")`, `CategoryName("Science")`, `CategoryName("Gaming")` |

### SyncPolicy

| Campo | Valor |
|-------|-------|
| **Definición** | Configuración de sincronización de un Feed. Define cómo, cuándo y con qué política de reintentos se ejecuta la obtención de contenido. |
| **Tipo** | Value Object (configuración pura — SIN lógica de timing) |
| **Atributos** | `mode: SyncMode`, `interval_minutes: int \| None`, `max_retries: int` (default 3), `backoff_multiplier: float` (default 2.0), `max_backoff_minutes: int` (default 60), `timeout_seconds: int` (default 30), `max_items_per_run: int` (default 100) |
| **Validaciones** | Modo PULL requiere `interval_minutes`; modo PUSH/STREAM/MANUAL no requiere intervalo |
| **Nota** | NO incluye `is_due()` ni `next_run()` — son responsabilidad del scheduler (Application Layer). |
| **Ejemplos** | `SyncPolicy(mode=PULL, interval_minutes=30, max_retries=5)` |

#### SyncMode

| Campo | Valor |
|-------|-------|
| **Definición** | Modo de sincronización que determina cómo se obtienen los datos de un Feed. |
| **Tipo** | Enum (Value Object) |
| **Valores** | `PULL` (el sistema consulta periódicamente), `PUSH` (el source notifica al sistema vía webhook), `STREAM` (conexión persistente), `MANUAL` (solo bajo demanda) |

---

## 4. Enums

### IngestionStatus

| Campo | Valor |
|-------|-------|
| **Definición** | Estado resultante de una ejecución de fetch para un Feed. |
| **Tipo** | Enum (Value Object, vive en Application Layer) |
| **Valores** | `SUCCESS` (completado sin errores), `FAILED` (error irrecuperable), `PARTIAL` (algunos items obtenidos, otros fallaron) |

---

## 5. Domain Events

### RawArticleCollected

| Campo | Valor |
|-------|-------|
| **Definición** | Evento de dominio que indica que uno o más RawArticles han sido recolectados exitosamente de un Feed después del proceso de deduplicación. |
| **Cuándo ocurre** | Cuando `Feed.record_collection()` es llamado con count > 0 |
| **Payload** | `feed_id: FeedId`, `batch_id: UUID`, `count: int`, `collected_at: datetime` |
| **Publisher** | `Feed` (AR) |
| **Consumidor** | Application Service → Normalization Pipeline |
| **Categoría** | Intra-BC Domain Event |

### SourceEnabled

| Campo | Valor |
|-------|-------|
| **Definición** | Evento de dominio que indica que un NewsSource ha sido habilitado para ingesta. |
| **Cuándo ocurre** | Cuando `NewsSource.enable()` es llamado exitosamente |
| **Payload** | `source_id: SourceId`, `enabled_at: datetime` |
| **Publisher** | `NewsSource` (AR) |
| **Consumidor** | Application Service → SchedulerDriver, Monitor |
| **Categoría** | Intra-BC Domain Event |

### SourceDisabled

| Campo | Valor |
|-------|-------|
| **Definición** | Evento de dominio que indica que un NewsSource ha sido deshabilitado y su ingesta debe detenerse. |
| **Cuándo ocurre** | Cuando `NewsSource.disable(reason)` es llamado exitosamente |
| **Payload** | `source_id: SourceId`, `reason: str`, `disabled_at: datetime` |
| **Publisher** | `NewsSource` (AR) |
| **Consumidor** | Application Service → SchedulerDriver (detiene polling), AlertService, Logger |
| **Categoría** | Intra-BC Domain Event |

---

## 6. Repository Ports

### NewsSourceRepository

| Campo | Valor |
|-------|-------|
| **Definición** | Puerto de persistencia para el Aggregate Root NewsSource. Define el contrato para guardar y recuperar fuentes externas. |
| **Tipo** | Protocol (interface de dominio) |
| **Métodos** | `save()`, `find_by_id()`, `find_by_name()`, `find_all()`, `find_active()`, `exists_by_name()` |
| **Entidad** | NewsSource |

### FeedRepository

| Campo | Valor |
|-------|-------|
| **Definición** | Puerto de persistencia para el Aggregate Root Feed. Define el contrato para guardar y recuperar streams configurables de ingesta. |
| **Tipo** | Protocol (interface de dominio) |
| **Métodos** | `save()`, `find_by_id()`, `find_by_source()`, `find_by_url()`, `find_active_by_source()`, `exists_by_source_and_url()`, `count_active_by_source()` |
| **Entidad** | Feed |

### RawArticleRepository

| Campo | Valor |
|-------|-------|
| **Definición** | Puerto de persistencia para el Aggregate Root RawArticle. Define el contrato para guardar y recuperar artículos crudos inmutables. |
| **Tipo** | Protocol (interface de dominio) |
| **Métodos** | `save()`, `save_batch()`, `find_by_id()`, `find_by_feed()`, `find_by_hash()`, `exists_by_url()`, `exists_by_hash()`, `count_by_feed()` |
| **Entidad** | RawArticle |

### CategoryRepository

| Campo | Valor |
|-------|-------|
| **Definición** | Puerto de persistencia para la Entity Category. Define el contrato para gestionar la taxonomía de categorías. |
| **Tipo** | Protocol (interface de dominio) |
| **Métodos** | `save()`, `find_by_id()`, `find_by_slug()`, `find_all()`, `find_active()`, `find_by_parent()`, `exists_by_slug()` |
| **Entidad** | Category |

### TopicRepository

| Campo | Valor |
|-------|-------|
| **Definición** | Puerto de persistencia para la Entity Topic. Define el contrato para gestionar la lista de temas de interés. |
| **Tipo** | Protocol (interface de dominio) |
| **Métodos** | `save()`, `find_by_id()`, `find_by_name()`, `find_all()`, `find_active()`, `exists_by_name()` |
| **Entidad** | Topic |

---

## 7. Conceptos

### Batch

| Campo | Valor |
|-------|-------|
| **Definición** | Agrupación conceptual de RawArticles obtenidos en una misma ejecución de fetch. NO es una entidad con identidad propia — es un conjunto de RawArticles que comparten el mismo `batch_id`. |
| **Tipo** | Concepto (identificador UUID) |
| **Representación** | `batch_id: UUID` — no tiene tipo propio, es un UUID simple |
| **Propósito** | Trazabilidad: vincula RawArticles con su ejecución de fetch. Recovery: permite reprocesar un batch completo. Publicación: notifica a Research BC sobre nuevos items. |
| **Reglas semánticas** | • Un Batch representa una ejecución atómica de fetch<br>• Todos los RawArticles del batch se obtuvieron en la misma operación<br>• El `batch_id` se genera al inicio del fetch y se asigna a todos los RawArticles producidos<br>• Un Batch contiene RawArticles de UN SOLO Feed |

### IngestionRun (Application Layer)

| Campo | Valor |
|-------|-------|
| **Definición** | Resultado de una ejecución de fetch para un Feed. Captura métricas y estado de la operación. |
| **Tipo** | Value Object (vive en Application Layer, no en Domain Core) |
| **Atributos** | `status: IngestionStatus`, `items_count: int`, `duration_ms: int`, `error_message: str \| None`, `started_at: datetime`, `finished_at: datetime` |
| **Nota** | No pertenece al Domain Core del Sprint 3.1. Se menciona porque Feed lo referencia indirectamente a través de `record_collection()`. |

---

## 8. Términos Excluidos del Dominio

| Término | ¿Por qué NO está en dominio? | Dónde vive |
|---------|------------------------------|------------|
| **FeedGroup** | Agrupación operativa sin reglas de negocio reales. YAGNI. | Application Layer / Infraestructura |
| **NormalizedItem** | Es el resultado del pipeline de normalización, que ocurre en Application Layer. | Application Layer |
| **TechnologyType** | Reemplazado por SourceType unificado. | — (eliminado) |
| **ProviderCapability** | Especificación de capacidades del adaptador de infraestructura, no del dominio. | Infraestructura |
| **SourceConfig** | Configuración técnica (auth, rate limiting) es responsabilidad de infraestructura. No pertenece al dominio. | Infraestructura |
| **RetryPolicy** | Aplanado dentro de SyncPolicy como atributos directos (max_retries, backoff, etc.). | — (integrado en SyncPolicy) |
| **IngestionRun** | Value Object de Application Layer. Feed lo referencia pero no vive en Domain Core. | Application Layer |
| **Scheduler** | Es orquestación temporal, no lógica de dominio. | Application Layer |
| **FetchOrchestrator** | Orquestación cross-AR que pertenece a Application Layer. | Application Layer |
