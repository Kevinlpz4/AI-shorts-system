"use client";

import { HTMLAttributes, forwardRef } from "react";
import { motion } from "framer-motion";

type ConflictingHandlers =
  | "onAnimationStart"
  | "onDragStart"
  | "onDragEnd"
  | "onDrag";

interface CardProps
  extends Omit<HTMLAttributes<HTMLDivElement>, ConflictingHandlers> {
  glow?: "cyan" | "violet" | "magenta" | "green" | "red" | "none";
  hoverable?: boolean;
}

const glowClasses: Record<string, string> = {
  cyan: "glass-glow-cyan",
  violet: "glass-glow-violet",
  magenta: "glass-glow-magenta",
  green: "glass-glow-green",
  red: "glass-glow-red",
  none: "",
};

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ glow = "none", hoverable = false, className, children, ...props }, ref) => {
    return (
      <motion.div
        ref={ref}
        whileHover={hoverable ? { y: -4, scale: 1.005 } : undefined}
        transition={
          hoverable
            ? { type: "spring" as const, stiffness: 200, damping: 20 }
            : undefined
        }
        className={`
          relative glass rounded-xl overflow-hidden transition-all duration-300
          ${glow !== "none" ? glowClasses[glow] : ""}
          ${hoverable ? "cursor-pointer" : ""}
          ${className || ""}
        `.trim()}
        {...props}
      >
        {/* Glass shine (top reflection) */}
        <span className="absolute inset-0 pointer-events-none">
          <span className="absolute inset-0 bg-glass-shine" />
        </span>

        {/* Content */}
        <div className="relative z-[1]">{children}</div>
      </motion.div>
    );
  }
);

Card.displayName = "Card";
