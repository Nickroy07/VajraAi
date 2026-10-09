import { BACKEND_BASE_URL } from '../constants/config';
import type { HealthResponse } from '../types/health';

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${BACKEND_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed (${response.status})`);
  }
  return (await response.json()) as HealthResponse;
}
