export interface OverviewMetric {
  label: string;
  value: number;
}

export interface ApiEvent {
  event_id: string;
  task_id: string | null;
  tool_name: string | null;
  event_type: string;
  authorization: 'pending' | 'allowed' | 'denied';
  authorization_reason: string;
  execution_status: 'not_attempted' | 'succeeded' | 'failed';
  resource: string;
  destination: string;
  timestamp: string;
}

export interface OverviewResponse {
  mode: string;
  gateway_connected: boolean;
  metrics: OverviewMetric[];
  recent_events: ApiEvent[];
  active_task: { task_id: string; description: string; status: string } | null;
  executor_calls_total: number;
  attention_items: string[];
}

export interface TaskResponse {
  task_id: string;
  status: string;
  description: string;
  scope: {
    allowed_tools: string[];
    resources: string[];
    destination_allowlist: string[];
    block_external_destinations: boolean;
  };
}

export interface TaskList {
  tasks: TaskResponse[];
  count: number;
}

export type ApprovalStatus = 'pending' | 'approved' | 'denied' | 'expired' | 'consumed';

export interface ApprovalResponse {
  approval_id: string;
  task_id: string;
  agent_id: string | null;
  tool_name: string;
  arguments: Record<string, unknown>;
  arguments_hash: string;
  resource: string;
  destination: string;
  reason: string;
  status: ApprovalStatus;
  expires_at: string;
  consumed_at: string | null;
  created_at: string;
  decided_at: string | null;
}

export interface ApprovalList {
  approvals: ApprovalResponse[];
  count: number;
}

export interface EventList {
  events: ApiEvent[];
  count: number;
}

export interface DocumentFinding {
  type: string;
  severity: 'review' | 'elevated' | 'high';
  evidence: string;
  explanation: string;
}

export interface DocumentScanResponse {
  risk_level: 'no_signals' | 'review' | 'elevated' | 'high';
  findings: DocumentFinding[];
  stats: { characters: number; lines: number; sha256_prefix: string };
  disclaimer: string;
}

export interface ScenarioResult {
  scenario_label: string;
  final_authorization: 'allowed' | 'denied' | 'pending_approval';
  authorization_reason: string;
  execution_status: string;
  executor_call_count: number;
  event_id: string;
  request: { tool_name: string; arguments: Record<string, unknown> };
  trace: { stage: string; status: string; detail: string | null }[];
}

export interface DocumentAgentRunResponse {
  scan: DocumentScanResponse;
  agent_rationale: string;
  result: ScenarioResult;
}
