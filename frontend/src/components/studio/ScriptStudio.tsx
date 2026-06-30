"use client";

import { useEffect } from "react";
import { useScriptStudioStore } from "@/store/scriptStudioStore";
import { StudioLayout } from "./StudioLayout";
import { Loader2, AlertCircle, Inbox } from "lucide-react";

/**
 * Container component for the Script Studio.
 *
 * Loads approved topics on mount and handles loading / error / empty states
 * before delegating to the 3-column StudioLayout.
 */
export function ScriptStudio() {
  const { approvedTopics, isLoading, error, loadApprovedTopics, clearError } =
    useScriptStudioStore();

  useEffect(() => {
    loadApprovedTopics();
  }, [loadApprovedTopics]);

  // ── Loading (initial) ──
  if (isLoading && approvedTopics.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-500">
        <Loader2 size={32} className="animate-spin text-cyber-cyan mb-4" />
        <p className="text-sm font-mono">Loading approved topics...</p>
      </div>
    );
  }

  // ── Error ──
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertCircle size={32} className="text-cyber-red mb-4" />
        <p className="text-sm font-mono text-cyber-red mb-2">
          Error loading topics
        </p>
        <p className="text-xs font-mono text-gray-500">{error}</p>
        <button
          onClick={clearError}
          className="mt-4 px-4 py-2 bg-glass-white border border-glass-border rounded-lg text-xs font-mono text-gray-300 hover:text-white transition-all"
        >
          Dismiss
        </button>
      </div>
    );
  }

  // ── Empty ──
  if (approvedTopics.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-500">
        <Inbox size={32} className="mb-4" />
        <p className="text-sm font-mono">No approved topics waiting for scripts</p>
        <p className="text-xs font-mono text-gray-600 mt-1">
          Approve topics from the review panel to start generating scripts
        </p>
      </div>
    );
  }

  // ── Ready ──
  return <StudioLayout />;
}
