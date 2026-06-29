// ═══════════════════════════════════════════════════
// ApproveTopic — Application Use Case
// ═══════════════════════════════════════════════════
// Aprueba un topic para producción de contenido.
// Usa el TopicModerationService para validar reglas de negocio.

import { Topic } from "@/domain/entities/Topic";
import { ITopicRepository } from "@/domain/ports/ITopicRepository";
import { TopicModerationService } from "@/domain/services/TopicModerationService";

/**
 * Use case: aprobar un topic para producción de contenido.
 *
 * Valida contra reglas de negocio vía TopicModerationService antes de
 * transicionar el estado a APPROVED y persistir.
 */
export class ApproveTopic {
  constructor(
    private readonly repository: ITopicRepository,
    private readonly moderationService: TopicModerationService
  ) {}

  /**
   * Ejecuta la aprobación de un topic por ID.
   * @param topicId - ID único del topic a aprobar
   * @returns Entidad Topic con estado actualizado
   * @throws Error si el topic no existe o no cumple las reglas de moderación
   */
  async execute(topicId: string): Promise<Topic> {
    const topic = await this.repository.findById(topicId);
    if (!topic) {
      throw new Error(`Topic not found: ${topicId}`);
    }

    const validation = this.moderationService.validateApproval(topic);
    if (!validation.canApprove) {
      throw new Error(`Cannot approve topic: ${validation.reason}`);
    }

    const approved = topic.approve();
    return this.repository.save(approved);
  }
}
