/**
 * OfficeFloor - The main SVG office environment with all agents.
 */
import OfficeFurniture from './OfficeFurniture';
import AgentDesk from './AgentDesk';
import CollaborationLines from './CollaborationLines';

export default function OfficeFloor({ agents, collaborations }) {
  return (
    <div style={{
      flex: 1,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      overflow: 'hidden',
    }}
    className="office-grid"
    >
      {/* Title overlay */}
      <div style={{
        position: 'absolute',
        top: '12px',
        left: '16px',
        zIndex: 10,
      }}>
        <div style={{
          fontSize: '14px',
          fontWeight: 700,
          color: '#06b6d4',
          letterSpacing: '2px',
          textTransform: 'uppercase',
        }}>
          Mission Control
        </div>
        <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>
          £10K Monthly Income Engine
        </div>
      </div>

      {/* Status indicator */}
      <div style={{
        position: 'absolute',
        top: '12px',
        right: '16px',
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        zIndex: 10,
      }}>
        <div style={{
          width: '8px', height: '8px', borderRadius: '50%',
          background: '#10b981',
          boxShadow: '0 0 8px rgba(16, 185, 129, 0.5)',
          animation: 'breathe 2s ease-in-out infinite',
        }} />
        <span style={{ fontSize: '10px', color: '#10b981', fontWeight: 600, letterSpacing: '1px' }}>
          SYSTEMS ONLINE
        </span>
      </div>

      <svg
        viewBox="0 0 800 450"
        style={{
          width: '100%',
          maxWidth: '900px',
          height: 'auto',
          maxHeight: '100%',
        }}
      >
        <OfficeFurniture />
        <CollaborationLines collaborations={collaborations} agents={agents} />
        {agents.map(agent => (
          <AgentDesk key={agent.id} agent={agent} />
        ))}
      </svg>
    </div>
  );
}
