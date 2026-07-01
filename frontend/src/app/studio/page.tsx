"use client";

import { ScriptStudio } from "@/components/studio/ScriptStudio";
import { motion } from "framer-motion";
import { Film } from "lucide-react";

export default function StudioPage() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="mb-8">
        <div className="flex items-center gap-2 text-[10px] font-mono text-neon-cyan/50 tracking-[0.2em] uppercase mb-2">
          <Film size={12} className="text-neon-cyan" />
          <span>Script Studio</span>
        </div>
        <h1 className="text-2xl font-display font-bold text-white tracking-wide">
          Studio
        </h1>
        <p className="text-sm font-sans text-gray-400 mt-1 font-light">
          Generate and refine AI-powered video scripts
        </p>
      </div>

      <ScriptStudio />
    </motion.div>
  );
}
