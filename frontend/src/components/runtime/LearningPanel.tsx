"use client";

import { BrainCircuit } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { SourceTag } from "./SourceTag";
import { useRuntimeStore } from "@/store/runtimeStore";

/**
 * LearningPanel — reports de simulación (simulation_reports/).
 * Tier REAL (archivos reales del runtime) PERO datos SIMULADOS:
 * label persistente + nota honesta — no son métricas de producción.
 */
export function LearningPanel({ className }: { className?: string }) {
  const section = useRuntimeStore((s) => s.learning);
  const reports = section.data ?? [];

  return (
    <Card glow="violet" className={`p-6 ${className ?? ""}`}>
      <div className="flex items-center gap-2 mb-5">
        <BrainCircuit size={14} className="text-neon-cyan" />
        <span className="text-[10px] font-mono text-neon-cyan/80 tracking-[0.2em] uppercase">
          Learning
        </span>
        <span className="ml-auto flex items-center gap-2">
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[9px] font-mono font-semibold tracking-[0.15em] border bg-neon-yellow/10 border-neon-yellow/30 text-neon-yellow">
            SIMULADO
          </span>
          <SourceTag
            tier="REAL"
            title="Archivo real de simulation_reports/ — contenido simulado"
          />
        </span>
      </div>

      {section.loading ? (
        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 border-2 border-neon-cyan/30 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm font-mono text-gray-500">
              Leyendo simulation_reports…
            </span>
          </div>
        </div>
      ) : section.error ? (
        <div className="rounded-xl p-4 border border-neon-red/25 bg-neon-red/10">
          <p className="text-sm font-mono text-neon-red">{section.error}</p>
        </div>
      ) : reports.length === 0 ? (
        <div className="rounded-xl p-4 border border-glass-border bg-glass-base">
          <p className="text-sm font-mono text-gray-400">
            Sin reports de simulación — ejecutar la CLI
            (python -m runtime simulate). La CLI sigue siendo la referencia.
          </p>
        </div>
      ) : (
        reports.map((rep) => (
          <div
            key={rep.name}
            className="glass rounded-xl p-4 mb-3 last:mb-0"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs font-mono text-neon-cyan break-all">
                {rep.name}
              </span>
              <span className="text-[10px] font-mono text-gray-500 shrink-0">
                {new Date(rep.generated_at).toLocaleString()}
              </span>
            </div>
            <p className="mt-2 text-[10px] font-mono text-neon-yellow uppercase tracking-[0.15em]">
              Datos simulados — no métricas de producción
            </p>
            <details className="mt-2">
              <summary className="cursor-pointer text-[10px] font-mono text-neon-cyan/70 tracking-[0.15em] uppercase list-none">
                Ver JSON
              </summary>
              <pre className="mt-2 p-3 rounded-lg bg-base-900/60 border border-glass-border text-[10px] font-mono text-gray-400 overflow-x-auto max-h-56 overflow-y-auto">
                {JSON.stringify(rep.report, null, 2)}
              </pre>
            </details>
          </div>
        ))
      )}
    </Card>
  );
}
