import { PropsWithChildren } from 'react';
import { StyleSheet, Text, View } from 'react-native';

type StatusCardProps = PropsWithChildren<{ online?: boolean }>;

export function StatusCard({ children, online }: StatusCardProps) {
  return (
    <View style={styles.card}>
      {typeof online === 'boolean' && (
        <StatusLine label="Backend" value={online ? 'Online' : 'Offline'} />
      )}
      {children}
    </View>
  );
}

export function StatusLine({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.line}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#0B1020',
    borderRadius: 14,
    padding: 16,
    gap: 8,
    width: '100%',
  },
  line: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  label: {
    color: '#98A2B3',
    fontSize: 14,
  },
  value: {
    color: '#EAECF0',
    fontSize: 14,
    fontWeight: '600',
    flexShrink: 1,
    textAlign: 'right',
  },
});
