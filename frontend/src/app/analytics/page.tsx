"use client";

import { Card } from "@/components/ui/Card";
import { BarChart3, Construction } from "lucide-react";

/** Página de analytics y métricas (placeholder — coming soon) */
export default function AnalyticsPage() {
  return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-2 text-[10px] font-mono text-cyber-cyan/60 tracking-widest uppercase mb-1">
        <span className="w-2 h-2 rounded-full bg-cyber-cyan animate-glow-pulse" />
        <span>Data & Insights</span>
      </div>
      <h1 className="text-2xl font-display font-bold text-white tracking-wide mb-6">
        Analytics
      </h1>

      <Card className="p-12 flex flex-col items-center justify-center text-gray-500">
        <BarChart3 size={48} className="mb-4 opacity-30" />
        <Construction size={24} className="mb-2 text-cyber-yellow" />
        <p className="text-sm font-mono">Analytics Dashboard</p>
        <p className="text-xs font-mono text-gray-600 mt-1">
          Coming soon — score trends, source performance, and more.
        </p>
      </Card>
    </div>
  );
}
