"use client";

import { ScoreComponents } from "@/types";
import { ScoreGauge } from "@/components/topic/ScoreGauge";

/** Props del radar de score visual */
interface ScoreRadarProps {
  /** Componentes individuales del score */
  score: ScoreComponents;
  /** Score total (0-10) */
  total: number;
  /** Tamaño del radar */
  size?: "sm" | "md";
}

/**
 * Radar visual de score con círculo SVG de progreso + barras individuales.
 * El color cambia según el valor: verde (≥7), amarillo (≥5), rojo (<5).
 */
export function ScoreRadar({ score, total, size = "md" }: ScoreRadarProps) {
  const items = [
    { label: "Relevance", value: score.relevance, color: "magenta" as const },
    { label: "Popularity", value: score.popularity, color: "cyan" as const },
    { label: "Recency", value: score.recency, color: "purple" as const },
    { label: "Reliability", value: score.reliability, color: "green" as const },
  ];

  return (
    <div className="space-y-4">
      {/* Score total circular */}
      <div className="flex justify-center mb-4">
        <div className="relative">
          <svg className="w-24 h-24 -rotate-90" viewBox="0 0 100 100">
            {/* Track */}
            <circle
              cx="50"
              cy="50"
              r="42"
              fill="none"
              stroke="rgba(255,255,255,0.05)"
              strokeWidth="6"
            />
            {/* Progress */}
            <circle
              cx="50"
              cy="50"
              r="42"
              fill="none"
              stroke={
                total >= 7 ? "#00FF88" : total >= 5 ? "#FFD700" : "#FF3355"
              }
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={`${(total / 10) * 264} 264`}
              className="transition-all duration-1000"
              style={{
                filter: `drop-shadow(0 0 6px ${
                  total >= 7
                    ? "rgba(0,255,136,0.5)"
                    : total >= 5
                    ? "rgba(255,215,0,0.5)"
                    : "rgba(255,51,85,0.5)"
                })`,
              }}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <p
                className={`text-2xl font-display font-bold ${
                  total >= 7
                    ? "text-cyber-green"
                    : total >= 5
                    ? "text-cyber-yellow"
                    : "text-cyber-red"
                }`}
              >
                {total.toFixed(1)}
              </p>
              <p className="text-[8px] font-mono text-gray-500 uppercase tracking-widest">
                Score
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Barras individuales */}
      <div className="space-y-3">
        {items.map((item) => (
          <ScoreGauge
            key={item.label}
            label={item.label}
            value={item.value}
            max={10}
            color={item.color}
            size={size === "sm" ? "sm" : "md"}
          />
        ))}
      </div>
    </div>
  );
}
