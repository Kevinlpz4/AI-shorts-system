"use client";

import { Card } from "@/components/ui/Card";
import { motion } from "framer-motion";
import { BarChart3, Construction } from "lucide-react";

export default function AnalyticsPage() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="mb-8">
        <div className="flex items-center gap-2 text-[10px] font-mono text-neon-cyan/50 tracking-[0.2em] uppercase mb-2">
          <BarChart3 size={12} className="text-neon-cyan" />
          <span>Data &amp; Insights</span>
        </div>
        <h1 className="text-2xl font-display font-bold text-white tracking-wide">
          Analytics
        </h1>
        <p className="text-sm font-sans text-gray-400 mt-1 font-light">
          Score trends, source performance, and more
        </p>
      </div>

      <Card className="p-16 flex flex-col items-center justify-center">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="flex flex-col items-center"
        >
          <div className="relative p-4 rounded-2xl bg-neon-yellow/10 border border-neon-yellow/20 mb-4">
            <Construction size={28} className="text-neon-yellow" />
          </div>
          <p className="text-sm font-mono text-gray-400">Analytics Dashboard</p>
          <p className="text-xs font-mono text-gray-600 mt-1.5">
            Coming soon — score trends, source performance, and more.
          </p>
        </motion.div>
      </Card>
    </motion.div>
  );
}
