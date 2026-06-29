"use client";

import { InputHTMLAttributes, forwardRef } from "react";
import clsx from "clsx";

/** Props del input con label flotante, error e icono opcional */
interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** Label que se muestra arriba del input */
  label?: string;
  /** Mensaje de error que se muestra debajo */
  error?: string;
  /** Icono a la izquierda del input */
  icon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block mb-1.5 text-xs font-mono text-gray-400 uppercase tracking-wider"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={clsx(
            "w-full bg-cyber-dark/60 border rounded-lg px-3 py-2.5",
            "text-sm font-mono text-white placeholder-gray-500",
            "backdrop-blur-sm transition-all duration-200",
            "focus:outline-none focus:ring-2 focus:ring-cyber-purple/50",
            error
              ? "border-cyber-red/50 focus:border-cyber-red"
              : "border-glass-border focus:border-cyber-cyan/50",
            className
          )}
          {...props}
        />
        {error && (
          <p className="mt-1 text-xs text-cyber-red font-mono">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
