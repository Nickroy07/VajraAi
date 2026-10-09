import { API_BASE_URL } from '../constants/config';
import type { HealthResponse } from '../types/health';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getHealth: () => request<HealthResponse>('/health'),

  getOverview: () => request<any>('/api/v1/overview'),

  getTasks: () => request<any>('/api/v1/tasks'),
  getTask: (id: string) => request<any>(`/api/v1/tasks/${id}`),

  getAgents: () => request<any>('/api/v1/agents'),

  getApprovals: (status = 'pending') => request<any>(`/api/v1/approvals?status=${status}`),
  decideApproval: (approvalId: string, decision: 'approve' | 'deny') =>
    request<any>(`/api/v1/approvals/${approvalId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision }),
    }),

  getEvents: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<any>(`/api/v1/events${qs}`);
  },
};