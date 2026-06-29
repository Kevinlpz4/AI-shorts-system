// ═══════════════════════════════════════════════════
// Score Value Object — Immutable score breakdown
// ═══════════════════════════════════════════════════
// Domain primitive: no depende de nada externo.
// Todos los puntajes van de 0 a 10.

export interface ScoreParams {
  relevance: number;
  popularity: number;
  recency: number;
  reliability: number;
}

export class Score {
  public readonly relevance: number;
  public readonly popularity: number;
  public readonly recency: number;
  public readonly reliability: number;

  // Pesos para el score total
  private static readonly WEIGHTS = {
    relevance: 0.35,
    popularity: 0.25,
    recency: 0.25,
    reliability: 0.15,
  } as const;

  constructor(params: ScoreParams) {
    this.relevance = Score._clamp(params.relevance);
    this.popularity = Score._clamp(params.popularity);
    this.recency = Score._clamp(params.recency);
    this.reliability = Score._clamp(params.reliability);

    // Congelar para inmutabilidad
    Object.freeze(this);
  }

  /** Score total ponderado (0–10) */
  get total(): number {
    return Number(
      (
        this.relevance * Score.WEIGHTS.relevance +
        this.popularity * Score.WEIGHTS.popularity +
        this.recency * Score.WEIGHTS.recency +
        this.reliability * Score.WEIGHTS.reliability
      ).toFixed(1)
    );
  }

  /** Representación plana para persistencia/API */
  toPlain(): ScoreParams & { total: number } {
    return {
      relevance: this.relevance,
      popularity: this.popularity,
      recency: this.recency,
      reliability: this.reliability,
      total: this.total,
    };
  }

  /** Crea Score desde datos planos */
  static fromPlain(data: ScoreParams): Score {
    return new Score(data);
  }

  /** Score cero (para seeded/default) */
  static zero(): Score {
    return new Score({ relevance: 0, popularity: 0, recency: 0, reliability: 0 });
  }

  // ── Privados ──

  private static _clamp(value: number): number {
    return Math.max(0, Math.min(10, Math.round(value)));
  }
}
