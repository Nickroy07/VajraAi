import { useEffect, useState } from 'react';

import { getHealth } from '../services/health';
import type { HealthResponse } from '../types/health';

const POLL_MS = 15000;

export function useHealth() {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const check = () =>
      getHealth()
        .then((h) => active && (setData(h), setError(null)))
        .catch((err: Error) => active && (setData(null), setError(err.message)));
    check();
    const id = window.setInterval(check, POLL_MS);
    return () => {
      active = false;
      window.clearInterval(id);
    };
  }, []);

  return { data, error };
}
