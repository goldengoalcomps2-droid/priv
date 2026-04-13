/**
 * AgentDetailPanel - Expandable detail view when you click an agent.
 * Shows full work reports, recommendations, KPIs, and task history.
 */
import { AGENT_DETAILS } from '../data/agentDetails';

const STATUS_COLORS = {
  complete: '#10b981',
  active: '#3b82f6',
  pending: '#64748b',
  proposed: '#f59e0b',
};

export default function AgentDetailPanel({ agent, onClose }) {
  if (!agent) return null;

  const details = AGENT_DETAILS[agent.id] || {};

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      right: 0,
      width: '420px',
      height: '100vh',
      background: '#0d1117',
      borderLeft: '2px solid ' + agent.color,
      zIndex: 100,
      display: 'flex',
      flexDirection: 'column',
      animation: 'slideIn 0.3s ease-out',
      boxShadow: '-8px 0 30px rgba(0,0,0,0.5)',
    }}>
      <style>{`@keyframes slideIn { from { transform: translateX(420px); } to { transform: translateX(0); } }`}</style>

      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid #1e3a5f',
        background: `linear-gradient(135deg, ${agent.colorBg}, #0d1117)`,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
      }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{
            width: '44px', height: '44px', borderRadius: '10px',
            background: agent.colorBg, border: `2px solid ${agent.color}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '22px',
          }}>
            {agent.emoji}
          </div>
          <div>
            <div style={{ fontSize: '16px', fontWeight: 700, color: agent.color }}>{agent.name}</div>
            <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '1px' }}>{agent.role}</div>
          </div>
        </div>
        <button onClick={onClose} style={{
          background: 'none', border: '1px solid #334155', borderRadius: '6px',
          color: '#94a3b8', padding: '4px 10px', cursor: 'pointer', fontFamily: 'inherit',
          fontSize: '12px',
        }}>✕</button>
      </div>

      {/* Scrollable content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
        {/* Summary */}
        <div style={{
          fontSize: '12px', color: '#94a3b8', lineHeight: '1.6',
          marginBottom: '16px', padding: '10px', background: '#1a2332',
          borderRadius: '8px', borderLeft: `3px solid ${agent.color}`,
        }}>
          {details.summary}
        </div>

        {/* KPIs */}
        {details.kpis && (
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
            {details.kpis.map((kpi, i) => (
              <div key={i} style={{
                flex: 1, background: '#1a2332', borderRadius: '8px', padding: '10px',
                border: '1px solid #1e3a5f', textAlign: 'center',
              }}>
                <div style={{ fontSize: '16px', fontWeight: 700, color: agent.color }}>{kpi.value}</div>
                <div style={{ fontSize: '8px', color: '#64748b', textTransform: 'uppercase', marginTop: '2px', letterSpacing: '0.5px' }}>{kpi.name}</div>
              </div>
            ))}
          </div>
        )}

        {/* Current Focus */}
        {details.currentFocus && (
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '9px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: '6px', fontWeight: 700 }}>
              Current Focus
            </div>
            <div style={{
              fontSize: '11px', color: '#e2e8f0', padding: '8px 12px',
              background: `${agent.colorBg}`, borderRadius: '6px',
              border: `1px solid ${agent.color}30`,
            }}>
              {details.currentFocus}
            </div>
          </div>
        )}

        {/* Work Reports */}
        {details.recentWork && (
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '9px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: '8px', fontWeight: 700 }}>
              Work Reports
            </div>
            {details.recentWork.map((work, i) => (
              <WorkItem key={i} work={work} color={agent.color} />
            ))}
          </div>
        )}

        {/* Recommendations */}
        {details.recommendations && (
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '9px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: '8px', fontWeight: 700 }}>
              Recommendations
            </div>
            {details.recommendations.map((rec, i) => (
              <div key={i} style={{
                fontSize: '11px', color: '#94a3b8', padding: '8px 10px',
                marginBottom: '4px', background: '#1a2332', borderRadius: '6px',
                display: 'flex', gap: '8px', alignItems: 'flex-start',
                lineHeight: '1.5',
              }}>
                <span style={{ color: agent.color, flexShrink: 0, marginTop: '1px' }}>→</span>
                <span>{rec}</span>
              </div>
            ))}
          </div>
        )}

        {/* Live State */}
        <div style={{ marginBottom: '16px' }}>
          <div style={{ fontSize: '9px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: '8px', fontWeight: 700 }}>
            Live State
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8', background: '#1a2332', borderRadius: '6px', padding: '10px' }}>
            <div>Status: <span style={{ color: agent.state === 'working' ? '#3b82f6' : agent.state === 'idle' ? '#64748b' : '#f59e0b', fontWeight: 700 }}>{agent.state?.toUpperCase()}</span></div>
            {agent.task && <div style={{ marginTop: '4px' }}>Task: <span style={{ color: '#e2e8f0' }}>{agent.task}</span></div>}
            <div style={{ marginTop: '4px' }}>Actions logged: <span style={{ color: '#e2e8f0' }}>{agent.completedCount || 0}</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}


function WorkItem({ work, color }) {
  const statusColor = STATUS_COLORS[work.status] || '#64748b';

  return (
    <div style={{
      background: '#1a2332',
      border: '1px solid #1e3a5f',
      borderRadius: '8px',
      padding: '10px 12px',
      marginBottom: '6px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
        <div style={{ fontSize: '12px', fontWeight: 600, color: '#e2e8f0' }}>{work.title}</div>
        <span style={{
          fontSize: '8px', fontWeight: 700, padding: '2px 8px', borderRadius: '10px',
          background: `${statusColor}20`, color: statusColor, letterSpacing: '0.5px',
          textTransform: 'uppercase',
        }}>
          {work.status}
        </span>
      </div>
      <div style={{ fontSize: '10px', color: '#94a3b8', lineHeight: '1.6' }}>
        {work.detail}
      </div>
    </div>
  );
}
