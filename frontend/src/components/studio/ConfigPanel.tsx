"use client";

import { useScriptStudioStore } from "@/store/scriptStudioStore";
import { DurationSelector } from "./DurationSelector";
import { ToneSelector } from "./ToneSelector";
import { NicheSelector } from "./NicheSelector";
import { Button } from "@/components/ui/Button";
import { Sliders, Sparkles, Loader2 } from "lucide-react";

/**
 * Center panel — Configuration for script generation.
 *
 * Shows the selected topic title and lets the user configure
 * duration, tone, and niche before generating a script.
 */
export function ConfigPanel() {
  const {
    selectedTopic,
    recommendations,
    config,
    isGenerating,
    setConfig,
    generateScript,
  } = useScriptStudioStore();

  // ── No topic selected ──
  if (!selectedTopic) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <Sliders size={40} className="mb-3 opacity-30" />
        <p className="text-sm font-mono">Select a topic to configure</p>
        <p className="text-xs font-mono text-gray-600 mt-1">
          Choose a topic from the queue to get started
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center gap-2 text-[10px] font-mono text-cyber-cyan/60 tracking-widest uppercase mb-1">
          <Sparkles size={12} />
          <span>Script Configuration</span>
        </div>
        <h2 className="text-base font-display font-bold text-white leading-snug line-clamp-2">
          {selectedTopic.title}
        </h2>
      </div>

      <div className="flex-1 space-y-6">
        {/* Duration */}
        <DurationSelector
          value={config.duration}
          onChange={(v) => setConfig({ duration: v })}
          recommended={recommendations?.duration}
        />

        {/* Tone */}
        <ToneSelector
          value={config.tone}
          onChange={(v) => setConfig({ tone: v })}
          recommended={recommendations?.tone}
        />

        {/* Niche */}
        <NicheSelector
          value={config.niche}
          onChange={(v) => setConfig({ niche: v })}
          recommended={recommendations?.niche}
        />
      </div>

      {/* Generate button */}
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
            <>
              <Loader2 size={16} className="animate-spin" />
              Generating...
            </>
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
