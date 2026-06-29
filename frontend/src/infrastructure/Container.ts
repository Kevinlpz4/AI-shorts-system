// ═══════════════════════════════════════════════════
// Container — Composition Root (Dependency Injection)
// ═══════════════════════════════════════════════════
// Único lugar donde se crean y conectan todas las dependencias.
// Si cambiás un adapter, lo cambiás SOLO acá.
//
// NEXT_PUBLIC_API_URL:
//   - Si está definida → usa ApiTopicSource + ApiTopicRepository
//   - Si NO está definida → usa MockTopicSource + TopicRepositoryImpl
//
// El switch es transparente para use cases y store.
// La firma del constructor NO cambia.

import { ITopicRepository } from "@/domain/ports/ITopicRepository";
import { TopicRepositoryImpl } from "@/infrastructure/repos/TopicRepositoryImpl";
import { MockTopicSource } from "@/infrastructure/api/MockTopicSource";
import { ApiTopicSource } from "@/infrastructure/api/ApiTopicSource";
import { ApiTopicRepository } from "@/infrastructure/api/ApiTopicRepository";
import { SourceRegistry } from "@/infrastructure/api/SourceRegistry";
import { ScoringService } from "@/domain/services/ScoringService";
import { TopicModerationService } from "@/domain/services/TopicModerationService";
import { DiscoverTopics } from "@/application/use-cases/DiscoverTopics";
import { ApproveTopic } from "@/application/use-cases/ApproveTopic";
import { RejectTopic } from "@/application/use-cases/RejectTopic";
import { CreateManualTopic } from "@/application/use-cases/CreateManualTopic";
import { ListTopics } from "@/application/use-cases/ListTopics";
import { Topic } from "@/domain/entities/Topic";
import { Source, SourceType } from "@/domain/value-objects/Source";
import { Score } from "@/domain/value-objects/Score";

// ── Seed Data (solo usado en modo mock) ────────────

/**
 * Genera topics semilla para el modo mock.
 * Datos variados con scores, fuentes y antigüedad diferentes
 * para una experiencia realista en desarrollo.
 */
function createSeedTopics(): Topic[] {
  return [
    new Topic({
      title: "La IA está transformando la educación: 5 casos reales",
      description: "Instituciones educativas implementan IA para personalizar el aprendizaje y mejorar resultados académicos.",
      source: new Source({ name: "google-news", type: SourceType.GOOGLE_NEWS, reliability: 75 }),
      score: new Score({ relevance: 9, popularity: 8, recency: 9, reliability: 7 }),
      url: "https://example.com/ai-education",
      createdAt: new Date(Date.now() - 1000 * 60 * 30), // 30 min ago
    }),
    new Topic({
      title: "Nuevo récord: batería de estado sólido alcanza 1000 km",
      description: "Investigadores coreanos presentan batería que promete revolucionar la industria automotriz.",
      source: new Source({ name: "google-news", type: SourceType.GOOGLE_NEWS, reliability: 70 }),
      score: new Score({ relevance: 8, popularity: 9, recency: 10, reliability: 7 }),
      url: "https://example.com/solid-state-battery",
      createdAt: new Date(Date.now() - 1000 * 60 * 120), // 2 hours ago
    }),
    new Topic({
      title: "Ciberseguridad 2026: amenazas que nadie está viendo",
      description: "Expertos identifican 3 vectores de ataque emergentes para infraestructuras críticas.",
      source: new Source({ name: "twitter", type: SourceType.TWITTER, reliability: 60 }),
      score: new Score({ relevance: 7, popularity: 8, recency: 8, reliability: 6 }),
      url: "https://example.com/cyber-2026",
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 5), // 5 hours ago
    }),
    new Topic({
      title: "Arquitectura limpia en el mundo real: lecciones de DDD",
      description: "Decisiones arquitectónicas que funcionaron al aplicar Domain-Driven Design en producción.",
      source: new Source({ name: "dev-blog", type: SourceType.RSS, reliability: 85 }),
      score: new Score({ relevance: 10, popularity: 5, recency: 8, reliability: 9 }),
      url: "https://example.com/ddd-lessons",
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24), // 1 day ago
    }),
    new Topic({
      title: "DeepSeek-R2: el modelo chino que desafía a GPT-5",
      description: "Nuevo modelo de DeepSeek alcanza rendimiento comparable a GPT-5 con 40% menos recursos.",
      source: new Source({ name: "google-news", type: SourceType.GOOGLE_NEWS, reliability: 70 }),
      score: new Score({ relevance: 9, popularity: 10, recency: 10, reliability: 7 }),
      url: "https://example.com/deepseek-r2",
      createdAt: new Date(Date.now() - 1000 * 60 * 15), // 15 min ago
    }),
  ];
}

