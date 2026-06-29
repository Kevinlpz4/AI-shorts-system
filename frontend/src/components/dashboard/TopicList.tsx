"use client";

import { useEffect } from "react";
import { useTopicStore } from "@/store/topicStore";
import { TopicCard } from "@/components/dashboard/TopicCard";
import { TopicData } from "@/types";
import { Loader2, AlertCircle, Inbox } from "lucide-react";

/** Props del listado de topics */
interface TopicListProps {
  /** Callback al seleccionar un topic (si no se provee, navega a /topics/{id}) */
  onTopicSelect?: (topic: TopicData) => void;
}

/**
 * Lista de topics con loading, error y empty states.
 * Se suscribe al store de Zustand y recarga al montarse.
 */
export function TopicList({ onTopicSelect }: TopicListProps) {
  const { topics, isLoading, error, loadTopics } = useTopicStore();

  useEffect(() => {
    loadTopics();
  }, [loadTopics]);

  if (isLoading && topics.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-500">
        <Loader2 size={32} className="animate-spin text-cyber-cyan mb-4" />
        <p className="text-sm font-mono">Loading topics...</p>
      </div>
    );
  }

  if (error && topics.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertCircle size={32} className="text-cyber-red mb-4" />
        <p className="text-sm font-mono text-cyber-red mb-2">Error loading topics</p>
        <p className="text-xs font-mono text-gray-500">{error}</p>
        <button
          onClick={loadTopics}
          className="mt-4 px-4 py-2 bg-glass-white border border-glass-border rounded-lg text-xs font-mono text-gray-300 hover:text-white transition-all"
        >
          Retry
        </button>
      </div>
    );
  }

  if (topics.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-500">
        <Inbox size={32} className="mb-4" />
        <p className="text-sm font-mono">No topics found</p>
        <p className="text-xs font-mono text-gray-600 mt-1">
          Try discovering new topics or create one manually
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs font-mono text-gray-500">
          Showing {topics.length} topic{topics.length !== 1 ? "s" : ""}
        </p>
        <button
          onClick={loadTopics}
          className="text-[11px] font-mono text-cyber-cyan/60 hover:text-cyber-cyan transition-colors"
        >
          Refresh
        </button>
      </div>
      {topics.map((topic) => (
        <TopicCard
          key={topic.id}
          topic={topic}
          onSelect={onTopicSelect}
        />
      ))}
    </div>
  );
}
