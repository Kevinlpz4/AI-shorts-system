// ═══════════════════════════════════════════════════
// ApiTopicSource — Adapter that fetches topics from the backend API
// ═══════════════════════════════════════════════════
// Infrastructure: implementa ITopicSource usando el backend REST API.
// Llama a POST /api/v1/discover y mapea la respuesta a TopicData[].

import { TopicData, SourceType, TopicStatusValue } from "@/types";
import { ITopicSource } from "@/domain/ports/ITopicSource";

/**
 * Adapter de ITopicSource que obtiene topics desde el backend REST API.
 *
 * Llama a POST /api/v1/discover y mapea la respuesta a TopicData[].
 * Fallback silencioso: si el backend no responde, retorna array vacío.
 */
export class ApiTopicSource implements ITopicSource {
  public readonly sourceName: string;

  constructor(
    private readonly baseUrl: string,
    sourceName?: string
  ) {
    this.sourceName = sourceName || "api";
  }

  get available(): boolean {
    return true;
  }

  /**
   * Descubre topics desde el backend API vía POST /api/v1/discover.
   * @returns Array de TopicData mapeados desde la respuesta
   */
  async fetch(query?: string, limit: number = 10): Promise<TopicData[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/discover`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query || undefined,
          limit,
          source_names: [this.sourceName],
        }),
      });

      if (!response.ok) {
        console.warn(
          `[ApiTopicSource] discover failed: ${response.status} ${response.statusText}`
        );
        return [];
      }

      const data: Record<string, unknown> = await response.json();
      const discovered = (data.discovered as Array<Record<string, unknown>>) || [];

      return discovered.map((item) => this._mapTopic(item));
    } catch (err) {
      console.warn("[ApiTopicSource] fetch error:", err);
      return [];
    }
  }

  // ── Private helpers ────────────────────────────

  /** Mapea un topic del JSON de la API → TopicData */
  private _mapTopic(data: Record<string, unknown>): TopicData {
    const scoreComp = (data.score_components as Record<string, number>) || {};
    const sourceTypeRaw = String(data.source_type || "automatic");
    const sourceType = this._parseSourceType(sourceTypeRaw);

    return {
      id: String(data.id),
      title: String(data.title),
      description: String(data.description || ""),
      contentPreview: String(data.content_preview || ""),
      sourceName: String(data.source_name || this.sourceName),
      sourceType,
      status: this._parseStatus(String(data.status || "pending_review")),
      score: {
        relevance: Math.round(scoreComp.relevance || 0),
        popularity: Math.round(scoreComp.popularity || 0),
        recency: Math.round(scoreComp.recency || 0),
        reliability: Math.round(scoreComp.reliability || 0),
      },
      scoreTotal: typeof data.score_total === "number" ? data.score_total : 0,
      url: data.url ? String(data.url) : null,
      author: data.author ? String(data.author) : null,
      createdAt: data.created_at ? String(data.created_at) : new Date().toISOString(),
      reviewedAt: data.reviewed_at ? String(data.reviewed_at) : null,
      duplicateHash: data.duplicate_hash ? String(data.duplicate_hash) : null,
    };
  }

  private _parseSourceType(raw: string): SourceType {
    const normalized = raw.toLowerCase();
    for (const val of Object.values(SourceType)) {
      if (val === normalized) return val;
    }
    return SourceType.AUTOMATIC;
  }

  private _parseStatus(raw: string): TopicStatusValue {
    const upper = raw.toUpperCase() as TopicStatusValue;
    if (Object.values(TopicStatusValue).includes(upper)) {
      return upper;
    }
    return TopicStatusValue.PENDING_REVIEW;
  }
}
