import { BACKEND_BASE_URL } from '../constants/config';
import type {
  HealthResponse,
  OverviewResponse,
  TaskList,
  TaskResponse,
  AgentList,
  PolicyResponse,
  PolicyUpdate,
  ApprovalList,
  ApprovalResponse,
  EventList,
  ApiEvent,
  GatewayExecuteRequest,
  GatewayExecuteResponse,
  AttackLabResponse,
  ScenarioId,
} from '../types/api';

class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, body: unknown) {
    super(`API error ${status}`);
    this.status = status;
    this.body = body;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BACKEND_BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, body);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getHealth: () => request<HealthResponse>('/health'),

  getOverview: () => request<OverviewResponse>('/api/v1/overview'),

  getTasks: () => request<TaskList>('/api/v1/tasks'),
  getTask: (id: string) => request<TaskResponse>(`/api/v1/tasks/${id}`),
  createTask: (body: unknown) =>
    request<TaskResponse>('/api/v1/tasks', { method: 'POST', body: JSON.stringify(body) }),

  getAgents: () => request<AgentList>('/api/v1/agents'),

  getPolicy: (taskId: string) => request<PolicyResponse>(`/api/v1/tasks/${taskId}/policy`),
  updatePolicy: (taskId: string, body: PolicyUpdate) =>
    request<PolicyResponse>(`/api/v1/tasks/${taskId}/policy`, {
      method: 'PUT',
      body: JSON.stringify(body),
    }),

  getApprovals: (status = 'pending') =>
    request<ApprovalList>(`/api/v1/approvals?status=${status}`),
  decideApproval: (approvalId: string, decision: 'approve' | 'deny') =>
    request<ApprovalResponse>(`/api/v1/approvals/${approvalId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision }),
    }),

  getEvents: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<EventList>(`/api/v1/events${qs}`);
  },
  getEvent: (id: string) => request<ApiEvent>(`/api/v1/events/${id}`),

  gatewayExecute: (body: GatewayExecuteRequest) =>
    request<GatewayExecuteResponse>('/api/v1/gateway/execute', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  runAttackLab: (scenarioIds: ScenarioId[]) =>
    request<AttackLabResponse>('/api/v1/attack-lab/run', {
      method: 'POST',
      body: JSON.stringify({ scenario_ids: scenarioIds }),
    }),
};