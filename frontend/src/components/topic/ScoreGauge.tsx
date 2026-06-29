"use client";

import clsx from "clsx";

/** Props de la barra de score individual */
interface ScoreGaugeProps {
  /** Valor actual (0-max) */
  value: number;
  /** Valor máximo (default: 10) */
  max?: number;
  /** Label de la barra */
  label: string;
  /** Tamaño: sm, md, lg */
  size?: "sm" | "md" | "lg";
  /** Color del glow: magenta, cyan, purple, green */
  color?: "magenta" | "cyan" | "purple" | "green";
}

const colorMap = {
  magenta: { bar: "bg-cyber-magenta", glow: "shadow-neon-magenta", track: "bg-cyber-magenta/10" },
  cyan: { bar: "bg-cyber-cyan", glow: "shadow-neon-cyan", track: "bg-cyber-cyan/10" },
  purple: { bar: "bg-cyber-purple", glow: "shadow-neon-purple", track: "bg-cyber-purple/10" },
  green: { bar: "bg-cyber-green", glow: "shadow-neon-green", track: "bg-cyber-green/10" },
};

const sizeMap = {
  sm: { bar: "h-1.5", text: "text-[10px]" },
  md: { bar: "h-2", text: "text-xs" },
  lg: { bar: "h-3", text: "text-sm" },
};

/**
 * Barra de progreso individual para un componente de score.
 * Con glow, animación y label. Usa colores del tema cyberpunk.
 */
export function ScoreGauge({
  value,
  max = 10,
  label,
  size = "md",
  color = "cyan",
}: ScoreGaugeProps) {
  const pct = Math.min(100, (value / max) * 100);
  const colors = colorMap[color];
  const sizes = sizeMap[size];

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className={clsx("font-mono text-gray-400 uppercase tracking-wider", sizes.text)}>
          {label}
        </span>
        <span className={clsx("font-display font-bold", sizes.text, colors.bar.replace("bg-", "text-"))}>
          {value.toFixed(1)}
        </span>
      </div>
      <div className={clsx("relative rounded-full overflow-hidden", colors.track, sizes.bar)}>
        <div
          className={clsx(
            "h-full rounded-full transition-all duration-1000 ease-out",
            colors.bar,
            colors.glow
          )}
          style={{ width: `${pct}%` }}
        >
          {/* Glow shine */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse-slow" />
        </div>
      </div>
    </div>
  );
}
