export function formatDate(value: string | undefined): string {
  if (!value) return 'N/A';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'N/A' : date.toISOString();
}
