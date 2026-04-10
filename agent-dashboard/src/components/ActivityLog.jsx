/**
 * ActivityLog - Live scrolling feed of agent activity.
 */

const TYPE_COLORS = {
  idle: '#64748b',
  working: '#3b82f6',
  collaborating: '#a855f7',
  waiting: '#f59e0b',
  complete: '#10b981',
};

const TYPE_ICONS = {
  idle: '💤',
  working: '⚡',
  collaborating: '🤝',
  waiting: '⏳',
  complete: '✅',
};

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export default function ActivityLog({ log }) {
  return (
    <div style={{
      height: '120px',
      background: '#0d1117',
      borderTop: '1px solid #1e3a5f',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
    }}>
      <div style={{
        padding: '6px 16px',
        borderBottom: '1px solid #1e3a5f',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <span style={{ fontSize: '9px', color: '#64748b', letterSpacing: '1.5px', textTransform: 'uppercase', fontWeight: 700 }}>
          Live Activity Feed
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <div style={{
            width: '6px', height: '6px', borderRadius: '50%',
            background: '#10b981', animation: 'breathe 2s ease-in-out infinite',
          }} />
          <span style={{ fontSize: '9px', color: '#64748b' }}>LIVE</span>
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '4px 12px' }}>
        {log.length === 0 && (
          <div style={{ padding: '8px', fontSize: '10px', color: '#475569', textAlign: 'center', fontStyle: 'italic' }}>
            Waiting for agent activity...
          </div>
        )}
        {log.map(entry => (
          <div key={entry.id} className="anim-slide" style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '3px 0',
            fontSize: '10px',
            fontFamily: 'monospace',
            borderBottom: '1px solid rgba(30, 58, 95, 0.2)',
          }}>
            <span style={{ color: '#475569', flexShrink: 0, width: '60px' }}>
              {formatTime(entry.timestamp)}
            </span>
            <span style={{ flexShrink: 0, fontSize: '11px' }}>
              {TYPE_ICONS[entry.type] || '•'}
            </span>
            <span style={{
              flexShrink: 0,
              color: entry.color,
              fontWeight: 700,
              width: '70px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}>
              {entry.agentName}
            </span>
            <span style={{
              color: TYPE_COLORS[entry.type] || '#94a3b8',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}>
              {entry.message}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
