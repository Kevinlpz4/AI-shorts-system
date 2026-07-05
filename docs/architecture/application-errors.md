# Application Error Flow Design — Ingestion Bounded Context

> **Flujo de errores en la capa de aplicación**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-03

---

## 1. Principios de Diseño

1. **Result patrón para flujos esperados**: `Result.failure(Error)` para errores de negocio y validación. NO excepciones.
2. **Excepciones para fallos inesperados**: `InfrastructureError` para DB caída, timeout, etc. Se capturan y mapean a `Result.failure`.
3. **Nunca leak de excepciones al caller**: Todo error se traduce a `Result.failure(Error)` antes de salir del Application Service.
4. **ApplicationError como base**: Define un error de aplicación que NO es de dominio (comando inválido, recurso no encontrado).
5. **Códigos de error propios**: `ApplicationErrorCode` (nuevo) para errores de aplicación. Los errores de dominio usan `IngestionErrorCode` ya definido.

---

## 2. Jerarquía de Errores

### Foundation (existente)

```
FoundationError (Exception)
├── DomainError        ← Reglas de negocio violadas
├── ApplicationError   ← Errores de aplicación (base)
└── InfrastructureError ← Fallos técnicos
```

### Application Layer (nuevo en este diseño)

```
ApplicationError (foundation.errors.ApplicationError)
├── CommandValidationError    ← Comando inválido (datos faltantes o incorrectos)
└── ResourceNotFoundError     ← Recurso no encontrado en aplicación
```

### Domain (existente, FROZEN)

```
IngestionError (DomainError + ValueError)
├── SourceError
│   ├── InvalidSourceUrlError
│   ├── SourceAlreadyEnabledError
│   └── SourceAlreadyDisabledError
├── FeedError
│   ├── FeedAlreadyEnabledError
│   ├── FeedAlreadyDisabledError
│   ├── FeedAlreadyPausedError
│   └── FeedMaxRetriesExceededError
├── RawArticleError
│   ├── InvalidArticleUrlError
│   └── InvalidArticleTitleError
├── CategoryError
│   ├── InvalidCategoryError
│   ├── DuplicateCategoryNameError
│   └── CycleDetectedError
├── TopicError
│   └── InvalidTopicError
└── ValidationError
    ├── InvalidSyncPolicyError
    └── InvalidLanguageError
```

---

## 3. ApplicationErrorCode

Los errores de aplicación tienen sus propios códigos, separados de `IngestionErrorCode`:

```python
class ApplicationErrorCode(str, Enum):
    """Códigos de error para la capa de aplicación.

    Diferentes de IngestionErrorCode (dominio).
    """

    # Errores de comando
    COMMAND_INVALID = "COMMAND_INVALID"
    COMMAND_MISSING_FIELD = "COMMAND_MISSING_FIELD"

    # Errores de recurso
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"

    # Errores de operación
    OPERATION_FAILED = "OPERATION_FAILED"
    TRANSACTION_FAILED = "TRANSACTION_FAILED"

    # Errores de concurrencia
    CONCURRENCY_CONFLICT = "CONCURRENCY_CONFLICT"
```

**¿Por qué separados de IngestionErrorCode?**

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| **✅ ApplicationErrorCode separado** | Claridad semántica. Los errores de dominio (NEWS_SOURCE_NOT_FOUND) representan reglas de negocio. Los errores de aplicación (COMMAND_INVALID) representan problemas de uso del sistema. Son conceptos diferentes. | **SELECCIONADO** |
| ❌ Reusar IngestionErrorCode | Mezcla errores de dominio con errores de aplicación. Un código como `HAS_ACTIVE_FEEDS` no tiene sentido en un contexto de validación de comando. | Descartado |

---

## 4. Flujo Completo de Errores

