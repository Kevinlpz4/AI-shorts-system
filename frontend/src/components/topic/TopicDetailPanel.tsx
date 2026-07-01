"use client";

import { useEffect } from "react";
import { useTopicStore } from "@/store/topicStore";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ScoreRadar } from "@/components/topic/ScoreRadar";
import { TopicStatus } from "@/types";
import { motion } from "framer-motion";
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

interface TopicDetailPanelProps {
  topicId?: string;
  onClose?: () => void;
}

export function TopicDetailPanel({ topicId, onClose }: TopicDetailPanelProps) {
  const { selectedTopic, isLoading, loadTopicById, approveTopic, rejectTopic } =
    useTopicStore();

  useEffect(() => {
    if (topicId) {
      loadTopicById(topicId);
    }
  }, [topicId, loadTopicById]);

  // ── Loading state ──
  if (isLoading) {
    return (
      <Card className="p-8 flex items-center justify-center">
        <Loader2 size={24} className="animate-spin text-neon-cyan" />
      </Card>
    );
  }

  // ── Empty state ──
  if (!selectedTopic) {
    return (
      <Card className="p-8 flex flex-col items-center justify-center">
        <div className="relative p-4 rounded-2xl bg-glass-strong border border-glass-border mb-4">
          <Code2 size={24} className="text-gray-500" />
        </div>
        <p className="text-sm font-mono text-gray-500">Select a topic</p>
        <p className="text-xs font-mono text-gray-600 mt-1">to view details</p>
      </Card>
    );
  }

  const topic = selectedTopic;
  const isPending = topic.status === "PENDING_REVIEW";
  const isTerminal = topic.status === "APPROVED" || topic.status === "REJECTED";

  const handleApprove = () => approveTopic(topic.id);
  const handleReject = () => rejectTopic(topic.id);

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ type: "spring", stiffness: 100, damping: 20 }}
    >
      <Card className="overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-glass-border">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <StatusBadge status={topic.status as TopicStatus} size="md" />
                <span className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">
                  {topic.sourceName}
                </span>
              </div>
              <h2 className="text-base font-semibold text-white leading-snug font-display">
                {topic.title}
              </h2>
            </div>
            {onClose && (
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={onClose}
                className="p-1.5 rounded-xl text-gray-500 hover:text-white hover:bg-glass-light transition-all shrink-0"
              >
                <X size={16} />
              </motion.button>
            )}
          </div>
        </div>

        {/* Body */}
        <div className="p-5 space-y-5">
          {/* Description */}
          <div>
            <p className="text-[10px] font-mono text-gray-400 uppercase tracking-[0.15em] mb-2">
              Description
            </p>
            <p className="text-sm text-gray-300 leading-relaxed font-sans">
              {topic.description || "No description available."}
            </p>
          </div>

          {/* Content preview */}
          {topic.contentPreview && (
            <div>
              <p className="text-[10px] font-mono text-gray-400 uppercase tracking-[0.15em] mb-2">
                Content Preview
              </p>
              <p className="text-sm text-gray-400 font-sans leading-relaxed line-clamp-4">
                {topic.contentPreview}
              </p>
            </div>
          )}

          {/* Metadata grid */}
          <div className="grid grid-cols-2 gap-2">
            <div className="glass rounded-xl p-3">
              <div className="flex items-center gap-1.5 text-[10px] font-mono text-gray-500 mb-1">
                <Clock size={11} /> Created
              </div>
              <p className="text-xs font-mono text-gray-300">
                {new Date(topic.createdAt).toLocaleString()}
              </p>
            </div>
            {topic.reviewedAt && (
              <div className="glass rounded-xl p-3">
                <div className="flex items-center gap-1.5 text-[10px] font-mono text-gray-500 mb-1">
                  <Clock size={11} /> Reviewed
                </div>
                <p className="text-xs font-mono text-gray-300">
                  {new Date(topic.reviewedAt).toLocaleString()}
                </p>
              </div>
            )}
            {topic.author && (
              <div className="glass rounded-xl p-3">
                <div className="flex items-center gap-1.5 text-[10px] font-mono text-gray-500 mb-1">
                  <User size={11} /> Author
                </div>
                <p className="text-xs font-mono text-gray-300">{topic.author}</p>
              </div>
            )}
            <div className="glass rounded-xl p-3">
              <div className="flex items-center gap-1.5 text-[10px] font-mono text-gray-500 mb-1">
                <Code2 size={11} /> Source
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
              className="flex items-center gap-2 text-xs font-mono text-neon-cyan/60 hover:text-neon-cyan transition-all duration-300"
            >
              <ExternalLink size={14} />
              Open original source
            </a>
          )}

          {/* Score */}
          <div className="pt-3 border-t border-glass-border">
            <p className="text-[10px] font-mono text-gray-400 uppercase tracking-[0.15em] mb-4">
              Score Analysis
            </p>
            <ScoreRadar score={topic.score} total={topic.scoreTotal} />
          </div>
        </div>

        {/* Actions */}
        {isPending && (
          <div className="p-5 border-t border-glass-border bg-glass-base">
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
          <div className="p-5 border-t border-glass-border bg-glass-base">
            <p className="text-xs font-mono text-center text-gray-500">
              Topic is{" "}
              <span
                className={
                  topic.status === "APPROVED"
                    ? "text-neon-green"
                    : "text-neon-red"
                }
              >
                {topic.status === "APPROVED" ? "Approved" : "Rejected"}
              </span>
              . This decision is final.
            </p>
          </div>
        )}
      </Card>
    </motion.div>
  );
}
