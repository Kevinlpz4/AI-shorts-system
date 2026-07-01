"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutGroup, motion } from "framer-motion";
import {
  LayoutDashboard,
  Compass,
  FileText,
  BarChart3,
  Film,
  ScrollText,
  Settings,
  PlusCircle,
  Terminal,
} from "lucide-react";

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Dashboard", icon: <LayoutDashboard size={18} /> },
  { href: "/discover", label: "Discover", icon: <Compass size={18} /> },
  { href: "/create", label: "Create Topic", icon: <PlusCircle size={18} /> },
  { href: "/topics", label: "Topics", icon: <FileText size={18} /> },
  { href: "/analytics", label: "Analytics", icon: <BarChart3 size={18} /> },
  { href: "/studio", label: "Studio", icon: <Film size={18} /> },
  { href: "/scripts", label: "Scripts", icon: <ScrollText size={18} /> },
  { href: "/settings", label: "Settings", icon: <Settings size={18} /> },
  { href: "/terminal", label: "Terminal", icon: <Terminal size={18} /> },
];

const sidebarVariants = {
  initial: { x: -280 },
  animate: {
    x: 0,
    transition: { type: "spring" as const, stiffness: 100, damping: 20 },
  },
};

export function Sidebar() {
  const pathname = usePathname();

  return (
    <motion.aside
      variants={sidebarVariants}
      initial="initial"
      animate="animate"
      className="fixed left-0 top-0 h-screen w-64 z-40 flex flex-col"
    >
      {/* Glass background */}
      <div className="absolute inset-0 backdrop-blur-2xl bg-base-800/60 border-r border-glass-border" />
      <div className="absolute inset-0 bg-layer-noise pointer-events-none" />

      {/* Content */}
      <div className="relative z-10 flex flex-col h-full">
        {/* Logo */}
        <div className="px-5 py-6 border-b border-glass-border">
          <div className="flex items-center gap-3">
            <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-neon-violet/30 to-neon-magenta/20 border border-neon-violet/30 flex items-center justify-center overflow-hidden">
              <div className="absolute inset-0 bg-glass-shine" />
              <span className="relative text-sm font-display font-bold text-white">
                AI
              </span>
            </div>
            <div>
              <h1 className="text-xs font-display font-semibold text-white tracking-wider">
                AI SHORTS
              </h1>
              <p className="text-[9px] font-mono text-neon-cyan/50 tracking-[0.2em] uppercase">
                Control Room
              </p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          <LayoutGroup>
            {NAV_ITEMS.map((item) => {
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname === item.href ||
                    pathname.startsWith(item.href + "/");
              return (
                <div key={item.href}>
                  <Link
                    href={item.href}
                    className={`relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-300 group
                      ${
                        isActive
                          ? "text-neon-magenta"
                          : "text-neon-magenta/50 hover:text-neon-magenta"
                      }`}
                  >
                    {/* Active glow background */}
                    {isActive && (
                      <motion.div
                        layoutId="nav-active"
                        layout
                        className="absolute inset-0 rounded-xl"
                        style={{
                          background:
                            "linear-gradient(135deg, rgba(124,58,237,0.15) 0%, rgba(0,229,255,0.05) 100%)",
                          border: "1px solid rgba(124,58,237,0.2)",
                          boxShadow:
                            "0 0 20px rgba(124,58,237,0.08), inset 0 1px 0 rgba(255,255,255,0.06)",
                        }}
                        transition={{
                          type: "spring" as const,
                          stiffness: 200,
                          damping: 25,
                        }}
                      />
                    )}

                    {/* Hover glow (non-active) */}
                    {!isActive && (
                      <div
                        className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                        style={{
                          background:
                            "linear-gradient(135deg, rgba(255,255,255,0.04) 0%, transparent 100%)",
                          border: "1px solid rgba(255,255,255,0.05)",
                        }}
                      />
                    )}

                    {/* Icon */}
                    <span
                      className={`relative transition-all duration-300 ${
                        isActive
                          ? "text-neon-cyan scale-110"
                          : "group-hover:scale-110"
                      }`}
                    >
                      {item.icon}
                    </span>

                    {/* Label */}
                    <span className="relative font-medium tracking-wide">
                      {item.label}
                    </span>

                    {/* Active indicator dot */}
                    {isActive && (
                      <motion.span
                        layoutId="nav-dot"
                        layout
                        className="ml-auto w-1.5 h-1.5 rounded-full bg-neon-cyan shrink-0"
                        animate={{
                          boxShadow: [
                            "0 0 4px rgba(0,229,255,0.5)",
                            "0 0 8px rgba(0,229,255,0.8)",
                            "0 0 4px rgba(0,229,255,0.5)",
                          ],
                        }}
                        transition={{
                          boxShadow: {
                            duration: 2,
                            repeat: Infinity,
                          },
                          layout: {
                            type: "spring" as const,
                            stiffness: 300,
                            damping: 30,
                          },
                        }}
                      />
                    )}
                  </Link>
                </div>
              );
            })}
          </LayoutGroup>
        </nav>

        {/* System status footer */}
        <div className="px-5 py-4 border-t border-glass-border">
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-neon-green opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-neon-green" />
            </span>
            <span className="text-[10px] font-mono text-gray-500">System Online</span>
            <span className="ml-auto text-[9px] font-mono text-gray-600 tracking-wider">
              v2.0
            </span>
          </div>
        </div>
      </div>
    </motion.aside>
  );
}
