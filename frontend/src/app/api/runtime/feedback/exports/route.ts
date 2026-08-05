import { NextResponse } from "next/server";
import fs from "node:fs";
import path from "node:path";

import { resolveRepoRoot } from "../../_lib";
import type { FeedbackExport, FeedbackExportsResponse } from "@/types/runtime";

const FEEDBACK_EXPORT_RE = /^feedback_session_.+\.json$/;

/**
 * GET /api/runtime/feedback/exports
 *
 * READ-ONLY: glob repoRoot/feedback_session_*.json (export_session cli.py:821).
 * Hay archivos → {status:"ok", exports:[{file, size, mtime, decisions?, session_id?}]}
 * con resumen por JSON parseable (counts de decisiones).
 * Sin archivos → {status:"empty", exports:[]} honesto.
 */
export async function GET(): Promise<Response> {
  const root = resolveRepoRoot();
  const empty: FeedbackExportsResponse = { status: "empty", exports: [] };

  if (root === null) return NextResponse.json(empty);

  let files: string[];
  try {
    files = fs.readdirSync(root).filter((name) => FEEDBACK_EXPORT_RE.test(name));
  } catch {
    return NextResponse.json(empty);
  }

  if (files.length === 0) return NextResponse.json(empty);

  const exportsList: FeedbackExport[] = files
    .map((name): FeedbackExport | null => {
      const fullPath = path.join(root, name);
      try {
        const stat = fs.statSync(fullPath);
        const raw = JSON.parse(fs.readFileSync(fullPath, "utf8")) as Record<string, unknown>;
        const decisions = Array.isArray(raw.decisions) ? raw.decisions.length : null;
        const session = (raw.session ?? {}) as Record<string, unknown>;
        return {
          file: name,
          size: stat.size,
          mtime: stat.mtime.toISOString(),
          decisions,
          session_id: typeof session.id === "string" ? session.id : undefined,
        };
      } catch {
        return null;
      }
    })
    .filter((entry): entry is FeedbackExport => entry !== null)
    .sort((a, b) => b.mtime.localeCompare(a.mtime));

  const body: FeedbackExportsResponse = { status: "ok", exports: exportsList };
  return NextResponse.json(body);
}
