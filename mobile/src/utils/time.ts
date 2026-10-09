export function formatIso(ts: string | undefined): string {
  if (!ts) return 'N/A';
  const date = new Date(ts);
  return Number.isNaN(date.getTime()) ? 'N/A' : date.toISOString();
}
