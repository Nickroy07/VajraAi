import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, RefreshControl, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Badge, Card, Demo, ErrorBox, Row, colors, screen } from '../src/components/ui';
import { api } from '../src/services/api';
import type { ApprovalResponse } from '../src/types/api';
import { formatIso, timeUntil } from '../src/utils/time';

export default function ApprovalsScreen() {
  const [approvals, setApprovals] = useState<ApprovalResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const load = useCallback(async () => {
    try {
      setApprovals((await api.getApprovals('pending')).approvals);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoaded(true);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, [load]);

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const decide = async (a: ApprovalResponse, decision: 'approve' | 'deny') => {
    setBusyId(a.approval_id);
    setMsg(null);
    try {
      const res = await api.decideApproval(a.approval_id, decision);
      setMsg({ ok: decision === 'approve', text: `${decision === 'approve' ? 'Approved' : 'Rejected'} ${a.tool_name} → ${a.destination || a.resource}. Status: ${res.status}.` });
    } catch (e) {
      setMsg({ ok: false, text: e instanceof Error ? e.message : 'Decision failed' });
    } finally {
      setBusyId(null);
      load();
    }
  };

  return (
    <ScrollView
      style={screen.container}
      contentContainerStyle={screen.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <Text style={screen.subtitle}>Each approval authorizes one exact action, once, before it expires.</Text>
      <Demo />
      {error && <ErrorBox message={error} />}
      {msg && <Text style={[styles.msg, msg.ok ? styles.msgOk : styles.msgBad]}>{msg.text}</Text>}
      {!loaded && <ActivityIndicator color={colors.primary} />}
      {loaded && !error && approvals.length === 0 && (
        <Text style={screen.empty}>No pending approvals. Run “Vendor email (needs human approval)” in the web Attack Lab.</Text>
      )}
      {approvals.map((a) => (
        <Card key={a.approval_id} accent={colors.amber}>
          <View style={styles.head}>
            <Text style={screen.cardTitle}>{a.tool_name}</Text>
            <Badge value={a.status} />
          </View>
          <Row label="Recipient" value={a.destination || '—'} />
          <Row label="Resource" value={a.resource || '—'} />
          <Row label="Arguments" value={Object.entries(a.arguments).map(([k, v]) => `${k}: ${String(v)}`).join('\n')} />
          <Row label="Policy reason" value={a.reason || '—'} />
          <Row label="Expires" value={`${formatIso(a.expires_at)} (${timeUntil(a.expires_at)})`} />
          <Text style={screen.mono}>task {a.task_id.slice(-4)} · args sha256 {a.arguments_hash.slice(0, 12)}…</Text>
          <View style={styles.actions}>
            <TouchableOpacity
              accessibilityRole="button"
              style={[styles.btn, styles.approve, busyId !== null && styles.disabled]}
              disabled={busyId !== null}
              onPress={() => decide(a, 'approve')}
            >
              <Text style={styles.btnText}>
                {busyId === a.approval_id ? 'Saving…' : a.destination ? `Approve email to ${a.destination}` : 'Approve this action'}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              accessibilityRole="button"
              style={[styles.btn, styles.deny, busyId !== null && styles.disabled]}
              disabled={busyId !== null}
              onPress={() => decide(a, 'deny')}
            >
              <Text style={[styles.btnText, { color: colors.deny }]}>Reject</Text>
            </TouchableOpacity>
          </View>
        </Card>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  head: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 8 },
  msg: { padding: 10, borderRadius: 8 },
  msgOk: { backgroundColor: colors.allowSoft, color: colors.allow },
  msgBad: { backgroundColor: colors.denySoft, color: colors.deny },
  actions: { gap: 8, marginTop: 4 },
  btn: { paddingVertical: 12, paddingHorizontal: 14, borderRadius: 10, alignItems: 'center' },
  approve: { backgroundColor: colors.allow },
  deny: { backgroundColor: colors.card, borderWidth: 1, borderColor: '#F0B4B4' },
  disabled: { opacity: 0.5 },
  btnText: { color: '#FFF', fontWeight: '700', fontSize: 15 },
});
