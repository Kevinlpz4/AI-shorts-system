"use client";

import clsx from "clsx";
import { CheckCircle2, Music } from "lucide-react";

/** Props for the tone selector */
interface ToneSelectorProps {
  /** Currently selected tone */
  value: string;
  /** Called when the user picks a tone */
  onChange: (tone: string) => void;
  /** Recommended tone from the system (optional) */
  recommended?: string;
}

const TONE_OPTIONS = [
  { value: "educational", label: "Educational", icon: "📚" },
  { value: "controversial", label: "Controversial", icon: "⚡" },
  { value: "informative", label: "Informative", icon: "📰" },
  { value: "entertaining", label: "Entertaining", icon: "🎬" },
  { value: "inspirational", label: "Inspirational", icon: "✨" },
] as const;

/**
 * Tone selector — clickable chips for each tone option.
 *
 * Highlights the selected chip and shows a "Recommended" badge
 * on the system-recommended tone.
 */
export function ToneSelector({
  value,
  onChange,
  recommended,
}: ToneSelectorProps) {
  return (
    <div>
      <div className="flex items-center gap-2 text-xs font-mono text-gray-400 uppercase tracking-wider mb-3">
        <Music size={14} />
        <span>Tone</span>
      </div>

      <div className="flex flex-wrap gap-2">
        {TONE_OPTIONS.map((opt) => {
          const isSelected = value === opt.value;
          const isRecommended = recommended === opt.value;

          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => onChange(opt.value)}
              className={clsx(
                "relative inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border transition-all duration-200",
                "text-xs font-mono",
                isSelected
                  ? "border-cyber-cyan/60 bg-cyber-cyan/10 text-cyber-cyan"
                  : "border-glass-border bg-glass-white text-gray-400 hover:border-gray-500 hover:text-gray-300",
              )}
            >
              {isRecommended && (
                <span className="absolute -top-1.5 -right-1.5">
                  <CheckCircle2
                    size={10}
                    className="text-cyber-green"
                  />
                </span>
              )}
              <span className="text-sm">{opt.icon}</span>
              <span>{opt.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
