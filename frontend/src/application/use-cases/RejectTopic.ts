// ═══════════════════════════════════════════════════
// RejectTopic — Application Use Case
// ═══════════════════════════════════════════════════
// Rechaza un topic vía API.

import { TopicData } from "@/types";
import { ITopicRepository } from "@/domain/ports/ITopicRepository";

/**
 * Use case: rechazar un topic.
 *
 * Delega al backend REST la validación y persistencia.
 */
export class RejectTopic {
  constructor(private readonly repository: ITopicRepository) {}

  /**
   * Ejecuta el rechazo de un topic por ID.
   * @returns TopicData con estado actualizado
   */
  async execute(topicId: string): Promise<TopicData> {
    return this.repository.reject(topicId);
  }
}
