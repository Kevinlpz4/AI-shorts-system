// ═══════════════════════════════════════════════════
// Topic — Aggregate Root entity
// ═══════════════════════════════════════════════════
// Núcleo del dominio: un topic es el agregado principal.
// Contiene toda la lógica de negocio del ciclo de vida.

import { Score, ScoreParams } from "@/domain/value-objects/Score";
import { TopicStatus, TopicStatusValue } from "@/domain/value-objects/TopicStatus";
import { Source } from "@/domain/value-objects/Source";

export interface TopicParams {
  id?: string;
  title: string;
  description?: string;
  content?: string;
  source: Source;
  score?: Score;
  status?: TopicStatus;
  url?: string | null;
  author?: string | null;
  publishedAt?: Date | null;
  createdAt?: Date;
  reviewedAt?: Date | null;
  duplicateHash?: string | null;
}

export class Topic {
  public readonly id: string;
  public readonly title: string;
  public readonly description: string;
  public readonly content: string;
  public readonly source: Source;
  public readonly score: Score;
  public readonly status: TopicStatus;
  public readonly url: string | null;
  public readonly author: string | null;
  public readonly publishedAt: Date | null;
  public readonly createdAt: Date;
  public readonly reviewedAt: Date | null;
  public readonly duplicateHash: string | null;

  constructor(params: TopicParams) {
    this.id = params.id || crypto.randomUUID();
    this.title = params.title;
    this.description = params.description || "";
    this.content = params.content || "";
    this.source = params.source;
    this.score = params.score || Score.zero();
    this.status = params.status || TopicStatus.initial();
    this.url = params.url || null;
    this.author = params.author || null;
    this.publishedAt = params.publishedAt || null;
    this.createdAt = params.createdAt || new Date();
    this.reviewedAt = params.reviewedAt || null;
    this.duplicateHash = params.duplicateHash || null;

    Object.freeze(this);
  }

  // ── Comportamiento ──

  /** Rechazar el topic */
  reject(): Topic {
    return this._transition(TopicStatusValue.REJECTED, { reviewedAt: new Date() });
  }

  /** Aprobar el topic para producción de contenido */
  approve(): Topic {
    return this._transition(TopicStatusValue.APPROVED, { reviewedAt: new Date() });
  }

  /** Marcar como pendiente de revisión (después de descubrimiento automático) */
  markAsPendingReview(): Topic {
    return this._transition(TopicStatusValue.PENDING_REVIEW);
  }

  /** Re-calcula el score del topic */
  rescore(scoreParams: ScoreParams): Topic {
    return new Topic({ ...this._plain(), score: new Score(scoreParams) });
  }

  // ── Queries ──

  get isApproved(): boolean {
    return this.status.value === TopicStatusValue.APPROVED;
  }

  get isRejected(): boolean {
    return this.status.value === TopicStatusValue.REJECTED;
  }

  get isPendingReview(): boolean {
    return this.status.value === TopicStatusValue.PENDING_REVIEW;
  }

  get isTerminal(): boolean {
    return this.status.isTerminal;
  }

  get scoreTotal(): number {
    return this.score.total;
  }

  // ── Serialización ──

  toPlain() {
    return {
      id: this.id,
      title: this.title,
      description: this.description,
      contentPreview: this.content.slice(0, 200),
      sourceName: this.source.name,
      sourceType: this.source.type,
      status: this.status.value,
      score: this.score.toPlain(),
      scoreTotal: this.score.total,
      url: this.url,
      author: this.author,
      createdAt: this.createdAt.toISOString(),
      reviewedAt: this.reviewedAt?.toISOString() || null,
      duplicateHash: this.duplicateHash,
    };
  }

  // ── Privados ──

  private _transition(nextStatus: TopicStatusValue, extra?: Partial<TopicParams>): Topic {
    const newStatus = this.status.transitionTo(nextStatus);
    return new Topic({ ...this._plain(), ...extra, status: newStatus });
  }

  private _plain(): TopicParams {
    return {
      id: this.id,
      title: this.title,
      description: this.description,
      content: this.content,
      source: this.source,
      score: this.score,
      status: this.status,
      url: this.url,
      author: this.author,
      publishedAt: this.publishedAt,
      createdAt: this.createdAt,
      reviewedAt: this.reviewedAt,
      duplicateHash: this.duplicateHash,
    };
  }
}
