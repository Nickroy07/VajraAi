import { BACKEND_BASE_URL } from '../constants/config';
import { useHealth } from '../hooks/useHealth';

export function StatusBanner() {
  const { data, error } = useHealth();
  const online = Boolean(data && !error);

  return (
    <div className={`status ${online ? 'online' : 'offline'}`}>
      <strong>Backend:</strong> {online ? 'Connected' : 'Unavailable'}
      <span> ({BACKEND_BASE_URL})</span>
      <span className="note"> Gateway enforcement is not asserted by UI-only status.</span>
    </div>
  );
}
