---
adr: "ADR-024"
title: "TypeDecorator Strategy for Value Objects and EntityId"
status: "APPROVED"
date: "2026-07-05"
---

# ADR-024: TypeDecorator Strategy for Value Objects and EntityId

## Contexto

El BC Ingestion define Value Objects (frozen dataclasses), EntityIds (UUID wrappers), y Enums
en su capa de dominio. Al implementar la persistencia con SQLAlchemy, necesitamos mapear estos
tipos de dominio a columnas SQL de manera consistente.

Tenemos varias opciones para cada tipo:

1. **Columnas SQL directas** (ej: `VARCHAR` para `ArticleTitle`, `UUID` para `EntityId`)
2. **TypeDecorators** de SQLAlchemy que convierten entre Python → SQL y SQL → Python
3. **`composite()`** de SQLAlchemy para Value Objects compuestos (ej: `SyncPolicy`)
4. **JSON** para VOs opacos no consultables

Cada estrategia tiene implicaciones en:
- Portabilidad entre SQLite (testing) y PostgreSQL (producción)
- Validación de datos al leer de BD
- Performance (sobrecarga de conversión)
- Mantenibilidad (cantidad de código boilerplate)
- Capacity de hacer queries sobre los campos

## Decisión

### EntityId → UN TypeDecorator genérico

Se define **un único** `EntityIdType[T]` que puede mapear cualquiera de los 5 IDs del dominio
(SourceId, FeedId, RawArticleId, CategoryId, TopicId). Todos tienen la misma estructura interna
(UUID wrapper), por lo que un decorator genérico elimina 4 decoradores duplicados.

```python
from typing import TypeVar
from sqlalchemy.types import TypeDecorator, UUID

T = TypeVar("T", bound=EntityId)

class EntityIdType(TypeDecorator[T]):
    """Generic TypeDecorator for any EntityId subtype."""
    
    impl = UUID
    cache_ok = True
    
    def process_bind_param(self, value: T | None, dialect) -> uuid.UUID | None:
        if value is None:
            return None
        return value.value  # EntityId.value es el UUID interno
    
    def process_result_value(self, value: uuid.UUID | None, dialect) -> T | None:
        if value is None:
            return None
        return self._id_type(value)  # type: ignore[call-arg]
```

**Limitación**: `process_result_value` necesita saber a qué tipo de ID convertir. Esto se resuelve
con una factory o subclass por ID:

```python
class SourceIdType(EntityIdType[SourceId]):
    _id_type = SourceId

class FeedIdType(EntityIdType[FeedId]):
    _id_type = FeedId
# ... etc
```

### Value Objects simples → TypeDecorators individuales

Cada VO con validación en su constructor necesita su propio TypeDecorator para ejecutar esa
validación al leer de BD. Esto protege contra datos corruptos en la base.

| VO | SQL Type | TypeDecorator |
|----|----------|---------------|
| `ArticleTitle` | `VARCHAR(500)` | `ArticleTitleType` |
| `ArticleUrl` | `VARCHAR(2048)` | `ArticleUrlType` |
| `CategoryName` | `VARCHAR(100)` | `CategoryNameType` |
| `SourceUrl` | `VARCHAR(2048)` | `SourceUrlType` |
| `Language` | `VARCHAR(2)` | `LanguageType` |

```python
class ArticleTitleType(TypeDecorator[ArticleTitle]):
    impl = VARCHAR(500)
    cache_ok = True
    
    def process_bind_param(self, value: ArticleTitle | None, dialect) -> str | None:
        return value.value if value else None
    
    def process_result_value(self, value: str | None, dialect) -> ArticleTitle | None:
        if value is None:
            return None
        return ArticleTitle(value)  # Valida en constructor
```

### Enums → VARCHAR + TypeDecorator

`SourceType` y `SyncMode` son `str, Enum`. Se almacenan como `VARCHAR(20)` en lugar de
ENUM nativo de PostgreSQL. Esto garantiza portabilidad con SQLite.

```python
class SourceTypeEnum(TypeDecorator[SourceType]):
    impl = VARCHAR(20)
    cache_ok = True
    
    def process_bind_param(self, value: SourceType | None, dialect) -> str | None:
        return value.value if value else None
    
    def process_result_value(self, value: str | None, dialect) -> SourceType | None:
        if value is None:
            return None
        return SourceType(value)  # ValueError si es inválido
```

