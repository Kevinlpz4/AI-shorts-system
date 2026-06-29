// ═══════════════════════════════════════════════════
// ApiTopicSource — Adapter that fetches topics from the backend API
// ═══════════════════════════════════════════════════
// Infrastructure: implementa ITopicSource usando el backend REST API.
// Llama a POST /api/v1/discover y mapea la respuesta a Topic[].

import { Topic } from "@/domain/entities/Topic";
import { Source, SourceType } from "@/domain/value-objects/Source";
import { Score } from "@/domain/value-objects/Score";
import { TopicStatus } from "@/domain/value-objects/TopicStatus";
import { ITopicSource } from "@/domain/ports/ITopicSource";

/**
 * Adapter de ITopicSource que obtiene topics desde el backend REST API.
 *
 * Llama a POST /api/v1/discover y mapea la respuesta a entidades Topic.
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

  /**
   * Siempre reporta disponible — el error handling se maneja en fetch().
   * Si el backend no responde, retorna array vacío sin tirar error.
   */
  get available(): boolean {
    return true;
  }

  /**
   * Descubre topics desde el backend API vía POST /api/v1/discover.
   * @param query - Término de búsqueda opcional
   * @param limit - Máximo de resultados
   * @returns Array de entidades Topic mapeadas desde la respuesta
   */
  async fetch(query?: string, limit: number = 10): Promise<Topic[]> {
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

  /** Mapea un topic del JSON de la API → entidad Topic del frontend */
  private _mapTopic(data: Record<string, unknown>): Topic {
    const scoreComp =
      (data.score_components as Record<string, number>) || {};

    const sourceTypeRaw = String(data.source_type || "automatic");
    const sourceType = this._parseSourceType(sourceTypeRaw);

    return new Topic({
      id: String(data.id),
      title: String(data.title),
      description: String(data.description || ""),
      content: String(data.content_preview || ""),
      source: new Source({
        name: String(data.source_name || this.sourceName),
        type: sourceType,
        reliability:
          typeof scoreComp.source_reliability === "number"
            ? scoreComp.source_reliability
            : 50,
      }),
      score: new Score({
        relevance: Math.round((scoreComp.relevance || 0) / 10),
        popularity: Math.round((scoreComp.popularity || 0) / 10),
        recency: Math.round((scoreComp.recency || 0) / 10),
        reliability: Math.round((scoreComp.source_reliability || 0) / 10),
      }),
      status: TopicStatus.from(String(data.status || "pending_review")),
      url: data.url ? String(data.url) : null,
      author: data.author ? String(data.author) : null,
      publishedAt: data.created_at ? new Date(String(data.created_at)) : null,
      createdAt: data.created_at
        ? new Date(String(data.created_at))
        : new Date(),
      reviewedAt: data.reviewed_at ? new Date(String(data.reviewed_at)) : null,
      duplicateHash: null,
    });
  }

  /** Convierte el source_type string de la API → enum SourceType */
  private _parseSourceType(raw: string): SourceType {
    const normalized = raw.toLowerCase();
    for (const val of Object.values(SourceType)) {
      if (val === normalized) return val as SourceType;
    }
    return SourceType.AUTOMATIC;
  }
}
