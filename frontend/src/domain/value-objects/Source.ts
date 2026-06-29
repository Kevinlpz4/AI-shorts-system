// ═══════════════════════════════════════════════════
// Source Value Object — Information source metadata
// ═══════════════════════════════════════════════════

export enum SourceType {
  MANUAL = "manual",
  AUTOMATIC = "automatic",
  GOOGLE_NEWS = "google_news",
  TWITTER = "twitter",
  RSS = "rss",
}

export interface SourceParams {
  name: string;
  type: SourceType;
  reliability: number;
}

export class Source {
  public readonly name: string;
  public readonly type: SourceType;
  public readonly reliability: number;

  constructor(params: SourceParams) {
    this.name = params.name;
    this.type = params.type;
    this.reliability = Math.max(0, Math.min(100, params.reliability));
    Object.freeze(this);
  }

  get isExternal(): boolean {
    return this.type !== SourceType.MANUAL;
  }

  get displayName(): string {
    const names: Record<SourceType, string> = {
      [SourceType.MANUAL]: "Manual Input",
      [SourceType.AUTOMATIC]: "Auto-Detected",
      [SourceType.GOOGLE_NEWS]: "Google News",
      [SourceType.TWITTER]: "Twitter/X",
      [SourceType.RSS]: "RSS Feed",
    };
    return names[this.type] || this.name;
  }

  static manual(): Source {
    return new Source({ name: "manual", type: SourceType.MANUAL, reliability: 80 });
  }

  static googleNews(): Source {
    return new Source({ name: "google-news-rss", type: SourceType.GOOGLE_NEWS, reliability: 75 });
  }

  toPlain() {
    return { name: this.name, type: this.type, reliability: this.reliability };
  }
}
