"use client";

import clsx from "clsx";
import { TopicStatus } from "@/types";

/** Props del badge que muestra el estado de un topic con color y animación */
interface StatusBadgeProps {
  /** Estado del topic (FOUND, PENDING_REVIEW, APPROVED, REJECTED) */
  status: TopicStatus;
  /** Tamaño del badge */
  size?: "sm" | "md";
}

const statusConfig: Record<
  TopicStatus,
  { label: string; color: string; dotColor: string }
> = {
  FOUND: {
    label: "Found",
    color: "text-cyber-cyan border-cyber-cyan/30 bg-cyber-cyan/10",
    dotColor: "bg-cyber-cyan",
  },
  PENDING_REVIEW: {
    label: "Pending Review",
    color: "text-cyber-yellow border-cyber-yellow/30 bg-cyber-yellow/10",
    dotColor: "bg-cyber-yellow",
  },
  APPROVED: {
    label: "Approved",
    color: "text-cyber-green border-cyber-green/30 bg-cyber-green/10",
    dotColor: "bg-cyber-green",
  },
  REJECTED: {
    label: "Rejected",
    color: "text-cyber-red border-cyber-red/30 bg-cyber-red/10",
    dotColor: "bg-cyber-red",
  },
};

export function StatusBadge({ status, size = "sm" }: StatusBadgeProps) {
  const config = statusConfig[status];
  const isPending = status === "PENDING_REVIEW";

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 font-mono border rounded-full",
        size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-3 py-1 text-xs",
        config.color,
        isPending && "animate-glow-pulse"
      )}
    >
      <span className={clsx("w-1.5 h-1.5 rounded-full", config.dotColor)} />
      {config.label}
    </span>
  );
}
