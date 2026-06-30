"use client";

import { useEffect, useState } from "react";
import { useScriptsStore } from "@/store/scriptsStore";
import { ScriptDetailPanel } from "@/components/scripts/ScriptDetailPanel";
import { ScriptListItem } from "@/components/scripts/ScriptListItem";
import { Loader2, AlertCircle, FileText } from "lucide-react";

/** Página de scripts generados — base para futura conversión a voz */
export function ScriptsPage() {
  const {
    scripts,
    selectedScript,
    isLoading,
    error,
    total,
    loadScripts,
    selectScript,
    clearSelection,
    clearError,
  } = useScriptsStore();

  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    loadScripts();
  }, [loadScripts]);

  const handleSelect = (id: string) => {
    const script = scripts.find((s) => s.id === id);
    if (script) {
      selectScript(script);
      setSelectedId(id);
    }
  };

  const handleClose = () => {
    clearSelection();
    setSelectedId(null);
  };

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-2 text-[10px] font-mono text-cyber-cyan/60 tracking-widest uppercase mb-1">
        <span className="w-2 h-2 rounded-full bg-cyber-cyan animate-glow-pulse" />
        <span>Scripts • Base para Conversión a Voz</span>
      </div>
      <h1 className="text-2xl font-display font-bold text-white tracking-wide mb-6">
        Generated Scripts
      </h1>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-cyber-cyan" />
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center h-64 gap-4">
          <AlertCircle className="w-12 h-12 text-cyber-red" />
          <p className="text-sm font-mono text-cyber-red">{error}</p>
          <button
            onClick={() => { clearError(); loadScripts(); }}
            className="px-4 py-2 rounded-lg bg-cyber-cyan/20 text-cyber-cyan text-sm font-mono hover:bg-cyber-cyan/30 transition-all"
          >
            Retry
          </button>
        </div>
      ) : scripts.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64">
          <FileText className="w-12 h-12 text-gray-500 mb-3" />
          <p className="text-sm font-mono text-gray-500">
            No scripts generated yet
          </p>
          <p className="text-xs font-mono text-gray-600 mt-1">
            Approve topics and generate scripts to see them here
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Script list */}
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-display font-semibold text-white tracking-wide">
                All Scripts
              </h2>
              <span className="text-[10px] font-mono text-gray-500">
                {total} total
              </span>
            </div>
            <div className="space-y-2">
              {scripts.map((script) => (
                <ScriptListItem
                  key={script.id}
                  script={script}
                  isSelected={selectedId === script.id}
                  onSelect={() => handleSelect(script.id)}
                />
              ))}
            </div>
          </div>

          {/* Detail panel */}
          <div className="lg:col-span-1">
            <div className="sticky top-24">
              <ScriptDetailPanel
                script={selectedScript}
                onClose={handleClose}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
