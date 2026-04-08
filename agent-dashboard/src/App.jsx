import { useAgentState } from './hooks/useAgentState';
import OfficeFloor from './components/OfficeFloor';
import StatusSidebar from './components/StatusSidebar';
import ActivityLog from './components/ActivityLog';

export default function App() {
  const { agents, log, cycle, collaborations } = useAgentState(3500);

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      background: '#0a0e17',
      overflow: 'hidden',
    }}>
      {/* Main area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <OfficeFloor agents={agents} collaborations={collaborations} />
        <ActivityLog log={log} />
      </div>

      {/* Right sidebar */}
      <StatusSidebar agents={agents} cycle={cycle} />
    </div>
  );
}
