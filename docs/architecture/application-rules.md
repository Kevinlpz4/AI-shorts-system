# AL Rules Implementation Design — Ingestion Bounded Context

> **Implementación de las 5 reglas cross-AR (AL-01 a AL-05) en la capa de aplicación**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-03

---

## 1. ¿Por qué estas reglas pertenecen a Application Layer?

Cada regla AL cruza la frontera de al menos un Aggregate Root. En DDD, un AR solo puede garantizar invariantes dentro de su propia frontera. Cuando se necesita verificar el estado de un AR diferente, la verificación debe hacerse en la capa de aplicación.

### Principio

> **Un Aggregate Root NO puede cargar otro Aggregate Root para verificar una invariante.**
> Si lo hiciera, violaría la independencia transaccional de los ARs y crearía dependencias de carga imposibles de escalar.

| Regla | AR Origen | AR Destino | ¿Por qué no es dominio? |
|-------|-----------|------------|------------------------|
| AL-01 | NewsSource | Feed | NewsSource no tiene acceso a FeedRepository |
| AL-02 | NewsSource | Feed | NewsSource no tiene acceso a FeedRepository |
| AL-03 | Feed | NewsSource | Feed no puede cargar un NewsSource para verificar existencia |
| AL-04 | Feed | NewsSource | Feed no conoce el estado de NewsSource |
| AL-05 | RawArticle | Feed | RawArticle es inmutable y no conoce otros ARs |

---

## 2. AL-01: NewsSource no puede desactivarse si tiene Feeds activos

### Implementación

```python
# En SourceService.execute_disable_source()

def execute_disable_source(self, cmd: DisableSourceCommand) -> Result[SourceDetailDTO]:
    # 1. Cargar el NewsSource
    source_result = self._source_repo.find_by_id(cmd.source_id)
    if source_result.is_failure:
        return Result.failure(source_result.error)

    source = source_result.value

    # 2. AL-01: Verificar Feeds activos
    active_feed_count = self._feed_repo.count_active_by_source(cmd.source_id)
    if active_feed_count > 0:
        return Result.failure(Error(
            code=IngestionErrorCode.HAS_ACTIVE_FEEDS,
            message=f"NewsSource '{source.name}' has {active_feed_count} active feed(s). "
                    f"Disable or remove all active feeds before disabling the source.",
        ))

    # 3. Llamar al dominio
    source.disable(reason=cmd.reason)
    # ...
```

### ¿Dónde ocurre?

| Aspecto | Detalle |
|---------|--------|
| **Service** | `SourceService.execute_disable_source()` |
| **Repositorio usado** | `FeedRepository.count_active_by_source()` |
| **Antes o después del método de dominio?** | **ANTES** de llamar `source.disable()`. |
| **Error** | `Result.failure(Error(HAS_ACTIVE_FEEDS, message))` |
| **Ventana de inconsistencia** | Mínima: entre count y disable, otro proceso podría crear un Feed. Aceptable por consistencia eventual. |

---

## 3. AL-02: NewsSource solo puede activarse si tiene al menos un Feed activo

### Implementación

```python
# En SourceService.execute_enable_source()

def execute_enable_source(self, cmd: EnableSourceCommand) -> Result[SourceDetailDTO]:
    # 1. Cargar el NewsSource
    source_result = self._source_repo.find_by_id(cmd.source_id)
    if source_result.is_failure:
        return Result.failure(source_result.error)

    source = source_result.value

    # 2. AL-02: Verificar que tiene al menos un Feed activo
    active_feed_count = self._feed_repo.count_active_by_source(cmd.source_id)
    if active_feed_count == 0:
        return Result.failure(Error(
            code=IngestionErrorCode.NEWS_SOURCE_INACTIVE,  # o INVALID_STATE
            message=f"NewsSource '{source.name}' has no active feeds. "
                    f"At least one active feed is required before enabling the source.",
        ))

    # 3. Llamar al dominio
    source.enable()
    # ...
```

### ¿Dónde ocurre?

| Aspecto | Detalle |
|---------|--------|
| **Service** | `SourceService.execute_enable_source()` |
| **Repositorio usado** | `FeedRepository.count_active_by_source()` |
| **Antes o después del método de dominio?** | **ANTES** de llamar `source.enable()`. |
| **Error** | `Result.failure(Error(NEWS_SOURCE_INACTIVE, message))` |

---

## 4. AL-03: source_id debe referenciar un NewsSource existente al crear Feed

### Implementación

```python
# En FeedService.execute_register_feed()

def execute_register_feed(self, cmd: RegisterFeedCommand) -> Result[FeedDetailDTO]:
    # 1. AL-03: Verificar que el NewsSource existe
    source_result = self._source_repo.find_by_id(cmd.source_id)
    if source_result.is_failure:
        return Result.failure(Error(
            code=IngestionErrorCode.NEWS_SOURCE_NOT_FOUND,
            message=f"NewsSource with id '{cmd.source_id}' does not exist.",
        ))

    source = source_result.value

    # 2. AL-04: Verificar que el NewsSource está activo (ver sección 5)
    if not source.is_active:
        return Result.failure(...)

    # 3. Continuar con la creación del Feed
    # ...
```

### ¿Dónde ocurre?