// ── Container — Singleton ─────────────────────────

/**
 * Composition Root del frontend (Dependency Injection).
 *
 * Único lugar donde se crean y conectan todas las dependencias.
 * Detecta automáticamente el modo de operación via NEXT_PUBLIC_API_URL:
 *   - Definida → modo API (conectado al backend REST real)
 *   - No definida → modo Mock (datos en memoria para desarrollo)
 *
 * El switch es transparente para use cases y store.
 * SRP: única responsabilidad → ensamblar el grafo de dependencias.
 */
class AppContainer {
  /** Servicio de scoring (domain service puro) */
  readonly scoringService: ScoringService;
  /** Servicio de moderación (domain service puro) */
  readonly moderationService: TopicModerationService;

  /** Repositorio — usa la interfaz, no la implementación concreta */
  readonly repository: ITopicRepository;
  /** Registry de fuentes externas */
  readonly sourceRegistry: SourceRegistry;

  /** Use case: descubrir topics desde fuentes externas */
  readonly discoverTopics: DiscoverTopics;
  /** Use case: aprobar topic */
  readonly approveTopic: ApproveTopic;
  /** Use case: rechazar topic */
  readonly rejectTopic: RejectTopic;
  /** Use case: crear topic manual */
  readonly createManualTopic: CreateManualTopic;
  /** Use case: listar topics con filtros */
  readonly listTopics: ListTopics;

  constructor() {
    // ── Leer env var para decidir modo ──
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;

    if (apiUrl) {
      // ── MODO API ──────────────────────────────────
      // Repositorio conectado al backend REST
      this.repository = new ApiTopicRepository(apiUrl);

      // Fuentes que consultan el backend via /api/v1/discover
      this.sourceRegistry = new SourceRegistry();
      this.sourceRegistry.register(new ApiTopicSource(apiUrl, "google-news"));
      this.sourceRegistry.register(new ApiTopicSource(apiUrl, "twitter"));
      this.sourceRegistry.register(new ApiTopicSource(apiUrl, "rss"));
    } else {
      // ── MODO MOCK ─────────────────────────────────
      // Repositorio en memoria con seed data
      this.repository = new TopicRepositoryImpl(createSeedTopics());

      // Fuentes mock
      this.sourceRegistry = new SourceRegistry();
      this.sourceRegistry.register(new MockTopicSource("google-news"));
      this.sourceRegistry.register(new MockTopicSource("twitter"));
      this.sourceRegistry.register(new MockTopicSource("rss"));
    }

    // Domain services (puros, sin dependencias)
    this.scoringService = new ScoringService();
    this.moderationService = new TopicModerationService();

    // Use cases (inyección de dependencias — idénticos en ambos modos)
    this.discoverTopics = new DiscoverTopics(
      this.repository,
      this.sourceRegistry,
      this.scoringService
    );
    this.approveTopic = new ApproveTopic(this.repository, this.moderationService);
    this.rejectTopic = new RejectTopic(this.repository, this.moderationService);
    this.createManualTopic = new CreateManualTopic(this.repository, this.scoringService);
    this.listTopics = new ListTopics(this.repository, this.scoringService);
  }
}

// Exportar instancia única (singleton)
export const container = new AppContainer();
