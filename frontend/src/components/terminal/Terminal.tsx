"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { TerminalOutput } from "@/types/terminal";

// ═══════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════

type OutputItem = {
  type: "input" | "output" | "error" | "system" | "table";
  content: string;
  lines?: string[];
};

// ═══════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════

const API_BASE =
  typeof process !== "undefined" ? process.env.NEXT_PUBLIC_API_URL || "" : "";

const isApiConnected = API_BASE.length > 0;

const WELCOME_BANNER = `
╔══════════════════════════════════════════════════════════╗
║           AI SHORTS SYSTEM — Developer Terminal          ║
║                                                          ║
║  Welcome to the control room terminal.                   ║
║  Type 'help' to see available commands.                  ║
║                                                          ║
║  ${isApiConnected ? "● Backend connected" : "○ Backend not connected"}${isApiConnected ? ` @ ${API_BASE}` : ""}
╚══════════════════════════════════════════════════════════╝
`;

const ERROR_NOT_CONNECTED =
  "Backend not connected. Set NEXT_PUBLIC_API_URL to enable real commands.";

const HELP_TABLE: { command: string; description: string; usage: string }[] = [
  { command: "help", description: "Show this help table", usage: "help" },
  {
    command: "topics list [status]",
    description: "List topics (optional filter: approved, rejected, pending_review, found)",
    usage: "topics list [status]",
  },
  {
    command: "topics approve <id>",
    description: "Approve a topic by ID",
    usage: "topics approve <id>",
  },
  {
    command: "topics reject <id>",
    description: "Reject a topic by ID",
    usage: "topics reject <id>",
  },
  {
    command: "topics discover [query]",
    description: "Run topic discovery",
    usage: "topics discover [query]",
  },
  {
    command: "script generate <topicId>",
    description: "Generate a script for a topic",
    usage: "script generate <topicId>",
  },
  {
    command: "script view <topicId>",
    description: "View existing script for a topic",
    usage: "script view <topicId>",
  },
  {
    command: "script regenerate <topicId>",
    description: "Regenerate script for a topic",
    usage: "script regenerate <topicId>",
  },
  { command: "status", description: "System status & metrics", usage: "status" },
  { command: "clear", description: "Clear terminal output", usage: "clear" },
  { command: "echo <text>", description: "Echo back input text", usage: "echo hello" },
];

// ═══════════════════════════════════════════════════
// Helpers
// ═══════════════════════════════════════════════════

/** Trunca un ID para mostrar en terminal (8 chars + ... + 4 chars) */
function maskId(id: string): string {
  if (id.length <= 12) return id;
  return id.slice(0, 8) + "..." + id.slice(-4);
}

/** Formatea segundos a formato legible (ej: "2h 30m 15s") */
function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  const parts: string[] = [];
  if (h > 0) parts.push(`${h}h`);
  if (m > 0) parts.push(`${m}m`);
  parts.push(`${s}s`);
  return parts.join(" ");
}

// ═══════════════════════════════════════════════════
// Command Handlers
// ═══════════════════════════════════════════════════

/** Handler: muestra tabla de comandos disponibles */
async function handleHelp(): Promise<OutputItem[]> {
  const lines: string[] = [];
  const colW = [28, 50, 28];
  const sep = "─".repeat(colW[0] + colW[1] + colW[2] + 6);

  lines.push(`┌${sep}┐`);
  lines.push(
    `│ ${"COMMAND".padEnd(colW[0])} │ ${"DESCRIPTION".padEnd(colW[1])} │ ${"USAGE".padEnd(colW[2])} │`
  );
  lines.push(`├${sep}┤`);

  for (const cmd of HELP_TABLE) {
    const name = cmd.command.padEnd(colW[0]);
    const desc = cmd.description.padEnd(colW[1]);
    const usage = cmd.usage.padEnd(colW[2]);
    lines.push(`│ ${name} │ ${desc} │ ${usage} │`);
  }

  lines.push(`└${sep}┘`);

  return [
    { type: "table", content: "Available Commands", lines },
  ];
}

