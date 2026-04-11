import EcgLine from "./EcgLine";
import "./PatientCard.css";

const ESI_COLORS = {
  1: "#ff2052",
  2: "#ff6b35",
  3: "#ffb300",
  4: "#39ff14",
  5: "#00ffe0",
};

const ESI_LABELS = {
  1: "IMMEDIATE",
  2: "EMERGENT",
  3: "URGENT",
  4: "SEMI-URGENT",
  5: "NON-URGENT",
};

const DIFFICULTY_COLORS = {
  easy: "#39ff14",
  medium: "#ffb300",
  hard: "#ff2052",
};

export default function PatientCard({ task, obs, isActive, score, onClick }) {
  const esiLevel = obs?.partial_score >= 0.7 ? (task?.expected_triage_level || "?") : "?";
  const isCorrect = obs?.is_correct;
  const isDone = obs?.episode_done;
  const difficulty = task?.difficulty || "easy";
  const diffColor = DIFFICULTY_COLORS[difficulty] || "#00ffe0";
  const esiColor = ESI_COLORS[task?.expected_triage_level] || "#00ffe0";

  return (
    <div
      className={`patient-card ${isActive ? "active" : ""} ${isDone ? "done" : ""}`}
      onClick={onClick}
      style={{ "--esi-color": esiColor, "--diff-color": diffColor }}
    >
      {/* Corner decorations */}
      <div className="corner tl" />
      <div className="corner tr" />
      <div className="corner bl" />
      <div className="corner br" />

      {/* Header */}
      <div className="pc-header">
        <div className="pc-id">
          <span className="pc-badge">{task?.patient_id || "---"}</span>
          <span className="pc-difficulty" style={{ color: diffColor }}>
            ◆ {difficulty.toUpperCase()}
          </span>
        </div>
        <div className="pc-esi" style={{ background: `${esiColor}22`, borderColor: esiColor }}>
          <span className="esi-number" style={{ color: esiColor }}>
            ESI {task?.expected_triage_level || "?"}
          </span>
          <span className="esi-label" style={{ color: esiColor }}>
            {ESI_LABELS[task?.expected_triage_level] || "UNKNOWN"}
          </span>
        </div>
      </div>

      {/* Task name */}
      <div className="pc-task-name">{task?.name || "Loading..."}</div>

      {/* Chief complaint */}
      {obs && (
        <div className="pc-complaint">
          <span className="pc-label">CHIEF COMPLAINT</span>
          <span className="pc-value">{obs.chief_complaint || task?.patient?.chief_complaint || "—"}</span>
        </div>
      )}

      {/* Vitals */}
      {obs?.vitals && Object.keys(obs.vitals).length > 0 && (
        <div className="pc-vitals">
          {Object.entries(obs.vitals).map(([k, v]) => (
            <div className="vital-chip" key={k}>
              <span className="vital-key">{k}</span>
              <span className="vital-val">{v}</span>
            </div>
          ))}
        </div>
      )}

      {/* ECG */}
      <div className="pc-ecg">
        <EcgLine
          color={isActive ? "#00ffe0" : isDone ? (isCorrect ? "#39ff14" : "#ff2052") : "rgba(0,255,224,0.3)"}
          speed={isActive ? 2 : 0.8}
          width={160}
          height={40}
        />
      </div>

      {/* Score */}
      {score !== undefined && score !== null && (
        <div className="pc-score">
          <div className="pc-score-bar-wrap">
            <div
              className="pc-score-bar"
              style={{
                width: `${Math.round(score * 100)}%`,
                background: score >= 0.7 ? "#39ff14" : score >= 0.4 ? "#ffb300" : "#ff2052",
              }}
            />
          </div>
          <span className="pc-score-val">{(score * 100).toFixed(1)}%</span>
        </div>
      )}

      {/* Status */}
      <div className="pc-status">
        {isActive && <span className="status-dot blink">●</span>}
        {isActive && <span className="status-text">ACTIVE SESSION</span>}
        {isDone && isCorrect && <span className="status-text correct">✓ CORRECT TRIAGE</span>}
        {isDone && !isCorrect && <span className="status-text incorrect">✗ INCORRECT TRIAGE</span>}
        {!isActive && !isDone && <span className="status-text idle">AWAITING TRIAGE</span>}
      </div>
    </div>
  );
}
