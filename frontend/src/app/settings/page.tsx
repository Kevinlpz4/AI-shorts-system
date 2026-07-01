"use client";

import { useState, useEffect } from "react";
import clsx from "clsx";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { motion } from "framer-motion";
import {
  Settings,
  Construction,
  Play,
  Square,
  Save,
  RefreshCw,
  Clock,
  Activity,
} from "lucide-react";
import type { SchedulerStatus, SchedulerConfig } from "@/types";
import { getApiBase } from "@/lib/utils";

export default function SettingsPage() {
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
        setFeedback({ type: "error", message: "Failed to load scheduler data" });
      })
      .finally(() => setIsLoading(false));
  }, []);

  const handleToggle = async () => {
    setIsToggling(true);
    setFeedback(null);
    try {
      const base = getApiBase();
      const endpoint = status?.is_running ? "stop" : "start";
      const res = await fetch(`${base}/api/v1/scheduler/${endpoint}`, { method: "POST" });
      if (!res.ok) throw new Error(`Failed to ${endpoint} scheduler`);
      setStatus((prev) => (prev ? { ...prev, is_running: !prev.is_running } : null));
      setFeedback({ type: "success", message: `Scheduler ${endpoint}ed successfully` });
    } catch (err) {
      setFeedback({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to toggle scheduler",
      });
    } finally {
      setIsToggling(false);
    }
  };

  const handleSaveConfig = async () => {
    setIsSaving(true);
    setFeedback(null);
    try {
      const base = getApiBase();
      const parsedQueries = queriesText.split("\n").map((q) => q.trim()).filter(Boolean);
      if (!base) {
        setConfig((prev) => ({ ...prev, queries: parsedQueries }));
        setFeedback({ type: "success", message: "Config saved (mock mode)" });
        return;
      }
      const body: Partial<SchedulerConfig> = {
        interval_minutes: config.interval_minutes,
        queries: parsedQueries,
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
        message: err instanceof Error ? err.message : "Failed to save config",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleRunNow = async () => {
    setIsRunning(true);
    setFeedback(null);
    try {
      const base = getApiBase();
      const res = await fetch(`${base}/api/v1/scheduler/run-now`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to run scheduler");
      const result = await res.json();
      setFeedback({
        type: "success",
        message: `Run complete: ${result.discovered_count || 0} discovered, ${result.errors?.length || 0} errors`,
      });
      const statusRes = await fetch(`${base}/api/v1/scheduler/status`);
      setStatus(await statusRes.json());
    } catch (err) {
      setFeedback({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to run scheduler",
      });
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="mb-8">
        <div className="flex items-center gap-2 text-[10px] font-mono text-neon-cyan/50 tracking-[0.2em] uppercase mb-2">
          <Settings size={12} className="text-neon-cyan" />
          <span>Configuration</span>
        </div>
        <h1 className="text-2xl font-display font-bold text-white tracking-wide">
          Settings
        </h1>
        <p className="text-sm font-sans text-gray-400 mt-1 font-light">
          Control the scheduler and system configuration
        </p>
      </div>

      {/* Scheduler Controls */}
      <Card glow="violet" className="p-6 mb-6">
        <div className="flex items-center gap-2 mb-6">
          <Activity size={14} className="text-neon-cyan" />
          <span className="text-[10px] font-mono text-neon-cyan/80 tracking-[0.2em] uppercase">
            Scheduler Controls
          </span>
        </div>

        {/* Feedback */}
        {feedback && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className={clsx(
              "mb-4 px-4 py-2.5 rounded-xl text-sm font-mono border",
              feedback.type === "success"
                ? "bg-neon-green/10 border-neon-green/25 text-neon-green"
                : "bg-neon-red/10 border-neon-red/25 text-neon-red",
            )}
          >
            {feedback.message}
          </motion.div>
        )}

        {/* Status */}
        {isLoading ? (
          <div className="glass rounded-xl p-4 mb-6">
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-neon-cyan/30 border-t-transparent rounded-full animate-spin" />
              <span className="text-sm font-mono text-gray-500">Loading scheduler status...</span>
            </div>
          </div>
        ) : (
          <div className="glass rounded-xl p-4 mb-6 flex items-center gap-3">
            <span className="relative flex h-3 w-3">
              <span
                className={clsx(
                  "animate-ping absolute inline-flex h-full w-full rounded-full opacity-75",
                  status?.is_running ? "bg-neon-green" : "bg-neon-red",
                )}
              />
              <span
                className={clsx(
                  "relative inline-flex rounded-full h-3 w-3",
                  status?.is_running ? "bg-neon-green" : "bg-neon-red",
                )}
              />
            </span>
            <span className="text-sm font-mono text-white">
              {status?.is_running ? "Running" : "Stopped"}
            </span>
            {status?.last_run && (
              <span className="text-xs font-mono text-gray-500 ml-auto flex items-center gap-1.5">
                <Clock size={12} />
                Last run: {new Date(status.last_run).toLocaleString()}
              </span>
            )}
          </div>
        )}

        {/* Controls */}
        <div className="flex gap-3 mb-6">
          <Button
            variant={status?.is_running ? "danger" : "success"}
            onClick={handleToggle}
            isLoading={isToggling}
          >
            {status?.is_running ? <Square size={16} /> : <Play size={16} />}
            {status?.is_running ? "Stop" : "Start"}
          </Button>
          <Button variant="secondary" onClick={handleRunNow} isLoading={isRunning}>
            <RefreshCw size={16} />
            Run Now
          </Button>
        </div>

        {/* Config */}
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
          <div className="glass rounded-xl p-4 self-end">
            <div className="flex items-center gap-3">
              <motion.button
                type="button"
                onClick={() =>
                  setConfig((prev) => ({
                    ...prev,
                    auto_generate_script: !prev.auto_generate_script,
                  }))
                }
                className={clsx(
                  "relative flex items-center w-12 h-7 rounded-full shrink-0 transition-colors duration-300 px-[3px]",
                  config.auto_generate_script
                    ? "bg-neon-violet justify-end"
                    : "bg-gray-700 justify-start",
                )}
                whileTap={{ scale: 0.95 }}
              >
                <motion.span
                  layout
                  className="w-[18px] h-[18px] rounded-full bg-white shadow-lg shrink-0"
                  transition={{
                    type: "spring" as const,
                    stiffness: 500,
                    damping: 28,
                  }}
                />
              </motion.button>
              <div>
                <p className="text-sm font-mono text-white">Auto-generate on approve</p>
                <p className="text-xs font-mono text-gray-500">
                  Automatically generate a script when approving a topic
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Queries */}
        <div className="mb-6">
          <label className="block mb-1.5 text-[10px] font-mono text-gray-400 uppercase tracking-[0.15em]">
            Queries (one per line)
          </label>
          <textarea
            value={queriesText}
            onChange={(e) => setQueriesText(e.target.value)}
            rows={4}
            className="w-full px-4 py-3 text-sm font-mono rounded-xl transition-all duration-300
              bg-glass-base backdrop-blur-xl border border-glass-border
              text-white placeholder-gray-500 resize-vertical
              focus:outline-none focus:border-neon-cyan/40 focus:bg-glass-light
              focus:shadow-[0_0_20px_rgba(0,229,255,0.08)]"
            placeholder="AI technology&#10;bitcoin news&#10;science discoveries"
          />
        </div>

        {/* Save */}
        <Button variant="primary" onClick={handleSaveConfig} isLoading={isSaving}>
          <Save size={16} />
          Save Config
        </Button>
      </Card>

      {/* Placeholder */}
      <Card className="p-16 flex flex-col items-center justify-center">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="flex flex-col items-center"
        >
          <div className="relative p-4 rounded-2xl bg-neon-yellow/10 border border-neon-yellow/20 mb-4">
            <Construction size={28} className="text-neon-yellow" />
          </div>
          <p className="text-sm font-mono text-gray-400">System Settings</p>
          <p className="text-xs font-mono text-gray-600 mt-1.5">
            Coming soon — source configuration, scoring weights, API keys.
          </p>
        </motion.div>
      </Card>
    </motion.div>
  );
}