| Aspecto | Detalle |
|---------|--------|
| **Service** | `FeedService.execute_register_feed()` |
| **Repositorio usado** | `NewsSourceRepository.find_by_id()` |
| **Antes o después del método de dominio?** | **ANTES** de construir el Feed (no hay método de dominio que llamar). |
| **Error** | `Result.failure(Error(NEWS_SOURCE_NOT_FOUND, message))` |

---

## 5. AL-04: No crear Feed bajo un NewsSource inactivo

### Implementación

```python
# En FeedService.execute_register_feed(), después de AL-03

    # 2. AL-04: Verificar que el NewsSource está activo
    if not source.is_active:
        return Result.failure(Error(
            code=IngestionErrorCode.NEWS_SOURCE_INACTIVE,
            message=f"NewsSource '{source.name}' is inactive. "
                    f"Feeds cannot be created under an inactive source.",
        ))
```

### ¿Dónde ocurre?

| Aspecto | Detalle |
|---------|--------|
| **Service** | `FeedService.execute_register_feed()` |
| **Dato usado** | `source.is_active` (ya cargado en AL-03) |
| **Antes o después del método de dominio?** | **ANTES** de construir el Feed. |
| **Error** | `Result.failure(Error(NEWS_SOURCE_INACTIVE, message))` |

**Nota**: AL-03 y AL-04 se verifican en el mismo paso (cargamos el source para ambas). No hay llamada extra al repositorio — reutilizamos el source cargado.

---

## 6. AL-05: feed_id debe referenciar un Feed existente al crear RawArticle

### Implementación

```python
# En ArticleService.execute_create_article()

def execute_create_article(self, cmd: CreateRawArticleCommand) -> Result[RawArticleDetailDTO]:
    # 1. AL-05: Verificar que el Feed existe
    feed_result = self._feed_repo.find_by_id(cmd.feed_id)
    if feed_result.is_failure:
        return Result.failure(Error(
            code=IngestionErrorCode.FEED_NOT_FOUND,
            message=f"Feed with id '{cmd.feed_id}' does not exist.",
        ))

    # 2. Verificar duplicados pre-save (optimización, no invariante)
    if self._raw_article_repo.exists_by_url(cmd.feed_id, cmd.url):
        return Result.failure(Error(
            code=IngestionErrorCode.DUPLICATE_ARTICLE,
            message="Article with this URL already exists in the feed.",
        ))

    # 3. Construir RawArticle (dominio valida invariantes I-11 a I-17)
    article = RawArticle(...)

    # 4. Persistir
    self._raw_article_repo.save(article)
    # ...
```

### ¿Dónde ocurre?

| Aspecto | Detalle |
|---------|--------|
| **Service** | `ArticleService.execute_create_article()` |
| **Repositorio usado** | `FeedRepository.find_by_id()` |
| **Antes o después del método de dominio?** | **ANTES** de construir el RawArticle. |
| **Error** | `Result.failure(Error(FEED_NOT_FOUND, message))` |

---

## 7. Tabla Resumen de AL Rules

| # | Regla | Use Case | Repositorio | Método | Error | 
|---|-------|----------|-------------|--------|-------|
| AL-01 | No desactivar NewsSource con Feeds activos | `DisableSource` | `FeedRepository.count_active_by_source()` | count > 0 → error | `HAS_ACTIVE_FEEDS` |
| AL-02 | Activar NewsSource requiere ≥1 Feed activo | `EnableSource` | `FeedRepository.count_active_by_source()` | count == 0 → error | `NEWS_SOURCE_INACTIVE` o `INVALID_STATE` |
| AL-03 | source_id referencia NewsSource existente | `RegisterFeed` | `NewsSourceRepository.find_by_id()` | Result.failure → error | `NEWS_SOURCE_NOT_FOUND` |
| AL-04 | No crear Feed bajo NewsSource inactivo | `RegisterFeed` | (reusa source de AL-03) | source.is_active == False → error | `NEWS_SOURCE_INACTIVE` |
| AL-05 | feed_id referencia Feed existente | `CreateRawArticle` | `FeedRepository.find_by_id()` | Result.failure → error | `FEED_NOT_FOUND` |

---

## 8. ¿Por qué Usamos Result.failure y NO Excepciones?

Las AL rules representan **flujos esperados** (el usuario intenta desactivar un source con feeds activos — es un error de negocio esperado, no una falla del sistema). Por lo tanto:

- **NO se lanzan excepciones de dominio** (no `raise HasActiveFeedsError`)
- **NO se lanzan excepciones de aplicación** (no `raise ApplicationError`)
- **Se retorna `Result.failure(Error(code, message))`** — el caller (presentación) decide cómo manejar el error

### Excepción: Errores de infraestructura

Si `FeedRepository.count_active_by_source()` falla por un problema de conexión a la BD, eso SÍ es una excepción (`InfrastructureError`) que se captura y se mapea a `Result.failure`.

```python
try:
    active_feed_count = self._feed_repo.count_active_by_source(cmd.source_id)
except InfrastructureError as e:
    return Result.failure(Error(
        code=IngestionErrorCode.INTERNAL_ERROR,  # o ErrorCode.UNKNOWN
        message="Database error while verifying active feeds.",
        detail=str(e),
    ))
```
