import { BACKEND_BASE_URL } from '../constants/config';

export function SettingsPage() {
  return (
    <section className="page">
      <div className="page-header">
        <h2>Settings</h2>
        <span className="demo-badge">DEMO ENVIRONMENT</span>
      </div>
      <div className="settings-card">
        <h3>Connection</h3>
        <dl className="detail-grid">
          <dt>API Base URL</dt>
          <dd className="mono">{BACKEND_BASE_URL}</dd>
          <dt>Mode</dt>
          <dd>Demo — simulated protections only</dd>
          <dt>Gateway</dt>
          <dd>Local SQLite, single-instance</dd>
        </dl>
        <h3>About</h3>
        <p>VAJRA AI Gateway v0.2.0 — Execution-time security gateway for supported AI-agent integrations.</p>
        <p className="note">
          This is a <strong>proof-of-concept demo</strong>. Not a production-grade multi-tenant authorization system.
          No real email, file operations, or external side effects occur. Mock tools simulate behavior deterministically.
        </p>
        <h3>Not Implemented</h3>
        <ul>
          <li>Multi-tenant auth / OAuth / SSO</li>
          <li>Production cryptographic key management</li>
          <li>Distributed/high-availability deployment</li>
          <li>Real AI agent SDK integrations</li>
          <li>Immutable audit log / blockchain anchoring</li>
        </ul>
      </div>
    </section>
  );
}