/** Handler: lista topics con filtro opcional por status */
async function handleTopicsList(args: string[]): Promise<OutputItem[]> {
  if (!isApiConnected) {
    return [{ type: "error", content: ERROR_NOT_CONNECTED }];
  }

  const status = args[0] || "";
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  params.set("limit", "20");

  try {
    const res = await fetch(`${API_BASE}/api/v1/topics?${params.toString()}`);
    if (!res.ok) {
      const err = await res.json().catch(() => null);
      return [{ type: "error", content: err?.detail || `HTTP ${res.status}: ${res.statusText}` }];
    }

    const data = await res.json();
    const topics: Record<string, unknown>[] = data.topics || data || [];

    if (topics.length === 0) {
      return [{ type: "output", content: "No topics found." }];
    }

    const lines: string[] = [];
    const idCol = 38;
    const titleCol = 50;
    const statusCol = 16;
    const scoreCol = 8;
    const sep = "─".repeat(idCol + titleCol + statusCol + scoreCol + 7);

    lines.push(`┌${sep}┐`);
    lines.push(
      `│ ${"ID".padEnd(idCol)} │ ${"TITLE".padEnd(titleCol)} │ ${"STATUS".padEnd(statusCol)} │ ${"SCORE".padEnd(scoreCol)} │`
    );
    lines.push(`├${sep}┤`);

    for (const t of topics) {
      const id = maskId(String(t.id || "")).padEnd(idCol);
      const title = String(t.title || "").slice(0, titleCol).padEnd(titleCol);
      const st = String(t.status || "").padEnd(statusCol);
      const sc = String(t.score_total ?? t.scoreTotal ?? 0).padEnd(scoreCol);
      lines.push(`│ ${id} │ ${title} │ ${st} │ ${sc} │`);
    }

    lines.push(`└${sep}┘`);
    lines.push(`\n${topics.length} topic(s) found.`);

    return [{ type: "table", content: `Topics${status ? ` (status: ${status})` : ""}`, lines }];
  } catch (err) {
    return [{ type: "error", content: `Connection error: ${err instanceof Error ? err.message : "Unknown"}` }];
  }
}

/** Handler: aprueba un topic por ID */
async function handleTopicsApprove(args: string[]): Promise<OutputItem[]> {
  if (!isApiConnected) {
    return [{ type: "error", content: ERROR_NOT_CONNECTED }];
  }

  const id = args[0];
  if (!id) {
    return [{ type: "error", content: "Usage: topics approve <topicId>" }];
  }

  try {
    const res = await fetch(`${API_BASE}/api/v1/topics/${id}/approve`, { method: "POST" });
    if (!res.ok) {
      const err = await res.json().catch(() => null);
      return [{ type: "error", content: err?.detail || `HTTP ${res.status}: ${res.statusText}` }];
    }

    const data = await res.json();
    const topic = data.topic || data;
    return [
      { type: "output", content: `✅ Topic approved successfully!` },
      { type: "output", content: `  ID: ${topic.id}` },
      { type: "output", content: `  Title: ${topic.title}` },
      { type: "output", content: `  Status: ${topic.status}` },
    ];
  } catch (err) {
    return [{ type: "error", content: `Connection error: ${err instanceof Error ? err.message : "Unknown"}` }];
  }
}

/** Handler: rechaza un topic por ID */
async function handleTopicsReject(args: string[]): Promise<OutputItem[]> {
  if (!isApiConnected) {
    return [{ type: "error", content: ERROR_NOT_CONNECTED }];
  }

  const id = args[0];
  if (!id) {
    return [{ type: "error", content: "Usage: topics reject <topicId>" }];
  }

  try {
    const res = await fetch(`${API_BASE}/api/v1/topics/${id}/reject`, { method: "POST" });
    if (!res.ok) {
      const err = await res.json().catch(() => null);
      return [{ type: "error", content: err?.detail || `HTTP ${res.status}: ${res.statusText}` }];
    }

    const data = await res.json();
    const topic = data.topic || data;
    return [
      { type: "output", content: `✅ Topic rejected successfully!` },
      { type: "output", content: `  ID: ${topic.id}` },
      { type: "output", content: `  Title: ${topic.title}` },
      { type: "output", content: `  Status: ${topic.status}` },
    ];
  } catch (err) {
    return [{ type: "error", content: `Connection error: ${err instanceof Error ? err.message : "Unknown"}` }];
  }
}

