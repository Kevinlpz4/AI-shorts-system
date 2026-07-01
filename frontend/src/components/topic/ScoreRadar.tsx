"use client";

import { ScoreComponents } from "@/types";
import { ScoreGauge } from "@/components/topic/ScoreGauge";

/** Props del radar de score visual */
interface ScoreRadarProps {
  /** Componentes individuales del score */
  score: ScoreComponents;
  /** Score total (0-100) */
  total: number;
  /** Tamaño del radar */
  size?: "sm" | "md";
}

/**
 * Radar visual de score con círculo SVG de progreso + barras individuales.
 * Escala 0-100 alineada con el backend.
 * El color cambia según el valor: verde (≥70), amarillo (≥50), rojo (<50).
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
                total >= 70 ? "#34D399" : total >= 50 ? "#FBBF24" : "#FB7185"
              }
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={`${(total / 100) * 264} 264`}
              className="transition-all duration-1000"
              style={{
                filter: `drop-shadow(0 0 10px ${
                  total >= 70
                    ? "rgba(52,211,153,0.4)"
                    : total >= 50
                    ? "rgba(251,191,36,0.4)"
                    : "rgba(251,113,133,0.4)"
                })`,
              }}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <p
                className={`text-2xl font-display font-bold ${
                  total >= 70
                    ? "text-neon-green"
                    : total >= 50
                    ? "text-neon-yellow"
                    : "text-neon-red"
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
            max={100}
            color={item.color}
            size={size === "sm" ? "sm" : "md"}
          />
        ))}
      </div>
    </div>
  );
}
