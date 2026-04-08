"""
Medical Triage Environment — Client
"""

from openenv.core import EnvClient, StepResult

try:
    from .models import TriageAction, TriageObservation, TriageState
except ImportError:
    from models import TriageAction, TriageObservation, TriageState


class MedicalTriageEnv(EnvClient[TriageAction, TriageObservation, TriageState]):
    """HTTP client for the Medical Triage Environment.

    Usage
    -----
    Async:
        async with MedicalTriageEnv(base_url="http://localhost:8000") as env:
            obs = await env.reset()
            result = await env.step(TriageAction(
                patient_id=obs.patient_id,
                triage_level="1",
                reasoning="Patient shows signs of STEMI ...",
                order_tests=["ECG", "Troponin"],
                disposition="resuscitation_bay",
            ))

    Sync:
        with MedicalTriageEnv(base_url="http://localhost:8000").sync() as env:
            obs = env.reset()
            result = env.step(TriageAction(...))
    """

    def _step_payload(self, action: TriageAction) -> dict:
        return {
            "patient_id": action.patient_id,
            "triage_level": action.triage_level,
            "reasoning": action.reasoning,
            "order_tests": action.order_tests,
            "disposition": action.disposition,
        }

    def _parse_result(self, payload: dict) -> StepResult[TriageObservation]:
        obs = TriageObservation(
            patient_id=payload.get("patient_id", ""),
            chief_complaint=payload.get("chief_complaint", ""),
            vitals=payload.get("vitals", {}),
            history=payload.get("history", ""),
            task_description=payload.get("task_description", ""),
            feedback=payload.get("feedback", ""),
            is_correct=payload.get("is_correct", False),
            partial_score=payload.get("partial_score", 0.0),
            episode_done=payload.get("episode_done", False),
        )
        return StepResult(
            observation=obs,
            reward=payload.get("partial_score", 0.0),
            done=payload.get("episode_done", False),
        )

    def _parse_state(self, payload: dict) -> TriageState:
        return TriageState(
            current_task_index=payload.get("current_task_index", 0),
            total_tasks=payload.get("total_tasks", 3),
            cumulative_reward=payload.get("cumulative_reward", 0.0),
            tasks_completed=payload.get("tasks_completed", 0),
            difficulty=payload.get("difficulty", "easy"),
            episode_id=payload.get("episode_id", ""),
            step_count=payload.get("step_count", 0),
        )
