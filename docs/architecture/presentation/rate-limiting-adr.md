# Rate Limiting Audit — ADR-029

**Sprint**: 6.5 — API Hardening & Production Readiness
**Date**: 2026-07-15
**Status**: DEFERRED (YAGNI)

---

## Decision

**Do NOT implement rate limiting at this time.**

## Context

The Ingestion API is an internal bounded context API, not a public-facing API. It is consumed by:
- Internal application services (Application Layer)
- Future background jobs (Sprint 7.x)
- Health check probes (k8s)

There are no external clients, no user-facing endpoints, and no multi-tenant usage patterns that would require rate limiting.

## Rationale

1. **YAGNI**: No current use case demands rate limiting. Adding it would be speculative architecture.
2. **No multi-tenancy**: Single-tenant API — no risk of one client starving others.
3. **Internal consumption**: All callers are controlled and known.
4. **Complexity cost**: Rate limiting requires state (Redis, in-memory counters, sliding windows), adds latency, and introduces failure modes (what happens when the rate limiter itself fails?).
5. **Future need is uncertain**: If the API becomes public-facing, rate limiting should be designed holistically (per-user, per-endpoint, global), not bolted on.

## Consequences

- **Risk**: If the API is exposed publicly without rate limiting, it's vulnerable to abuse.
- **Mitigation**: The API should NOT be exposed publicly without adding rate limiting first. This ADR should be revisited when:
  - The API is exposed to external clients
  - Multi-tenant usage is introduced
  - Background jobs need throttling

## When to Revisit

- Sprint 7.x if public API exposure is planned
- If abuse or performance degradation is observed
- When adding authentication/authorization layer

## Alternatives Considered

| Approach | Verdict |
|----------|---------|
| In-memory rate limiting | Rejected — lost on restart, not shared across instances |
| Redis-based rate limiting | Deferred — adds infrastructure dependency |
| API gateway rate limiting | Recommended for production — handled at infra level |
| Per-endpoint throttling | Over-engineered for current needs |

## Recommendation

For production deployment behind an API gateway (nginx, Kong, AWS API Gateway), configure rate limiting at the **infrastructure level** rather than in the application. This is more resilient, more performant, and doesn't add code complexity.
