import { useEffect, useState } from 'react';
import { AttackLabPage } from './pages/AttackLabPage';
import { OverviewPage } from './pages/OverviewPage';
import { TasksPage } from './pages/TasksPage';
import { AgentsPage } from './pages/AgentsPage';
import { PoliciesPage } from './pages/PoliciesPage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { EventsPage } from './pages/EventsPage';
import { AuditTrailPage } from './pages/AuditTrailPage';
import { SettingsPage } from './pages/SettingsPage';
import { DocumentGuardPage } from './pages/DocumentGuardPage';
import { StatusBanner } from './components/StatusBanner';

export type Tab =
  | 'overview'
  | 'document-guard'
  | 'attack-lab'
  | 'approvals'
  | 'events'
  | 'audit-trail'
  | 'tasks'
  | 'policies'
  | 'agents'
  | 'settings';

const NAV_GROUPS: { title: string; items: { id: Tab; label: string }[] }[] = [
  {
    title: 'Protect',
    items: [
      { id: 'overview', label: 'Overview' },
      { id: 'document-guard', label: 'Document Guard' },
      { id: 'attack-lab', label: 'Attack Lab' },
      { id: 'approvals', label: 'Approvals' },
    ],
  },
  {
    title: 'Inspect',
    items: [
      { id: 'events', label: 'Event Explorer' },
      { id: 'audit-trail', label: 'Audit Trail' },
    ],
  },
  {
    title: 'Configure',
    items: [
      { id: 'tasks', label: 'Tasks' },
      { id: 'policies', label: 'Policies' },
      { id: 'agents', label: 'Agents' },
      { id: 'settings', label: 'Settings' },
    ],
  },
];

const ALL_TABS = NAV_GROUPS.flatMap((g) => g.items.map((i) => i.id));

function tabFromHash(): Tab {
  const id = window.location.hash.replace(/^#\/?/, '') as Tab;
  return ALL_TABS.includes(id) ? id : 'overview';
}

export function navigate(tab: Tab) {
  window.location.hash = `/${tab}`;
}

function renderPage(tab: Tab) {
  switch (tab) {
    case 'document-guard':
      return <DocumentGuardPage />;
    case 'attack-lab':
      return <AttackLabPage />;
    case 'approvals':
      return <ApprovalsPage />;
    case 'events':
      return <EventsPage />;
    case 'audit-trail':
      return <AuditTrailPage />;
    case 'tasks':
      return <TasksPage />;
    case 'policies':
      return <PoliciesPage />;
    case 'agents':
      return <AgentsPage />;
    case 'settings':
      return <SettingsPage />;
    default:
      return <OverviewPage onNavigate={navigate} />;
  }
}

export function App() {
  const [tab, setTab] = useState<Tab>(tabFromHash);

  useEffect(() => {
    const onHash = () => setTab(tabFromHash());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark" aria-hidden="true">V</div>
          <div>
            <h1>VAJRA AI</h1>
            <div className="tagline">Let AI work. Never let it overstep.</div>
          </div>
        </div>
        <nav className="sidebar-nav" aria-label="Main">
          {NAV_GROUPS.map((group) => (
            <div key={group.title} className="nav-group">
              <div className="nav-group-title">{group.title}</div>
              {group.items.map((item) => (
                <a
                  key={item.id}
                  href={`#/${item.id}`}
                  className={tab === item.id ? 'active' : ''}
                  aria-current={tab === item.id ? 'page' : undefined}
                >
                  {item.label}
                </a>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="demo-badge">DEMO ENVIRONMENT</span>
          <p>Mock tools only. No real email, files or third-party AI apps are touched.</p>
        </div>
      </aside>
      <div className="main-column">
        <StatusBanner />
        <main className="main-content">{renderPage(tab)}</main>
      </div>
    </div>
  );
}
