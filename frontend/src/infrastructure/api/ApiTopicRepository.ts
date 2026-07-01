// ═══════════════════════════════════════════════════
// ApiTopicRepository — ITopicRepository via REST API
// ═══════════════════════════════════════════════════
// Infrastructure: implementa ITopicRepository usando el backend REST API.
// Todas las operaciones CRUD se traducen a llamadas HTTP.
// Trabaja con TopicData (plain data) — no con entidades del dominio.

import { TopicData, SourceType, TopicStatusValue } from "@/types";
import {
  ITopicRepository,
  TopicFilters,
  KPIResult,
} from "@/domain/ports/ITopicRepository";

// ── Response types ─────────────────────────────────

interface TopicResponse {
  id: string;
  title: string;
  description?: string;
  content_preview?: string;
  source_name: string;
  source_type: string;
  status: string;
  score_total?: number;
  score_components?: {
    relevance?: number;
    popularity?: number;
    recency?: number;
    reliability?: number;
  };
  url?: string | null;
  author?: string | null;
  created_at?: string | null;
  reviewed_at?: string | null;
  duplicate_hash?: string | null;
}

interface TopicListResponse {
  topics: TopicResponse[];
  count: number;
}

interface StatusResponse {
  topics: Record<string, number>;
  total_topics: number;
}

/**
 * Implementación de ITopicRepository que se comunica con el backend REST API.
 *
 * Todas las operaciones se traducen a llamadas HTTP.
 * Trabaja con TopicData (plain objects), sin dependencia del dominio frontend.
 */
export class ApiTopicRepository implements ITopicRepository {
  constructor(private readonly baseUrl: string = "http://localhost:8000") {}

  // ── READ ──────────────────────────────────────────

