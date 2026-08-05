# Integración Frontend ↔ Runtime (read-only) — AI_Shorts_System

> **Fecha**: 2026-08-05
> **Change**: `sprint-p1-runtime-integration`
> **Estado**: implementado (fases 1-4); verificación de rutas en fase 5.

## 1. Arquitectura — 3 tiers

| Tier | Qué | Cómo | Etiqueta |
|---|---|---|---|
| **1 — Runtime (route handlers)** | Datos vivos del runtime: catálogo de fuentes, config, versión, liveness del daemon, artefactos en disco | Route handlers Next.js `frontend/src/app/api/runtime/*` (server-only): subprocess `.venv/bin/python3` + filesystem del repo root | `REAL` |
| **2 — Legacy reutilizado** | Scheduler y monitoring del **research BC** (API servida `presentation/api/`, congelada) | Mismo fetch pattern que `settings/page.tsx`: `getApiBase()` + `{base}/api/v1/*` | `LEGACY` |
| **3 — Brechas** | Pipeline, jobs, feedback queue viva, learning metrics vivas → no observables desde el FE | Documentadas en UI (`UnavailablePanel`) y en este doc | `NA` |

```
browser ── GET /runtime ──► runtimeStore (zustand, 6 secciones, fetch paralelo)
   ├─ runtime/sources/learning/feedback ──► /api/runtime/* (route handler, mismo origen)
   │                                          ├─ subprocess .venv/bin/python3 -c SCRIPT (fuentes, config)
   │                                          ├─ pgrep (liveness) + fs read __main__.py (versión)
   │                                          └─ fs read repoRoot/simulation_reports + feedback_session_*.json
   └─ scheduler/monitoring ──► {NEXT_PUBLIC_API_URL}/api/v1/* (legacy, sin cambios)
```

## 2. Endpoints usados

### 2.1 Route handlers NUEVOS (fase 1-2, ya implementados)

| Endpoint | Método | Contrato de respuesta |
|---|---|---|
| `/api/runtime/info` | GET | `{status, version, config, is_running, venv_available, repo_root?, liveness_check?}` |
| `/api/runtime/sources` | GET | `{status:"ok", sources[], count}` \| `{status:"unavailable", message, hint}` |
| `/api/runtime/learning/reports` | GET | `{status:"ok", simulated:true, note, reports[]}` \| `{status:"empty", reports:[]}` |
| `/api/runtime/feedback/exports` | GET | `{status:"ok", exports[]}` \| `{status:"empty", exports:[]}` |

Detalles clave de la implementación (fases 1-2):

- **Scripts de probe CONSTANTES** (`SCRIPT_SOURCES`, `SCRIPT_CONFIG`): cero interpolación de input → sin inyección.
- `runProbe()` usa `execFile` con timeout 10s y **nunca lanza**: fallo → `{status:"unavailable"}` honesto, jamás 500 ni mock.
- Liveness: `pgrep -f "runtime schedule|run\.py schedule"` (ERE con alternation — el cmdline real es `run.py schedule`, no `runtime schedule`).
- Versión: regex sobre `src/runtime/__main__.py` (`__init__.py` no define `__version__`; importar `__main__` dispara argparse).
- Artefactos leídos del **repo root** (`RUNTIME_REPO_ROOT` env → walk-up hasta `src/runtime/__main__.py`), no del CWD del proceso Next.js.

### 2.2 Legacy reutilizado (research BC, sin cambios)

| Endpoint | Método | Uso en /runtime |
|---|---|---|
| `/api/v1/scheduler/status` | GET | SchedulerPanel (status) |
| `/api/v1/scheduler/config` | GET | SchedulerPanel (resumen read-only) |
| `/api/v1/scheduler/run-now` | POST | Botón "Run now" |
| `/api/v1/status` | GET | MonitoringPanel |

## 3. Brechas → gate P6/P7 (facade `/api/v2`)

