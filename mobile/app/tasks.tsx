import { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { api } from '../src/services/api';

export default function TasksScreen() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getTasks()
      .then((d: any) => setTasks(d.tasks))
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <View style={styles.container}><Text style={styles.error}>Error: {error}</Text></View>;

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Tasks</Text>
      <Text style={styles.demo}>DEMO ENVIRONMENT</Text>
      {tasks.map((t: any) => (
        <View key={t.task_id} style={styles.card}>
          <Text style={styles.cardTitle}>{t.description}</Text>
          <Text style={styles.mono}>ID: {t.task_id}</Text>
          <Text>Status: {t.status}</Text>
          <Text>Allowed Tools: {t.scope?.allowed_tools?.join(', ') || 'none'}</Text>
          <Text>Resources: {t.scope?.resources?.join(', ') || 'none'}</Text>
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
  cardTitle: { fontSize: 15, fontWeight: '600' },
  mono: { fontFamily: 'monospace', fontSize: 11, color: '#64748B' },
});