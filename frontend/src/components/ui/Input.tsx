"use client";

import { InputHTMLAttributes, forwardRef, useState } from "react";
import { motion } from "framer-motion";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, icon, className, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");
    const [focused, setFocused] = useState(false);

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block mb-1.5 text-[10px] font-mono text-gray-400 uppercase tracking-[0.15em]"
          >
            {label}
          </label>
        )}
        <motion.div
          className="relative"
          animate={focused ? { scale: 1.01 } : { scale: 1 }}
          transition={{ type: "spring", stiffness: 300, damping: 25 }}
        >
          {icon && (
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500">
              {icon}
            </span>
          )}
          <input
            ref={ref}
            id={inputId}
            onFocus={(e) => {
              setFocused(true);
              props.onFocus?.(e);
            }}
            onBlur={(e) => {
              setFocused(false);
              props.onBlur?.(e);
            }}
            className={`
              w-full h-11 px-4 text-sm font-mono rounded-xl transition-all duration-300
              bg-glass-base backdrop-blur-xl border text-white placeholder-gray-500
              ${icon ? "pl-10" : ""}
              ${
                error
                  ? "border-neon-red/50 focus:border-neon-red"
                  : "border-glass-border focus:border-neon-cyan/40"
              }
              focus:outline-none focus:bg-glass-light
              focus:shadow-[0_0_20px_rgba(0,229,255,0.08)]
              ${className || ""}
            `.trim()}
            {...props}
          />
          {/* Focus glow line */}
          {focused && (
            <motion.span
              layoutId="input-glow"
              className="absolute inset-0 rounded-xl pointer-events-none"
              style={{
                boxShadow: "0 0 20px rgba(0, 229, 255, 0.08), inset 0 0 20px rgba(0, 229, 255, 0.03)",
              }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            />
          )}
        </motion.div>
        {error && (
          <p className="mt-1.5 text-[11px] font-mono text-neon-red">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