/** Handler: ejecuta descubrimiento de topics */
async function handleTopicsDiscover(args: string[]): Promise<OutputItem[]> {
  if (!isApiConnected) {
    return [{ type: "error", content: ERROR_NOT_CONNECTED }];
  }

  const query = args[0] || "";
  const body: Record<string, unknown> = { limit: 5 };
  if (query) body.query = query;

  try {
    const res = await fetch(`${API_BASE}/api/v1/discover`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => null);
      return [{ type: "error", content: err?.detail || `HTTP ${res.status}: ${res.statusText}` }];
    }

    const data = await res.json();
    const discovered: unknown[] = data.discovered || [];
    const duplicates: unknown[] = data.duplicates || [];
    const errors: unknown[] = data.errors || [];

    const lines: string[] = [
      `🔍 Discovery complete${query ? ` for "${query}"` : ""}`,
      `  • Discovered: ${discovered.length}`,
      `  • Duplicates: ${duplicates.length}`,
      `  • Errors: ${errors.length}`,
    ];

    if (discovered.length > 0) {
      lines.push(`\n New Topics:`);
      for (const t of discovered as Record<string, unknown>[]) {
        lines.push(`  - [${String(t.status || "").toUpperCase()}] ${t.title}`);
      }
    }

    return [{ type: "output", content: lines.join("\n") }];
  } catch (err) {
    return [{ type: "error", content: `Connection error: ${err instanceof Error ? err.message : "Unknown"}` }];
  }
}

/** Handler: genera script para un topic */
async function handleScriptGenerate(args: string[]): Promise<OutputItem[]> {
  if (!isApiConnected) {
    return [{ type: "error", content: ERROR_NOT_CONNECTED }];
  }

  const topicId = args[0];
  if (!topicId) {
    return [{ type: "error", content: "Usage: script generate <topicId>" }];
  }

  try {
    const res = await fetch(`${API_BASE}/api/v1/topics/${topicId}/script/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });

    if (!res.ok) {
      const err = await res.json().catch(() => null);
      return [{ type: "error", content: err?.detail || `HTTP ${res.status}: ${res.statusText}` }];
    }

    const data = await res.json();
    return formatScriptOutput(data, "generated");
  } catch (err) {
    return [{ type: "error", content: `Connection error: ${err instanceof Error ? err.message : "Unknown"}` }];
  }
}

/** Handler: visualiza script existente de un topic */
async function handleScriptView(args: string[]): Promise<OutputItem[]> {
  if (!isApiConnected) {
    return [{ type: "error", content: ERROR_NOT_CONNECTED }];
  }

  const topicId = args[0];
  if (!topicId) {
    return [{ type: "error", content: "Usage: script view <topicId>" }];
  }

  try {
    const res = await fetch(`${API_BASE}/api/v1/topics/${topicId}/script`);

    if (res.status === 404) {
      return [{ type: "output", content: "No script found for this topic." }];
    }

    if (!res.ok) {
      const err = await res.json().catch(() => null);
      return [{ type: "error", content: err?.detail || `HTTP ${res.status}: ${res.statusText}` }];
    }

    const data = await res.json();
    return formatScriptOutput(data, "view");
  } catch (err) {
    return [{ type: "error", content: `Connection error: ${err instanceof Error ? err.message : "Unknown"}` }];
  }
}

/** Handler: regenera script existente */
async function handleScriptRegenerate(args: string[]): Promise<OutputItem[]> {
  if (!isApiConnected) {
    return [{ type: "error", content: ERROR_NOT_CONNECTED }];
  }

  const topicId = args[0];
  if (!topicId) {
    return [{ type: "error", content: "Usage: script regenerate <topicId>" }];
  }

  try {
    const res = await fetch(`${API_BASE}/api/v1/topics/${topicId}/script/regenerate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });

    if (!res.ok) {
      const err = await res.json().catch(() => null);
      return [{ type: "error", content: err?.detail || `HTTP ${res.status}: ${res.statusText}` }];
    }

    const data = await res.json();
    return formatScriptOutput(data, "regenerated");
  } catch (err) {
    return [{ type: "error", content: `Connection error: ${err instanceof Error ? err.message : "Unknown"}` }];
  }
}

