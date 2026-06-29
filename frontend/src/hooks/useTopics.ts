// ═══════════════════════════════════════════════════
// useTopics — Hook for consuming the topic store
// ═══════════════════════════════════════════════════
// Abstracción sobre el store para componentes.
// SRP: un hook, una responsabilidad (acceder a datos de topics).

import { useEffect, useCallback, useState } from "react";
import { useTopicStore } from "@/store/topicStore";
import { TopicFilters } from "@/types";

/**
 * Hook para acceder a la lista de topics con filtros.
 * Se re-ejecuta cuando cambian los filtros.
 */
export function useTopicList(filters?: Partial<TopicFilters>) {
  const {
    topics,
    isLoading,
    error,
    loadTopics,
    setFilters,
    filters: currentFilters,
  } = useTopicStore();

  useEffect(() => {
    if (filters) {
      setFilters(filters);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadTopics();
  }, [currentFilters, loadTopics]);

  return { topics, isLoading, error, refresh: loadTopics };
}

/**
 * Hook para acceder a un topic individual por ID.
 */
export function useTopicDetail(topicId: string) {
  const { selectedTopic, isLoading, error, loadTopicById } = useTopicStore();

  useEffect(() => {
    loadTopicById(topicId);
  }, [topicId, loadTopicById]);

  return { topic: selectedTopic, isLoading, error };
}

/**
 * Hook para las acciones de moderación (approve/reject).
 */
export function useTopicModeration() {
  const { approveTopic, rejectTopic, isLoading } = useTopicStore();

  const approve = useCallback(
    async (id: string) => {
      await approveTopic(id);
    },
    [approveTopic]
  );

  const reject = useCallback(
    async (id: string) => {
      await rejectTopic(id);
    },
    [rejectTopic]
  );

  return { approve, reject, isLoading };
}

/**
 * Hook para el descubrimiento automático (con estado de carga).
 */
export function useTopicDiscovery() {
  const { discoverTopics, isDiscovering } = useTopicStore();
  const [lastResult, setLastResult] = useState<{
    discovered: number;
    duplicates: number;
    errors: number;
  } | null>(null);

  const discover = useCallback(
    async (query?: string) => {
      const result = await discoverTopics(query);
      setLastResult({
        discovered: result.discovered.length,
        duplicates: result.duplicates.length,
        errors: result.errors.length,
      });
      return result;
    },
    [discoverTopics]
  );

  return { discover, isDiscovering, lastResult };
}
