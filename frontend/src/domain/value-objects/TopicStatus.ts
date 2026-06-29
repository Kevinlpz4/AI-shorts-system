// ═══════════════════════════════════════════════════
// TopicStatus Value Object — State machine for topics
// ═══════════════════════════════════════════════════
// Domain primitive: define los estados válidos de un topic
// y las transiciones permitidas.

export enum TopicStatusValue {
  FOUND = "FOUND",
  PENDING_REVIEW = "PENDING_REVIEW",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
}

const TRANSITIONS: Record<TopicStatusValue, TopicStatusValue[]> = {
  [TopicStatusValue.FOUND]: [TopicStatusValue.PENDING_REVIEW],
  [TopicStatusValue.PENDING_REVIEW]: [TopicStatusValue.APPROVED, TopicStatusValue.REJECTED],
  [TopicStatusValue.APPROVED]: [],
  [TopicStatusValue.REJECTED]: [],
};

export class TopicStatus {
  private constructor(public readonly value: TopicStatusValue) {
    Object.freeze(this);
  }

  // ── Factory ──

  static initial(): TopicStatus {
    return new TopicStatus(TopicStatusValue.PENDING_REVIEW);
  }

  static from(value: string): TopicStatus {
    const upper = value.toUpperCase() as TopicStatusValue;
    if (!Object.values(TopicStatusValue).includes(upper)) {
      throw new Error(`Invalid TopicStatus: "${value}"`);
    }
    return new TopicStatus(upper);
  }

  // ── Transiciones ──

  canTransitionTo(next: TopicStatus): boolean {
    return TRANSITIONS[this.value].includes(next.value);
  }

  transitionTo(next: TopicStatusValue): TopicStatus {
    if (!TRANSITIONS[this.value].includes(next)) {
      throw new Error(
        `Cannot transition from "${this.value}" to "${next}". Allowed: [${TRANSITIONS[this.value]}]`
      );
    }
    return new TopicStatus(next);
  }

  // ── Queries ──

  get isTerminal(): boolean {
    return TRANSITIONS[this.value].length === 0;
  }

  get isReviewable(): boolean {
    return this.value === TopicStatusValue.PENDING_REVIEW;
  }

  get label(): string {
    const labels: Record<TopicStatusValue, string> = {
      [TopicStatusValue.FOUND]: "Found",
      [TopicStatusValue.PENDING_REVIEW]: "Pending Review",
      [TopicStatusValue.APPROVED]: "Approved",
      [TopicStatusValue.REJECTED]: "Rejected",
    };
    return labels[this.value];
  }
}
