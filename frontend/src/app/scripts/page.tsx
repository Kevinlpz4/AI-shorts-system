"use client";

import { ScriptsPage } from "@/components/scripts/ScriptsPage";
import { motion } from "framer-motion";
import { ScrollText } from "lucide-react";

export default function ScriptsRoute() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="mb-8">
        <div className="flex items-center gap-2 text-[10px] font-mono text-neon-cyan/50 tracking-[0.2em] uppercase mb-2">
          <ScrollText size={12} className="text-neon-cyan" />
          <span>Generated Scripts</span>
        </div>
        <h1 className="text-2xl font-display font-bold text-white tracking-wide">
          Scripts
        </h1>
        <p className="text-sm font-sans text-gray-400 mt-1 font-light">
          Browse and manage AI-generated video scripts
        </p>
      </div>

      <ScriptsPage />
    </motion.div>
  );
}
