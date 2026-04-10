/**
 * Static office environment: walls, floor tiles, plants, whiteboard, water cooler.
 */
export default function OfficeFurniture() {
  return (
    <g className="furniture">
      {/* Room walls */}
      <rect x="20" y="20" width="760" height="400" rx="12"
        fill="none" stroke="#1e3a5f" strokeWidth="2" strokeDasharray="8 4" opacity="0.4" />

      {/* Floor texture lines */}
      {[0,1,2,3,4,5,6,7,8,9].map(i => (
        <line key={`h${i}`} x1="20" y1={60 + i * 40} x2="780" y2={60 + i * 40}
          stroke="#1e3a5f" strokeWidth="0.5" opacity="0.15" />
      ))}
      {[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19].map(i => (
        <line key={`v${i}`} x1={60 + i * 40} y1="20" x2={60 + i * 40} y2="420"
          stroke="#1e3a5f" strokeWidth="0.5" opacity="0.15" />
      ))}

      {/* Plants */}
      <g transform="translate(40, 200)">
        <circle cx="0" cy="0" r="8" fill="#064e3b" opacity="0.6" />
        <circle cx="-3" cy="-4" r="5" fill="#065f46" opacity="0.7" />
        <circle cx="3" cy="-3" r="4" fill="#047857" opacity="0.8" />
        <rect x="-3" y="4" width="6" height="8" rx="1" fill="#78350f" opacity="0.5" />
      </g>
      <g transform="translate(760, 200)">
        <circle cx="0" cy="0" r="8" fill="#064e3b" opacity="0.6" />
        <circle cx="-3" cy="-4" r="5" fill="#065f46" opacity="0.7" />
        <circle cx="3" cy="-3" r="4" fill="#047857" opacity="0.8" />
        <rect x="-3" y="4" width="6" height="8" rx="1" fill="#78350f" opacity="0.5" />
      </g>
      <g transform="translate(400, 430)">
        <circle cx="0" cy="-4" r="6" fill="#064e3b" opacity="0.5" />
        <circle cx="-4" cy="-2" r="4" fill="#065f46" opacity="0.6" />
        <circle cx="4" cy="-2" r="4" fill="#047857" opacity="0.7" />
        <rect x="-2" y="2" width="4" height="6" rx="1" fill="#78350f" opacity="0.4" />
      </g>

      {/* Whiteboard */}
      <g transform="translate(340, 30)">
        <rect x="0" y="0" width="120" height="50" rx="4"
          fill="#1a2332" stroke="#334155" strokeWidth="1.5" />
        <text x="60" y="18" textAnchor="middle" fill="#475569" fontSize="8" fontFamily="monospace">
          MISSION BOARD
        </text>
        <line x1="15" y1="26" x2="105" y2="26" stroke="#334155" strokeWidth="0.5" />
        <line x1="15" y1="33" x2="80" y2="33" stroke="#334155" strokeWidth="0.5" />
        <line x1="15" y1="40" x2="95" y2="40" stroke="#334155" strokeWidth="0.5" />
      </g>

      {/* Water cooler */}
      <g transform="translate(760, 380)">
        <rect x="-6" y="-12" width="12" height="20" rx="2" fill="#1e3a5f" opacity="0.6" />
        <rect x="-4" y="-14" width="8" height="6" rx="2" fill="#0ea5e9" opacity="0.3" />
        <text x="0" y="18" textAnchor="middle" fill="#475569" fontSize="6" fontFamily="monospace">H2O</text>
      </g>

      {/* Divider lines between desk rows */}
      <line x1="60" y1="210" x2="740" y2="210" stroke="#1e3a5f" strokeWidth="1" opacity="0.2" strokeDasharray="4 6" />
    </g>
  );
}
