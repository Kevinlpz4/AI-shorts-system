// ═══════════════════════════════════════════════════
// CreateManualTopic — Application Use Case
// ═══════════════════════════════════════════════════
// Crea un topic manualmente desde input del usuario vía API.

import { TopicData } from "@/types";
import { ITopicRepository } from "@/domain/ports/ITopicRepository";

/** Input para crear un topic manualmente desde formulario */
export interface ManualTopicInput {
  title: string;
  description: string;
  url: string | null;
  sourceName?: string;
}

/** Resultado de la creación manual */
export interface ManualTopicResult {
  topic: TopicData;
  isDuplicate: boolean;
}

/**
 * Use case: crear un topic manualmente.
 *
 * Delega al backend REST la detección de duplicados y persistencia.
 */
export class CreateManualTopic {
  constructor(private readonly repository: ITopicRepository) {}

  async execute(input: ManualTopicInput): Promise<ManualTopicResult> {
    return this.repository.createManual({
      title: input.title,
      description: input.description,
      url: input.url,
      sourceName: input.sourceName || "manual",
    });
  }
}
