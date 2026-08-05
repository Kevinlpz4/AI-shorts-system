import { NextResponse } from "next/server";
import fs from "node:fs";
import path from "node:path";

import { resolveRepoRoot } from "../../_lib";
import type { LearningReportsResponse, RuntimeReport } from "@/types/runtime";

/**
 * GET /api/runtime/learning/reports
 *
 * READ-ONLY: lee repoRoot/simulation_reports/simulation_report.json.
 * Existe → {status:"ok", simulated:true, note, reports:[{name, generated_at, report}]}.
 * No existe / ilegible → {status:"empty", reports:[]} honesto.
 */
export async function GET(): Promise<Response> {
  const root = resolveRepoRoot();
  const empty: LearningReportsResponse = { status: "empty", reports: [] };

  if (root === null) return NextResponse.json(empty);

  const filePath = path.join(root, "simulation_reports", "simulation_report.json");
  if (!fs.existsSync(filePath)) return NextResponse.json(empty);

  try {
    const raw = JSON.parse(fs.readFileSync(filePath, "utf8")) as Record<string, unknown>;
    const stat = fs.statSync(filePath);
    const report: RuntimeReport = {
      name: "simulation_report.json",
      generated_at: stat.mtime.toISOString(),
      report: raw,
    };
    const body: LearningReportsResponse = {
      status: "ok",
      simulated: true,
      note: "datos simulados — no métricas de producción",
      reports: [report],
    };
    return NextResponse.json(body);
  } catch {
    return NextResponse.json(empty);
  }
}
