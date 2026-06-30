"use client";

import clsx from "clsx";
import { ScriptWithTopic } from "@/types";
import { Card } from "@/components/ui/Card";
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
      <Card className="p-8 flex flex-col items-center justify-center text-gray-500">
        <FileText size={32} className="mb-3 opacity-50" />
        <p className="text-sm font-mono">Select a script to view details</p>
        <p className="text-xs font-mono text-gray-600 mt-1">
          Full content + metadata will appear here
        </p>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-glass-border">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              {script.isValid ? (
                <span className="flex items-center gap-1 text-[10px] font-mono text-cyber-green">
                  <CheckCircle size={10} /> Valid
                </span>
              ) : (
                <span className="flex items-center gap-1 text-[10px] font-mono text-cyber-yellow">
                  <AlertTriangle size={10} /> Warnings
                </span>
              )}
              <span className="text-[10px] font-mono text-gray-500 uppercase">
                {script.format}
              </span>
            </div>
            <h2 className="text-base font-semibold text-white leading-snug">
              {script.topic_title}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-500 hover:text-white hover:bg-glass-white transition-all"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-5 space-y-5">
        {/* Hook */}
        <div>
          <p className="text-[10px] font-mono text-cyber-magenta uppercase tracking-wider mb-2 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-cyber-magenta" />
            Hook
          </p>
          <p className="text-sm text-gray-200 font-sans leading-relaxed">
            {script.hook}
          </p>
        </div>

        {/* Body */}
        <div>
          <p className="text-[10px] font-mono text-cyber-cyan uppercase tracking-wider mb-2 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-cyber-cyan" />
            Body
          </p>
          <p className="text-sm text-gray-300 font-sans leading-relaxed">
            {script.body}
          </p>
        </div>

        {/* CTA */}
        <div>
          <p className="text-[10px] font-mono text-cyber-green uppercase tracking-wider mb-2 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-cyber-green" />
            Call to Action
          </p>
          <p className="text-sm text-gray-200 font-sans leading-relaxed">
            {script.cta}
          </p>
        </div>

        {/* Metadata */}
        <div className="grid grid-cols-2 gap-2 pt-3 border-t border-glass-border">
          <div className="p-2.5 rounded-lg bg-glass-white">
            <div className="flex items-center gap-1.5 text-[9px] font-mono text-gray-500 mb-0.5">
              <Clock size={10} /> Duration
            </div>
            <p className="text-xs font-mono text-gray-200">{script.duration}s</p>
          </div>
          <div className="p-2.5 rounded-lg bg-glass-white">
            <div className="flex items-center gap-1.5 text-[9px] font-mono text-gray-500 mb-0.5">
              <Music size={10} /> Tone
            </div>
            <p className="text-xs font-mono text-gray-200">{script.tone}</p>
          </div>
          <div className="p-2.5 rounded-lg bg-glass-white">
            <div className="flex items-center gap-1.5 text-[9px] font-mono text-gray-500 mb-0.5">
              <Target size={10} /> Format
            </div>
            <p className="text-xs font-mono text-gray-200">{script.format}</p>
          </div>
          <div className="p-2.5 rounded-lg bg-glass-white">
            <div className="flex items-center gap-1.5 text-[9px] font-mono text-gray-500 mb-0.5">
              <FileText size={10} /> Words
            </div>
            <p className="text-xs font-mono text-gray-200">{script.wordCount}</p>
          </div>
        </div>

        {/* Topic info */}
        <div className="p-3 rounded-lg bg-glass-white border border-glass-border">
          <div className="flex items-center gap-2 text-[10px] font-mono text-gray-500 mb-1">
            <Code2 size={12} /> Associated Topic
          </div>
          <div className="flex items-center gap-2">
            <p className="text-xs font-mono text-gray-300 line-clamp-1">
              {script.topic_title}
            </p>
            <span
              className={clsx(
                "text-[10px] font-mono px-1.5 py-0.5 rounded shrink-0",
                script.topic_score >= 80
                  ? "bg-cyber-green/10 text-cyber-green"
                  : script.topic_score >= 60
                    ? "bg-cyber-yellow/10 text-cyber-yellow"
                    : "bg-cyber-red/10 text-cyber-red",
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
  );
}
