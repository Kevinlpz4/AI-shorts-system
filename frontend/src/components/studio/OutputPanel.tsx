"use client";

import { useScriptStudioStore } from "@/store/scriptStudioStore";
import { ScriptDisplay } from "./ScriptDisplay";
import { ScriptMetadata } from "./ScriptMetadata";
import { ActionButtons } from "./ActionButtons";
import { FileText, MousePointerClick } from "lucide-react";

/**
 * Right panel — Script output display.
 *
 * Shows the generated script, its metadata, and action buttons
 * (regenerate, accept, discard) when a script exists.
 * Shows contextual placeholders when no topic or no script is selected.
 */
export function OutputPanel() {
  const {
    selectedTopic,
    script,
    isGenerating,
    regenerateScript,
    acceptScript,
  } = useScriptStudioStore();

  // ── No topic selected ──
  if (!selectedTopic) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <MousePointerClick size={40} className="mb-3 opacity-30" />
        <p className="text-sm font-mono">No topic selected</p>
        <p className="text-xs font-mono text-gray-600 mt-1">
          Select a topic and configure your script
        </p>
      </div>
    );
  }

  // ── Topic selected but no script yet ──
  if (!script) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <FileText size={40} className="mb-3 opacity-30" />
        <p className="text-sm font-mono">Generate your first script</p>
        <p className="text-xs font-mono text-gray-600 mt-1 text-center">
          Configure the options on the left, then click{" "}
          <span className="text-cyber-cyan/80">&quot;Generate Script&quot;</span>
        </p>
      </div>
    );
  }

  // ── Script generated ──
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2 text-[10px] font-mono text-cyber-cyan/60 tracking-widest uppercase mb-3">
        <FileText size={12} />
        <span>Generated Script</span>
      </div>

      {/* Metadata bar */}
      <div className="mb-4">
        <ScriptMetadata script={script} />
      </div>

      {/* Scrollable script content */}
      <div className="flex-1 overflow-y-auto mb-4">
        <ScriptDisplay script={script} />
      </div>

      {/* Actions */}
      <div className="pt-3 border-t border-glass-border">
        <ActionButtons
          isGenerating={isGenerating}
          onRegenerate={regenerateScript}
          onAccept={acceptScript}
        />
      </div>
    </div>
  );
}
