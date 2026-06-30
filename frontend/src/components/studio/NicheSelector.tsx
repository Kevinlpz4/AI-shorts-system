"use client";

import clsx from "clsx";
import { CheckCircle2, Target } from "lucide-react";
import { Select } from "@/components/ui/Select";

/** Props for the niche selector */
interface NicheSelectorProps {
  /** Currently selected niche */
  value: string;
  /** Called when the user picks a niche */
  onChange: (niche: string) => void;
  /** Recommended niche from the system (optional) */
  recommended?: string;
}

const NICHE_OPTIONS = [
  { value: "tecnología", label: "Tecnología" },
  { value: "negocios", label: "Negocios" },
  { value: "salud", label: "Salud" },
  { value: "educación", label: "Educación" },
  { value: "finanzas", label: "Finanzas" },
] as const;

/**
 * Niche selector — dropdown select with an optional recommended badge.
 *
 * Uses the existing Select component for consistency with the rest of the app.
 */
export function NicheSelector({
  value,
  onChange,
  recommended,
}: NicheSelectorProps) {
  const recommendedLabel = NICHE_OPTIONS.find(
    (o) => o.value === recommended,
  )?.label;

  return (
    <div>
      <div className="flex items-center gap-2 text-xs font-mono text-gray-400 uppercase tracking-wider mb-3">
        <Target size={14} />
        <span>Niche</span>
      </div>

      <div className="relative">
        <Select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          options={NICHE_OPTIONS.map((o) => ({
            value: o.value,
            label: o.label,
          }))}
        />

        {/* Recommended badge */}
        {recommended && recommended !== value && (
          <div className="mt-2 flex items-center gap-1.5 text-[10px] font-mono text-cyber-green">
            <CheckCircle2 size={10} />
            <span>
              Recommended: <strong>{recommendedLabel}</strong>
            </span>
          </div>
        )}

        {recommended && recommended === value && (
          <div className="mt-2 flex items-center gap-1.5 text-[10px] font-mono text-cyber-green">
            <CheckCircle2 size={10} />
            <span>Using recommended niche</span>
          </div>
        )}
      </div>
    </div>
  );
}
