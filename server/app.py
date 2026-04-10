"""
Medical Triage Environment — FastAPI Server
"""

from fastapi import FastAPI
from medical_triage_environment import MedicalTriageEnvironment
from models import TriageAction

app = FastAPI()

env = MedicalTriageEnvironment()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reset")
def reset(body: dict = None):
    try:
        task_id = (body or {}).get("task_id")
        obs = env.reset(task_id=task_id)
        # obs is a Pydantic BaseModel — use model_dump() for serialization
        return obs.model_dump()
    except Exception as e:
        return {"error": str(e)}


@app.post("/step")
def step(action: dict):
    try:
        action_obj = TriageAction(**action)
        obs = env.step(action_obj)
        return obs.model_dump()
    except Exception as e:
        return {"error": str(e)}


@app.get("/state")
def state():
    try:
        return env.state.model_dump()
    except Exception as e:
        return {"error": str(e)}


@app.get("/tasks")
def tasks():
    try:
        return env.get_tasks()
    except Exception as e:
        return {"error": str(e)}


def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
