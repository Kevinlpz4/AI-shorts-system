"use client";

import { useEffect, useState } from "react";
import { useScriptsStore } from "@/store/scriptsStore";
import { ScriptDetailPanel } from "@/components/scripts/ScriptDetailPanel";
import { ScriptListItem } from "@/components/scripts/ScriptListItem";
import { motion } from "framer-motion";
import { Loader2, AlertCircle, FileText } from "lucide-react";

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

  // ── Loading ──
  if (isLoading) {
    return (
      <div className="glass rounded-xl p-12 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Loader2 size={28} className="animate-spin text-neon-cyan" />
          <p className="text-sm font-mono text-gray-500">Loading scripts...</p>
        </div>
      </div>
    );
  }

  // ── Error ──
  if (error) {
    return (
      <div className="glass rounded-xl p-12">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center justify-center gap-4"
        >
          <AlertCircle size={32} className="text-neon-red" />
          <p className="text-sm font-mono text-neon-red">{error}</p>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => { clearError(); loadScripts(); }}
            className="px-5 py-2.5 glass rounded-xl text-xs font-mono text-gray-300 hover:text-white transition-all"
          >
            Retry
          </motion.button>
        </motion.div>
      </div>
    );
  }

  // ── Empty ──
  if (scripts.length === 0) {
    return (
      <div className="glass rounded-xl p-12">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center"
        >
          <FileText size={32} className="text-gray-500 mb-3" />
          <p className="text-sm font-mono text-gray-500">No scripts generated yet</p>
          <p className="text-xs font-mono text-gray-600 mt-1">
            Approve topics and generate scripts to see them here
          </p>
        </motion.div>
      </div>
    );
  }

  // ── Scripts ──
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Script list */}
      <div className="lg:col-span-2">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-display font-semibold text-white tracking-wide">
            All Scripts
          </h2>
          <span className="text-[10px] font-mono text-gray-500">{total} total</span>
        </div>
        <div className="space-y-2">
          {scripts.map((script, i) => (
            <motion.div
              key={script.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
            >
              <ScriptListItem
                script={script}
                isSelected={selectedId === script.id}
                onSelect={() => handleSelect(script.id)}
              />
            </motion.div>
          ))}
        </div>
      </div>

      {/* Detail panel */}
      <div className="lg:col-span-1">
        <div className="sticky top-24">
          <motion.div
            key={selectedId || "empty"}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ type: "spring", stiffness: 100, damping: 20 }}
          >
            <ScriptDetailPanel
              script={selectedScript}
              onClose={handleClose}
            />
          </motion.div>
        </div>
      </div>
    </div>
  );
}
