// ═══════════════════════════════════════════════════
// RejectTopic — Application Use Case
// ═══════════════════════════════════════════════════
// Rechaza un topic. Validación vía TopicModerationService.

import { Topic } from "@/domain/entities/Topic";
import { ITopicRepository } from "@/domain/ports/ITopicRepository";
import { TopicModerationService } from "@/domain/services/TopicModerationService";

/**
 * Use case: rechazar un topic.
 *
 * Valúa que el topic sea elegible para rechazo (no terminal)
 * antes de transicionar el estado a REJECTED y persistir.
 */
export class RejectTopic {
  constructor(
    private readonly repository: ITopicRepository,
    private readonly moderationService: TopicModerationService
  ) {}

  /**
   * Ejecuta el rechazo de un topic por ID.
   * @param topicId - ID único del topic a rechazar
   * @returns Entidad Topic con estado actualizado
   * @throws Error si el topic no existe o no cumple las reglas de moderación
   */
  async execute(topicId: string): Promise<Topic> {
    const topic = await this.repository.findById(topicId);
    if (!topic) {
      throw new Error(`Topic not found: ${topicId}`);
    }

    const validation = this.moderationService.validateRejection(topic);
    if (!validation.canReject) {
      throw new Error(`Cannot reject topic: ${validation.reason}`);
    }

    const rejected = topic.reject();
    return this.repository.save(rejected);
  }
}
