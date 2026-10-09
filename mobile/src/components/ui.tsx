import { ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';

export const colors = {
  canvas: '#F5F6FA',
  card: '#FFFFFF',
  border: '#E3E6EE',
  text: '#141A2A',
  muted: '#5B6478',
  primary: '#6D28D9',
  allow: '#15803D',
  allowSoft: '#E8F7EE',
  deny: '#C81E1E',
  denySoft: '#FDECEC',
  amber: '#B45309',
  amberSoft: '#FEF5E3',
  neutralSoft: '#F0F2F7',
};

const TONE: Record<string, [string, string]> = {
  allowed: [colors.allowSoft, colors.allow],
  approved: [colors.allowSoft, colors.allow],
  succeeded: [colors.allowSoft, colors.allow],
  no_signals: [colors.allowSoft, colors.allow],
  denied: [colors.denySoft, colors.deny],
  high: [colors.denySoft, colors.deny],
  pending: [colors.amberSoft, colors.amber],
  pending_approval: [colors.amberSoft, colors.amber],
  review: [colors.amberSoft, colors.amber],
  elevated: [colors.amberSoft, colors.amber],
};

export function toneColor(value: string): string {
  return (TONE[value] ?? [colors.neutralSoft, colors.border])[1];
}

export function Badge({ value, label }: { value: string; label?: string }) {
  const [bg, fg] = TONE[value] ?? [colors.neutralSoft, colors.muted];
  return (
    <Text style={[styles.badge, { backgroundColor: bg, color: fg }]}>{label ?? value.replace(/_/g, ' ')}</Text>
  );
}

export function Card({ children, accent }: { children: ReactNode; accent?: string }) {
  return <View style={[styles.card, accent ? { borderLeftWidth: 4, borderLeftColor: accent } : null]}>{children}</View>;
}

export function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={styles.rowValue} selectable>{value}</Text>
    </View>
  );
}

export function Demo() {
  return <Text style={styles.demo}>DEMO ENVIRONMENT · mock tools only</Text>;
}

export function ErrorBox({ message }: { message: string }) {
  return <Text style={styles.error}>{message} — pull down to retry.</Text>;
}

export const screen = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.canvas },
  content: { padding: 16, gap: 12, paddingBottom: 40 },
  title: { fontSize: 24, fontWeight: '700', color: colors.text },
  subtitle: { fontSize: 14, color: colors.muted },
  empty: { color: colors.muted, textAlign: 'center', marginTop: 24 },
  cardTitle: { fontSize: 16, fontWeight: '700', color: colors.text },
  mono: { fontFamily: 'monospace', fontSize: 12, color: colors.muted },
});

const styles = StyleSheet.create({
  badge: {
    fontSize: 12,
    fontWeight: '700',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 999,
    overflow: 'hidden',
    alignSelf: 'flex-start',
    textTransform: 'capitalize',
  },
  card: { backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border, borderRadius: 12, padding: 14, gap: 8 },
  row: { gap: 2 },
  rowLabel: { fontSize: 12, fontWeight: '600', color: colors.muted },
  rowValue: { fontSize: 14, color: colors.text },
  demo: { fontSize: 11, color: colors.amber, fontWeight: '700', letterSpacing: 0.5 },
  error: { color: colors.deny, backgroundColor: colors.denySoft, padding: 10, borderRadius: 8 },
});
