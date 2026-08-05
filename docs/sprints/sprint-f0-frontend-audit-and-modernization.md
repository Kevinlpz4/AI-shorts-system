# Sprint F0 — Frontend Architecture Audit & Modernization Assessment

> **Date**: 2026-08-04
> **Status**: ✅ COMPLETO
> **Scope**: READ-ONLY — auditoría y assessment. Sin implementación de código. No se modifica `frontend/`, no se tocan los Bounded Contexts congelados, no se elimina nada del repo.
> **Fuentes**: 3 informes parciales consolidados desde Engram — `sdd/sprint-f0/explore-frontend` (obs #360), `sdd/sprint-f0/explore-backend` (obs #357), `sdd/sprint-f0/explore-strategy` (obs #363)

---

## 0. Documento base para futuros sprints del frontend

Este documento es el **entregable único y consolidado** del Sprint F0, y será la **base de referencia obligatoria** para todos los futuros sprints del frontend de AI_Shorts_System. Consolida los tres informes parciales producidos durante el explore:

| Informe parcial | Observación Engram | Contenido |
|---|---|---|
| Frontend audit (partes 1-3, 6, 10-12) | `#360` — `sdd/sprint-f0/explore-frontend` | Arquitectura, estado del proyecto, reutilización de componentes, UX, inventario de rutas/APIs, deuda técnica |
| Gap analysis & backend integration (partes 4-5) | `#357` — `sdd/sprint-f0/explore-backend` | Inventario de las 18 llamadas API del FE, las 3 superficies backend, matriz de integración |
| Modernization strategy, dashboard vision & roadmap (partes 7-9) | `#363` — `sdd/sprint-f0/explore-strategy` | Opciones A/B/C/D, selección de estrategia, visión de dashboard, roadmap P0-P7 |

El Sprint F0 es **read-only**: produce evidencia y decisiones, no código. Todo lo que se implemente en sprints futuros deberá partir de este documento y respetar las restricciones de la sección 12.

---

## 1. Executive Summary

### Veredicto CORREGIDO

El frontend (`frontend/`, **Next.js 14 App Router + Zustand + Tailwind + TypeScript**) está **bien organizado**: ~6500 líneas en 59 archivos, layering limpio (domain/ports → application/use-cases → infrastructure/adapters → presentation), `tsc` limpio, **5 lint warnings** únicamente.

- El FE **consume la API servida legacy `presentation/api/`** — los **18 endpoints existen** y **15/18 MATCH** contra el contrato que el FE espera.
- Los **3 mismatches son bugs de adaptador FE-side**: `#7` discover `source_names`, `#8` studio approved-topics camelCase, `#13` scripts list camelCase.
- La API que el FE consume **vive sobre el BC `research/` CONGELADO**; la arquitectura nueva (Ingestion API diseñada + Runtime CLI) la supera.
- **Recomendación**: estrategia **B (Refactor parcial) ahora → C-lite después**, en un decision gate.

> ⚠️ **CORRECTION NOTICE (2026-08-04)**: el hallazgo "CRITICAL #1" del borrador original era INCORRECTO. Comparaba el FE contra `src/ingestion/presentation/routers/` (la Ingestion API DISEÑADA pero NO SERVIDA) y concluía que el contrato del FE "no existe". **Verificado**: la API SERVIDA es `presentation/api/` (`app/main.py:424-448` `run_api` → `presentation/api/main.py` `create_app`, puerto `app/config.py:165-168`, `.env=8001`) y contiene los 18 endpoints que el FE consume. 15/18 MATCH, 3 bugs de adaptador FE-side.

### Los 3 bugs concretos

| # | Ruta del FE | Bug | Efecto observable |
|---|---|---|---|
| **#7** | `POST /api/v1/discover` | El FE envía `source_names: [google-news, twitter, rss]` (`ApiTopicSource.ts:42`), pero el registry backend solo tiene `google-news-rss`/`mock` | **Siempre 0 descubiertos** en modo API real; el Terminal funciona porque omite `source_names` |
| **#8** | `GET /api/v1/studio/approved-topics` | `asdict(ResearchTopicDTO)` (snake_case) asignado directo a `TopicData` camelCase (`scriptStudioStore.ts:382`) | `scoreTotal`/`sourceName`/`createdAt` undefined → **"undefined pts"** (`TopicQueueItem.tsx:78`) |
| **#13** | `GET /api/v1/scripts` | `word_count`/`is_valid`/`created_at` vs `wordCount`/`isValid`/`createdAt` (`ScriptDetailPanel.tsx:48,135,165-166`) | **"Invalid Date"** / campos undefined con API real; solo funciona con mocks |

---

## 2. Parte 1 — Auditoría Arquitectónica

### Stack verificado

| Capa | Tecnología | Versión / Nota |
|---|---|---|
| Framework | Next.js (App Router) | 14.2.35 |
| UI | React | 18.3.1 |
| Estado | Zustand | 4.5.7 |
| Estilos | Tailwind CSS | 3.4.19 |
| Lenguaje | TypeScript | 5.9.3 (declarado `^5.4.0`), `strict: true`, **cero `any`** |
| Animación | framer-motion | 12.42.2 |
| Utilidades | clsx, lucide-react | — |
| Config | `next.config.js` | Solo `reactStrictMode`; **sin rewrites/proxy** — el FE golpea al backend con CORS directo |

> `package.json` name = `"content-discovery-dashboard"` (mismatch con el proyecto AI_Shorts_System).

### Organización de carpetas y arquitectura

**Clean/Hexagonal: PARCIALMENTE real.** El layering existe y es correcto en la dirección de dependencias:

- `domain/ports/` → `ITopicRepository.ts`, `ITopicSource.ts` (importan solo `@/types` — correcto).
- `application/use-cases/` → 5 use cases que dependen solo de ports + types (correcto).
- `infrastructure/Container.ts` → composition root (DI, `NEXT_PUBLIC_API_URL`, default `http://localhost:8000`).
- `infrastructure/api/*` → adapters; stores; components; app pages.

**Violaciones concretas:**

1. `types/index.ts` (catch-all compartido) **duplica conceptos de dominio**: `TopicFilters` definido DOS veces con shapes distintos (`types/index.ts:67-73` vs `ITopicRepository.ts:9-16`); `KPIStats` (`types:59`) vs `KPIResult` (`ITopicRepository:18`).
2. El DTO `TopicData` es importado por los domain ports — los ports **no son domain-agnostic**.
3. **5 estilos de fetch distintos**, sin cliente HTTP compartido, sin convención de manejo de errores (`ApiTopicRepository._fetch` wrapper; `ApiTopicSource`/`Terminal`/`scriptsStore`/`scriptStudioStore`/`settings` con raw fetch).
4. Los stores **importan `container` directamente** (`topicStore.ts:9`).
5. `scriptsStore` **bypasea clean architecture** por completo (sin use case, raw fetch `scriptsStore.ts:95`); la página de settings también es raw.

### Estado, rutas, componentes, servicios, temas

- **Estado**: 3 zustand stores. `topicStore` mezcla datos de servidor + estado de UI; `filters`/`setFilters` **nunca se llaman** (dead); `clearSelection` nunca se llama. `scriptsStore` (lista + seleccionado + mocks). `scriptStudioStore` (548 líneas, mock generators 55-351).
- **Mock generators embebidos en stores** para modo offline (`scriptsStore.ts:8-62`, `scriptStudioStore.ts:55-351`); `getApiBase()` devuelve `""` cuando falta env → mock mode.
- **Rutas** (10, todas client components con wrappers `motion.div`): `/`, `/discover`, `/create`, `/topics`, `/topics/[id]`, `/analytics`, `/studio`, `/scripts`, `/settings`, `/terminal`. **No existen** `error.tsx`/`loading.tsx`/`not-found.tsx`. El Header tiene `<div id="page-header">` (`Header.tsx:28`) "populated via layout portal" — **no existe portal** → div vacío muerto, el título del header siempre en blanco.
- **Lint/typecheck**: `tsc --noEmit` = 0 errores; `next lint` = 5 warnings (imports sin usar: `discover/page.tsx:9` XCircle/Copy, `KPIGrid.tsx:91` 'i', `NicheSelector.tsx:3` clsx, `Terminal.tsx:4` TerminalOutput, `scriptsStore.ts:78` 'get').
- **tsconfig**: `strict: true`; alias `@hooks/*` apunta a `./src/hooks` que **NO EXISTE** (alias muerto).

---

## 3. Parte 2 — Estado del Proyecto

| Ruta | Estado | Detalle |
|---|---|---|
| `/` Dashboard | ✅ IMPLEMENTADA | — |
| `/discover` | ⚠️ IMPLEMENTADA pero con fallas | Conteos vienen de `ApiTopicSource` que devuelve `[]` ante CUALQUIER fallo (`ApiTopicSource.ts:46-60`) → silenciosamente "0 new / 0 duplicates / 0 errors"; además `source_names` nunca matchea el registry backend (`Container.ts:43-45`) → siempre 0 descubiertos en modo API real |
| `/create` | ✅ IMPLEMENTADA | `ManualTopicForm` con validación |
| `/topics` | ✅ IMPLEMENTADA | — |
| `/topics/[id]` | ⚠️ IMPLEMENTADA | Usa dead classes `cyber-*` (`page.tsx:34-49`) |
| `/analytics` | 🔴 STUB | "Coming soon" (`analytics/page.tsx:37-40`) |
| `/studio` | ⚠️ IMPLEMENTADA (3 cols) | Dead-class styling intenso + bug camelCase (approved-topics) |
| `/scripts` | ⚠️ IMPLEMENTADA con bug de mapeo | `scriptsStore.ts:97-102` asigna el JSON snake_case raw, NO usa `mapScriptFromApi` (`utils.ts:20`); `ScriptDetailPanel` lee camelCase (`createdAt:165`, `wordCount:135`) → "Invalid Date"/undefined con API real; funciona solo con mocks |
| `/settings` | 🟡 PARCIAL | Scheduler cableado (status/start/stop/config/run-now), el resto "Coming soon" (316-331) |
| `/terminal` | ✅ IMPLEMENTADA | 11 comandos, tablas ASCII, historial — colores muertos (`cyber-*`) |

- **Rutas huérfanas**: ninguna.
- **Diseñado pero nunca construido**: UI de filtros (`setFilters` nunca llamado), KPI "TrendingUp" estático, campana de notificaciones no funcional (`Header.tsx:77-87`), avatar "OP" estático, portal `#page-header`, `SourceRegistry.list()` nunca usado, `ITopicSource.available` siempre `true`.

**Calificación general**: frontend implementado y funcional en su mayoría (8 de 10 rutas operativas, 1 parcial, 1 stub), con deuda técnica concentrada en estilos muertos, bugs de adaptador y ausencia de tests.

---

## 4. Parte 3 — Reutilización (31 componentes)

Clasificación de los 31 componentes. **NO se elimina nada todavía** — esto es solo inventario y justificación.

### ✅ Reutilizable sin cambios (8)

| Componente | Justificación |
|---|---|
| `ui/Button`, `ui/Card`, `ui/Input`, `ui/StatusBadge` | Genéricos, sin acoplamiento |
| `layout/Sidebar` | Navegación fija |
| `layout/Header` | Reutilizable menos el div muerto del portal |
| `topic/ScoreGauge` | Reutilizable (nota: dead class `animate-pulse-slow` línea 73) |
| `topic/ScoreRadar` | Reutilizable |

### 🟡 Reutilizable con pequeñas mejoras (5)

| Componente | Mejora necesaria |
|---|---|
| `ui/Select` | Usado una sola vez (por `NicheSelector`) |
| `dashboard/TopicCard` | `div` con `onClick` — no accesible por teclado; **bug de matemática del score ring** (línea 118: `dasharray 2.51×score` con `r=25` → circunferencia 157 → el ring se llena con score ≥ 63) |
| `dashboard/TopicList` | Hardwired al store |
| `topic/TopicDetailPanel` | Acoplado al store |
| `forms/ManualTopicForm` | Bien, pero acoplado al store |

### 🔴 Obsoleto / requiere migración de tema (8) — dead classes `cyber-*`

`studio/DurationSelector`, `studio/ToneSelector`, `studio/NicheSelector`, `studio/ScriptDisplay`, `studio/ScriptMetadata`, `studio/TopicQueueItem`, `terminal/Terminal`, `app/topics/[id]/page`

> Justificación: sus estilos dependen de 43 usos de classes `cyber-*` muertas (verificado 0 hits en el CSS compilado `.next/static/css/app/layout.css`), por lo que el estado seleccionado y los colores no se renderizan.

### 🧩 Único (no reutilizable por diseño)

`dashboard/KPIGrid`, `scripts/ScriptsPage`, `scripts/ScriptListItem`, `scripts/ScriptDetailPanel`, `studio/ScriptStudio`, `studio/StudioLayout`, `studio/TopicQueue`, `studio/ConfigPanel`, `studio/OutputPanel`, `studio/ActionButtons`, `layout/DashboardLayout`, y las app pages.

### Sin huérfanos

**ORPHANED: ninguno** — todos los componentes están importados (verificado con grep). Nota: `ScoreGauge` solo lo usa `ScoreRadar`; `Select` solo lo usa `NicheSelector`.

---

## 5. Parte 4 — Gap Analysis Frontend ↔ Runtime

El informe fuente (#357) es un gap analysis **FE ↔ Backend** (18 llamadas vs 3 superficies backend). A continuación la clasificación por capacidad del runtime según la evidencia: qué capacidades existen, dónde viven, y qué soporte tiene hoy el FE para cada una.

### Clasificación por capacidad

| Capacidad | Soporte en el FE | Evidencia |
|---|---|---|
| **Runtime** | ❌ No existe | El FE no habla con `src/runtime/`: es CLI only (`src/runtime/__main__.py`: ingest/feedback/schedule/stats/list-sources/cycle/simulate), **sin superficie HTTP**, con DB propia `ai_shorts` vs la DB de la API `system_shorts` |
| **Scheduler** | ✅ Soporte completo | `GET status`, `GET/PUT config`, `POST start/stop`, `POST run-now` → MATCH (#14-#18) contra `scheduler.py:34-152` (scheduler legacy de `presentation/api`, respaldado por el BC research CONGELADO — no el scheduler del runtime) |
| **Sources** | 🟡 Soporte parcial | `POST /api/v1/discover` MISMATCH (#7): `source_names` del FE nunca matchean el registry backend (solo `google-news-rss`/`mock`); `source_type` backend solo `manual`/`automatic` vs enum FE de 5 valores (`types/index.ts:18-24`) |
| **Pipeline** | 🟡 Soporte parcial | Script generate/regenerate/get → MATCH (#10, #11, #12), pero `GET /api/v1/scripts` MISMATCH (#13) y el `niche` enviado por el Studio es **ignorado** por el backend (`GenerateScriptRequest` lee solo `duration`+`tone`, `application/dtos/script.py:130-139`) |
| **Feedback** | ✅ Soporte completo | `POST approve` / `POST reject?reason=` → MATCH (#3, #4) contra `topics.py:175,208` |
| **Learning** | ❌ No existe en el FE | La Learning API (`src/learning/presentation/app.py`: analytics, feedback, prediction, recommendation) existe con **cero consumidores**; el FE no consume ninguna de sus métricas |
| **Analytics** | ❌ No existe (STUB) | `/analytics` = "Coming soon"; las métricas que necesita (Top-K Precision, Acceptance Rate, Feedback Coverage, Dataset Growth, ventanas 7d/30d) viven en el `MetricSnapshot` del runtime pero no se exponen ni consume |
| **Simulation** | ❌ No existe | `simulate` existe solo como comando CLI del runtime (`runtime simulate`) |
| **Datasets** | ❌ No existe | Sin soporte en el FE |
| **Artifacts** | ❌ No existe | Sin soporte en el FE |
| **Monitoring** | 🟡 Soporte parcial | `GET /api/v1/status` MATCH (#6) expone version/uptime/counts, pero sin observabilidad de runtime |
| **Traceability** | ❌ No existe | Sin soporte en el FE |
| **Jobs** | 🟡 Soporte parcial | `POST /api/v1/scheduler/run-now` MATCH (#18) como disparador puntual; sin gestión de jobs |
| **Validation** | 🟡 Soporte parcial | Solo validación client-side de `ManualTopicForm` (title ≥ 3 chars + prefijo URL http); sin validación server-side por campo |
| **Storage** | ❌ No existe en el FE | El FE no toca persistencia; existen DOS DBs sin unificar (`ai_shorts` runtime vs `system_shorts` API) |

### Cobertura funcional determinada

De las 18 llamadas del FE, el gap analysis clasifica: **15 MATCH / 3 MISMATCH / 0 MISSING-BACKEND** — el FE **NO está huérfano**, pero habla con la API legacy servida sobre el BC research congelado, mientras que la arquitectura nueva (Ingestion API diseñada + Runtime CLI) lo supera por completo.

---

## 6. Parte 5 — Backend Integration

### Inventario de las 18 APIs consumidas por el FE

Base URL: `NEXT_PUBLIC_API_URL` (`.env.local` → `http://172.23.214.85:8001`, fallback `http://localhost:8000`).

| # | FE call (archivo:línea) | Método + Path |
|---|---|---|
| 1 | `ApiTopicRepository.ts:83`, `Terminal.tsx:145` | `GET /api/v1/topics?status&source&q&min_score&limit` |
| 2 | `ApiTopicRepository.ts:98` | `GET /api/v1/topics/{id}` |
| 3 | `ApiTopicRepository.ts:152`, `Terminal.tsx:200` | `POST /api/v1/topics/{id}/approve` |
| 4 | `ApiTopicRepository.ts:166`, `Terminal.tsx:231` | `POST /api/v1/topics/{id}/reject?reason=` |
| 5 | `ApiTopicRepository.ts:186` | `POST /api/v1/topics/manual` |
| 6 | `ApiTopicRepository.ts:216`, `Terminal.tsx:456` | `GET /api/v1/status` |
| 7 | `ApiTopicSource.ts:36`, `Terminal.tsx:261` | `POST /api/v1/discover {query,limit,source_names}` |
| 8 | `scriptStudioStore.ts:382` | `GET /api/v1/studio/approved-topics` |
| 9 | `scriptStudioStore.ts:433` | `GET /api/v1/studio/recommendations/{topic_id}` |
| 10 | `scriptStudioStore.ts:486`, `Terminal.tsx:309` | `POST /api/v1/topics/{topicId}/script/generate` |
| 11 | `Terminal.tsx:339` | `GET /api/v1/topics/{topicId}/script` |
| 12 | `Terminal.tsx:369` | `POST /api/v1/topics/{topicId}/script/regenerate` |
| 13 | `scriptsStore.ts:95` | `GET /api/v1/scripts` |
| 14 | `settings/page.tsx:46,128` | `GET /api/v1/scheduler/status` |
| 15 | `settings/page.tsx:47` | `GET /api/v1/scheduler/config` |
| 16 | `settings/page.tsx:66` | `POST /api/v1/scheduler/start\|stop` |
| 17 | `settings/page.tsx:96` | `PUT /api/v1/scheduler/config` |
| 18 | `settings/page.tsx:121` | `POST /api/v1/scheduler/run-now` |

Sin headers de auth en ninguna llamada. Sin abstracción de cliente API más allá de raw fetch.

### Las 3 superficies backend disponibles hoy

| Superficie | Estado | Consumidores |
|---|---|---|
| **1. `presentation/api/` (legacy servida)** — puerto 8001 (`.env`; default 8000), 17 endpoints + root/docs; respaldada por `research/application/*`, `research/infrastructure/persistence/*` (Postgres `system_shorts`), `application/use_cases/script/*` + `postgres_script_repository`, `domain/exceptions` | SERVIDA (construida 29-30 de junio, lockstep con el FE) | **El FE (18/18 llamadas)** |
| **2. Ingestion API diseñada** — `src/ingestion/presentation/app.py:99-204` (sources/feeds/articles/categories/topics + `/health/live` `/health/ready`); docs `api-design.md` = **29 endpoints** con envelope `{status,data,meta}`, errores RFC9457, paginación; router `topics.py:75-179` IMPLEMENTADO (CRUD+activate/deactivate) | DISEÑADA, SIN launcher, **cero consumidores**; docs drift: `api-design.md:23,494-502` aún dice 501 stubs | Ninguno |
| **3. `src/runtime/` CLI** — `src/runtime/__main__.py`; contratos internos en `src/runtime/contracts/*.py`; DB propia `ai_shorts` | CLI only, **sin HTTP** | Ninguno (CLI manual) |

> La Ingestion API y el runtime **postdatan** al par FE+API (julio vs junio): el FE fue construido contra un contrato que nunca se formalizó en los design docs, y los design docs describen un contrato que el FE nunca consume.

### Matriz Frontend → API → Estado (15 MATCH / 3 MISMATCH)

| FE call | BE served endpoint | Estado |
|---|---|---|
| `GET /api/v1/topics` (+status,source,q,min_score,limit) | `topics.py:82` | ✅ MATCH (post-filters in-memory, `asdict(ResearchTopicDTO)`+count) |
| `GET /api/v1/topics/{id}` | `topics.py:152` | ✅ MATCH |
| `POST /api/v1/topics/{id}/approve` | `topics.py:175` | ✅ MATCH (query `auto_generate`; `{topic,events}`) |
| `POST /api/v1/topics/{id}/reject?reason=` | `topics.py:208` | ✅ MATCH (`{topic,events}`) |
| `POST /api/v1/topics/manual` | `topics.py:237` | ✅ MATCH (`{topic,is_duplicate,events}`) |
| `GET /api/v1/status` | `discover.py:89` | ✅ MATCH |
| `POST /api/v1/discover` | `discover.py:42` | ❌ **MISMATCH (bug #7)**: FE envía `source_names` `[google-news,twitter,rss]` (`ApiTopicSource.ts:42`) — registry backend solo `google-news-rss`/`mock` (`presentation/cli/container.py:252-254`) → siempre 0 descubiertos; Terminal funciona porque omite `source_names` |
| `GET /api/v1/studio/approved-topics` | `studio.py:35` | ❌ **MISMATCH (bug #8)**: `asdict(ResearchTopicDTO)` snake_case asignado directo a `TopicData` camelCase (`scriptStudioStore.ts:382`) → `scoreTotal`/`sourceName`/`createdAt` undefined → "undefined pts" (`TopicQueueItem.tsx:78`) |
| `GET /api/v1/studio/recommendations/{topicId}` | `studio.py:61` | ✅ MATCH |
| `POST /api/v1/topics/{topicId}/script/generate` | `scripts.py:81` | ✅ MATCH (lee `duration`,`tone` only — niche ignorado; 201) |
| `POST /api/v1/topics/{topicId}/script/regenerate` | `scripts.py:131` | ✅ MATCH |
| `GET /api/v1/topics/{topicId}/script` | `scripts.py:49` | ✅ MATCH (404 si no existe) |
| `GET /api/v1/scripts` | `script_list.py:31` | ❌ **MISMATCH (bug #13)**: `word_count`/`is_valid`/`created_at` vs `wordCount`/`isValid`/`createdAt` (`ScriptDetailPanel.tsx:48,135,165-166`) → "Invalid Date"/undefined |
| `GET /api/v1/scheduler/status` | `scheduler.py:34-46` | ✅ MATCH |
| `POST /api/v1/scheduler/start\|stop` | `scheduler.py:52-81` | ✅ MATCH |
| `POST /api/v1/scheduler/run-now` | `scheduler.py:84-97` | ✅ MATCH |
| `GET/PUT /api/v1/scheduler/config` | `scheduler.py:103-152` | ✅ MATCH |

### Endpoints faltantes, obsoletos, duplicación, lógica y acoplamiento

- **Faltantes**: ninguno — los 18 endpoints existen. Único port latente sin endpoint: `findByDuplicateHash` (`ApiTopicRepository.ts:113-115`, devuelve `[]`, nunca se llama).
- **Obsoletos / sin consumidores**: la Ingestion API diseñada completa (29 endpoints), toda la Learning API, y todos los contratos de `src/runtime/contracts/*`.
- **Duplicación**: **dual `/api/v1/topics`** — el research congelado lo usa para approve/reject, la Ingestion API diseñada para CRUD+activate/deactivate.
- **Lógica movida al frontend**: mock generators embebidos en stores (~190 líneas); filtros de topics como post-filters in-memory del backend; la política de `source_names` de discover; la lógica de score colors duplicada en 4 lugares.
- **Acoplamiento**: FE acoplado al contrato legacy servido sobre el BC research congelado; stores importando `container` directamente; `scriptsStore` bypaseando clean architecture; CORS: allowlist default `localhost:3000,3001` (`app/config.py:169-175`) vs origen LAN del FE → fallo de CORS si el FE se sirve desde un origen no-localhost; base URL con IP LAN hardcodeada en `.env.local` commiteado.

---

## 7. Parte 6 — UX Audit

- **Consistencia visual**: diseño GlassOS cyberpunk cohesivo (`tailwind.config.ts` paletas base/glass/neon, 11 animaciones, glow shadows; `globals.css` background layers, orbs, grid-scroll) — **EXCEPTO** por las dead classes `cyber-*` que rompen los selectors del studio (estado seleccionado/no-seleccionado idéntico), los colores del Terminal y los acentos del header de `topics/[id]`.
- **Navegación**: sidebar fija de 256px (`Sidebar.tsx:52` `w-64`) + main `pl-64` (`DashboardLayout.tsx:42`) — **sin breakpoint mobile/tablet** → en pantalla de 375px el contenido queda con ~119px; responsive efectivamente roto. El search del header "Search topics or discover..." en realidad **dispara DISCOVERY** (`Header.tsx:45`), no filtra — label engañoso.
- **Loading/empty/error**: BUENO en `TopicList` (skeletons + retry), `ScriptStudio`, `ScriptsPage`, `topics/[id]` — pero **errores tragados** en el flujo de discover; `TopicDetailPanel` sin retry (empty genérico).
- **Formularios**: `ManualTopicForm` valida title ≥ 3 chars + prefijo URL http; sin error server-side por campo (el store devuelve `success:false` → "Failed" genérico).
- **Accesibilidad**: faltan `aria-labels` (Bell `Header.tsx:77`, avatar, input del Terminal); `TopicCard` con `div onClick` no accesible por teclado; toggle `motion.button` sin `role=switch`/`aria-pressed` (`settings/page.tsx:254-279`); fuentes `text-[8px]/[9px]`; `gray-600` sobre `#0A1A2E` con bajo contraste; sin dark-mode toggle; `favicon.ico` referenciado (`layout.tsx:10`) pero **NO existe `public/`** → 404.
- **Legibilidad del dashboard**: KPI micro-bars `value×8%` (`KPIGrid.tsx:45`); bug del score ring (`TopicCard.tsx:118`); lógica de colores de score **duplicada en 4 lugares** (`TopicCard` 28-47, `TopicQueueItem` 31-43, `ScriptListItem` 61-66, `ScriptDetailPanel` 151-156).

---

## 8. Parte 7 — Modernization Strategy

### Las 4 opciones (coste / riesgo / impacto)

| Opción | Coste | Riesgo | Impacto en BCs congelados | Desbloquea | Rompe |
|---|---|---|---|---|---|
| **A — Maintain** | ~1 sem | Muy bajo | Ninguno | 3 calls corregidas + doc de contrato | Nada; el FE sigue sobre el BC research congelado, analytics sigue stub, sin tests/mobile |
| **B — Partial refactor** | ~5-8 sem | Bajo-Medio | **NINGUNO (todo FE-side)** | Dashboard usable, baseline de tests, mobile, analytics tier-1, consistencia visual | Nada |
| **C — Major restructure** | ~12-20 sem | Alto | Necesita excepciones ADR+ARB (endpoints research, persistencia si se unifica DB) | Contrato único, gestión de sources/feeds, métricas de learning en el FE, historia de DB | 18 FE calls, dual `/api/v1/topics` requiere versioning, wiring del scheduler, flujos del studio |
| **D — Full rewrite** | ~16-32+ sem | Muy alto | Excepciones + contrato completo | Greenfield | Todo; descarta ~6500 líneas de un FE genuinamente en capas |

### SELECCIÓN ÚNICA: B (Refactor parcial) ahora → C-lite como decisión diferida

**Por qué B ahora:**
1. **15/18 FE calls ya MATCH** la API servida (obs #357) — el gap de modernización son **3 mappers + polish, NO un gap de contrato**.
2. B **toca cero código congelado** — seguro bajo el régimen de freeze (Foundation/Ingestion/Research/Learning congelados; excepciones requieren ADR+ARB según ADR-021 + `freeze-review.md`).
3. El layering del FE es **genuinamente limpio** (ports/adapters, DI, TS strict, tsc clean — obs #360); D descartaría valor arquitectónico real sin evidencia.

**Por qué C-lite después, no ahora:**
- La Ingestion API diseñada (`src/ingestion/presentation`) **NO puede expresar el workflow core del FE** — approve/reject/manual/scheduler son operaciones de dominio del BC research sobre código congelado. "Migración" es en realidad un **problema de FACADE**.
- El host correcto del facade es la **capa runtime NO congelada** (EPIC 8 cerrado 2026-08-03, orquestación delgada per AD-001, BCs intactos per AD-002, DB propia `ai_shorts`, y tiene las métricas de learning que el stub de analytics necesita).
- **C-lite = superficie HTTP del runtime (`/api/v2`)** que proxea los endpoints research congelados + sirve métricas del runtime; el FE cambia base URL + mappers vía su capa de adapters. El dual `/api/v1/topics` se resuelve **por versioning** (sin tocar routers congelados). La unificación de DB es opcional — **se prefiere read-side projection**/endpoint de métricas para evitar excepciones de persistencia.

**Por qué NO D:** sin evidencia; el FE está ~70% construido, con identidad GlassOS cohesiva y wiring de scheduler funcional.

---

## 9. Parte 8 — Dashboard Vision

### Módulos conceptuales (cyberpunk control room) e IA / navegación

Arreglar el sprawl de 10 rutas **agrupando, no borrando**:

| Grupo | Pantallas |
|---|---|
| **OBSERVE** | Dashboard (`/`), Analytics (`/analytics`) |
| **DISCOVER** | Discover (`/discover`), Topics (`/topics` + `/topics/[id]`), Create (`/create`) |
| **PRODUCE** | Studio (`/studio`), Scripts (`/scripts`) |
| **OPERATE** | Terminal (`/terminal`), Settings (`/settings`) |

Refleja el flujo acquire → review → produce → operate y los clusters de la API servida.

### Responsabilidades de cada pantalla

- **Dashboard** (`/`): KPIs desde `GET /api/v1/status` (`topics.found/pending_review/approved/rejected`, `total_topics`, `version`, `api_version`, `uptime_seconds`) + card de estado del scheduler (enabled, is_running, last_run, interval_minutes, queries).
- **Discover** (`/discover`): superficie `{discovered,duplicates,errors}` — **NUNCA tragar errores** (`ApiTopicSource.ts:46-60` devuelve `[]` ante fallo).
- **Topics / Create**: gestión y creación manual de topics.
- **Studio** (`/studio`): approved-topics mapeados + recommendations (tone/duration/niche/reasoning); **ocultar niche** (el backend lo ignora).
- **Scripts** (`/scripts`): listado de scripts con mapeo correcto de fechas/counts.
- **Analytics** (`/analytics`): tier-1 = funnel + approval rate + script throughput desde endpoints status/topics/scripts; tier-2 = `MetricSnapshot` del runtime (Top-K Precision, Acceptance Rate, Feedback Coverage, Dataset Growth, ventanas 7d/30d).
- **Terminal** (`/terminal`): operaciones CLI-ish contra la API servida.
- **Settings** (`/settings`): scheduler + resto de configuración.

### Consolidación de componentes

- `PageHeader` compartido (reemplaza 10× bloques de header duplicados + el div muerto `#page-header`, `Header.tsx:28`).
- El search del header → `GET /api/v1/topics?q=` para navegación en vez de disparar discovery (`Header.tsx:45`).
- Cablear la campana al estado del scheduler o eliminarla (`Header.tsx:77-87`).
- Añadir `error.tsx`/`loading.tsx`/`not-found.tsx`.

### Estrategia de estado y datos

- **Mantener zustand** (3 stores); **un único cliente HTTP** en `infrastructure/` (timeout, abort, normalización de errores) reemplazando los 5 estilos de fetch; disciplina de server-state `{data,loading,error}` por entidad; los stores dejan de importar `container` (`topicStore.ts:9`).
- **LOS 3 BUGS RECIBEN MAPPERS** en la capa de infrastructure: `mapApprovedTopic` (#8), cablear el `mapScriptFromApi` existente en `scriptsStore` (#13), discover result mapper + política de source-name (#7) — omitir `source_names` (el Terminal demuestra que funciona) o enviar nombres válidos del registry.
- **Quitar ~190 líneas de mock generators** (o gatearlas detrás de `NEXT_PUBLIC_MOCK_MODE` explícito; corregir la escala de mocks 0-10 vs UI 0-100, `scriptStudioStore.ts:67`).
- **Quitar código muerto**: `setFilters`/`clearSelection`, `repository.save/saveMany/delete/findByDuplicateHash`, types duplicados (`TopicFilters`, `KPIStats`/`KPIResult`, `ManualTopicInput`, `CreateTopicResult`), alias muerto `@hooks/*`, `getKPIStats`.

### Tema, mobile, testing, a11y

- **Tema**: barrido de 43 dead classes `cyber-*` + `bg-glass-white` + `animate-pulse-slow` → tokens neon/glass existentes en 10 archivos (studio ×6, terminal, `topics/[id]`, `ScoreGauge.tsx:73`); `lib/score.ts` único para colores de score (duplicado 4×); corregir la matemática del ring (`TopicCard.tsx:118` factor 2.51 vs `r=25` circunferencia 157 → `(score/100)×157`); check de CI para dead classes en CSS compilado.
- **Mobile**: `DashboardLayout` `pl-64` → `md:pl-64` (`:42`); `Sidebar` `w-64` → hidden `<md` con overlay drawer + hamburger (`:52`); studio 1-col mobile → `lg:3-col` (`StudioLayout.tsx:16`); tabla de scripts → card stack `<md`; viewport meta.
- **Testing (hoy cero)**: vitest + @testing-library/react + jsdom; orden: 1) mappers (los 3 bugs), 2) stores con cliente mockeado, 3) 5 use-cases, 4) componentes (TopicCard ring math, KPIGrid, StatusBadge, ManualTopicForm validation, ScriptDetailPanel dates), 5) adapters vs fetch mockeado, 6) Playwright E2E discover→approve→script (tier opcional). CI: tests + coverage ≥80% en infrastructure/application/store + tsc + lint.
- **A11y**: `TopicCard` div-onClick → button (teclado); aria-labels (Bell, avatar, input del terminal); toggle → `role=switch` + `aria-checked` (`settings/page.tsx:254-279`); quitar `text-[8px]/[9px]`; corregir contraste `gray-600` sobre `#0A1A2E`; `html lang` + favicon (no hay `public/` → 404); boundaries error/loading/not-found; skip-to-content, focus-visible, prefers-reduced-motion.

---

## 10. Parte 9 — Roadmap

Camino B ≈ 7-8 semanas secuenciales (~5-6 semanas en paralelo); C-lite agrega 5-8 semanas después del gate.

| Sprint | Alcance | Tamaño / Duración | Dependencia | Exit criteria |
|---|---|---|---|---|
| **P0 — Contract stabilization & adapter bugs** | 3 mappers + política de `source_names` en discover; documentar el contrato servido | S / ~1 sem | ninguna | Modo API real correcto en studio/scripts/discover; sin "undefined pts"/"Invalid Date" |
| **P1 — Theme sweep** | `cyber-*` → tokens neon, ring math, score helper, PageHeader compartido, relabel del search | S / ~1 sem | P0 | 0 hits de dead classes en CSS compilado (check CI) |
| **P2 — Mobile pass** | Sidebar drawer, studio stack, scroll de tablas, viewport | S-M / ~1 sem | P1 | 375px usable, lighthouse mobile en verde |
| **P3 — Test baseline** | vitest setup; tests de mapper/store/use-case/componente | M / ~2 sem | P0 (paralelo a P1/P2) | Coverage ≥80%, CI verde |
| **P4 — Data/config hygiene** | httpClient único, quitar/gatear mocks, código muerto + types duplicados, estrategia env (`.env.example`, alineación CORS, sacar IP LAN commiteada) | M / ~1.5 sem | P3 | Un solo estilo de fetch, tsc+lint limpios |
| **P5 — Analytics tier-1** | Funnel, approval rate, scheduler health desde endpoints servidos | S-M / ~1 sem | P0+P3 | `/analytics` renderiza datos reales |
| **P6 — API-surface decision gate** | Usuario + ARB eligen keep-legacy vs runtime facade; ADR-030 (alcance de la superficie HTTP del runtime) si facade; estrategia de DB (unificar vs read-side — **recomendado read-side**); versioning para el dual `/api/v1/topics` | S (proceso) / ~1 sem | P5 | Decisión registrada |
| **P7 — Analytics tier-2 + facade opcional** | Endpoint de métricas del runtime + charts (tier-2), O facade `/api/v2` + swap del FE (18 calls vía capa de adapters) | M-L / ~2-6 sem | P6 | Paridad con tier-1 + API legacy decommissioned/feature-flagged |

**MUST NOT touch:** BC `research/` (domain/application/infrastructure/persistence), Foundation, capas congeladas de Ingestion/Learning, presentation design docs (congelados; cambios de diseño requieren ADR), código servido de `presentation/api` (respaldado por el BC research congelado — **los bugs se arreglan FE-side solamente**).

**Excepciones de freeze (solo camino P6/P7):** superficie HTTP del runtime = scope nuevo vs ADR-026/027 → **ADR-030 + ARB** (ventana natural: ARB audit del Epic 6.6 NO INICIADO); unificación de DB = excepción de persistencia → **EVITAR** vía read-side projection; dual topics → **versioning, sin excepción**.

---

## 11. Entregables consolidados (checklist)

| # | Entregable | Estado | Fuente |
|---|---|---|---|
| 1 | Auditoría completa (arquitectura + estado + UX + reutilización) | ✅ | #360 (partes 1-3, 6, 10-12) |
| 2 | Inventario de componentes (31) | ✅ | #360 (parte 3) |
| 3 | Inventario de rutas (10) | ✅ | #360 (partes 1-2) |
| 4 | Inventario de APIs consumidas (18) | ✅ | #357 (parte 5) |
| 5 | Gap analysis FE↔Backend (15 MATCH / 3 MISMATCH / 0 missing) | ✅ | #357 (parte 4) + #360 (parte 11 corregida) |
| 6 | Estado arquitectónico (clean/hexagonal parcial, violaciones) | ✅ | #360 (parte 1) |
| 7 | Deuda técnica (15 ítems) | ✅ | #360 (parte 12) |
| 8 | Componentes reutilizables (8 + 5 parciales) | ✅ | #360 (parte 3) |
| 9 | Componentes obsoletos (8 con dead classes `cyber-*`) | ✅ | #360 (parte 3) |
| 10 | Estrategia (B ahora → C-lite diferida) | ✅ | #363 (parte 7) |
| 11 | Roadmap (P0..P7) | ✅ | #363 (parte 9) |
| 12 | Informe ejecutivo (veredicto corregido) | ✅ | Consolidación (sección 1) |

---

## 12. Restricciones y límites

- **READ-ONLY**: este Sprint F0 no produce código. No se modificó ni un solo archivo de `frontend/`.
- **No tocar los Bounded Contexts congelados**: Foundation, Ingestion, Research, Learning. Toda excepción requiere ADR+ARB (ADR-021 + `freeze-review.md`).
- **No eliminar nada del repo**: la clasificación de componentes obsoletos (sección 4) es inventario; la eliminación/refactor es decisión de sprints futuros.
- **No asumir tecnologías**: toda afirmación de este documento está respaldada por evidencia de los tres informes fuente (#360, #357, #363), que a su vez citan archivos y líneas verificados.
- **Sin builds ni tests** en este sprint.

---

## 13. Decisiones pendientes (next_recommended consolidado)

Decisiones consolidadas de los tres informes (deduplicadas):

1. **Estrategia de superficie de API (decision gate, P6)** — elegir UNA fuente de verdad de contrato: (a) mantener la API legacy servida `presentation/api` (BC research congelado debajo), (b) migrar el FE a la Ingestion API diseñada (rompe 18 FE calls; requiere launcher + CORS + re-mapeo de approve/reject/manual/scheduler que viven en el BC research congelado), o (c) el runtime gana superficie HTTP / se vuelve el executor detrás de la API servida. Unificar el split de DB `ai_shorts` vs `system_shorts`. Resolver el dual `/api/v1/topics`.
2. **Aprobar la estrategia B ahora** con P6 como decision gate — **NO comprometerse a C hoy**.
3. **Adoptar fixes FE-side con mappers para los 3 bugs** (riesgo cero sobre backend/BC congelados) — rechazar cualquier cambio de contrato backend para estos bugs.
4. **Theme cleanup**: eliminar dead classes `cyber-*` → tokens neon (mecánico, ~10 archivos).
5. **Mock-mode policy**: borrar vs gate explícito (`NEXT_PUBLIC_MOCK_MODE`).
6. **Tests**: vitest + RTL (+Playwright después) — hoy el FE tiene **cero tests**.
7. **Mobile layout pass** (collapse de sidebar, studio stack).
8. **Analytics**: tier-1 con agregación local primero; el endpoint de métricas del runtime (tier-2) es el C-spike de-riesgado.
9. **CORS/env alignment + estrategia de auth** para la API servida (hoy sin auth en ninguno de los dos lados).
10. **Confirmar el proceso de excepciones de freeze para el gate** (timing del borrador de ADR-030 vs ventana del ARB del Epic 6.6).

---

*Documento generado por el sub-agente de consolidación del Sprint F0. Fuentes: Engram obs #360 (`sdd/sprint-f0/explore-frontend`), #357 (`sdd/sprint-f0/explore-backend`), #363 (`sdd/sprint-f0/explore-strategy`).*
