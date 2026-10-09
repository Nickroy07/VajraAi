import { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { api } from '../src/services/api';

export default function EventsScreen() {
  const [events, setEvents] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getEvents({ limit: '50' })
      .then((d: any) => setEvents(d.events))
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <View style={styles.container}><Text style={styles.error}>Error: {error}</Text></View>;

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Events</Text>
      <Text style={styles.demo}>DEMO ENVIRONMENT</Text>
      {events.map((ev: any) => (
        <View key={ev.event_id} style={styles.card}>
          <View style={styles.row}>
            <Text style={styles.cardTitle}>{ev.tool_name || ev.event_type}</Text>
            <Text style={[styles.badge, ev.authorization === 'allowed' ? styles.allowed : styles.denied]}>
              {ev.authorization}
            </Text>
          </View>
          <Text style={styles.mono}>{ev.event_id}</Text>
          <Text>Execution: {ev.execution_status}</Text>
          <Text style={styles.reason}>{ev.authorization_reason}</Text>
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC', padding: 16 },
  title: { fontSize: 24, fontWeight: '700', marginBottom: 8 },
  demo: { fontSize: 11, color: '#D97706', fontWeight: '700', marginBottom: 16 },
  error: { color: '#DC2626' },
  card: { backgroundColor: '#FFF', borderWidth: 1, borderColor: '#E2E8F0', borderRadius: 8, padding: 12, marginBottom: 8 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardTitle: { fontSize: 14, fontWeight: '600' },
  mono: { fontFamily: 'monospace', fontSize: 10, color: '#64748B' },
  badge: { fontSize: 11, fontWeight: '700', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 },
  allowed: { backgroundColor: '#DCFCE7', color: '#166534' },
  denied: { backgroundColor: '#FEE2E2', color: '#991B1B' },
  reason: { fontSize: 11, color: '#64748B', marginTop: 4 },
});