"use client";

import { useTopicStore } from "@/store/topicStore";
import { Card } from "@/components/ui/Card";
import { motion } from "framer-motion";
import { Compass, Clock, CheckCircle, XCircle, TrendingUp } from "lucide-react";

interface KPIItemProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  glow: "cyan" | "violet" | "magenta" | "green" | "red";
  accent: string;
}

function KPIItem({ label, value, icon, glow, accent }: KPIItemProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 100, damping: 20 }}
    >
      <Card glow={glow} className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-[10px] font-mono text-gray-400 uppercase tracking-[0.15em]">
              {label}
            </p>
            <div className="flex items-baseline gap-1 mt-2">
              <span className={`text-3xl font-display font-bold ${accent}`}>
                {value.toLocaleString()}
              </span>
              <TrendingUp size={16} className="text-neon-green/60" />
            </div>
          </div>
          <div className={`relative p-3 rounded-xl ${accent.replace("text-", "bg-").replace("font-bold", "")}/10 border border-current/10`}>
            <span className="absolute inset-0 bg-glass-shine rounded-xl" />
            <span className="relative">{icon}</span>
          </div>
        </div>
        {/* Micro bar */}
        <div className="mt-4 h-[2px] rounded-full bg-glass-base overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(100, value * 8)}%` }}
            transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
            className={`h-full rounded-full ${accent.replace("text-", "bg-")}`}
          />
        </div>
      </Card>
    </motion.div>
  );
}

export function KPIGrid() {
  const { kpiStats } = useTopicStore();

  const items = [
    {
      label: "Discovered",
      value: kpiStats.discovered,
      icon: <Compass size={22} className="text-neon-cyan" />,
      glow: "cyan" as const,
      accent: "text-neon-cyan font-bold",
    },
    {
      label: "Pending Review",
      value: kpiStats.pendingReview,
      icon: <Clock size={22} className="text-neon-yellow" />,
      glow: "violet" as const,
      accent: "text-neon-yellow font-bold",
    },
    {
      label: "Approved",
      value: kpiStats.approved,
      icon: <CheckCircle size={22} className="text-neon-green" />,
      glow: "green" as const,
      accent: "text-neon-green font-bold",
    },
    {
      label: "Rejected",
      value: kpiStats.rejected,
      icon: <XCircle size={22} className="text-neon-red" />,
      glow: "red" as const,
      accent: "text-neon-red font-bold",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {items.map((item, i) => (
        <KPIItem key={item.label} {...item} />
      ))}
    </div>
  );
}
