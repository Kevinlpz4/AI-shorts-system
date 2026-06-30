"use client";

import clsx from "clsx";
import { ScriptWithTopic } from "@/types";
import { Clock, Music, CheckCircle, AlertTriangle } from "lucide-react";

interface ScriptListItemProps {
  script: ScriptWithTopic;
  isSelected: boolean;
  onSelect: () => void;
}

export function ScriptListItem({ script, isSelected, onSelect }: ScriptListItemProps) {
  return (
    <button
      onClick={onSelect}
      className={clsx(
        "w-full text-left p-4 rounded-lg border transition-all duration-200",
        "hover:bg-glass-white",
        isSelected
          ? "bg-cyber-cyan/10 border-cyber-cyan/30 border-l-4 border-l-cyber-cyan"
          : "bg-glass-white border-glass-border",
      )}
    >
      {/* Title + status */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="text-sm font-semibold text-white leading-snug line-clamp-1">
          {script.topic_title}
        </h3>
        {script.isValid ? (
          <CheckCircle size={14} className="text-cyber-green shrink-0 mt-0.5" />
        ) : (
          <AlertTriangle size={14} className="text-cyber-yellow shrink-0 mt-0.5" />
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
        <span className="flex items-center gap-1">
          <span
            className={clsx(
              "px-1.5 py-0.5 rounded",
              script.topic_score >= 80
                ? "bg-cyber-green/10 text-cyber-green"
                : script.topic_score >= 60
                  ? "bg-cyber-yellow/10 text-cyber-yellow"
                  : "bg-cyber-red/10 text-cyber-red",
            )}
          >
            Score: {script.topic_score}
          </span>
        </span>
        <span className="ml-auto text-gray-600">
          {new Date(script.createdAt).toLocaleDateString()}
        </span>
      </div>
    </button>
  );
}
