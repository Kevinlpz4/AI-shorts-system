"use client";

import { useScriptStudioStore } from "@/store/scriptStudioStore";
import { TopicQueueItem } from "./TopicQueueItem";
import { Inbox } from "lucide-react";

/**
 * Left panel — Queue of approved topics waiting for script generation.
 *
 * Shows a count badge and renders a scrollable list of TopicQueueItems.
 */
export function TopicQueue() {
  const { approvedTopics, selectedTopic, selectTopic } = useScriptStudioStore();

  if (approvedTopics.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <Inbox size={32} className="mb-3 opacity-50" />
        <p className="text-sm font-mono">Queue is empty</p>
        <p className="text-xs font-mono text-gray-600 mt-1">
          No approved topics available
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-mono text-gray-400 uppercase tracking-wider">
          Topic Queue
        </p>
        <span className="px-2 py-0.5 text-[10px] font-mono border border-glass-border rounded-full text-gray-400 bg-glass-white">
          {approvedTopics.length} topic{approvedTopics.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Scrollable list */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {approvedTopics.map((topic) => (
          <TopicQueueItem
            key={topic.id}
            topic={topic}
            isSelected={selectedTopic?.id === topic.id}
            onSelect={() => selectTopic(topic)}
          />
        ))}
      </div>
    </div>
  );
}
