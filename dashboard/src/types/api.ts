export interface HealthResponse {
  status: string;
  service: string;
  timestamp: string;
}

export interface OverviewMetric {
  label: string;
  value: number;
}

export interface OverviewResponse {
  mode: string;
  gateway_connected: boolean;
  metrics: OverviewMetric[];
  recent_events: ApiEvent[];
  active_task: { task_id: string; description: string; status: TaskStatus } | null;
  last_attack_lab_event: ApiEvent | null;
  executor_calls_total: number;
  attention_items: string[];
}

export interface TaskScope {
  allowed_tools: string[];
  resources: string[];
  destination_allowlist: string[];
  block_external_destinations: boolean;
}

export type TaskStatus = 'pending' | 'running' | 'blocked' | 'completed' | 'failed';

export interface TaskResponse {
  task_id: string;
  created_at: string;
  updated_at: string;
  status: TaskStatus;
  description: string;
  scope: TaskScope;
}

export interface TaskList {
  tasks: TaskResponse[];
  count: number;
}

export type AgentStatus = 'connected' | 'disconnected' | 'unknown';

export interface AgentResponse {
  agent_id: string;
  name: string;
  agent_type: string;
  status: AgentStatus;
  registered_at: string;
}

export interface AgentList {
  agents: AgentResponse[];
  count: number;
}

export type PolicyAction = 'allow' | 'deny' | 'require_approval';

export interface PolicyRule {
  tool: string;
  action: PolicyAction;
  description: string;
}

export interface PolicyResponse {
  policy_id: string;
  task_id: string;
  rules: PolicyRule[];
  updated_at: string;
}

export interface PolicyUpdate {
  rules: PolicyRule[];
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
  decided_by: string;
}

export interface ApprovalList {
  approvals: ApprovalResponse[];
  count: number;
}

export type AuthorizationResult = 'pending' | 'allowed' | 'denied';
export type ExecutionStatus = 'not_attempted' | 'succeeded' | 'failed';

export interface ApiEvent {
  event_id: string;
  task_id: string | null;
  agent_id: string | null;
  tool_name: string | null;
  event_type: string;
  authorization: AuthorizationResult;
  authorization_reason: string;
  execution_status: ExecutionStatus;
  execution_result: string | null;
  arguments: Record<string, unknown>;
  resource: string;
  destination: string;
  timestamp: string;
  details: Record<string, unknown>;
}

export interface EventList {
  events: ApiEvent[];
  count: number;
}

export interface GatewayExecuteRequest {
  task_id: string;
  agent_id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
  resource?: string;
  destination?: string;
  approval_id?: string;
}

export type GatewayAuthorization = 'allowed' | 'denied' | 'pending_approval';

export interface GatewayExecuteResponse {
  event_id: string;
  task_id: string;
  tool_name: string;
  authorization: GatewayAuthorization;
  authorization_reason: string;
  execution_status: ExecutionStatus;
  execution_result: string | null;
  /** Mock-executor invocations caused by this request (0 or 1). */
  executor_call_count: number;
  resource: string;
  destination: string;
  approval_id: string | null;
  timestamp: string;
}

export interface TraceStage {
  stage: string;
  status: string;
  detail: string | null;
}

export interface ScenarioResult {
  scenario_id: string;
  scenario_label: string;
  final_authorization: GatewayAuthorization;
  authorization_reason: string;
  execution_status: ExecutionStatus;
  /** Verified delta of the persisted mock-executor counter. */
  executor_call_count: number;
  executor_calls_before: number;
  executor_calls_after: number;
  event_id: string;
  approval_id: string | null;
  request: GatewayExecuteRequest;
  trace: TraceStage[];
}

export interface AttackLabResponse {
  mode: string;
  results: ScenarioResult[];
}

export type ScenarioId =
  | 'authorized_invoice_read'
  | 'local_summary'
  | 'prompt_injection_email'
  | 'unauthorized_file_delete'
  | 'approval_vendor_email';

export type FindingSeverity = 'review' | 'elevated' | 'high';
export type DocumentRiskLevel = 'no_signals' | FindingSeverity;

export interface DocumentFinding {
  type: string;
  severity: FindingSeverity;
  evidence: string;
  explanation: string;
}

export interface DocumentScanResponse {
  mode: string;
  risk_level: DocumentRiskLevel;
  findings: DocumentFinding[];
  stats: { characters: number; lines: number; sha256_prefix: string };
  disclaimer: string;
}

export interface DocumentAgentRunResponse {
  mode: string;
  scan: DocumentScanResponse;
  agent_rationale: string;
  result: ScenarioResult;
}