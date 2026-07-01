// ═════════════════════════════════════════════════════════
// Shared Utilities — helpers puros sin estado
// ═════════════════════════════════════════════════════════
// Funciones reutilizables extraídas de duplicaciones en stores
// y componentes. Son puras: mismo input → mismo output.

import type { ScriptData } from "@/types";

/** Obtiene la base URL de la API desde env var, o vacío para modo mock */
export function getApiBase(): string {
  return typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL
    : "";
}

/**
 * Mapea la respuesta JSON de la API de scripts → tipo ScriptData.
 * Convierte snake_case de la API a camelCase del frontend.
 */
export function mapScriptFromApi(data: Record<string, unknown>): ScriptData {
  return {
    id: data.id as string,
    topicId: data.topic_id as string,
    hook: data.hook as string,
    body: data.body as string,
    cta: data.cta as string,
    duration: (data.duration as number) || 60,
    tone: (data.tone as string) || "informative",
    format: (data.format as string) || "youtube-shorts",
    wordCount: (data.word_count as number) || 0,
    isValid: (data.is_valid as boolean) ?? true,
    createdAt: (data.created_at as string) || new Date().toISOString(),
    updatedAt: (data.updated_at as string) || new Date().toISOString(),
  };
}

/**
 * Formatea una fecha ISO a texto relativo ("Just now", "3h ago", "5d ago").
 */
export function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const hours = Math.floor(diff / (1000 * 60 * 60));
  if (hours < 1) return "Just now";
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}
