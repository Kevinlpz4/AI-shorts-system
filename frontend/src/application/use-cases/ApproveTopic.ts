// ═══════════════════════════════════════════════════
// ApproveTopic — Application Use Case
// ═══════════════════════════════════════════════════
// Aprueba un topic para producción de contenido vía API.

import { TopicData } from "@/types";
import { ITopicRepository } from "@/domain/ports/ITopicRepository";

/**
 * Use case: aprobar un topic para producción de contenido.
 *
 * Delega al backend REST la validación y persistencia.
 */
export class ApproveTopic {
  constructor(private readonly repository: ITopicRepository) {}

  /**
   * Ejecuta la aprobación de un topic por ID.
   * @returns TopicData con estado actualizado
   */
  async execute(topicId: string): Promise<TopicData> {
    return this.repository.approve(topicId);
  }
}
