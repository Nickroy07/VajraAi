import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { AgentResponse } from '../types/api';
import { formatDate } from '../utils/time';

export function AgentsPage() {
  const [agents, setAgents] = useState<AgentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getAgents()
      .then((d) => setAgents(d.agents))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading agents…</div>;
  if (error) return <div className="error-state">Failed to load: {error}</div>;

  return (
    <section className="page">
      <div className="page-header">
        <h2>Agents</h2>
        <span className="demo-badge">DEMO ENVIRONMENT</span>
      </div>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Status</th>
              <th>Registered</th>
            </tr>
          </thead>
          <tbody>
            {agents.map((a) => (
              <tr key={a.agent_id}>
                <td>{a.name}</td>
                <td className="mono">{a.agent_type}</td>
                <td>
                  <span className={`badge badge-${a.status === 'connected' ? 'allowed' : 'denied'}`}>
                    {a.status}
                  </span>
                </td>
                <td>{formatDate(a.registered_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}