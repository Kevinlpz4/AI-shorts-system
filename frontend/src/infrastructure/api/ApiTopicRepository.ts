// ═══════════════════════════════════════════════════
// ApiTopicRepository — ITopicRepository implementation via REST API
// ═══════════════════════════════════════════════════
// Infrastructure: implementa ITopicRepository usando el backend REST API.
// Todas las operaciones CRUD se traducen a llamadas HTTP.

import { Topic } from "@/domain/entities/Topic";
import { Source, SourceType } from "@/domain/value-objects/Source";
import { Score } from "@/domain/value-objects/Score";
import { TopicStatus, TopicStatusValue } from "@/domain/value-objects/TopicStatus";
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
    source_reliability?: number;
  };
  url?: string | null;
  author?: string | null;
  created_at?: string | null;
  reviewed_at?: string | null;
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
 * Todas las operaciones CRUD se traducen a llamadas HTTP.
 * Usa fetch() nativo con manejo consistente de errores.
 */
export class ApiTopicRepository implements ITopicRepository {
  constructor(private readonly baseUrl: string = "http://localhost:8000") {}

  // ── READ ──────────────────────────────────────────

  /**
   * Obtiene todos los topics desde GET /api/v1/topics con filtros opcionales.
   * @param filters - Filtros: status, sourceName, searchQuery, minScore, limit
   */
  async findAll(filters?: TopicFilters): Promise<Topic[]> {
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
    return (data.topics || []).map((item) => this._mapTopic(item));
  }

  /**
   * Busca un topic por ID via GET /api/v1/topics/{id}.
   * @returns Topic o null si el backend responde 404
   */
  async findById(id: string): Promise<Topic | null> {
    const url = `${this.baseUrl}/api/v1/topics/${encodeURIComponent(id)}`;

    const response = await this._fetch(url);
    if (response.status === 404) {
      return null;
    }
    if (!response.ok) {
      throw new Error(`Failed to fetch topic ${id}: ${response.status} ${response.statusText}`);
    }

    const data: TopicResponse = await response.json();
    return this._mapTopic(data);
  }

  // ── DUPLICATE HASH ────────────────────────────────

  /**
   * Búsqueda por duplicateHash.
   * El backend maneja la deduplicación server-side — no hay endpoint público.
   * @returns Siempre array vacío
   */
  async findByDuplicateHash(_hash: string): Promise<Topic[]> {
    return [];
  }

  // ── WRITE ─────────────────────────────────────────

  /**
   * Guarda (crea o actualiza) un topic en el backend.
   *
   * Según el estado del topic, llama al endpoint correspondiente:
   * - APPROVED → POST /api/v1/topics/{id}/approve
   * - REJECTED → POST /api/v1/topics/{id}/reject
   * - Otros estados → retorna el topic sin cambios (ya existe en backend)
   *
   * @param topic - Topic con el estado deseado
   * @returns Topic actualizado desde la respuesta del backend
   */
  async save(topic: Topic): Promise<Topic> {
    const id = topic.id;
    const encodedId = encodeURIComponent(id);

    // Según el estado, llamamos a approve o reject
    if (topic.status.value === TopicStatusValue.APPROVED) {
      const url = `${this.baseUrl}/api/v1/topics/${encodedId}/approve`;

      const response = await this._fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) {
        throw new Error(
          `Failed to approve topic ${id}: ${response.status} ${response.statusText}`
        );
      }

      const data: Record<string, unknown> = await response.json();
      const topicData = data.topic as TopicResponse;
      return this._mapTopic(topicData);
    }

    if (topic.status.value === TopicStatusValue.REJECTED) {
      const url = `${this.baseUrl}/api/v1/topics/${encodedId}/reject`;

      const response = await this._fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) {
        throw new Error(
          `Failed to reject topic ${id}: ${response.status} ${response.statusText}`
        );
      }

      const data: Record<string, unknown> = await response.json();
      const topicData = data.topic as TopicResponse;
      return this._mapTopic(topicData);
    }

    // Para otros estados (FOUND, PENDING_REVIEW) no hay endpoint de escritura;
    // el topic ya fue creado via discover o manual. Devolvemos el topic intacto.
    return topic;
  }

  /**
   * Guarda múltiples topics secuencialmente en el backend.
   */
  async saveMany(topics: Topic[]): Promise<Topic[]> {
    const results: Topic[] = [];
    for (const topic of topics) {
      const saved = await this.save(topic);
      results.push(saved);
    }
    return results;
  }

  /**
   * Elimina un topic. No soportado por la API REST.
   * @throws Error siempre — el backend no expone endpoint DELETE
   */
  async delete(_id: string): Promise<void> {
    throw new Error("Delete operation is not supported by the API");
  }

  // ── STATS ─────────────────────────────────────────

  /**
   * Obtiene KPI stats desde GET /api/v1/status.
   * Fallback: cuenta desde la lista completa si el endpoint status falla.
   */
  async getKPIStats(): Promise<KPIResult> {
    try {
      const url = `${this.baseUrl}/api/v1/status`;
      const response = await this._fetch(url);

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
      // Si falla el status endpoint, derivamos desde findAll
    }

    // Fallback: contar desde la lista completa
    const all = await this.findAll({ limit: 1000 });
    return {
      discovered: all.filter((t) => t.status.value === TopicStatusValue.FOUND).length,
      pendingReview: all.filter(
        (t) => t.status.value === TopicStatusValue.PENDING_REVIEW
      ).length,
      approved: all.filter((t) => t.status.value === TopicStatusValue.APPROVED).length,
      rejected: all.filter((t) => t.status.value === TopicStatusValue.REJECTED).length,
    };
  }

  // ── Private helpers ───────────────────────────────

  /** Wrapper around native fetch() for consistent error handling */
  private async _fetch(
    url: string,
    options?: RequestInit
  ): Promise<Response> {
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

  /**
   * Mapea un topic del JSON de la API → entidad Topic del frontend.
   * Convierte campos snake_case de la API a camelCase del dominio.
   */
  private _mapTopic(data: TopicResponse): Topic {
    const scoreComp = data.score_components || {};

    const sourceTypeRaw = String(data.source_type || "automatic");
    const sourceType = this._parseSourceType(sourceTypeRaw);

    return new Topic({
      id: String(data.id),
      title: String(data.title),
      description: String(data.description || ""),
      content: String(data.content_preview || ""),
      source: new Source({
        name: String(data.source_name),
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
      url: data.url || null,
      author: data.author || null,
      publishedAt: data.created_at ? new Date(data.created_at) : null,
      createdAt: data.created_at ? new Date(data.created_at) : new Date(),
      reviewedAt: data.reviewed_at ? new Date(data.reviewed_at) : null,
      duplicateHash: null,
    });
  }

  /**
   * Convierte el source_type string de la API → enum SourceType.
   * Normaliza a lowercase y busca coincidencia exacta.
   * Fallback: SourceType.AUTOMATIC.
   */
  private _parseSourceType(raw: string): SourceType {
    const normalized = raw.toLowerCase();
    for (const val of Object.values(SourceType)) {
      if (val === normalized) return val as SourceType;
    }
    return SourceType.AUTOMATIC;
  }
}
