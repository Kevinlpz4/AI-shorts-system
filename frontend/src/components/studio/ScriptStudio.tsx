"use client";

import { useEffect } from "react";
import { useScriptStudioStore } from "@/store/scriptStudioStore";
import { StudioLayout } from "./StudioLayout";
import { motion } from "framer-motion";
import { Loader2, AlertCircle, Inbox } from "lucide-react";

export function ScriptStudio() {
  const { approvedTopics, isLoading, error, loadApprovedTopics, clearError } =
    useScriptStudioStore();

  useEffect(() => {
    loadApprovedTopics();
  }, [loadApprovedTopics]);

  // ── Loading ──
  if (isLoading && approvedTopics.length === 0) {
    return (
      <div className="glass rounded-xl p-12 flex flex-col items-center justify-center gap-4">
        <Loader2 size={28} className="animate-spin text-neon-cyan" />
        <p className="text-sm font-mono text-gray-500">Loading approved topics...</p>
      </div>
    );
  }

  // ── Error ──
  if (error && approvedTopics.length === 0) {
    return (
      <div className="glass rounded-xl p-12">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center gap-4"
        >
          <AlertCircle size={32} className="text-neon-red" />
          <p className="text-sm font-mono text-neon-red">{error}</p>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => { clearError(); loadApprovedTopics(); }}
            className="px-5 py-2.5 glass rounded-xl text-xs font-mono text-gray-300 hover:text-white transition-all"
          >
            Retry
          </motion.button>
        </motion.div>
      </div>
    );
  }

  // ── Empty ──
  if (approvedTopics.length === 0) {
    return (
      <div className="glass rounded-xl p-12">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center"
        >
          <div className="relative p-4 rounded-2xl bg-glass-strong border border-glass-border mb-4">
            <Inbox size={28} className="text-gray-500" />
          </div>
          <p className="text-sm font-mono text-gray-500">No approved topics</p>
          <p className="text-xs font-mono text-gray-600 mt-1.5">
            Approve topics from the Dashboard to start generating scripts
          </p>
        </motion.div>
      </div>
    );
  }

  return <StudioLayout />;
}
