---
adr: "ADR-028"
title: "Observability Strategy — Structured Logging, Health Checks, y Request Tracing"
status: "APPROVED"
date: "2026-07-13"
---

# ADR-028: Observability Strategy

## Contexto

La observabilidad debe diseñarse desde el inicio, no añadirse después. Cuando scrapers y background jobs empiecen a correr, structured logging y tracing serán críticos para debugging y monitoreo. Necesitamos decidir qué nivel de observabilidad implementar desde la primera versión.

Fuerzas en conflicto:
- Production readiness vs YAGNI (no sobre-engineering)
- Structured logging (JSON) vs readability during development
- Full tracing vs simple request IDs

## Decisión

### Request ID

- Header: `X-Request-ID`
- Auto-generado UUID si el client no lo provee
- Incluido en todos los logs y responses
- Propagated a downstream services (futuro)

### Correlation ID

- Header: `X-Correlation-ID`
- Auto-generado UUID si no se provee
- Agrupa requests relacionados (batch operations)
- Propagated across service boundaries (futuro)

### Structured Logging

- **Formato**: JSON en producción, human-readable en desarrollo
- **Librería**: `structlog`
- **Fields**: timestamp, level, message, request_id, correlation_id, duration, status
- **Exception logging**: traceback completo con contexto

### Timing Middleware

- Header: `X-Response-Time` (en response)
- Mide duración total del request
- Logueado en access log

### Access Log

- method, path, status code, duration, request_id
- Una línea por request
- Level: INFO

### Exception Log

- Exception context completo
- Request details (method, path, body)
- Stack trace
- Level: ERROR

### Health Checks

| Endpoint | Descripción | Response |
|----------|-------------|----------|
| `GET /health` | Full health check | 200: status, version, checks |
| `GET /health/live` | Liveness probe | 200: `{ "status": "alive" }` |
| `GET /health/ready` | Readiness probe | 200: ready / 503: not ready |

- Ubicados fuera de `/api/v1` prefix
- Liveness: siempre 200 si la app está corriendo
- Readiness: verifica conexión DB

### Metrics (Futuro — Diseño Only)

- Prometheus endpoint: `GET /metrics`
- Counters: `requests_total`, `errors_total`
- Histograms: `request_duration_seconds`
- **NO implementado en primera versión** — solo diseño

## Consecuencias

### Positivas ✅

- **Debugging trivial**: Request ID traza el lifecycle completo
- **Production readiness desde día uno**: Logging estructurado habilita aggregation (ELK, Datadog)
- **Health checks para K8s**: Liveness/readiness son requeridos para container orchestration
- **Correlation para batch**: Agrupa operaciones relacionadas
- **structlog es battle-tested**: Ampliamente usado en producción

### Negativas ⚠️

- **Overhead del middleware**: ~0.2ms por request (aceptable)
- **structlog como dependencia**: Añade un paquete (aceptable, ampliamente mantenido)
- **JSON en desarrollo**: Menos legible que text (mitigado: `log_format=text` en dev)

## Alternativas Consideradas

### Alternativa 1: Logging estándar de Python (`logging` stdlib)
- **Descripción**: Usar `logging` estándar sin structured logging
- **Descartada por**: No produce JSON output. Los logs de producción necesitan formato estructurado para aggregation tools. stdlib logging no tiene context vars integration.

### Alternativa 2: Sentry / DataDog APM completo
- **Descripción**: Añadir APM completo con tracing distribuido desde el inicio
- **Descartada por**: YAGNI. El sistema es single-instance. Tracing distribuido es premature optimization. Las métricas de Prometheus se implementan cuando se necesite.

### Alternativa 3: Health checks dentro de `/api/v1`
- **Descripción**: Poner `/api/v1/health` en vez de `/health`
- **Descartada por**: Los probes de Kubernetes y load balancers esperan `/health` en la raíz. Separar health de la API versionada evita breakage cuando se lance `/api/v2`.

## Compliance

- **Principios**: P5 (YAGNI), P6 (KISS)
- **Baseline**: v1.0 (no rompe)
- **Foundation**: No se modifica
- **Domain**: No se modifica
- **Application**: No se modifica
- **ADR relacionados**: ADR-026 (Presentation Layer Architecture), ADR-027 (HTTP API Contract)
