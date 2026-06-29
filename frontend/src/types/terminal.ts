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

/** A registered terminal command */
export interface TerminalCommand {
  name: string;
  description: string;
  usage: string;
}

/** Command history entry */
export interface CommandHistory {
  command: string;
  output: TerminalOutput[];
}
