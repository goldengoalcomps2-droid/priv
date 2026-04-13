import { useState } from 'react';
import { useAgentState } from './hooks/useAgentState';
import OfficeFloor from './components/OfficeFloor';
import StatusSidebar from './components/StatusSidebar';
import ActivityLog from './components/ActivityLog';
import AgentDetailPanel from './components/AgentDetailPanel';

export default function App() {
  const { agents, log, cycle, collaborations } = useAgentState(3500);
  const [selectedAgent, setSelectedAgent] = useState(null);

  const handleAgentClick = (agentId) => {
    const agent = agents.find(a => a.id === agentId);
    setSelectedAgent(agent || null);
  };

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      background: '#0a0e17',
      overflow: 'hidden',
    }}>
      {/* Main area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <OfficeFloor
          agents={agents}
          collaborations={collaborations}
          onAgentClick={handleAgentClick}
        />
        <ActivityLog log={log} />
      </div>

      {/* Right sidebar */}
      <StatusSidebar
        agents={agents}
        cycle={cycle}
        onAgentClick={handleAgentClick}
      />

      {/* Detail panel (slides in from right) */}
      {selectedAgent && (
        <AgentDetailPanel
          agent={selectedAgent}
          onClose={() => setSelectedAgent(null)}
        />
      )}
    </div>
  );
}
