"use client";

import { TopicList } from "@/components/dashboard/TopicList";
import { TopicDetailPanel } from "@/components/topic/TopicDetailPanel";
import { TopicData } from "@/types";
import { useState } from "react";

/** Página de listado completo de topics con panel de detalle lateral */
export default function TopicsPage() {
  const [selectedTopic, setSelectedTopic] = useState<TopicData | null>(null);

  return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-2 text-[10px] font-mono text-cyber-cyan/60 tracking-widest uppercase mb-1">
        <span className="w-2 h-2 rounded-full bg-cyber-cyan animate-glow-pulse" />
        <span>Topic Management</span>
      </div>
      <h1 className="text-2xl font-display font-bold text-white tracking-wide mb-6">
        All Topics
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <TopicList onTopicSelect={setSelectedTopic} />
        </div>
        <div className="lg:col-span-1">
          <div className="sticky top-24 space-y-4">
            <TopicDetailPanel
              topicId={selectedTopic?.id}
              onClose={() => setSelectedTopic(null)}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
