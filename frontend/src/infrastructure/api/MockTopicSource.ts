// ═══════════════════════════════════════════════════
// MockTopicSource — Adapter that simulates external sources
// ═══════════════════════════════════════════════════
// Infrastructure: implementa ITopicSource con datos mock.
// Fácil de reemplazar por un adapter real (Google News API, etc.)

import { Topic } from "@/domain/entities/Topic";
import { Source, SourceType } from "@/domain/value-objects/Source";
import { Score } from "@/domain/value-objects/Score";
import { ITopicSource } from "@/domain/ports/ITopicSource";

/** Data mock para simular topics descubiertos desde fuentes externas */
const MOCK_TOPICS: Array<{
  title: string;
  description: string;
  sourceType: SourceType;
  url: string;
  score: { relevance: number; popularity: number; recency: number; reliability: number };
}> = [
  {
    title: "La IA está transformando la educación: 5 casos reales",
    description: "Descubre cómo instituciones educativas están implementando inteligencia artificial para personalizar el aprendizaje y mejorar resultados académicos.",
    sourceType: SourceType.GOOGLE_NEWS,
    url: "https://example.com/ai-education",
    score: { relevance: 9, popularity: 8, recency: 9, reliability: 7 },
  },
  {
    title: "Nuevo récord: batería de estado sólido alcanza 1000 km de autonomía",
    description: "Investigadores coreanos presentan una batería de estado sólido que promete revolucionar la industria automotriz con 1000 km de autonomía real.",
    sourceType: SourceType.GOOGLE_NEWS,
    url: "https://example.com/solid-state-battery",
    score: { relevance: 8, popularity: 9, recency: 10, reliability: 7 },
  },
  {
    title: "Ciberseguridad en 2026: las amenazas que nadie está viendo",
    description: "Expertos en seguridad identifican 3 vectores de ataque emergentes que podrían comprometer infraestructuras críticas este año.",
    sourceType: SourceType.TWITTER,
    url: "https://example.com/cyber-2026",
    score: { relevance: 7, popularity: 8, recency: 8, reliability: 6 },
  },
  {
    title: "El mercado de los NFTs renace: ventas aumentan 300% en Q2",
    description: "El mercado de tokens no fungibles experimenta un resurgimiento impulsado por nuevas aplicaciones en gaming y propiedad intelectual.",
    sourceType: SourceType.GOOGLE_NEWS,
    url: "https://example.com/nft-rebirth",
    score: { relevance: 6, popularity: 7, recency: 9, reliability: 5 },
  },
  {
    title: "JavaScript 2026: las características que van a cambiar cómo programás",
    description: "TC39 finaliza nuevas propuestas para ECMAScript 2026 incluyendo pattern matching, records y tuples que transformarán el desarrollo web.",
    sourceType: SourceType.RSS,
    url: "https://example.com/js-2026",
    score: { relevance: 9, popularity: 6, recency: 10, reliability: 8 },
  },
  {
    title: "DeepSeek-R2: el modelo chino que desafía a GPT-5",
    description: "El nuevo modelo de lenguaje de DeepSeek alcanza rendimiento comparable a GPT-5 con 40% menos recursos computacionales.",
    sourceType: SourceType.GOOGLE_NEWS,
    url: "https://example.com/deepseek-r2",
    score: { relevance: 9, popularity: 10, recency: 10, reliability: 7 },
  },
  {
    title: "Robótica asequible: robots con propósito entran al hogar",
    description: "Empresas japonesas lanzan robots domésticos con capacidades de limpieza, cocina y cuidado de adultos mayores a precios accesibles.",
    sourceType: SourceType.TWITTER,
    url: "https://example.com/home-robots",
    score: { relevance: 8, popularity: 7, recency: 7, reliability: 6 },
  },
  {
    title: "Arquitectura limpia en el mundo real: lecciones de 5 años de DDD",
    description: "Un repaso por las decisiones arquitectónicas que funcionaron (y las que no) al aplicar Domain-Driven Design en proyectos de producción.",
    sourceType: SourceType.RSS,
    url: "https://example.com/ddd-lessons",
    score: { relevance: 10, popularity: 5, recency: 8, reliability: 9 },
  },
];

/**
 * Adapter mock de ITopicSource que simula fuentes externas.
 *
 * Retorna datos precargados (MOCK_TOPICS) con latencia simulada.
 * Útil para desarrollo y testing sin conexión a APIs reales.
 * Fácil de reemplazar por un adapter real (Google News API, etc.).
 */
export class MockTopicSource implements ITopicSource {
  public readonly sourceName: string;

  constructor(
    name: string,
    private readonly mockData: typeof MOCK_TOPICS = MOCK_TOPICS
  ) {
    this.sourceName = name;
  }

  /** Siempre disponible (mock) */
  get available(): boolean {
    return true;
  }

  /**
   * Obtiene topics mock, opcionalmente filtrados por query.
   * Simula latencia de red (300-800ms).
   * @param query - Término de búsqueda opcional para filtrar por título/descripción
   * @param limit - Máximo de resultados a retornar
   */
  async fetch(query?: string, limit: number = 10): Promise<Topic[]> {
    // Simular latencia de red
    await new Promise((r) => setTimeout(r, 300 + Math.random() * 500));

    let filtered = this.mockData;

    if (query) {
      const q = query.toLowerCase();
      filtered = filtered.filter(
        (t) =>
          t.title.toLowerCase().includes(q) ||
          t.description.toLowerCase().includes(q)
      );
    }

    const results = filtered.slice(0, limit);

    return results.map(
      (data) =>
        new Topic({
          title: data.title,
          description: data.description,
          source: new Source({
            name: this.sourceName,
            type: data.sourceType,
            reliability: data.score.reliability * 10,
          }),
          score: new Score(data.score),
          url: data.url,
          publishedAt: new Date(Date.now() - Math.random() * 86400000 * 3), // últimos 3 días
        })
    );
  }
}
