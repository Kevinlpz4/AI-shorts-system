"use client";

import { Terminal } from "@/components/terminal/Terminal";
import { Terminal as TerminalIcon } from "lucide-react";

/** Página del terminal de desarrollo con comandos para gestionar topics y scripts */
export default function TerminalPage() {
  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-2 text-[10px] font-mono text-cyber-cyan/60 tracking-widest uppercase mb-1">
        <span className="w-2 h-2 rounded-full bg-cyber-cyan animate-glow-pulse" />
        <span>Developer Console</span>
      </div>
      <h1 className="text-2xl font-display font-bold text-white tracking-wide mb-6 flex items-center gap-3">
        <TerminalIcon size={28} className="text-cyber-cyan" />
        Terminal
      </h1>

      {/* Terminal component */}
      <Terminal />
    </div>
  );
}