```
                    ┌────────────────────────────────────────────┐
                    │            PRESENTATION                    │
                    │  (API/CLI) recibe Result[DTO]              │
                    │  Si Result.failure → HTTP 4xx/5xx          │
                    └──────────────┬─────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        APPLICATION SERVICE                           │
│                                                                      │
│  try {                                                                │
│      ┌─────────────────────────────────────────────┐                 │
│      │  1. Validate command (type checks)           │                 │
│      │  2. Load aggregates from repos               │                 │
│      │  3. Execute AL rules (cross-AR verification) │                 │
│      │  4. Call domain methods                     │                 │
│      │  5. Save aggregates via repos                │                 │
│      │  6. Commit UoW                              │                 │
│      │  7. Pull and publish events                  │                 │
│      │  8. Return Result.success(dto)               │                 │
│      └─────────────────────────────────────────────┘                 │
│  } catch (DomainError de) {                                          │
│      // Regla de negocio violada (ej: SourceAlreadyEnabledError)     │
│      uow.rollback()                                                  │
│      return Result.failure(map_domain_error(de))                     │
│  } catch (InfrastructureError ie) {                                  │
│      // DB caída, timeout, etc.                                      │
│      uow.rollback()                                                  │
│      return Result.failure(map_infra_error(ie))                      │
│  } catch (CommandValidationError cve) {                              │
│      // Comando inválido (ej: ID mal formado)                        │
│      return Result.failure(map_validation_error(cve))                │
│  } catch (Exception e) {                                             │
│      // Error inesperado (bug, caso no contemplado)                  │
│      uow.rollback()                                                  │
│      logger.exception("Unexpected error in use case")                │
│      return Result.failure(Error(UNKNOWN, "Internal error"))         │
│  }                                                                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Error Mapper

```python
class ErrorMapper:
    """Mapea excepciones y errores de dominio a Result.failure(Error).

    Centraliza la lógica de traducción para que los services
    no tengan try/except dispersos.
    """

    @staticmethod
    def map_domain_error(error: IngestionError) -> Error:
        """Convierte DomainError a Error para Result.failure().

        Args:
            error: Excepción de dominio (IngestionError o subclase).

        Returns:
            Error con el mismo código y mensaje que la excepción.
        """
        return Error(
            code=IngestionErrorCode(error.code),
            message=str(error),
        )

    @staticmethod
    def map_infra_error(error: InfrastructureError) -> Error:
        """Convierte InfrastructureError a Error para Result.failure().

        Args:
            error: Excepción de infraestructura.

        Returns:
            Error con código genérico y mensaje sanitizado (sin leak técnico).
        """
        return Error(
            code=ApplicationErrorCode.OPERATION_FAILED,
            message="An internal operation failed. Please try again.",
            detail=str(error),  # Solo para logging, no exponer al usuario
        )

    @staticmethod
    def map_validation_error(error: CommandValidationError) -> Error:
        """Convierte errores de validación de comando.

        Args:
            error: Error de validación de comando.

        Returns:
            Error con código COMMAND_INVALID y mensaje descriptivo.
        """
        return Error(
            code=ApplicationErrorCode.COMMAND_INVALID,
            message=error.message,
            detail=error.detail,
        )
