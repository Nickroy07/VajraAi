import { useState } from 'react';
import { api } from '../services/api';
import type { ScenarioId, ScenarioResult, TraceStage } from '../types/api';

const SCENARIOS: { id: ScenarioId; label: string; desc: string }[] = [
  { id: 'authorized_invoice_read', label: 'Authorized Invoice Read', desc: 'Policy allows reading seeded invoice; executor called.' },
  { id: 'prompt_injection_email', label: 'Prompt Injection → External Email', desc: 'Hostile text + send_external_email → policy denies.' },
  { id: 'unauthorized_file_delete', label: 'Unauthorized File Delete', desc: 'Delete against protected file → default deny.' },
];

const STATUS_COLORS: Record<string, string> = {
  allowed: 'var(--color-allow)',
  denied: 'var(--color-deny)',
  succeeded: 'var(--color-allow)',
  skipped: 'var(--color-amber)',
  failed: 'var(--color-deny)',
  error: 'var(--color-deny)',
  info: 'var(--color-muted)',
};

export function AttackLabPage() {
  const [results, setResults] = useState<ScenarioResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<ScenarioId>>(
    new Set(SCENARIOS.map((s) => s.id))
  );

  const toggle = (id: ScenarioId) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id); else next.add(id);
    setSelectedIds(next);
  };

  const run = async () => {
    if (selectedIds.size === 0) return;
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const data = await api.runAttackLab([...selectedIds] as ScenarioId[]);
      setResults(data.results);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="page">
      <div className="page-header">
        <h2>Attack Lab</h2>
        <span className="demo-badge">SIMULATED ATTACK — DEMO ONLY</span>
      </div>

      <p className="note">Each scenario exercises the real gateway enforcement. No real side effects occur.</p>

      <div className="scenario-select">
        {SCENARIOS.map((s) => (
          <label key={s.id} className="scenario-check">
            <input type="checkbox" checked={selectedIds.has(s.id)} onChange={() => toggle(s.id)} />
            <div>
              <strong>{s.label}</strong>
              <p>{s.desc}</p>
            </div>
          </label>
        ))}
      </div>

      <button className="btn btn-primary" onClick={run} disabled={loading || selectedIds.size === 0}>
        {loading ? 'Running…' : 'Run Selected Scenarios'}
      </button>

      {error && <div className="error-state">Error: {error}</div>}

      {results && (
        <div className="results-section">
          {results.map((r) => (
            <div key={r.scenario_id} className={`result-card result-${r.final_authorization}`}>
              <h3>
                {r.scenario_label}
                <span className={`badge badge-${r.final_authorization === 'allowed' ? 'allowed' : 'denied'}`}>
                  {r.final_authorization}
                </span>
              </h3>
              <div className="result-meta">
                <div><strong>Reason:</strong> {r.authorization_reason}</div>
                <div><strong>Execution:</strong> {r.execution_status} | <strong>Executor calls:</strong> {r.executor_call_count}</div>
                <div className="mono"><strong>Event:</strong> {r.event_id}</div>
              </div>

              <div className="trace-pipeline">
                {r.trace.map((stage: TraceStage, i: number) => (
                  <div key={i} className="trace-stage">
                    <span className="trace-arrow">{i > 0 ? '→' : ''}</span>
                    <span className="trace-badge" style={{ background: STATUS_COLORS[stage.status] ?? STATUS_COLORS.info }}>
                      {stage.stage}
                    </span>
                    {stage.detail && <span className="trace-detail">{stage.detail}</span>}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}