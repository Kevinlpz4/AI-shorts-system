// ═══════════════════════════════════════════════════
// ScoringService — Domain service for score calculation
// ═══════════════════════════════════════════════════
// Puro: sin efectos secundarios, sin dependencias externas.
// Las reglas de scoring viven acá, no en los componentes.

import { Score } from "@/domain/value-objects/Score";
import { Topic } from "@/domain/entities/Topic";

export interface KeywordWeight {
  keyword: string;
  relevanceBoost: number;
}

const DEFAULT_KEYWORDS: KeywordWeight[] = [
  { keyword: "ia", relevanceBoost: 2 },
  { keyword: "inteligencia artificial", relevanceBoost: 3 },
  { keyword: "machine learning", relevanceBoost: 2 },
  { keyword: "tecnología", relevanceBoost: 1 },
  { keyword: "startup", relevanceBoost: 1 },
  { keyword: "innovación", relevanceBoost: 1 },
];

export class ScoringService {
  constructor(private readonly keywords: KeywordWeight[] = DEFAULT_KEYWORDS) {}

  /**
   * Calcula el score para un topic basado en su contenido.
   * SRP: única responsabilidad → calcular scores.
   */
  calculate(topic: Topic): Score {
    const relevance = this._calcRelevance(topic);
    const popularity = this._calcPopularity(topic);
    const recency = this._calcRecency(topic);
    const reliability = topic.source.reliability / 10;

    return new Score({ relevance, popularity, recency, reliability });
  }

  /**
   * Calcula score basado en metadata (sin entidad Topic).
   * Útil para previsualizaciones antes de crear el agregado.
   */
  calculateFromMeta(params: {
    title: string;
    description: string;
    sourceReliability: number;
    publishedAt?: Date | null;
  }): Score {
    const lowerText = `${params.title} ${params.description}`.toLowerCase();
    const relevance = this._keywordScore(lowerText);
    const recency = params.publishedAt
      ? this._recencyScore(params.publishedAt)
      : 5;
    return new Score({
      relevance,
      popularity: 5, // default sin datos
      recency,
      reliability: params.sourceReliability / 10,
    });
  }

  // ── Privados ──

  private _calcRelevance(topic: Topic): number {
    const text = `${topic.title} ${topic.description} ${topic.content}`.toLowerCase();
    return this._keywordScore(text);
  }

  private _keywordScore(text: string): number {
    let score = 3; // base
    for (const kw of this.keywords) {
      if (text.includes(kw.keyword.toLowerCase())) {
        score += kw.relevanceBoost;
      }
    }
    return Math.min(10, score);
  }

  private _calcPopularity(_topic: Topic): number {
    // En producción: vendría de datos reales (shares, views, etc.)
    return Math.floor(Math.random() * 5) + 3; // 3–8 simulados
  }

  private _calcRecency(topic: Topic): number {
    const date = topic.publishedAt || topic.createdAt;
    return this._recencyScore(date);
  }

  private _recencyScore(date: Date): number {
    const hoursDiff = (Date.now() - date.getTime()) / (1000 * 60 * 60);
    if (hoursDiff < 6) return 10;
    if (hoursDiff < 24) return 8;
    if (hoursDiff < 72) return 6;
    if (hoursDiff < 168) return 4; // 1 semana
    return 2;
  }
}
