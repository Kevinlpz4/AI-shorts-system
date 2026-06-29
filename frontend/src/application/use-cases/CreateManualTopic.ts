// ═══════════════════════════════════════════════════
// CreateManualTopic — Application Use Case
// ═══════════════════════════════════════════════════
// Crea un topic manualmente desde input del usuario.
// Detecta duplicados por URL.

import { Topic } from "@/domain/entities/Topic";
import { Source, SourceType } from "@/domain/value-objects/Source";
import { ITopicRepository } from "@/domain/ports/ITopicRepository";
import { ScoringService } from "@/domain/services/ScoringService";

/** Input para crear un topic manualmente desde formulario */
export interface ManualTopicInput {
  title: string;
  description: string;
  url: string | null;
  sourceName?: string;
}

/** Resultado de la creación manual */
export interface ManualTopicResult {
  topic: Topic;
  isDuplicate: boolean;
}

/**
 * Use case: crear un topic manualmente desde input del usuario.
 *
 * Detecta duplicados por URL/título antes de persistir,
 * calcula score inicial vía ScoringService.
 */
export class CreateManualTopic {
  constructor(
    private readonly repository: ITopicRepository,
    private readonly scoringService: ScoringService
  ) {}

  /**
   * Ejecuta la creación manual de un topic.
   * @param input - Datos del formulario (title, description, url, sourceName)
   * @returns Topic creado (o detectado como duplicado) + flag isDuplicate
   */
  async execute(input: ManualTopicInput): Promise<ManualTopicResult> {
    // Verificar duplicados por URL
    if (input.url) {
      const existing = await this.repository.findAll({ limit: 100 });
      const isDuplicate = existing.some(
        (t) => t.url === input.url || (t.title.toLowerCase() === input.title.toLowerCase())
      );
      if (isDuplicate) {
        // No guardar, retornar duplicado
        const topic = this._createTopic(input);
        return { topic, isDuplicate: true };
      }
    }

    const topic = this._createTopic(input);

    // Calcular score
    const scored = topic.rescore(
      this.scoringService
        .calculateFromMeta({
          title: topic.title,
          description: topic.description,
          sourceReliability: 80,
          publishedAt: topic.publishedAt,
        })
        .toPlain()
    );

    const saved = await this.repository.save(scored);
    return { topic: saved, isDuplicate: false };
  }

  /**
   * Crea la entidad Topic desde el input del formulario.
   * No persiste — solo construye la entidad en memoria.
   */
  private _createTopic(input: ManualTopicInput): Topic {
    return new Topic({
      title: input.title,
      description: input.description,
      source: new Source({
        name: input.sourceName || "manual",
        type: SourceType.MANUAL,
        reliability: 80,
      }),
      url: input.url || null,
    });
  }
}