/**
 * Formatea la respuesta de la API de scripts para display en terminal.
 * Incluye HOOK, BODY (con word-wrap a ~60 chars) y CTA.
 */
function formatScriptOutput(data: Record<string, unknown>, action: string): OutputItem[] {
  const lines: string[] = [
    `╔══════════════════════════════════════════════════╗`,
    `║  SCRIPT ${action.toUpperCase()}${" ".repeat(Math.max(0, 44 - action.length - 12))}║`,
    `╚══════════════════════════════════════════════════╝`,
    ``,
    `  ID:        ${data.id}`,
    `  Topic ID:  ${data.topic_id}`,
    `  Duration:  ${data.duration}s`,
    `  Tone:      ${data.tone}`,
    `  Format:    ${data.format}`,
    `  Words:     ${data.word_count ?? "—"}`,
    `  Valid:     ${data.is_valid !== false ? "✅ Yes" : "❌ No"}`,
    ``,
    `  ── HOOK ──`,
    `  ${data.hook || "—"}`,
    ``,
    `  ── BODY ──`,
  ];

  const body = (data.body || "—") as string;
  // Wrap body to ~60 chars per line for terminal display
  const bodyWords = body.split(" ");
  let bodyLine = "";
  for (const word of bodyWords) {
    if (bodyLine.length + word.length + 1 > 60 && bodyLine.length > 0) {
      lines.push(`  ${bodyLine}`);
      bodyLine = word;
    } else {
      bodyLine = bodyLine ? `${bodyLine} ${word}` : word;
    }
  }
  if (bodyLine) {
    lines.push(`  ${bodyLine}`);
  }

  lines.push(``);
  lines.push(`  ── CTA ──`);
  lines.push(`  ${data.cta || "—"}`);
  lines.push(``);
  lines.push(`  Created: ${data.created_at || "—"}`);
  lines.push(`  Updated: ${data.updated_at || "—"}`);

  return [
    { type: "output", content: `✅ Script ${action} successfully!` },
    { type: "output", content: lines.join("\n") },
  ];
}

/** Handler: muestra estado del sistema y stats */
async function handleStatus(): Promise<OutputItem[]> {
  if (!isApiConnected) {
    return [
      { type: "output", content: "System Status" },
      { type: "system", content: `  API URL:    ${API_BASE || "(not set)"}` },
      { type: "system", content: `  Connection: ${isApiConnected ? "● Connected" : "○ Disconnected"}` },
      { type: "system", content: `  Mode:       ${isApiConnected ? "Real API" : "Mock (offline)"}` },
      { type: "system", content: `  Terminal:   Developer Console v1.0.0` },
      { type: "system", content: `  Frontend:   Next.js + Zustand + Tailwind` },
      { type: "system", content: `  Backend:    ${isApiConnected ? "FastAPI (Python)" : "— (not connected)"}` },
      { type: "error", content: `\n${ERROR_NOT_CONNECTED}` },
    ];
  }

  try {
    const res = await fetch(`${API_BASE}/api/v1/status`);
    if (!res.ok) {
      return [{ type: "error", content: `Status endpoint returned HTTP ${res.status}` }];
    }

    const data = await res.json();
    const topics = (data.topics as Record<string, number>) || {};

    return [
      { type: "output", content: "System Status" },
      { type: "system", content: `  API URL:       ${API_BASE}` },
      { type: "system", content: `  Connection:    ● Connected` },
      { type: "system", content: `  API Version:   ${data.api_version || "—"}` },
      { type: "system", content: `  App Version:   ${data.version || "—"}` },
      { type: "system", content: `  Uptime:        ${formatUptime(data.uptime_seconds || 0)}` },
      { type: "system", content: `  Total Topics:  ${data.total_topics ?? "—"}` },
      { type: "output", content: `\n  Topic Breakdown:` },
      ...Object.entries(topics).map(
        ([status, count]) =>
          ({
            type: "output",
            content: `    • ${status}: ${count}`,
          }) as OutputItem
      ),
    ];
  } catch (err) {
    return [
      { type: "error", content: `Failed to fetch status: ${err instanceof Error ? err.message : "Unknown"}` },
    ];
  }
}

