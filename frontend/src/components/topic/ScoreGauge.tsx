"use client";

import clsx from "clsx";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";

interface ScoreGaugeProps {
  value: number;
  max?: number;
  label: string;
  size?: "sm" | "md" | "lg";
  color?: "magenta" | "cyan" | "purple" | "green";
}

const colorMap = {
  magenta: { bar: "bg-neon-magenta", track: "bg-neon-magenta/10" },
  cyan: { bar: "bg-neon-cyan", track: "bg-neon-cyan/10" },
  purple: { bar: "bg-neon-violet", track: "bg-neon-violet/10" },
  green: { bar: "bg-neon-green", track: "bg-neon-green/10" },
};

const sizeMap = {
  sm: { bar: "h-1.5", text: "text-[10px]" },
  md: { bar: "h-2", text: "text-xs" },
  lg: { bar: "h-3", text: "text-sm" },
};

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
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => setWidth(pct), 100);
    return () => clearTimeout(timer);
  }, [pct]);

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className={clsx("font-mono text-gray-400 uppercase tracking-[0.15em]", sizes.text)}>
          {label}
        </span>
        <span className={clsx("font-display font-bold", sizes.text, colors.bar.replace("bg-", "text-"))}>
          {value.toFixed(1)}
        </span>
      </div>
      <div className={clsx("relative rounded-full overflow-hidden bg-glass-base", sizes.bar)}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${width}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className={clsx("h-full rounded-full relative overflow-hidden", colors.bar)}
          style={{
            boxShadow: `0 0 8px ${
              color === "cyan"
                ? "rgba(0,229,255,0.3)"
                : color === "magenta"
                  ? "rgba(236,72,153,0.3)"
                  : color === "purple"
                    ? "rgba(124,58,237,0.3)"
                    : "rgba(52,211,153,0.3)"
            }`,
          }}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse-slow" />
        </motion.div>
      </div>
    </div>
  );
}
