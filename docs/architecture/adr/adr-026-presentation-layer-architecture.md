---
adr: "ADR-026"
title: "Presentation Layer Architecture — FastAPI Adapter con Bridge Temporal"
status: "APPROVED"
date: "2026-07-13"
---

# ADR-026: Presentation Layer Architecture

## Contexto

El BC Ingestion tiene 4 capas interiores FROZEN (Foundation v1.0, Domain v2.0, Application v1.0, Persistence v1.0) con 823+ tests, pero ningún mecanismo para exponer sus 3 Application Services (22 operaciones) vía HTTP. Necesitamos un Presentation Layer que sirva como adapter HTTP inbound, manteniendo la Dependency Rule: Presentation → Application → Domain, NUNCA al revés.

Fuerzas en conflicto:
- Application Layer es **sync** (no puede cambiarse — FROZEN)
- FastAPI es **async-first** (todos los endpoints son `async def`)
- Necesitamos un bridge sync→async que sea temporal y localizado

## Decisión

### Organización de Routers

Un router por aggregate root:
- `routers/sources.py` → `/api/v1/sources/*`
- `routers/feeds.py` → `/api/v1/feeds/*`, `/api/v1/sources/{id}/feeds`
- `routers/articles.py` → `/api/v1/articles/*`, `/api/v1/feeds/{id}/articles`
- `routers/categories.py` → `/api/v1/categories/*` (stub 501)
- `routers/topics.py` → `/api/v1/topics/*` (stub 501)
- `routers/system.py` → `/health`, `/api/v1/info`

Todos compuestos en `main.py` bajo prefijo `/api/v1`.

### Dependency Injection

DI nativa de FastAPI (`Depends()`). Sin contenedor IoC externo.

Archivos:
- `dependencies.py` — Funciones request-scoped (get_uow, get_repos)
- `providers.py` — Factory functions para servicios
- `lifespan.py` — Startup/shutdown hooks

### Composition Root

Factory functions para creación de servicios. UoW vía lifecycle de generator:

```python
async def get_uow(session_factory, event_publisher):
    async with SQLAlchemyUnitOfWork(session_factory, event_publisher) as uow:
        yield uow
```

Testing overrides vía `app.dependency_overrides`.

### Lifespan

- **Startup**: inicializar engine, verificar conexión DB
- **Shutdown**: cerrar engine, flush logs

### Middleware Stack (orden estricto)

1. **Request ID** — UUID auto-generado si no se provee
2. **Correlation ID** — Desde header o auto-generado
3. **Timing** — Duración del request
4. **Access Log** — method, path, status, duration
5. **Exception Handler** — RFC 9457 Problem Details

### Async-First con Bridge Temporal

Todos los endpoints son `async def`. El bridge sync→async está localizado en UN ÚNICO archivo:

```
bridge/sync_async.py
```

```python
async def run_sync(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(func, *args, **kwargs))
```

El bridge es **TEMPORAL** — se elimina cuando el stack completo migra a async. Application Layer permanece sync (sin cambios).

## Consecuencias

### Positivas ✅

- **Separación limpia**: Presentation es un adapter inbound, no contiene lógica de negocio
- **DI pythonico**: Sin contenedores complejos, fácil de entender
- **Fácil de testar**: `app.dependency_overrides` para testing
- **Listo para async**: Cuando el stack migra, solo se elimina el bridge
- **Composición explícita**: Composition Root visible en `main.py`

### Negativas ⚠️

- **Overhead del bridge**: `run_in_executor` añade ~0.1ms por request (aceptable)
- **Mantenimiento del bridge**: Debe mantenerse hasta que se migre a async completo
- **Complejidad del bridge**: Si no está localizado, puede proliferar (mitigado: UN archivo)

## Alternativas Consideradas

### Alternativa 1: Contenedor IoC externo (dependency-injector)
- **Descripción**: Usar `dependency-injector` para inyección de dependencias declarativa
- **Descartada por**: Complejidad innecesaria. FastAPI `Depends()` ya resuelve el problema. KISS. El contenedor introduce abstractions adicionales que no aportan valor para 22 endpoints.

### Alternativa 2: Endpoints sync (`def` en vez de `async def`)
- **Descripción**: FastAPI ejecuta `def` endpoints en thread pool automáticamente
- **Descartada por**: FastAPI maneja `def` como sync pero el runtime es async. Usar `async def` con bridge explícito es más predecible y controlado. Además, `def` endpoints no pueden usar `await` internamente.

### Alternativa 3: Application Layer async desde el inicio
- **Descripción**: Modificar Application Services para ser async
- **Descartada por**: IMPOSIBLE — Application v1.0 está FROZEN. 823+ tests dependen de sync services. Modificar violaría la restricción de capas congeladas.

## Compliance

- **Principios**: P1 (Clean Architecture), P2 (Dependency Rule), P5 (YAGNI), P6 (KISS)
- **Baseline**: v1.0 (no rompe)
- **Foundation**: No se modifica
- **Domain**: No se modifica
- **Application**: No se modifica
- **Persistence**: No se modifica
- **ADR relacionados**: ADR-021 (Foundation FROZEN), ADR-024 (Typedecorator), ADR-025 (Event Publication)
