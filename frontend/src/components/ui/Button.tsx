"use client";

import { ButtonHTMLAttributes, forwardRef } from "react";
import clsx from "clsx";

type ButtonVariant = "primary" | "secondary" | "success" | "danger" | "ghost";
type ButtonSize = "sm" | "md" | "lg";

/** Props del botón reutilizable con variantes de cyberpunk theme */
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Variante de color: primary (magenta), secondary (cyan), success, danger, ghost */
  variant?: ButtonVariant;
  /** Tamaño: sm, md, lg */
  size?: ButtonSize;
  /** Muestra spinner de carga y deshabilita el botón */
  isLoading?: boolean;
  /** Activa animación de glow pulsante */
  glow?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-cyber-magenta/20 border-cyber-magenta/50 text-cyber-magenta hover:bg-cyber-magenta/30 hover:shadow-neon-magenta",
  secondary:
    "bg-cyber-cyan/10 border-cyber-cyan/30 text-cyber-cyan hover:bg-cyber-cyan/20 hover:shadow-neon-cyan",
  success:
    "bg-cyber-green/10 border-cyber-green/30 text-cyber-green hover:bg-cyber-green/20 hover:shadow-neon-green",
  danger:
    "bg-cyber-red/10 border-cyber-red/30 text-cyber-red hover:bg-cyber-red/20 hover:shadow-neon-red",
  ghost:
    "bg-transparent border-glass-border text-gray-400 hover:text-white hover:bg-glass-white",
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
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
    <button
      ref={ref}
      disabled={disabled || isLoading}
      className={clsx(
        "relative inline-flex items-center justify-center gap-2 font-mono font-medium",
        "border rounded-lg backdrop-blur-sm transition-all duration-200",
        "disabled:opacity-40 disabled:cursor-not-allowed",
        "focus:outline-none focus:ring-2 focus:ring-cyber-purple/50",
        variantStyles[variant],
        sizeStyles[size],
        glow && "animate-glow-pulse",
        className
      )}
      {...props}
    >
      {isLoading && (
        <span className="absolute inset-0 flex items-center justify-center">
          <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
        </span>
      )}
      <span className={clsx(isLoading && "invisible")}>{children}</span>
    </button>
  )
);

Button.displayName = "Button";
