import { useMemo, useState } from 'react';

import { StatusBanner } from './components/StatusBanner';
import { useHealth } from './hooks/useHealth';
import { AttackLabPage } from './pages/AttackLabPage';
import { EventsPage } from './pages/EventsPage';
import { OverviewPage } from './pages/OverviewPage';
import { PoliciesPage } from './pages/PoliciesPage';
import { formatDate } from './utils/time';

type Tab = 'overview' | 'policies' | 'events' | 'attack-lab';

export function App() {
  const [tab, setTab] = useState<Tab>('overview');
  const { data } = useHealth();

  const content = useMemo(() => {
    switch (tab) {
      case 'policies':
        return <PoliciesPage />;
      case 'events':
        return <EventsPage />;
      case 'attack-lab':
        return <AttackLabPage />;
      default:
        return <OverviewPage />;
    }
  }, [tab]);

  return (
    <main className="container">
      <h1>VAJRA AI Dashboard</h1>
      <p className="tagline">Let AI work. Never let it overstep.</p>
      <StatusBanner />
      <p className="meta">Backend timestamp: {formatDate(data?.timestamp)}</p>

      <nav className="tabs">
        <button onClick={() => setTab('overview')}>Overview</button>
        <button onClick={() => setTab('policies')}>Policies</button>
        <button onClick={() => setTab('events')}>Events</button>
        <button onClick={() => setTab('attack-lab')}>Attack Lab</button>
      </nav>

      {content}
    </main>
  );
}
