"use client";

import { Search, Bell, RefreshCw } from "lucide-react";
import { useTopicStore } from "@/store/topicStore";
import { useState } from "react";
import { motion } from "framer-motion";

/**
 * Header del dashboard — glassmorphism, sticky, con buscador y controles.
 */
export function Header() {
  const { discoverTopics, isDiscovering } = useTopicStore();
  const [searchValue, setSearchValue] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);

  const handleDiscover = async () => {
    await discoverTopics(searchValue || undefined);
  };

  return (
    <header className="sticky top-0 z-30">
      {/* Glass background */}
      <div className="absolute inset-0 backdrop-blur-2xl bg-base-900/70 border-b border-glass-border" />
      <div className="absolute inset-0 bg-layer-noise pointer-events-none" />

      <div className="relative flex items-center justify-between h-16 px-6 lg:px-8">
        {/* Left: Page title — populated by pages */}
        <div id="page-header" />

        {/* Center: Search + Discover */}
        <div className="flex items-center gap-3 flex-1 max-w-lg mx-auto lg:mx-6">
          <motion.div
            className="relative flex-1"
            animate={searchFocused ? { scale: 1.02 } : { scale: 1 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
          >
            <Search
              size={16}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500"
            />
            <input
              type="text"
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleDiscover()}
              onFocus={() => setSearchFocused(true)}
              onBlur={() => setSearchFocused(false)}
              placeholder="Search topics or discover..."
              className="w-full h-10 pl-10 pr-3 text-sm font-mono rounded-xl transition-all duration-300
                bg-glass-base backdrop-blur-xl
                border border-glass-border
                text-white placeholder-gray-500
                focus:outline-none focus:border-neon-cyan/40 focus:bg-glass-light
                focus:shadow-[0_0_20px_rgba(0,229,255,0.08)]"
            />
          </motion.div>
          <motion.button
            onClick={handleDiscover}
            disabled={isDiscovering}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            className="flex items-center gap-2 h-10 px-4 rounded-xl text-sm font-mono font-medium
              bg-neon-cyan/10 border border-neon-cyan/25 text-neon-cyan
              hover:bg-neon-cyan/20 hover:shadow-[0_0_20px_rgba(0,229,255,0.12)]
              transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw
              size={16}
              className={isDiscovering ? "animate-spin" : ""}
            />
            {isDiscovering ? "Scanning..." : "Discover"}
          </motion.button>
        </div>

        {/* Right: Notifications + Avatar */}
        <div className="flex items-center gap-3">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="relative p-2.5 rounded-xl text-gray-400 hover:text-white transition-all duration-300
              bg-glass-base hover:bg-glass-light border border-transparent hover:border-glass-border"
          >
            <Bell size={18} />
            <span className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-neon-magenta">
              <span className="absolute inline-flex w-full h-full rounded-full bg-neon-magenta opacity-75 animate-ping" />
            </span>
          </motion.button>
          <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-neon-violet/30 to-neon-magenta/20 border border-neon-violet/30 flex items-center justify-center overflow-hidden">
            <div className="absolute inset-0 bg-glass-shine" />
            <span className="relative text-[10px] font-mono font-bold text-white">
              OP
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
