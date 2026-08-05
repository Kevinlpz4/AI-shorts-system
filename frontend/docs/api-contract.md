# Contrato FE ↔ API servida — AI_Shorts_System

> **Fecha**: 2026-08-04
> **Estado**: 15 MATCH + 3 FIXED (P0) + 0 missing
> **Fuente**: inventario canónico de F0 §6 (`docs/sprints/sprint-f0-frontend-audit-and-modernization.md`, líneas 189-208) y matriz de integración (224-242). Este documento es la referencia operativa del contrato que el frontend consume hoy.

## 1. Intro

El frontend (`frontend/`, Next.js 14 + Zustand + TypeScript strict) consume **la API servida legacy `presentation/api/`**, que vive **sobre el BC `research/` CONGELADO**. Cualquier fix a estos endpoints es **FE-side únicamente** (mappers en la capa infrastructure); el backend no se toca (requiere ADR+ARB, ADR-021).

- **Base URL**: `NEXT_PUBLIC_API_URL` (`.env.local` → `http://172.23.214.85:8001`; fallback `http://localhost:8000`). Sin la env var, `getApiBase()` devuelve `""` → **mock mode** (mocks embebidos en stores, sin llamadas HTTP).
- **Superficie**: `presentation/api/` — puerto 8001 (`.env`; default 8000), 17 endpoints + root/docs.
- **Resultado del P0 (contract stabilization)**: los 3 mismatches de adaptador (#7 discover, #8 studio approved-topics, #13 scripts list) quedan **FIXED** con mappers FE-side → **18/18 endpoints con contrato alineado**.

## 2. Inventario de los 18 endpoints

| # | Método + Path | Call site FE | Handler backend | Estado |
|---|---|---|---|---|
| 1 | `GET /api/v1/topics?status&source&q&min_score&limit` | `ApiTopicRepository.ts:83`, `Terminal.tsx:145` | `topics.py:82` | ✅ MATCH |
| 2 | `GET /api/v1/topics/{id}` | `ApiTopicRepository.ts:98` | `topics.py:152` | ✅ MATCH |
| 3 | `POST /api/v1/topics/{id}/approve` | `ApiTopicRepository.ts:152`, `Terminal.tsx:200` | `topics.py:175` | ✅ MATCH |
| 4 | `POST /api/v1/topics/{id}/reject?reason=` | `ApiTopicRepository.ts:166`, `Terminal.tsx:231` | `topics.py:208` | ✅ MATCH |
| 5 | `POST /api/v1/topics/manual` | `ApiTopicRepository.ts:186` | `topics.py:237` | ✅ MATCH |
| 6 | `GET /api/v1/status` | `ApiTopicRepository.ts:216`, `Terminal.tsx:456` | `discover.py:89` | ✅ MATCH |
| 7 | `POST /api/v1/discover` | `ApiTopicSource.ts:36`, `Terminal.tsx:261` | `discover.py:42` | ✅ **FIXED** (P0, bug #7) |
| 8 | `GET /api/v1/studio/approved-topics` | `scriptStudioStore.ts:382` | `studio.py:35` | ✅ **FIXED** (P0, bug #8) |
| 9 | `GET /api/v1/studio/recommendations/{topic_id}` | `scriptStudioStore.ts:433` | `studio.py:61` | ✅ MATCH |
| 10 | `POST /api/v1/topics/{topicId}/script/generate` | `scriptStudioStore.ts:486`, `Terminal.tsx:309` | `scripts.py:81` | ✅ MATCH |
| 11 | `GET /api/v1/topics/{topicId}/script` | `Terminal.tsx:339` | `scripts.py:49` | ✅ MATCH |
| 12 | `POST /api/v1/topics/{topicId}/script/regenerate` | `Terminal.tsx:369` | `scripts.py:131` | ✅ MATCH |
| 13 | `GET /api/v1/scripts` | `scriptsStore.ts:95` | `script_list.py:31` | ✅ **FIXED** (P0, bug #13) |
| 14 | `GET /api/v1/scheduler/status` | `settings/page.tsx:46,128` | `scheduler.py:34-46` | ✅ MATCH |
| 15 | `GET /api/v1/scheduler/config` | `settings/page.tsx:47` | `scheduler.py:103-152` | ✅ MATCH |
| 16 | `POST /api/v1/scheduler/start\|stop` | `settings/page.tsx:66` | `scheduler.py:52-81` | ✅ MATCH |
| 17 | `PUT /api/v1/scheduler/config` | `settings/page.tsx:96` | `scheduler.py:103-152` | ✅ MATCH |
| 18 | `POST /api/v1/scheduler/run-now` | `settings/page.tsx:121` | `scheduler.py:84-97` | ✅ MATCH |

> Los call sites FE referencian el inventario canónico de F0 §6 (código pre-P0); el P0 no movió ningún call site, solo agregó mappers en la rama API de los stores y del adapters.

## 3. Autenticación y CORS

- **Autenticación**: NINGUNA. Ninguna de las 18 llamadas envía headers de auth.
- **CORS**: la API servida usa allowlist default `localhost:3000,3001` (`app/config.py:169-175`). Si el FE se sirve desde un origen no-localhost (p.ej. una IP LAN), las llamadas fallan por CORS — la base URL con IP LAN commiteada en `.env.local` es deuda conocida (P4 del roadmap).

## 4. Notas de campos

### #7 — `POST /api/v1/discover`: política `source_names` (FIXED P0)
El FE **NO envía** `source_names`: los nombres anteriores (`google-news`/`twitter`/`rss`) no existen en el registry backend (solo `google-news-rss`/`mock`) → `SourceNotAvailableError` → skip silencioso → **0 descubiertos**. Sin la key, `discover.py` usa las fuentes default (`auto_discover.py:165` `get_all_available()`). Cambios FE:
- `ApiTopicSource.fetch` → body `{ query?, limit }` (sin `source_names`).
- `Container.ts` → el registry registra **UNA** `ApiTopicSource` (antes 3) → `DiscoverTopics.execute` emite exactamente **1 POST** por ejecución (el backend persiste vía `auto_discover.py:140` y deduplica cross-call).

### #8 — `GET /api/v1/studio/approved-topics`: snake → camel (FIXED P0)
El backend sirve `asdict(ResearchTopicDTO)` en snake_case (`score_total`, `source_name`, `created_at`). Fix FE: `scriptStudioStore.loadApprovedTopics` mapea cada elemento con `mapApprovedTopic` (= `mapTopicFromApi`, `infrastructure/api/mappers.ts`) → `TopicData` camelCase (`scoreTotal`, `sourceName`, `createdAt`). `TopicQueueItem` renderiza `{scoreTotal} pts` y `timeAgo(createdAt)` válidos — sin "undefined pts" ni "Invalid Date".

### #13 — `GET /api/v1/scripts`: snake → camel + enrich (FIXED P0)
El backend sirve `word_count`/`is_valid`/`created_at`/`updated_at` más `topic_title`/`topic_score`/`topic_status` (`script_list.py:66-76`). Fix FE: `scriptsStore.loadScripts` reutiliza `mapScriptFromApi` (`lib/utils.ts`, NO duplicado) → `wordCount`/`isValid`/`createdAt`/`updatedAt`, y hace passthrough de `topic_*` (snake_case, tal cual los declara `ScriptWithTopic`). `ScriptDetailPanel` muestra fechas válidas y scores del topic.

### Mapper compartido (SCEN-4, cero drift)
`mapTopicFromApi` (nuevo en `infrastructure/api/mappers.ts`) es la extracción verbatim de `ApiTopicRepository._mapResponse` con formas strict-safe; lo usan `ApiTopicRepository._mapResponse`, `ApiTopicSource._mapTopic` (con fallback `sourceName`) y `mapApprovedTopic`. Cero cambio de comportamiento en endpoints que ya MATCH (#1-#6, #9).

### Fallback silencioso `[]` de `ApiTopicSource` (pre-existente, FUERA de P0)
`ApiTopicSource.fetch` devuelve `[]` ante CUALQUIER fallo de red/HTTP (`try/catch` + `!response.ok`). Esto puede enmascarar "0 descubiertos" sin error visible. Es comportamiento pre-existente y NO se tocó en P0 (visión P8/P4-P5: descubrir nunca debe tragar errores).

## 5. Cómo se verifica

- Gates estáticos: `tsc --noEmit` (0 errores) + `next lint` (≤ 5 warnings baseline, sin nuevos). NO builds.
- Mock mode: sin `NEXT_PUBLIC_API_URL` → `getApiBase() === ""` → mocks en-store intactos (las 3 rutas studio/scripts/discover funcionan offline).
- Modo API real: requiere backend servido + env → verificación manual (fuera del gate estático).
