"use client";

import { TopicData, TopicStatus } from "@/types";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useRouter } from "next/navigation";
import { ExternalLink, Clock, User } from "lucide-react";

/** Props de la card que muestra un topic resumido */
interface TopicCardProps {
  /** Datos del topic a renderizar */
  topic: TopicData;
  /** Callback al hacer click (default: navega a /topics/{id}) */
  onSelect?: (topic: TopicData) => void;
}

/**
 * Card resumen de un topic con score gauge circular.
 * Hoverable: escala al pasar el mouse.
 */
export function TopicCard({ topic, onSelect }: TopicCardProps) {
  const router = useRouter();

  const handleClick = () => {
    if (onSelect) {
      onSelect(topic);
    } else {
      router.push(`/topics/${topic.id}`);
    }
  };

  const timeAgo = (dateStr: string): string => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    if (hours < 1) return "Just now";
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  return (
    <Card
      glow="purple"
      hoverable
      onClick={handleClick}
      className="p-4 animate-slide-up"
    >
      <div className="flex items-start justify-between gap-4">
        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5">
            <StatusBadge status={topic.status as TopicStatus} />
            <span className="text-[10px] font-mono text-gray-500 uppercase">
              {topic.sourceName}
            </span>
          </div>

          <h3 className="text-sm font-semibold text-white leading-snug mb-1.5 line-clamp-2">
            {topic.title}
          </h3>

          <p className="text-xs text-gray-400 line-clamp-2 mb-3 font-sans leading-relaxed">
            {topic.description}
          </p>

          {/* Meta */}
          <div className="flex items-center gap-3 text-[10px] font-mono text-gray-500">
            <span className="flex items-center gap-1">
              <Clock size={12} />
              {timeAgo(topic.createdAt)}
            </span>
            {topic.author && (
              <span className="flex items-center gap-1">
                <User size={12} />
                {topic.author}
              </span>
            )}
            {topic.url && (
              <span className="flex items-center gap-1 text-cyber-cyan/60">
                <ExternalLink size={12} />
                Source
              </span>
            )}
          </div>
        </div>

        {/* Score gauge */}
        <div className="flex flex-col items-center gap-1 shrink-0">
          <div
            className="relative w-14 h-14 rounded-full flex items-center justify-center"
            style={{
              background: `conic-gradient(
                ${topic.scoreTotal >= 7 ? "#00FF88" : topic.scoreTotal >= 5 ? "#FFD700" : "#FF3355"} 
                ${topic.scoreTotal * 10}%, 
                rgba(255,255,255,0.05) ${topic.scoreTotal * 10}%
              )`,
            }}
          >
            <div className="w-10 h-10 rounded-full bg-cyber-dark flex items-center justify-center">
              <span
                className={`text-sm font-display font-bold ${
                  topic.scoreTotal >= 7
                    ? "text-cyber-green"
                    : topic.scoreTotal >= 5
                    ? "text-cyber-yellow"
                    : "text-cyber-red"
                }`}
              >
                {topic.scoreTotal.toFixed(1)}
              </span>
            </div>
          </div>
          <span className="text-[9px] font-mono text-gray-500 uppercase tracking-wider">
            Score
          </span>
        </div>
      </div>
    </Card>
  );
}
