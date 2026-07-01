"use client";

import { useScriptStudioStore } from "@/store/scriptStudioStore";
import { TopicQueueItem } from "./TopicQueueItem";
import { Inbox } from "lucide-react";

export function TopicQueue() {
  const { approvedTopics, selectedTopic, selectTopic } = useScriptStudioStore();

  if (approvedTopics.length === 0) {
    return (
      <div className="glass rounded-xl p-12 flex flex-col items-center justify-center h-full">
        <div className="relative p-4 rounded-2xl bg-glass-strong border border-glass-border mb-4">
          <Inbox size={28} className="text-gray-500" />
        </div>
        <p className="text-sm font-mono text-gray-500">Queue is empty</p>
        <p className="text-xs font-mono text-gray-600 mt-1">No approved topics available</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <p className="text-[10px] font-mono text-gray-400 uppercase tracking-[0.15em]">
          Topic Queue
        </p>
        <span className="px-2.5 py-0.5 text-[9px] font-mono glass rounded-full text-gray-400">
          {approvedTopics.length} topic{approvedTopics.length !== 1 ? "s" : ""}
        </span>
      </div>
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
