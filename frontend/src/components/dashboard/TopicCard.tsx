"use client";

import { TopicData, TopicStatus } from "@/types";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ExternalLink, Clock, User } from "lucide-react";
import { timeAgo } from "@/lib/utils";

interface TopicCardProps {
  topic: TopicData;
  onSelect?: (topic: TopicData) => void;
  index?: number;
}

export function TopicCard({ topic, onSelect, index = 0 }: TopicCardProps) {
  const router = useRouter();

  const handleClick = () => {
    if (onSelect) {
      onSelect(topic);
    } else {
      router.push(`/topics/${topic.id}`);
    }
  };

  const scoreColor =
    topic.scoreTotal >= 80
      ? "text-neon-green"
      : topic.scoreTotal >= 60
        ? "text-neon-yellow"
        : "text-neon-red";

  const scoreBg =
    topic.scoreTotal >= 80
      ? "from-neon-green/20 to-emerald-900/20"
      : topic.scoreTotal >= 60
        ? "from-neon-yellow/20 to-amber-900/20"
        : "from-neon-red/20 to-rose-900/20";

  const scoreBorder =
    topic.scoreTotal >= 80
      ? "border-neon-green/30"
      : topic.scoreTotal >= 60
        ? "border-neon-yellow/30"
        : "border-neon-red/30";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, type: "spring", stiffness: 100, damping: 20 }}
    >
      <Card glow="violet" hoverable onClick={handleClick} className="p-4">
        <div className="flex items-start justify-between gap-4">
          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <StatusBadge status={topic.status as TopicStatus} />
              <span className="text-[9px] font-mono text-gray-500 uppercase tracking-wider">
                {topic.sourceName}
              </span>
            </div>

            <h3 className="text-sm font-semibold text-white leading-snug mb-1.5 line-clamp-2 font-display">
              {topic.title}
            </h3>

            <p className="text-xs text-gray-400 line-clamp-2 mb-3 font-sans leading-relaxed">
              {topic.description}
            </p>

            {/* Meta */}
            <div className="flex items-center gap-3 text-[10px] font-mono text-gray-500">
              <span className="flex items-center gap-1.5">
                <Clock size={12} className="text-gray-600" />
                {timeAgo(topic.createdAt)}
              </span>
              {topic.author && (
                <span className="flex items-center gap-1.5">
                  <User size={12} className="text-gray-600" />
                  {topic.author}
                </span>
              )}
              {topic.url && (
                <span className="flex items-center gap-1.5 text-neon-cyan/50">
                  <ExternalLink size={12} />
                  Source
                </span>
              )}
            </div>
          </div>

          {/* Score gauge — glass style */}
          <div className="flex flex-col items-center gap-1.5 shrink-0">
            <div
              className={`relative w-14 h-14 rounded-full flex items-center justify-center bg-gradient-to-br ${scoreBg} border ${scoreBorder}`}
            >
              {/* Score ring */}
              <svg className="absolute inset-0 w-full h-full -rotate-90">
                <circle
                  cx="28"
                  cy="28"
                  r="25"
                  fill="none"
                  stroke="rgba(255,255,255,0.05)"
                  strokeWidth="2"
                />
                <motion.circle
                  cx="28"
                  cy="28"
                  r="25"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeDasharray={`${topic.scoreTotal * 2.51} 251`}
                  className={scoreColor}
                  initial={{ strokeDasharray: "0 251" }}
                  animate={{
                    strokeDasharray: `${topic.scoreTotal * 2.51} 251`,
                  }}
                  transition={{ duration: 1, ease: "easeOut" }}
                />
              </svg>
              <span className={`relative text-sm font-display font-bold ${scoreColor}`}>
                {topic.scoreTotal.toFixed(1)}
              </span>
            </div>
            <span className="text-[8px] font-mono text-gray-500 uppercase tracking-[0.15em]">
              Score
            </span>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
