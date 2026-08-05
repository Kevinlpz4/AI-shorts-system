import { NextResponse } from "next/server";
import path from "node:path";

import {
  extractVersion,
  getVenvPython,
  isRuntimeDaemonRunning,
  resolveRepoRoot,
  runProbe,
  SCRIPT_CONFIG,
} from "../_lib";
import type { InfoResponse, RuntimeConfigInfo } from "@/types/runtime";

/**
 * GET /api/runtime/info
 *
 * READ-ONLY: versión (fs), config defaults (probe), liveness del daemon (pgrep).
 * version "unknown" si no se pudo extraer — honesto, nunca mock.
 */
export async function GET(): Promise<Response> {
  const root = resolveRepoRoot();
  const version =
    root !== null
      ? extractVersion(path.join(root, "src", "runtime", "__main__.py"))
      : "unknown";
  const python = getVenvPython();

  let config: RuntimeConfigInfo | null = null;
  if (python !== null) {
    const probe = await runProbe(SCRIPT_CONFIG);
    if (probe.ok) {
      try {
        config = JSON.parse(probe.stdout) as RuntimeConfigInfo;
      } catch {
        config = null;
      }
    }
  }

  const liveness = await isRuntimeDaemonRunning();

  const body: InfoResponse = {
    status: "ok",
    version,
    config,
    is_running: liveness.is_running,
    venv_available: python !== null,
    repo_root: root,
    ...(liveness.liveness_check !== undefined
      ? { liveness_check: liveness.liveness_check }
      : {}),
  };
  return NextResponse.json(body);
}
