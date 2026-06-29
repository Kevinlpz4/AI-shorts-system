// ═══════════════════════════════════════════════════
// ListTopics — Application Use Case
// ═══════════════════════════════════════════════════
// Lista topics con filtros.
// Sin lógica de negocio — solo orquestación.

import { Topic } from "@/domain/entities/Topic";
import { ITopicRepository, TopicFilters } from "@/domain/ports/ITopicRepository";
import { ScoringService } from "@/domain/services/ScoringService";

/**
 * Use case: listar topics con filtros opcionales.
 *
 * Recalcula scores al vuelo (factores como recencia cambian con el tiempo).
 * Sin lógica de negocio — solo orquestación entre repositorio y dominio.
 */
export class ListTopics {
  constructor(
    private readonly repository: ITopicRepository,
    private readonly scoringService: ScoringService
  ) {}

  /**
   * Ejecuta la consulta de topics aplicando filtros y recalculando scores.
   * @param filters - Filtros opcionales (status, sourceName, minScore, searchQuery, limit, offset)
   * @returns Lista de entidades Topic con scores actualizados
   */
  async execute(filters?: TopicFilters): Promise<Topic[]> {
    const topics = await this.repository.findAll(filters);

    // Re-calcular scores (pueden haber cambiado factores externos como recencia)
    return topics.map((topic) => {
      const newScore = this.scoringService.calculate(topic);
      return topic.rescore(newScore.toPlain());
    });
  }

  /**
   * Obtiene estadísticas KPI directamente del repositorio.
   * @returns Conteo de topics por estado (discovered, pendingReview, approved, rejected)
   */
  async getKPIStats() {
    return this.repository.getKPIStats();
  }
}
