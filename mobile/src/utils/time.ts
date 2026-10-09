export function formatIso(ts: string | null | undefined): string {
  if (!ts) return 'N/A';
  const date = new Date(ts);
  return Number.isNaN(date.getTime()) ? 'N/A' : date.toLocaleString();
}

export function timeUntil(ts: string | null | undefined): string {
  if (!ts) return '—';
  const ms = new Date(ts).getTime() - Date.now();
  if (Number.isNaN(ms)) return '—';
  if (ms <= 0) return 'expired';
  const m = Math.floor(ms / 60000);
  const s = Math.floor((ms % 60000) / 1000);
  return m > 0 ? `${m}m ${s}s left` : `${s}s left`;
}
