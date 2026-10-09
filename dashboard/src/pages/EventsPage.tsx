import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { ApiEvent } from '../types/api';
import { formatDate } from '../utils/time';

export function EventsPage() {
  const [events, setEvents] = useState<ApiEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState('');
  const [execFilter, setExecFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<ApiEvent | null>(null);
  const [offset, setOffset] = useState(0);

  const load = (newOffset = 0) => {
    setLoading(true);
    const params: Record<string, string> = { limit: '25', offset: String(newOffset) };
    if (filter) params.authorization = filter;
    if (execFilter) params.execution_status = execFilter;
    api.getEvents(params)
      .then((d) => { setEvents(d.events); setTotal(d.count); setOffset(newOffset); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [filter, execFilter]);

  if (loading && events.length === 0) return <div className="loading">Loading events…</div>;
  if (error) return <div className="error-state">Failed to load: {error}</div>;

  return (
    <section className="page">
      <div className="page-header">
        <h2>Event Explorer</h2>
        <span className="demo-badge">DEMO ENVIRONMENT</span>
      </div>

      <div className="filter-row">
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">All authorizations</option>
          <option value="allowed">Allowed</option>
          <option value="denied">Denied</option>
        </select>
        <select value={execFilter} onChange={(e) => setExecFilter(e.target.value)}>
          <option value="">All executions</option>
          <option value="succeeded">Succeeded</option>
          <option value="not_attempted">Not attempted</option>
          <option value="failed">Failed</option>
        </select>
        <span className="count-label">{total} events</span>
      </div>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Tool</th>
              <th>Authorization</th>
              <th>Execution</th>
              <th>Reason</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {events.map((ev) => (
              <tr key={ev.event_id} className={selected?.event_id === ev.event_id ? 'row-active' : ''}>
                <td className="mono">{formatDate(ev.timestamp)}</td>
                <td className="mono">{ev.tool_name ?? '-'}</td>
                <td><span className={`badge badge-${ev.authorization}`}>{ev.authorization}</span></td>
                <td><span className={`badge badge-${ev.execution_status === 'succeeded' ? 'allowed' : ev.execution_status === 'not_attempted' ? 'denied' : 'pending'}`}>{ev.execution_status}</span></td>
                <td className="reason-cell">{ev.authorization_reason}</td>
                <td><button className="btn btn-sm btn-secondary" onClick={() => setSelected(ev)}>Details</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="pagination">
        <button className="btn btn-sm btn-secondary" disabled={offset === 0} onClick={() => load(offset - 25)}>Prev</button>
        <button className="btn btn-sm btn-secondary" disabled={offset + 25 >= total} onClick={() => load(offset + 25)}>Next</button>
      </div>

      {selected && (
        <div className="detail-panel detail-modal">
          <h3>Event Detail</h3>
          <button className="btn btn-sm btn-secondary" onClick={() => setSelected(null)} style={{float:'right'}}>Close</button>
          <dl className="detail-grid">
            <dt>Event ID</dt><dd className="mono">{selected.event_id}</dd>
            <dt>Task ID</dt><dd className="mono">{selected.task_id ?? '-'}</dd>
            <dt>Tool</dt><dd>{selected.tool_name ?? '-'}</dd>
            <dt>Authorization</dt><dd><span className={`badge badge-${selected.authorization}`}>{selected.authorization}</span></dd>
            <dt>Reason</dt><dd>{selected.authorization_reason || '-'}</dd>
            <dt>Execution</dt><dd><span className={`badge badge-${selected.execution_status === 'succeeded' ? 'allowed' : 'denied'}`}>{selected.execution_status}</span></dd>
            <dt>Result</dt><dd className="mono">{selected.execution_result ?? '-'}</dd>
            <dt>Resource</dt><dd>{selected.resource || '-'}</dd>
            <dt>Destination</dt><dd>{selected.destination || '-'}</dd>
          </dl>
          <h4>Arguments</h4>
          <pre className="policy-display">{JSON.stringify(selected.arguments, null, 2)}</pre>
        </div>
      )}
    </section>
  );
}