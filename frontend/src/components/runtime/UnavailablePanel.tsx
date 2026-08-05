"use client";

import Link from "next/link";
import { Ban, Terminal } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { SourceTag } from "./SourceTag";

/** Brechas del sprint: funcionalidad runtime viva sin observabilidad FE. */
const UNAVAILABLE_ITEMS: { label: string; description: string }[] = [
  {
    label: "Pipeline",
    description:
      "Ejecución del pipeline del runtime (ingestion → learning) no observable desde el FE.",
  },
  {
    label: "Jobs",
    description:
      "Estados de jobs del runtime no expuestos vía API — solo enabled_jobs en config.",
  },
  {
    label: "Feedback queue viva",
    description: "Cola de feedback en memoria del runtime — CLI-only.",
  },
  {
    label: "Learning metrics vivas",
    description:
      "Métricas de aprendizaje en memoria — solo reports simulados en disco.",
  },
];

/**
 * UnavailablePanel — sección honesta de lo que NO está disponible en este
 * sprint. Tier NA: runtime CLI-only, la terminal sigue siendo la referencia.
 */
export function UnavailablePanel({ className }: { className?: string }) {
  return (
    <Card className={`p-6 ${className ?? ""}`}>
      <div className="flex items-center gap-2 mb-5">
        <Ban size={14} className="text-gray-500" />
        <span className="text-[10px] font-mono text-gray-400 uppercase tracking-[0.2em]">
          No disponible en este sprint
        </span>
        <span className="ml-auto">
          <SourceTag
            tier="NA"
            title="CLI-only — sin endpoint hasta gate P6/P7 (facade /api/v2)"
          />
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
        {UNAVAILABLE_ITEMS.map((item) => (
          <div
            key={item.label}
            className="rounded-xl p-3 border border-glass-border bg-base-900/40"
          >
            <p className="text-[10px] font-mono text-gray-300 uppercase tracking-[0.15em]">
              {item.label}
            </p>
            <p className="mt-1 text-xs font-mono text-gray-500 leading-relaxed">
              {item.description}
            </p>
          </div>
        ))}
      </div>

      <div className="rounded-xl p-4 border border-neon-yellow/25 bg-neon-yellow/5 flex flex-col sm:flex-row sm:items-center gap-3">
        <p className="text-sm font-mono text-neon-yellow/90">
          runtime CLI-only: usar la terminal — la CLI sigue siendo la
          referencia.
        </p>
        <Link
          href="/terminal"
          className="inline-flex items-center gap-2 text-xs font-mono text-neon-cyan hover:text-neon-cyan/80 transition-colors shrink-0"
        >
          <Terminal size={14} />
          abrir /terminal
        </Link>
      </div>
    </Card>
  );
}
