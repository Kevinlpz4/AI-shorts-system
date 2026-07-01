"use client";

import { useState, useEffect } from "react";
import { KPIGrid } from "@/components/dashboard/KPIGrid";
import { TopicList } from "@/components/dashboard/TopicList";
import { TopicDetailPanel } from "@/components/topic/TopicDetailPanel";
import { TopicData } from "@/types";
import { useTopicStore } from "@/store/topicStore";
import { motion } from "framer-motion";

export default function DashboardPage() {
  const [selectedTopic, setSelectedTopic] = useState<TopicData | null>(null);
  const loadTopics = useTopicStore((s) => s.loadTopics);

  useEffect(() => {
    loadTopics();
  }, [loadTopics]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* Page header — populated via layout portal */}
      <div className="mb-8">
        <div className="flex items-center gap-2 text-[10px] font-mono text-neon-cyan/50 tracking-[0.2em] uppercase mb-2">
          <span className="w-1.5 h-1.5 rounded-full bg-neon-cyan animate-glow-pulse" />
          <span>Control Room</span>
        </div>
        <h1 className="text-2xl font-display font-bold text-white tracking-wide">
          Topic Dashboard
        </h1>
        <p className="text-sm font-sans text-gray-400 mt-1 font-light">
          Real-time topic monitoring and discovery feed
        </p>
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
            <span className="text-[10px] font-mono text-gray-500">
              Click to inspect
            </span>
          </div>
          <TopicList onTopicSelect={setSelectedTopic} />
        </div>

        {/* Detail panel */}
        <div className="lg:col-span-1">
          <div className="sticky top-24">
            <motion.div
              key={selectedTopic?.id || "empty"}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ type: "spring", stiffness: 100, damping: 20 }}
            >
              <TopicDetailPanel
                topicId={selectedTopic?.id}
                onClose={() => setSelectedTopic(null)}
              />
            </motion.div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