// ═══════════════════════════════════════════════════
// Command Router
// ═══════════════════════════════════════════════════

type CommandHandler = (args: string[]) => Promise<OutputItem[]>;

const commandMap: Record<string, CommandHandler> = {
  help: handleHelp,
  status: handleStatus,
  clear: async () => [],
  echo: async (args) => [{ type: "output", content: args.join(" ") }],
  "topics list": handleTopicsList,
  "topics approve": handleTopicsApprove,
  "topics reject": handleTopicsReject,
  "topics discover": handleTopicsDiscover,
  "script generate": handleScriptGenerate,
  "script view": handleScriptView,
  "script regenerate": handleScriptRegenerate,
};

/**
 * Router de comandos del terminal.
 * Prueba primero comandos de dos palabras (topics *, script *),
 * luego comandos de una palabra.
 */
async function executeCommand(input: string): Promise<OutputItem[]> {
  const trimmed = input.trim();
  if (!trimmed) return [];

  const parts = trimmed.split(/\s+/);

  // Try two-word commands first (topics *, script *)
  if (parts.length >= 2) {
    const twoWordKey = `${parts[0]} ${parts[1]}`;
    if (commandMap[twoWordKey]) {
      return commandMap[twoWordKey](parts.slice(2));
    }
  }

  // Single word commands
  const cmd = parts[0].toLowerCase();
  const args = parts.slice(1);

  if (commandMap[cmd]) {
    return commandMap[cmd](args);
  }

  return [
    {
      type: "error",
      content: `Unknown command: ${cmd}. Type 'help' for available commands.`,
    },
  ];
}

// ═══════════════════════════════════════════════════
// Terminal Component
// ═══════════════════════════════════════════════════

const initialOutput: OutputItem[] = [{ type: "system", content: WELCOME_BANNER }];

/**
 * Componente interactivo tipo terminal para desarrolladores.
 *
 * Soporta comandos: help, topics list/approve/reject/discover,
 * script generate/view/regenerate, status, clear, echo.
 * Conexión vía API REST al backend o modo offline.
 */
