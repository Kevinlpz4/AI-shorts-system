"use client";

import { useEffect } from "react";
import { useTopicStore } from "@/store/topicStore";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ScoreRadar } from "@/components/topic/ScoreRadar";
import { TopicStatus } from "@/types";
import {
  ExternalLink,
  Clock,
  User,
  Code2,
  Loader2,
  X,
  CheckCircle,
  XCircle,
} from "lucide-react";

/** Props del panel de detalle de un topic */
interface TopicDetailPanelProps {
  /** ID del topic a cargar (opcional — si no se provee muestra empty state) */
  topicId?: string;
  /** Callback al cerrar el panel */
  onClose?: () => void;
}

/**
 * Panel lateral de detalle de un topic.
 *
 * Muestra toda la metadata, score breakdown, y botones de moderación
 * (approve/reject) cuando el topic está en PENDING_REVIEW.
 */
export function TopicDetailPanel({ topicId, onClose }: TopicDetailPanelProps) {
  const { selectedTopic, isLoading, loadTopicById, approveTopic, rejectTopic } =
    useTopicStore();

  useEffect(() => {
    if (topicId) {
      loadTopicById(topicId);
    }
  }, [topicId, loadTopicById]);

  if (isLoading) {
    return (
      <Card className="p-8 flex items-center justify-center">
        <Loader2 size={24} className="animate-spin text-cyber-cyan" />
      </Card>
    );
  }

  if (!selectedTopic) {
    return (
      <Card className="p-8 flex flex-col items-center justify-center text-gray-500">
        <Code2 size={32} className="mb-3 opacity-50" />
        <p className="text-sm font-mono">Select a topic to view details</p>
      </Card>
    );
  }

  const topic = selectedTopic;
  const isPending = topic.status === "PENDING_REVIEW";
  const isTerminal =
    topic.status === "APPROVED" || topic.status === "REJECTED";

  const handleApprove = () => approveTopic(topic.id);
  const handleReject = () => rejectTopic(topic.id);

  return (
    <Card className="overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-glass-border">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <StatusBadge status={topic.status as TopicStatus} size="md" />
              <span className="text-[10px] font-mono text-gray-500 uppercase">
                {topic.sourceName}
              </span>
            </div>
            <h2 className="text-base font-semibold text-white leading-snug">
              {topic.title}
            </h2>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-gray-500 hover:text-white hover:bg-glass-white transition-all"
            >
              <X size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="p-5 space-y-5">
        {/* Description */}
        <div>
          <p className="text-xs font-mono text-gray-400 uppercase tracking-wider mb-2">
            Description
          </p>
          <p className="text-sm text-gray-300 leading-relaxed font-sans">
            {topic.description || "No description available."}
          </p>
        </div>

        {/* Content preview */}
        {topic.contentPreview && (
          <div>
            <p className="text-xs font-mono text-gray-400 uppercase tracking-wider mb-2">
              Content Preview
            </p>
            <p className="text-sm text-gray-400 font-sans leading-relaxed line-clamp-4">
              {topic.contentPreview}
            </p>
          </div>
        )}

        {/* Metadata */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-lg bg-glass-white">
            <div className="flex items-center gap-2 text-[10px] font-mono text-gray-500 mb-1">
              <Clock size={12} /> Created
            </div>
            <p className="text-xs font-mono text-gray-300">
              {new Date(topic.createdAt).toLocaleString()}
            </p>
          </div>
          {topic.reviewedAt && (
            <div className="p-3 rounded-lg bg-glass-white">
              <div className="flex items-center gap-2 text-[10px] font-mono text-gray-500 mb-1">
                <Clock size={12} /> Reviewed
              </div>
              <p className="text-xs font-mono text-gray-300">
                {new Date(topic.reviewedAt).toLocaleString()}
              </p>
            </div>
          )}
          {topic.author && (
            <div className="p-3 rounded-lg bg-glass-white">
              <div className="flex items-center gap-2 text-[10px] font-mono text-gray-500 mb-1">
                <User size={12} /> Author
              </div>
              <p className="text-xs font-mono text-gray-300">{topic.author}</p>
            </div>
          )}
          <div className="p-3 rounded-lg bg-glass-white">
            <div className="flex items-center gap-2 text-[10px] font-mono text-gray-500 mb-1">
              <Code2 size={12} /> Source
            </div>
            <p className="text-xs font-mono text-gray-300">{topic.sourceName}</p>
          </div>
        </div>

        {/* URL */}
        {topic.url && (
          <a
            href={topic.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-xs font-mono text-cyber-cyan/70 hover:text-cyber-cyan transition-colors"
          >
            <ExternalLink size={14} />
            Open original source
          </a>
        )}

        {/* Score breakdown */}
        <div className="pt-3 border-t border-glass-border">
          <p className="text-xs font-mono text-gray-400 uppercase tracking-wider mb-4">
            Score Analysis
          </p>
          <ScoreRadar
            score={topic.score}
            total={topic.scoreTotal}
          />
        </div>
      </div>

      {/* Actions */}
      {isPending && (
        <div className="p-5 border-t border-glass-border bg-glass-white">
          <div className="flex items-center gap-3">
            <Button
              variant="success"
              onClick={handleApprove}
              className="flex-1"
            >
              <CheckCircle size={16} />
              Approve
            </Button>
            <Button
              variant="danger"
              onClick={handleReject}
              className="flex-1"
            >
              <XCircle size={16} />
              Reject
            </Button>
          </div>
        </div>
      )}

      {isTerminal && (
        <div className="p-5 border-t border-glass-border bg-glass-white">
          <p className="text-xs font-mono text-center text-gray-500">
            Topic is{" "}
            <span
              className={
                topic.status === "APPROVED"
                  ? "text-cyber-green"
                  : "text-cyber-red"
              }
            >
              {topic.status === "APPROVED" ? "Approved" : "Rejected"}
            </span>
            . This decision is final.
          </p>
        </div>
      )}
    </Card>
  );
}
