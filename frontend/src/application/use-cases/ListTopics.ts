// ═══════════════════════════════════════════════════
// ListTopics — Application Use Case
// ═══════════════════════════════════════════════════
// Lista topics con filtros vía API.

import { TopicData } from "@/types";
import { ITopicRepository, TopicFilters } from "@/domain/ports/ITopicRepository";

/**
 * Use case: listar topics con filtros opcionales.
 *
 * El backend maneja scores, filtros y ordenamiento.
 */
export class ListTopics {
  constructor(private readonly repository: ITopicRepository) {}

  /**
   * Ejecuta la consulta de topics aplicando filtros.
   * @returns Lista de TopicData con scores desde el backend
   */
  async execute(filters?: TopicFilters): Promise<TopicData[]> {
    return this.repository.findAll(filters);
  }

  /** Obtiene estadísticas KPI directamente del repositorio. */
  async getKPIStats() {
    return this.repository.getKPIStats();
  }
}
