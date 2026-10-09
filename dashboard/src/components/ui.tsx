import type { ReactNode } from 'react';
import type { ScenarioResult, TraceStage } from '../types/api';

type Tone = 'allow' | 'deny' | 'pending' | 'neutral' | 'accent';

const TONES: Record<string, Tone> = {
  allowed: 'allow',
  succeeded: 'allow',
  approved: 'allow',
  connected: 'allow',
  running: 'allow',
  no_signals: 'allow',
  denied: 'deny',
  failed: 'deny',
  high: 'deny',
  blocked: 'deny',
  error: 'deny',
  pending: 'pending',
  pending_approval: 'pending',
  review: 'pending',
  elevated: 'pending',
  expired: 'neutral',
  consumed: 'neutral',
  not_attempted: 'neutral',
  skipped: 'neutral',
  info: 'neutral',
};

export function toneFor(value: string | null | undefined): Tone {
  return (value && TONES[value]) || 'neutral';
}

export function humanize(value: string | null | undefined): string {
  if (!value) return '—';
  return value.replace(/_/g, ' ');
}

export function Badge({ value, label }: { value: string | null | undefined; label?: string }) {
  return <span className={`badge tone-${toneFor(value)}`}>{label ?? humanize(value)}</span>;
}

export function DemoTag({ children = 'DEMO' }: { children?: ReactNode }) {
  return <span className="demo-badge">{children}</span>;
}

export function PageHeader({
  title,
  subtitle,
  actions,
  tag = 'DEMO',
}: {
  title: string;
  subtitle?: ReactNode;
  actions?: ReactNode;
  tag?: string | null;
}) {
  return (
    <header className="page-header">
      <div>
        <div className="page-title-row">
          <h2>{title}</h2>
          {tag && <DemoTag>{tag}</DemoTag>}
        </div>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </header>
  );
}

export function LoadingState({ label }: { label: string }) {
  return (
    <div className="state state-loading" role="status">
      <span className="spinner" aria-hidden="true" /> {label}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="state state-error" role="alert">
      <strong>Could not load data.</strong> {message}
      {onRetry && (
        <button className="btn btn-sm btn-secondary" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="state state-empty">
      <strong>{title}</strong>
      {children && <div>{children}</div>}
    </div>
  );
}

export function errorText(e: unknown): string {
  return e instanceof Error ? e.message : 'Unknown error';
}

export function Trace({ stages }: { stages: TraceStage[] }) {
  return (
    <ol className="trace">
      {stages.map((s, i) => (
        <li key={i} className={`trace-step tone-${toneFor(s.status)}`}>
          <span className="trace-dot" aria-hidden="true">{i + 1}</span>
          <div className="trace-body">
            <div className="trace-head">
              <span className="trace-name">{s.stage}</span>
              {s.status !== 'info' && <Badge value={s.status} />}
            </div>
            {s.detail && <p className="trace-detail">{s.detail}</p>}
          </div>
        </li>
      ))}
    </ol>
  );
}

const OUTCOME_LABEL: Record<string, string> = {
  allowed: 'Allowed & executed',
  denied: 'Blocked before execution',
  pending_approval: 'Waiting for human approval',
};

export function ScenarioResultCard({ result, footer }: { result: ScenarioResult; footer?: ReactNode }) {
  const tone = toneFor(result.final_authorization);
  return (
    <article className={`result-card tone-border-${tone}`}>
      <div className="result-head">
        <div>
          <h3>{result.scenario_label}</h3>
          <div className={`result-outcome tone-text-${tone}`}>
            {OUTCOME_LABEL[result.final_authorization] ?? result.final_authorization}
          </div>
        </div>
        <div className={`delta-chip tone-${result.executor_call_count === 0 ? 'neutral' : 'allow'}`}>
          <span className="delta-value">Δ {result.executor_call_count}</span>
          <span className="delta-label">executor calls</span>
        </div>
      </div>
      <dl className="kv">
        <dt>Reason</dt>
        <dd>{result.authorization_reason}</dd>
        <dt>Tool</dt>
        <dd className="mono">{result.request.tool_name}</dd>
        <dt>Counter</dt>
        <dd className="mono">
          {result.executor_calls_before} → {result.executor_calls_after} (persisted mock-executor counter)
        </dd>
        <dt>Event ID</dt>
        <dd className="mono">{result.event_id}</dd>
        {result.approval_id && (
          <>
            <dt>Approval ID</dt>
            <dd className="mono">{result.approval_id}</dd>
          </>
        )}
      </dl>
      <Trace stages={result.trace} />
      {footer}
    </article>
  );
}

export function formatArgs(args: Record<string, unknown>): string {
  return Object.entries(args)
    .map(([k, v]) => `${k}: ${typeof v === 'string' ? v : JSON.stringify(v)}`)
    .join('\n');
}
