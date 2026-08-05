/**
 * SourceTag — pill de etiquetado honesto de la procedencia de datos.
 *
 * REAL   → datos vivos leídos del runtime (subprocess + filesystem).
 * LEGACY → datos del research BC vía API legacy /api/v1/* (sin cambios).
 * NA     → no disponible / CLI-only en este sprint.
 *
 * Usa SOLO tokens existentes (neon-*, gray-*) — sin clases nuevas.
 */

export type DataTier = "REAL" | "LEGACY" | "NA";

const TIER_STYLES: Record<DataTier, string> = {
  REAL: "bg-neon-green/10 border-neon-green/30 text-neon-green",
  LEGACY: "bg-neon-yellow/10 border-neon-yellow/30 text-neon-yellow",
  NA: "bg-gray-500/10 border-gray-500/30 text-gray-400",
};

export function SourceTag({
  tier,
  label,
  title,
}: {
  tier: DataTier;
  label?: string;
  title?: string;
}) {
  return (
    <span
      title={title}
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-[9px] font-mono font-semibold tracking-[0.15em] border whitespace-nowrap ${TIER_STYLES[tier]}`}
    >
      {label ?? tier}
    </span>
  );
}
