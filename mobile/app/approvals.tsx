import { useCallback, useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { api } from '../src/services/api';

export default function ApprovalsScreen() {
  const [approvals, setApprovals] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const load = useCallback(() => {
    api.getApprovals('pending')
      .then((d: any) => setApprovals(d.approvals))
      .catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => { load(); }, [load]);

  const decide = (id: string, decision: 'approve' | 'deny') => {
    api.decideApproval(id, decision)
      .then(() => { setMsg(`Successfully ${decision}d`); load(); })
      .catch((e: Error) => setMsg(`Failed: ${e.message}`));
  };

  if (error) return <View style={styles.container}><Text style={styles.error}>Error: {error}</Text></View>;

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Approvals</Text>
      <Text style={styles.demo}>DEMO ENVIRONMENT</Text>
      {msg && <Text style={styles.msg}>{msg}</Text>}
      {approvals.length === 0 && <Text style={styles.empty}>No pending approvals</Text>}
      {approvals.map((a: any) => (
        <View key={a.approval_id} style={styles.card}>
          <Text style={styles.cardTitle}>{a.tool_name}</Text>
          <Text style={styles.mono}>Resource: {a.resource || '-'}</Text>
          <Text>Reason: {a.reason || '-'}</Text>
          <View style={styles.actions}>
            <TouchableOpacity style={styles.approveBtn} onPress={() => decide(a.approval_id, 'approve')}>
              <Text style={styles.btnText}>Approve</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.denyBtn} onPress={() => decide(a.approval_id, 'deny')}>
              <Text style={styles.btnText}>Deny</Text>
            </TouchableOpacity>
          </View>
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
  msg: { padding: 8, backgroundColor: '#F0FDF4', borderRadius: 6, marginBottom: 8, color: '#166534' },
  empty: { color: '#64748B', textAlign: 'center', marginTop: 32 },
  card: { backgroundColor: '#FFF', borderWidth: 1, borderColor: '#E2E8F0', borderRadius: 8, padding: 12, marginBottom: 8 },
  cardTitle: { fontSize: 15, fontWeight: '600' },
  mono: { fontFamily: 'monospace', fontSize: 11, color: '#64748B' },
  actions: { flexDirection: 'row', gap: 8, marginTop: 8 },
  approveBtn: { backgroundColor: '#16A34A', paddingVertical: 6, paddingHorizontal: 14, borderRadius: 6 },
  denyBtn: { backgroundColor: '#DC2626', paddingVertical: 6, paddingHorizontal: 14, borderRadius: 6 },
  btnText: { color: '#FFF', fontWeight: '600', fontSize: 13 },
});