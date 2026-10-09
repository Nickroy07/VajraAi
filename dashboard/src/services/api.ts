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
  DocumentScanResponse,
  DocumentAgentRunResponse,
  ScenarioResult,
} from '../types/api';

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, message: string, body: unknown = null) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

function errorMessage(status: number, body: unknown): string {
  const err = (body as { error?: { message?: string } } | null)?.error;
  return err?.message ? `${err.message} (HTTP ${status})` : `Request failed (HTTP ${status})`;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  if (BACKEND_BASE_URL === null) {
    throw new ApiError(0, 'Backend not configured — set VITE_BACKEND_BASE_URL at build time.');
  }
  let res: Response;
  try {
    res = await fetch(`${BACKEND_BASE_URL}${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options?.headers },
    });
  } catch {
    throw new ApiError(0, `Backend offline — could not reach ${BACKEND_BASE_URL}`);
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, errorMessage(res.status, body), body);
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
    request<ApprovalList>(`/api/v1/approvals?status=${encodeURIComponent(status)}`),
  decideApproval: (approvalId: string, decision: 'approve' | 'deny') =>
    request<ApprovalResponse>(`/api/v1/approvals/${approvalId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision }),
    }),

  executeApproval: (approvalId: string) =>
    request<ScenarioResult>(`/api/v1/approvals/${approvalId}/execute`, { method: 'POST' }),

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