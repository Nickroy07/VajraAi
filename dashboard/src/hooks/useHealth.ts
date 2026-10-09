import { useEffect, useState } from 'react';

import { getHealth } from '../services/health';
import type { HealthResponse } from '../types/health';

export function useHealth() {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth().then(setData).catch((err: Error) => setError(err.message));
  }, []);

  return { data, error };
}
