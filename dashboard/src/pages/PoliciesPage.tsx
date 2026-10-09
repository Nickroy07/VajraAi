import { useCallback, useEffect, useState } from 'react';
import { api } from '../services/api';
import type { PolicyResponse, PolicyRule, TaskResponse } from '../types/api';

export function PoliciesPage() {
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [policy, setPolicy] = useState<PolicyResponse | null>(null);
  const [editing, setEditing] = useState(false);
  const [draftRules, setDraftRules] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  useEffect(() => {
    api.getTasks()
      .then((d) => { setTasks(d.tasks); if (d.tasks.length > 0) setSelectedTaskId(d.tasks[0].task_id); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedTaskId) return;
    setEditing(false);
    setSaveMsg(null);
    api.getPolicy(selectedTaskId)
      .then((p) => {
        setPolicy(p);
        setDraftRules(JSON.stringify(p.rules, null, 2));
      })
      .catch(() => setPolicy(null));
  }, [selectedTaskId]);

  const handleSave = useCallback(() => {
    if (!selectedTaskId) return;
    try {
      const rules: PolicyRule[] = JSON.parse(draftRules);
      api.updatePolicy(selectedTaskId, { rules })
        .then((p) => {
          setPolicy(p);
          setEditing(false);
          setSaveMsg('Policy saved successfully.');
          setTimeout(() => setSaveMsg(null), 3000);
        })
        .catch((e) => setSaveMsg(`Save failed: ${e.message}`));
    } catch {
      setSaveMsg('Invalid JSON — please fix syntax');
    }
  }, [selectedTaskId, draftRules]);

  if (loading) return <div className="loading">Loading policies…</div>;
  if (error) return <div className="error-state">Failed to load: {error}</div>;

  const selectedTask = tasks.find((t) => t.task_id === selectedTaskId);

  return (
    <section className="page">
      <div className="page-header">
        <h2>Policies</h2>
        <span className="demo-badge">DEMO ENVIRONMENT</span>
      </div>
      <div className="split-layout">
        <div className="list-panel">
          {tasks.map((t) => (
            <div
              key={t.task_id}
              className={`list-item ${selectedTaskId === t.task_id ? 'active' : ''}`}
              onClick={() => setSelectedTaskId(t.task_id)}
            >
              <div className="list-item-title">{t.description}</div>
              <div className="list-item-sub mono">{t.task_id.slice(0, 12)}…</div>
            </div>
          ))}
        </div>
        <div className="detail-panel">
          {policy ? (
            <>
              <h3>Policy for: {selectedTask?.description ?? selectedTaskId}</h3>
              {saveMsg && <div className="save-feedback">{saveMsg}</div>}
              {editing ? (
                <>
                  <textarea
                    className="policy-editor"
                    rows={12}
                    value={draftRules}
                    onChange={(e) => setDraftRules(e.target.value)}
                  />
                  <div className="button-row">
                    <button className="btn btn-primary" onClick={handleSave}>Save</button>
                    <button className="btn btn-secondary" onClick={() => setEditing(false)}>Cancel</button>
                  </div>
                </>
              ) : (
                <>
                  <pre className="policy-display">{JSON.stringify(policy.rules, null, 2)}</pre>
                  <button className="btn btn-primary" onClick={() => setEditing(true)}>Edit Policy</button>
                </>
              )}
            </>
          ) : (
            <div className="empty-state">No policy found for this task. Use PUT to create one.</div>
          )}
        </div>
      </div>
    </section>
  );
}