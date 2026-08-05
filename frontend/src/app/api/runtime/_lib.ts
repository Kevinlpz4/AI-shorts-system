/**
 * Helpers server-only para los route handlers de `/api/runtime/*`.
 *
 * Prefijo `_` = no ruteable en App Router.
 * READ-ONLY: ejecuta probes con subprocess + filesystem, NUNCA mock silencioso.
 * Los SCRIPT_* son CONSTANTES del módulo — cero interpolación de input de usuario.
 */
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import fs from "node:fs";
import path from "node:path";

const execFileAsync = promisify(execFile);

/** Timeout de subprocess probes (design D2). */
export const PROBE_TIMEOUT_MS = 10_000;

/** ERE para pgrep: cubre `python -m runtime schedule` y `run.py schedule`. */
const DAEMON_PGREP_ERE = "runtime schedule|run\\.py schedule";

/** Regex de versión sobre src/runtime/__main__.py (design D4). */
const RUNTIME_VERSION_RE = /Runtime v(\d+\.\d+\.\d+)/;

/**
 * Resuelve la raíz del repo: env override `RUNTIME_REPO_ROOT` o walk-up desde
 * process.cwd() buscando un directorio con `src/runtime/` (marcador primario)
 * o `.git` (fallback). Devuelve null si no se encontró nada.
 */
export function resolveRepoRoot(): string | null {
  const override = process.env.RUNTIME_REPO_ROOT;
  if (override && override.trim() !== "") {
    return override.trim();
  }

  let fallbackGitRoot: string | null = null;
  let dir = process.cwd();

  for (;;) {
    if (fs.existsSync(path.join(dir, "src", "runtime"))) {
      return dir;
    }
    if (fallbackGitRoot === null && fs.existsSync(path.join(dir, ".git"))) {
      fallbackGitRoot = dir;
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }

  return fallbackGitRoot;
}

/** Path a `.venv/bin/python3` dentro del repoRoot; null si no existe. */
export function getVenvPython(): string | null {
  const root = resolveRepoRoot();
  if (root === null) return null;
  const candidate = path.join(root, ".venv", "bin", "python3");
  return fs.existsSync(candidate) ? candidate : null;
}

export interface ProbeResult {
  ok: boolean;
  stdout: string;
  stderr: string;
  message?: string;
}

/**
 * Ejecuta un probe Python con el venv del repo. NUNCA lanza:
 * devuelve {ok:false, message} ante venv ausente, exit ≠ 0 o timeout.
 * `args` adicionales se pasan tras `-c SCRIPT`.
 */
export async function runProbe(
  script: string,
  args: string[] = [],
  timeoutMs: number = PROBE_TIMEOUT_MS,
): Promise<ProbeResult> {
  const python = getVenvPython();
  if (python === null) {
    return {
      ok: false,
      stdout: "",
      stderr: "",
      message:
        "venv no disponible: falta .venv/bin/python3 en el repo. Ver frontend/docs/runtime-integration.md",
    };
  }

  const root = resolveRepoRoot();
  try {
    const { stdout, stderr } = await execFileAsync(python, ["-c", script, ...args], {
      cwd: root ?? undefined,
      timeout: timeoutMs,
      maxBuffer: 16 * 1024 * 1024,
    });
    return { ok: true, stdout: stdout.toString(), stderr: stderr.toString() };
  } catch (error) {
    const err = error as {
      code?: string | number;
      killed?: boolean;
      stdout?: Buffer | string;
      stderr?: Buffer | string;
      message?: string;
    };
    const stderrText = (err.stderr ?? "").toString();
    const stdoutText = (err.stdout ?? "").toString();
    const message = err.killed
      ? `probe excedió el timeout (${timeoutMs}ms)`
      : stderrText.trim() !== ""
        ? stderrText.trim().split("\n").slice(-3).join("\n")
        : err.message ?? "probe falló";
    return { ok: false, stdout: stdoutText, stderr: stderrText, message };
  }
}

/**
 * Script Python CONSTANTE: importa el catálogo de fuentes del runtime y
 * serializa cada SourceDefinition a JSON (id, provider, technology, categories,
 * enabled, priority, poll_interval→minutos, metadata.url).
 */
export const SCRIPT_SOURCES = `
import json
import sys

sys.path.insert(0, "src")

from runtime.providers.catalog import ALL_SOURCES


def _serialize(source):
    metadata = source.metadata or {}
    return {
        "id": source.id,
        "provider": source.provider,
        "technology": source.technology,
        "categories": list(source.categories),
        "enabled": bool(source.enabled),
        "priority": int(source.priority),
        "poll_interval_minutes": int(source.poll_interval.total_seconds() // 60),
        "url": metadata.get("url"),
    }


print(json.dumps([_serialize(source) for source in ALL_SOURCES]))
`.trim();

/**
 * Script Python CONSTANTE: importa RuntimeConfig y serializa los defaults
 * (storage_base_path es Path → str; default=str cubre timedeltas residuales).
 */
export const SCRIPT_CONFIG = `
import dataclasses
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")

from runtime.config import RuntimeConfig


def _clean(value):
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(item) for item in value]
    return value


config = dataclasses.asdict(RuntimeConfig())
print(json.dumps(_clean(config), default=str))
`.trim();

/**
 * Extrae la versión del runtime leyendo src/runtime/__main__.py
 * (regex /Runtime v(\d+\.\d+\.\d+)/). Fallback "unknown".
 */
export function extractVersion(filePath: string): string {
  try {
    const content = fs.readFileSync(filePath, "utf8");
    const match = RUNTIME_VERSION_RE.exec(content);
    return match ? match[1] : "unknown";
  } catch {
    return "unknown";
  }
}

export interface DaemonLiveness {
  is_running: boolean;
  liveness_check?: string;
}

/**
 * Liveness del daemon de schedule vía pgrep (ERE alternation).
 * exit 0 → running; exit 1/sin match → false; pgrep ausente → false + liveness_check.
 */
export async function isRuntimeDaemonRunning(): Promise<DaemonLiveness> {
  try {
    await execFileAsync("pgrep", ["-f", DAEMON_PGREP_ERE]);
    return { is_running: true };
  } catch (error) {
    const err = error as NodeJS.ErrnoException;
    if (err.code === "ENOENT") {
      return { is_running: false, liveness_check: "pgrep unavailable" };
    }
    return { is_running: false };
  }
}
