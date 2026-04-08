/**
 * CollaborationLines - Animated beams connecting collaborating agents.
 */
export default function CollaborationLines({ collaborations, agents }) {
  return (
    <g className="collab-lines">
      {collaborations.map(([id1, id2], i) => {
        const a1 = agents.find(a => a.id === id1);
        const a2 = agents.find(a => a.id === id2);
        if (!a1 || !a2) return null;

        const x1 = a1.deskX;
        const y1 = a1.deskY + 30;
        const x2 = a2.deskX;
        const y2 = a2.deskY + 30;

        // Midpoint for curve
        const mx = (x1 + x2) / 2;
        const my = (y1 + y2) / 2 - 30;

        const gradient = `collab-grad-${i}`;

        return (
          <g key={`${id1}-${id2}`}>
            <defs>
              <linearGradient id={gradient} x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor={a1.color} stopOpacity="0.8" />
                <stop offset="50%" stopColor="#ffffff" stopOpacity="0.4" />
                <stop offset="100%" stopColor={a2.color} stopOpacity="0.8" />
              </linearGradient>
            </defs>

            {/* Glow behind the line */}
            <path
              d={`M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`}
              fill="none"
              stroke={`url(#${gradient})`}
              strokeWidth="4"
              opacity="0.15"
            />

            {/* Main beam */}
            <path
              d={`M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`}
              fill="none"
              stroke={`url(#${gradient})`}
              strokeWidth="2"
              strokeDasharray="8 4"
              className="anim-dash"
              opacity="0.7"
            />

            {/* Energy dots along the path */}
            <circle r="3" fill="white" opacity="0.6">
              <animateMotion
                dur="2s"
                repeatCount="indefinite"
                path={`M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`}
              />
            </circle>
            <circle r="2" fill="white" opacity="0.4">
              <animateMotion
                dur="2s"
                repeatCount="indefinite"
                begin="1s"
                path={`M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`}
              />
            </circle>

            {/* Collab label */}
            <g transform={`translate(${mx}, ${my - 10})`}>
              <rect x="-22" y="-6" width="44" height="12" rx="6"
                fill="#0f172a" stroke="#475569" strokeWidth="0.5" opacity="0.9" />
              <text x="0" y="3" textAnchor="middle" fill="#94a3b8" fontSize="6" fontFamily="monospace">
                COLLAB
              </text>
            </g>
          </g>
        );
      })}
    </g>
  );
}
