"use client";

import clsx from "clsx";
import { ScriptWithTopic } from "@/types";
import { motion } from "framer-motion";
import { Clock, Music, CheckCircle, AlertTriangle } from "lucide-react";

interface ScriptListItemProps {
  script: ScriptWithTopic;
  isSelected: boolean;
  onSelect: () => void;
}

export function ScriptListItem({ script, isSelected, onSelect }: ScriptListItemProps) {
  return (
    <motion.button
      onClick={onSelect}
      whileHover={{ scale: 1.005 }}
      whileTap={{ scale: 0.995 }}
      className={clsx(
        "w-full text-left p-4 rounded-xl border transition-all duration-300 relative overflow-hidden",
        isSelected
          ? "glass-glow-cyan"
          : "glass hover:bg-glass-light",
      )}
    >
      {/* Glass shine */}
      <span className="absolute inset-0 bg-glass-shine pointer-events-none" />

      <div className="relative">
        {/* Title + status */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <h3 className="text-sm font-semibold text-white leading-snug line-clamp-1 font-display">
            {script.topic_title}
          </h3>
          {script.isValid ? (
            <CheckCircle size={14} className="text-neon-green shrink-0 mt-0.5" />
          ) : (
            <AlertTriangle size={14} className="text-neon-yellow shrink-0 mt-0.5" />
          )}
        </div>

        {/* Hook preview */}
        <p className="text-xs text-gray-400 font-sans leading-relaxed line-clamp-2 mb-3">
          {script.hook}
        </p>

        {/* Metadata row */}
        <div className="flex items-center gap-3 text-[10px] font-mono text-gray-500">
          <span className="flex items-center gap-1">
            <Clock size={10} />
            {script.duration}s
          </span>
          <span className="flex items-center gap-1">
            <Music size={10} />
            {script.tone}
          </span>
          <span
            className={clsx(
              "px-1.5 py-0.5 rounded text-[9px] font-mono",
              script.topic_score >= 8
                ? "bg-neon-green/10 text-neon-green"
                : script.topic_score >= 6
                  ? "bg-neon-yellow/10 text-neon-yellow"
                  : "bg-neon-red/10 text-neon-red",
            )}
          >
            Score: {script.topic_score}
          </span>
          <span className="ml-auto text-gray-600">
            {new Date(script.createdAt).toLocaleDateString()}
          </span>
        </div>
      </div>
    </motion.button>
  );
}
