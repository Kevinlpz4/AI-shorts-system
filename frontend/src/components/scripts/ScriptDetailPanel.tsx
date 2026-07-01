"use client";

import clsx from "clsx";
import { ScriptWithTopic } from "@/types";
import { Card } from "@/components/ui/Card";
import { motion } from "framer-motion";
import {
  Clock,
  Music,
  Target,
  FileText,
  CheckCircle,
  AlertTriangle,
  X,
  Code2,
} from "lucide-react";

interface ScriptDetailPanelProps {
  script: ScriptWithTopic | null;
  onClose: () => void;
}

export function ScriptDetailPanel({ script, onClose }: ScriptDetailPanelProps) {
  if (!script) {
    return (
      <Card className="p-8 flex flex-col items-center justify-center">
        <div className="relative p-4 rounded-2xl bg-glass-strong border border-glass-border mb-4">
          <FileText size={24} className="text-gray-500" />
        </div>
        <p className="text-sm font-mono text-gray-500">Select a script</p>
        <p className="text-xs font-mono text-gray-600 mt-1">to view details</p>
      </Card>
    );
  }

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
                {script.isValid ? (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-neon-green/10 border border-neon-green/25 text-[10px] font-mono text-neon-green">
                    <CheckCircle size={10} /> Valid
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-neon-yellow/10 border border-neon-yellow/25 text-[10px] font-mono text-neon-yellow">
                    <AlertTriangle size={10} /> Warnings
                  </span>
                )}
                <span className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">
                  {script.format}
                </span>
              </div>
              <h2 className="text-base font-semibold text-white leading-snug font-display">
                {script.topic_title}
              </h2>
            </div>
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={onClose}
              className="p-1.5 rounded-xl text-gray-500 hover:text-white hover:bg-glass-light transition-all shrink-0"
            >
              <X size={16} />
            </motion.button>
          </div>
        </div>

        {/* Content */}
        <div className="p-5 space-y-5">
          {/* Hook */}
          <div>
            <p className="text-[10px] font-mono text-neon-magenta uppercase tracking-[0.15em] mb-2 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-neon-magenta" />
              Hook
            </p>
            <p className="text-sm text-gray-200 font-sans leading-relaxed">
              {script.hook}
            </p>
          </div>

          {/* Body */}
          <div>
            <p className="text-[10px] font-mono text-neon-cyan uppercase tracking-[0.15em] mb-2 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-neon-cyan" />
              Body
            </p>
            <p className="text-sm text-gray-300 font-sans leading-relaxed">
              {script.body}
            </p>
          </div>

          {/* CTA */}
          <div>
            <p className="text-[10px] font-mono text-neon-green uppercase tracking-[0.15em] mb-2 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-neon-green" />
              Call to Action
            </p>
            <p className="text-sm text-gray-200 font-sans leading-relaxed">
              {script.cta}
            </p>
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-2 pt-3 border-t border-glass-border">
            <div className="glass rounded-xl p-2.5">
              <div className="flex items-center gap-1.5 text-[9px] font-mono text-gray-500 mb-0.5">
                <Clock size={10} /> Duration
              </div>
              <p className="text-xs font-mono text-gray-200">{script.duration}s</p>
            </div>
            <div className="glass rounded-xl p-2.5">
              <div className="flex items-center gap-1.5 text-[9px] font-mono text-gray-500 mb-0.5">
                <Music size={10} /> Tone
              </div>
              <p className="text-xs font-mono text-gray-200">{script.tone}</p>
            </div>
            <div className="glass rounded-xl p-2.5">
              <div className="flex items-center gap-1.5 text-[9px] font-mono text-gray-500 mb-0.5">
                <Target size={10} /> Format
              </div>
              <p className="text-xs font-mono text-gray-200">{script.format}</p>
            </div>
            <div className="glass rounded-xl p-2.5">
              <div className="flex items-center gap-1.5 text-[9px] font-mono text-gray-500 mb-0.5">
                <FileText size={10} /> Words
              </div>
              <p className="text-xs font-mono text-gray-200">{script.wordCount}</p>
            </div>
          </div>

          {/* Topic info */}
          <div className="glass rounded-xl p-3">
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-gray-500 mb-1">
              <Code2 size={12} /> Associated Topic
            </div>
            <div className="flex items-center gap-2">
              <p className="text-xs font-mono text-gray-300 line-clamp-1">
                {script.topic_title}
              </p>
              <span
                className={clsx(
                  "text-[10px] font-mono px-1.5 py-0.5 rounded shrink-0",
                  script.topic_score >= 8
                    ? "bg-neon-green/10 text-neon-green"
                    : script.topic_score >= 6
                      ? "bg-neon-yellow/10 text-neon-yellow"
                      : "bg-neon-red/10 text-neon-red",
                )}
              >
                {script.topic_score}
              </span>
            </div>
          </div>

          {/* Timestamps */}
          <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-gray-600">
            <span>Created: {new Date(script.createdAt).toLocaleString()}</span>
            <span>Updated: {new Date(script.updatedAt).toLocaleString()}</span>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
