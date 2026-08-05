import { NextResponse } from "next/server";

import { runProbe, SCRIPT_SOURCES } from "../_lib";
import type { RuntimeSource, SourcesResponse } from "@/types/runtime";

/**
 * GET /api/runtime/sources
 *
 * READ-ONLY: probe subprocess del catálogo real de fuentes del runtime.
 * ok → {status:"ok", sources, count} | fallo honesto → {status:"unavailable", ...}.
 */
export async function GET(): Promise<Response> {
  const result = await runProbe(SCRIPT_SOURCES);

  if (!result.ok) {
    const body: SourcesResponse = {
      status: "unavailable",
      message:
        result.message ?? "No se pudo leer el catálogo de fuentes del runtime.",
      hint: "ver frontend/docs/runtime-integration.md",
    };
    return NextResponse.json(body);
  }

  try {
    const sources = JSON.parse(result.stdout) as RuntimeSource[];
    const body: SourcesResponse = { status: "ok", sources, count: sources.length };
    return NextResponse.json(body);
  } catch {
    const body: SourcesResponse = {
      status: "unavailable",
      message: "El probe devolvió una salida no parseable.",
      hint: "ver frontend/docs/runtime-integration.md",
    };
    return NextResponse.json(body);
  }
}
