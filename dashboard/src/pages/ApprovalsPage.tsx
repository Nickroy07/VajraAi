import { useCallback, useEffect, useState } from 'react';
import { api } from '../services/api';
import type { ApprovalResponse, TaskResponse } from '../types/api';
import { formatDate, timeUntil } from '../utils/time';
import { Badge, EmptyState, ErrorState, LoadingState, PageHeader, errorText, formatArgs } from '../components/ui';

const FILTERS = ['pending', 'approved', 'all'] as const;
type Filter = (typeof FILTERS)[number];

export function ApprovalsPage() {
  const [filter, setFilter] = useState<Filter>('pending');
  const [approvals, setApprovals] = useState<ApprovalResponse[]>([]);
  const [tasks, setTasks] = useState<Record<string, TaskResponse>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ tone: 'allow' | 'deny'; text: string } | null>(null);
  const [, setTick] = useState(0);

  const load = useCallback(() => {
    Promise.all([api.getApprovals(filter), api.getTasks()])
      .then(([a, t]) => {
        setApprovals(a.approvals);
        setTasks(Object.fromEntries(t.tasks.map((x) => [x.task_id, x])));
        setError(null);
      })
      .catch((e) => setError(errorText(e)))
      .finally(() => setLoading(false));
  }, [filter]);

  useEffect(() => {
    setLoading(true);
    load();
    const poll = window.setInterval(load, 5000);
    const clock = window.setInterval(() => setTick((n) => n + 1), 1000);
    return () => {
      window.clearInterval(poll);
      window.clearInterval(clock);
    };
  }, [load]);

  const decide = async (a: ApprovalResponse, decision: 'approve' | 'deny') => {
    setBusyId(a.approval_id);
    setFeedback(null);
    try {
      const res = await api.decideApproval(a.approval_id, decision);
      setFeedback({
        tone: decision === 'approve' ? 'allow' : 'deny',
        text: `${decision === 'approve' ? 'Approved' : 'Rejected'} ${a.tool_name} → ${a.destination || a.resource}. Status is now “${res.status}”.`,
      });
      load();
    } catch (e) {
      setFeedback({ tone: 'deny', text: errorText(e) });
      load();
    } finally {
      setBusyId(null);
    }
  };

  return (
    <section className="page">
      <PageHeader
        title="Approvals"
        subtitle="Each approval authorizes one exact action — this tool, these arguments, this recipient — once, before it expires. The same records appear in the mobile app."
        actions={<button className="btn btn-secondary" onClick={load}>Refresh</button>}
      />

      <div className="segmented" role="tablist" aria-label="Approval status">
        {FILTERS.map((f) => (
          <button key={f} role="tab" aria-selected={filter === f} className={filter === f ? 'active' : ''} onClick={() => setFilter(f)}>
            {f}
          </button>
        ))}
      </div>

      {feedback && <div className={`alert alert-${feedback.tone}`} role="status">{feedback.text}</div>}

      {loading ? (
        <LoadingState label="Loading approvals…" />
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : approvals.length === 0 ? (
        <EmptyState title={filter === 'pending' ? 'No pending approvals' : 'No approvals'}>
          In Attack Lab, run “Vendor email (needs human approval)” — the gateway creates a pending approval here.
        </EmptyState>
      ) : (
        <div className="approval-list">
          {approvals.map((a) => {
            const pending = a.status === 'pending';
            return (
              <article key={a.approval_id} className={`card approval-card ${pending ? 'tone-border-pending' : ''}`}>
                <div className="card-head">
                  <div>
                    <div className="eyebrow">Authorize exactly this action</div>
                    <h3 className="approval-title">
                      <span className="mono">{a.tool_name}</span>
                      {a.destination && <> → <span className="accent">{a.destination}</span></>}
                    </h3>
                  </div>
                  <Badge value={a.status} />
                </div>
                <dl className="kv">
                  <dt>Task</dt>
                  <dd>{tasks[a.task_id]?.description ?? a.task_id}</dd>
                  <dt>Agent</dt>
                  <dd className="mono">{a.agent_id ?? '—'}</dd>
                  <dt>Recipient</dt>
                  <dd>{a.destination || '—'}</dd>
                  <dt>Resource</dt>
                  <dd className="mono">{a.resource || '—'}</dd>
                  <dt>Arguments</dt>
                  <dd><pre className="args">{formatArgs(a.arguments)}</pre></dd>
                  <dt>Policy reason</dt>
                  <dd>{a.reason || '—'}</dd>
                  <dt>Expires</dt>
                  <dd>{formatDate(a.expires_at)}{pending && <span className="muted"> · {timeUntil(a.expires_at)}</span>}</dd>
                  <dt>Binding</dt>
                  <dd className="mono">args sha256 {a.arguments_hash.slice(0, 16)}… · {a.approval_id}</dd>
                </dl>
                {pending ? (
                  <div className="button-row">
                    <button className="btn btn-allow" disabled={busyId !== null} onClick={() => decide(a, 'approve')}>
                      {busyId === a.approval_id
                        ? 'Saving…'
                        : a.destination
                          ? `Approve email to ${a.destination}`
                          : `Approve ${a.tool_name} on ${a.resource || 'resource'}`}
                    </button>
                    <button className="btn btn-deny" disabled={busyId !== null} onClick={() => decide(a, 'deny')}>
                      Reject
                    </button>
                  </div>
                ) : (
                  <p className="muted">
                    Decided {formatDate(a.decided_at)}{a.consumed_at && ` · used once at ${formatDate(a.consumed_at)}`}
                  </p>
                )}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
