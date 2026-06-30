"use client";

import { ScriptData } from "@/types";
import { MessageSquare, AlignLeft, Bell } from "lucide-react";

/** Props for the script display component */
interface ScriptDisplayProps {
  /** The generated script data to display */
  script: ScriptData;
}

/**
 * Renders a generated script in a formatted display.
 *
 * Splits the script into three labeled sections:
 * - Hook (opening line)
 * - Body (main content)
 * - CTA (call to action)
 */
export function ScriptDisplay({ script }: ScriptDisplayProps) {
  return (
    <div className="space-y-4">
      {/* Hook */}
      <div className="p-4 rounded-lg border border-glass-border bg-glass-white">
        <div className="flex items-center gap-2 mb-2">
          <span className="flex items-center justify-center w-6 h-6 rounded-full bg-cyber-magenta/20 text-cyber-magenta">
            <Bell size={12} />
          </span>
          <span className="text-[10px] font-mono text-cyber-magenta uppercase tracking-wider">
            Hook
          </span>
        </div>
        <p className="text-sm text-white font-sans leading-relaxed">
          {script.hook}
        </p>
      </div>

      {/* Body */}
      <div className="p-4 rounded-lg border border-glass-border bg-glass-white">
        <div className="flex items-center gap-2 mb-2">
          <span className="flex items-center justify-center w-6 h-6 rounded-full bg-cyber-cyan/20 text-cyber-cyan">
            <AlignLeft size={12} />
          </span>
          <span className="text-[10px] font-mono text-cyber-cyan uppercase tracking-wider">
            Body
          </span>
        </div>
        <div className="text-sm text-gray-300 font-sans leading-relaxed whitespace-pre-line">
          {script.body}
        </div>
      </div>

      {/* CTA */}
      <div className="p-4 rounded-lg border border-glass-border bg-glass-white">
        <div className="flex items-center gap-2 mb-2">
          <span className="flex items-center justify-center w-6 h-6 rounded-full bg-cyber-green/20 text-cyber-green">
            <MessageSquare size={12} />
          </span>
          <span className="text-[10px] font-mono text-cyber-green uppercase tracking-wider">
            Call to Action
          </span>
        </div>
        <p className="text-sm text-white font-sans leading-relaxed">
          {script.cta}
        </p>
      </div>
    </div>
  );
}
