import { Link } from 'expo-router';
import { SafeAreaView, ScrollView, StyleSheet, Text, View } from 'react-native';

import { StatusCard, StatusLine } from '../src/components/StatusCard';
import { BACKEND_BASE_URL } from '../src/constants/config';
import { useHealth } from '../src/hooks/useHealth';
import { formatIso } from '../src/utils/time';

export default function HomeScreen() {
  const { data, loading, error } = useHealth();

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>VAJRA AI</Text>
        <Text style={styles.tagline}>Let AI work. Never let it overstep.</Text>

        <StatusCard>
          <StatusLine label="Backend URL" value={BACKEND_BASE_URL} />
          <StatusLine
            label="Connectivity"
            value={loading ? 'Checking...' : error ? 'Offline' : 'Online'}
          />
          <StatusLine
            label="Gateway enforcement"
            value={error ? 'Not confirmed' : 'Backend reachable (status only)'}
          />
          <StatusLine label="Last update" value={formatIso(data?.timestamp)} />
        </StatusCard>

        <View style={styles.nav}>
          <Link href="/tasks" style={styles.link}>Tasks</Link>
          <Link href="/approvals" style={styles.link}>Approvals</Link>
          <Link href="/events" style={styles.link}>Events</Link>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#020617' },
  container: { padding: 20, gap: 16 },
  title: { color: '#F8FAFC', fontSize: 30, fontWeight: '700' },
  tagline: { color: '#CBD5E1', fontSize: 16 },
  nav: { gap: 8 },
  link: {
    color: '#93C5FD',
    fontSize: 16,
    textDecorationLine: 'underline',
  },
});
