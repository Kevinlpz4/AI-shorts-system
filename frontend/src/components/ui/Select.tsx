"use client";

import { SelectHTMLAttributes, forwardRef } from "react";
import clsx from "clsx";

/** Props del select reutilizable con label y opciones tipadas */
interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'placeholder'> {
  /** Label que se muestra arriba del select */
  label?: string;
  /** Opciones del select: array de { value, label } */
  options: { value: string; label: string }[];
  /** Texto del placeholder (se muestra como primera opción deshabilitada) */
  placeholder?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, options, placeholder, className, id, ...props }, ref) => {
    const selectId = id || label?.toLowerCase().replace(/\s+/g, "-");

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={selectId}
            className="block mb-1.5 text-xs font-mono text-gray-400 uppercase tracking-wider"
          >
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={selectId}
          className={clsx(
            "w-full bg-cyber-dark/60 border border-glass-border rounded-lg px-3 py-2.5",
            "text-sm font-mono text-white",
            "backdrop-blur-sm transition-all duration-200 appearance-none",
            "focus:outline-none focus:ring-2 focus:ring-cyber-purple/50 focus:border-cyber-cyan/50",
            className
          )}
          {...props}
        >
          {placeholder && (
            <option value="" className="bg-cyber-dark">
              {placeholder}
            </option>
          )}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value} className="bg-cyber-dark">
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    );
  }
);

Select.displayName = "Select";
