// ═══════════════════════════════════════════════════
// TopicRepositoryImpl — In-memory repository implementation
// ═══════════════════════════════════════════════════
// Infrastructure: implementa ITopicRepository en memoria.
// Fácil de reemplazar por SQLite, IndexedDB, o API REST.

import { Topic } from "@/domain/entities/Topic";
import { TopicStatusValue } from "@/domain/value-objects/TopicStatus";
import { ITopicRepository, TopicFilters, KPIResult } from "@/domain/ports/ITopicRepository";

/**
 * Repositorio en memoria que implementa ITopicRepository.
 *
 * Almacena topics en un Map<string, Topic>. Diseñado para desarrollo
 * y testing — fácil de reemplazar por una implementación real
 * (SQLite, IndexedDB, API REST) sin cambiar el dominio.
 */
export class TopicRepositoryImpl implements ITopicRepository {
  private topics: Map<string, Topic> = new Map();

  // ── Seed data ──

  constructor(seedData?: Topic[]) {
    if (seedData) {
      seedData.forEach((t) => this.topics.set(t.id, t));
    }
  }

  // ── Lectura ──

  /**
   * Obtiene todos los topics aplicando filtros opcionales.
   * Ordena por score descendente + fecha descendente.
   * Soporta paginación via limit/offset.
   */
  async findAll(filters?: TopicFilters): Promise<Topic[]> {
    let result = Array.from(this.topics.values());

    if (filters?.status) {
      result = result.filter((t) => t.status.value === filters.status);
    }
    if (filters?.sourceName) {
      result = result.filter((t) => t.source.name === filters.sourceName);
    }
    if ((filters?.minScore ?? 0) > 0) {
      result = result.filter((t) => t.scoreTotal >= (filters?.minScore ?? 0));
    }
    if (filters?.searchQuery) {
      const q = filters.searchQuery.toLowerCase();
      result = result.filter(
        (t) =>
          t.title.toLowerCase().includes(q) ||
          t.description.toLowerCase().includes(q)
      );
    }

    // Ordenar por score descendente + fecha descendente
    result.sort((a, b) => {
      const scoreDiff = b.scoreTotal - a.scoreTotal;
      if (scoreDiff !== 0) return scoreDiff;
      return b.createdAt.getTime() - a.createdAt.getTime();
    });

    const limit = filters?.limit ?? 50;
    const offset = filters?.offset ?? 0;
    return result.slice(offset, offset + limit);
  }

  /**
   * Busca un topic por su ID único.
   * @returns Topic o null si no existe
   */
  async findById(id: string): Promise<Topic | null> {
    return this.topics.get(id) || null;
  }

  /**
   * Busca topics que compartan un mismo duplicateHash.
   * Útil para detección de duplicados por contenido.
   */
  async findByDuplicateHash(hash: string): Promise<Topic[]> {
    return Array.from(this.topics.values()).filter(
      (t) => t.duplicateHash === hash
    );
  }

  /**
   * Obtiene estadísticas KPI: conteo de topics agrupados por estado.
   */
  async getKPIStats(): Promise<KPIResult> {
    const all = Array.from(this.topics.values());
    return {
      discovered: all.filter((t) => t.status.value === TopicStatusValue.FOUND).length,
      pendingReview: all.filter((t) => t.status.value === TopicStatusValue.PENDING_REVIEW).length,
      approved: all.filter((t) => t.status.value === TopicStatusValue.APPROVED).length,
      rejected: all.filter((t) => t.status.value === TopicStatusValue.REJECTED).length,
    };
  }

  // ── Escritura ──

  /**
   * Guarda (crea o actualiza) un topic en el repositorio en memoria.
   * @returns El topic guardado (idéntico al de entrada)
   */
  async save(topic: Topic): Promise<Topic> {
    this.topics.set(topic.id, topic);
    return topic;
  }

  /**
   * Guarda múltiples topics en batch.
   */
  async saveMany(topics: Topic[]): Promise<Topic[]> {
    topics.forEach((t) => this.topics.set(t.id, t));
    return topics;
  }

  /**
   * Elimina un topic del repositorio por ID.
   */
  async delete(id: string): Promise<void> {
    this.topics.delete(id);
  }
}
