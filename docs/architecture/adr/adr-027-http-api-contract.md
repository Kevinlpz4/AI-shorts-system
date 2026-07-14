---
adr: "ADR-027"
title: "HTTP API Contract — RFC 9457, Versioning, DTOs, e Idempotencia"
status: "APPROVED"
date: "2026-07-13"
---

# ADR-027: HTTP API Contract

## Contexto

La API del BC Ingestion debe ser un contrato limpio y consistente que los clientes puedan usar con confianza. Necesitamos definir: formato de errores, versioning, DTOs, serialización, e idempotencia para POST endpoints.

Fuerzas en conflicto:
- Estándares industriales vs simplicidad de implementación
- Consistencia del contrato vs velocidad de desarrollo
- Seguridad en retries vs overhead de idempotency store

## Decisión

### Formato de Errores: RFC 9457 Problem Details

TODOS los errores retornan Problem Details JSON:

```json
{
  "type": "about:blank",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "Source 'abc-123' not found",
  "instance": "/api/v1/sources/abc-123",
  "error_code": "RESOURCE_NOT_FOUND"
}
```

- Sin formatos de error custom
- Fields: `type`, `title`, `status`, `detail`, `instance`
- Campo custom: `error_code` (para mapeo interno)
- Validation errors incluyen `errors` array

### Versioning

- URL prefix: `/api/v1/` (todas las endpoints de dominio)
- Futuro: `/api/v2/` solo para breaking changes
- Non-versioned: `/health`, `/docs`, `/redoc`

### DTOs

- Pydantic models para HTTP (Request/Response)
- Separados de domain DTOs (capa de converter delgada)
- `snake_case` para JSON (default de Python/FastAPI)

### Serialización

| Tipo | Representación | Ejemplo |
|------|---------------|---------|
| UUID | string | `"550e8400-e29b-41d4-a716-446655440000"` |
| datetime | ISO 8601 | `"2026-07-13T10:30:00Z"` |
| Enum | string | `"active"` (no `1`) |
| None | null | `null` |
| bool | boolean | `true` / `false` |

### Idempotencia

- Header: `Idempotency-Key` (UUID string)
- Aplica a POST endpoints (recomendado, no obligatorio)
- GET/PUT/PATCH/DELETE no necesitan (ya son idempotentes por HTTP spec)
- Duplicate → retorna respuesta cacheada con header `X-Idempotent-Replay: true`
- Store: InMemory con TTL 24h (primera versión)

### OpenAPI

- Tags: Sources, Feeds, Articles, Categories, Topics, System
- Cada endpoint tiene: summary, description, tags, examples, error responses
- `/docs` (Swagger UI), `/redoc` (ReDoc)
- Schema auto-generado desde Pydantic models

## Consecuencias

### Positivas ✅

- **Estándar industrial**: RFC 9457 es ampliamente soportado por herramientas
- **Versioning limpio**: `/api/v1` es explícito, fácil de evolucionar
- **Retry safety**: Idempotencia en POST previene duplicados
- **Self-documenting**: OpenAPI completo reduce tiempo de integración
- **Type-safe**: Pydantic validation automática

### Negativas ⚠️

- **Overhead de Problem Details**: Más bytes que un error simple `{ "error": "msg" }` (aceptable)
- **Idempotency store en memoria**: Se pierde en restart (aceptable para single-instance)
- **No distribuido**: Idempotencia no funciona across instances (mitigación: Redis futuro)

## Alternativas Consideradas

### Alternativa 1: Error format custom (`{ "error": { "code": "...", "message": "..." } }`)
- **Descripción**: Formato JSON simple para errores
- **Descartada por**: No es un estándar. Los clientes no pueden usar herramientas estándar para parsear errores. RFC 9457 tiene soporte nativo en OpenAPI.

### Alternativa 2: Header-based versioning (`Accept: application/vnd.ai-shorts.v1+json`)
- **Descripción**: Versioning vía Accept header
- **Descartada por**: Más complejo de implementar, harder de probar con curl/browser, no es tan explícito como URL path. La mayoría de APIs públicas usan URL path versioning.

### Alternativa 3: Sin idempotencia (dejar al cliente manejar retries)
- **Descripción**: No implementar idempotency keys
- **Descartada por**: Los clientes no pueden asumir que retries son seguros. Sin idempotencia, un POST duplicado crea recursos duplicados. La implementación es trivial (~50 líneas).

## Compliance

- **Principios**: P1 (Clean Architecture), P5 (YAGNI), P6 (KISS)
- **Baseline**: v1.0 (no rompe)
- **Foundation**: No se modifica
- **Domain**: No se modifica
- **Application**: No se modifica
- **ADR relacionados**: ADR-026 (Presentation Layer Architecture)
