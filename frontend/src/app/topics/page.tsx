"use client";

import { TopicList } from "@/components/dashboard/TopicList";
import { TopicDetailPanel } from "@/components/topic/TopicDetailPanel";
import { TopicData } from "@/types";
import { useState } from "react";
import { motion } from "framer-motion";
import { FileText } from "lucide-react";

export default function TopicsPage() {
  const [selectedTopic, setSelectedTopic] = useState<TopicData | null>(null);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 text-[10px] font-mono text-neon-cyan/50 tracking-[0.2em] uppercase mb-2">
          <FileText size={12} className="text-neon-cyan" />
          <span>Topic Management</span>
        </div>
        <h1 className="text-2xl font-display font-bold text-white tracking-wide">
          All Topics
        </h1>
        <p className="text-sm font-sans text-gray-400 mt-1 font-light">
          Browse, review, and manage discovered topics
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <TopicList onTopicSelect={setSelectedTopic} />
        </div>
        <div className="lg:col-span-1">
          <div className="sticky top-24 space-y-4">
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
