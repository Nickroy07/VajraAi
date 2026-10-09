import { useMemo, useState } from 'react';
import { AttackLabPage } from './pages/AttackLabPage';
import { OverviewPage } from './pages/OverviewPage';
import { TasksPage } from './pages/TasksPage';
import { AgentsPage } from './pages/AgentsPage';
import { PoliciesPage } from './pages/PoliciesPage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { EventsPage } from './pages/EventsPage';
import { AuditTrailPage } from './pages/AuditTrailPage';
import { SettingsPage } from './pages/SettingsPage';

type Tab =
  | 'overview'
  | 'tasks'
  | 'agents'
  | 'policies'
  | 'approvals'
  | 'events'
  | 'attack-lab'
  | 'audit-trail'
  | 'settings';

const NAV_ITEMS: { id: Tab; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'tasks', label: 'Tasks' },
  { id: 'agents', label: 'Agents' },
  { id: 'policies', label: 'Policies' },
  { id: 'approvals', label: 'Approvals' },
  { id: 'events', label: 'Event Explorer' },
  { id: 'attack-lab', label: 'Attack Lab' },
  { id: 'audit-trail', label: 'Audit Trail' },
  { id: 'settings', label: 'Settings' },
];

export function App() {
  const [tab, setTab] = useState<Tab>('overview');

  const content = useMemo(() => {
    switch (tab) {
      case 'tasks':
        return <TasksPage />;
      case 'agents':
        return <AgentsPage />;
      case 'policies':
        return <PoliciesPage />;
      case 'approvals':
        return <ApprovalsPage />;
      case 'events':
        return <EventsPage />;
      case 'attack-lab':
        return <AttackLabPage />;
      case 'audit-trail':
        return <AuditTrailPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <OverviewPage />;
    }
  }, [tab]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>VAJRA AI</h1>
          <div className="tagline">Let AI work. Never let it overstep.</div>
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={tab === item.id ? 'active' : ''}
              onClick={() => setTab(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="demo-badge">DEMO ENVIRONMENT</span>
        </div>
      </aside>
      <main className="main-content">{content}</main>
    </div>
  );
}