| Brecha | Estado hoy | Plan |
|---|---|---|
| Pipeline (ingestion → learning) | CLI-only | facade `/api/v2` (P6/P7) |
| Jobs del runtime | solo `enabled_jobs` en config | facade `/api/v2` |
| Feedback queue viva (en memoria) | CLI-only | facade `/api/v2` |
| Learning metrics vivas (en memoria) | solo reports simulados en disco | facade `/api/v2` |

La UI muestra estas brechas en `UnavailablePanel` (tag `NA`) con la nota: "runtime CLI-only: usar la terminal (CLI sigue siendo la referencia)".

## 4. ¿Por qué NO se crearon endpoints en el runtime?

1. **Restricción del usuario**: CERO cambios en `src/runtime/` (BC congelado) — prohibido tocar el backend del runtime.
2. **Estado in-memory**: la mayoría del estado vivo (jobs, queue, learning) vive en memoria del proceso daemon; no hay API HTTP propia y no se puede añadir sin modificar el BC.
3. **Read-only suficiente para P1**: catálogo y config se leen por subprocess (probe); artefactos se leen del filesystem. No se requiere escritura.

Los route handlers Next.js son la **frontera de lectura** del FE: aíslan subprocess/fs del browser y devuelven fallos honestos (`unavailable`/`empty`).

## 5. Instructivo venv + RUNTIME_REPO_ROOT

Los probes requieren el venv del runtime (`httpx` para providers):

```bash
# RUNTIME_REPO_ROOT apunta a la raíz del repo que contiene src/runtime/
export RUNTIME_REPO_ROOT=/ruta/al/repo   # opcional; default: walk-up desde CWD

# Crear/actualizar el venv (patrón run.py:19,40)
cd "$RUNTIME_REPO_ROOT"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

- Sin venv → `/api/runtime/info` responde `venv_available:false` y `/api/runtime/sources` responde `unavailable` con hint a este doc — **sin mock**.
- `NEXT_PUBLIC_API_URL` (`.env.local` del FE) apunta al research BC legacy; vacío → las secciones LEGACY muestran error honesto.

## 6. Etiquetado REAL / LEGACY / NA

| Tag | Color | Significado | Dónde |
|---|---|---|---|
| `REAL` | verde/neón (`neon-green`) | Datos vivos del runtime (probe/fs) | Runtime, Sources, Feedback, Learning |
| `LEGACY` | ámbar (`neon-yellow`) | Research BC vía API legacy | Scheduler, Monitoring |
| `NA` | gris (`gray-*`) | CLI-only / no disponible | UnavailablePanel, Runtime Scheduler |

Paneles y su etiqueta:

| Panel | Tag | Nota |
|---|---|---|
| RuntimePanel | REAL | versión, is_running, venv_available, config resumido |
| SourcesPanel | REAL | tabla de fuentes reales (16 verificado) |
| SchedulerPanel | LEGACY | "Discovery Topics Scheduler (research BC)" + sección NA "Runtime Scheduler: no observable (CLI-only)" |
| MonitoringPanel | LEGACY | topics found/pending_review/approved/rejected, total_topics, version, uptime |
| FeedbackPanel | REAL | feedback_session_*.json; empty → "la CLI sigue siendo la referencia" |
| LearningPanel | REAL + badge SIMULADO | "datos simulados — no métricas de producción" |
| UnavailablePanel | NA | pipeline/jobs/queue/learning vivas → CLI-only |

## 7. Caveats

- **Timeout subprocess**: 10s por probe (import de providers con httpx) → fallback honesto `unavailable`.
- **Host/venv coupling**: el FE puede correr en un host distinto al del repo → `RUNTIME_REPO_ROOT` env + fallback honesto.
- **pgrep edge**: `pgrep -f` matchea cmdlines; el route handler NO tiene el patrón en su propio cmdline (sin auto-match); riesgo inherente documentado, `liveness_check` informativo.
- **CWD del FE ≠ CWD del repo**: artefactos se leen del repo root resuelto.
- **PUT config duplicado**: el editor compacto del SchedulerPanel duplica /settings (decisión REQ-SCHEDULER-LEGACY); en esta implementación el panel muestra config read-only + link a /settings (sin editor duplicado) — ver desviación.
