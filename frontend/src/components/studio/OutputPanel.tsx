"use client";

import { useScriptStudioStore } from "@/store/scriptStudioStore";
import { ScriptDisplay } from "./ScriptDisplay";
import { ScriptMetadata } from "./ScriptMetadata";
import { ActionButtons } from "./ActionButtons";
import { FileText, MousePointerClick } from "lucide-react";

export function OutputPanel() {
  const {
    selectedTopic,
    script,
    isGenerating,
    regenerateScript,
    acceptScript,
  } = useScriptStudioStore();

  if (!selectedTopic) {
    return (
      <div className="glass rounded-xl p-12 flex flex-col items-center justify-center h-full">
        <MousePointerClick size={40} className="mb-3 opacity-30 text-gray-500" />
        <p className="text-sm font-mono text-gray-500">No topic selected</p>
        <p className="text-xs font-mono text-gray-600 mt-1">
          Select a topic and configure your script
        </p>
      </div>
    );
  }

  if (!script) {
    return (
      <div className="glass rounded-xl p-12 flex flex-col items-center justify-center h-full">
        <FileText size={40} className="mb-3 opacity-30 text-gray-500" />
        <p className="text-sm font-mono text-gray-500">Generate your first script</p>
        <p className="text-xs font-mono text-gray-600 mt-1 text-center">
          Configure the options on the left, then click{' '}
          <span className="text-neon-cyan/80">&quot;Generate Script&quot;</span>
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-1.5 text-[10px] font-mono text-neon-cyan/60 tracking-[0.2em] uppercase mb-3">
        <FileText size={12} className="text-neon-cyan" />
        <span>Generated Script</span>
      </div>

      <div className="mb-4">
        <ScriptMetadata script={script} />
      </div>

      <div className="flex-1 overflow-y-auto mb-4">
        <ScriptDisplay script={script} />
      </div>

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
