import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { ApiEvent } from '../types/api';
import { formatDate } from '../utils/time';

export function AuditTrailPage() {
  const [events, setEvents] = useState<ApiEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getEvents({ limit: '100' })
      .then((d) => setEvents(d.events))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading audit trail…</div>;
  if (error) return <div className="error-state">Failed to load: {error}</div>;

  return (
    <section className="page">
      <div className="page-header">
        <h2>Audit Trail</h2>
        <span className="demo-badge">DEMO ENVIRONMENT</span>
      </div>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr><th>Timestamp</th><th>Event Type</th><th>Tool</th><th>Authorization</th><th>Execution</th><th>Reason</th></tr>
          </thead>
          <tbody>
            {events.map((ev) => (
              <tr key={ev.event_id}>
                <td className="mono">{formatDate(ev.timestamp)}</td>
                <td className="mono">{ev.event_type}</td>
                <td className="mono">{ev.tool_name ?? '-'}</td>
                <td><span className={`badge badge-${ev.authorization}`}>{ev.authorization}</span></td>
                <td><span className={`badge badge-${ev.execution_status === 'succeeded' ? 'allowed' : 'denied'}`}>{ev.execution_status}</span></td>
                <td className="reason-cell">{ev.authorization_reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}