import { API_BASE_URL } from '../constants/config';
import type { HealthResponse } from '../types/health';
import type {
  ApprovalList,
  ApprovalResponse,
  DocumentAgentRunResponse,
  DocumentScanResponse,
  EventList,
  OverviewResponse,
  TaskList,
  TaskResponse,
} from '../types/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options?.headers },
    });
  } catch {
    throw new Error(`Cannot reach backend at ${API_BASE_URL}`);
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.error?.message;
    throw new Error(message ? `${message} (HTTP ${res.status})` : `API error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getHealth: () => request<HealthResponse>('/health'),

  getOverview: () => request<OverviewResponse>('/api/v1/overview'),

  getTasks: () => request<TaskList>('/api/v1/tasks'),
  getTask: (id: string) => request<TaskResponse>(`/api/v1/tasks/${id}`),

  getApprovals: (status = 'pending') => request<ApprovalList>(`/api/v1/approvals?status=${status}`),
  decideApproval: (approvalId: string, decision: 'approve' | 'deny') =>
    request<ApprovalResponse>(`/api/v1/approvals/${approvalId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision }),
    }),

  getEvents: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<EventList>(`/api/v1/events${qs}`);
  },

  scanDocument: (text: string) =>
    request<DocumentScanResponse>('/api/v1/document-guard/scan', {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),
  runDocumentAgent: (text: string) =>
    request<DocumentAgentRunResponse>('/api/v1/document-guard/agent-run', {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),
};
