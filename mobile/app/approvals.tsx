import { SafeAreaView, StyleSheet, Text } from 'react-native';

export default function ApprovalsScreen() {
  return (
    <SafeAreaView style={styles.safe}>
      <Text style={styles.title}>Approvals</Text>
      <Text style={styles.body}>DEMO DATA: approvals queue placeholder.</Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#020617', padding: 20, gap: 12 },
  title: { color: '#F8FAFC', fontSize: 24, fontWeight: '700' },
  body: { color: '#CBD5E1', fontSize: 16 },
});
