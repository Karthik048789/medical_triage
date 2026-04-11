import "./ScoreGauge.css";

const ESI_COLORS = {
  1: "#ff2052",
  2: "#ff6b35",
  3: "#ffb300",
  4: "#39ff14",
  5: "#00ffe0",
};

export default function ScoreGauge({ score = 0, label = "SCORE" }) {
  const pct = Math.round(score * 100);
  const angle = -135 + (pct / 100) * 270;

  const getColor = () => {
    if (pct >= 80) return "#39ff14";
    if (pct >= 60) return "#ffb300";
    if (pct >= 40) return "#ff6b35";
    return "#ff2052";
  };

  const color = getColor();
  const r = 54;
  const circumference = 2 * Math.PI * r;
  const arcFraction = 0.75; // 270deg out of 360
  const dashArray = circumference * arcFraction;
  const dashOffset = dashArray * (1 - pct / 100);

  return (
    <div className="gauge-wrapper">
      <svg className="gauge-svg" viewBox="0 0 130 130" width="130" height="130">
        {/* Track arc */}
        <circle
          cx="65" cy="65" r={r}
          fill="none"
          stroke="rgba(0,255,224,0.08)"
          strokeWidth="8"
          strokeDasharray={`${dashArray} ${circumference}`}
          strokeDashoffset={0}
          strokeLinecap="round"
          transform="rotate(135 65 65)"
        />
        {/* Value arc */}
        <circle
          cx="65" cy="65" r={r}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeDasharray={`${dashArray} ${circumference}`}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          transform="rotate(135 65 65)"
          style={{
            filter: `drop-shadow(0 0 6px ${color}) drop-shadow(0 0 14px ${color})`,
            transition: "stroke-dashoffset 0.6s ease, stroke 0.3s ease",
          }}
        />
        {/* Needle */}
        <line
          x1="65" y1="65"
          x2={65 + 38 * Math.cos(((angle - 90) * Math.PI) / 180)}
          y2={65 + 38 * Math.sin(((angle - 90) * Math.PI) / 180)}
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 4px ${color})`, transition: "x2 0.5s, y2 0.5s" }}
        />
        <circle cx="65" cy="65" r="5" fill={color} style={{ filter: `drop-shadow(0 0 6px ${color})` }} />
      </svg>
      <div className="gauge-center">
        <span className="gauge-value" style={{ color }}>{pct}%</span>
        <span className="gauge-label">{label}</span>
      </div>
    </div>
  );
}
