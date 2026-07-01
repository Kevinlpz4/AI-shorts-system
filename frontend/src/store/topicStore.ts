// ═══════════════════════════════════════════════════
// topicStore — Zustand global state
// ═══════════════════════════════════════════════════
// Estado global de topics. Desacoplado del dominio:
// almacena DTOs planos, no entidades del dominio.

import { create } from "zustand";
import { TopicData, TopicFilters, KPIStats, BatchDiscoverResult, ScriptData } from "@/types";
import { TopicStatusValue } from "@/domain/value-objects/TopicStatus";
import { container } from "@/infrastructure/Container";
import { getApiBase, mapScriptFromApi } from "@/lib/utils";

/** Estado global de topics vía Zustand */
interface TopicState {
  // ── Data ──
  topics: TopicData[];
  selectedTopic: TopicData | null;
  filters: TopicFilters;
  kpiStats: KPIStats;
  isLoading: boolean;
  isDiscovering: boolean;
  error: string | null;

  // ── Script data ──
  script: ScriptData | null;
  scriptLoading: boolean;
  scriptError: string | null;

  // ── Acciones ──
  loadTopics: () => Promise<void>;
  loadTopicById: (id: string) => Promise<void>;
  approveTopic: (id: string) => Promise<void>;
  rejectTopic: (id: string) => Promise<void>;
  createManualTopic: (input: {
    title: string;
    description: string;
    url: string | null;
  }) => Promise<{ success: boolean; isDuplicate: boolean }>;
  discoverTopics: (query?: string) => Promise<BatchDiscoverResult>;
  setFilters: (filters: Partial<TopicFilters>) => void;
  clearSelection: () => void;
  clearError: () => void;

  // ── Script acciones ──
  loadScript: (topicId: string) => Promise<void>;
  generateScript: (topicId: string, duration?: number, tone?: string) => Promise<void>;
  regenerateScript: (topicId: string, duration?: number, tone?: string) => Promise<void>;
  clearScript: () => void;
}

const DEFAULT_FILTERS: TopicFilters = {
  status: null,
  sourceName: null,
  minScore: 0,
  maxScore: 10,
  query: "",
};

// ── Helpers ──



