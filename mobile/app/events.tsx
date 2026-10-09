import { useCallback, useEffect, useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Badge, Card, Demo, ErrorBox, screen, toneColor } from '../src/components/ui';
import { api } from '../src/services/api';
import type { ApiEvent } from '../src/types/api';
import { formatIso } from '../src/utils/time';

export default function EventsScreen() {
  const [events, setEvents] = useState<ApiEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      setEvents((await api.getEvents({ limit: '50' })).events);
      setError(null);
    } catch (e) {
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

  return (
    <ScrollView
      style={screen.container}
      contentContainerStyle={screen.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <Demo />
      {error && <ErrorBox message={error} />}
      {!error && events.length === 0 && <Text style={screen.empty}>No events yet.</Text>}
      {events.map((ev) => (
        <Card key={ev.event_id} accent={toneColor(ev.authorization)}>
          <View style={styles.row}>
            <Text style={screen.cardTitle}>{ev.tool_name || ev.event_type}</Text>
            <Badge value={ev.authorization} />
          </View>
          <Text style={styles.reason}>{ev.authorization_reason}</Text>
          <Text style={screen.mono}>
            {formatIso(ev.timestamp)} · execution {ev.execution_status.replace(/_/g, ' ')}
          </Text>
          <Text style={screen.mono} selectable>{ev.event_id}</Text>
        </Card>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 8 },
  reason: { fontSize: 14, color: '#141A2A' },
});
