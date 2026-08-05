// ═══════════════════════════════════════════════════
// ApiTopicSource — Adapter that fetches topics from the backend API
// ═══════════════════════════════════════════════════
// Infrastructure: implementa ITopicSource usando el backend REST API.
// Llama a POST /api/v1/discover y mapea la respuesta a TopicData[].

import { TopicData } from "@/types";
import { mapTopicFromApi } from "@/infrastructure/api/mappers";
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
   * Política source_names (P0, bug #7): NO se envía la key — los nombres
   * del FE (`google-news`/`twitter`/`rss`) no existen en el registry
   * backend (solo `google-news-rss`/`mock`) y producían 0 descubiertos
   * vía SourceNotAvailableError. Sin la key, `discover.py` usa las fuentes
   * default (`get_all_available()`). `sourceName` queda solo para reporting
   * de errores y fallback del mapper.
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
    // Delegación al mapper compartido con fallback al sourceName
    // de este adapter (para payloads sin `source_name`).
    return mapTopicFromApi(data, this.sourceName);
  }
}
