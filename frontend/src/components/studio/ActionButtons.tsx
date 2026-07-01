"use client";

import { Button } from "@/components/ui/Button";
import { RefreshCw, Check } from "lucide-react";

/** Props for the script action buttons */
interface ActionButtonsProps {
  /** Whether a script generation is in progress */
  isGenerating: boolean;
  /** Callback to regenerate the script */
  onRegenerate: () => void;
  /** Callback to accept the script and remove the topic from the queue */
  onAccept: () => void;
}

/**
 * Action buttons for the generated script.
 *
 * Three buttons in a row:
 * - Regenerate (secondary)
 * - Accept (success / primary — blue)
 * - Discard (ghost)
 *
 * All disabled during generation.
 */
export function ActionButtons({
  isGenerating,
  onRegenerate,
  onAccept,
}: ActionButtonsProps) {
  return (
    <div className="flex items-center gap-3">
      <Button
        variant="secondary"
        size="sm"
        disabled={isGenerating}
        isLoading={isGenerating}
        onClick={onRegenerate}
        className="flex-1"
      >
        <RefreshCw size={14} />
        Regenerate
      </Button>

      <Button
        variant="success"
        size="sm"
        disabled={isGenerating}
        onClick={onAccept}
        className="flex-1"
      >
        <Check size={14} />
        Accept
      </Button>
    </div>
  );
}
