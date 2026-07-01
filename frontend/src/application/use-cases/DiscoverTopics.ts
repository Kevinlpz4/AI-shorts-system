// ═══════════════════════════════════════════════════
// DiscoverTopics — Application Use Case
// ═══════════════════════════════════════════════════
// Orquesta el descubrimiento desde fuentes externas.
// Depende de los puertos ITopicRepository e ITopicSourceRegistry.
// Trabaja con TopicData (plain objects) — sin entidades de dominio.

import { TopicData } from "@/types";
import { ITopicRepository } from "@/domain/ports/ITopicRepository";
import { ITopicSource, ITopicSourceRegistry } from "@/domain/ports/ITopicSource";

/** Input para el descubrimiento automático de topics desde fuentes externas */
export interface DiscoverInput {
  query?: string;
  limit?: number;
  sourceNames?: string[];
}

/** Resultado del descubrimiento */
export interface DiscoverOutput {
  discovered: TopicData[];
  duplicates: TopicData[];
  errors: { source: string; error: string }[];
}

/**
 * Use case: descubrir topics desde fuentes externas.
 *
 * La deduplicación la maneja el backend (server-side). El frontend
 * solo pasa a través de los topics que el backend devuelve como
 * descubiertos y persiste si el repositorio lo requiere.
 */
export class DiscoverTopics {
  constructor(
    private readonly repository: ITopicRepository,
    private readonly sourceRegistry: ITopicSourceRegistry
  ) {}

  /**
   * Ejecuta el descubrimiento de topics desde fuentes externas.
   * @param input - Configuración: query opcional, límite por fuente, fuentes específicas
   * @returns Topics descubiertos y errores por fuente
   */
  async execute(input: DiscoverInput): Promise<DiscoverOutput> {
    const sources = this._resolveSources(input.sourceNames);
    const allDiscovered: TopicData[] = [];
    const errors: { source: string; error: string }[] = [];

    for (const source of sources) {
      try {
        const topics = await source.fetch(input.query, input.limit);
        // Backend ya persiste via POST /api/v1/discover
        // El frontend solo pasa a través
        allDiscovered.push(...topics);
      } catch (err) {
        errors.push({
          source: source.sourceName,
          error: err instanceof Error ? err.message : "Unknown error",
        });
      }
    }

    return {
      discovered: allDiscovered,
      duplicates: [],
      errors,
    };
  }

  private _resolveSources(sourceNames?: string[]): ITopicSource[] {
    if (sourceNames && sourceNames.length > 0) {
      return sourceNames
        .map((name) => {
          try {
            return this.sourceRegistry.get(name);
          } catch {
            return null;
          }
        })
        .filter((s): s is ITopicSource => s !== null);
    }
    return this.sourceRegistry.getAllAvailable();
  }
}
