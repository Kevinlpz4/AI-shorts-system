"use client";

import clsx from "clsx";
import { CheckCircle2, Clock } from "lucide-react";

/** Props for the duration selector */
interface DurationSelectorProps {
  /** Currently selected duration in seconds */
  value: number;
  /** Called when the user picks a duration */
  onChange: (duration: number) => void;
  /** Recommended duration from the system (optional) */
  recommended?: number;
}

const DURATION_OPTIONS = [
  { value: 30, label: "30s", description: "Quick hit" },
  { value: 60, label: "60s", description: "Standard" },
  { value: 90, label: "90s", description: "Deep dive" },
] as const;

/**
 * Duration selector — three clickable cards for 30s / 60s / 90s.
 *
 * Highlights the selected option and shows a "Recommended" badge
 * if the system recommendation matches an option.
 */
export function DurationSelector({
  value,
  onChange,
  recommended,
}: DurationSelectorProps) {
  return (
    <div>
      <div className="flex items-center gap-2 text-xs font-mono text-gray-400 uppercase tracking-wider mb-3">
        <Clock size={14} />
        <span>Duration</span>
      </div>

      <div className="grid grid-cols-3 gap-2">
        {DURATION_OPTIONS.map((opt) => {
          const isSelected = value === opt.value;
          const isRecommended = recommended === opt.value;

          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => onChange(opt.value)}
              className={clsx(
                "relative flex flex-col items-center gap-1 p-3 rounded-lg border transition-all duration-200",
                "text-xs font-mono",
                isSelected
                  ? "border-cyber-cyan/60 bg-cyber-cyan/10 text-cyber-cyan shadow-neon-cyan"
                  : "border-glass-border bg-glass-white text-gray-400 hover:border-gray-500 hover:text-gray-300",
              )}
            >
              {/* Recommended badge */}
              {isRecommended && (
                <span className="absolute -top-2 -right-2 flex items-center gap-0.5 px-1.5 py-0.5 text-[9px] font-mono rounded-full bg-cyber-green/20 text-cyber-green border border-cyber-green/30">
                  <CheckCircle2 size={8} />
                  Rec
                </span>
              )}

              <span className="text-sm font-display font-bold">{opt.label}</span>
              <span className="text-[10px] opacity-70">{opt.description}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
