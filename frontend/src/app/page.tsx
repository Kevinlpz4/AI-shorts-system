"use client";

import { useState } from "react";
import { KPIGrid } from "@/components/dashboard/KPIGrid";
import { TopicList } from "@/components/dashboard/TopicList";
import { TopicDetailPanel } from "@/components/topic/TopicDetailPanel";
import { TopicData } from "@/types";

/** Página principal del dashboard con KPIs, lista de topics y panel de detalle */
export default function DashboardPage() {
  const [selectedTopic, setSelectedTopic] = useState<TopicData | null>(null);

  return (
    <div className="animate-fade-in">
      {/* Page header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-[10px] font-mono text-cyber-cyan/60 tracking-widest uppercase mb-1">
          <span className="w-2 h-2 rounded-full bg-cyber-cyan animate-glow-pulse" />
          <span>Control Room • Real-time Feed</span>
        </div>
        <h1 className="text-2xl font-display font-bold text-white tracking-wide">
          Topic Dashboard
        </h1>
      </div>

      {/* KPI Cards */}
      <KPIGrid />

      {/* Main content area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Topic list */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-display font-semibold text-white tracking-wide">
              Recent Topics
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono text-gray-500">
                Click a topic to inspect
              </span>
            </div>
          </div>
          <TopicList onTopicSelect={setSelectedTopic} />
        </div>

        {/* Detail panel */}
        <div className="lg:col-span-1">
          <div className="sticky top-24">
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
