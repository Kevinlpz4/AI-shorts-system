"use client";

import { motion } from "framer-motion";
import { TopicStatus } from "@/types";

interface StatusBadgeProps {
  status: TopicStatus;
  size?: "sm" | "md";
}

const statusConfig: Record<
  TopicStatus,
  { label: string; glow: string; border: string; bg: string; dot: string }
> = {
  FOUND: {
    label: "Found",
    glow: "shadow-[0_0_12px_rgba(0,229,255,0.1)]",
    border: "border-neon-cyan/25",
    bg: "bg-neon-cyan/8",
    dot: "bg-neon-cyan",
  },
  PENDING_REVIEW: {
    label: "Pending Review",
    glow: "shadow-[0_0_12px_rgba(251,191,36,0.1)]",
    border: "border-neon-yellow/25",
    bg: "bg-neon-yellow/8",
    dot: "bg-neon-yellow",
  },
  APPROVED: {
    label: "Approved",
    glow: "shadow-[0_0_12px_rgba(52,211,153,0.1)]",
    border: "border-neon-green/25",
    bg: "bg-neon-green/8",
    dot: "bg-neon-green",
  },
  REJECTED: {
    label: "Rejected",
    glow: "shadow-[0_0_12px_rgba(251,113,133,0.1)]",
    border: "border-neon-red/25",
    bg: "bg-neon-red/8",
    dot: "bg-neon-red",
  },
};

export function StatusBadge({ status, size = "sm" }: StatusBadgeProps) {
  const config = statusConfig[status];
  const isPending = status === "PENDING_REVIEW";

  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`
        inline-flex items-center gap-1.5 font-mono rounded-full backdrop-blur-xl
        border ${config.border} ${config.glow}
        ${size === "sm" ? "px-2.5 py-0.5 text-[9px]" : "px-3 py-1 text-[11px]"}
        bg-glass-base
      `.trim()}
    >
      <span
        className={`relative flex h-1.5 w-1.5 ${isPending ? "" : ""}`}
      >
        <span
          className={`absolute inline-flex w-full h-full rounded-full ${config.dot} ${
            isPending ? "animate-ping opacity-75" : ""
          }`}
        />
        <span
          className={`relative inline-flex rounded-full h-1.5 w-1.5 ${config.dot}`}
        />
      </span>
      <span className="text-white/80 font-medium tracking-wide">{config.label}</span>
    </motion.span>
  );
}
