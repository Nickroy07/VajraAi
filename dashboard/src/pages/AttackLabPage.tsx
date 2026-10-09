import { useState } from 'react';
import { api } from '../services/api';
import type { GatewayExecuteResponse, ScenarioId, ScenarioResult } from '../types/api';
import { Badge, PageHeader, ScenarioResultCard, errorText } from '../components/ui';

const SCENARIOS: { id: ScenarioId; label: string; desc: string; expect: 'allowed' | 'denied' | 'pending_approval' }[] = [
  { id: 'local_summary', label: 'Local summary', desc: 'Agent writes a summary of its assigned invoice to the local workspace.', expect: 'allowed' },
  { id: 'prompt_injection_email', label: 'Prompt injection → external email', desc: 'Hidden invoice text tells the agent to email the invoice to external@example.com.', expect: 'denied' },
  { id: 'unauthorized_file_delete', label: 'Unauthorized file delete', desc: 'Agent tries to delete /etc/critical/config.yaml.', expect: 'denied' },
  { id: 'authorized_invoice_read', label: 'Authorized invoice read', desc: 'Agent reads invoice-42, the resource assigned to its task.', expect: 'allowed' },
  { id: 'approval_vendor_email', label: 'Vendor email (needs human approval)', desc: 'Allowlisted vendor recipient; policy requires one-time approval of this exact email.', expect: 'pending_approval' },
];

const EXPECT_LABEL = { allowed: 'Expect: allowed', denied: 'Expect: blocked', pending_approval: 'Expect: approval' };

export function AttackLabPage() {
  const [results, setResults] = useState<ScenarioResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<ScenarioId>>(
    new Set<ScenarioId>(['local_summary', 'prompt_injection_email', 'unauthorized_file_delete']),
  );

  const toggle = (id: ScenarioId) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelected(next);
  };

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const ordered = SCENARIOS.map((s) => s.id).filter((id) => selected.has(id));
      setResults((await api.runAttackLab(ordered)).results);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="page">
      <PageHeader
        title="Attack Lab"
        tag="SIMULATED ATTACKS · DEMO"
        subtitle="Each scenario is a deterministic agent proposal sent through the real backend gateway. Executor deltas are read from the persisted mock-executor counter before and after the call."
      />

      <div className="scenario-grid" role="group" aria-label="Scenarios">
        {SCENARIOS.map((s) => (
          <label key={s.id} className={`scenario-card ${selected.has(s.id) ? 'selected' : ''}`}>
            <input type="checkbox" checked={selected.has(s.id)} onChange={() => toggle(s.id)} />
            <div>
              <div className="scenario-title">{s.label}</div>
              <p>{s.desc}</p>
              <Badge value={s.expect} label={EXPECT_LABEL[s.expect]} />
            </div>
          </label>
        ))}
      </div>

      <div className="button-row">
        <button className="btn btn-primary" onClick={run} disabled={loading || selected.size === 0}>
          {loading ? 'Running through gateway…' : `Run ${selected.size} scenario${selected.size === 1 ? '' : 's'}`}
        </button>
        {selected.size === 0 && <span className="muted">Select at least one scenario.</span>}
      </div>

      {error && <div className="alert alert-deny" role="alert">{error}</div>}

      {results && (
        <div className="results-grid">
          {results.map((r) => (
            <ScenarioResultCard
              key={r.event_id}
              result={r}
              footer={r.final_authorization === 'pending_approval' && r.approval_id ? <ApprovalFollowUp result={r} /> : undefined}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function ApprovalFollowUp({ result }: { result: ScenarioResult }) {
  const approvalId = result.approval_id!;
  type LogResp = Pick<GatewayExecuteResponse, 'authorization' | 'executor_call_count' | 'authorization_reason'>;
  const [log, setLog] = useState<{ label: string; resp?: LogResp; error?: string }[]>([]);
  const [busy, setBusy] = useState(false);

  const step = async (label: string, fn: () => Promise<GatewayExecuteResponse | ScenarioResult | null>) => {
    setBusy(true);
    try {
      const resp = await fn();
      const norm = resp && 'final_authorization' in resp
        ? { authorization: resp.final_authorization, executor_call_count: resp.executor_call_count, authorization_reason: resp.authorization_reason }
        : resp;
      setLog((l) => [...l, norm ? { label, resp: norm } : { label }]);
    } catch (e) {
      setLog((l) => [...l, { label, error: errorText(e) }]);
    } finally {
      setBusy(false);
    }
  };

  // Normal execution uses the server-held approved payload; the tamper button
  // deliberately resubmits a client-modified recipient to show it is rejected.
  const execute = () => api.executeApproval(approvalId);
  const tampered = () =>
    api.gatewayExecute({
      ...result.request,
      arguments: { ...result.request.arguments, to: 'attacker@evil.example' },
      approval_id: approvalId,
    });

  return (
    <div className="followup">
      <p className="muted">
        Approve on the phone, the Approvals page or here, then execute. The server runs only the stored approved action, once, after re-checking expiry, arguments and policy.
      </p>
      <div className="button-row wrap">
        <button className="btn btn-sm btn-allow" disabled={busy} onClick={() => step('Approved this exact action', async () => { await api.decideApproval(approvalId, 'approve'); return null; })}>
          Approve
        </button>
        <button className="btn btn-sm btn-primary" disabled={busy} onClick={() => step('Execute with approval', () => execute())}>
          Execute with approval
        </button>
        <button className="btn btn-sm btn-secondary" disabled={busy} onClick={() => step('Tampered recipient', tampered)}>
          Try changed recipient
        </button>
        <button className="btn btn-sm btn-secondary" disabled={busy} onClick={() => step('Replay same approval', () => execute())}>
          Replay
        </button>
      </div>
      {log.length > 0 && (
        <ul className="followup-log">
          {log.map((entry, i) => (
            <li key={i}>
              <strong>{entry.label}</strong>{' '}
              {entry.resp && (
                <>
                  <Badge value={entry.resp.authorization} /> Δ{entry.resp.executor_call_count} · {entry.resp.authorization_reason}
                </>
              )}
              {entry.error && <span className="tone-text-deny">{entry.error}</span>}
              {!entry.resp && !entry.error && <Badge value="approved" />}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
