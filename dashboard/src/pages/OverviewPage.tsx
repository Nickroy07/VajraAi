import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { OverviewResponse } from '../types/api';
import { formatDate } from '../utils/time';

export function OverviewPage() {
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getOverview()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading overview…</div>;
  if (error) return <div className="error-state">Failed to load: {error}</div>;
  if (!data) return <div className="empty-state">No data available</div>;

  return (
    <section className="page">
      <div className="page-header">
        <h2>Overview</h2>
        <span className="demo-badge">DEMO ENVIRONMENT</span>
      </div>

      <div className={`gateway-status ${data.gateway_connected ? 'connected' : 'disconnected'}`}>
        Gateway: {data.gateway_connected ? 'Connected' : 'Disconnected'} &middot; Mode: {data.mode}
      </div>

      <div className="metric-grid">
        {data.metrics.map((m) => (
          <div key={m.label} className="metric-card">
            <span className="metric-value">{m.value}</span>
            <span className="metric-label">{m.label}</span>
          </div>
        ))}
      </div>

      {data.attention_items.length > 0 && (
        <div className="attention-box">
          <h3>Attention</h3>
          {data.attention_items.map((item, i) => (
            <p key={i} className="attention-item">{item}</p>
          ))}
        </div>
      )}

      {data.recent_events.length > 0 && (
        <>
          <h3>Recent Events</h3>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Tool</th>
                  <th>Authorization</th>
                  <th>Execution</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_events.slice(0, 5).map((ev) => (
                  <tr key={ev.event_id}>
                    <td className="mono">{formatDate(ev.timestamp)}</td>
                    <td className="mono">{ev.tool_name ?? '-'}</td>
                    <td>
                      <span className={`badge badge-${ev.authorization}`}>
                        {ev.authorization}
                      </span>
                    </td>
                    <td>
                      <span className={`badge badge-${ev.execution_status === 'succeeded' ? 'allowed' : ev.execution_status === 'not_attempted' ? 'denied' : 'pending'}`}>
                        {ev.execution_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}