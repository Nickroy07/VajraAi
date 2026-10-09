export function formatDate(value: string | null | undefined): string {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? '—'
    : date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'medium' });
}

export function timeUntil(value: string | null | undefined, now = Date.now()): string {
  if (!value) return '—';
  const ms = new Date(value).getTime() - now;
  if (Number.isNaN(ms)) return '—';
  if (ms <= 0) return 'expired';
  const mins = Math.floor(ms / 60000);
  const secs = Math.floor((ms % 60000) / 1000);
  return mins > 0 ? `${mins}m ${secs}s left` : `${secs}s left`;
}
