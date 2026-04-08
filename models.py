"""
Medical Triage Environment — Models
Defines typed Action, Observation, and State models.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from openenv.core.env_server import Action, Observation, State


# ──────────────────────────────────────────────────────────────────────────────
# ACTION
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class TriageAction(Action):
    """Action taken by the triage agent for a patient.

    Fields
    ------
    patient_id : str
        Identifier of the patient being assessed.
    triage_level : str
        Assigned ESI level: "1" (Immediate) … "5" (Non-Urgent).
    reasoning : str
        Free-text clinical reasoning for the assignment (used by grader).
    order_tests : list[str]
        Optional diagnostic tests to order (e.g. ["ECG", "CBC", "CXR"]).
    disposition : str
        One of: "resuscitation_bay", "trauma_bay", "fast_track",
                "waiting_room", "discharge".
    """
    patient_id: str = ""
    triage_level: str = "3"          # ESI 1-5
    reasoning: str = ""
    order_tests: List[str] = field(default_factory=list)
    disposition: str = "waiting_room"


# ──────────────────────────────────────────────────────────────────────────────
# OBSERVATION
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class TriageObservation(Observation):
    """Observation returned after each step.

    Fields
    ------
    patient_id : str
    chief_complaint : str
    vitals : dict  — HR, BP, RR, SpO2, Temp, GCS
    history : str  — relevant past medical history
    task_description : str — what the agent must do
    feedback : str — grader feedback after an action
    is_correct : bool
    partial_score : float  — 0.0 – 1.0
    episode_done : bool
    """
    patient_id: str = ""
    chief_complaint: str = ""
    vitals: Dict[str, str] = field(default_factory=dict)
    history: str = ""
    task_description: str = ""
    feedback: str = ""
    is_correct: bool = False
    partial_score: float = 0.0
    episode_done: bool = False


# ──────────────────────────────────────────────────────────────────────────────
# STATE
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class TriageState(State):
    """Internal episode state."""
    current_task_index: int = 0
    total_tasks: int = 3
    cumulative_reward: float = 0.0
    tasks_completed: int = 0
    difficulty: str = "easy"
    episode_id: str = ""
    step_count: int = 0
