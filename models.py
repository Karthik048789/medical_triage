"""
Medical Triage Environment — Models
Defines typed Action, Observation, and State models.
All three are pure Pydantic BaseModel subclasses to avoid
the @dataclass + Pydantic inheritance conflict in Pydantic v2.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────────
# ACTION
# ──────────────────────────────────────────────────────────────────────────────

class TriageAction(BaseModel):
    """Action taken by the triage agent for a patient."""
    patient_id: str = ""
    triage_level: str = "3"          # ESI 1-5
    reasoning: str = ""
    order_tests: List[str] = Field(default_factory=list)
    disposition: str = "waiting_room"


# ──────────────────────────────────────────────────────────────────────────────
# OBSERVATION
# ──────────────────────────────────────────────────────────────────────────────

class TriageObservation(BaseModel):
    """Observation returned after each step."""
    patient_id: str = ""
    chief_complaint: str = ""
    vitals: Dict[str, str] = Field(default_factory=dict)
    history: str = ""
    task_description: str = ""
    feedback: str = ""
    is_correct: bool = False
    partial_score: float = 0.0
    episode_done: bool = False


# ──────────────────────────────────────────────────────────────────────────────
# STATE
# ──────────────────────────────────────────────────────────────────────────────

class TriageState(BaseModel):
    current_task_index: int = 0
    current_task_id: Optional[str] = None
    total_tasks: int = 3
    cumulative_reward: float = 0.0
    tasks_completed: int = 0
    difficulty: str = "easy"
    episode_id: str = ""
    step_count: int = 0
