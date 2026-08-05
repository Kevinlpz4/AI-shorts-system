/**
 * Tipos para la integración frontend ↔ runtime (read-only).
 *
 * Aditivo: NO tocar `types/index.ts` (solo se leen SchedulerStatus/SchedulerConfig).
 * Las respuestas de los route handlers `/api/runtime/*` usan el wrapper
 * `status: "ok" | "empty" | "unavailable"` — nunca 500 ni mock silencioso.
 */

export type RuntimeApiStatus = "ok" | "empty" | "unavailable";

/** Fuente del catálogo del runtime (SourceDefinition serializado por SCRIPT_SOURCES). */
export interface RuntimeSource {
  id: string;
  provider: string;
  technology: string;
  categories: string[];
  enabled: boolean;
  priority: number;
  /** poll_interval (timedelta) convertido a minutos por el script Python. */
  poll_interval_minutes: number;
  /** metadata.url del SourceDefinition; null si el source no la define. */
  url: string | null;
}

/** Defaults de RuntimeConfig serializados por SCRIPT_CONFIG. */
export interface RuntimeConfigInfo {
  sources: unknown[];
  database_url: string;
  pipeline_interval_minutes: number;
  event_bridge_max_buffer: number;
  storage_base_path: string;
  log_level: string;
  enabled_jobs: string[];
}

/** Respuesta del route handler `/api/runtime/info`. */
export interface RuntimeInfo {
  version: string;
  config: RuntimeConfigInfo | null;
  is_running: boolean;
  venv_available: boolean;
  repo_root?: string | null;
  liveness_check?: string;
}

/** Reporte de aprendizaje (simulado) leído de simulation_reports/. */
export interface RuntimeReport {
  name: string;
  generated_at: string;
  report: Record<string, unknown>;
}

/** Export de sesión de feedback (feedback_session_*.json). */
export interface FeedbackExport {
  file: string;
  size: number;
  mtime: string;
  /** Cantidad de decisiones si el JSON es parseable; null si no. */
  decisions?: number | null;
  session_id?: string;
}

/** Envoltorio base de respuesta de `/api/runtime/*` (status honesto). */
export interface RuntimeApiResponse<T = unknown> {
  status: RuntimeApiStatus;
  message?: string;
  hint?: string;
  data?: T;
}

/** GET /api/runtime/sources */
export interface SourcesResponse extends RuntimeApiResponse<RuntimeSource[]> {
  sources?: RuntimeSource[];
  count?: number;
}

/** GET /api/runtime/info */
export interface InfoResponse extends RuntimeApiResponse {
  version: string;
  config: RuntimeConfigInfo | null;
  is_running: boolean;
  venv_available: boolean;
  repo_root?: string | null;
  liveness_check?: string;
}

/** GET /api/runtime/learning/reports */
export interface LearningReportsResponse extends RuntimeApiResponse<RuntimeReport[]> {
  status: "ok" | "empty";
  simulated?: boolean;
  note?: string;
  reports: RuntimeReport[];
}

/** GET /api/runtime/feedback/exports */
export interface FeedbackExportsResponse extends RuntimeApiResponse<FeedbackExport[]> {
  status: "ok" | "empty";
  exports: FeedbackExport[];
}

/** GET /api/v1/status (legacy, research BC) — shape verificado en presentation/api/routes/discover.py. */
export interface LegacyStatus {
  version?: string;
  uptime_seconds?: number;
  topics?: Record<string, number>;
  total_topics?: number;
  api_version?: string;
  [key: string]: unknown;
}

/** Estado de una sección del runtime store (patrón topicStore). */
export interface Section<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}
