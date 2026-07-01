"use client";

import { useScriptStudioStore } from "@/store/scriptStudioStore";
import { DurationSelector } from "./DurationSelector";
import { ToneSelector } from "./ToneSelector";
import { NicheSelector } from "./NicheSelector";
import { Button } from "@/components/ui/Button";
import { Sliders, Sparkles } from "lucide-react";

export function ConfigPanel() {
  const {
    selectedTopic,
    recommendations,
    config,
    isGenerating,
    setConfig,
    generateScript,
  } = useScriptStudioStore();

  if (!selectedTopic) {
    return (
      <div className="glass rounded-xl p-12 flex flex-col items-center justify-center h-full">
        <Sliders size={40} className="mb-3 opacity-30 text-gray-500" />
        <p className="text-sm font-mono text-gray-500">Select a topic to configure</p>
        <p className="text-xs font-mono text-gray-600 mt-1">
          Choose a topic from the queue to get started
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="mb-4">
        <div className="flex items-center gap-1.5 text-[10px] font-mono text-neon-cyan/60 tracking-[0.2em] uppercase mb-1">
          <Sparkles size={12} className="text-neon-cyan" />
          <span>Script Configuration</span>
        </div>
        <h2 className="text-base font-display font-bold text-white leading-snug line-clamp-2">
          {selectedTopic.title}
        </h2>
      </div>

      <div className="flex-1 space-y-6">
        <DurationSelector
          value={config.duration}
          onChange={(v) => setConfig({ duration: v })}
          recommended={recommendations?.duration}
        />
        <ToneSelector
          value={config.tone}
          onChange={(v) => setConfig({ tone: v })}
          recommended={recommendations?.tone}
        />
        <NicheSelector
          value={config.niche}
          onChange={(v) => setConfig({ niche: v })}
          recommended={recommendations?.niche}
        />
      </div>

      <div className="mt-6 pt-4 border-t border-glass-border">
        <Button
          variant="secondary"
          size="lg"
          isLoading={isGenerating}
          disabled={isGenerating}
          onClick={generateScript}
          className="w-full"
          glow
        >
          {isGenerating ? (
            <>Generating...</>
          ) : (
            <>
              <Sparkles size={16} />
              Generate Script
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
