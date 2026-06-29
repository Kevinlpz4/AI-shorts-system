// ═══════════════════════════════════════════════════
// DiscoverTopics — Application Use Case
// ═══════════════════════════════════════════════════
// Orquesta el descubrimiento desde fuentes externas.
// Depende del puerto ITopicRepository, no de implementaciones.

import { Topic } from "@/domain/entities/Topic";
import { ITopicRepository } from "@/domain/ports/ITopicRepository";
import { ITopicSource, ITopicSourceRegistry } from "@/domain/ports/ITopicSource";
import { ScoringService } from "@/domain/services/ScoringService";

/** Input para el descubrimiento automático de topics desde fuentes externas */
export interface DiscoverInput {
  query?: string;
  limit?: number;
  sourceNames?: string[];
}

/** Resultado del descubrimiento */
export interface DiscoverOutput {
  discovered: Topic[];
  duplicates: Topic[];
  errors: { source: string; error: string }[];
}

/**
 * Use case: descubrir topics desde fuentes externas.
 *
 * Orquesta la consulta a múltiples fuentes (ITopicSource) registradas,
 * detecta duplicados contra topics existentes, calcula scores,
 * y persiste los nuevos.
 */
export class DiscoverTopics {
  constructor(
    private readonly repository: ITopicRepository,
    private readonly sourceRegistry: ITopicSourceRegistry,
    private readonly scoringService: ScoringService
  ) {}

  /**
   * Ejecuta el descubrimiento de topics desde fuentes externas.
   * @param input - Configuración: query opcional, límite por fuente, fuentes específicas
   * @returns Topics descubiertos, duplicados detectados y errores por fuente
   */
  async execute(input: DiscoverInput): Promise<DiscoverOutput> {
    const sources = this._resolveSources(input.sourceNames);
    const existingTopics = await this.repository.findAll({ limit: 1000 });
    const existingUrls = new Set(existingTopics.map((t) => t.url).filter(Boolean));
    const existingHashes = new Set(existingTopics.map((t) => t.duplicateHash).filter(Boolean));

    const allDiscovered: Topic[] = [];
    const allDuplicates: Topic[] = [];
    const errors: { source: string; error: string }[] = [];

    for (const source of sources) {
      try {
        const topics = await source.fetch(input.query, input.limit);

        for (const topic of topics) {
          // Asignar score
          const scored = topic.rescore(this.scoringService.calculate(topic).toPlain());

          // Detectar duplicados
          if (topic.url && existingUrls.has(topic.url)) {
            allDuplicates.push(scored);
            continue;
          }
          if (topic.duplicateHash && existingHashes.has(topic.duplicateHash)) {
            allDuplicates.push(scored);
            continue;
          }

          // Marcar como revisable
          allDiscovered.push(scored.markAsPendingReview());
        }
      } catch (err) {
        errors.push({
          source: source.sourceName,
          error: err instanceof Error ? err.message : "Unknown error",
        });
      }
    }

    // Persistir los nuevos
    if (allDiscovered.length > 0) {
      await this.repository.saveMany(allDiscovered);
    }

    return {
      discovered: allDiscovered.map((t) =>
        t.rescore(this.scoringService.calculate(t).toPlain())
      ),
      duplicates: allDuplicates,
      errors,
    };
  }

  /**
   * Resuelve las fuentes a consultar según los nombres solicitados.
   * Si no se especifican nombres, usa todas las fuentes disponibles.
   */
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
