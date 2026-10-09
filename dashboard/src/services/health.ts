import { api } from './api';
import type { HealthResponse } from '../types/health';

export function getHealth(): Promise<HealthResponse> {
  return api.getHealth();
}