/** Genera un script mock para desarrollo sin backend */
function createMockScript(topicId: string): ScriptData {
  return {
    id: `mock-script-${topicId}`,
    topicId,
    hook: "🤯 ¿Sabías que la IA ya puede hacer esto?",
    body:
      "La inteligencia artificial está revolucionando la forma en que interactuamos con la tecnología. " +
      "Desde asistentes virtuales hasta generación de contenido, las posibilidades son infinitas. " +
      "En este video te muestro 5 casos reales que te van a dejar con la boca abierta.\n\n" +
      "Primero, la IA en la educación está personalizando el aprendizaje como nunca antes. " +
      "Segundo, en la medicina, los algoritmos están detectando enfermedades con precisión sobrehumana. " +
      "Tercero, la creación de contenido nunca fue tan accesible.\n\n" +
      "¿Estás listo para el futuro? Porque el futuro ya llegó.",
    cta: "🔥 Dale like y suscribite para más contenido sobre IA y tecnología.",
    duration: 60,
    tone: "informative",
    format: "youtube-shorts",
    wordCount: 148,
    isValid: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

export const useTopicStore = create<TopicState>((set, get) => ({
  // ── Estado inicial ──
  topics: [],
  selectedTopic: null,
  filters: DEFAULT_FILTERS,
  kpiStats: { discovered: 0, pendingReview: 0, approved: 0, rejected: 0 },
  isLoading: false,
  isDiscovering: false,
  error: null,
  script: null,
  scriptLoading: false,
  scriptError: null,

  // ── Cargar topics ──
  /**
   * Carga la lista de topics desde el repositorio aplicando filtros actuales.
   * También actualiza los KPI stats.
   */
  loadTopics: async () => {
    set({ isLoading: true, error: null });
    try {
      const { listTopics, repository } = container;

      // Aplicar filtros
      const filters = get().filters;
      const domainTopics = await listTopics.execute({
        status: filters.status as TopicStatusValue | undefined,
        sourceName: filters.sourceName || undefined,
        minScore: filters.minScore > 0 ? filters.minScore : undefined,
        searchQuery: filters.query || undefined,
      });

      const topics = domainTopics.map((t) => t.toPlain());
      const kpiStats = await repository.getKPIStats();

      set({ topics, kpiStats, isLoading: false });
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : "Failed to load topics",
      });
    }
  },

  // ── Cargar un topic ──
  /**
   * Carga un topic individual por ID y lo establece como seleccionado.
   * @param id - ID del topic a cargar
   */
  loadTopicById: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const topic = await container.repository.findById(id);
      set({
        selectedTopic: topic?.toPlain() || null,
        isLoading: false,
      });
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : "Topic not found",
      });
    }
  },

  // ── Aprobar topic ──
  /**
   * Aprueba un topic, actualiza la lista y recarga KPI stats.
   * @param id - ID del topic a aprobar
   */
  approveTopic: async (id: string) => {
    set({ error: null });
    try {
      const updated = await container.approveTopic.execute(id);
      set((state) => ({
        topics: state.topics.map((t) =>
          t.id === id ? updated.toPlain() : t
        ),
        selectedTopic:
          state.selectedTopic?.id === id ? updated.toPlain() : state.selectedTopic,
      }));
      // Recargar stats
      const kpiStats = await container.repository.getKPIStats();
      set({ kpiStats });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Failed to approve" });
    }
  },

  // ── Rechazar topic ──
  /**
   * Rechaza un topic, actualiza la lista y recarga KPI stats.
   * @param id - ID del topic a rechazar
   */
  rejectTopic: async (id: string) => {
    set({ error: null });
    try {
      const updated = await container.rejectTopic.execute(id);
      set((state) => ({
        topics: state.topics.map((t) =>
          t.id === id ? updated.toPlain() : t
        ),
        selectedTopic:
          state.selectedTopic?.id === id ? updated.toPlain() : state.selectedTopic,
      }));
      const kpiStats = await container.repository.getKPIStats();
      set({ kpiStats });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Failed to reject" });
    }
  },

  // ── Crear topic manual ──
  /**
   * Crea un topic manualmente desde el formulario.
   * @returns Resultado con flag isDuplicate si ya existe
   */
  createManualTopic: async (input) => {
    set({ isLoading: true, error: null });
    try {
      const result = await container.createManualTopic.execute(input);
      if (!result.isDuplicate) {
        const topics = get().topics;
        set({ topics: [result.topic.toPlain(), ...topics] });
        const kpiStats = await container.repository.getKPIStats();
        set({ kpiStats });
      }
      set({ isLoading: false });
      return { success: true, isDuplicate: result.isDuplicate };
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : "Failed to create topic",
      });
      return { success: false, isDuplicate: false };
    }
  },

  // ── Descubrir topics ──
  /**
   * Ejecuta descubrimiento automático desde fuentes externas.
   * @param query - Término de búsqueda opcional
   * @returns Resultado con topics descubiertos, duplicados y errores
   */
  discoverTopics: async (query?: string) => {
    set({ isDiscovering: true, error: null });
    try {
      const result = await container.discoverTopics.execute({
        query,
        limit: 5,
      });

      // Recargar lista completa
      await get().loadTopics();

      set({ isDiscovering: false });

      return {
        discovered: result.discovered.map((t) => t.toPlain()),
        duplicates: result.duplicates.map((t) => t.toPlain()),
        errors: result.errors,
      };
    } catch (err) {
      set({
        isDiscovering: false,
        error: err instanceof Error ? err.message : "Discovery failed",
      });
      return { discovered: [], duplicates: [], errors: [] };
    }
  },

  // ── Filtros ──
  /** Actualiza parcialmente los filtros activos */
  setFilters: (filters) => {
    set((state) => ({
      filters: { ...state.filters, ...filters },
    }));
  },

  /** Limpia la selección actual */
  clearSelection: () => set({ selectedTopic: null }),
  /** Limpia el mensaje de error actual */
  clearError: () => set({ error: null }),

  // ── Script actions ──
  /** Carga un script existente para un topic. En modo mock simula delay. */
  loadScript: async (topicId: string) => {
    set({ scriptLoading: true, scriptError: null });
    try {
      const apiBase = getApiBase();

      if (!apiBase) {
        // Mock mode: simulate delay and return mock data
        await new Promise((r) => setTimeout(r, 600));
        set({ script: createMockScript(topicId), scriptLoading: false });
        return;
      }

      const res = await fetch(`${apiBase}/api/v1/topics/${topicId}/script`);
      if (!res.ok) {
        if (res.status === 404) {
          set({ script: null, scriptLoading: false });
          return;
        }
        throw new Error(`API error: ${res.status} ${res.statusText}`);
      }
      const data = await res.json();
      set({ script: mapScriptFromApi(data), scriptLoading: false });
    } catch (err) {
      set({
        scriptLoading: false,
        script: null,
        scriptError: err instanceof Error ? err.message : "Failed to load script",
      });
    }
  },

  /** Genera un script nuevo para un topic con duración y tono opcionales */
  generateScript: async (topicId: string, duration?: number, tone?: string) => {
    set({ scriptLoading: true, scriptError: null });
    try {
      const apiBase = getApiBase();

      if (!apiBase) {
        await new Promise((r) => setTimeout(r, 800));
        set({ script: createMockScript(topicId), scriptLoading: false });
        return;
      }

      const body: Record<string, unknown> = {};
      if (duration) body.duration = duration;
      if (tone) body.tone = tone;

      const res = await fetch(
        `${apiBase}/api/v1/topics/${topicId}/script/generate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: Object.keys(body).length > 0 ? JSON.stringify(body) : undefined,
        }
      );

      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(
          errData?.detail || `API error: ${res.status} ${res.statusText}`
        );
      }

      const data = await res.json();
      set({ script: mapScriptFromApi(data), scriptLoading: false });
    } catch (err) {
      set({
        scriptLoading: false,
        script: null,
        scriptError: err instanceof Error ? err.message : "Failed to generate script",
      });
    }
  },

  /** Regenera un script existente (reemplaza el anterior) */
  regenerateScript: async (topicId: string, duration?: number, tone?: string) => {
    set({ scriptLoading: true, scriptError: null });
    try {
      const apiBase = getApiBase();

      if (!apiBase) {
        await new Promise((r) => setTimeout(r, 800));
        set({ script: createMockScript(topicId), scriptLoading: false });
        return;
      }

      const body: Record<string, unknown> = {};
      if (duration) body.duration = duration;
      if (tone) body.tone = tone;

      const res = await fetch(
        `${apiBase}/api/v1/topics/${topicId}/script/regenerate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: Object.keys(body).length > 0 ? JSON.stringify(body) : undefined,
        }
      );

      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(
          errData?.detail || `API error: ${res.status} ${res.statusText}`
        );
      }

      const data = await res.json();
      set({ script: mapScriptFromApi(data), scriptLoading: false });
    } catch (err) {
      set({
        scriptLoading: false,
        script: null,
        scriptError: err instanceof Error ? err.message : "Failed to regenerate script",
      });
    }
  },

  /** Limpia el script cargado y sus errores */
  clearScript: () => set({ script: null, scriptError: null, scriptLoading: false }),
}));
