/**
 * StatusSidebar - Shows all agents, their state, current task, and elapsed time.
 */
import { useState, useEffect } from 'react';

const STATE_LABELS = {
  idle: { text: 'IDLE', color: '#64748b', bg: 'rgba(100, 116, 139, 0.15)' },
  working: { text: 'WORKING', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)' },
  collaborating: { text: 'COLLAB', color: '#a855f7', bg: 'rgba(168, 85, 247, 0.15)' },
  waiting: { text: 'WAITING', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)' },
  complete: { text: 'DONE', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' },
};

function ElapsedTime({ since }) {
  const [elapsed, setElapsed] = useState('0s');

  useEffect(() => {
    if (!since) { setElapsed('--'); return; }
    const tick = () => {
      const s = Math.floor((Date.now() - since) / 1000);
      if (s < 60) setElapsed(`${s}s`);
      else setElapsed(`${Math.floor(s / 60)}m ${s % 60}s`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [since]);

  return <span style={{ color: '#64748b', fontSize: '10px', fontFamily: 'monospace' }}>{elapsed}</span>;
}

export default function StatusSidebar({ agents, cycle, onAgentClick }) {
  const working = agents.filter(a => a.state === 'working' || a.state === 'collaborating').length;
  const completed = agents.reduce((s, a) => s + a.completedCount, 0);

  return (
    <div style={{
      width: '260px',
      background: '#111827',
      borderLeft: '1px solid #1e3a5f',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding: '14px 16px',
        borderBottom: '1px solid #1e3a5f',
        background: 'linear-gradient(135deg, #0f172a, #1e293b)',
      }}>
        <div style={{ fontSize: '11px', fontWeight: 700, color: '#06b6d4', letterSpacing: '1.5px', textTransform: 'uppercase' }}>
          Agent Status
        </div>
        <div style={{ display: 'flex', gap: '16px', marginTop: '8px', fontSize: '10px' }}>
          <div>
            <span style={{ color: '#64748b' }}>Active </span>
            <span style={{ color: '#3b82f6', fontWeight: 700 }}>{working}</span>
          </div>
          <div>
            <span style={{ color: '#64748b' }}>Completed </span>
            <span style={{ color: '#10b981', fontWeight: 700 }}>{completed}</span>
          </div>
          <div>
            <span style={{ color: '#64748b' }}>Cycle </span>
            <span style={{ color: '#f59e0b', fontWeight: 700 }}>{cycle}</span>
          </div>
        </div>
      </div>

      {/* Agent list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
        {agents.map(agent => {
          const sl = STATE_LABELS[agent.state] || STATE_LABELS.idle;
          return (
            <div key={agent.id} className="anim-slide" onClick={() => onAgentClick && onAgentClick(agent.id)} style={{
              background: '#1a2332',
              border: `1px solid ${agent.state === 'idle' ? '#1e3a5f' : agent.color + '40'}`,
              borderRadius: '8px',
              padding: '10px 12px',
              marginBottom: '6px',
              transition: 'all 0.3s ease',
              cursor: 'pointer',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{
                    width: '28px', height: '28px', borderRadius: '6px',
                    background: agent.colorBg, border: `1px solid ${agent.color}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '14px',
                  }}>
                    {agent.emoji}
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: 700, color: agent.color }}>{agent.name}</div>
                    <div style={{ fontSize: '9px', color: '#64748b' }}>{agent.role}</div>
                  </div>
                </div>
                <div style={{
                  padding: '2px 8px', borderRadius: '10px',
                  background: sl.bg, color: sl.color,
                  fontSize: '8px', fontWeight: 700, letterSpacing: '0.5px',
                }}>
                  {sl.text}
                </div>
              </div>

              {agent.task && (
                <div style={{
                  marginTop: '6px', padding: '4px 8px',
                  background: '#0f172a', borderRadius: '4px',
                  fontSize: '9px', color: '#94a3b8', fontFamily: 'monospace',
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}>
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '160px' }}>
                    {agent.task}
                  </span>
                  <ElapsedTime since={agent.taskStartedAt} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
