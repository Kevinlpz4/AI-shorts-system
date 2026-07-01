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
 * Layout principal con diseño GlassOS — capas de fondo, sidebar, header.
 *
 * Fondos:
 * - Gradiente oscuro profundo
 * - Textura noise sutil
 * - Grid futurista con máscara radial
 * - Orbes luminosos flotantes
 */
export function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-base-900 text-white antialiased">
      {/* ═══ Background layers ═══ */}
      <div className="background-layer bg-layer-deep" />
      <div className="background-layer bg-layer-noise" />
      <div className="background-layer bg-layer-grid" />
      <div className="background-layer bg-layer-orbs">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
        <div className="orb orb-4" />
      </div>

      {/* ═══ Content layers ═══ */}
      <div className="relative z-10">
        {/* Sidebar */}
        <Sidebar />

        {/* Main area */}
        <div className="pl-64">
          <Header />

          {/* Content */}
          <main className="p-6 lg:p-8 animate-fade-in">{children}</main>
        </div>
      </div>
    </div>
  );
}
