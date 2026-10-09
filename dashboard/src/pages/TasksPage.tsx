import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { TaskResponse } from '../types/api';
import { formatDate } from '../utils/time';

export function TasksPage() {
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [selected, setSelected] = useState<TaskResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getTasks()
      .then((d) => { setTasks(d.tasks); if (d.tasks.length > 0) setSelected(d.tasks[0]); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const selectTask = (id: string) => {
    api.getTask(id).then(setSelected).catch(() => {});
  };

  if (loading) return <div className="loading">Loading tasks…</div>;
  if (error) return <div className="error-state">Failed to load: {error}</div>;

  return (
    <section className="page">
      <div className="page-header">
        <h2>Tasks</h2>
        <span className="demo-badge">DEMO ENVIRONMENT</span>
      </div>
      <div className="split-layout">
        <div className="list-panel">
          {tasks.map((t) => (
            <div
              key={t.task_id}
              className={`list-item ${selected?.task_id === t.task_id ? 'active' : ''}`}
              onClick={() => selectTask(t.task_id)}
            >
              <div className="list-item-title">{t.description}</div>
              <div className="list-item-sub mono">{t.task_id.slice(0, 8)}… &middot; <span className={`badge badge-${t.status === 'running' ? 'allowed' : t.status === 'blocked' ? 'denied' : 'pending'}`}>{t.status}</span></div>
            </div>
          ))}
        </div>
        <div className="detail-panel">
          {selected ? (
            <>
              <h3>{selected.description}</h3>
              <dl className="detail-grid">
                <dt>Task ID</dt><dd className="mono">{selected.task_id}</dd>
                <dt>Status</dt><dd><span className={`badge badge-${selected.status === 'running' ? 'allowed' : 'pending'}`}>{selected.status}</span></dd>
                <dt>Created</dt><dd>{formatDate(selected.created_at)}</dd>
                <dt>Updated</dt><dd>{formatDate(selected.updated_at)}</dd>
              </dl>
              <h4>Scope</h4>
              <div className="scope-box">
                <div>
                  <strong>Allowed Tools:</strong>
                  <ul className="tag-list">
                    {selected.scope.allowed_tools.map((t) => <li key={t} className="tag">{t}</li>)}
                  </ul>
                </div>
                <div>
                  <strong>Resources:</strong>
                  <ul className="tag-list">
                    {selected.scope.resources.map((r) => <li key={r} className="tag">{r}</li>)}
                  </ul>
                </div>
                {selected.scope.block_external_destinations && (
                  <div><span className="badge badge-denied">External destinations blocked</span></div>
                )}
              </div>
            </>
          ) : (
            <div className="empty-state">Select a task to view details</div>
          )}
        </div>
      </div>
    </section>
  );
}