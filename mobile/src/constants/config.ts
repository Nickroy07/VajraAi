import { Platform } from 'react-native';

// Android emulator reaches the host machine at 10.0.2.2. For a physical phone set
// EXPO_PUBLIC_API_BASE_URL=http://<laptop-LAN-IP>:8000 before `npm run start`.
const DEFAULT_URL = Platform.select({
  android: 'http://10.0.2.2:8000',
  default: 'http://localhost:8000',
});

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ?? DEFAULT_URL;

export const BACKEND_BASE_URL = API_BASE_URL;
