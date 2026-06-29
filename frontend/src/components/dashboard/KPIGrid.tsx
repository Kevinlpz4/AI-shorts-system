"use client";

import { useEffect } from "react";
import { useTopicStore } from "@/store/topicStore";
import { Card } from "@/components/ui/Card";
import { Compass, Clock, CheckCircle, XCircle } from "lucide-react";
import clsx from "clsx";

/** Props de cada item individual de KPI */
interface KPIItemProps {
  /** Label del KPI */
  label: string;
  /** Valor numérico */
  value: number;
  /** Icono SVG */
  icon: React.ReactNode;
  /** Clase de color de texto */
  color: string;
  /** Color del glow en la Card */
  glow: "magenta" | "cyan" | "purple" | "green" | "red";
}

function KPIItem({ label, value, icon, color, glow }: KPIItemProps) {
  return (
    <Card glow={glow} className="p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-mono text-gray-400 uppercase tracking-wider">
            {label}
          </p>
          <p
            className={clsx(
              "mt-2 text-3xl font-display font-bold",
              color
            )}
          >
            {value.toLocaleString()}
          </p>
        </div>
        <div className={clsx("p-3 rounded-lg bg-opacity-20", color.replace("text-", "bg-").replace("font-", "") + "/10")}>
          {icon}
        </div>
      </div>
      {/* Minibar */}
      <div className="mt-4 h-1 rounded-full bg-glass-white overflow-hidden">
        <div
          className={clsx(
            "h-full rounded-full transition-all duration-500",
            color.replace("text-", "bg-")
          )}
          style={{ width: `${Math.min(100, value * 10)}%` }}
        />
      </div>
    </Card>
  );
}

/**
 * Grid de KPIs (Discovered, Pending Review, Approved, Rejected).
 * Carga datos del store al montarse y muestra mini-barras de progreso.
 */
export function KPIGrid() {
  const { kpiStats, loadTopics } = useTopicStore();

  useEffect(() => {
    loadTopics();
  }, [loadTopics]);

  const items = [
    {
      label: "Discovered",
      value: kpiStats.discovered,
      icon: <Compass size={22} className="text-cyber-cyan" />,
      color: "text-cyber-cyan",
      glow: "cyan" as const,
    },
    {
      label: "Pending Review",
      value: kpiStats.pendingReview,
      icon: <Clock size={22} className="text-cyber-yellow" />,
      color: "text-cyber-yellow",
      glow: "purple" as const,
    },
    {
      label: "Approved",
      value: kpiStats.approved,
      icon: <CheckCircle size={22} className="text-cyber-green" />,
      color: "text-cyber-green",
      glow: "green" as const,
    },
    {
      label: "Rejected",
      value: kpiStats.rejected,
      icon: <XCircle size={22} className="text-cyber-red" />,
      color: "text-cyber-red",
      glow: "red" as const,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {items.map((item) => (
        <KPIItem key={item.label} {...item} />
      ))}
    </div>
  );
}
