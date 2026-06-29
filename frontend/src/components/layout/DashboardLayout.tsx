"use client";

import { ReactNode } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";

/** Props del layout principal del dashboard */
interface DashboardLayoutProps {
  /** Contenido a renderizar en el área principal */
  children: ReactNode;
}

/**
 * Layout principal del dashboard con cyberpunk theme.
 *
 * Incluye: fondo de cuadrícula, overlay de glow, línea de scan animada,
 * sidebar fijo a la izquierda, header sticky y área de contenido.
 */
export function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-cyber-black text-white">
      {/* Cyber grid background */}
      <div className="fixed inset-0 bg-cyber-grid bg-grid opacity-20 pointer-events-none" />
      <div className="fixed inset-0 bg-cyber-glow pointer-events-none" />

      {/* Scan line overlay */}
      <div className="fixed inset-0 bg-scan-line opacity-[0.02] pointer-events-none animate-scan-line" />

      {/* Sidebar */}
      <Sidebar />

      {/* Main area */}
      <div className="pl-64">
        <Header />

        {/* Content */}
        <main className="p-6 relative z-10 animate-fade-in">
          {children}
        </main>
      </div>
    </div>
  );
}
