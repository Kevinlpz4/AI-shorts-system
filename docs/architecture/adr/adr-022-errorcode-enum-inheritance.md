---
adr: "ADR-022"
title: "ErrorCode Enum Inheritance Policy"
status: "APPROVED"
date: "2026-07-02"
---

# ADR-022: ErrorCode Enum Inheritance Policy

## Contexto

Durante la implementación del Sprint 2.3 (Foundation Result Pattern), se definió
`ErrorCode` como `class ErrorCode(str, Enum)` con un único miembro:
`UNKNOWN = "UNKNOWN"`.

La especificación original planteaba que cada Bounded Context extendería `ErrorCode`
mediante herencia:

```python
class IngestionError(ErrorCode):
    SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
```

Sin embargo, **Python 3.11+ prohíbe subclasear Enums que tienen miembros definidos**
([PEP 663 / Python docs](https://docs.python.org/3/library/enum.html#restricted-subclassing-of-enumerations)).
Como `ErrorCode` tiene `UNKNOWN = "UNKNOWN"`, cualquier intento de herencia lanza:

```
TypeError: cannot extend <enum 'ErrorCode'>
```

Esto no es un bug ni una limitación del diseño — es una restricción del lenguaje que
existía antes de tomar la decisión pero no se detectó durante la fase de especificación.

## Decisión

Foundation define **únicamente** `ErrorCode` como enum base con su miembro `UNKNOWN`.

Cada Bounded Context define su **propio Enum independiente** para sus códigos de error.
No existe herencia entre Enums. La relación entre Foundation y los BCs es de
**convención, no de herencia**:

```python
# ✅ BIEN — Cada BC define su propio Enum
class IngestionErrorCode(str, Enum):
    """Códigos de error del BC Ingestion."""
    SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
    DUPLICATE_SOURCE = "DUPLICATE_SOURCE"

# ✅ BIEN — Se usa con Error(code=...) sin problemas de tipo
Error(code=IngestionErrorCode.SOURCE_NOT_FOUND, message="Source not found")
```

### ¿Por qué no sacar UNKNOWN del enum?

Se consideró sacar `UNKNOWN` de `ErrorCode` para permitir herencia. Se descartó porque:

1. `UNKNOWN` es semanticamente un valor del enum — no un "tipo base".
2. Sacarlo requeriría un handling especial (`UNKNOWN` como constante, `ErrorCode` sin miembros).
3. Los BCs igual van a definir sus propios enums con nombres específicos de dominio.
4. No hay beneficio real en heredar de `ErrorCode` — la convención de tipo `str, Enum` es
   suficiente para garantizar consistencia.

## Consecuencias

### Positivas ✅

- `ErrorCode` con `UNKNOWN` es un enum completo y autocontenido.
- Cada BC tiene autonomía total sobre sus códigos de error.
- No hay acoplamiento entre BCs vía una jerarquía de enums compartida.
- La convención `str, Enum` es autodocumentada: cualquier desarrollador sabe que
  los códigos de error son strings con nombre.

### Negativas ⚠️

- No hay una manera de tipar "cualquier ErrorCode de cualquier BC" sin usar `str, Enum`
  como tipo base, lo cual es menos restrictivo que una clase concreta.
- Los BCs no pueden compartir códigos de error vía herencia (aunque este no es un
  caso de uso esperado — cada BC tiene su propio dominio).
- La spec original especificaba herencia; esta decisión la corrige.

## Alternativas Consideradas

### Alternativa 1: ErrorCode sin miembros (herencia permitida)

- **Descripción**: `ErrorCode` como `class ErrorCode(str, Enum)` sin ningún miembro.
  `UNKNOWN` sería una constante aparte: `UNKNOWN = ErrorCode("UNKNOWN")` o similar.
- **Descartada por**: Complejidad innecesaria. No hay BC que necesite heredar de
  `ErrorCode` hoy. Cuando surja la necesidad, se evaluará. YAGNI.

### Alternativa 2: Usar un decorador/metaclase para bypass

- **Descripción**: Usar `@functools.wraps` o `enum._simple_enum` (privado) para
  permitir herencia.
- **Descartada por**: APIs privadas de Python estándar. Inestable, no portable.
  Violaría el principio ZERO DEPENDENCIES de Foundation.

## Compliance

- **Principios**: F3 (explicit over implicit), F5 (zero special cases),
  ADR-021 Foundation Stability Policy
- **Baseline**: v1.0 (no rompe)
