# Proposal: EPIC 6 — Presentation Layer & External Adapters Design

## Intent

The 4 inner layers (Foundation v1.0, Domain v2.0, Application v1.0, Infrastructure v1.0) are FROZEN with 823+ tests. The Ingestion BC has 3 Application Services exposing 22 operations (15 writes + 7 reads) but no way to call them from outside Python. This epic designs (NOT implements) the complete Presentation Layer and External Adapters so the system is ready for HTTP consumption and external feed ingestion.

## Scope

### In Scope
- FastAPI layer: routers, versioning, DI, lifespan, exception handlers, response models, pagination, OpenAPI
- Composition Root: wiring Services → Repos → UoW → EventPublisher → Engine → Settings → Routers
- Dependency Injection: providers, factories, lifetimes, testing overrides
- API Contracts: all 22 HTTP operations for Sources, Feeds, Articles
- Exception Mapping: Foundation→Domain→Application→Persistence→HTTP→RFC 7807 Problem Details
- Serialization: DTO→JSON, camelCase, UUID/datetime/Enum handling, pagination envelope
- Configuration: dev/test/prod, env vars, CORS, logging
- Authentication design: JWT/API Keys/OAuth2 (design only)
- Observability: logging, health checks, metrics, tracing, correlation IDs
- Background Jobs: Celery/APScheduler interfaces (design only)
- External Adapters: RSS/Atom/HTTP/Scrapers (Ports only)
- Webhook Strategy: event publication (design only)
- Testing Strategy: unit, API, integration, contract, smoke, performance
- ADRs as needed

### Out of Scope
- Actual implementation of any Presentation code
- Modifications to frozen layers (Foundation, Domain, Application, Persistence)
- Old `presentation/` (Research/Script BC) — left untouched
- Category/Topic services (no Application Service yet)
- Database migrations

## Approach

**Design-only epic** — 14 documents produced in dependency order, each reviewed by ARB before proceeding. The design surface is split into 4 phases:

| Phase | Documents | Dependency |
|-------|-----------|------------|
| **P1: Foundation** | presentation-design, exception-handling, serialization | None (can parallelize) |
| **P2: Wiring** | composition-root, dependency-injection, configuration | Depends on P1 |
| **P3: API Surface** | api-design, routing-strategy | Depends on P1+P2 |
| **P4: Cross-cutting** | observability, background-jobs, external-adapters, testing-strategy, epic-6-roadmap, arb-report | Depends on P1-P3 |

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/ingestion/presentation/` | New | FastAPI routers, models, container, error handlers |
| `tests/ingestion/presentation/` | New | API tests, integration tests |
| `docs/architecture/` | New | 14 design documents |
| `src/ingestion/application/` | Read-only | Reference for services, commands, DTOs |
| `src/ingestion/infrastructure/` | Read-only | Reference for repos, UoW, engine |

## Key Decision Points (ARB Approval Required)

| # | Decision | Options | Default |
|---|----------|---------|---------|
| D1 | Async-to-Sync bridging | A) `def` endpoints (FastAPI thread pool) / B) `run_in_executor` | A |
| D2 | Result[T] → HTTP mapping | A) Thin adapter per endpoint / B) Generic Result→Response utility | A |
| D3 | Pydantic models vs frozen dataclasses | A) Separate Pydantic + converter / B) Use dataclasses directly | A |
| D4 | Composition Root location | A) `src/ingestion/presentation/container.py` / B) Top-level | A |
| D5 | Old presentation coexistence | A) Side-by-side prefixes / B) Replace / C) Leave old, new separate | C |
| D6 | Error response format | A) RFC 7807 Problem Details / B) Custom JSON envelope | A |
| D7 | API versioning strategy | A) URL path `/api/v1/` / B) Header-based | A |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Over-engineering cross-cutting concerns | High | YAGNI: design only what 22 operations need |
| Tight coupling Presentation→Domain | Medium | Strict adapter pattern: Presentation→Application only |
| UoW lifecycle outliving request | Medium | Explicit design: UoW scoped to request via DI |
| Large design surface → slow ARB review | Medium | Phase-gated reviews: P1 before P2, etc. |
| Old presentation code confusion | Low | Separate directory `src/ingestion/presentation/`, no imports |

## Rollback Plan

Design-only — no code to rollback. If ARB rejects any document, that document is revised in-place. If the entire epic is rejected, all `docs/architecture/` files are deletable (no code changes).

## Dependencies

- FastAPI ≥ 0.110.0 (already in requirements.txt)
- Pydantic ≥ 2.5.0 (already in requirements.txt)
- All 4 frozen layers must remain untouched

## Success Criteria

- [ ] 14 design documents produced and reviewed
- [ ] All 7 decision points resolved by ARB
- [ ] API surface covers all 22 Application Service operations
- [ ] Dependency Rule maintained: Presentation depends on Application, never Domain/Infrastructure
- [ ] No modifications to any frozen layer
- [ ] Testing strategy covers 6 levels (unit → performance)
- [ ] Composition Root design is implementable without modifying existing code
