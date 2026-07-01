// ═══════════════════════════════════════════════════
// Container — Composition Root (Dependency Injection)
// ═══════════════════════════════════════════════════
// Único lugar donde se crean y conectan todas las dependencias.
// Siempre conecta al backend REST via NEXT_PUBLIC_API_URL.

import { ApiTopicSource } from "@/infrastructure/api/ApiTopicSource";
import { ApiTopicRepository } from "@/infrastructure/api/ApiTopicRepository";
import { SourceRegistry } from "@/infrastructure/api/SourceRegistry";
import { DiscoverTopics } from "@/application/use-cases/DiscoverTopics";
import { ApproveTopic } from "@/application/use-cases/ApproveTopic";
import { RejectTopic } from "@/application/use-cases/RejectTopic";
import { CreateManualTopic } from "@/application/use-cases/CreateManualTopic";
import { ListTopics } from "@/application/use-cases/ListTopics";

/**
 * Composition Root del frontend (Dependency Injection).
 * Siempre usa adapters API REST conectados al backend.
 */
class AppContainer {
  readonly repository: ApiTopicRepository;
  readonly sourceRegistry: SourceRegistry;
  readonly discoverTopics: DiscoverTopics;
  readonly approveTopic: ApproveTopic;
  readonly rejectTopic: RejectTopic;
  readonly createManualTopic: CreateManualTopic;
  readonly listTopics: ListTopics;

  constructor() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;

    if (!apiUrl) {
      console.warn(
        "[Container] NEXT_PUBLIC_API_URL not set. API calls will use default http://localhost:8000"
      );
    }

    const baseUrl = apiUrl || "http://localhost:8000";

    // ── Infra ─────────────────────────────────────
    this.repository = new ApiTopicRepository(baseUrl);
    this.sourceRegistry = new SourceRegistry();
    this.sourceRegistry.register(new ApiTopicSource(baseUrl, "google-news"));
    this.sourceRegistry.register(new ApiTopicSource(baseUrl, "twitter"));
    this.sourceRegistry.register(new ApiTopicSource(baseUrl, "rss"));

    // ── Use cases ─────────────────────────────────
    this.discoverTopics = new DiscoverTopics(this.repository, this.sourceRegistry);
    this.approveTopic = new ApproveTopic(this.repository);
    this.rejectTopic = new RejectTopic(this.repository);
    this.createManualTopic = new CreateManualTopic(this.repository);
    this.listTopics = new ListTopics(this.repository);
  }
}

export const container = new AppContainer();
