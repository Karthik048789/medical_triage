# 🏥 Medical Triage Environment

> **OpenEnv Hackathon Submission — Scaler × Meta × Hugging Face**

An Emergency Room (ER) Medical Triage environment where an AI agent learns to function as a triage nurse. The agent assesses real-world patient presentations, assigns ESI triage levels, chooses dispositions, and orders diagnostic tests — all evaluated against clinically validated answers.

---

## 🎯 Why This Environment?

Medical triage is a **high-stakes, real-world decision problem** that:
- Requires **multi-step clinical reasoning** over structured observations
- Has **clear, objective correctness criteria** (ESI triage levels are standardised)
- Produces **partial reward signals** — rewarding partial knowledge even when the final answer is wrong
- Spans **5 patient scenarios across 3 difficulty tiers** (easy → medium → hard)
- Is immediately useful for training RL agents in **healthcare AI**

---

## 📋 Environment Specification

| Property | Value |
|---|---|
| Framework | OpenEnv (Gymnasium-style) |
| API | `reset()` / `step()` / `state()` |
| Transport | WebSocket / HTTP (FastAPI) |
| Tasks | 5 patient scenarios |
| Difficulty | Easy, Medium, Hard |
| Reward Range | `[0.0, 1.0]` per step |
| Max Steps/Episode | 3 (configurable) |
| Deployment | Hugging Face Spaces + Docker |

---

## 🧠 Action Space

```python
TriageAction(
    patient_id: str,           # Patient identifier
    triage_level: str,         # "1" (Immediate) to "5" (Non-Urgent)
    reasoning: str,            # Clinical reasoning (free text)
    order_tests: list[str],    # Diagnostic tests: ["ECG", "Troponin", ...]
    disposition: str,          # "resuscitation_bay" | "trauma_bay" |
                               # "fast_track" | "waiting_room" | "discharge"
)
```

---

## 👁️ Observation Space

```python
TriageObservation(
    patient_id: str,
    chief_complaint: str,      # Why the patient came to ER
    vitals: dict,              # HR, BP, RR, SpO2, Temp, GCS
    history: str,              # Relevant past medical history
    task_description: str,     # Task prompt with difficulty label
    feedback: str,             # Grader feedback from last action
    is_correct: bool,          # True if triage level + disposition correct
    partial_score: float,      # Reward 0.0–1.0 for last action
    episode_done: bool,        # True when episode ends
)
```

---

## 🏆 Reward Function

Each action is scored across **four weighted components**:

| Component | Easy | Medium | Hard | Description |
|---|---|---|---|---|
| **Triage Level** | 45% | 40% | 35% | Exact match = full; 1-level off = 40% partial |
| **Disposition** | 25% | 25% | 30% | Exact match only |
| **Tests Ordered** | 20% | 25% | 25% | Proportional to key tests hit |
| **Reasoning Quality** | 10% | 10% | 10% | Keyword match against expected concepts |

Partial credit is awarded throughout — agents that partially understand a case still receive meaningful signal.

---

## 📂 Project Structure

```
medical_triage_env/
├── __init__.py               # Public exports
├── models.py                 # TriageAction, TriageObservation, TriageState
├── client.py                 # MedicalTriageEnv (EnvClient)
├── openenv.yaml              # OpenEnv manifest
├── pyproject.toml            # Package config
├── inference.py              # ← Inference script (hackathon required)
├── README.md
├── server/
│   ├── __init__.py
│   ├── app.py                # FastAPI application
│   ├── medical_triage_environment.py  # Core environment logic
│   ├── requirements.txt
│   └── Dockerfile
└── outputs/
    ├── logs/
    └── evals/
```

---

## 🚀 Quick Start

### Local Development

```bash
# 1. Install dependencies
pip install openenv-core fastapi uvicorn openai

# 2. Run the server
uvicorn server.app:app --host 0.0.0.0 --port 7860

# 3. Test health
curl http://localhost:7860/health
# → {"status": "healthy"}

# 4. Run inference
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o-mini
export HF_TOKEN=your_token_here

python inference.py --env-url http://localhost:7860
```

### Docker

```bash
# Build
docker build -t medical-triage-env -f Dockerfile .

# Run
docker run -p 7860:7860 medical-triage-env

# Verify
curl http://localhost:7860/health
```

### Programmatic Usage

```python
from medical_triage_env import MedicalTriageEnv, TriageAction

# Async
import asyncio

async def main():
    async with MedicalTriageEnv(base_url="http://localhost:7860") as env:
        obs = await env.reset()
        print(obs.chief_complaint)

        result = await env.step(TriageAction(
            patient_id=obs.patient_id,
            triage_level="1",
            reasoning="Patient presents with chest pain, diaphoresis, hypotension. Classic STEMI.",
            order_tests=["ECG", "Troponin", "CXR"],
            disposition="resuscitation_bay",
        ))
        print(f"Reward: {result.reward}")
        print(f"Feedback: {result.observation.feedback}")

asyncio.run(main())

# Sync
with MedicalTriageEnv(base_url="http://localhost:7860").sync() as env:
    obs = env.reset()
    result = env.step(TriageAction(...))
```

---

## 🩺 Patient Scenarios

| # | Patient | Difficulty | Expected Level | Key Challenge |
|---|---|---|---|---|
| PT-001 | 65M, chest pain + diaphoresis | Easy | ESI-1 | Recognise classic STEMI |
| PT-002 | 72F, fever + confusion + hypotension | Medium | ESI-2 | Identify urosepsis → septic shock |
| PT-003 | 38M, MVC, GCS 8, tracheal deviation | Hard | ESI-1 | Polytrauma + tension pneumothorax |
| PT-004 | 18mo, febrile seizure | Hard | ESI-2 | Paediatric — rule out meningitis |
| PT-005 | 28M, agitated + empty pill bottles | Hard | ESI-2 | Psychiatric + medical overlay (overdose) |

---

## 📊 Evaluation

The hackathon grader will:
1. `POST /reset` → verify 200 response
2. `POST /step` for each task → verify reward in `[0.0, 1.0]`
3. `GET /state` → verify state fields
4. Run `inference.py` end-to-end in under 20 minutes on 2 vCPU / 8 GB RAM

---

## 🔧 Environment Variables

| Variable | Description |
|---|---|
| `API_BASE_URL` | LLM API endpoint (OpenAI-compatible) |
| `MODEL_NAME` | Model identifier string |
| `HF_TOKEN` | Hugging Face / API key |

---

## 📄 License

MIT — contributions welcome.
