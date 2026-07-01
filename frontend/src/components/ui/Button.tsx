"use client";

import { ButtonHTMLAttributes, forwardRef } from "react";
import { motion } from "framer-motion";

type ButtonVariant = "primary" | "secondary" | "success" | "danger" | "ghost";
type ButtonSize = "sm" | "md" | "lg";

type ConflictingHandlers =
  | "onAnimationStart"
  | "onDragStart"
  | "onDragEnd"
  | "onDrag";

interface ButtonProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, ConflictingHandlers> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  glow?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-gradient-to-br from-neon-violet/20 to-neon-magenta/10 border-neon-violet/30 text-white hover:border-neon-violet/50",
  secondary:
    "bg-neon-cyan/10 border-neon-cyan/25 text-neon-cyan hover:bg-neon-cyan/20 hover:border-neon-cyan/40",
  success:
    "bg-neon-green/10 border-neon-green/25 text-neon-green hover:bg-neon-green/20 hover:border-neon-green/40",
  danger:
    "bg-neon-red/10 border-neon-red/25 text-neon-red hover:bg-neon-red/20 hover:border-neon-red/40",
  ghost:
    "bg-transparent border-glass-border text-gray-400 hover:text-white hover:bg-glass-light",
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2.5 text-sm",
  lg: "px-6 py-3 text-base",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      isLoading = false,
      glow = false,
      className,
      disabled,
      children,
      ...props
    },
    ref
  ) => (
    <motion.button
      ref={ref}
      disabled={disabled || isLoading}
      whileHover={!disabled && !isLoading ? { scale: 1.02 } : undefined}
      whileTap={!disabled && !isLoading ? { scale: 0.97 } : undefined}
      className={`
        relative inline-flex items-center justify-center gap-2 font-mono font-medium
        border backdrop-blur-xl rounded-xl transition-all duration-300
        disabled:opacity-40 disabled:cursor-not-allowed
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan/50
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${glow && !disabled ? "shadow-[0_0_20px_rgba(124,58,237,0.1)]" : ""}
        ${className || ""}
      `.trim()}
      {...props}
    >
      {/* Glass shine overlay */}
      <span className="absolute inset-0 rounded-xl overflow-hidden pointer-events-none">
        <span className="absolute inset-0 bg-glass-shine" />
      </span>

      {/* Loading spinner */}
      {isLoading && (
        <span className="absolute inset-0 flex items-center justify-center backdrop-blur-sm rounded-xl bg-inherit">
          <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
        </span>
      )}

      {/* Content */}
      <span className={`relative inline-flex items-center gap-2 ${isLoading ? "invisible" : ""}`}>
        {children}
      </span>
    </motion.button>
  )
);

Button.displayName = "Button";
