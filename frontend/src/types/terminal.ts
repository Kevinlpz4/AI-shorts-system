// ═══════════════════════════════════════════════════
// Terminal Types — Command-line interface types
// ═══════════════════════════════════════════════════

/** A single line of output in the terminal */
export interface TerminalOutput {
  type: "input" | "output" | "error" | "system" | "table";
  content: string;
  /** Optional array of strings for table rendering */
  lines?: string[];
}


