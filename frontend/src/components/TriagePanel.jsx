import { useState } from "react";
import "./TriagePanel.css";

const ESI_LEVELS = [
  { level: "1", label: "IMMEDIATE", sublabel: "Life Threat", color: "#ff2052", icon: "☠" },
  { level: "2", label: "EMERGENT", sublabel: "High Risk", color: "#ff6b35", icon: "⚡" },
  { level: "3", label: "URGENT", sublabel: "Multi-Resource", color: "#ffb300", icon: "⚠" },
  { level: "4", label: "SEMI-URGENT", sublabel: "One Resource", color: "#39ff14", icon: "◉" },
  { level: "5", label: "NON-URGENT", sublabel: "No Resources", color: "#00ffe0", icon: "○" },
];

const DISPOSITIONS = [
  { val: "resuscitation_bay", label: "RESUSCITATION BAY", color: "#ff2052", icon: "🏥" },
  { val: "trauma_bay", label: "TRAUMA BAY", color: "#ff6b35", icon: "🔴" },
  { val: "fast_track", label: "FAST TRACK", color: "#ffb300", icon: "⚡" },
  { val: "waiting_room", label: "WAITING ROOM", color: "#39ff14", icon: "🪑" },
  { val: "discharge", label: "DISCHARGE", color: "#00ffe0", icon: "✓" },
];

const TEST_OPTIONS = [
  "ECG", "CBC", "BMP", "Troponin", "Chest X-Ray",
  "CT Head", "CT Chest", "Urinalysis", "Lipase", "D-Dimer",
  "Blood Culture", "ABG", "Coagulation Panel", "Lactic Acid",
];

export default function TriagePanel({ obs, onSubmit, loading }) {
  const [triageLevel, setTriageLevel] = useState("3");
  const [disposition, setDisposition] = useState("waiting_room");
  const [reasoning, setReasoning] = useState("");
  const [orderTests, setOrderTests] = useState([]);

  const toggleTest = (test) => {
    setOrderTests((prev) =>
      prev.includes(test) ? prev.filter((t) => t !== test) : [...prev, test]
    );
  };

  const handleSubmit = () => {
    onSubmit({
      patient_id: obs?.patient_id || "",
      triage_level: triageLevel,
      reasoning,
      order_tests: orderTests,
      disposition,
    });
    setReasoning("");
    setOrderTests([]);
    setTriageLevel("3");
    setDisposition("waiting_room");
  };

  const selectedEsi = ESI_LEVELS.find((e) => e.level === triageLevel);

  return (
    <div className="triage-panel">
      <div className="tp-section-title">
        <span className="tp-icon">╠</span> TRIAGE ASSIGNMENT CONSOLE
      </div>

      {/* Patient info */}
      {obs && obs.patient_id && obs.patient_id !== "END" && (
        <div className="tp-patient-info">
          <div className="tp-info-row">
            <span className="tp-info-label">PATIENT ID</span>
            <span className="tp-info-val cyan">{obs.patient_id}</span>
          </div>
          <div className="tp-info-row">
            <span className="tp-info-label">COMPLAINT</span>
            <span className="tp-info-val">{obs.chief_complaint}</span>
          </div>
          {obs.history && (
            <div className="tp-info-row">
              <span className="tp-info-label">HISTORY</span>
              <span className="tp-info-val">{obs.history}</span>
            </div>
          )}
          {obs.feedback && obs.feedback !== "Start" && (
            <div className={`tp-feedback ${obs.is_correct ? "correct" : "incorrect"}`}>
              <span className="feedback-icon">{obs.is_correct ? "✓" : "✗"}</span>
              <span>{obs.feedback}</span>
            </div>
          )}
        </div>
      )}

      {/* ESI Level selector */}
      <div className="tp-subsection">
        <div className="tp-sub-label">ESI TRIAGE LEVEL</div>
        <div className="esi-grid">
          {ESI_LEVELS.map((e) => (
            <button
              key={e.level}
              className={`esi-btn ${triageLevel === e.level ? "selected" : ""}`}
              style={{ "--esi-c": e.color }}
              onClick={() => setTriageLevel(e.level)}
            >
              <span className="esi-icon">{e.icon}</span>
              <span className="esi-num">{e.level}</span>
              <span className="esi-lbl">{e.label}</span>
              <span className="esi-sub">{e.sublabel}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Disposition */}
      <div className="tp-subsection">
        <div className="tp-sub-label">PATIENT DISPOSITION</div>
        <div className="disp-grid">
          {DISPOSITIONS.map((d) => (
            <button
              key={d.val}
              className={`disp-btn ${disposition === d.val ? "selected" : ""}`}
              style={{ "--disp-c": d.color }}
              onClick={() => setDisposition(d.val)}
            >
              <span>{d.icon}</span>
              <span className="disp-label">{d.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Order tests */}
      <div className="tp-subsection">
        <div className="tp-sub-label">ORDER TESTS ({orderTests.length} selected)</div>
        <div className="test-grid">
          {TEST_OPTIONS.map((t) => (
            <button
              key={t}
              className={`test-btn ${orderTests.includes(t) ? "selected" : ""}`}
              onClick={() => toggleTest(t)}
            >
              {orderTests.includes(t) && <span className="test-check">✓</span>}
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Reasoning */}
      <div className="tp-subsection">
        <div className="tp-sub-label">CLINICAL REASONING</div>
        <textarea
          className="tp-textarea"
          placeholder="Enter clinical reasoning for triage decision..."
          value={reasoning}
          onChange={(e) => setReasoning(e.target.value)}
          rows={4}
        />
      </div>

      {/* Submit */}
      <button
        className={`tp-submit ${loading ? "loading" : ""}`}
        onClick={handleSubmit}
        disabled={loading || !obs}
      >
        {loading ? (
          <>
            <span className="spinner" />
            PROCESSING...
          </>
        ) : (
          <>
            <span className="submit-icon">▸</span>
            SUBMIT TRIAGE DECISION
          </>
        )}
      </button>
    </div>
  );
}