```

---

## 6. Mapeo Específico por Origen

### 6.1 DomainError → Result.failure

| Excepción (DomainError) | Código Result | Use Case |
|------------------------|---------------|----------|
| `SourceAlreadyEnabledError` | `SOURCE_ALREADY_ENABLED` | EnableSource |
| `SourceAlreadyDisabledError` | `SOURCE_ALREADY_DISABLED` | DisableSource |
| `FeedAlreadyEnabledError` | `FEED_ALREADY_ENABLED` | ActivateFeed |
| `FeedAlreadyDisabledError` | `FEED_ALREADY_DISABLED` | PauseFeed |
| `FeedAlreadyPausedError` | `FEED_ALREADY_PAUSED` | PauseFeed |
| `FeedMaxRetriesExceededError` | `FEED_MAX_RETRIES_EXCEEDED` | RecordFailure |
| `InvalidSourceUrlError` | `INVALID_SOURCE_URL` | RegisterSource, UpdateSource |
| `InvalidArticleUrlError` | `INVALID_ARTICLE_URL` | CreateRawArticle |
| `InvalidArticleTitleError` | `INVALID_ARTICLE_TITLE` | CreateRawArticle |
| `InvalidLanguageError` | `INVALID_LANGUAGE` | RegisterFeed |
| `InvalidCategoryError` | `CATEGORY_NOT_FOUND` | AssignCategoryToSource, AssignCategoryToFeed |
| `InvalidTopicError` | `TOPIC_NOT_FOUND` | AssignTopicToSource, AssignTopicToFeed |
| `InvalidSyncPolicyError` | `INVALID_SYNC_POLICY` | RegisterFeed |
| `CycleDetectedError` | `CYCLE_DETECTED` | Category.change_parent |
| `DuplicateCategoryNameError` | `DUPLICATE_CATEGORY_NAME` | Category creation |
| `InvalidStateError` | `INVALID_STATE` | Varios |

### 6.2 ApplicationError (excepción) → Result.failure

| Excepción | Código Result | Cuándo ocurre |
|-----------|---------------|---------------|
| `CommandValidationError` | `COMMAND_INVALID` | Comando mal formado |
| `ResourceNotFoundError` | `RESOURCE_NOT_FOUND` | Recurso no encontrado en BD |

### 6.3 Repository Error (Result.failure) → Propagado

Los repositorios retornan `Result.failure` con códigos de `IngestionErrorCode`:

| Código de repositorio | Use Case que lo propaga |
|----------------------|------------------------|
| `NEWS_SOURCE_NOT_FOUND` | EnableSource, DisableSource, RegisterFeed, AssignCategoryToSource, AssignTopicToSource |
| `FEED_NOT_FOUND` | CreateRawArticle, PauseFeed, ActivateFeed |
| `RAW_ARTICLE_NOT_FOUND` | FindArticle |
| `DUPLICATE_ARTICLE` | CreateRawArticle (también verificado pre-save) |
| `DUPLICATE_FEED_URL` | RegisterFeed (verificado pre-save) |

---

## 7. Estándar try/except Wrapper

Cada método de Application Service sigue este patrón:

```python
def execute_disable_source(self, cmd: DisableSourceCommand) -> Result[SourceDetailDTO]:
    try:
        # 1. AL rules
        active_count = self._feed_repo.count_active_by_source(cmd.source_id)
        if active_count > 0:
            return Result.failure(Error(...))

        # 2. Domain call
        source_result = self._source_repo.find_by_id(cmd.source_id)
        if source_result.is_failure:
            return source_result  # propaga NEWS_SOURCE_NOT_FOUND

        source = source_result.value
        source.disable(reason=cmd.reason)

        # 3. Persist
        with self._uow:
            self._source_repo.save(source)

        # 4. Events
        for event in source.pull_events():
            self._event_publisher.publish(event)

        # 5. Response
        return Result.success(self._mapper.to_detail(source))

    except IngestionError as e:
        self._uow.rollback()
        return Result.failure(self._error_mapper.map_domain_error(e))

    except InfrastructureError as e:
        self._uow.rollback()
        logger.error(f"Infrastructure error disabling source: {e}")
        return Result.failure(self._error_mapper.map_infra_error(e))

    except Exception as e:
        self._uow.rollback()
        logger.exception(f"Unexpected error disabling source {cmd.source_id}")
        return Result.failure(Error(
            code=ErrorCode.UNKNOWN,
            message="An unexpected error occurred.",
            detail=str(e) if self._debug else None,
        ))
```

---

## 8. Cuándo Usar Excepción vs Result.failure

| Situación | Mecanismo | Razón |
|-----------|-----------|-------|
| AL rule violation (ej: has active feeds) | `Result.failure(Error(...))` | Flujo esperado, no es error del sistema |
| Entidad no encontrada en BD | `Result.failure(Error(NOT_FOUND))` | Flujo esperado (recurso no existe) |
| Comando mal formado (ID inválido) | `raise CommandValidationError` → catch → `Result.failure` | Error de programación/usuario |
| DB caída / timeout | `raise InfrastructureError` → catch → `Result.failure` | Fallo técnico irrecuperable |
| Bug / caso no contemplado | `raise Exception` → catch genérico → `Result.failure(UNKNOWN)` | Error inesperado, log + degrade |

**Regla de oro**: Si el error es un resultado esperado de la operación (el usuario intentó deshabilitar un source con feeds activos), usa `Result.failure`. Si el error es una falla del sistema (BD caída, bug), usa excepción y tradúcela a `Result.failure` en el catch.
