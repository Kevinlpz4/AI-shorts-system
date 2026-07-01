"use client";

import { Terminal } from "@/components/terminal/Terminal";
import { motion } from "framer-motion";
import { Terminal as TerminalIcon } from "lucide-react";

export default function TerminalPage() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="mb-8">
        <div className="flex items-center gap-2 text-[10px] font-mono text-neon-cyan/50 tracking-[0.2em] uppercase mb-2">
          <TerminalIcon size={12} className="text-neon-cyan" />
          <span>Developer Console</span>
        </div>
        <h1 className="text-2xl font-display font-bold text-white tracking-wide flex items-center gap-3">
          <TerminalIcon size={28} className="text-neon-cyan" />
          Terminal
        </h1>
        <p className="text-sm font-sans text-gray-400 mt-1 font-light ml-[40px]">
          Execute commands to manage topics, scripts, and system operations
        </p>
      </div>

      <Terminal />
    </motion.div>
  );
}
