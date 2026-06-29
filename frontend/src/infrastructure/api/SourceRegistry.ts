// ═══════════════════════════════════════════════════
// SourceRegistry — Concrete implementation of ITopicSourceRegistry
// ═══════════════════════════════════════════════════
// Infrastructure: Registry pattern. Almacena referencias a
// fuentes externas y permite consultarlas por nombre.

import { ITopicSource, ITopicSourceRegistry } from "@/domain/ports/ITopicSource";

/**
 * Registry de fuentes externas (Registry Pattern).
 *
 * Almacena referencias a adapters ITopicSource y permite
 * consultarlas por nombre u obtener todas las disponibles.
 */
export class SourceRegistry implements ITopicSourceRegistry {
  private sources: Map<string, ITopicSource> = new Map();

  /**
   * Registra una nueva fuente en el registry.
   * @throws Error si ya existe una fuente con el mismo sourceName
   */
  register(source: ITopicSource): void {
    if (this.sources.has(source.sourceName)) {
      throw new Error(`Source '${source.sourceName}' already registered`);
    }
    this.sources.set(source.sourceName, source);
  }

  /**
   * Obtiene una fuente por nombre.
   * @throws Error si la fuente no está registrada
   */
  get(name: string): ITopicSource {
    const source = this.sources.get(name);
    if (!source) {
      throw new Error(`Source '${name}' not found in registry`);
    }
    return source;
  }

  /** Obtiene todas las fuentes que están actualmente disponibles */
  getAllAvailable(): ITopicSource[] {
    return Array.from(this.sources.values()).filter((s) => s.available);
  }

  /** Lista todas las fuentes registradas con su estado de disponibilidad */
  list(): { name: string; available: boolean }[] {
    return Array.from(this.sources.entries()).map(([name, source]) => ({
      name,
      available: source.available,
    }));
  }
}
