"use client";

import Link from "next/link";
import { useState } from "react";
import clsx from "clsx";
import { CalendarClock, RefreshCw, Terminal } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { SourceTag } from "./SourceTag";
import { useRuntimeStore } from "@/store/runtimeStore";

/**
 * SchedulerPanel — Discovery Topics Scheduler del research BC (legacy).
 * Tier LEGACY: consume GET /api/v1/scheduler/{status,config} + POST run-now
 * vía store (patrón settings/page.tsx). El scheduler del RUNTIME no es
 * observable desde el FE → sección NA (CLI-only).
 */
export function SchedulerPanel({ className }: { className?: string }) {
  const section = useRuntimeStore((s) => s.scheduler);
  const config = useRuntimeStore((s) => s.schedulerConfig);
  const runSchedulerNow = useRuntimeStore((s) => s.runSchedulerNow);
  const [running, setRunning] = useState(false);
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const status = section.data;

  const handleRunNow = async () => {
    setRunning(true);
    setFeedback(null);
    const result = await runSchedulerNow();
    setFeedback(
      result
        ? {
            type: "success",
            message: `Run complete: ${result.discovered} descubiertos, ${result.errors.length} errores`,
          }
        : {
            type: "error",
            message: "Run now falló — ver estado de la sección",
          }
    );
    setRunning(false);
  };

  return (
    <Card className={`p-6 ${className ?? ""}`}>
      <div className="flex items-center gap-2 mb-5">
        <CalendarClock size={14} className="text-neon-yellow" />
        <span className="text-[10px] font-mono text-neon-yellow/80 tracking-[0.2em] uppercase">
          Discovery Topics Scheduler (research BC)
        </span>
        <span className="ml-auto">
          <SourceTag
            tier="LEGACY"
            title="API legacy del research BC — NO es el scheduler del runtime"
          />
        </span>
      </div>

      {section.loading ? (
        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 border-2 border-neon-cyan/30 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm font-mono text-gray-500">
              Leyendo scheduler legacy…
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
          <div className="flex items-center gap-3 glass rounded-xl p-4 mb-4">
            <span className="relative flex h-3 w-3">
              <span
                className={clsx(
                  "animate-ping absolute inline-flex h-full w-full rounded-full opacity-75",
                  status.is_running ? "bg-neon-green" : "bg-neon-red"
                )}
              />
              <span
                className={clsx(
                  "relative inline-flex rounded-full h-3 w-3",
                  status.is_running ? "bg-neon-green" : "bg-neon-red"
                )}
              />
            </span>
            <span className="text-sm font-mono text-white">
              {status.is_running
                ? "Corriendo"
                : status.enabled
                  ? "Habilitado (en pausa)"
                  : "Deshabilitado"}
            </span>
            {status.last_run && (
              <span className="text-[10px] font-mono text-gray-500 ml-auto">
                Last run: {new Date(status.last_run).toLocaleString()}
              </span>
            )}
          </div>

          <div className="mb-4">
            <div className="flex items-center justify-between py-1.5 border-b border-glass-border">
              <span className="text-[10px] font-mono text-gray-500 uppercase tracking-[0.15em]">
                Intervalo
              </span>
              <span className="text-xs font-mono text-white">
                {status.interval_minutes} min
              </span>
            </div>
            {status.running_query && (
              <div className="flex items-center justify-between py-1.5 border-b border-glass-border">
                <span className="text-[10px] font-mono text-gray-500 uppercase tracking-[0.15em]">
                  Query activa
                </span>
                <span className="text-xs font-mono text-neon-cyan break-all">
                  {status.running_query}
                </span>
              </div>
            )}
            {config && (
              <>
                <div className="flex items-center justify-between py-1.5 border-b border-glass-border">
                  <span className="text-[10px] font-mono text-gray-500 uppercase tracking-[0.15em]">
                    Queries
                  </span>
                  <span className="text-xs font-mono text-white">
                    {config.queries.length}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1.5 border-b border-glass-border">
                  <span className="text-[10px] font-mono text-gray-500 uppercase tracking-[0.15em]">
                    Auto-generate
                  </span>
                  <span className="text-xs font-mono text-white">
                    {config.auto_generate_script ? "on" : "off"}
                  </span>
                </div>
              </>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button
              variant="secondary"
              onClick={handleRunNow}
              isLoading={running}
            >
              <RefreshCw size={16} />
              Run now (legacy)
            </Button>
            <Link
              href="/settings"
              className="text-[10px] font-mono text-neon-cyan/70 hover:text-neon-cyan transition-colors"
            >
              Edición completa en /settings →
            </Link>
          </div>

          {feedback && (
            <div
              className={clsx(
                "mt-4 px-4 py-2.5 rounded-xl text-sm font-mono border",
                feedback.type === "success"
                  ? "bg-neon-green/10 border-neon-green/25 text-neon-green"
                  : "bg-neon-red/10 border-neon-red/25 text-neon-red"
              )}
            >
              {feedback.message}
            </div>
          )}
        </>
      ) : null}

      {/* Runtime scheduler: no observable */}
      <div className="mt-5 rounded-xl p-4 border border-glass-border bg-base-900/40">
        <div className="flex items-center gap-2 mb-2">
          <Terminal size={12} className="text-gray-500" />
          <span className="text-[10px] font-mono text-gray-400 uppercase tracking-[0.15em]">
            Runtime Scheduler: no observable (CLI-only)
          </span>
          <span className="ml-auto">
            <SourceTag tier="NA" label="NA" title="Sin endpoint en este sprint" />
          </span>
        </div>
        <p className="text-xs font-mono text-gray-500 leading-relaxed">
          El scheduler del runtime corre vía CLI (python -m runtime schedule);
          no hay endpoint para observarlo desde el frontend. La terminal sigue
          siendo la referencia —{" "}
          <Link
            href="/terminal"
            className="text-neon-cyan/80 hover:text-neon-cyan transition-colors"
          >
            abrir /terminal
          </Link>
          .
        </p>
      </div>
    </Card>
  );
}
