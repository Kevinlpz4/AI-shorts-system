"use client";

import { Search, Bell, RefreshCw } from "lucide-react";
import { useTopicStore } from "@/store/topicStore";
import { useState } from "react";

/**
 * Header del dashboard con buscador, botón Discover y notificaciones.
 *
 * Sticky top, glassmorphism. Incluye el input de búsqueda que también
 * dispara discover al presionar Enter.
 */
export function Header() {
  const { discoverTopics, isDiscovering } = useTopicStore();
  const [searchValue, setSearchValue] = useState("");

  const handleDiscover = async () => {
    await discoverTopics(searchValue || undefined);
  };

  return (
    <header className="sticky top-0 z-30 border-b border-glass-border bg-cyber-black/80 backdrop-blur-xl">
      <div className="flex items-center justify-between h-16 px-6">
        {/* Left: Page title */}
        <div>
          <h2 className="text-lg font-display font-bold text-white tracking-wide">
            Dashboard
          </h2>
          <p className="text-[11px] font-mono text-gray-500">
            Real-time topic monitoring
          </p>
        </div>

        {/* Center: Search + Discover */}
        <div className="flex items-center gap-3 flex-1 max-w-lg mx-6">
          <div className="relative flex-1">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"
            />
            <input
              type="text"
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleDiscover()}
              placeholder="Search topics or discover..."
              className="w-full bg-cyber-dark/60 border border-glass-border rounded-lg pl-10 pr-3 py-2 text-sm font-mono text-white placeholder-gray-500 focus:outline-none focus:border-cyber-cyan/50 focus:ring-1 focus:ring-cyber-cyan/30 transition-all"
            />
          </div>
          <button
            onClick={handleDiscover}
            disabled={isDiscovering}
            className="flex items-center gap-2 px-4 py-2 bg-cyber-cyan/10 border border-cyber-cyan/30 rounded-lg text-cyber-cyan text-sm font-mono hover:bg-cyber-cyan/20 transition-all disabled:opacity-50"
          >
            <RefreshCw
              size={16}
              className={isDiscovering ? "animate-spin" : ""}
            />
            {isDiscovering ? "Scanning..." : "Discover"}
          </button>
        </div>

        {/* Right: Notifications */}
        <div className="flex items-center gap-2">
          <button className="relative p-2 rounded-lg text-gray-400 hover:text-white hover:bg-glass-white transition-all">
            <Bell size={18} />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-cyber-magenta animate-glow-pulse" />
          </button>
          <div className="w-8 h-8 rounded-lg bg-cyber-purple/20 border border-cyber-purple/30 flex items-center justify-center">
            <span className="text-xs font-mono text-cyber-purple font-bold">
              OP
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
