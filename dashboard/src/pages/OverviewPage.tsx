import { useCallback, useEffect, useState } from 'react';
import { api } from '../services/api';
import type { ApprovalResponse, OverviewResponse } from '../types/api';
import { formatDate, timeUntil } from '../utils/time';
import { Badge, EmptyState, ErrorState, LoadingState, PageHeader, errorText, humanize } from '../components/ui';
import type { Tab } from '../App';

export function OverviewPage({ onNavigate }: { onNavigate: (tab: Tab) => void }) {
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [pending, setPending] = useState<ApprovalResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    Promise.all([api.getOverview(), api.getApprovals('pending')])
      .then(([o, a]) => {
        setData(o);
        setPending(a.approvals);
      })
      .catch((e) => setError(errorText(e)))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
    const id = window.setInterval(load, 10000);
    return () => window.clearInterval(id);
  }, [load]);

  if (loading) return <LoadingState label="Loading overview…" />;
  if (error && !data) return <ErrorState message={error} onRetry={load} />;
  if (!data) return <EmptyState title="No data available" />;

  const metric = (label: string) => data.metrics.find((m) => m.label === label)?.value ?? 0;
  const lab = data.last_attack_lab_event;

  return (
    <section className="page">
      <PageHeader
        title="Overview"
        subtitle="Live state of the gateway, read from persisted events. Refreshes every 10 seconds."
        actions={<button className="btn btn-secondary" onClick={load}>Refresh</button>}
      />

      <div className="hero">
        <div className="hero-main">
          <div className="hero-eyebrow">Protection state · DEMO</div>
          <h3 className="hero-title">
            Gateway enforcing policy for <span className="accent">{data.active_task?.description ?? 'no active task'}</span>
          </h3>
          <p className="hero-copy">
            Every action from the demo agent is checked against task scope, tool allowlist, resource, destination and
            approval <em>before</em> a mock tool runs. Protection covers actions sent through this gateway only.
          </p>
          <div className="button-row">
            <button className="btn btn-primary" onClick={() => onNavigate('document-guard')}>Scan a document</button>
            <button className="btn btn-secondary" onClick={() => onNavigate('attack-lab')}>Run Attack Lab</button>
          </div>
        </div>
        <div className="hero-stats">
          <Stat label="Allowed" value={metric('Allowed')} tone="allow" />
          <Stat label="Blocked" value={metric('Blocked')} tone="deny" />
          <Stat label="Pending approvals" value={metric('Pending Approvals')} tone="pending" />
          <Stat label="Mock executor calls" value={data.executor_calls_total} tone="neutral" />
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-head">
            <h3>Pending approvals</h3>
            <button className="btn btn-sm btn-secondary" onClick={() => onNavigate('approvals')}>Open approvals</button>
          </div>
          {pending.length === 0 ? (
            <EmptyState title="Nothing waiting">Run “Vendor email (needs human approval)” in Attack Lab to create one.</EmptyState>
          ) : (
            <ul className="mini-list">
              {pending.slice(0, 4).map((a) => (
                <li key={a.approval_id}>
                  <div>
                    <span className="mono">{a.tool_name}</span> → <strong>{a.destination || a.resource || '—'}</strong>
                  </div>
                  <span className="muted">{timeUntil(a.expires_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <div className="card-head">
            <h3>Last Attack Lab result</h3>
            <button className="btn btn-sm btn-secondary" onClick={() => onNavigate('attack-lab')}>Open Attack Lab</button>
          </div>
          {lab ? (
            <dl className="kv">
              <dt>Decision</dt>
              <dd><Badge value={lab.authorization} /></dd>
              <dt>Tool</dt>
              <dd className="mono">{lab.tool_name}</dd>
              <dt>Reason</dt>
              <dd>{lab.authorization_reason}</dd>
              <dt>When</dt>
              <dd>{formatDate(lab.timestamp)}</dd>
            </dl>
          ) : (
            <EmptyState title="No Attack Lab runs yet">Run a scenario to see the enforced trace here.</EmptyState>
          )}
        </div>
      </div>

      <div className="explain-strip">
        <div>
          <Badge value="review" label="Document risk detected" />
          <p>Heuristic. Document Guard flags suspicious text; it never authorizes or blocks anything.</p>
        </div>
        <div>
          <Badge value="denied" label="Action blocked by gateway" />
          <p>Enforced. The backend policy refuses the action; the mock executor is never called.</p>
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <h3>Recent decisions</h3>
          <button className="btn btn-sm btn-secondary" onClick={() => onNavigate('events')}>All events</button>
        </div>
        {data.recent_events.length === 0 ? (
          <EmptyState title="No events yet">Decisions appear here as soon as an action reaches the gateway.</EmptyState>
        ) : (
          <div className="table-wrap flush">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Tool</th>
                  <th>Decision</th>
                  <th>Execution</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_events.slice(0, 6).map((ev) => (
                  <tr key={ev.event_id}>
                    <td className="nowrap">{formatDate(ev.timestamp)}</td>
                    <td className="mono">{ev.tool_name ?? '—'}</td>
                    <td><Badge value={ev.authorization} /></td>
                    <td><Badge value={ev.execution_status} label={humanize(ev.execution_status)} /></td>
                    <td className="reason-cell" title={ev.authorization_reason}>{ev.authorization_reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

function Stat({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className={`stat tone-text-${tone}`}>
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}
