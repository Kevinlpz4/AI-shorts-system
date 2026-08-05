// ═══════════════════════════════════════════════════
// mappers — Shared API → domain DTO mappers
// ═══════════════════════════════════════════════════
// Infrastructure: funciones puras que convierten respuestas JSON
// de la API servida (snake_case, asdict(ResearchTopicDTO)) a DTOs
// del frontend (camelCase). Fuente canónica: ApiTopicRepository._mapResponse
// (los adapters delegan aquí; evita la 3ª copia latente).
// Strict-safe: operan sobre Record<string, unknown> sin type-punning crudo.

import { TopicData, SourceType, TopicStatusValue } from "@/types";

/**
 * Mapea un topic JSON de la API → TopicData (camelCase).
 * Convierte score_total → scoreTotal, source_name → sourceName,
 * created_at → createdAt, etc. Strict-safe: guard `typeof` para
 * campos numéricos que pueden venir ausentes.
 *
 * @param data               Payload del topic servido por la API
 * @param fallbackSourceName Fuente a usar si `source_name` viene ausente
 *                           (p.ej. el sourceName del adapter que consultó)
 */
export function mapTopicFromApi(
  data: Record<string, unknown>,
  fallbackSourceName?: string
): TopicData {
  const scoreComp = (data.score_components as Record<string, number>) || {};

  const sourceTypeRaw = String(data.source_type || "automatic");
  const sourceType = parseSourceType(sourceTypeRaw);

  return {
    id: String(data.id),
    title: String(data.title),
    description: String(data.description || ""),
    contentPreview: String(data.content_preview || ""),
    sourceName: String(data.source_name || fallbackSourceName || ""),
    sourceType,
    status: parseStatus(String(data.status || "pending_review")),
    score: {
      relevance: Math.round(scoreComp.relevance || 0),
      popularity: Math.round(scoreComp.popularity || 0),
      recency: Math.round(scoreComp.recency || 0),
      reliability: Math.round(scoreComp.reliability || 0),
    },
    // Guard obligatorio: sobre unknown, `data.score_total ?? 0` tiparía
    // `unknown` → error strict. Solo acepta números reales.
    scoreTotal: typeof data.score_total === "number" ? data.score_total : 0,
    url: data.url ? String(data.url) : null,
    author: data.author ? String(data.author) : null,
    createdAt: data.created_at ? String(data.created_at) : new Date().toISOString(),
    reviewedAt: data.reviewed_at ? String(data.reviewed_at) : null,
    duplicateHash: data.duplicate_hash ? String(data.duplicate_hash) : null,
  };
}

/**
 * Alias de `mapTopicFromApi` para el flujo de approved-topics del Studio
 * (naming de proposal/spec). Cero lógica duplicada.
 */
export const mapApprovedTopic = mapTopicFromApi;

// ── Helpers módulo-privados (verbatim de los parsers de los adapters) ──

/** Convierte source_type string → SourceType enum */
function parseSourceType(raw: string): SourceType {
  const normalized = raw.toLowerCase();
  for (const val of Object.values(SourceType)) {
    if (val === normalized) return val;
  }
  return SourceType.AUTOMATIC;
}

/** Convierte status string → TopicStatusValue enum */
function parseStatus(raw: string): TopicStatusValue {
  const upper = raw.toUpperCase() as TopicStatusValue;
  if (Object.values(TopicStatusValue).includes(upper)) {
    return upper;
  }
  return TopicStatusValue.PENDING_REVIEW;
}
