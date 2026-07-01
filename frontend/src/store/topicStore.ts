// ═══════════════════════════════════════════════════
// topicStore — Zustand global state
// ═══════════════════════════════════════════════════
// Estado global de topics. Almacena TopicData (plain objects),
// sin entidades de dominio.

import { create } from "zustand";
import { TopicData, TopicFilters, KPIStats, BatchDiscoverResult } from "@/types";
import { container } from "@/infrastructure/Container";
import { TopicStatusValue } from "@/types";

/** Estado global de topics vía Zustand */
interface TopicState {
  topics: TopicData[];
  selectedTopic: TopicData | null;
  filters: TopicFilters;
  kpiStats: KPIStats;
  isLoading: boolean;
  isDiscovering: boolean;
  error: string | null;

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
}

const DEFAULT_FILTERS: TopicFilters = {
  status: null,
  sourceName: null,
  minScore: 0,
  maxScore: 100,
  query: "",
};

export const useTopicStore = create<TopicState>((set, get) => ({
  topics: [],
  selectedTopic: null,
  filters: DEFAULT_FILTERS,
  kpiStats: { discovered: 0, pendingReview: 0, approved: 0, rejected: 0 },
  isLoading: false,
  isDiscovering: false,
  error: null,

  // ── Cargar topics ──
  loadTopics: async () => {
    set({ isLoading: true, error: null });
    try {
      const { listTopics, repository } = container;
      const filters = get().filters;
      const topics = await listTopics.execute({
        status: filters.status as TopicStatusValue | undefined,
        sourceName: filters.sourceName || undefined,
        minScore: filters.minScore > 0 ? filters.minScore : undefined,
        searchQuery: filters.query || undefined,
      });
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
  loadTopicById: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const topic = await container.repository.findById(id);
      set({ selectedTopic: topic, isLoading: false });
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : "Topic not found",
      });
    }
  },

  // ── Aprobar topic ──
  approveTopic: async (id: string) => {
    set({ error: null });
    try {
      const updated = await container.approveTopic.execute(id);
      set((state) => ({
        topics: state.topics.map((t) => (t.id === id ? updated : t)),
        selectedTopic: state.selectedTopic?.id === id ? updated : state.selectedTopic,
      }));
      const kpiStats = await container.repository.getKPIStats();
      set({ kpiStats });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Failed to approve" });
    }
  },

  // ── Rechazar topic ──
  rejectTopic: async (id: string) => {
    set({ error: null });
    try {
      const updated = await container.rejectTopic.execute(id);
      set((state) => ({
        topics: state.topics.map((t) => (t.id === id ? updated : t)),
        selectedTopic: state.selectedTopic?.id === id ? updated : state.selectedTopic,
      }));
      const kpiStats = await container.repository.getKPIStats();
      set({ kpiStats });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Failed to reject" });
    }
  },

  // ── Crear topic manual ──
  createManualTopic: async (input) => {
    set({ isLoading: true, error: null });
    try {
      const result = await container.createManualTopic.execute(input);
      if (!result.isDuplicate) {
        const topics = get().topics;
        set({ topics: [result.topic, ...topics] });
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
  discoverTopics: async (query?: string) => {
    set({ isDiscovering: true, error: null });
    try {
      const result = await container.discoverTopics.execute({ query, limit: 5 });
      await get().loadTopics();
      set({ isDiscovering: false });
      return {
        discovered: result.discovered,
        duplicates: result.duplicates,
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
  setFilters: (filters) => {
    set((state) => ({ filters: { ...state.filters, ...filters } }));
  },

  clearSelection: () => set({ selectedTopic: null }),
  clearError: () => set({ error: null }),
}));
