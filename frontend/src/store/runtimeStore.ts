// ═══════════════════════════════════════════════════
// runtimeStore — Zustand: centro de operación del Runtime
// ═══════════════════════════════════════════════════
// 6 secciones Section<T> (patrón topicStore) con loading/error
// por sección. Tier 1 (runtime) consume los route handlers
// /api/runtime/* (mismo origen); Tier 2 (legacy) consume
// /api/v1/* vía getApiBase() (patrón settings/page.tsx).
// Sin mock: errores/ausencia de datos se reflejan honestos.

import { create } from "zustand";
import { getApiBase } from "@/lib/utils";
import type { SchedulerConfig, SchedulerStatus } from "@/types";
import type {
  FeedbackExport,
  FeedbackExportsResponse,
  InfoResponse,
  LearningReportsResponse,
  LegacyStatus,
  RuntimeInfo,
  RuntimeReport,
  RuntimeSource,
  Section,
  SourcesResponse,
} from "@/types/runtime";

/** Claves de las 6 secciones del runtime store. */
export type RuntimeSectionKey =
  | "runtime"
  | "sources"
  | "scheduler"
  | "monitoring"
  | "feedback"
  | "learning";

type AnySection = Section<unknown>;

const initialSection = <T,>(): Section<T> => ({
  data: null,
  loading: false,
  error: null,
});

/** GET JSON con chequeo HTTP; lanza con mensaje honesto (nunca mock). */
async function fetchJson<T = unknown>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status} — ${url}`);
  return (await res.json()) as T;
}

/** Scheduler legacy: status + config en paralelo (mismo patrón que settings). */
async function fetchLegacyScheduler(): Promise<[SchedulerStatus, SchedulerConfig]> {
  const base = getApiBase();
  if (!base) {
    throw new Error("Legacy API no configurada — NEXT_PUBLIC_API_URL vacío");
  }
  return Promise.all([
    fetchJson<SchedulerStatus>(`${base}/api/v1/scheduler/status`),
    fetchJson<SchedulerConfig>(`${base}/api/v1/scheduler/config`),
  ]);
}

/** Monitoring legacy: GET /api/v1/status (research BC). */
async function fetchLegacyStatus(): Promise<LegacyStatus> {
  const base = getApiBase();
  if (!base) {
    throw new Error("Legacy API no configurada — NEXT_PUBLIC_API_URL vacío");
  }
  return fetchJson<LegacyStatus>(`${base}/api/v1/status`);
}

interface RuntimeState {
  runtime: Section<RuntimeInfo>;
  sources: Section<RuntimeSource[]>;
  scheduler: Section<SchedulerStatus>;
  monitoring: Section<LegacyStatus>;
  feedback: Section<FeedbackExport[]>;
  learning: Section<RuntimeReport[]>;
  /** Config legacy del scheduler (sección auxiliar, no Section<T>). */
  schedulerConfig: SchedulerConfig | null;
  schedulerConfigLoading: boolean;

  loadAll: () => Promise<void>;
  refreshSection: (key: RuntimeSectionKey) => Promise<void>;
  refresh: () => Promise<void>;
  runSchedulerNow: () => Promise<{ discovered: number; errors: string[] } | null>;
}

export const useRuntimeStore = create<RuntimeState>((set, get) => {
  /** Actualiza una sección por clave (cast acotado: todas son Section<T>). */
  const patchSection = (key: RuntimeSectionKey, patch: Partial<AnySection>) =>
    set((state) => ({
      ...state,
      [key]: { ...(state[key] as AnySection), ...patch },
    }) as RuntimeState);

  return {
    runtime: initialSection(),
    sources: initialSection(),
    scheduler: initialSection(),
    monitoring: initialSection(),
    feedback: initialSection(),
    learning: initialSection(),
    schedulerConfig: null,
    schedulerConfigLoading: false,

    /** Fetch paralelo de las 6 secciones (mismo origen + legacy). */
    loadAll: async () => {
      const keys: RuntimeSectionKey[] = [
        "runtime",
        "sources",
        "scheduler",
        "monitoring",
        "feedback",
        "learning",
      ];
      await Promise.all(keys.map((key) => get().refreshSection(key)));
    },

    /** Recarga todas las secciones (alias de loadAll). */
    refresh: async () => {
      await get().loadAll();
    },

    /** Recarga una sección. Errores honestos por sección, nunca mock. */
    refreshSection: async (key) => {
      patchSection(key, { loading: true, error: null });
      try {
        switch (key) {
          case "runtime": {
            patchSection(key, {
              data: await fetchJson<InfoResponse>("/api/runtime/info"),
              loading: false,
            });
            break;
          }
          case "sources": {
            const res = await fetchJson<SourcesResponse>("/api/runtime/sources");
            if (res.status === "unavailable") {
              patchSection(key, {
                data: null,
                loading: false,
                error: res.message ?? "Catálogo de fuentes no disponible",
              });
            } else {
              patchSection(key, { data: res.sources ?? [], loading: false });
            }
            break;
          }
          case "scheduler": {
            const [status, config] = await fetchLegacyScheduler();
            patchSection(key, { data: status, loading: false });
            set({ schedulerConfig: config, schedulerConfigLoading: false });
            break;
          }
          case "monitoring": {
            patchSection(key, {
              data: await fetchLegacyStatus(),
              loading: false,
            });
            break;
          }
          case "feedback": {
            const res = await fetchJson<FeedbackExportsResponse>(
              "/api/runtime/feedback/exports"
            );
            patchSection(key, { data: res.exports ?? [], loading: false });
            break;
          }
          case "learning": {
            const res = await fetchJson<LearningReportsResponse>(
              "/api/runtime/learning/reports"
            );
            patchSection(key, { data: res.reports ?? [], loading: false });
            break;
          }
        }
      } catch (err) {
        patchSection(key, {
          loading: false,
          error: err instanceof Error ? err.message : "Error al cargar la sección",
        });
      }
    },

    /** POST legacy /api/v1/scheduler/run-now + refresh de la sección scheduler. */
    runSchedulerNow: async () => {
      const base = getApiBase();
      if (!base) {
        patchSection("scheduler", {
          error: "Legacy API no configurada — NEXT_PUBLIC_API_URL vacío",
        });
        return null;
      }
      try {
        const res = await fetch(`${base}/api/v1/scheduler/run-now`, {
          method: "POST",
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const result = (await res.json()) as {
          discovered_count?: number;
          errors?: unknown[];
        };
        await get().refreshSection("scheduler");
        return {
          discovered: result.discovered_count ?? 0,
          errors: Array.isArray(result.errors)
            ? result.errors.map(String)
            : [],
        };
      } catch (err) {
        patchSection("scheduler", {
          error: err instanceof Error ? err.message : "Run now falló",
        });
        return null;
      }
    },
  };
});
