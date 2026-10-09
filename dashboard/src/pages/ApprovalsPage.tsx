import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { ApprovalResponse } from '../types/api';
import { formatDate } from '../utils/time';

export function ApprovalsPage() {
  const [approvals, setApprovals] = useState<ApprovalResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    api.getApprovals('pending')
      .then((d) => setApprovals(d.approvals))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const decide = (approvalId: string, decision: 'approve' | 'deny') => {
    setActionMsg(null);
    api.decideApproval(approvalId, decision)
      .then(() => {
        setActionMsg(`Successfully ${decision}d`);
        load();
      })
      .catch((e) => setActionMsg(`Failed: ${e.message}`));
  };

  if (loading) return <div className="loading">Loading approvals…</div>;
  if (error) return <div className="error-state">Failed to load: {error}</div>;

  return (
    <section className="page">
      <div className="page-header">
        <h2>Approvals</h2>
        <span className="demo-badge">DEMO ENVIRONMENT</span>
      </div>
      {actionMsg && <div className="save-feedback">{actionMsg}</div>}
      {approvals.length === 0 ? (
        <div className="empty-state">No pending approvals</div>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Tool</th>
                <th>Resource</th>
                <th>Destination</th>
                <th>Reason</th>
                <th>Expires</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {approvals.map((a) => (
                <tr key={a.approval_id}>
                  <td className="mono">{a.tool_name}</td>
                  <td className="mono">{a.resource || '-'}</td>
                  <td>{a.destination || '-'}</td>
                  <td>{a.reason || '-'}</td>
                  <td className="mono">{formatDate(a.expires_at)}</td>
                  <td>
                    <div className="button-row">
                      <button className="btn btn-sm btn-allow" onClick={() => decide(a.approval_id, 'approve')}>Approve</button>
                      <button className="btn btn-sm btn-deny" onClick={() => decide(a.approval_id, 'deny')}>Deny</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}