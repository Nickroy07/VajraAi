import { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { StatusCard } from '../src/components/StatusCard';
import { api } from '../src/services/api';
import type { HealthResponse } from '../src/types/health';

export default function HomeScreen() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [overview, setOverview] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getHealth()
      .then((h) => {
        setHealth(h);
        return api.getOverview();
      })
      .then(setOverview)
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>VAJRA AI</Text>
        <StatusCard online={false} />
        <Text style={styles.error}>Disconnected: {error}</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>VAJRA AI</Text>
      <StatusCard online={!!health} />
      <Text style={styles.demo}>DEMO ENVIRONMENT</Text>

      {overview && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Overview</Text>
          <Text style={styles.mode}>Mode: {overview.mode}</Text>
          <View style={styles.metrics}>
            {overview.metrics?.map((m: any) => (
              <View key={m.label} style={styles.metricCard}>
                <Text style={styles.metricValue}>{m.value}</Text>
                <Text style={styles.metricLabel}>{m.label}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {overview?.attention_items?.map((item: string, i: number) => (
        <Text key={i} style={styles.attention}>{item}</Text>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC', padding: 16 },
  title: { fontSize: 24, fontWeight: '700', color: '#090D16', marginBottom: 8 },
  error: { color: '#DC2626', marginTop: 16 },
  demo: { fontSize: 11, color: '#D97706', fontWeight: '700', marginBottom: 16 },
  section: { marginVertical: 12 },
  sectionTitle: { fontSize: 16, fontWeight: '600', marginBottom: 8 },
  mode: { fontSize: 13, color: '#64748B' },
  metrics: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8 },
  metricCard: { backgroundColor: '#FFF', borderWidth: 1, borderColor: '#E2E8F0', borderRadius: 8, padding: 12, minWidth: 80 },
  metricValue: { fontSize: 24, fontWeight: '700', color: '#4F46E5' },
  metricLabel: { fontSize: 11, color: '#64748B' },
  attention: { fontSize: 12, color: '#92400E', backgroundColor: '#FFFBEB', padding: 8, borderRadius: 6, marginVertical: 4 },
});