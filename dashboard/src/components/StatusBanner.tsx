import { BACKEND_BASE_URL, BACKEND_CONFIGURED } from '../constants/config';
import { useHealth } from '../hooks/useHealth';

export function StatusBanner() {
  const { data, error } = useHealth();
  const state = !BACKEND_CONFIGURED ? 'unconfigured' : data ? 'online' : error ? 'offline' : 'checking';
  const label = {
    unconfigured: 'Backend not configured',
    online: 'Gateway online',
    offline: 'Backend offline',
    checking: 'Checking backend…',
  }[state];

  return (
    <div className={`topbar status-${state}`} role="status">
      <span className="status-dot" aria-hidden="true" />
      <strong>{label}</strong>
      <span className="topbar-url mono">{BACKEND_BASE_URL ?? 'set VITE_BACKEND_BASE_URL at build time'}</span>
      {state === 'offline' && (
        <span className="topbar-hint">Start it with <code>uvicorn app.main:app --host 0.0.0.0</code> in backend/</span>
      )}
      {state === 'unconfigured' && (
        <span className="topbar-hint">This static site hosts only the UI; the FastAPI backend runs separately.</span>
      )}
    </div>
  );
}
