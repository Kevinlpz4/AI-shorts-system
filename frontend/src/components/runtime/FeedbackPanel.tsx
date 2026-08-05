"use client";

import { FileJson } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { SourceTag } from "./SourceTag";
import { useRuntimeStore } from "@/store/runtimeStore";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * FeedbackPanel — artefactos feedback_session_*.json del runtime (fs).
 * Tier REAL: archivos reales en repo root. Sin exports → estado honesto:
 * la CLI sigue siendo la referencia.
 */
export function FeedbackPanel({ className }: { className?: string }) {
  const section = useRuntimeStore((s) => s.feedback);
  const exportsList = section.data ?? [];

  return (
    <Card glow="magenta" className={`p-6 ${className ?? ""}`}>
      <div className="flex items-center gap-2 mb-5">
        <FileJson size={14} className="text-neon-cyan" />
        <span className="text-[10px] font-mono text-neon-cyan/80 tracking-[0.2em] uppercase">
          Feedback exports
        </span>
        <span className="ml-auto">
          <SourceTag
            tier="REAL"
            title="Artefactos feedback_session_*.json leídos del repo root"
          />
        </span>
      </div>

      {section.loading ? (
        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 border-2 border-neon-cyan/30 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm font-mono text-gray-500">
              Leyendo feedback_session_*.json…
            </span>
          </div>
        </div>
      ) : section.error ? (
        <div className="rounded-xl p-4 border border-neon-red/25 bg-neon-red/10">
          <p className="text-sm font-mono text-neon-red">{section.error}</p>
        </div>
      ) : exportsList.length === 0 ? (
        <div className="rounded-xl p-4 border border-glass-border bg-glass-base">
          <p className="text-sm font-mono text-gray-400">
            Sin exports de feedback — la CLI sigue siendo la referencia
            (export_session).
          </p>
        </div>
      ) : (
        <ul className="space-y-2">
          {exportsList.map((exp) => (
            <li key={exp.file} className="glass rounded-xl p-3">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-mono text-neon-cyan break-all">
                  {exp.file}
                </span>
                <span className="text-[10px] font-mono text-gray-500 shrink-0">
                  {formatBytes(exp.size)}
                </span>
              </div>
              <div className="mt-1 flex flex-wrap items-center gap-3 text-[10px] font-mono text-gray-500">
                <span>{new Date(exp.mtime).toLocaleString()}</span>
                {typeof exp.decisions === "number" && (
                  <span className="text-neon-green">
                    {exp.decisions} decisiones
                  </span>
                )}
                {exp.session_id && (
                  <span className="text-gray-600">{exp.session_id}</span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
