/**
 * AgentDesk - A single agent's desk with avatar and state-driven animations.
 */
import { useState, useEffect } from 'react';

const STATE_CONFIG = {
  idle: { deskStroke: '#334155', deskFill: '#1a2332', avatarScale: 1 },
  working: { deskStroke: null, deskFill: '#1a2332', avatarScale: 1 },
  collaborating: { deskStroke: null, deskFill: '#1a2332', avatarScale: 1.05 },
  waiting: { deskStroke: '#475569', deskFill: '#1a2332', avatarScale: 1 },
  complete: { deskStroke: '#10b981', deskFill: '#1a2332', avatarScale: 1 },
};

export default function AgentDesk({ agent }) {
  const { deskX, deskY, color, colorBg, name, role, emoji, avatar, state, task } = agent;
  const cfg = STATE_CONFIG[state] || STATE_CONFIG.idle;
  const [showComplete, setShowComplete] = useState(false);

  useEffect(() => {
    if (state === 'complete') {
      setShowComplete(true);
      const t = setTimeout(() => setShowComplete(false), 1200);
      return () => clearTimeout(t);
    }
  }, [state, agent.completedCount]);

  const isWorking = state === 'working' || state === 'collaborating';
  const isIdle = state === 'idle';
  const isWaiting = state === 'waiting';
  const isComplete = state === 'complete';

  return (
    <g transform={`translate(${deskX}, ${deskY})`}>
      {/* Desk surface */}
      <rect x="-55" y="-25" width="110" height="80" rx="6"
        fill={cfg.deskFill}
        stroke={cfg.deskStroke || color}
        strokeWidth={isWorking ? 2 : 1}
        opacity={isIdle ? 0.6 : 0.9}
        style={isWorking ? { '--glow': colorBg } : {}}
        className={isWorking ? 'anim-work' : ''}
      />

      {/* Desk glow effect when working */}
      {isWorking && (
        <rect x="-55" y="-25" width="110" height="80" rx="6"
          fill="none" stroke={color} strokeWidth="1" opacity="0.3">
          <animate attributeName="opacity" values="0.1;0.4;0.1" dur="2s" repeatCount="indefinite" />
        </rect>
      )}

      {/* Monitor */}
      <rect x="-20" y="-18" width="40" height="24" rx="3"
        fill={isWorking ? '#0f172a' : '#0d1117'}
        stroke={isWorking ? color : '#334155'}
        strokeWidth="1" opacity={isIdle ? 0.5 : 0.9} />

      {/* Screen content when working */}
      {isWorking && (
        <g>
          <rect x="-16" y="-14" width="32" height="3" rx="1" fill={color} opacity="0.4">
            <animate attributeName="width" values="10;32;20;32" dur="2s" repeatCount="indefinite" />
          </rect>
          <rect x="-16" y="-9" width="24" height="2" rx="1" fill={color} opacity="0.2">
            <animate attributeName="width" values="24;12;24" dur="1.5s" repeatCount="indefinite" />
          </rect>
          <rect x="-16" y="-5" width="16" height="2" rx="1" fill={color} opacity="0.15" />
        </g>
      )}

      {/* Agent avatar circle */}
      <g transform={`translate(0, 30) scale(${cfg.avatarScale})`}
         className={isIdle ? 'anim-breathe' : showComplete ? 'anim-celebrate' : ''}>
        {/* Ripple effect when collaborating */}
        {state === 'collaborating' && (
          <>
            <circle cx="0" cy="0" r="16" fill="none" stroke={color} strokeWidth="1" className="anim-ripple" opacity="0.4" />
            <circle cx="0" cy="0" r="16" fill="none" stroke={color} strokeWidth="1" className="anim-ripple" opacity="0.3"
              style={{ animationDelay: '0.5s' }} />
          </>
        )}

        {/* Avatar background */}
        <circle cx="0" cy="0" r="16" fill={colorBg} stroke={color}
          strokeWidth={isWorking ? 2 : 1.5} opacity={isIdle ? 0.6 : 1} />

        {/* Avatar emoji */}
        <text x="0" y="5" textAnchor="middle" fontSize="14" className="select-none">
          {emoji}
        </text>
      </g>

      {/* Name plaque */}
      <g transform="translate(0, 58)">
        <rect x="-40" y="-6" width="80" height="14" rx="3"
          fill="#0f172a" stroke={color} strokeWidth="0.5" opacity="0.8" />
        <text x="0" y="4" textAnchor="middle" fill={color} fontSize="7"
          fontFamily="monospace" fontWeight="600" letterSpacing="0.5">
          {name.toUpperCase()}
        </text>
      </g>

      {/* Role label */}
      <text x="0" y="74" textAnchor="middle" fill="#64748b" fontSize="6" fontFamily="monospace">
        {role}
      </text>

      {/* State indicators */}
      {isIdle && (
        <text x="28" y="22" fill="#64748b" fontSize="10" className="anim-zzz" fontFamily="monospace">
          zZz
        </text>
      )}

      {isWaiting && (
        <g transform="translate(28, 18)">
          <text x="0" y="0" fontSize="12" className="anim-hourglass" style={{ transformOrigin: '0 -3px' }}>
            ⏳
          </text>
        </g>
      )}

      {(isComplete || showComplete) && (
        <g transform="translate(28, 18)">
          <circle cx="0" cy="0" r="8" fill="#10b981" opacity="0.3" />
          <text x="0" y="4" textAnchor="middle" fontSize="10" fill="#10b981">✓</text>
        </g>
      )}

      {/* Task label when working */}
      {isWorking && task && (
        <g transform="translate(0, -35)">
          <rect x="-60" y="-8" width="120" height="14" rx="4"
            fill="#0f172a" stroke={color} strokeWidth="0.5" opacity="0.9" />
          <text x="0" y="2" textAnchor="middle" fill={color} fontSize="6"
            fontFamily="monospace" opacity="0.9">
            {task.length > 28 ? task.slice(0, 28) + '...' : task}
          </text>
        </g>
      )}
    </g>
  );
}
