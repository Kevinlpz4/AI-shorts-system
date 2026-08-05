"use client";

import clsx from "clsx";
import { AlertTriangle, Server } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { SourceTag } from "./SourceTag";
import { useRuntimeStore } from "@/store/runtimeStore";

/** Fila label/valor mono consistente con las páginas existentes. */
function InfoRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4 py-1.5 border-b border-glass-border last:border-0">
      <span className="text-[10px] font-mono text-gray-500 uppercase tracking-[0.15em] shrink-0 pt-0.5">
        {label}
      </span>
      <span className="text-xs font-mono text-white text-right break-all">
        {children}
      </span>
    </div>
  );
}

/**
 * RuntimePanel — estado del runtime (versión, liveness, venv, config).
 * Tier REAL: leído vivo del runtime por /api/runtime/info.
 */
export function RuntimePanel({ className }: { className?: string }) {
  const section = useRuntimeStore((s) => s.runtime);
  const data = section.data;

  return (
    <Card glow="cyan" className={`p-6 ${className ?? ""}`}>
      <div className="flex items-center gap-2 mb-5">
        <Server size={14} className="text-neon-cyan" />
        <span className="text-[10px] font-mono text-neon-cyan/80 tracking-[0.2em] uppercase">
          Runtime
        </span>
        <span className="ml-auto">
          <SourceTag
            tier="REAL"
            title="Datos vivos del runtime (subprocess + filesystem)"
          />
        </span>
      </div>

      {section.loading ? (
        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 border-2 border-neon-cyan/30 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm font-mono text-gray-500">
              Leyendo estado del runtime…
            </span>
          </div>
        </div>
      ) : section.error ? (
        <div className="rounded-xl p-4 border border-neon-red/25 bg-neon-red/10">
          <p className="text-sm font-mono text-neon-red">{section.error}</p>
          <p className="mt-1 text-[10px] font-mono text-gray-500">
            hint: ver frontend/docs/runtime-integration.md
          </p>
        </div>
      ) : data ? (
        <>
          <div className="flex items-center gap-3 glass rounded-xl p-4 mb-4">
            <span className="relative flex h-3 w-3">
              <span
                className={clsx(
                  "animate-ping absolute inline-flex h-full w-full rounded-full opacity-75",
                  data.is_running ? "bg-neon-green" : "bg-neon-red"
                )}
              />
              <span
                className={clsx(
                  "relative inline-flex rounded-full h-3 w-3",
                  data.is_running ? "bg-neon-green" : "bg-neon-red"
                )}
              />
            </span>
            <span className="text-sm font-mono text-white">
              {data.is_running ? "Daemon corriendo" : "Daemon detenido"}
            </span>
            {data.liveness_check && (
              <span className="ml-auto text-[10px] font-mono text-gray-500">
                {data.liveness_check}
              </span>
            )}
          </div>

          <InfoRow label="Versión">{data.version}</InfoRow>
          <InfoRow label="Venv">
            {data.venv_available ? "disponible" : "NO disponible"}
          </InfoRow>
          {data.repo_root && <InfoRow label="Repo root">{data.repo_root}</InfoRow>}
          {data.config && (
            <>
              <InfoRow label="Pipeline interval">
                {data.config.pipeline_interval_minutes} min
              </InfoRow>
              <InfoRow label="Enabled jobs">
                {data.config.enabled_jobs.join(", ")}
              </InfoRow>
              <InfoRow label="Storage base">
                {data.config.storage_base_path}
              </InfoRow>
              <details className="mt-3">
                <summary className="cursor-pointer text-[10px] font-mono text-neon-cyan/70 tracking-[0.15em] uppercase list-none">
                  Config (defaults) — ver JSON
                </summary>
                <pre className="mt-2 p-3 rounded-lg bg-base-900/60 border border-glass-border text-[10px] font-mono text-gray-400 overflow-x-auto max-h-48 overflow-y-auto">
                  {JSON.stringify(data.config, null, 2)}
                </pre>
              </details>
            </>
          )}

          {!data.venv_available && (
            <div className="mt-4 rounded-xl p-3 border border-neon-yellow/25 bg-neon-yellow/10 flex gap-2 items-start">
              <AlertTriangle
                size={14}
                className="text-neon-yellow shrink-0 mt-0.5"
              />
              <p className="text-xs font-mono text-neon-yellow/90">
                Venv no disponible en el host — instructivo en
                frontend/docs/runtime-integration.md
              </p>
            </div>
          )}
        </>
      ) : null}
    </Card>
  );
}
