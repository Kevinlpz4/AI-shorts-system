"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import {
  LayoutDashboard,
  Compass,
  FileText,
  BarChart3,
  Film,
  Settings,
  PlusCircle,
  Terminal,
} from "lucide-react";

/** Item de navegación del sidebar */
interface NavItem {
  /** Ruta de destino */
  href: string;
  /** Texto visible */
  label: string;
  /** Icono SVG */
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Dashboard", icon: <LayoutDashboard size={18} /> },
  { href: "/discover", label: "Discover", icon: <Compass size={18} /> },
  { href: "/create", label: "Create Topic", icon: <PlusCircle size={18} /> },
  { href: "/topics", label: "Topics", icon: <FileText size={18} /> },
  { href: "/analytics", label: "Analytics", icon: <BarChart3 size={18} /> },
  { href: "/studio", label: "Studio", icon: <Film size={18} /> },
  { href: "/settings", label: "Settings", icon: <Settings size={18} /> },
  { href: "/terminal", label: "Terminal", icon: <Terminal size={18} /> },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 z-40 flex flex-col">
      {/* Scan line effect */}
      <div className="absolute inset-0 bg-cyber-grid bg-grid opacity-30 pointer-events-none" />

      {/* Glass background */}
      <div className="absolute inset-0 bg-cyber-black/90 backdrop-blur-xl border-r border-glass-border" />

      {/* Content */}
      <div className="relative z-10 flex flex-col h-full">
        {/* Logo */}
        <div className="p-6 border-b border-glass-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-cyber-magenta/20 border border-cyber-magenta/40 flex items-center justify-center">
              <span className="text-cyber-magenta text-lg font-display font-bold">
                AI
              </span>
            </div>
            <div>
              <h1 className="text-sm font-display font-bold text-white tracking-wider">
                CONTENT DISCOVERY
              </h1>
              <p className="text-[10px] font-mono text-cyber-cyan/60 tracking-widest uppercase">
                Control Room v1.0
              </p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-mono transition-all duration-200",
                  "border border-transparent",
                  isActive
                    ? "bg-cyber-magenta/15 border-cyber-magenta/30 text-cyber-magenta shadow-neon-magenta/20"
                    : "text-gray-400 hover:text-white hover:bg-glass-white hover:border-glass-border"
                )}
              >
                <span
                  className={clsx(
                    "transition-transform duration-200",
                    isActive && "scale-110"
                  )}
                >
                  {item.icon}
                </span>
                <span>{item.label}</span>
                {isActive && (
                  <span className="ml-auto w-1.5 h-1.5 rounded-full bg-cyber-magenta animate-glow-pulse" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* System status footer */}
        <div className="p-4 border-t border-glass-border">
          <div className="flex items-center gap-2 text-[10px] font-mono text-gray-500">
            <span className="w-2 h-2 rounded-full bg-cyber-green animate-glow-pulse" />
            <span>System Online</span>
            <span className="ml-auto text-cyber-cyan/50">v1.0.0</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
