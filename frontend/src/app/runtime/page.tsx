"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import clsx from "clsx";
import { motion } from "framer-motion";
import { Cpu, Play, RefreshCw, Terminal } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useRuntimeStore } from "@/store/runtimeStore";
import { RuntimePanel } from "@/components/runtime/RuntimePanel";
import { SourcesPanel } from "@/components/runtime/SourcesPanel";
import { SchedulerPanel } from "@/components/runtime/SchedulerPanel";
import { MonitoringPanel } from "@/components/runtime/MonitoringPanel";
import { FeedbackPanel } from "@/components/runtime/FeedbackPanel";
import { LearningPanel } from "@/components/runtime/LearningPanel";
import { UnavailablePanel } from "@/components/runtime/UnavailablePanel";

/**
 * /runtime — Centro de operación del Runtime (read-only).
 * 6 paneles + UnavailablePanel. Monta el runtimeStore en useEffect y
 * expone refresh global + run-now del scheduler legacy.
 */
export default function RuntimePage() {
  const loadAll = useRuntimeStore((s) => s.loadAll);
  const refresh = useRuntimeStore((s) => s.refresh);
  const runSchedulerNow = useRuntimeStore((s) => s.runSchedulerNow);
  const [refreshing, setRefreshing] = useState(false);
  const [running, setRunning] = useState(false);
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const handleRefresh = async () => {
    setRefreshing(true);
    setFeedback(null);
    await refresh();
    setRefreshing(false);
  };

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
            message:
              "Run now falló — ver el panel Discovery Topics Scheduler",
          }
    );
    setRunning(false);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="mb-8">
        <div className="flex items-center gap-2 text-[10px] font-mono text-neon-cyan/50 tracking-[0.2em] uppercase mb-2">
          <Cpu size={12} className="text-neon-cyan" />
          <span>Runtime Operations</span>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-display font-bold text-white tracking-wide">
              Runtime
            </h1>
            <p className="text-sm font-sans text-gray-400 mt-1 font-light">
              Centro de operación del runtime — datos vivos (read-only),
              legacy del research BC y brechas honestas
            </p>
          </div>
          <div className="flex gap-3">
            <Button
              variant="secondary"
              onClick={handleRefresh}
              isLoading={refreshing}
            >
              <RefreshCw size={16} />
              Refresh
            </Button>
            <Button
              variant="success"
              onClick={handleRunNow}
              isLoading={running}
            >
              <Play size={16} />
              Run now (scheduler legacy)
            </Button>
          </div>
        </div>
      </div>

      {feedback && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={clsx(
            "mb-6 px-4 py-2.5 rounded-xl text-sm font-mono border",
            feedback.type === "success"
              ? "bg-neon-green/10 border-neon-green/25 text-neon-green"
              : "bg-neon-red/10 border-neon-red/25 text-neon-red"
          )}
        >
          {feedback.message}
        </motion.div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <RuntimePanel />
        <MonitoringPanel />
        <SchedulerPanel />
        <LearningPanel />
        <FeedbackPanel />
        <SourcesPanel className="xl:col-span-2" />
      </div>

      <div className="mt-6">
        <UnavailablePanel />
      </div>

      <p className="mt-6 text-[10px] font-mono text-gray-600 flex items-center gap-1.5">
        <Terminal size={11} />
        La CLI sigue siendo la referencia para pipeline, jobs y colas —{" "}
        <Link
          href="/terminal"
          className="text-neon-cyan/70 hover:text-neon-cyan transition-colors"
        >
          abrir /terminal
        </Link>
      </p>
    </motion.div>
  );
}
