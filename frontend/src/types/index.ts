// ═══════════════════════════════════════════════════
// Domain Types — Shared type definitions
// ═══════════════════════════════════════════════════
// Status and SourceType are defined in domain/value-objects.
// We re-export them here so application/infrastructure layers
// have a single import path without depending on domain internals.

import { TopicStatusValue } from "@/domain/value-objects/TopicStatus";
import { SourceType } from "@/domain/value-objects/Source";

// ── Re-exported types ──
export type TopicStatus = TopicStatusValue;
export { TopicStatusValue } from "@/domain/value-objects/TopicStatus";
export type { SourceType as SourceType } from "@/domain/value-objects/Source";

// ── Shared interfaces ──

/** Componentes individuales del score de un topic (0–10 cada uno) */
export interface ScoreComponents {
  /** Relevancia del contenido (0-10) */
  relevance: number;
  /** Popularidad / engagement (0-10) */
  popularity: number;
  /** Qué tan reciente es (0-10) */
  recency: number;
  /** Confiabilidad de la fuente (0-10) */
  reliability: number;
}

/** DTO plano de un Topic para la capa de presentación */
export interface TopicData {
  id: string;
  title: string;
  description: string;
  contentPreview: string;
  sourceName: string;
  sourceType: SourceType;
  status: TopicStatusValue;
  score: ScoreComponents;
  scoreTotal: number;
  url: string | null;
  author: string | null;
  createdAt: string;
  reviewedAt: string | null;
  duplicateHash: string | null;
}

/** KPIs agrupados por estado de topic */
export interface KPIStats {
  discovered: number;
  pendingReview: number;
  approved: number;
  rejected: number;
}

/** Filtros para el listado de topics */
export interface TopicFilters {
  status: TopicStatusValue | null;
  sourceName: string | null;
  minScore: number;
  maxScore: number;
  query: string;
}

// ═══════════════════════════════════════════════════
// Application DTOs
// ═══════════════════════════════════════════════════

/** Input para crear un topic manualmente desde el formulario */
export interface ManualTopicInput {
  title: string;
  description: string;
  url: string | null;
  sourceName: string;
}

/** Resultado de crear un topic manual */
export interface CreateTopicResult {
  topic: TopicData | null;
  isDuplicate: boolean;
}

/** Resultado del descubrimiento batch desde fuentes externas */
export interface BatchDiscoverResult {
  discovered: TopicData[];
  duplicates: TopicData[];
  errors: { source: string; error: string }[];
}

// ── Script types ──

// ═══════════════════════════════════════════════════
// Scheduler + Studio types
// ═══════════════════════════════════════════════════

/** Estado completo del scheduler */
export interface SchedulerStatus {
  enabled: boolean;
  interval_minutes: number;
  queries: string[];
  last_run: string | null;
  is_running: boolean;
  running_query: string | null;
}

/** Configuración del scheduler */
export interface SchedulerConfig {
  interval_minutes: number;
  queries: string[];
  auto_generate_script: boolean;
}

/** Recomendaciones del sistema para generar un script */
export interface ScriptRecommendations {
  tone: string;
  duration: number;
  niche: string;
  reasoning: {
    tone: string;
    duration: string;
    niche: string;
  };
}

/** Configuración del Studio (config panel en UI) */
export interface StudioConfig {
  duration: number;
  tone: string;
  niche: string;
}

/** DTO plano de un Script para la capa de presentación */
export interface ScriptData {
  /** ID único del script */
  id: string;
  /** ID del topic al que pertenece */
  topicId: string;
  /** Hook / apertura del script */
  hook: string;
  /** Cuerpo del script */
  body: string;
  /** Call to action */
  cta: string;
  /** Duración estimada en segundos */
  duration: number;
  /** Tono del script (informative, humorous, etc.) */
  tone: string;
  /** Formato (youtube-shorts, tiktok, etc.) */
  format: string;
  /** Conteo de palabras */
  wordCount: number;
  /** Si el script pasa validaciones */
  isValid: boolean;
  /** Fecha de creación ISO */
  createdAt: string;
  /** Fecha de última actualización ISO */
  updatedAt: string;
}
