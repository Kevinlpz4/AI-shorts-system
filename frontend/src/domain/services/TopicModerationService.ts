// ═══════════════════════════════════════════════════
// TopicModerationService — Domain service for moderation
// ═══════════════════════════════════════════════════
// Reglas de negocio sobre moderación/aprobación.
// Sin dependencias externas.

import { Topic } from "@/domain/entities/Topic";

export interface ModerationResult {
  canApprove: boolean;
  canReject: boolean;
  reason?: string;
}

export class TopicModerationService {
  /**
   * Valida si un topic puede ser aprobado.
   * SRP: solo reglas de moderación.
   * OCP: nuevas reglas se agregan sin modificar el método.
   */
  validateApproval(topic: Topic): ModerationResult {
    const rules = [
      this._mustBePendingReview,
      this._mustHaveTitle,
      this._mustHaveMinimumScore,
    ];

    for (const rule of rules) {
      const result = rule(topic);
      if (!result.canApprove) return result;
    }

    return { canApprove: true, canReject: true };
  }

  /**
   * Valida si un topic puede ser rechazado.
   */
  validateRejection(topic: Topic): ModerationResult {
    if (topic.isTerminal) {
      return {
        canApprove: false,
        canReject: false,
        reason: `Topic already ${topic.status.label}. Terminal state.`,
      };
    }
    return { canApprove: topic.isPendingReview, canReject: true };
  }

  // ── Reglas individuales (SRP: una regla por método) ──

  private _mustBePendingReview(topic: Topic): ModerationResult {
    if (!topic.isPendingReview) {
      return {
        canApprove: false,
        canReject: false,
        reason: `Cannot moderate a topic in "${topic.status.label}" state. Must be Pending Review.`,
      };
    }
    return { canApprove: true, canReject: true };
  }

  private _mustHaveTitle(topic: Topic): ModerationResult {
    if (!topic.title || topic.title.trim().length < 3) {
      return {
        canApprove: false,
        canReject: true,
        reason: "Topic must have a meaningful title (at least 3 characters).",
      };
    }
    return { canApprove: true, canReject: true };
  }

  private _mustHaveMinimumScore(topic: Topic): ModerationResult {
    if (topic.scoreTotal < 3) {
      return {
        canApprove: false,
        canReject: true,
        reason: `Topic score too low (${topic.scoreTotal}). Minimum required: 3.0.`,
      };
    }
    return { canApprove: true, canReject: true };
  }
}
