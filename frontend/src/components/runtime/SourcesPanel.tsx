"use client";

import clsx from "clsx";
import { Database } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { SourceTag } from "./SourceTag";
import { useRuntimeStore } from "@/store/runtimeStore";

/**
 * SourcesPanel — catálogo real de fuentes del runtime (probe subprocess).
 * Tier REAL. Si el probe falla (venv ausente/timeout) → mensaje honesto + hint.
 */
export function SourcesPanel({ className }: { className?: string }) {
  const section = useRuntimeStore((s) => s.sources);
  const sources = section.data ?? [];

  return (
    <Card glow="violet" className={`p-6 ${className ?? ""}`}>
      <div className="flex items-center gap-2 mb-5">
        <Database size={14} className="text-neon-cyan" />
        <span className="text-[10px] font-mono text-neon-cyan/80 tracking-[0.2em] uppercase">
          Catálogo de fuentes
        </span>
        <span className="ml-auto">
          <SourceTag
            tier="REAL"
            title="Leído vivo del runtime: probe .venv/bin/python3 (catálogo real)"
          />
        </span>
      </div>

      {section.loading ? (
        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 border-2 border-neon-cyan/30 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm font-mono text-gray-500">
              Probando catálogo de fuentes…
            </span>
          </div>
        </div>
      ) : section.error ? (
        <div className="rounded-xl p-4 border border-neon-red/25 bg-neon-red/10">
          <p className="text-sm font-mono text-neon-red">{section.error}</p>
          <p className="mt-1 text-[10px] font-mono text-gray-500">
            hint: ver frontend/docs/runtime-integration.md (venv +
            RUNTIME_REPO_ROOT)
          </p>
        </div>
      ) : sources.length === 0 ? (
        <p className="text-sm font-mono text-gray-400">
          Sin fuentes en el catálogo.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="text-[9px] font-mono text-gray-500 uppercase tracking-[0.15em] border-b border-glass-border">
                <th className="py-2 pr-3">Id</th>
                <th className="py-2 pr-3">Provider</th>
                <th className="py-2 pr-3">Tech</th>
                <th className="py-2 pr-3">Categorías</th>
                <th className="py-2 pr-3">Enabled</th>
                <th className="py-2 pr-3">Prioridad</th>
                <th className="py-2 pr-3">Poll</th>
                <th className="py-2">Url</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((src) => (
                <tr
                  key={src.id}
                  className="border-b border-glass-border/50 last:border-0"
                >
                  <td className="py-2 pr-3 text-xs font-mono text-neon-cyan">
                    {src.id}
                  </td>
                  <td className="py-2 pr-3 text-xs font-mono text-white">
                    {src.provider}
                  </td>
                  <td className="py-2 pr-3 text-xs font-mono text-gray-300">
                    {src.technology}
                  </td>
                  <td className="py-2 pr-3 text-xs font-mono text-gray-400">
                    {src.categories.length > 0
                      ? src.categories.join(", ")
                      : "—"}
                  </td>
                  <td className="py-2 pr-3">
                    <span className="relative flex h-2 w-2">
                      <span
                        className={clsx(
                          "relative inline-flex rounded-full h-2 w-2",
                          src.enabled ? "bg-neon-green" : "bg-gray-600"
                        )}
                      />
                    </span>
                  </td>
                  <td className="py-2 pr-3 text-xs font-mono text-gray-300">
                    {src.priority}
                  </td>
                  <td className="py-2 pr-3 text-xs font-mono text-gray-300">
                    {src.poll_interval_minutes}m
                  </td>
                  <td className="py-2 text-xs font-mono text-gray-400 break-all">
                    {src.url ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
