// ═══════════════════════════════════════════════════
// ITopicRepository — Port (Interface Adapter pattern)
// ═══════════════════════════════════════════════════
// Define el contrato para persistencia de topics.
// El dominio depende de esto, no al revés.
// La implementación concreta vive en infrastructure/.

import { Topic } from "@/domain/entities/Topic";
import { TopicStatusValue } from "@/domain/value-objects/TopicStatus";

export interface TopicFilters {
  status?: TopicStatusValue;
  sourceName?: string;
  minScore?: number;
  searchQuery?: string;
  limit?: number;
  offset?: number;
}

export interface KPIResult {
  discovered: number;
  pendingReview: number;
  approved: number;
  rejected: number;
}

export interface ITopicRepository {
  /** Obtener todos los topics (con filtros opcionales) */
  findAll(filters?: TopicFilters): Promise<Topic[]>;

  /** Obtener un topic por ID */
  findById(id: string): Promise<Topic | null>;

  /** Guardar un topic (crear o actualizar) */
  save(topic: Topic): Promise<Topic>;

  /** Guardar múltiples topics (batch) */
  saveMany(topics: Topic[]): Promise<Topic[]>;

  /** Eliminar un topic */
  delete(id: string): Promise<void>;

  /** Contar topics agrupados por estado */
  getKPIStats(): Promise<KPIResult>;

  /** Buscar duplicados por hash */
  findByDuplicateHash(hash: string): Promise<Topic[]>;
}
