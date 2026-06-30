"use client";

import clsx from "clsx";
import { ScriptData } from "@/types";
import { Clock, Music, Target, FileText, CheckCircle, AlertTriangle } from "lucide-react";

/** Props for the script metadata display */
interface ScriptMetadataProps {
  /** The generated script data */
  script: ScriptData;
}

/**
 * Metadata bar for a generated script.
 *
 * Shows duration, tone, niche, word count, and validation status
 * in a compact horizontal layout.
 */
export function ScriptMetadata({ script }: ScriptMetadataProps) {
  const metaItems = [
    { icon: Clock, label: "Duration", value: `${script.duration}s` },
    { icon: Music, label: "Tone", value: script.tone },
    { icon: Target, label: "Format", value: script.format },
    {
      icon: FileText,
      label: "Words",
      value: `${script.wordCount.toLocaleString()}`,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-2">
      {metaItems.map((item) => (
        <div
          key={item.label}
          className="flex items-center gap-2 p-2.5 rounded-lg bg-glass-white border border-glass-border"
        >
          <item.icon size={14} className="text-gray-500 shrink-0" />
          <div className="min-w-0">
            <p className="text-[9px] font-mono text-gray-500 uppercase tracking-wider">
              {item.label}
            </p>
            <p className="text-xs font-mono text-gray-300 truncate">
              {item.value}
            </p>
          </div>
        </div>
      ))}

      {/* Validation status */}
      <div
        className={clsx(
          "col-span-2 flex items-center gap-2 p-2.5 rounded-lg border",
          script.isValid
            ? "bg-cyber-green/5 border-cyber-green/20"
            : "bg-cyber-yellow/5 border-cyber-yellow/20",
        )}
      >
        {script.isValid ? (
          <>
            <CheckCircle size={14} className="text-cyber-green shrink-0" />
            <span className="text-[10px] font-mono text-cyber-green">
              Script passes all validations
            </span>
          </>
        ) : (
          <>
            <AlertTriangle size={14} className="text-cyber-yellow shrink-0" />
            <span className="text-[10px] font-mono text-cyber-yellow">
              Script has validation warnings
            </span>
          </>
        )}
      </div>
    </div>
  );
}
