"use client";

import { HTMLAttributes, forwardRef } from "react";
import clsx from "clsx";

/** Props del componente Card con glassmorphism y glow opcional */
interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Color del glow hover: magenta, cyan, purple, green, red o none */
  glow?: "magenta" | "cyan" | "purple" | "green" | "red" | "none";
  /** Si es true, escala al hacer hover y muestra cursor pointer */
  hoverable?: boolean;
}

const glowStyles = {
  magenta: "hover:shadow-neon-magenta border-cyber-magenta/20",
  cyan: "hover:shadow-neon-cyan border-cyber-cyan/20",
  purple: "hover:shadow-neon-purple border-cyber-purple/20",
  green: "hover:shadow-neon-green border-cyber-green/20",
  red: "hover:shadow-neon-red border-cyber-red/20",
  none: "border-glass-border",
};

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ glow = "none", hoverable = false, className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={clsx(
        // Glassmorphism base
        "bg-glass-white backdrop-blur-xl",
        "border rounded-xl",
        "transition-all duration-300",
        hoverable && "hover:bg-glass-light hover:scale-[1.02] cursor-pointer",
        glowStyles[glow],
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
);

Card.displayName = "Card";
