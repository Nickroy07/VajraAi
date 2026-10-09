import { useCallback, useEffect, useState } from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Link } from 'expo-router';
import { StatusCard, StatusLine } from '../src/components/StatusCard';
import { Card, Demo, ErrorBox, colors, screen } from '../src/components/ui';
import { API_BASE_URL } from '../src/constants/config';
import { api } from '../src/services/api';
import type { OverviewResponse } from '../src/types/api';

const SHORTCUTS = [
  { href: '/document-guard', label: 'Document Guard', desc: 'Scan text before an agent reads it' },
  { href: '/approvals', label: 'Approvals', desc: 'Approve or reject exact actions' },
  { href: '/events', label: 'Events', desc: 'Persisted gateway decisions' },
  { href: '/tasks', label: 'Tasks', desc: 'Scopes the agent works within' },
] as const;

export default function HomeScreen() {
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      setOverview(await api.getOverview());
      setError(null);
    } catch (e) {
      setOverview(null);
      setError(e instanceof Error ? e.message : 'Unknown error');
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 10000);
    return () => clearInterval(id);
  }, [load]);

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const metric = (label: string) => overview?.metrics.find((m) => m.label === label)?.value ?? 0;

  return (
    <ScrollView
      style={screen.container}
      contentContainerStyle={screen.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <Text style={screen.subtitle}>Let AI work. Never let it overstep.</Text>
      <StatusCard online={!!overview}>
        <StatusLine label="Mode" value={overview ? 'DEMO gateway enforcing' : 'Not connected'} />
        <StatusLine label="Active task" value={overview?.active_task?.description ?? '—'} />
        <StatusLine label="Server" value={API_BASE_URL} />
      </StatusCard>
      <Demo />
      {error && <ErrorBox message={error} />}

      {overview && (
        <View style={styles.metrics}>
          <Metric label="Allowed" value={metric('Allowed')} color={colors.allow} />
          <Metric label="Blocked" value={metric('Blocked')} color={colors.deny} />
          <Metric label="Pending" value={metric('Pending Approvals')} color={colors.amber} />
        </View>
      )}

      {SHORTCUTS.map((s) => (
        <Link key={s.href} href={s.href} asChild>
          <Pressable accessibilityRole="button">
            <Card>
              <Text style={screen.cardTitle}>{s.label} ›</Text>
              <Text style={screen.subtitle}>{s.desc}</Text>
            </Card>
          </Pressable>
        </Link>
      ))}
      <Text style={screen.mono}>
        Protects only actions sent through this gateway. It does not intercept the ChatGPT app or other third-party AI apps.
      </Text>
    </ScrollView>
  );
}

function Metric({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <View style={styles.metric}>
      <Text style={[styles.metricValue, { color }]}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  metrics: { flexDirection: 'row', gap: 8 },
  metric: { flex: 1, backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border, borderRadius: 12, padding: 12 },
  metricValue: { fontSize: 26, fontWeight: '800' },
  metricLabel: { fontSize: 12, color: colors.muted, fontWeight: '600' },
});
