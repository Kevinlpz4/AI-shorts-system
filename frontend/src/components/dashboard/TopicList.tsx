"use client";

import { useEffect } from "react";
import { useTopicStore } from "@/store/topicStore";
import { TopicCard } from "@/components/dashboard/TopicCard";
import { TopicData } from "@/types";
import { motion } from "framer-motion";
import { AlertCircle, Inbox } from "lucide-react";

interface TopicListProps {
  onTopicSelect?: (topic: TopicData) => void;
}

export function TopicList({ onTopicSelect }: TopicListProps) {
  const { topics, isLoading, error, loadTopics } = useTopicStore();

  useEffect(() => {
    loadTopics();
  }, [loadTopics]);

  // ── Loading ──
  if (isLoading && topics.length === 0) {
    return (
      <div className="glass rounded-xl p-12">
        <div className="flex flex-col items-center justify-center gap-4">
          {/* Skeleton cards */}
          <div className="w-full space-y-3">
            {[1, 2, 3].map((i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.1 }}
                className="glass rounded-xl p-4"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-3">
                    <div className="flex gap-2">
                      <div className="h-5 w-24 rounded-full bg-glass-strong animate-pulse" />
                      <div className="h-5 w-16 rounded-full bg-glass-strong animate-pulse" />
                    </div>
                    <div className="h-4 w-3/4 rounded-lg bg-glass-strong animate-pulse" />
                    <div className="h-3 w-1/2 rounded-lg bg-glass-strong animate-pulse" />
                  </div>
                  <div className="w-14 h-14 rounded-full bg-glass-strong animate-pulse" />
                </div>
              </motion.div>
            ))}
          </div>
          <div className="flex items-center gap-2 text-sm font-mono text-gray-500 mt-2">
            <span className="w-4 h-4 border-2 border-neon-cyan/30 border-t-transparent rounded-full animate-spin" />
            Loading topics...
          </div>
        </div>
      </div>
    );
  }

  // ── Error ──
  if (error && topics.length === 0) {
    return (
      <div className="glass rounded-xl p-12">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center justify-center"
        >
          <div className="relative p-4 rounded-2xl bg-neon-red/10 border border-neon-red/20 mb-4">
            <AlertCircle size={28} className="text-neon-red" />
          </div>
          <p className="text-sm font-mono text-neon-red mb-1">Error loading topics</p>
          <p className="text-xs font-mono text-gray-500 mb-6">{error}</p>
          <motion.button
            onClick={loadTopics}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            className="px-5 py-2.5 glass rounded-xl text-xs font-mono text-gray-300 hover:text-white transition-all duration-300"
          >
            Retry
          </motion.button>
        </motion.div>
      </div>
    );
  }

  // ── Empty ──
  if (topics.length === 0) {
    return (
      <div className="glass rounded-xl p-12">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center justify-center"
        >
          <div className="relative p-4 rounded-2xl bg-glass-strong border border-glass-border mb-4">
            <Inbox size={28} className="text-gray-500" />
          </div>
          <p className="text-sm font-mono text-gray-400">No topics found</p>
          <p className="text-xs font-mono text-gray-600 mt-1.5">
            Try discovering new topics from the Discover page
          </p>
        </motion.div>
      </div>
    );
  }

  // ── Topics ──
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-3">
        <p className="text-[11px] font-mono text-gray-500">
          {topics.length} topic{topics.length !== 1 ? "s" : ""}
        </p>
        <motion.button
          onClick={loadTopics}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          className="text-[10px] font-mono text-neon-cyan/50 hover:text-neon-cyan transition-all duration-300"
        >
          Refresh
        </motion.button>
      </div>
      {topics.map((topic, i) => (
        <TopicCard
          key={topic.id}
          topic={topic}
          onSelect={onTopicSelect}
          index={i}
        />
      ))}
    </div>
  );
}
