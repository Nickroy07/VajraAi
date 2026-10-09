import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

export default function RootLayout() {
  return (
    <>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: '#0B1020' },
          headerTintColor: '#FFFFFF',
          headerTitleStyle: { fontWeight: '700' },
        }}
      >
        <Stack.Screen name="index" options={{ title: 'VAJRA AI' }} />
        <Stack.Screen name="document-guard" options={{ title: 'Document Guard' }} />
        <Stack.Screen name="approvals" options={{ title: 'Approvals' }} />
        <Stack.Screen name="tasks" options={{ title: 'Tasks' }} />
        <Stack.Screen name="events" options={{ title: 'Events' }} />
      </Stack>
    </>
  );
}