### Composite Value Objects → Columnas separadas + composite()

`SyncPolicy` tiene 7 campos que son consultables e indexables individualmente. Se descompone
en columnas separadas en `ingestion_feeds` y se reconstruye con `composite()`.

**SyncPolicy (Domain)**:
```python
@dataclass(frozen=True)
class SyncPolicy:
    mode: SyncMode
    interval_minutes: int = 30
    max_retries: int = 3
    backoff_minutes: int = 5
```

**En la tabla** `ingestion_feeds`:
| Columna | Tipo |
|---------|------|
| `sync_mode` | `VARCHAR(20)` (SyncModeEnum) |
| `sync_interval_minutes` | `INTEGER` |
| `sync_max_retries` | `INTEGER` |
| `sync_backoff_minutes` | `INTEGER` |

### JSON columns → JSONB/JSON

`RawArticle.metadata` es un `dict` opaco que nunca se consulta por contenido interno. Se
almacena como JSON.

## Consecuencias

### Positivas ✅

- **Un solo patrón** para todos los Value Objects: TypeDecorator
- **Validación en la lectura**: si hay datos corruptos en BD, se detectan al leer
- **Portabilidad**: SQLite + PostgreSQL con el mismo schema
- **DRY**: un TypeDecorator genérico para los 5 EntityIds
- **SyncPolicy consultable**: se puede hacer WHERE sobre interval_minutes, max_retries, etc.

### Negativas ⚠️

- **Boilerplate**: 8 TypeDecorators + 5 EntityId subclasses = ~13 clases de infraestructura
- **Overhead de validación**: cada lectura ejecuta validación del VO. Mínimo, pero existe.
- **SyncPolicy en 7 columnas**: ocupa más espacio que un JSON (~50 bytes vs ~200 bytes por fila)

## Alternativas Consideradas

### Alternativa 1: JSON para todo (descartada)

- **Descripción**: Persistir todos los VOs como JSON en una columna.
- **Ventaja**: Zero TypeDecorators, schema más simple.
- **Desventaja**: Sin validación al leer, sin constraints, sin índices, sin queries sobre campos.
- **Descartada por**: Violaría el principio de que la BD debe reflejar el modelo de dominio.
  SyncPolicy es consultable y debe ser indexable.

### Alternativa 2: Columnas directas con property setters (descartada)

- **Descripción**: Mapear values a columnas directas (strings, ints) y tener property setters
  en el modelo ORM para convertir.
- **Ventaja**: Sin TypeDecorators.
- **Desventaja**: Lógica de validación duplicada entre Domain y ORM. El ORM termina conociendo
  reglas de dominio.
- **Descartada por**: Violación DRY. Si un VO cambia su validación, hay que actualizar dos lugares.

### Alternativa 3: TypeDecorator por cada VO sin generic (considerada, no seleccionada)

- **Descripción**: Un TypeDecorator para cada EntityId, no uno genérico.
- **Ventaja**: Typing más simple (sin TypeVar).
- **Desventaja**: 4 clases más para los IDs. Código repetitivo.
- **No seleccionada por**: El overhead de `EntityIdType[T]` es mínimo y elimina 4 clases.
  La factory/subclass approach es clara.

## Compliance

- **Principios**: P2 (Clean Architecture), F1 (zero dependencies)
- **Baseline**: v1.0 (no rompe — los TypeDecorators son código nuevo en infraestructura)
- **Foundation**: No se modifica. `EntityId` se usa como bound del TypeVar.
- **Domain**: No se modifica. Los VOs se usan en `process_result_value`.
- **ADR relacionados**: ADR-021 (Foundation FROZEN), ADR-023 (RawArticle inmutable)

## Cumplimiento Futuro

- Si Foundation agrega un método `generate()` a `EntityId` que use UUID v7 → actualizar
  `RawArticleIdType` para generar UUID v7 en lugar de uuid4.
- Si se agregan nuevos VOs → agregar TypeDecorator correspondiente.
- Si `SyncPolicy` se expande → agregar columnas y actualizar `composite()`.