export function Terminal() {
  const [output, setOutput] = useState<OutputItem[]>(initialOutput);
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<string[]>([]);
  const [historyIdx, setHistoryIdx] = useState(-1);
  const [isExecuting, setIsExecuting] = useState(false);

  const outputRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom on new output
  useEffect(() => {
    if (outputRef.current) {
      const el = outputRef.current;
      requestAnimationFrame(() => {
        el.scrollTop = el.scrollHeight;
      });
    }
  }, [output]);

  // Focus input on mount and click
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const focusInput = useCallback(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = useCallback(
    async (cmd: string) => {
      if (isExecuting) return;
      setIsExecuting(true);

      const trimmed = cmd.trim();
      setHistory((prev) => [...prev, trimmed]);
      setHistoryIdx(-1);

      // Show input in output
      setOutput((prev) => [...prev, { type: "input", content: `>_ ${trimmed}` }]);

      if (trimmed) {
        const results = await executeCommand(trimmed);

        // Handle clear command immediately
        if (trimmed.toLowerCase() === "clear") {
          setOutput([]);
        } else {
          setOutput((prev) => [...prev, ...results]);
        }
      }

      setIsExecuting(false);
      // Keep focus after execution
      requestAnimationFrame(() => inputRef.current?.focus());
    },
    [isExecuting]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        handleSubmit(input);
        setInput("");
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        if (history.length === 0) return;
        const newIdx = historyIdx === -1 ? history.length - 1 : Math.max(0, historyIdx - 1);
        setHistoryIdx(newIdx);
        setInput(history[newIdx]);
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        if (historyIdx === -1) return;
        if (historyIdx >= history.length - 1) {
          setHistoryIdx(-1);
          setInput("");
        } else {
          const newIdx = historyIdx + 1;
          setHistoryIdx(newIdx);
          setInput(history[newIdx]);
        }
      }
    },
    [input, history, historyIdx, handleSubmit]
  );

  // Render output line
  const renderOutputItem = (item: OutputItem, index: number) => {
    switch (item.type) {
      case "input":
        return (
          <div key={index} className="text-white/90 font-mono whitespace-pre-wrap">
            {item.content}
          </div>
        );
      case "output":
        return (
          <div
            key={index}
            className="text-cyber-green font-mono whitespace-pre-wrap"
          >
            {item.content}
          </div>
        );
      case "error":
        return (
          <div
            key={index}
            className="text-cyber-red font-mono whitespace-pre-wrap"
          >
            {item.content}
          </div>
        );
      case "system":
        return (
          <div
            key={index}
            className="text-cyber-cyan font-mono whitespace-pre-wrap"
          >
            {item.content}
          </div>
        );
      case "table":
        return (
          <div key={index} className="font-mono">
            <div className="text-cyber-cyan/70 text-xs tracking-wider uppercase mb-1">
              ── {item.content} ──
            </div>
            <div className="text-cyber-green whitespace-pre-wrap">
              {item.lines?.join("\n")}
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div
      className="relative rounded-xl overflow-hidden border border-glass-border bg-[#0a0a0a] shadow-2xl"
      style={{ minHeight: "520px" }}
    >
      {/* Terminal header bar */}
      <div className="flex items-center gap-2 px-4 py-2 bg-[#111] border-b border-white/5">
        <div className="w-3 h-3 rounded-full bg-cyber-red/80" />
        <div className="w-3 h-3 rounded-full bg-cyber-yellow/80" />
        <div className="w-3 h-3 rounded-full bg-cyber-green/80" />
        <span className="ml-3 text-[10px] font-mono text-gray-500 tracking-wider uppercase">
          Terminal — Developer Console
        </span>
        <span
          className={`ml-auto text-[10px] font-mono ${
            isApiConnected ? "text-cyber-green" : "text-cyber-red"
          }`}
        >
          {isApiConnected ? "● ONLINE" : "○ OFFLINE"}
        </span>
      </div>

      {/* Output area */}
      <div
        ref={outputRef}
        className="p-4 overflow-y-auto font-mono text-sm leading-relaxed select-text"
        style={{
          height: "460px",
          background: "#0a0a0a",
          scrollBehavior: "smooth",
        }}
        onClick={focusInput}
      >
        {output.length === 0 ? null : (
          <div className="space-y-0.5">{output.map(renderOutputItem)}</div>
        )}

        {/* Blinking cursor at end of output */}
        {!isExecuting && (
          <div className="inline-flex items-center gap-0 mt-1">
            <span className="text-cyber-cyan font-bold">{" >_ "}</span>
            <span className="text-white/90">&nbsp;</span>
            <span
              className="inline-block w-2 h-4 bg-cyber-cyan animate-pulse"
              style={{ animation: "terminal-blink 1s step-end infinite" }}
            />
          </div>
        )}
        {isExecuting && (
          <div className="inline-flex items-center gap-2 mt-1 text-gray-500">
            <span className="inline-block w-3 h-3 border-2 border-cyber-cyan border-t-transparent rounded-full animate-spin" />
            <span className="text-xs font-mono">Executing...</span>
          </div>
        )}
      </div>

      {/* Input line */}
      <div className="flex items-center px-4 py-2.5 bg-[#0d0d0d] border-t border-white/5">
        <span className="text-cyber-cyan font-bold font-mono text-sm mr-2 shrink-0">
          {" >_ "}
        </span>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a command..."
          disabled={isExecuting}
          className="terminal-input flex-1 bg-transparent text-white/90 font-mono text-sm outline-none border-none placeholder-gray-600 disabled:opacity-40"
          spellCheck={false}
          autoComplete="off"
          autoCorrect="off"
        />
        <div className="text-[10px] font-mono text-gray-600 shrink-0 hidden sm:block">
          Enter to run · ↑↓ for history
        </div>
      </div>

      {/* Terminal-specific styles */}
      <style jsx>{`
        @keyframes terminal-blink {
          0%,
          100% {
            opacity: 1;
          }
          50% {
            opacity: 0;
          }
        }
        .terminal-input::selection {
          background: rgba(0, 240, 255, 0.3);
          color: white;
        }
      `}</style>
    </div>
  );
}
