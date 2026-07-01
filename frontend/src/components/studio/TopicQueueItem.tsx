"use client";

import clsx from "clsx";
import { TopicData } from "@/types";
import { Clock, User, ExternalLink } from "lucide-react";
import { timeAgo } from "@/lib/utils";

/** Props for an individual topic card in the queue */
interface TopicQueueItemProps {
  /** Topic data to render */
  topic: TopicData;
  /** Whether this topic is currently selected */
  isSelected: boolean;
  /** Callback when the card is clicked */
  onSelect: () => void;
}

/**
 * Individual topic card in the queue panel.
 *
 * Shows title (truncated), source badge, score with color coding,
 * and metadata. Highlights with a left border when selected.
 */
export function TopicQueueItem({
  topic,
  isSelected,
  onSelect,
}: TopicQueueItemProps) {

  // Score color: green ≥80, yellow ≥60, red <60
  const scoreColor =
    topic.scoreTotal >= 80
      ? "text-cyber-green"
      : topic.scoreTotal >= 60
        ? "text-cyber-yellow"
        : "text-cyber-red";

  const scoreBg =
    topic.scoreTotal >= 8
      ? "bg-cyber-green/10 border-cyber-green/30"
      : topic.scoreTotal >= 6
        ? "bg-cyber-yellow/10 border-cyber-yellow/30"
        : "bg-cyber-red/10 border-cyber-red/30";

  return (
    <button
      onClick={onSelect}
      className={clsx(
        "w-full text-left p-3 rounded-lg border transition-all duration-200",
        "hover:bg-glass-light",
        isSelected
          ? "border-l-4 border-l-cyber-cyan border-glass-border bg-cyber-cyan/5"
          : "border-glass-border bg-glass-white",
      )}
    >
      {/* Source badge */}
      <div className="flex items-center gap-2 mb-1.5">
        <span className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">
          {topic.sourceName}
        </span>
      </div>

      {/* Title — truncated */}
      <h3 className="text-sm font-semibold text-white leading-snug mb-2 line-clamp-2">
        {topic.title}
      </h3>

      {/* Meta row */}
      <div className="flex items-center gap-3 text-[10px] font-mono text-gray-500">
        {/* Score badge */}
        <span
          className={clsx(
            "inline-flex items-center gap-1 px-1.5 py-0.5 rounded border text-[10px] font-mono font-medium",
            scoreColor,
            scoreBg,
          )}
        >
          {topic.scoreTotal} pts
        </span>

        {/* Time */}
        <span className="flex items-center gap-1">
          <Clock size={11} />
          {timeAgo(topic.createdAt)}
        </span>

        {/* Author if present */}
        {topic.author && (
          <span className="flex items-center gap-1">
            <User size={11} />
            {topic.author}
          </span>
        )}

        {/* External link indicator */}
        {topic.url && (
          <span className="flex items-center gap-1 text-cyber-cyan/60">
            <ExternalLink size={11} />
          </span>
        )}
      </div>
    </button>
  );
}
