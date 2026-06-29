// ═══════════════════════════════════════════════════
// ITopicSource — Port for external topic sources
// ═══════════════════════════════════════════════════
// Puerto para fuentes externas (Google News, Twitter, etc.).
// Cualquier adapter externo implementa esto.

import { Topic } from "@/domain/entities/Topic";

export interface ITopicSource {
  /** Nombre único de la fuente (ej: "google-news", "twitter") */
  readonly sourceName: string;

  /** Si la fuente está disponible */
  readonly available: boolean;

  /**
   * Obtener topics desde la fuente externa.
   * @param query Término de búsqueda (opcional)
   * @param limit Máximo de resultados
   */
  fetch(query?: string, limit?: number): Promise<Topic[]>;
}

/**
 * Registry de fuentes — permite registrar múltiples adapters
 * y consultarlos por nombre (Registry Pattern).
 */
export interface ITopicSourceRegistry {
  register(source: ITopicSource): void;
  get(name: string): ITopicSource;
  getAllAvailable(): ITopicSource[];
  list(): { name: string; available: boolean }[];
}
