// ═══════════════════════════════════════════════════
// ITopicRepository — Port (Interface Adapter pattern)
// ═══════════════════════════════════════════════════
// Define el contrato para persistencia de topics.
// Implementaciones concretas en infrastructure/.

import { TopicData, TopicStatusValue } from "@/types";

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
  findAll(filters?: TopicFilters): Promise<TopicData[]>;

  /** Obtener un topic por ID */
  findById(id: string): Promise<TopicData | null>;

  /** Guardar un topic (crear o actualizar) */
  save(topic: TopicData): Promise<TopicData>;

  /** Guardar múltiples topics (batch) */
  saveMany(topics: TopicData[]): Promise<TopicData[]>;

  /** Eliminar un topic */
  delete(id: string): Promise<void>;

  /** Contar topics agrupados por estado */
  getKPIStats(): Promise<KPIResult>;

  /** Buscar duplicados por hash */
  findByDuplicateHash(hash: string): Promise<TopicData[]>;

  /** Aprobar un topic */
  approve(id: string): Promise<TopicData>;

  /** Rechazar un topic */
  reject(id: string, reason?: string): Promise<TopicData>;

  /** Crear topic manual */
  createManual(input: {
    title: string;
    description?: string;
    url?: string | null;
    content?: string;
    author?: string;
    sourceName?: string;
  }): Promise<{ topic: TopicData; isDuplicate: boolean }>;
}
