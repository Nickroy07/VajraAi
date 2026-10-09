import { useCallback, useEffect, useState } from 'react';
import { RefreshControl, ScrollView, Text } from 'react-native';
import { Badge, Card, Demo, ErrorBox, Row, screen } from '../src/components/ui';
import { api } from '../src/services/api';
import type { TaskResponse } from '../src/types/api';

export default function TasksScreen() {
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      setTasks((await api.getTasks()).tasks);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    }
  }, []);

  useEffect(() => {
    load();
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
      {tasks.map((t) => (
        <Card key={t.task_id}>
          <Text style={screen.cardTitle}>{t.description}</Text>
          <Badge value={t.status === 'running' ? 'allowed' : 'pending'} label={t.status} />
          <Row label="Allowed tools" value={t.scope.allowed_tools.join(', ') || 'none'} />
          <Row label="Resources" value={t.scope.resources.join(', ') || 'none'} />
          <Row
            label="Destinations"
            value={
              t.scope.destination_allowlist.length
                ? t.scope.destination_allowlist.join(', ')
                : t.scope.block_external_destinations
                  ? 'All external destinations blocked'
                  : 'none'
            }
          />
          <Text style={screen.mono}>{t.task_id}</Text>
        </Card>
      ))}
    </ScrollView>
  );
}
