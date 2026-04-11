import { useState, useEffect, useRef, useCallback } from "react";
import { getHealth, getTasks, getState, resetEnv, stepEnv } from "./api";
import PatientCard from "./components/PatientCard";
import TriagePanel from "./components/TriagePanel";
import ScoreGauge from "./components/ScoreGauge";
import EcgLine from "./components/EcgLine";
import "./App.css";

export default function App() {
  const [connected, setConnected] = useState(null); // null=checking, true, false
  const [tasks, setTasks] = useState([]);
  const [state, setState] = useState(null);
  const [activeTaskId, setActiveTaskId] = useState(null);
  const [obs, setObs] = useState(null);
  const [scores, setScores] = useState({}); // { taskId -> score }
  const [stepResults, setStepResults] = useState({}); // last obs per taskId
  const [loading, setLoading] = useState(false);
  const [log, setLog] = useState([]);
  const [allDone, setAllDone] = useState(false);
  const logRef = useRef(null);

  const addLog = useCallback((type, msg) => {
    setLog((prev) => [
      ...prev.slice(-49),
      { type, msg, time: new Date().toLocaleTimeString("en-US", { hour12: false }) },
    ]);
  }, []);

  // Check health on mount
  useEffect(() => {
    getHealth()
      .then(() => {
        setConnected(true);
        addLog("success", "Connected to Medical Triage Environment");
      })
      .catch(() => {
        setConnected(false);
        addLog("error", "Cannot connect to server at localhost:7860");
      });
  }, [addLog]);

  // Load tasks when connected
  useEffect(() => {
    if (!connected) return;
    getTasks().then((t) => {
      setTasks(Array.isArray(t) ? t : []);
      addLog("info", `Loaded ${Array.isArray(t) ? t.length : 0} tasks`);
    });
  }, [connected, addLog]);

  // Scroll log to bottom
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [log]);

  const handleReset = async (taskId) => {
    setLoading(true);
    setAllDone(false);
    try {
      const result = await resetEnv(taskId);
      setObs(result);
      setActiveTaskId(taskId);
      addLog("info", `[START] task=${taskId} — patient ${result.patient_id}`);
      // refresh state
      const s = await getState();
      setState(s);
    } catch (e) {
      addLog("error", `Reset failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleStep = async (action) => {
    if (!activeTaskId) return;
    setLoading(true);
    try {
      const result = await stepEnv(action);
      const score = result.partial_score ?? 0;
      const clampedScore = Math.max(0.001, Math.min(0.999, score));

      setObs(result);
      setScores((prev) => ({ ...prev, [activeTaskId]: clampedScore }));
      setStepResults((prev) => ({ ...prev, [activeTaskId]: result }));

      addLog(
        result.is_correct ? "success" : "warn",
        `[STEP] task=${activeTaskId} score=${clampedScore.toFixed(4)} correct=${result.is_correct}`
      );

      if (result.episode_done) {
        addLog("info", `[END] task=${activeTaskId} score=${clampedScore.toFixed(4)}`);
        setActiveTaskId(null);
        // Check if all tasks done
        const completedCount = Object.keys({ ...scores, [activeTaskId]: clampedScore }).length;
        if (completedCount >= tasks.length) {
          setAllDone(true);
          addLog("success", "▶ All tasks completed!");
        }
      }

      const s = await getState();
      setState(s);
    } catch (e) {
      addLog("error", `Step failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const meanScore =
    Object.values(scores).length > 0
      ? Object.values(scores).reduce((a, b) => a + b, 0) / Object.values(scores).length
      : 0;

  const completedTasks = Object.keys(scores).length;

  return (
    <div className="app">
      {/* Ambient scan line */}
      <div className="scan-line" />
      {/* Background grid */}
      <div className="bg-grid" />

      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <div className="logo-mark">
            <span className="logo-cross">✚</span>
            <div className="logo-text">
              <span className="logo-main">MED<span className="logo-accent">TRIAGE</span></span>
              <span className="logo-sub">AI ENVIRONMENT v1.0</span>
            </div>
          </div>
        </div>

        <div className="header-ecg">
          <EcgLine color={connected ? "#00ffe0" : "#ff2052"} speed={1.5} width={220} height={44} />
        </div>

        <div className="header-right">
          <div className="header-stats">
            <div className="hstat">
              <span className="hstat-label">TASKS</span>
              <span className="hstat-val">{completedTasks}/{tasks.length}</span>
            </div>
            <div className="hstat">
              <span className="hstat-label">MEAN SCORE</span>
              <span className="hstat-val" style={{ color: meanScore >= 0.7 ? "#39ff14" : meanScore >= 0.4 ? "#ffb300" : "#ff2052" }}>
                {(meanScore * 100).toFixed(1)}%
              </span>
            </div>
          </div>
          <div className={`conn-badge ${connected === null ? "checking" : connected ? "ok" : "error"}`}>
            <span className="conn-dot" />
            {connected === null ? "CHECKING..." : connected ? "SERVER ONLINE" : "SERVER OFFLINE"}
          </div>
        </div>
      </header>

      <main className="app-main">
        {/* ── LEFT: Patient Dashboard ── */}
        <aside className="sidebar-left">
          <div className="panel-header">
            <span className="ph-accent">▐</span>
            PATIENT QUEUE
            <span className="ph-count">{tasks.length}</span>
          </div>

          {tasks.length === 0 && connected && (
            <div className="empty-state">
              <div className="empty-icon">⌛</div>
              <div>Loading patients...</div>
            </div>
          )}

          {!connected && connected !== null && (
            <div className="empty-state error">
              <div className="empty-icon">⚡</div>
              <div>Backend offline</div>
              <div className="empty-sub">Start server on port 7860</div>
            </div>
          )}

          <div className="patient-list">
            {tasks.map((task) => (
              <PatientCard
                key={task.id}
                task={task}
                obs={stepResults[task.id]}
                isActive={activeTaskId === task.id}
                score={scores[task.id]}
                onClick={() => {
                  if (!loading && activeTaskId !== task.id) {
                    handleReset(task.id);
                  }
                }}
              />
            ))}
          </div>

          {/* Score Gauges */}
          {tasks.length > 0 && (
            <div className="gauge-section">
              <div className="panel-header" style={{ marginBottom: "12px" }}>
                <span className="ph-accent">▐</span>
                PERFORMANCE METRICS
              </div>
              <div className="gauge-row">
                <div className="gauge-item">
                  <ScoreGauge score={meanScore} label="MEAN SCORE" />
                </div>
                {tasks.map((t) => (
                  <div className="gauge-item" key={t.id}>
                    <ScoreGauge score={scores[t.id] ?? 0} label={t.id.toUpperCase()} />
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>

        {/* ── CENTER: Main workspace ── */}
        <section className="workspace">
          {/* All done celebration */}
          {allDone && (
            <div className="all-done-banner">
              <div className="adb-icon">✦</div>
              <div className="adb-text">
                <div className="adb-title">EPISODE COMPLETE</div>
                <div className="adb-score">
                  Mean Score: {(meanScore * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          )}

          {/* Triage panel */}
          <TriagePanel
            obs={activeTaskId ? obs : null}
            onSubmit={handleStep}
            loading={loading}
          />

          {/* State info */}
          {state && (
            <div className="state-panel">
              <div className="panel-header">
                <span className="ph-accent">▐</span>
                ENVIRONMENT STATE
              </div>
              <div className="state-grid">
                {[
                  { k: "EPISODE_ID", v: state.episode_id?.slice(0, 16) + "…" },
                  { k: "STEP_COUNT", v: state.step_count },
                  { k: "TASKS_COMPLETED", v: state.tasks_completed },
                  { k: "CUMULATIVE_REWARD", v: state.cumulative_reward?.toFixed(4) },
                  { k: "DIFFICULTY", v: state.difficulty?.toUpperCase() },
                  { k: "TOTAL_TASKS", v: state.total_tasks },
                ].map(({ k, v }) => (
                  <div className="state-item" key={k}>
                    <span className="si-key">{k}</span>
                    <span className="si-val">{v ?? "—"}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ESI reference */}
          <div className="esi-reference">
            <div className="panel-header">
              <span className="ph-accent">▐</span>
              ESI LEVEL REFERENCE
            </div>
            <div className="esi-ref-grid">
              {[
                { level: 1, color: "#ff2052", label: "IMMEDIATE", desc: "Requires immediate life-saving intervention" },
                { level: 2, color: "#ff6b35", label: "EMERGENT", desc: "High risk, severe pain, or altered mental status" },
                { level: 3, color: "#ffb300", label: "URGENT", desc: "Multiple resources needed, stable vitals" },
                { level: 4, color: "#39ff14", label: "SEMI-URGENT", desc: "One resource needed only" },
                { level: 5, color: "#00ffe0", label: "NON-URGENT", desc: "No resources needed" },
              ].map(({ level, color, label, desc }) => (
                <div className="esi-ref-row" key={level}>
                  <div className="esi-ref-badge" style={{ background: `${color}18`, borderColor: color, color }}>
                    {level}
                  </div>
                  <div className="esi-ref-info">
                    <span style={{ color, fontFamily: "var(--font-mono)", fontSize: "0.65rem", letterSpacing: "0.1em" }}>{label}</span>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>{desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── RIGHT: Log terminal ── */}
        <aside className="sidebar-right">
          <div className="panel-header">
            <span className="ph-accent">▐</span>
            SYSTEM LOG
            <span className="blink-dot">●</span>
          </div>
          <div className="log-terminal" ref={logRef}>
            {log.length === 0 && (
              <div className="log-empty">Awaiting events...</div>
            )}
            {log.map((entry, i) => (
              <div key={i} className={`log-entry log-${entry.type}`}>
                <span className="log-time">{entry.time}</span>
                <span className="log-msg">{entry.msg}</span>
              </div>
            ))}
          </div>

          {/* Quick action panel */}
          <div className="quick-actions">
            <div className="panel-header" style={{ marginBottom: "10px" }}>
              <span className="ph-accent">▐</span>
              QUICK ACTIONS
            </div>
            {tasks.map((task) => (
              <button
                key={task.id}
                className="qa-btn"
                onClick={() => handleReset(task.id)}
                disabled={loading || !connected}
              >
                <span className="qa-icon">▸</span>
                START {task.id.toUpperCase()}: {task.name}
              </button>
            ))}
            <button
              className="qa-btn qa-reset-all"
              onClick={() => {
                setScores({});
                setStepResults({});
                setObs(null);
                setActiveTaskId(null);
                setAllDone(false);
                setLog([]);
                handleReset(null);
              }}
              disabled={loading || !connected}
            >
              <span className="qa-icon">↺</span>
              RESET ALL TASKS
            </button>
          </div>
        </aside>
      </main>
    </div>
  );
}
