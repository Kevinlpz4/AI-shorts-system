"use client";

import { useState, useEffect } from "react";
import clsx from "clsx";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import {
  Settings,
  Construction,
  Play,
  Square,
  Save,
  RefreshCw,
} from "lucide-react";
import type { SchedulerStatus, SchedulerConfig } from "@/types";

/** Obtiene la base URL de la API desde env var, o vacío para modo mock */
function getApiBase(): string {
  return typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL
    : "";
}

/** Página de configuración del sistema */
export default function SettingsPage() {
  // ── Scheduler state (local — no necesita store global) ──
  const [status, setStatus] = useState<SchedulerStatus | null>(null);
  const [config, setConfig] = useState<SchedulerConfig>({
    interval_minutes: 60,
    queries: [],
    auto_generate_script: false,
  });
  const [queriesText, setQueriesText] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isToggling, setIsToggling] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  // ── Cargar estado inicial ──
  useEffect(() => {
    const base = getApiBase();

    if (!base) {
      setIsLoading(false);
      return;
    }

    Promise.all([
      fetch(`${base}/api/v1/scheduler/status`).then((r) => r.json()),
      fetch(`${base}/api/v1/scheduler/config`).then((r) => r.json()),
    ])
      .then(([statusData, configData]) => {
        setStatus(statusData);
        setConfig(configData);
        setQueriesText(configData.queries?.join("\n") || "");
      })
      .catch(() => {
        setFeedback({
          type: "error",
          message: "Failed to load scheduler data",
        });
      })
      .finally(() => setIsLoading(false));
  }, []);

  // ── Handlers ──

  /** Enciende / apaga el scheduler */
  const handleToggle = async () => {
    setIsToggling(true);
    setFeedback(null);

    try {
      const base = getApiBase();
      const endpoint = status?.is_running ? "stop" : "start";
      const res = await fetch(`${base}/api/v1/scheduler/${endpoint}`, {
        method: "POST",
      });

      if (!res.ok) throw new Error(`Failed to ${endpoint} scheduler`);

      setStatus((prev) =>
        prev ? { ...prev, is_running: !prev.is_running } : null,
      );
      setFeedback({
        type: "success",
        message: `Scheduler ${endpoint}ed successfully`,
      });
    } catch (err) {
      setFeedback({
        type: "error",
        message:
          err instanceof Error ? err.message : "Failed to toggle scheduler",
      });
    } finally {
      setIsToggling(false);
    }
  };

  /** Guarda la configuración del scheduler */
  const handleSaveConfig = async () => {
    setIsSaving(true);
    setFeedback(null);

    try {
      const base = getApiBase();

      if (!base) {
        // Modo mock: solo actualizamos estado local
        const updated: SchedulerConfig = {
          interval_minutes: config.interval_minutes,
          queries: queriesText
            .split("\n")
            .map((q) => q.trim())
            .filter(Boolean),
          auto_generate_script: config.auto_generate_script,
        };
        setConfig(updated);
        setFeedback({ type: "success", message: "Config saved (mock mode)" });
        return;
      }

      const body: Partial<SchedulerConfig> = {
        interval_minutes: config.interval_minutes,
        queries: queriesText
          .split("\n")
          .map((q) => q.trim())
          .filter(Boolean),
        auto_generate_script: config.auto_generate_script,
      };

      const res = await fetch(`${base}/api/v1/scheduler/config`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) throw new Error("Failed to save config");

      const updated = await res.json();
      setConfig(updated);
      setQueriesText(updated.queries?.join("\n") || "");
      setFeedback({ type: "success", message: "Config saved successfully" });
    } catch (err) {
      setFeedback({
        type: "error",
        message:
          err instanceof Error ? err.message : "Failed to save config",
      });
    } finally {
      setIsSaving(false);
    }
  };

  /** Ejecuta un ciclo de descubrimiento inmediato */
  const handleRunNow = async () => {
    setIsRunning(true);
    setFeedback(null);

    try {
      const base = getApiBase();
      const res = await fetch(`${base}/api/v1/scheduler/run-now`, {
        method: "POST",
      });

      if (!res.ok) throw new Error("Failed to run scheduler");

      const result = await res.json();
      setFeedback({
        type: "success",
        message: `Run complete: ${result.discovered_count || 0} discovered, ${result.errors?.length || 0} errors`,
      });

      // Refrescar estado
      const statusRes = await fetch(`${base}/api/v1/scheduler/status`);
      setStatus(await statusRes.json());
    } catch (err) {
      setFeedback({
        type: "error",
        message:
          err instanceof Error ? err.message : "Failed to run scheduler",
      });
    } finally {
      setIsRunning(false);
    }
  };

  // ── Render ──
  return (
    <div className="animate-fade-in">
      {/* ── Header ── */}
      <div className="flex items-center gap-2 text-[10px] font-mono text-cyber-cyan/60 tracking-widest uppercase mb-1">
        <span className="w-2 h-2 rounded-full bg-cyber-cyan animate-glow-pulse" />
        <span>Configuration</span>
      </div>
      <h1 className="text-2xl font-display font-bold text-white tracking-wide mb-6">
        Settings
      </h1>

      {/* ── Scheduler Controls ── */}
      <Card className="p-6 mb-6">
        {/* Section header */}
        <div className="flex items-center gap-2 text-[10px] font-mono text-cyber-cyan/60 tracking-widest uppercase mb-4">
          <span className="w-2 h-2 rounded-full bg-cyber-green animate-glow-pulse" />
          <span>Scheduler Controls</span>
        </div>

        {/* Feedback message */}
        {feedback && (
          <div
            className={clsx(
              "mb-4 px-4 py-2.5 rounded-lg text-sm font-mono border",
              feedback.type === "success"
                ? "bg-cyber-green/10 border-cyber-green/30 text-cyber-green"
                : "bg-cyber-red/10 border-cyber-red/30 text-cyber-red",
            )}
          >
            {feedback.message}
          </div>
        )}

        {/* ── Status indicator ── */}
        {isLoading ? (
          <div className="mb-6 p-3 bg-cyber-dark/40 rounded-lg border border-glass-border">
            <div className="flex items-center gap-2 text-sm font-mono text-gray-500">
              <span className="w-4 h-4 border-2 border-gray-500 border-t-transparent rounded-full animate-spin" />
              Loading scheduler status...
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-3 mb-6 p-3 bg-cyber-dark/40 rounded-lg border border-glass-border">
            <span
              className={clsx(
                "w-3 h-3 rounded-full",
                status?.is_running
                  ? "bg-cyber-green animate-glow-pulse"
                  : "bg-cyber-red",
              )}
            />
            <span className="text-sm font-mono text-white">
              {status?.is_running ? "🟢 Running" : "🔴 Stopped"}
            </span>
            {status?.last_run && (
              <span className="text-xs font-mono text-gray-500 ml-auto">
                Last run: {new Date(status.last_run).toLocaleString()}
              </span>
            )}
          </div>
        )}

        {/* ── Toggle + Run Now ── */}
        <div className="flex gap-3 mb-6">
          <Button
            variant={status?.is_running ? "danger" : "success"}
            onClick={handleToggle}
            isLoading={isToggling}
          >
            {status?.is_running ? <Square size={16} /> : <Play size={16} />}
            {status?.is_running ? "Stop" : "Start"}
          </Button>
          <Button
            variant="secondary"
            onClick={handleRunNow}
            isLoading={isRunning}
          >
            <RefreshCw size={16} />
            Run Now
          </Button>
        </div>

        {/* ── Config form ── */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <Input
            label="Interval (minutes)"
            type="number"
            min={1}
            value={config.interval_minutes}
            onChange={(e) =>
              setConfig((prev) => ({
                ...prev,
                interval_minutes: parseInt(e.target.value) || 60,
              }))
            }
          />

          {/* Auto-generate toggle */}
          <div className="flex items-center gap-3 p-3 bg-cyber-dark/40 rounded-lg border border-glass-border self-end">
            <button
              type="button"
              onClick={() =>
                setConfig((prev) => ({
                  ...prev,
                  auto_generate_script: !prev.auto_generate_script,
                }))
              }
              className={clsx(
                "relative w-12 h-6 rounded-full transition-colors duration-200 shrink-0",
                config.auto_generate_script
                  ? "bg-cyber-magenta"
                  : "bg-gray-600",
              )}
            >
              <span
                className={clsx(
                  "absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform duration-200",
                  config.auto_generate_script && "translate-x-6",
                )}
              />
            </button>
            <div>
              <p className="text-sm font-mono text-white">
                Auto-generate on approve
              </p>
              <p className="text-xs font-mono text-gray-500">
                Automatically generate a script when approving a topic
              </p>
            </div>
          </div>
        </div>

        {/* Queries textarea */}
        <div className="mb-6">
          <label className="block mb-1.5 text-xs font-mono text-gray-400 uppercase tracking-wider">
            Queries (one per line)
          </label>
          <textarea
            value={queriesText}
            onChange={(e) => setQueriesText(e.target.value)}
            rows={4}
            className="w-full bg-cyber-dark/60 border border-glass-border rounded-lg px-3 py-2.5 text-sm font-mono text-white placeholder-gray-500 backdrop-blur-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-cyber-purple/50 focus:border-cyber-cyan/50 resize-vertical"
            placeholder="AI technology&#10;bitcoin news&#10;science discoveries"
          />
        </div>

        {/* Save button */}
        <Button
          variant="primary"
          onClick={handleSaveConfig}
          isLoading={isSaving}
        >
          <Save size={16} />
          Save Config
        </Button>
      </Card>

      {/* ── Existing placeholder card ── */}
      <Card className="p-12 flex flex-col items-center justify-center text-gray-500">
        <Settings size={48} className="mb-4 opacity-30" />
        <Construction size={24} className="mb-2 text-cyber-yellow" />
        <p className="text-sm font-mono">System Settings</p>
        <p className="text-xs font-mono text-gray-600 mt-1">
          Coming soon — source configuration, scoring weights, API keys.
        </p>
      </Card>
    </div>
  );
}
