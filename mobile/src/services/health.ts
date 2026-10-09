import { BACKEND_BASE_URL } from '../constants/config';
import type { HealthResponse } from '../types/health';

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${BACKEND_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Backend request failed: ${response.status}`);
  }
  return (await response.json()) as HealthResponse;
}
