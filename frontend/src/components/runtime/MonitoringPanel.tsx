"use client";

import { Activity } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { SourceTag } from "./SourceTag";
import { useRuntimeStore } from "@/store/runtimeStore";

/** Labels legibles para las claves de topics del research BC. */
const TOPIC_LABELS: Record<string, string> = {
  found: "Found",
  pending_review: "Pending review",
  approved: "Approved",
  rejected: "Rejected",
};

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

/**
 * MonitoringPanel — estado del research BC vía GET /api/v1/status (legacy).
 * Tier LEGACY. Nota honesta: pipeline y jobs del runtime NO son observables
 * aquí (CLI-only).
 */
export function MonitoringPanel({ className }: { className?: string }) {
  const section = useRuntimeStore((s) => s.monitoring);
  const status = section.data;
  const topics = status?.topics ?? null;

  return (
    <Card glow="green" className={`p-6 ${className ?? ""}`}>
      <div className="flex items-center gap-2 mb-5">
        <Activity size={14} className="text-neon-cyan" />
        <span className="text-[10px] font-mono text-neon-cyan/80 tracking-[0.2em] uppercase">
          Monitoring (research BC)
        </span>
        <span className="ml-auto">
          <SourceTag
            tier="LEGACY"
            title="GET /api/v1/status — research BC, no el runtime"
          />
        </span>
      </div>

      {section.loading ? (
        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 border-2 border-neon-cyan/30 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm font-mono text-gray-500">
              Leyendo /api/v1/status…
            </span>
          </div>
        </div>
      ) : section.error ? (
        <div className="rounded-xl p-4 border border-neon-red/25 bg-neon-red/10">
          <p className="text-sm font-mono text-neon-red">{section.error}</p>
          <p className="mt-1 text-[10px] font-mono text-gray-500">
            hint: NEXT_PUBLIC_API_URL debe apuntar al backend del research BC
          </p>
        </div>
      ) : status ? (
        <>
          <div className="flex items-center justify-between py-1.5 border-b border-glass-border">
            <span className="text-[10px] font-mono text-gray-500 uppercase tracking-[0.15em]">
              Versión API
            </span>
            <span className="text-xs font-mono text-white">
              {status.version ?? status.api_version ?? "unknown"}
            </span>
          </div>
          <div className="flex items-center justify-between py-1.5 border-b border-glass-border">
            <span className="text-[10px] font-mono text-gray-500 uppercase tracking-[0.15em]">
              Uptime
            </span>
            <span className="text-xs font-mono text-white">
              {typeof status.uptime_seconds === "number"
                ? formatUptime(status.uptime_seconds)
                : "—"}
            </span>
          </div>
          <div className="flex items-center justify-between py-1.5 border-b border-glass-border">
            <span className="text-[10px] font-mono text-gray-500 uppercase tracking-[0.15em]">
              Total topics
            </span>
            <span className="text-xs font-mono text-white">
              {status.total_topics ?? "—"}
            </span>
          </div>

          {topics ? (
            <div className="mt-4">
              <p className="text-[10px] font-mono text-gray-500 uppercase tracking-[0.15em] mb-2">
                Topics por estado
              </p>
              {Object.entries(topics).map(([key, value]) => (
                <div
                  key={key}
                  className="flex items-center justify-between py-1 border-b border-glass-border/50 last:border-0"
                >
                  <span className="text-xs font-mono text-gray-400">
                    {TOPIC_LABELS[key] ?? key}
                  </span>
                  <span className="text-xs font-mono text-neon-cyan">
                    {String(value)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-3 text-xs font-mono text-gray-500">
              Sin desglose de topics en la respuesta.
            </p>
          )}

          <div className="mt-4 rounded-xl p-3 border border-glass-border bg-base-900/40">
            <p className="text-[10px] font-mono text-gray-400 uppercase tracking-[0.15em]">
              No disponible aquí
            </p>
            <p className="mt-1 text-xs font-mono text-gray-500 leading-relaxed">
              Pipeline y jobs del runtime NO son observables vía legacy API —
              son CLI-only (ver UnavailablePanel abajo).
            </p>
          </div>
        </>
      ) : null}
    </Card>
  );
}
