"use client";

import { SelectHTMLAttributes, forwardRef } from "react";

interface SelectProps
  extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "placeholder"> {
  label?: string;
  options: { value: string; label: string }[];
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
            className="block mb-1.5 text-[10px] font-mono text-gray-400 uppercase tracking-[0.15em]"
          >
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            className={`
              w-full h-11 px-4 text-sm font-mono rounded-xl transition-all duration-300
              bg-glass-base backdrop-blur-xl border border-glass-border text-white
              appearance-none cursor-pointer
              focus:outline-none focus:border-neon-cyan/40 focus:bg-glass-light
              focus:shadow-[0_0_20px_rgba(0,229,255,0.08)]
              ${className || ""}
            `.trim()}
            {...props}
          >
            {placeholder && (
              <option value="" className="bg-base-800 text-gray-500">
                {placeholder}
              </option>
            )}
            {options.map((opt) => (
              <option
                key={opt.value}
                value={opt.value}
                className="bg-base-800 text-white"
              >
                {opt.label}
              </option>
            ))}
          </select>
          {/* Custom arrow */}
          <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none">
            <svg width="12" height="8" viewBox="0 0 12 8" fill="none">
              <path
                d="M1 1.5L6 6.5L11 1.5"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
        </div>
      </div>
    );
  }
);

Select.displayName = "Select";