  /**
   * Obtiene todos los topics desde GET /api/v1/topics con filtros opcionales.
   */
  async findAll(filters?: TopicFilters): Promise<TopicData[]> {
    const params = new URLSearchParams();

    if (filters?.status) {
      params.set("status", filters.status.toLowerCase());
    }
    if (filters?.sourceName) {
      params.set("source", filters.sourceName);
    }
    if (filters?.searchQuery) {
      params.set("q", filters.searchQuery);
    }
    if (filters?.minScore != null && filters.minScore > 0) {
      params.set("min_score", String(filters.minScore));
    }
    if (filters?.limit) {
      params.set("limit", String(filters.limit));
    }

    const queryString = params.toString();
    const url = `${this.baseUrl}/api/v1/topics${queryString ? `?${queryString}` : ""}`;

    const response = await this._fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch topics: ${response.status} ${response.statusText}`);
    }

    const data: TopicListResponse = await response.json();
    return (data.topics || []).map((item) => this._mapResponse(item));
  }

  /**
   * Busca un topic por ID via GET /api/v1/topics/{id}.
   */
  async findById(id: string): Promise<TopicData | null> {
    const url = `${this.baseUrl}/api/v1/topics/${encodeURIComponent(id)}`;

    const response = await this._fetch(url);
    if (response.status === 404) {
      return null;
    }
    if (!response.ok) {
      throw new Error(`Failed to fetch topic ${id}: ${response.status} ${response.statusText}`);
    }

    const data: TopicResponse = await response.json();
    return this._mapResponse(data);
  }

  /** Búsqueda por duplicateHash — el backend no expone endpoint público. */
  async findByDuplicateHash(_hash: string): Promise<TopicData[]> {
    return [];
  }

  // ── WRITE ─────────────────────────────────────────

  /**
   * Guarda (crea o actualiza) un topic en el backend.
   * Para estados APPROVED/REJECTED, llama a los endpoints correspondientes.
   * Para otros estados, retorna el topic sin cambios (ya existe en backend).
   */
  async save(topic: TopicData): Promise<TopicData> {
    if (topic.status === TopicStatusValue.APPROVED) {
      return this.approve(topic.id);
    }
    if (topic.status === TopicStatusValue.REJECTED) {
      return this.reject(topic.id);
    }
    return topic;
  }

  /** Guarda múltiples topics secuencialmente. */
  async saveMany(topics: TopicData[]): Promise<TopicData[]> {
    const results: TopicData[] = [];
    for (const topic of topics) {
      const saved = await this.save(topic);
      results.push(saved);
    }
    return results;
  }

  /** Elimina un topic. No soportado por la API REST. */
  async delete(_id: string): Promise<void> {
    throw new Error("Delete operation is not supported by the API");
  }

  /** Aprueba un topic via POST /api/v1/topics/{id}/approve */
  async approve(id: string): Promise<TopicData> {
    const response = await this._fetch(
      `${this.baseUrl}/api/v1/topics/${encodeURIComponent(id)}/approve`,
      { method: "POST", headers: { "Content-Type": "application/json" } }
    );
    if (!response.ok) {
      throw new Error(`Failed to approve topic ${id}: ${response.status}`);
    }
    const data: Record<string, unknown> = await response.json();
    return this._mapResponse(data.topic as TopicResponse);
  }

  /** Rechaza un topic via POST /api/v1/topics/{id}/reject */
  async reject(id: string, reason?: string): Promise<TopicData> {
    const params = reason ? `?reason=${encodeURIComponent(reason)}` : "";
    const response = await this._fetch(
      `${this.baseUrl}/api/v1/topics/${encodeURIComponent(id)}/reject${params}`,
      { method: "POST", headers: { "Content-Type": "application/json" } }
    );
    if (!response.ok) {
      throw new Error(`Failed to reject topic ${id}: ${response.status}`);
    }
    const data: Record<string, unknown> = await response.json();
    return this._mapResponse(data.topic as TopicResponse);
  }

  /** Crea un topic manual via POST /api/v1/topics/manual */
  async createManual(input: {
    title: string;
    description?: string;
    url?: string | null;
    content?: string;
    author?: string;
    sourceName?: string;
  }): Promise<{ topic: TopicData; isDuplicate: boolean }> {
    const response = await this._fetch(
      `${this.baseUrl}/api/v1/topics/manual`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: input.title,
          url: input.url || undefined,
          description: input.description || undefined,
          content: input.content || undefined,
          author: input.author || undefined,
          source_name: input.sourceName || "manual",
        }),
      }
    );
    if (!response.ok) {
      const err = await response.json().catch(() => null);
      throw new Error(err?.detail || `Failed to create topic: ${response.status}`);
    }
    const data: Record<string, unknown> = await response.json();
    return {
      topic: this._mapResponse(data.topic as TopicResponse),
      isDuplicate: !!data.is_duplicate,
    };
  }

  // ── STATS ─────────────────────────────────────────

  /** Obtiene KPI stats desde GET /api/v1/status. */
  async getKPIStats(): Promise<KPIResult> {
    try {
      const response = await this._fetch(`${this.baseUrl}/api/v1/status`);
      if (response.ok) {
        const data: StatusResponse = await response.json();
        const topics = data.topics || {};
        return {
          discovered: topics.found ?? 0,
          pendingReview: topics.pending_review ?? 0,
          approved: topics.approved ?? 0,
          rejected: topics.rejected ?? 0,
        };
      }
    } catch {
      // Fallback: contar desde la lista completa
    }

    const all = await this.findAll({ limit: 1000 });
    return {
      discovered: all.filter((t) => t.status === TopicStatusValue.FOUND).length,
      pendingReview: all.filter((t) => t.status === TopicStatusValue.PENDING_REVIEW).length,
      approved: all.filter((t) => t.status === TopicStatusValue.APPROVED).length,
      rejected: all.filter((t) => t.status === TopicStatusValue.REJECTED).length,
    };
  }

  // ── Private helpers ───────────────────────────────

  private async _fetch(url: string, options?: RequestInit): Promise<Response> {
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          ...(options?.headers || {}),
        },
      });
      return response;
    } catch (err) {
      throw new Error(
        `Network error fetching ${url}: ${
          err instanceof Error ? err.message : "Unknown error"
        }`
      );
    }
  }

  /** Mapea TopicResponse (API JSON) → TopicData (plain object) */
  private _mapResponse(data: TopicResponse): TopicData {
    const scoreComp = data.score_components || {};

    const sourceTypeRaw = String(data.source_type || "automatic");
    const sourceType = this._parseSourceType(sourceTypeRaw);

    return {
      id: String(data.id),
      title: String(data.title),
      description: String(data.description || ""),
      contentPreview: String(data.content_preview || ""),
      sourceName: String(data.source_name),
      sourceType,
      status: this._parseStatus(String(data.status || "pending_review")),
      score: {
        relevance: Math.round(scoreComp.relevance || 0),
        popularity: Math.round(scoreComp.popularity || 0),
        recency: Math.round(scoreComp.recency || 0),
        reliability: Math.round(scoreComp.reliability || 0),
      },
      scoreTotal: data.score_total ?? 0,
      url: data.url || null,
      author: data.author || null,
      createdAt: data.created_at ? String(data.created_at) : new Date().toISOString(),
      reviewedAt: data.reviewed_at ? String(data.reviewed_at) : null,
      duplicateHash: data.duplicate_hash || null,
    };
  }

  /** Convierte source_type string → SourceType enum */
  private _parseSourceType(raw: string): SourceType {
    const normalized = raw.toLowerCase();
    for (const val of Object.values(SourceType)) {
      if (val === normalized) return val;
    }
    return SourceType.AUTOMATIC;
  }

  /** Convierte status string → TopicStatusValue enum */
  private _parseStatus(raw: string): TopicStatusValue {
    const upper = raw.toUpperCase() as TopicStatusValue;
    if (Object.values(TopicStatusValue).includes(upper)) {
      return upper;
    }
    return TopicStatusValue.PENDING_REVIEW;
  }
}
